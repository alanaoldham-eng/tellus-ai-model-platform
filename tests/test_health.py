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
    assert "Tellus AI Model Platform" in response.text
    assert "X-API-Key" in response.text


def test_favicon_is_public() -> None:
    response = client.get("/favicon.ico")

    assert response.status_code == 204


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
