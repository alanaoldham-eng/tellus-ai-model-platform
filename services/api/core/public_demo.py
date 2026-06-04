from __future__ import annotations

from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field

from services.api.core.flow_builder.flow_schema import ActionDefinition, Condition, FlowDefinition
from services.api.core.flow_builder.simulator import simulate_flow
from services.api.core.flow_builder.templates import template_by_key
from services.api.core.safety import assess_text, safety_block_message


class FlowBuilderDemoBuilderOptions(BaseModel):
    flow_name: str | None = Field(default=None, max_length=120)
    include_identity: bool = True
    include_contact: bool = True
    include_address: bool = True
    include_employment_income: bool = True
    include_funding_source: bool = True
    include_documents: bool = True
    include_disclosures: bool = True
    include_api_connectors: bool = True
    show_residency_for_non_us: bool = True
    route_minors_to_manual_review: bool = True
    minor_age_threshold: int = Field(default=18, ge=0, le=25)
    collect_beneficial_owners_for_legal_entities: bool = True
    require_human_review: bool = False


class FlowBuilderDemoGenerateRequest(BaseModel):
    prompt: str = Field(..., min_length=8, max_length=2000)
    target_flow_type: str | None = Field(default=None, max_length=120)
    builder_options: FlowBuilderDemoBuilderOptions | None = None


class FlowBuilderDemoSimulateRequest(BaseModel):
    flow_json: dict[str, Any]
    test_answers: dict[str, Any] = Field(default_factory=dict)
    mock_api_responses: dict[str, Any] = Field(default_factory=dict)


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
    flow = _apply_builder_options(flow, request.builder_options)
    flow.name = request.builder_options.flow_name if request.builder_options and request.builder_options.flow_name else flow.name
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


def simulate_flow_builder_demo(request: FlowBuilderDemoSimulateRequest) -> dict[str, Any]:
    flow = FlowDefinition.model_validate(request.flow_json)
    result = simulate_flow(
        flow,
        test_answers=request.test_answers,
        mock_api_responses=request.mock_api_responses,
    )
    steps_by_id = {step.step_id: step for step in flow.steps}
    fields_by_step = {
        step.step_id: {field.field_id: field for field in step.fields}
        for step in flow.steps
    }
    visible_step_titles = [
        steps_by_id[step_id].title
        for step_id in result.visible_steps
        if step_id in steps_by_id
    ]
    visible_field_details = {
        step_id: [
            {
                "field_id": field_id,
                "label": fields_by_step.get(step_id, {}).get(field_id).label
                if field_id in fields_by_step.get(step_id, {})
                else field_id,
                "pii_classification": fields_by_step.get(step_id, {}).get(field_id).pii_classification
                if field_id in fields_by_step.get(step_id, {})
                else "none",
            }
            for field_id in field_ids
        ]
        for step_id, field_ids in result.visible_fields.items()
    }
    return {
        "mode": "mock_public_demo",
        "message": "Simulated the generated draft with sample answers.",
        **result.model_dump(mode="json"),
        "visible_step_titles": visible_step_titles,
        "visible_field_details": visible_field_details,
        "tester_notes": [
            "Conditional visibility is evaluated from the generated flow JSON.",
            "API actions are mock-only and are not sent to external vendors.",
            "Manual review, decline, and approval statuses are placeholders in this public demo.",
        ],
    }


def _apply_builder_options(
    flow: FlowDefinition,
    options: FlowBuilderDemoBuilderOptions | None,
) -> FlowDefinition:
    if options is None:
        return flow

    removed_step_ids: set[str] = set()
    if not options.include_contact:
        removed_step_ids.add("contact_information")
    if not options.include_address:
        removed_step_ids.update({"address", "business_address", "housing"})
    if not options.include_identity:
        removed_step_ids.update({"identity", "authorized_signer", "tax_information"})
    if not options.include_employment_income:
        removed_step_ids.update({"employment_income", "income"})
    if not options.include_funding_source:
        removed_step_ids.update({"funding_source", "expected_activity", "requested_amount"})
    if not options.include_documents:
        removed_step_ids.update({"document_upload", "documents"})
    if not options.include_disclosures:
        removed_step_ids.update({"disclosures_consent", "credit_consent"})
    if not options.collect_beneficial_owners_for_legal_entities:
        removed_step_ids.add("beneficial_ownership")

    flow.steps = [step for step in flow.steps if step.step_id not in removed_step_ids]

    for step in flow.steps:
        if not options.show_residency_for_non_us:
            step.fields = [
                field
                for field in step.fields
                if field.field_id not in {"residency_status", "country_of_citizenship"}
            ]
        if not options.route_minors_to_manual_review:
            step.actions = [
                action for action in step.actions if action.action_id != "route_minor_to_manual_review"
            ]
            if step.next_step_logic:
                step.next_step_logic.rules = [
                    rule
                    for rule in step.next_step_logic.rules
                    if rule.condition.field != "applicant_age"
                ]
        else:
            for action in step.actions:
                if action.action_id == "route_minor_to_manual_review" and action.condition:
                    action.condition.value = options.minor_age_threshold
            if step.next_step_logic:
                for rule in step.next_step_logic.rules:
                    if rule.condition.field == "applicant_age":
                        rule.condition.value = options.minor_age_threshold
        if not options.include_api_connectors:
            step.actions = [action for action in step.actions if action.type != "call_api"]

    if options.require_human_review:
        review_step = next((step for step in flow.steps if "review" in step.step_id), flow.steps[-1])
        if not any(action.action_id == "demo_require_human_review" for action in review_step.actions):
            review_step.actions.append(
                ActionDefinition(
                    action_id="demo_require_human_review",
                    trigger="before_final_submit",
                    type="require_human_review",
                    condition=Condition(operator="exists", field="application_certification"),
                )
            )

    if not options.include_api_connectors:
        flow.connectors = []

    _relink_steps(flow)
    return flow


def _relink_steps(flow: FlowDefinition) -> None:
    flow.steps = sorted(flow.steps, key=lambda step: step.order)
    for index, step in enumerate(flow.steps):
        step.order = index + 1
        if index == len(flow.steps) - 1:
            step.next_step_logic = None
            continue
        next_step_id = flow.steps[index + 1].step_id
        if step.next_step_logic is None:
            continue
        step.next_step_logic.default_next_step_id = next_step_id
        valid_step_ids = {item.step_id for item in flow.steps}
        for rule in step.next_step_logic.rules:
            if rule.target_step_id and rule.target_step_id not in valid_step_ids:
                rule.target_step_id = None


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
