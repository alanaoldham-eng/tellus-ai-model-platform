from __future__ import annotations

from typing import Any

from services.api.core.flow_builder.flow_schema import (
    ActionType,
    FieldType,
    FlowStatus,
    PiiClassification,
)


RENDERER_CONTRACT_VERSION = "2026-06-04"


def renderer_contract() -> dict[str, Any]:
    return {
        "contract_name": "Tellus FlowBuilder Renderer Contract",
        "contract_version": RENDERER_CONTRACT_VERSION,
        "target_products": ["banking_modernization"],
        "non_targets": ["CAPIT"],
        "purpose": (
            "Defines how Tellus banking modernization frontends should render, validate, "
            "simulate, and submit portable FlowBuilder JSON definitions."
        ),
        "flow_statuses": list(FlowStatus.__args__),  # type: ignore[attr-defined]
        "supported_field_types": list(FieldType.__args__),  # type: ignore[attr-defined]
        "supported_action_types": list(ActionType.__args__),  # type: ignore[attr-defined]
        "pii_classifications": list(PiiClassification.__args__),  # type: ignore[attr-defined]
        "renderer_requirements": [
            "Render steps in ascending order.",
            "Evaluate visible_if and enabled_if before displaying each step, section, and field.",
            "Block final submission when required visible fields are missing or invalid.",
            "Display draft/review/published status clearly to authenticated bank staff.",
            "Never render connector secrets or request users to paste API credentials.",
            "Show human-review warnings for regulated banking, lending, KYC, KYB, AML, OFAC, "
            "FCRA, ECOA, UDAAP, GLBA, privacy, and retention risk flags.",
            "Respect pii_classification and retention_policy metadata in frontend analytics, "
            "logging, and session replay tools.",
        ],
        "frontend_events": [
            "flow_loaded",
            "step_viewed",
            "field_changed",
            "step_submitted",
            "manual_review_routed",
            "connector_mock_previewed",
            "application_submitted",
        ],
        "submission_contract": {
            "flow_id": "string",
            "flow_version": "integer",
            "tenant_id": "string",
            "answers": "object keyed by field_id",
            "renderer_metadata": {
                "renderer_name": "string",
                "renderer_version": "string",
                "session_id": "string",
            },
        },
        "accessibility_requirements": [
            "Every rendered field must bind label, help text, error text, and required state.",
            "Conditional changes must be announced to assistive technology.",
            "File upload, consent, disclosure, and signature fields require explicit review states.",
        ],
    }
