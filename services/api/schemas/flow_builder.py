from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from services.api.core.flow_builder.flow_schema import Condition, ConnectorConfig


class FlowGenerateRequest(BaseModel):
    natural_language_request: str = Field(..., min_length=1)
    target_industry: str = "banking"
    target_flow_type: str = "consumer_deposit_account_opening"
    regulatory_context: str | list[str] | None = None
    required_fields: list[str] = Field(default_factory=list)
    optional_existing_schema: dict[str, Any] | None = None
    product_context: str | None = None
    tenant_id: str | None = None
    created_by: str = "flow_builder_user"


class FlowGenerateResponse(BaseModel):
    flow_json: dict[str, Any]
    assumptions_made: list[str]
    missing_requirements: list[str]
    risk_flags: list[str]
    recommended_human_review_items: list[str]
    generation_metadata: dict[str, Any] = Field(default_factory=dict)


class FlowSchemaResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    json_schema: dict[str, Any] = Field(alias="schema")
    strict: bool = True
    renderer_contract_url: str = "/flow-builder/renderer-contract"


class RendererContractResponse(BaseModel):
    contract: dict[str, Any]


class FlowValidateRequest(BaseModel):
    flow_json: dict[str, Any]


class FlowValidateResponse(BaseModel):
    valid: bool
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    risk_flags: list[str] = Field(default_factory=list)
    normalized_flow: dict[str, Any] | None = None


class FlowSimulateRequest(BaseModel):
    flow_json: dict[str, Any]
    test_answers: dict[str, Any] = Field(default_factory=dict)
    mock_api_responses: dict[str, Any] = Field(default_factory=dict)


class FlowSimulateResponse(BaseModel):
    visible_steps: list[str]
    visible_fields: dict[str, list[str]]
    triggered_actions: list[dict[str, Any]]
    api_calls: list[dict[str, Any]]
    validation_errors: list[str]
    routing_decision: str
    final_status: str


class EvaluateConditionRequest(BaseModel):
    condition: Condition
    sample_payload: dict[str, Any] = Field(default_factory=dict)


class EvaluateConditionResponse(BaseModel):
    result: bool


class TestConnectorRequest(BaseModel):
    connector: ConnectorConfig
    input_payload: dict[str, Any] = Field(default_factory=dict)
    mock_api_response: dict[str, Any] | None = None
    mock_mode: bool = True
    actor: str = "flow_builder_user"
    flow_id: str = "connector_test"


class TestConnectorResponse(BaseModel):
    connector_id: str
    success: bool
    mock_mode: bool
    request_preview: dict[str, Any]
    response: dict[str, Any]
    warnings: list[str] = Field(default_factory=list)


class PublishFlowRequest(BaseModel):
    flow_id: str | None = None
    flow_json: dict[str, Any] | None = None
    review_approved: bool = False
    reviewed_by: str = Field(default="flow_reviewer", min_length=1)
    review_notes: str | None = None


class PublishFlowResponse(BaseModel):
    flow_json: dict[str, Any]
    version: int
    status: str
    audit_events: list[dict[str, Any]] = Field(default_factory=list)


class FlowGetResponse(BaseModel):
    flow_json: dict[str, Any]
    audit_events: list[dict[str, Any]] = Field(default_factory=list)


class FlowVersionsResponse(BaseModel):
    flow_id: str
    versions: list[dict[str, Any]] = Field(default_factory=list)
