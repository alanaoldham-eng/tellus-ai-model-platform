from fastapi.testclient import TestClient

from services.api.core.config import get_settings
from services.api.main import app

client = TestClient(app)


def auth_headers() -> dict[str, str]:
    return {"X-API-Key": get_settings().api_key}


def test_health_returns_status() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["backend"] == "mock"
    assert "general_assistant" in body["enabled_model_roles"]
    assert "code_agent" in body["enabled_model_roles"]


def test_root_page_is_public() -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert "Tellus FlowBuilder API" in response.text
    assert "/flow-builder/demo" in response.text
    assert "X-API-Key" in response.text


def test_flow_builder_demo_page_is_public() -> None:
    response = client.get("/flow-builder/demo")

    assert response.status_code == 200
    assert "Tellus FlowBuilder Demo" in response.text
    assert "demo-form" in response.text
    assert "Generate Conditional Flow" in response.text
    assert "Run Flow Test" in response.text
    assert "Consumer Checking Account Onboarding" in response.text
    assert "No API keys in browser code" in response.text


def test_flow_builder_public_demo_generate_is_mock_only() -> None:
    response = client.post(
        "/flow-builder/demo/generate",
        json={
            "prompt": (
                "Create a small business onboarding flow with KYB, beneficial owners, "
                "documents, disclosures, OFAC, and manual review."
            ),
            "builder_options": {
                "flow_name": "Demo small business flow",
                "require_human_review": True,
            },
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["mode"] == "mock_public_demo"
    assert body["blocked"] is False
    assert body["selected_template"]["flow_type"] == "small_business_deposit_account_opening"
    assert body["flow_json"]["name"] == "Demo Draft: Demo small business flow"
    assert body["flow_json"]["status"] == "draft"
    assert "secret/tellus" not in response.text


def test_flow_builder_public_demo_simulates_conditional_flow() -> None:
    generate_response = client.post(
        "/flow-builder/demo/generate",
        json={
            "prompt": "Create a checking account flow with KYC and manual review for minors.",
            "target_flow_type": "consumer_deposit_account_opening",
        },
    )
    flow_json = generate_response.json()["flow_json"]

    simulate_response = client.post(
        "/flow-builder/demo/simulate",
        json={
            "flow_json": flow_json,
            "test_answers": {
                "citizenship_status": "US Citizen",
                "applicant_age": 17,
                "ssn_last4": "1234",
                "deposit_account_disclosure_ack": True,
                "esign_consent": True,
                "privacy_notice_ack": True,
            },
        },
    )

    assert simulate_response.status_code == 200
    body = simulate_response.json()
    assert body["mode"] == "mock_public_demo"
    assert body["final_status"] in {"manual_review", "incomplete"}
    assert "Eligibility" in body["visible_step_titles"]


def test_favicon_is_public() -> None:
    response = client.get("/favicon.ico")

    assert response.status_code == 204


def test_flow_builder_templates_still_requires_api_key() -> None:
    response = client.get("/flow-builder/templates")

    assert response.status_code == 401


def test_models_requires_api_key() -> None:
    response = client.get("/models")

    assert response.status_code == 401


def test_models_returns_configured_roles() -> None:
    response = client.get("/models", headers=auth_headers())

    assert response.status_code == 200
    body = response.json()
    model_keys = {model["model_key"] for model in body["models"]}
    assert {"qwen3-14b", "qwen3-32b", "qwen3-coder-next"}.issubset(model_keys)


def test_chat_works_with_mock_adapter() -> None:
    response = client.post(
        "/chat",
        headers=auth_headers(),
        json={
            "message": "Draft a short onboarding note.",
            "product_context": "Tellus Gateway",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert "Mock assistant response" in body["assistant_response"]
    assert "mock_response" in body["safety_flags"]
    assert body["token_usage"]["total_tokens"] > 0


def test_code_agent_works_with_mock_adapter() -> None:
    response = client.post(
        "/code-agent",
        headers=auth_headers(),
        json={
            "repo_context": "FastAPI service",
            "task_instructions": "Propose tests for the health route.",
            "file_snippets": [],
            "constraints": ["small diff"],
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["files_touched"] == []
    assert "mock_response" in body["safety_flags"]
    assert body["proposed_changes"]
