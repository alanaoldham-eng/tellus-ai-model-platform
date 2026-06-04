from __future__ import annotations

from typing import Any
from uuid import uuid4

from services.api.core.config import Settings
from services.api.core.flow_builder.flow_schema import FlowDefinition, flatten_fields, now_utc
from services.api.core.flow_builder.publishing import FLOW_REPOSITORY
from services.api.core.flow_builder.templates import template_by_key
from services.api.core.model_router import ModelRouter


REGULATED_RISK_TERMS = {
    "kyc": "kyc_aml_review_required",
    "kyb": "kyb_review_required",
    "aml": "kyc_aml_review_required",
    "ofac": "ofac_sanctions_review_required",
    "lending": "ecoa_udaap_review_required",
    "loan": "fcra_ecoa_udaap_review_required",
    "credit": "fcra_review_required",
    "beneficial ownership": "beneficial_ownership_review_required",
    "privacy": "glba_privacy_review_required",
}


async def generate_draft_flow(
    settings: Settings,
    natural_language_request: str,
    target_industry: str,
    target_flow_type: str,
    regulatory_context: str | list[str] | None = None,
    required_fields: list[str] | None = None,
    optional_existing_schema: dict[str, Any] | None = None,
    product_context: str | None = None,
    tenant_id: str | None = None,
    created_by: str = "flow_builder_user",
) -> tuple[FlowDefinition, dict[str, Any]]:
    flow, schema_note = _base_flow_from_request(
        natural_language_request,
        target_industry,
        target_flow_type,
        optional_existing_schema,
    )
    flow.flow_id = f"flow_{uuid4().hex[:12]}"
    flow.tenant_id = tenant_id
    flow.industry = target_industry or flow.industry
    flow.flow_type = target_flow_type or flow.flow_type
    flow.name = _name_from_flow_type(target_flow_type, flow.name)
    flow.description = natural_language_request[:500] or flow.description
    flow.status = "draft"
    flow.version = 1
    flow.created_by = created_by
    flow.created_at = now_utc()
    flow.updated_at = now_utc()

    assumptions = list(flow.assumptions)
    assumptions.extend(
        [
            "Generated as a draft only; publishing requires human approval.",
            "API connectors are placeholders and reference credentials by secret name only.",
            "Retention policies are starter metadata and must be reviewed against bank policy.",
        ]
    )
    if product_context:
        assumptions.append(f"Product context supplied by requester: {product_context}")
    if schema_note:
        assumptions.append(schema_note)

    missing_requirements = _missing_required_fields(flow, required_fields or [])
    if not regulatory_context:
        missing_requirements.append("regulatory_context was not provided")

    risk_flags = _risk_flags(natural_language_request, target_flow_type, regulatory_context)
    review_items = _review_items(target_flow_type, natural_language_request)

    model_note = await _optional_model_note(settings, natural_language_request, flow)

    flow.assumptions = sorted(set(assumptions))
    flow.missing_requirements = sorted(set(missing_requirements))
    flow.risk_flags = sorted(set(flow.risk_flags + risk_flags))
    flow.recommended_human_review_items = sorted(
        set(flow.recommended_human_review_items + review_items)
    )
    FLOW_REPOSITORY.save_draft(flow, actor=created_by)

    metadata = {
        "generation_mode": "template_guided_ai_assisted_draft",
        "model_note": model_note,
        "model_backend": settings.inference_backend,
    }
    return flow, metadata


def _base_flow_from_request(
    natural_language_request: str,
    target_industry: str,
    target_flow_type: str,
    optional_existing_schema: dict[str, Any] | None,
) -> tuple[FlowDefinition, str | None]:
    if optional_existing_schema:
        try:
            return (
                FlowDefinition.model_validate(optional_existing_schema).model_copy(deep=True),
                "optional_existing_schema was used as the starting point",
            )
        except ValueError:
            pass

    selector = f"{natural_language_request} {target_industry} {target_flow_type}".lower()
    return template_by_key(selector).model_copy(deep=True), None


def _name_from_flow_type(target_flow_type: str, fallback: str) -> str:
    if not target_flow_type:
        return fallback
    return target_flow_type.replace("_", " ").replace("-", " ").title()


def _missing_required_fields(flow: FlowDefinition, required_fields: list[str]) -> list[str]:
    field_ids = {field.field_id.lower() for field in flatten_fields(flow)}
    field_labels = {field.label.lower() for field in flatten_fields(flow)}
    missing: list[str] = []
    for required in required_fields:
        normalized = required.strip().lower()
        if normalized and normalized not in field_ids and normalized not in field_labels:
            missing.append(f"Required field not mapped to starter schema: {required}")
    return missing


def _risk_flags(
    natural_language_request: str,
    target_flow_type: str,
    regulatory_context: str | list[str] | None,
) -> list[str]:
    text = f"{natural_language_request} {target_flow_type} {regulatory_context}".lower()
    flags = ["human_review_required_before_publish", "regulated_workflow_draft"]
    for term, flag in REGULATED_RISK_TERMS.items():
        if term in text:
            flags.append(flag)
    prohibited_terms = ["race", "religion", "gender", "national origin", "disability"]
    if any(term in text for term in prohibited_terms):
        flags.append("prohibited_basis_logic_review_required")
    if "loan" in text or "credit" in text:
        flags.append("adverse_action_notice_review_required")
    if "bank" in text or "deposit" in text or "account" in text:
        flags.append("glba_privacy_review_required")
    return flags


def _review_items(target_flow_type: str, natural_language_request: str) -> list[str]:
    text = f"{target_flow_type} {natural_language_request}".lower()
    items = [
        "Bank compliance review required before publishing.",
        "Confirm no prohibited or discriminatory eligibility logic is present.",
        "Review PII classification, retention, disclosures, consent, and audit requirements.",
    ]
    if "loan" in text or "credit" in text:
        items.append("Review FCRA, ECOA, UDAAP, permissible purpose, and adverse action handling.")
    if "kyc" in text or "kyb" in text or "ofac" in text:
        items.append("Review KYC, KYB, AML, OFAC, and CIP operational requirements.")
    return items


async def _optional_model_note(
    settings: Settings,
    natural_language_request: str,
    flow: FlowDefinition,
) -> str:
    try:
        prompt_path = settings.project_root / "prompts" / "system" / "tellus_flow_builder_agent.md"
        system_prompt = prompt_path.read_text(encoding="utf-8").strip()
        router = ModelRouter(settings)
        route = router.select_for_chat()
        response = await router.generate(
            route,
            [
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": (
                        "Summarize risks and missing requirements for this draft flow. "
                        f"Request: {natural_language_request}\nFlow: {flow.name}"
                    ),
                },
            ],
            {"role": "flow_builder", "product_context": "Tellus FlowBuilder", "max_tokens": 400},
        )
        return response.content
    except Exception as exc:  # pragma: no cover - defensive fallback for optional model note
        return f"Model note unavailable: {exc.__class__.__name__}"

