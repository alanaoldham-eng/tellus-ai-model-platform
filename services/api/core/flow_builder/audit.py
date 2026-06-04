from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field

from services.api.core.safety import redact_sensitive_text


AuditEventType = Literal[
    "flow_generated",
    "flow_edited",
    "flow_reviewed",
    "flow_published",
    "flow_archived",
    "connector_added",
    "connector_changed",
    "api_action_executed",
]


class AuditEvent(BaseModel):
    event_id: str = Field(default_factory=lambda: f"audit_{uuid4().hex[:12]}")
    flow_id: str
    event_type: AuditEventType
    actor: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    metadata: dict[str, Any] = Field(default_factory=dict)


class AuditLog:
    def __init__(self) -> None:
        self._events: list[AuditEvent] = []

    def append(
        self,
        flow_id: str,
        event_type: AuditEventType,
        actor: str,
        metadata: dict[str, Any] | None = None,
    ) -> AuditEvent:
        event = AuditEvent(
            flow_id=flow_id,
            event_type=event_type,
            actor=actor,
            metadata=redact_metadata(metadata or {}),
        )
        self._events.append(event)
        return event

    def for_flow(self, flow_id: str) -> list[AuditEvent]:
        return [event for event in self._events if event.flow_id == flow_id]


def redact_metadata(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: redact_metadata(child) for key, child in value.items()}
    if isinstance(value, list):
        return [redact_metadata(child) for child in value]
    if isinstance(value, str):
        return redact_sensitive_text(value)
    return value


AUDIT_LOG = AuditLog()

