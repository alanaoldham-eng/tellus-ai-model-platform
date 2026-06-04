from services.api.core.flow_builder.api_connector_engine import (
    execute_connector_test,
    placeholder_connectors,
    validate_connector_security,
)
from services.api.core.flow_builder.audit import AUDIT_LOG


def test_connector_mock_execution_succeeds() -> None:
    connector = placeholder_connectors()[0]

    result = execute_connector_test(
        connector,
        input_payload={"applicant_email": "alana@example.com"},
        mock_response={"status": "passed_placeholder"},
    )

    assert result.success is True
    assert result.mock_mode is True
    assert result.response["status"] == "passed_placeholder"
    assert result.request_preview["body"]["applicant_email"] == "[REDACTED_EMAIL]"


def test_connector_rejects_secret_headers() -> None:
    connector = placeholder_connectors()[0].model_copy(
        update={"headers": {"Authorization": "Bearer sk-thisisasecretthisisasecret"}}
    )

    errors = validate_connector_security(connector)

    assert errors
    assert "credentials" in errors[0] or "secret" in errors[0]


def test_audit_metadata_redacts_secrets_and_pii() -> None:
    event = AUDIT_LOG.append(
        flow_id="test_flow",
        event_type="api_action_executed",
        actor="tester",
        metadata={
            "email": "alana@example.com",
            "token": "hf_abcdefghijklmnopqrstuvwxyz123456",
        },
    )

    assert event.metadata["email"] == "[REDACTED_EMAIL]"
    assert event.metadata["token"] == "[REDACTED_HF_TOKEN]"
