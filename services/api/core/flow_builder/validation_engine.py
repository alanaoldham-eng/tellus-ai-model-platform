from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ValidationError

from services.api.core.flow_builder.api_connector_engine import validate_connector_security
from services.api.core.flow_builder.flow_schema import FlowDefinition, flatten_fields
from services.api.core.safety import redact_sensitive_text


SENSITIVE_FIELD_TYPES = {
    "address",
    "ssn_last4",
    "tax_id",
    "file_upload",
    "signature",
    "beneficial_owner",
    "business_entity",
}


class FlowValidationResult(BaseModel):
    valid: bool
    errors: list[str] = []
    warnings: list[str] = []
    risk_flags: list[str] = []
    normalized_flow: dict[str, Any] | None = None


def validate_flow_definition(flow_json: dict[str, Any] | FlowDefinition) -> FlowValidationResult:
    errors: list[str] = []
    warnings: list[str] = []
    risk_flags: list[str] = []

    try:
        flow = flow_json if isinstance(flow_json, FlowDefinition) else FlowDefinition.model_validate(flow_json)
    except ValidationError as exc:
        return FlowValidationResult(
            valid=False,
            errors=[_format_validation_error(error) for error in exc.errors()],
            warnings=[],
            risk_flags=[],
        )
    except ValueError as exc:
        return FlowValidationResult(valid=False, errors=[str(exc)], warnings=[], risk_flags=[])

    _validate_unique_ids(flow, errors)
    _validate_connectors(flow, errors)
    _validate_actions(flow, errors)
    _validate_sensitive_fields(flow, errors, warnings)
    _validate_no_secrets(flow, errors)
    _add_regulated_warnings(flow, warnings, risk_flags)

    return FlowValidationResult(
        valid=not errors,
        errors=errors,
        warnings=warnings,
        risk_flags=sorted(set(risk_flags + flow.risk_flags)),
        normalized_flow=flow.model_dump(mode="json"),
    )


def _validate_unique_ids(flow: FlowDefinition, errors: list[str]) -> None:
    step_ids: set[str] = set()
    field_ids: set[str] = set()
    action_ids: set[str] = set()

    for step in flow.steps:
        if step.step_id in step_ids:
            errors.append(f"duplicate step_id: {step.step_id}")
        step_ids.add(step.step_id)

        for field in step.fields:
            if field.field_id in field_ids:
                errors.append(f"duplicate field_id: {field.field_id}")
            field_ids.add(field.field_id)

        for section in step.sections:
            for field in section.fields:
                if field.field_id in field_ids:
                    errors.append(f"duplicate field_id: {field.field_id}")
                field_ids.add(field.field_id)

        for action in step.actions:
            if action.action_id in action_ids:
                errors.append(f"duplicate action_id: {action.action_id}")
            action_ids.add(action.action_id)


def _validate_connectors(flow: FlowDefinition, errors: list[str]) -> None:
    for connector in flow.connectors:
        for connector_error in validate_connector_security(connector):
            errors.append(f"connector {connector.connector_id}: {connector_error}")


def _validate_actions(flow: FlowDefinition, errors: list[str]) -> None:
    connector_ids = {connector.connector_id for connector in flow.connectors}
    step_ids = {step.step_id for step in flow.steps}

    for step in flow.steps:
        for action in step.actions:
            if action.type == "call_api" and not action.connector_id:
                errors.append(f"action {action.action_id} must include connector_id")
            if action.connector_id and action.connector_id not in connector_ids:
                errors.append(f"action {action.action_id} references missing connector {action.connector_id}")
            if action.target_step_id and action.target_step_id not in step_ids:
                errors.append(f"action {action.action_id} references missing step {action.target_step_id}")

        if step.next_step_logic:
            if (
                step.next_step_logic.default_next_step_id
                and step.next_step_logic.default_next_step_id not in step_ids
            ):
                errors.append(f"step {step.step_id} default_next_step_id references missing step")
            for rule in step.next_step_logic.rules:
                if rule.target_step_id and rule.target_step_id not in step_ids:
                    errors.append(f"step {step.step_id} next-step rule references missing step")


def _validate_sensitive_fields(
    flow: FlowDefinition,
    errors: list[str],
    warnings: list[str],
) -> None:
    for field in flatten_fields(flow):
        if field.type in SENSITIVE_FIELD_TYPES and field.pii_classification in {"none", "low"}:
            errors.append(f"sensitive field {field.field_id} must set pii_classification")
        if field.pii_classification in {"high", "restricted"} and not field.retention_policy:
            errors.append(f"sensitive field {field.field_id} must set retention_policy")
        if field.pii_classification in {"high", "restricted"} and not field.audit_required:
            warnings.append(f"sensitive field {field.field_id} should set audit_required=true")


def _validate_no_secrets(flow: FlowDefinition, errors: list[str]) -> None:
    serialized = str(flow.model_dump(mode="json"))
    if redact_sensitive_text(serialized) != serialized:
        errors.append("flow JSON appears to contain a secret or direct personal contact value")


def _add_regulated_warnings(
    flow: FlowDefinition,
    warnings: list[str],
    risk_flags: list[str],
) -> None:
    normalized = f"{flow.industry} {flow.flow_type} {flow.description}".lower()
    if any(token in normalized for token in ["bank", "kyc", "kyb", "deposit", "account"]):
        warnings.append("Banking flows require compliance review before publishing.")
        risk_flags.extend(["regulated_banking_flow", "human_review_required_before_publish"])
    if any(token in normalized for token in ["loan", "credit", "prequalification", "lending"]):
        warnings.append("Lending flows may require FCRA, ECOA, UDAAP, and adverse action review.")
        risk_flags.extend(["regulated_lending_flow", "adverse_action_notice_review_required"])


def _format_validation_error(error: dict[str, Any]) -> str:
    location = ".".join(str(part) for part in error.get("loc", []))
    return f"{location}: {error.get('msg', 'invalid value')}"

