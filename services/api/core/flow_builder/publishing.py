from __future__ import annotations

import json
import sqlite3
from typing import Any
from pathlib import Path

from services.api.core.config import get_settings
from services.api.core.flow_builder.audit import AUDIT_LOG, AuditEvent
from services.api.core.flow_builder.flow_schema import FlowDefinition, now_utc
from services.api.core.flow_builder.validation_engine import validate_flow_definition
from services.api.core.flow_builder.versioning import (
    FlowVersionRecord,
    create_version_record,
    next_version,
)


class FlowPublishError(ValueError):
    pass


class SQLiteFlowRepository:
    def __init__(self, db_path: str) -> None:
        self.db_path = Path(db_path)
        if not self.db_path.is_absolute():
            self.db_path = get_settings().project_root / self.db_path
        self._ensure_schema()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _ensure_schema(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS flows (
                    flow_id TEXT PRIMARY KEY,
                    tenant_id TEXT,
                    status TEXT NOT NULL,
                    version INTEGER NOT NULL,
                    flow_json TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS flow_versions (
                    version_id TEXT PRIMARY KEY,
                    flow_id TEXT NOT NULL,
                    tenant_id TEXT,
                    version INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    published_by TEXT NOT NULL,
                    published_at TEXT NOT NULL,
                    review_notes TEXT,
                    flow_snapshot TEXT NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS audit_events (
                    event_id TEXT PRIMARY KEY,
                    flow_id TEXT NOT NULL,
                    tenant_id TEXT,
                    event_type TEXT NOT NULL,
                    actor TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    metadata TEXT NOT NULL
                )
                """
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_flows_tenant ON flows (tenant_id, flow_id)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_versions_flow ON flow_versions (flow_id, tenant_id)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_audit_flow ON audit_events (flow_id, tenant_id)"
            )

    def save_draft(self, flow: FlowDefinition, actor: str = "flow_builder") -> FlowDefinition:
        flow.status = "draft"
        flow.updated_at = now_utc()
        self._upsert_flow(flow)
        self.append_audit(
            flow_id=flow.flow_id,
            tenant_id=flow.tenant_id,
            event_type="flow_generated",
            actor=actor,
            metadata={"flow_type": flow.flow_type, "industry": flow.industry},
        )
        return flow

    def get_flow(self, flow_id: str, tenant_id: str | None = None) -> FlowDefinition | None:
        query = "SELECT flow_json, tenant_id FROM flows WHERE flow_id = ?"
        params: list[str] = [flow_id]
        with self._connect() as connection:
            row = connection.execute(query, params).fetchone()
        if not row:
            return None
        if tenant_id is not None and row["tenant_id"] != tenant_id:
            return None
        return FlowDefinition.model_validate(json.loads(row["flow_json"]))

    def versions(self, flow_id: str, tenant_id: str | None = None) -> list[FlowVersionRecord]:
        query = "SELECT * FROM flow_versions WHERE flow_id = ?"
        params: list[str] = [flow_id]
        if tenant_id is not None:
            query += " AND tenant_id = ?"
            params.append(tenant_id)
        query += " ORDER BY version ASC"
        with self._connect() as connection:
            rows = connection.execute(query, params).fetchall()
        return [
            FlowVersionRecord(
                version_id=row["version_id"],
                flow_id=row["flow_id"],
                version=row["version"],
                status=row["status"],
                published_by=row["published_by"],
                published_at=row["published_at"],
                review_notes=row["review_notes"],
                flow_snapshot=json.loads(row["flow_snapshot"]),
            )
            for row in rows
        ]

    def audit_events(self, flow_id: str, tenant_id: str | None = None) -> list[AuditEvent]:
        query = "SELECT * FROM audit_events WHERE flow_id = ?"
        params: list[str] = [flow_id]
        if tenant_id is not None:
            query += " AND tenant_id = ?"
            params.append(tenant_id)
        query += " ORDER BY timestamp ASC"
        with self._connect() as connection:
            rows = connection.execute(query, params).fetchall()
        return [
            AuditEvent(
                event_id=row["event_id"],
                flow_id=row["flow_id"],
                event_type=row["event_type"],
                actor=row["actor"],
                timestamp=row["timestamp"],
                metadata=json.loads(row["metadata"]),
            )
            for row in rows
        ]

    def append_audit(
        self,
        flow_id: str,
        event_type: str,
        actor: str,
        metadata: dict[str, Any] | None = None,
        tenant_id: str | None = None,
    ) -> AuditEvent:
        event = AUDIT_LOG.append(
            flow_id=flow_id,
            event_type=event_type,  # type: ignore[arg-type]
            actor=actor,
            metadata=metadata or {},
        )
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO audit_events (
                    event_id, flow_id, tenant_id, event_type, actor, timestamp, metadata
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event.event_id,
                    flow_id,
                    tenant_id,
                    event.event_type,
                    actor,
                    event.timestamp.isoformat(),
                    json.dumps(event.metadata),
                ),
            )
        return event

    def publish(
        self,
        flow: FlowDefinition,
        review_approved: bool,
        reviewed_by: str,
        review_notes: str | None = None,
    ) -> FlowDefinition:
        if not review_approved:
            raise FlowPublishError("Human review approval is required before publishing.")

        validation = validate_flow_definition(flow)
        if not validation.valid:
            raise FlowPublishError("Flow cannot be published until validation errors are resolved.")

        existing_versions = self.versions(flow.flow_id, tenant_id=flow.tenant_id)
        flow.version = next_version(existing_versions)
        flow.status = "published"
        flow.updated_at = now_utc()
        self._upsert_flow(flow)
        version_record = create_version_record(flow, reviewed_by, review_notes)
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO flow_versions (
                    version_id, flow_id, tenant_id, version, status, published_by,
                    published_at, review_notes, flow_snapshot
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    version_record.version_id,
                    version_record.flow_id,
                    flow.tenant_id,
                    version_record.version,
                    version_record.status,
                    version_record.published_by,
                    version_record.published_at.isoformat(),
                    version_record.review_notes,
                    json.dumps(version_record.flow_snapshot),
                ),
            )
        self.append_audit(
            flow_id=flow.flow_id,
            tenant_id=flow.tenant_id,
            event_type="flow_reviewed",
            actor=reviewed_by,
            metadata={"review_approved": True},
        )
        self.append_audit(
            flow_id=flow.flow_id,
            tenant_id=flow.tenant_id,
            event_type="flow_published",
            actor=reviewed_by,
            metadata={"version": flow.version, "review_notes": review_notes or ""},
        )
        return flow

    def _upsert_flow(self, flow: FlowDefinition) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO flows (flow_id, tenant_id, status, version, flow_json, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(flow_id) DO UPDATE SET
                    tenant_id = excluded.tenant_id,
                    status = excluded.status,
                    version = excluded.version,
                    flow_json = excluded.flow_json,
                    updated_at = excluded.updated_at
                """,
                (
                    flow.flow_id,
                    flow.tenant_id,
                    flow.status,
                    flow.version,
                    json.dumps(flow.model_dump(mode="json")),
                    flow.updated_at.isoformat(),
                ),
            )


FLOW_REPOSITORY = SQLiteFlowRepository(get_settings().flow_store_path)


def flow_response_with_audit(flow: FlowDefinition, tenant_id: str | None = None) -> dict[str, Any]:
    return {
        "flow": flow.model_dump(mode="json"),
        "audit_events": [
            event.model_dump(mode="json")
            for event in FLOW_REPOSITORY.audit_events(flow.flow_id, tenant_id=tenant_id)
        ],
    }
