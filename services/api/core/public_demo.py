from __future__ import annotations

from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field

from services.api.core.flow_builder.flow_schema import FlowDefinition
from services.api.core.flow_builder.templates import template_by_key
from services.api.core.safety import assess_text, safety_block_message


class FlowBuilderDemoGenerateRequest(BaseModel):
    prompt: str = Field(..., min_length=8, max_length=2000)
    target_flow_type: str | None = Field(default=None, max_length=120)


def build_flow_builder_demo(request: FlowBuilderDemoGenerateRequest) -> dict[str, Any]:
    assessment = assess_text(request.prompt)
    if assessment.should_block:
        return {
            "blocked": True,
            "mode": "mock_public_demo",
            "message": safety_block_message(assessment.flags),
            "safety_flags": assessment.flags,
        }

    lookup_text = f"{request.target_flow_type or ''} {request.prompt}"
    flow = template_by_key(lookup_text)
    flow.flow_id = f"demo_{uuid4().hex[:10]}"
    flow.tenant_id = "demo_public"
    flow.name = f"Demo Draft: {flow.name}"
    flow.status = "draft"
    flow.created_by = "tellus_public_demo"
    flow.assumptions = [
        "This public demo uses deterministic template matching, not live model generation.",
        "The production endpoint remains protected at POST /flow-builder/generate.",
        "The draft should be reviewed by bank operations, compliance, legal, and security teams.",
        *flow.assumptions,
    ]
    flow.missing_requirements = sorted(
        {
            *flow.missing_requirements,
            "Institution-specific disclosures, eligibility rules, and approval criteria.",
            "Real connector credentials stored in a managed secrets system.",
            "Bank-approved retention, audit, and adverse-action policies.",
        }
    )

    return {
        "blocked": False,
        "mode": "mock_public_demo",
        "message": "Generated a website-safe draft from the closest FlowBuilder starter template.",
        "interpreted_request": _interpret_request(request.prompt),
        "selected_template": {
            "name": flow.name.replace("Demo Draft: ", ""),
            "flow_type": flow.flow_type,
            "reason": _selection_reason(lookup_text, flow.flow_type),
        },
        "summary": _flow_summary(flow),
        "assumptions": flow.assumptions,
        "missing_requirements": flow.missing_requirements,
        "risk_flags": sorted(set([*flow.risk_flags, *assessment.flags, "human_review_required"])),
        "recommended_human_review_items": flow.recommended_human_review_items,
        "next_steps": [
            "Review the generated structure with product, operations, compliance, and legal teams.",
            "Replace placeholder connectors with tenant-approved connector configurations.",
            "Test the flow with sample answers through POST /flow-builder/simulate.",
            "Publish only after review_approved=true is recorded by an authorized reviewer.",
        ],
        "flow_json": _public_flow_json(flow),
        "safety_flags": assessment.flags,
    }


def _interpret_request(prompt: str) -> dict[str, list[str]]:
    lowered = prompt.lower()
    signals = {
        "identity": ["identity", "ssn", "id", "kyc", "cip"],
        "business": ["business", "kyb", "beneficial owner", "entity", "ein"],
        "lending": ["loan", "credit", "prequalification", "prequal", "borrow"],
        "documents": ["document", "upload", "driver", "passport"],
        "consent": ["consent", "disclosure", "esign", "privacy"],
        "review": ["manual review", "review", "under 18", "minor", "exception"],
        "connectors": ["api", "kyc", "kyb", "ofac", "core banking", "fraud", "credit bureau"],
    }
    matched = [
        label
        for label, terms in signals.items()
        if any(term in lowered for term in terms)
    ]
    if not matched:
        matched = ["general onboarding"]
    return {"detected_workflow_signals": matched}


def _selection_reason(prompt: str, flow_type: str) -> str:
    lowered = prompt.lower()
    if "business" in lowered or "kyb" in lowered:
        return "The prompt mentioned business or KYB signals, so the demo selected the small business template."
    if "loan" in lowered or "credit" in lowered or "prequal" in lowered:
        return "The prompt mentioned lending or credit signals, so the demo selected the loan prequalification template."
    if "checking" in lowered or "deposit" in lowered or "account" in lowered:
        return "The prompt mentioned deposit account onboarding, so the demo selected the consumer checking template."
    return f"The prompt did not name a specialized flow, so the demo used {flow_type} as the baseline."


def _flow_summary(flow: FlowDefinition) -> dict[str, Any]:
    steps = sorted(flow.steps, key=lambda step: step.order)
    fields = [field for step in steps for field in step.fields]
    sensitive_fields = [
        field.field_id
        for field in fields
        if field.pii_classification in {"high", "restricted"}
    ]
    api_actions = [
        {
            "step_id": step.step_id,
            "action_id": action.action_id,
            "connector_id": action.connector_id,
            "trigger": action.trigger,
        }
        for step in steps
        for action in step.actions
        if action.type == "call_api"
    ]
    return {
        "step_count": len(steps),
        "field_count": len(fields),
        "connector_count": len(flow.connectors),
        "sensitive_field_count": len(sensitive_fields),
        "sensitive_fields": sensitive_fields[:12],
        "api_actions": api_actions,
        "manual_review_controls": [
            action.action_id
            for step in steps
            for action in step.actions
            if action.type in {"route_to_manual_review", "require_human_review"}
        ],
    }


def _public_flow_json(flow: FlowDefinition) -> dict[str, Any]:
    data = flow.model_dump(mode="json", exclude={"created_at", "updated_at"})
    for connector in data.get("connectors", []):
        connector.pop("auth_secret_name", None)
        connector["auth_secret_name"] = "[stored outside flow JSON]"
    return data
