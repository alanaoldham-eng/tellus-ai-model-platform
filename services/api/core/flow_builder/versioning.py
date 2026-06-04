from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field

from services.api.core.flow_builder.flow_schema import FlowDefinition


class FlowVersionRecord(BaseModel):
    version_id: str = Field(default_factory=lambda: f"flow_version_{uuid4().hex[:12]}")
    flow_id: str
    version: int
    status: str
    published_by: str
    published_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    review_notes: str | None = None
    flow_snapshot: dict[str, Any]


def next_version(existing_versions: list[FlowVersionRecord]) -> int:
    if not existing_versions:
        return 1
    return max(record.version for record in existing_versions) + 1


def create_version_record(
    flow: FlowDefinition,
    published_by: str,
    review_notes: str | None,
) -> FlowVersionRecord:
    return FlowVersionRecord(
        flow_id=flow.flow_id,
        version=flow.version,
        status=flow.status,
        published_by=published_by,
        review_notes=review_notes,
        flow_snapshot=flow.model_dump(mode="json"),
    )

