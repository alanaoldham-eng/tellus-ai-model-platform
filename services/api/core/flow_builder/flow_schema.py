from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


FlowStatus = Literal["draft", "review", "published", "archived"]
FieldType = Literal[
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
]
ConditionOperator = Literal[
    "equals",
    "not_equals",
    "contains",
    "greater_than",
    "less_than",
    "between",
    "exists",
    "not_exists",
    "in",
    "not_in",
    "and",
    "or",
    "not",
]
ActionTrigger = Literal[
    "on_step_load",
    "on_field_change",
    "on_step_submit",
    "before_final_submit",
    "after_final_submit",
    "on_manual_review",
    "on_decline",
    "on_approval",
]
ActionType = Literal[
    "call_api",
    "set_field_value",
    "show_step",
    "hide_step",
    "route_to_step",
    "route_to_manual_review",
    "calculate_value",
    "create_audit_event",
    "generate_disclosure_packet",
    "require_human_review",
    "submit_application",
]
PiiClassification = Literal["none", "low", "moderate", "high", "restricted"]
AuthType = Literal["none", "api_key", "bearer_token", "oauth2", "mTLS_placeholder"]


class FlowModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Condition(FlowModel):
    operator: ConditionOperator
    field: str | None = None
    value: Any = None
    values: list[Any] | None = None
    min_value: Any = None
    max_value: Any = None
    conditions: list[Condition] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_shape(self) -> Condition:
        if self.operator in {"and", "or"} and not self.conditions:
            raise ValueError(f"{self.operator} requires one or more child conditions")
        if self.operator == "not" and len(self.conditions) != 1:
            raise ValueError("not requires exactly one child condition")
        if self.operator not in {"and", "or", "not"} and not self.field:
            raise ValueError(f"{self.operator} requires field")
        return self


class ValidationRule(FlowModel):
    rule: str
    value: Any = None
    message: str | None = None


class FieldOption(FlowModel):
    label: str
    value: str | int | float | bool


class DataBinding(FlowModel):
    source: str = "application"
    path: str
    write_path: str | None = None


class RetentionPolicy(FlowModel):
    policy_id: str
    retention_period: str
    deletion_rule: str
    legal_hold_allowed: bool = True


class FieldDefinition(FlowModel):
    field_id: str
    label: str
    type: FieldType
    required: bool = False
    help_text: str | None = None
    placeholder: str | None = None
    default_value: Any = None
    validation_rules: list[ValidationRule] = Field(default_factory=list)
    visible_if: Condition | None = None
    enabled_if: Condition | None = None
    options: list[FieldOption] = Field(default_factory=list)
    data_binding: DataBinding | None = None
    pii_classification: PiiClassification = "none"
    retention_policy: RetentionPolicy | None = None
    audit_required: bool = False


class SectionDefinition(FlowModel):
    section_id: str
    title: str
    description: str | None = None
    order: int
    visible_if: Condition | None = None
    fields: list[FieldDefinition] = Field(default_factory=list)


class RetryPolicy(FlowModel):
    max_attempts: int = Field(default=2, ge=0, le=5)
    backoff_seconds: float = Field(default=0.5, ge=0.0, le=30.0)


class ConnectorConfig(FlowModel):
    connector_id: str
    name: str
    base_url: str
    auth_type: AuthType = "none"
    auth_secret_name: str | None = None
    headers: dict[str, str] = Field(default_factory=dict)
    request_template: dict[str, Any] = Field(default_factory=dict)
    response_mapping: dict[str, str] = Field(default_factory=dict)
    timeout_seconds: float = Field(default=10.0, gt=0.0, le=60.0)
    retry_policy: RetryPolicy = Field(default_factory=RetryPolicy)
    allowed_domains: list[str] = Field(default_factory=list)
    pii_allowed: bool = False
    audit_logging_required: bool = True

    @field_validator("base_url")
    @classmethod
    def require_http_url(cls, value: str) -> str:
        if not value.startswith(("https://", "http://")):
            raise ValueError("base_url must be an HTTP(S) URL")
        return value

    @model_validator(mode="after")
    def require_secret_reference_for_auth(self) -> ConnectorConfig:
        if self.auth_type != "none" and not self.auth_secret_name:
            raise ValueError("auth_secret_name is required when auth_type is not none")
        return self


class ActionDefinition(FlowModel):
    action_id: str
    trigger: ActionTrigger
    type: ActionType
    condition: Condition | None = None
    connector_id: str | None = None
    parameters: dict[str, Any] = Field(default_factory=dict)
    target_step_id: str | None = None
    target_field_id: str | None = None
    value: Any = None
    audit_event_type: str | None = None


class NextStepRule(FlowModel):
    condition: Condition
    target_step_id: str | None = None
    route_to_manual_review: bool = False
    decline_placeholder: bool = False
    approval_placeholder: bool = False


class NextStepLogic(FlowModel):
    default_next_step_id: str | None = None
    rules: list[NextStepRule] = Field(default_factory=list)


class StepDefinition(FlowModel):
    step_id: str
    title: str
    description: str | None = None
    order: int
    visible_if: Condition | None = None
    sections: list[SectionDefinition] = Field(default_factory=list)
    fields: list[FieldDefinition] = Field(default_factory=list)
    actions: list[ActionDefinition] = Field(default_factory=list)
    next_step_logic: NextStepLogic | None = None


class FlowDefinition(FlowModel):
    flow_id: str = Field(default_factory=lambda: f"flow_{uuid4().hex[:12]}")
    tenant_id: str | None = None
    name: str
    description: str
    industry: str
    flow_type: str
    version: int = Field(default=1, ge=1)
    status: FlowStatus = "draft"
    created_by: str = "tellus_flow_builder"
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    steps: list[StepDefinition]
    connectors: list[ConnectorConfig] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    missing_requirements: list[str] = Field(default_factory=list)
    risk_flags: list[str] = Field(default_factory=list)
    recommended_human_review_items: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def require_steps(self) -> FlowDefinition:
        if not self.steps:
            raise ValueError("flow must include at least one step")
        return self


def flow_json_schema() -> dict[str, Any]:
    return FlowDefinition.model_json_schema()


def strict_flow_json_schema() -> dict[str, Any]:
    schema = FlowDefinition.model_json_schema()
    schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
    schema["title"] = "Tellus FlowBuilder FlowDefinition"
    schema["x-tellus-contract-version"] = "2026-06-04"
    schema["x-tellus-publish-rules"] = {
        "ai_generation_status": "draft_only",
        "publish_requires_review_approved": True,
        "credentials": "secret_references_only",
        "renderer_target": "banking_modernization_products",
    }
    _force_additional_properties_false(schema)
    return schema


def flatten_fields(flow: FlowDefinition) -> list[FieldDefinition]:
    fields: list[FieldDefinition] = []
    for step in flow.steps:
        fields.extend(step.fields)
        for section in step.sections:
            fields.extend(section.fields)
    return fields


def now_utc() -> datetime:
    return datetime.now(UTC)


def _force_additional_properties_false(node: Any) -> None:
    if isinstance(node, dict):
        if node.get("type") == "object" or "properties" in node:
            node.setdefault("additionalProperties", False)
        for child in node.values():
            _force_additional_properties_false(child)
    elif isinstance(node, list):
        for child in node:
            _force_additional_properties_false(child)
