import pytest
from fastapi.testclient import TestClient

from services.api.core.config import Settings, get_settings
from services.api.core.flow_builder.ai_flow_generator import generate_draft_flow
from services.api.core.flow_builder.publishing import FLOW_REPOSITORY, FlowPublishError
from services.api.core.flow_builder.simulator import simulate_flow
from services.api.core.flow_builder.templates import consumer_checking_template
from services.api.core.flow_builder.validation_engine import validate_flow_definition
from services.api.main import app

client = TestClient(app)


def auth_headers() -> dict[str, str]:
    return {"X-API-Key": get_settings().api_key}


@pytest.mark.asyncio
async def test_generate_draft_flow_structure() -> None:
    flow, metadata = await generate_draft_flow(
        Settings(inference_backend="mock"),
        natural_language_request=(
            "Create a consumer checking onboarding flow with KYC, ID upload, "
            "residency questions for non-US citizens, and manual review for minors."
        ),
        target_industry="banking",
        target_flow_type="consumer_deposit_account_opening",
        regulatory_context=["KYC", "AML", "GLBA"],
        required_fields=["ssn_last4", "email", "government_id_upload"],
        tenant_id="tenant_test",
    )

    validation = validate_flow_definition(flow)

    assert flow.status == "draft"
    assert validation.valid is True
    assert any(connector.connector_id == "kyc_placeholder" for connector in flow.connectors)
    assert "template_guided_ai_assisted_draft" == metadata["generation_mode"]
    assert "human_review_required_before_publish" in flow.risk_flags


def test_simulation_routes_minor_to_manual_review() -> None:
    flow = consumer_checking_template()

    result = simulate_flow(flow, _complete_consumer_answers(applicant_age=17))

    assert result.final_status == "manual_review"
    assert "route_minor_to_manual_review" in {
        action["action_id"] for action in result.triggered_actions
    }


def test_simulation_shows_residency_fields_for_non_us_citizen() -> None:
    flow = consumer_checking_template()
    answers = _complete_consumer_answers(citizenship_status="Permanent Resident")
    answers["residency_status"] = "Permanent Resident"
    answers["country_of_citizenship"] = "Canada"

    result = simulate_flow(flow, answers)

    assert "residency_status" in result.visible_fields["eligibility"]
    assert "country_of_citizenship" in result.visible_fields["eligibility"]


def test_publishing_blocked_without_review_approval() -> None:
    flow = consumer_checking_template()
    flow.flow_id = "test_publish_blocked"

    with pytest.raises(FlowPublishError):
        FLOW_REPOSITORY.publish(flow, review_approved=False, reviewed_by="reviewer")


def test_flow_builder_endpoints_generate_simulate_publish_and_versions() -> None:
    generate_response = client.post(
        "/flow-builder/generate",
        headers=auth_headers(),
        json={
            "natural_language_request": "Create a consumer checking onboarding flow with KYC.",
            "target_industry": "banking",
            "target_flow_type": "consumer_deposit_account_opening",
            "regulatory_context": ["KYC", "AML", "GLBA"],
            "tenant_id": "tenant_endpoint_test",
        },
    )
    assert generate_response.status_code == 200
    flow_json = generate_response.json()["flow_json"]
    assert flow_json["status"] == "draft"

    validate_response = client.post(
        "/flow-builder/validate",
        headers=auth_headers(),
        json={"flow_json": flow_json},
    )
    assert validate_response.status_code == 200
    assert validate_response.json()["valid"] is True

    publish_blocked = client.post(
        "/flow-builder/publish",
        headers=auth_headers(),
        json={"flow_json": flow_json, "review_approved": False, "reviewed_by": "reviewer"},
    )
    assert publish_blocked.status_code == 400

    publish_response = client.post(
        "/flow-builder/publish",
        headers=auth_headers(),
        json={"flow_json": flow_json, "review_approved": True, "reviewed_by": "reviewer"},
    )
    assert publish_response.status_code == 200
    assert publish_response.json()["status"] == "published"

    versions_response = client.get(
        f"/flow-builder/{flow_json['flow_id']}/versions",
        headers=auth_headers(),
    )
    assert versions_response.status_code == 200
    assert len(versions_response.json()["versions"]) == 1

    get_response = client.get(
        f"/flow-builder/{flow_json['flow_id']}",
        headers=auth_headers(),
    )
    assert get_response.status_code == 200
    assert get_response.json()["flow_json"]["flow_id"] == flow_json["flow_id"]


def test_flow_builder_schema_and_renderer_contract_endpoints() -> None:
    schema_response = client.get("/flow-builder/schema", headers=auth_headers())

    assert schema_response.status_code == 200
    schema_body = schema_response.json()
    assert schema_body["strict"] is True
    assert schema_body["schema"]["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert schema_body["schema"]["x-tellus-publish-rules"]["renderer_target"] == (
        "banking_modernization_products"
    )

    renderer_response = client.get("/flow-builder/renderer-contract", headers=auth_headers())

    assert renderer_response.status_code == 200
    contract = renderer_response.json()["contract"]
    assert "banking_modernization" in contract["target_products"]
    assert "CAPIT" in contract["non_targets"]


def test_flow_builder_generate_stream_returns_notes_and_draft() -> None:
    with client.stream(
        "POST",
        "/flow-builder/generate/stream",
        headers=auth_headers(),
        json={
            "natural_language_request": "Create a loan prequalification workflow.",
            "target_industry": "banking",
            "target_flow_type": "loan_prequalification",
            "regulatory_context": ["FCRA", "ECOA"],
            "tenant_id": "tenant_stream_test",
        },
    ) as response:
        body = "".join(response.iter_text())

    assert response.status_code == 200
    assert "event: generation_note" in body
    assert "event: flow_draft" in body
    assert "CAPIT is not a FlowBuilder target" in body


def test_tenant_scoped_flow_reads_hide_other_tenant_flows() -> None:
    generate_response = client.post(
        "/flow-builder/generate",
        headers={**auth_headers(), "X-Tellus-Tenant-Id": "tenant_bank_a"},
        json={
            "natural_language_request": "Create a small business deposit onboarding flow.",
            "target_industry": "banking",
            "target_flow_type": "small_business_deposit_account_opening",
        },
    )
    assert generate_response.status_code == 200
    flow_id = generate_response.json()["flow_json"]["flow_id"]

    same_tenant_response = client.get(
        f"/flow-builder/{flow_id}",
        headers={**auth_headers(), "X-Tellus-Tenant-Id": "tenant_bank_a"},
    )
    assert same_tenant_response.status_code == 200

    other_tenant_response = client.get(
        f"/flow-builder/{flow_id}",
        headers={**auth_headers(), "X-Tellus-Tenant-Id": "tenant_bank_b"},
    )
    assert other_tenant_response.status_code == 404


def _complete_consumer_answers(
    applicant_age: int = 30,
    citizenship_status: str = "US Citizen",
) -> dict[str, object]:
    return {
        "citizenship_status": citizenship_status,
        "applicant_age": applicant_age,
        "first_name": "Alana",
        "last_name": "Oldham",
        "date_of_birth": "1990-01-01",
        "email": "alana@example.com",
        "phone": "555-555-1212",
        "physical_address": "123 Main St",
        "ssn_last4": "1234",
        "government_id_type": "Driver License",
        "government_id_number": "D1234567",
        "employment_status": "Employed",
        "annual_income": 100000,
        "funding_source": "Payroll",
        "deposit_account_disclosure_ack": True,
        "esign_consent": True,
        "privacy_notice_ack": True,
        "government_id_upload": "mock-document-id",
        "application_certification": True,
    }
