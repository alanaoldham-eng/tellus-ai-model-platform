import json
from collections.abc import AsyncGenerator

from fastapi import APIRouter, Depends, HTTPException
from fastapi import Request as FastAPIRequest
from starlette.responses import StreamingResponse

from services.api.core.config import Settings, get_settings
from services.api.core.flow_builder.ai_flow_generator import generate_draft_flow
from services.api.core.flow_builder.api_connector_engine import execute_connector_test
from services.api.core.flow_builder.condition_engine import evaluate_condition
from services.api.core.flow_builder.flow_schema import FlowDefinition, strict_flow_json_schema
from services.api.core.flow_builder.publishing import (
    FLOW_REPOSITORY,
    FlowPublishError,
    flow_response_with_audit,
)
from services.api.core.flow_builder.renderer_contract import renderer_contract
from services.api.core.flow_builder.simulator import simulate_flow
from services.api.core.flow_builder.templates import starter_templates
from services.api.core.flow_builder.validation_engine import validate_flow_definition
from services.api.core.safety import assess_text
from services.api.schemas.flow_builder import (
    EvaluateConditionRequest,
    EvaluateConditionResponse,
    FlowGenerateRequest,
    FlowGenerateResponse,
    FlowGetResponse,
    FlowSchemaResponse,
    FlowSimulateRequest,
    FlowSimulateResponse,
    FlowValidateRequest,
    FlowValidateResponse,
    FlowVersionsResponse,
    PublishFlowRequest,
    PublishFlowResponse,
    RendererContractResponse,
    TestConnectorRequest,
    TestConnectorResponse,
)

router = APIRouter(prefix="/flow-builder", tags=["flow-builder"])


@router.get("/templates")
async def templates() -> dict[str, list[dict]]:
    return {
        "templates": [
            template.model_dump(mode="json", exclude={"created_at", "updated_at"})
            for template in starter_templates()
        ]
    }


@router.get("/schema", response_model=FlowSchemaResponse)
async def schema() -> FlowSchemaResponse:
    return FlowSchemaResponse(json_schema=strict_flow_json_schema())


@router.get("/renderer-contract", response_model=RendererContractResponse)
async def renderer_contract_endpoint() -> RendererContractResponse:
    return RendererContractResponse(contract=renderer_contract())


@router.post("/generate", response_model=FlowGenerateResponse)
async def generate(
    request: FlowGenerateRequest,
    http_request: FastAPIRequest,
    settings: Settings = Depends(get_settings),
) -> FlowGenerateResponse:
    tenant_id = _resolve_tenant_id(http_request, request.tenant_id)
    safety_text = " ".join(
        [
            request.natural_language_request,
            request.target_industry,
            request.target_flow_type,
            str(request.regulatory_context or ""),
            request.product_context or "",
        ]
    )
    assessment = assess_text(safety_text)
    if assessment.should_block:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "Flow generation blocked by safety layer.",
                "safety_flags": assessment.flags,
            },
        )

    flow, metadata = await generate_draft_flow(
        settings=settings,
        natural_language_request=request.natural_language_request,
        target_industry=request.target_industry,
        target_flow_type=request.target_flow_type,
        regulatory_context=request.regulatory_context,
        required_fields=request.required_fields,
        optional_existing_schema=request.optional_existing_schema,
        product_context=request.product_context,
        tenant_id=tenant_id,
        created_by=request.created_by,
    )
    return FlowGenerateResponse(
        flow_json=flow.model_dump(mode="json"),
        assumptions_made=flow.assumptions,
        missing_requirements=flow.missing_requirements,
        risk_flags=sorted(set(flow.risk_flags + assessment.flags)),
        recommended_human_review_items=flow.recommended_human_review_items,
        generation_metadata=metadata,
    )


@router.post("/generate/stream")
async def generate_stream(
    request: FlowGenerateRequest,
    http_request: FastAPIRequest,
    settings: Settings = Depends(get_settings),
) -> StreamingResponse:
    tenant_id = _resolve_tenant_id(http_request, request.tenant_id)
    assessment = assess_text(
        " ".join(
            [
                request.natural_language_request,
                request.target_industry,
                request.target_flow_type,
                str(request.regulatory_context or ""),
                request.product_context or "",
            ]
        )
    )
    if assessment.should_block:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "Flow generation blocked by safety layer.",
                "safety_flags": assessment.flags,
            },
        )

    async def events() -> AsyncGenerator[str, None]:
        yield _sse(
            "generation_started",
            {
                "message": "Starting Tellus FlowBuilder draft generation.",
                "target_flow_type": request.target_flow_type,
                "tenant_id": tenant_id,
            },
        )
        yield _sse(
            "generation_note",
            {
                "message": (
                    "Generation is draft-only. Publishing requires bank human review approval."
                )
            },
        )
        yield _sse(
            "generation_note",
            {
                "message": (
                    "Using banking modernization templates and placeholder connectors; "
                    "CAPIT is not a FlowBuilder target."
                )
            },
        )
        flow, metadata = await generate_draft_flow(
            settings=settings,
            natural_language_request=request.natural_language_request,
            target_industry=request.target_industry,
            target_flow_type=request.target_flow_type,
            regulatory_context=request.regulatory_context,
            required_fields=request.required_fields,
            optional_existing_schema=request.optional_existing_schema,
            product_context=request.product_context,
            tenant_id=tenant_id,
            created_by=request.created_by,
        )
        yield _sse(
            "risk_flags",
            {
                "risk_flags": sorted(set(flow.risk_flags + assessment.flags)),
                "recommended_human_review_items": flow.recommended_human_review_items,
            },
        )
        yield _sse(
            "flow_draft",
            {
                "flow_json": flow.model_dump(mode="json"),
                "assumptions_made": flow.assumptions,
                "missing_requirements": flow.missing_requirements,
                "generation_metadata": metadata,
            },
        )
        yield _sse("generation_complete", {"flow_id": flow.flow_id, "status": flow.status})

    return StreamingResponse(events(), media_type="text/event-stream")


@router.post("/validate", response_model=FlowValidateResponse)
async def validate(request: FlowValidateRequest, http_request: FastAPIRequest) -> FlowValidateResponse:
    _assert_flow_json_tenant_scope(request.flow_json, _request_tenant_id(http_request))
    result = validate_flow_definition(request.flow_json)
    return FlowValidateResponse(**result.model_dump(mode="json"))


@router.post("/simulate", response_model=FlowSimulateResponse)
async def simulate(request: FlowSimulateRequest, http_request: FastAPIRequest) -> FlowSimulateResponse:
    _assert_flow_json_tenant_scope(request.flow_json, _request_tenant_id(http_request))
    result = simulate_flow(
        request.flow_json,
        test_answers=request.test_answers,
        mock_api_responses=request.mock_api_responses,
    )
    return FlowSimulateResponse(**result.model_dump(mode="json"))


@router.post("/evaluate-condition", response_model=EvaluateConditionResponse)
async def evaluate_condition_endpoint(
    request: EvaluateConditionRequest,
) -> EvaluateConditionResponse:
    return EvaluateConditionResponse(
        result=evaluate_condition(request.condition, request.sample_payload)
    )


@router.post("/test-connector", response_model=TestConnectorResponse)
async def test_connector_endpoint(
    request: TestConnectorRequest,
    http_request: FastAPIRequest,
) -> TestConnectorResponse:
    tenant_id = _request_tenant_id(http_request)
    try:
        result = execute_connector_test(
            request.connector,
            input_payload=request.input_payload,
            mock_response=request.mock_api_response,
            mock_mode=request.mock_mode,
            actor=request.actor,
            flow_id=request.flow_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if result.success:
        FLOW_REPOSITORY.append_audit(
            flow_id=request.flow_id,
            tenant_id=tenant_id,
            event_type="api_action_executed",
            actor=request.actor,
            metadata={"connector_id": request.connector.connector_id, "mock_mode": request.mock_mode},
        )
    return TestConnectorResponse(**result.model_dump(mode="json"))


@router.post("/publish", response_model=PublishFlowResponse)
async def publish(request: PublishFlowRequest, http_request: FastAPIRequest) -> PublishFlowResponse:
    tenant_id = _request_tenant_id(http_request)
    flow = _flow_from_publish_request(request, tenant_id)
    if tenant_id is not None and flow.tenant_id is None:
        flow.tenant_id = tenant_id
    try:
        published = FLOW_REPOSITORY.publish(
            flow,
            review_approved=request.review_approved,
            reviewed_by=request.reviewed_by,
            review_notes=request.review_notes,
        )
    except FlowPublishError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    response = flow_response_with_audit(published, tenant_id=tenant_id)
    return PublishFlowResponse(
        flow_json=response["flow"],
        version=published.version,
        status=published.status,
        audit_events=response["audit_events"],
    )


@router.get("/{flow_id}/versions", response_model=FlowVersionsResponse)
async def versions(flow_id: str, http_request: FastAPIRequest) -> FlowVersionsResponse:
    tenant_id = _request_tenant_id(http_request)
    return FlowVersionsResponse(
        flow_id=flow_id,
        versions=[
            record.model_dump(mode="json")
            for record in FLOW_REPOSITORY.versions(flow_id, tenant_id=tenant_id)
        ],
    )


@router.get("/{flow_id}", response_model=FlowGetResponse)
async def get_flow(flow_id: str, http_request: FastAPIRequest) -> FlowGetResponse:
    tenant_id = _request_tenant_id(http_request)
    flow = FLOW_REPOSITORY.get_flow(flow_id, tenant_id=tenant_id)
    if not flow:
        raise HTTPException(status_code=404, detail="Flow not found.")
    response = flow_response_with_audit(flow, tenant_id=tenant_id)
    return FlowGetResponse(flow_json=response["flow"], audit_events=response["audit_events"])


def _flow_from_publish_request(
    request: PublishFlowRequest,
    tenant_id: str | None = None,
) -> FlowDefinition:
    if request.flow_json:
        _assert_flow_json_tenant_scope(request.flow_json, tenant_id)
        return FlowDefinition.model_validate(request.flow_json)
    if request.flow_id:
        flow = FLOW_REPOSITORY.get_flow(request.flow_id, tenant_id=tenant_id)
        if flow:
            return flow
        raise HTTPException(status_code=404, detail="Flow not found.")
    raise HTTPException(status_code=400, detail="flow_id or flow_json is required.")


def _request_tenant_id(request: FastAPIRequest) -> str | None:
    return getattr(request.state, "tenant_id", None)


def _resolve_tenant_id(request: FastAPIRequest, body_tenant_id: str | None) -> str | None:
    auth_tenant_id = _request_tenant_id(request)
    if auth_tenant_id and body_tenant_id and auth_tenant_id != body_tenant_id:
        raise HTTPException(status_code=403, detail="Request tenant does not match auth tenant.")
    return body_tenant_id or auth_tenant_id


def _assert_flow_json_tenant_scope(flow_json: dict, tenant_id: str | None) -> None:
    flow_tenant_id = flow_json.get("tenant_id")
    if tenant_id and flow_tenant_id and flow_tenant_id != tenant_id:
        raise HTTPException(status_code=403, detail="Flow tenant does not match auth tenant.")


def _sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"
