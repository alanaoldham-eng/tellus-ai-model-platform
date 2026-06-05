from __future__ import annotations

import json
import re
from time import monotonic
from typing import Any
from uuid import uuid4

from fastapi import HTTPException, Request
from pydantic import BaseModel, Field, ValidationError

from services.api.core.config import Settings
from services.api.core.flow_builder.flow_schema import (
    ActionDefinition,
    Condition,
    FieldDefinition,
    FlowDefinition,
)
from services.api.core.flow_builder.simulator import simulate_flow
from services.api.core.flow_builder.templates import template_by_key
from services.api.core.model_router import ModelRouter
from services.api.core.safety import assess_text, safety_block_message


PUBLIC_DEMO_RATE_LIMIT_WINDOW_SECONDS = 60.0
PUBLIC_DEMO_BUCKETS: dict[str, list[float]] = {}
ALLOWED_PLAN_FIELD_TYPES = {
    "text",
    "textarea",
    "email",
    "phone",
    "date",
    "number",
    "currency",
    "select",
    "multiselect",
    "radio",
    "checkbox",
    "address",
    "ssn_last4",
    "tax_id",
    "file_upload",
    "signature",
    "consent_checkbox",
    "disclosure_acknowledgment",
    "business_entity",
    "beneficial_owner",
    "api_lookup",
    "computed",
}
ALLOWED_PII_CLASSIFICATIONS = {"none", "low", "moderate", "high", "restricted"}


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


class FlowBuilderDemoPlannedField(BaseModel):
    step_hint: str | None = Field(default=None, max_length=80)
    field_id: str = Field(..., max_length=80)
    label: str = Field(..., max_length=120)
    type: str = Field(default="text", max_length=40)
    required: bool = False
    pii_classification: str = Field(default="none", max_length=20)
    help_text: str | None = Field(default=None, max_length=240)


class FlowBuilderDemoModelPlan(BaseModel):
    flow_name: str | None = Field(default=None, max_length=120)
    target_flow_type: str | None = Field(default=None, max_length=120)
    description: str | None = Field(default=None, max_length=500)
    include_modules: list[str] = Field(default_factory=list, max_length=12)
    conditional_logic: list[str] = Field(default_factory=list, max_length=12)
    api_connectors: list[str] = Field(default_factory=list, max_length=12)
    additional_fields: list[FlowBuilderDemoPlannedField] = Field(default_factory=list, max_length=12)
    assumptions: list[str] = Field(default_factory=list, max_length=12)
    missing_requirements: list[str] = Field(default_factory=list, max_length=12)
    risk_flags: list[str] = Field(default_factory=list, max_length=12)
    recommended_human_review_items: list[str] = Field(default_factory=list, max_length=12)


async def build_flow_builder_demo(
    settings: Settings,
    request: FlowBuilderDemoGenerateRequest,
    http_request: Request,
) -> dict[str, Any]:
    _enforce_public_demo_guardrails(settings, http_request, request.prompt)
    assessment = assess_text(request.prompt)
    if assessment.should_block:
        return {
            "blocked": True,
            "mode": "mock_public_demo",
            "message": safety_block_message(assessment.flags),
            "safety_flags": assessment.flags,
        }

    model_plan, model_metadata = await _build_model_plan(settings, request)
    selected_flow_type = request.target_flow_type or (model_plan.target_flow_type if model_plan else None)
    lookup_text = f"{selected_flow_type or ''} {request.prompt}"
    flow = template_by_key(lookup_text)
    flow.flow_id = f"demo_{uuid4().hex[:10]}"
    flow.tenant_id = "demo_public"
    flow = _apply_builder_options(flow, request.builder_options)
    if model_plan:
        flow = _apply_model_plan(flow, model_plan)
    flow.name = _demo_flow_name(flow, request.builder_options, model_plan)
    flow.name = f"Demo Draft: {flow.name}"
    if model_plan and model_plan.description:
        flow.description = model_plan.description
    flow.status = "draft"
    flow.created_by = "tellus_public_demo"
    flow.assumptions = [
        _generation_assumption(model_metadata),
        "The public website endpoint calls the model server-side; no model credentials are exposed.",
        "The draft should be reviewed by bank operations, compliance, legal, and security teams.",
        *flow.assumptions,
        *(model_plan.assumptions if model_plan else []),
    ]
    flow.missing_requirements = sorted(
        {
            *flow.missing_requirements,
            *(model_plan.missing_requirements if model_plan else []),
            "Institution-specific disclosures, eligibility rules, and approval criteria.",
            "Real connector credentials stored in a managed secrets system.",
            "Bank-approved retention, audit, and adverse-action policies.",
        }
    )
    flow.risk_flags = sorted(set([*flow.risk_flags, *(model_plan.risk_flags if model_plan else [])]))
    flow.recommended_human_review_items = sorted(
        set(
            [
                *flow.recommended_human_review_items,
                *(model_plan.recommended_human_review_items if model_plan else []),
            ]
        )
    )

    return {
        "blocked": False,
        "mode": "public_model_demo",
        "message": _generation_message(model_metadata),
        "interpreted_request": _interpret_request(request.prompt),
        "selected_template": {
            "name": flow.name.replace("Demo Draft: ", ""),
            "flow_type": flow.flow_type,
            "reason": _selection_reason(lookup_text, flow.flow_type),
        },
        "generation_metadata": model_metadata,
        "model_plan": model_plan.model_dump(mode="json") if model_plan else None,
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


def _enforce_public_demo_guardrails(
    settings: Settings,
    request: Request,
    prompt: str | None = None,
) -> None:
    if prompt is not None and len(prompt) > settings.public_demo_max_prompt_chars:
        raise HTTPException(
            status_code=413,
            detail=f"Prompt is too long for the public demo. Limit is {settings.public_demo_max_prompt_chars} characters.",
        )

    origin = request.headers.get("origin")
    if origin and settings.public_demo_allowed_origins:
        normalized_allowed = {origin.rstrip("/") for origin in settings.public_demo_allowed_origins}
        if origin.rstrip("/") not in normalized_allowed:
            raise HTTPException(status_code=403, detail="Origin is not allowed for public demo calls.")

    client_key = _client_key(request)
    now = monotonic()
    bucket = [
        timestamp
        for timestamp in PUBLIC_DEMO_BUCKETS.get(client_key, [])
        if now - timestamp < PUBLIC_DEMO_RATE_LIMIT_WINDOW_SECONDS
    ]
    limit = max(1, min(settings.public_demo_rate_limit_per_minute, 60))
    if len(bucket) >= limit:
        raise HTTPException(status_code=429, detail="Public demo rate limit exceeded. Try again soon.")
    bucket.append(now)
    PUBLIC_DEMO_BUCKETS[client_key] = bucket


def _client_key(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for", "")
    client_ip = forwarded.split(",", 1)[0].strip()
    if not client_ip and request.client:
        client_ip = request.client.host
    user_agent = request.headers.get("user-agent", "unknown")[:80]
    return f"{client_ip or 'unknown'}:{user_agent}"


async def _build_model_plan(
    settings: Settings,
    request: FlowBuilderDemoGenerateRequest,
) -> tuple[FlowBuilderDemoModelPlan | None, dict[str, Any]]:
    metadata: dict[str, Any] = {
        "model_calls_enabled": settings.enable_public_model_demo,
        "backend": settings.inference_backend,
        "model_plan_used": False,
        "fallback_reason": None,
    }
    if not settings.enable_public_model_demo:
        metadata["fallback_reason"] = "public_model_demo_disabled"
        return None, metadata
    if settings.inference_backend == "mock":
        metadata["fallback_reason"] = "mock_backend_configured"
        return None, metadata

    try:
        router = ModelRouter(settings)
        route = router.select_for_chat()
        metadata["model_key"] = route.model_key
        metadata["hf_model_id"] = route.hf_model_id
        response = await router.generate(
            route,
            [
                {"role": "system", "content": _model_plan_system_prompt()},
                {"role": "user", "content": _model_plan_user_prompt(request)},
            ],
            {
                "role": "flow_builder_demo",
                "product_context": "Tellus FlowBuilder public demo",
                "temperature": 0.1,
                "max_tokens": 1800,
            },
        )
        metadata["model"] = response.model
        metadata["usage"] = response.usage
        if "mock_response" in response.safety_flags:
            metadata["fallback_reason"] = "model_backend_returned_mock_response"
            return None, metadata

        parsed = _extract_json_object(response.content)
        plan = FlowBuilderDemoModelPlan.model_validate(parsed)
        metadata["model_plan_used"] = True
        return plan, metadata
    except (ValueError, ValidationError, json.JSONDecodeError) as exc:
        metadata["fallback_reason"] = f"model_plan_parse_failed:{exc.__class__.__name__}"
        return None, metadata
    except Exception as exc:  # pragma: no cover - live model backends vary by deployment
        metadata["fallback_reason"] = f"model_call_failed:{exc.__class__.__name__}"
        return None, metadata


def _model_plan_system_prompt() -> str:
    return (
        "You are Tellus FlowBuilder. Convert a banking workflow request into JSON only. "
        "Do not include markdown. Do not claim legal compliance. Avoid prohibited or discriminatory "
        "eligibility logic. Use only these target_flow_type values when possible: "
        "consumer_deposit_account_opening, small_business_deposit_account_opening, "
        "loan_prequalification. Keep additional_fields short and schema-safe. Each additional field "
        "must include step_hint, field_id, label, type, required, pii_classification, and help_text. "
        "Supported field types include text, textarea, email, phone, date, number, currency, select, "
        "checkbox, address, ssn_last4, tax_id, file_upload, signature, consent_checkbox, "
        "disclosure_acknowledgment, business_entity, beneficial_owner, api_lookup, computed. "
        "Return an object with keys: flow_name, target_flow_type, description, include_modules, "
        "conditional_logic, api_connectors, additional_fields, assumptions, missing_requirements, "
        "risk_flags, recommended_human_review_items."
    )


def _model_plan_user_prompt(request: FlowBuilderDemoGenerateRequest) -> str:
    return json.dumps(
        {
            "natural_language_request": request.prompt,
            "target_flow_type": request.target_flow_type,
            "builder_options": request.builder_options.model_dump(mode="json")
            if request.builder_options
            else None,
            "demo_constraints": [
                "draft only",
                "no real vendor credentials",
                "no secrets in output",
                "human review required before publish",
            ],
        },
        indent=2,
    )


def _extract_json_object(text: str) -> dict[str, Any]:
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = re.sub(r"^```(?:json)?", "", stripped, flags=re.IGNORECASE).strip()
        stripped = re.sub(r"```$", "", stripped).strip()
    start = stripped.find("{")
    end = stripped.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("No JSON object found in model response")
    parsed = json.loads(stripped[start : end + 1])
    if not isinstance(parsed, dict):
        raise ValueError("Model response JSON must be an object")
    return parsed


def _demo_flow_name(
    flow: FlowDefinition,
    options: FlowBuilderDemoBuilderOptions | None,
    model_plan: FlowBuilderDemoModelPlan | None,
) -> str:
    if options and options.flow_name:
        return options.flow_name
    if model_plan and model_plan.flow_name:
        return model_plan.flow_name
    return flow.name


def _generation_assumption(metadata: dict[str, Any]) -> str:
    if metadata.get("model_plan_used"):
        return (
            "This public demo used a server-side model call to create a structured build plan, "
            "then compiled it into validated FlowBuilder JSON."
        )
    return (
        "This public demo used the template-guided fallback because live model generation was not "
        f"used ({metadata.get('fallback_reason') or 'unknown reason'})."
    )


def _generation_message(metadata: dict[str, Any]) -> str:
    if metadata.get("model_plan_used"):
        return "Generated a website-safe draft from a live server-side model build plan."
    return "Generated a website-safe fallback draft from the closest FlowBuilder starter template."


def _apply_model_plan(flow: FlowDefinition, model_plan: FlowBuilderDemoModelPlan) -> FlowDefinition:
    if model_plan.target_flow_type:
        flow.flow_type = model_plan.target_flow_type
    for planned_field in model_plan.additional_fields[:12]:
        field = _field_from_plan(planned_field)
        if field is None:
            continue
        target_step = _find_step_for_planned_field(flow, planned_field.step_hint)
        existing_field_ids = {item.field_id for item in target_step.fields}
        if field.field_id not in existing_field_ids:
            target_step.fields.append(field)
    return flow


def _field_from_plan(planned_field: FlowBuilderDemoPlannedField) -> FieldDefinition | None:
    field_type = planned_field.type.strip().lower()
    if field_type not in ALLOWED_PLAN_FIELD_TYPES:
        field_type = "text"
    pii = planned_field.pii_classification.strip().lower()
    if pii not in ALLOWED_PII_CLASSIFICATIONS:
        pii = "none"
    field_id = _safe_field_id(planned_field.field_id)
    if not field_id:
        return None
    return FieldDefinition(
        field_id=field_id,
        label=planned_field.label[:120],
        type=field_type,  # type: ignore[arg-type]
        required=planned_field.required,
        help_text=planned_field.help_text,
        pii_classification=pii,  # type: ignore[arg-type]
        audit_required=pii in {"high", "restricted"},
    )


def _safe_field_id(value: str) -> str:
    normalized = re.sub(r"[^a-zA-Z0-9_]+", "_", value.strip().lower()).strip("_")
    return normalized[:80]


def _find_step_for_planned_field(flow: FlowDefinition, step_hint: str | None):
    if step_hint:
        hint = step_hint.strip().lower().replace(" ", "_")
        for step in flow.steps:
            haystack = f"{step.step_id} {step.title}".lower().replace(" ", "_")
            if hint in haystack or haystack in hint:
                return step
    for step in flow.steps:
        if "review" in step.step_id:
            return step
    return flow.steps[-1]


def simulate_flow_builder_demo(
    settings: Settings,
    payload: FlowBuilderDemoSimulateRequest,
    http_request: Request,
) -> dict[str, Any]:
    _enforce_public_demo_guardrails(settings, http_request)
    if len(json.dumps(payload.flow_json)) > 250_000:
        raise HTTPException(status_code=413, detail="Flow JSON is too large for the public demo.")

    flow = FlowDefinition.model_validate(payload.flow_json)
    result = simulate_flow(
        flow,
        test_answers=payload.test_answers,
        mock_api_responses=payload.mock_api_responses,
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
