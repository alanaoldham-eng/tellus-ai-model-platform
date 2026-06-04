from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from services.api.core.flow_builder.condition_engine import evaluate_condition
from services.api.core.flow_builder.flow_schema import (
    ActionDefinition,
    FieldDefinition,
    FlowDefinition,
    StepDefinition,
)
from services.api.core.flow_builder.validation_engine import validate_flow_definition


class FlowSimulationResult(BaseModel):
    visible_steps: list[str] = Field(default_factory=list)
    visible_fields: dict[str, list[str]] = Field(default_factory=dict)
    triggered_actions: list[dict[str, Any]] = Field(default_factory=list)
    api_calls: list[dict[str, Any]] = Field(default_factory=list)
    validation_errors: list[str] = Field(default_factory=list)
    routing_decision: str
    final_status: str


def simulate_flow(
    flow_json: dict[str, Any] | FlowDefinition,
    test_answers: dict[str, Any],
    mock_api_responses: dict[str, Any] | None = None,
) -> FlowSimulationResult:
    flow = flow_json if isinstance(flow_json, FlowDefinition) else FlowDefinition.model_validate(flow_json)
    validation = validate_flow_definition(flow)

    visible_steps: list[str] = []
    visible_fields: dict[str, list[str]] = {}
    triggered_actions: list[dict[str, Any]] = []
    api_calls: list[dict[str, Any]] = []
    validation_errors = list(validation.errors)
    manual_review = False
    declined = False
    approved = False
    route_to_step: str | None = None

    connector_ids = {connector.connector_id for connector in flow.connectors}
    for step in sorted(flow.steps, key=lambda item: item.order):
        if not evaluate_condition(step.visible_if, test_answers):
            continue

        visible_steps.append(step.step_id)
        visible_fields[step.step_id] = _visible_field_ids(step, test_answers)
        validation_errors.extend(_field_validation_errors(step, test_answers, visible_fields[step.step_id]))

        for action in step.actions:
            if not evaluate_condition(action.condition, test_answers):
                continue
            action_record = _action_record(step.step_id, action)
            triggered_actions.append(action_record)
            if action.type == "call_api":
                api_calls.append(
                    {
                        "step_id": step.step_id,
                        "action_id": action.action_id,
                        "connector_id": action.connector_id,
                        "would_execute": action.connector_id in connector_ids,
                        "mock_response": (mock_api_responses or {}).get(action.connector_id or "", {}),
                    }
                )
            if action.type in {"route_to_manual_review", "require_human_review"}:
                manual_review = True
            if action.type == "route_to_step":
                route_to_step = action.target_step_id

        if step.next_step_logic:
            for rule in step.next_step_logic.rules:
                if evaluate_condition(rule.condition, test_answers):
                    manual_review = manual_review or rule.route_to_manual_review
                    declined = declined or rule.decline_placeholder
                    approved = approved or rule.approval_placeholder
                    route_to_step = rule.target_step_id or route_to_step
                    break

    final_status = _final_status(validation_errors, manual_review, declined, approved)
    routing_decision = route_to_step or final_status
    return FlowSimulationResult(
        visible_steps=visible_steps,
        visible_fields=visible_fields,
        triggered_actions=triggered_actions,
        api_calls=api_calls,
        validation_errors=validation_errors,
        routing_decision=routing_decision,
        final_status=final_status,
    )


def _visible_field_ids(step: StepDefinition, answers: dict[str, Any]) -> list[str]:
    fields: list[FieldDefinition] = []
    fields.extend(step.fields)
    for section in step.sections:
        if evaluate_condition(section.visible_if, answers):
            fields.extend(section.fields)
    return [field.field_id for field in fields if evaluate_condition(field.visible_if, answers)]


def _field_validation_errors(
    step: StepDefinition,
    answers: dict[str, Any],
    visible_field_ids: list[str],
) -> list[str]:
    errors: list[str] = []
    fields = {field.field_id: field for field in step.fields}
    for section in step.sections:
        fields.update({field.field_id: field for field in section.fields})

    for field_id in visible_field_ids:
        field = fields[field_id]
        value = answers.get(field_id)
        if field.required and (value is None or value == "" or value is False):
            errors.append(f"{field_id} is required")
        for rule in field.validation_rules:
            if rule.rule == "length" and value not in {None, ""} and len(str(value)) != int(rule.value):
                errors.append(rule.message or f"{field_id} must have length {rule.value}")
    return errors


def _action_record(step_id: str, action: ActionDefinition) -> dict[str, Any]:
    return {
        "step_id": step_id,
        "action_id": action.action_id,
        "type": action.type,
        "trigger": action.trigger,
        "connector_id": action.connector_id,
        "target_step_id": action.target_step_id,
    }


def _final_status(
    validation_errors: list[str],
    manual_review: bool,
    declined: bool,
    approved: bool,
) -> str:
    if validation_errors:
        return "incomplete"
    if manual_review:
        return "manual_review"
    if declined:
        return "declined_placeholder"
    if approved:
        return "approved_placeholder"
    return "ready_to_submit"

