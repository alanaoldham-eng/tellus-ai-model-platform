from __future__ import annotations

from typing import Any
from urllib.parse import urlparse

from pydantic import BaseModel, Field

from services.api.core.flow_builder.audit import AUDIT_LOG
from services.api.core.flow_builder.flow_schema import ConnectorConfig
from services.api.core.safety import redact_sensitive_text


SENSITIVE_HEADER_NAMES = {"authorization", "x-api-key", "api-key", "token", "secret", "password"}


class ConnectorExecutionResult(BaseModel):
    connector_id: str
    success: bool
    mock_mode: bool
    request_preview: dict[str, Any]
    response: dict[str, Any]
    warnings: list[str] = Field(default_factory=list)


def validate_connector_security(connector: ConnectorConfig) -> list[str]:
    errors: list[str] = []
    parsed = urlparse(connector.base_url)
    domain = parsed.hostname or ""

    if connector.allowed_domains and domain not in connector.allowed_domains:
        errors.append("base_url domain is not present in allowed_domains")

    for key, value in connector.headers.items():
        key_lower = key.lower()
        if key_lower in SENSITIVE_HEADER_NAMES or "auth" in key_lower:
            errors.append(f"header {key} must not contain credentials in flow JSON")
        if redact_sensitive_text(value) != value:
            errors.append(f"header {key} appears to contain a secret")

    flattened_template = str(connector.request_template)
    if redact_sensitive_text(flattened_template) != flattened_template:
        errors.append("request_template appears to contain a secret")

    return errors


def execute_connector_test(
    connector: ConnectorConfig,
    input_payload: dict[str, Any] | None = None,
    mock_response: dict[str, Any] | None = None,
    mock_mode: bool = True,
    actor: str = "flow_builder",
    flow_id: str = "connector_test",
) -> ConnectorExecutionResult:
    if not mock_mode:
        raise ValueError("Live connector execution is disabled in this MVP. Use mock_mode=true.")

    errors = validate_connector_security(connector)
    if errors:
        return ConnectorExecutionResult(
            connector_id=connector.connector_id,
            success=False,
            mock_mode=True,
            request_preview={},
            response={},
            warnings=errors,
        )

    preview = {
        "method": connector.request_template.get("method", "POST"),
        "url": connector.base_url,
        "headers": redact_payload(connector.headers),
        "body": redact_payload(input_payload or connector.request_template.get("body", {})),
        "timeout_seconds": connector.timeout_seconds,
    }
    response = mock_response or _default_mock_response(connector.connector_id)

    AUDIT_LOG.append(
        flow_id=flow_id,
        event_type="api_action_executed",
        actor=actor,
        metadata={"connector_id": connector.connector_id, "mock_mode": True, "request": preview},
    )
    return ConnectorExecutionResult(
        connector_id=connector.connector_id,
        success=True,
        mock_mode=True,
        request_preview=preview,
        response=response,
        warnings=["mock_connector_execution_only"],
    )


def placeholder_connectors() -> list[ConnectorConfig]:
    return [
        ConnectorConfig(
            connector_id="kyc_placeholder",
            name="KYC API placeholder",
            base_url="https://kyc.example.invalid/v1/checks",
            auth_type="api_key",
            auth_secret_name="secret/tellus/kyc_api_key",
            request_template={"method": "POST", "body": {"applicant_id": "{{applicant.id}}"}},
            response_mapping={"status": "kyc.status", "risk_score": "kyc.risk_score"},
            allowed_domains=["kyc.example.invalid"],
            pii_allowed=True,
        ),
        ConnectorConfig(
            connector_id="kyb_placeholder",
            name="KYB API placeholder",
            base_url="https://kyb.example.invalid/v1/businesses",
            auth_type="bearer_token",
            auth_secret_name="secret/tellus/kyb_bearer_token",
            request_template={"method": "POST", "body": {"business_id": "{{business.id}}"}},
            response_mapping={"status": "kyb.status"},
            allowed_domains=["kyb.example.invalid"],
            pii_allowed=True,
        ),
        ConnectorConfig(
            connector_id="ofac_sanctions_placeholder",
            name="OFAC sanctions placeholder",
            base_url="https://sanctions.example.invalid/v1/screen",
            auth_type="api_key",
            auth_secret_name="secret/tellus/ofac_api_key",
            request_template={"method": "POST", "body": {"name": "{{applicant.name}}"}},
            response_mapping={"match_status": "sanctions.match_status"},
            allowed_domains=["sanctions.example.invalid"],
            pii_allowed=True,
        ),
        ConnectorConfig(
            connector_id="core_create_customer_placeholder",
            name="Core banking create-customer placeholder",
            base_url="https://core.example.invalid/v1/customers",
            auth_type="oauth2",
            auth_secret_name="secret/tellus/core_oauth_client",
            request_template={"method": "POST", "body": {"application_id": "{{application.id}}"}},
            response_mapping={"customer_id": "core.customer_id"},
            allowed_domains=["core.example.invalid"],
            pii_allowed=True,
        ),
        ConnectorConfig(
            connector_id="core_create_account_placeholder",
            name="Core banking create-account placeholder",
            base_url="https://core.example.invalid/v1/accounts",
            auth_type="oauth2",
            auth_secret_name="secret/tellus/core_oauth_client",
            request_template={"method": "POST", "body": {"customer_id": "{{core.customer_id}}"}},
            response_mapping={"account_id": "core.account_id"},
            allowed_domains=["core.example.invalid"],
            pii_allowed=True,
        ),
        ConnectorConfig(
            connector_id="credit_bureau_placeholder",
            name="Credit bureau placeholder",
            base_url="https://credit.example.invalid/v1/soft-pull",
            auth_type="api_key",
            auth_secret_name="secret/tellus/credit_bureau_api_key",
            request_template={"method": "POST", "body": {"applicant_id": "{{applicant.id}}"}},
            response_mapping={"score_band": "credit.score_band"},
            allowed_domains=["credit.example.invalid"],
            pii_allowed=True,
        ),
        ConnectorConfig(
            connector_id="document_verification_placeholder",
            name="Document verification placeholder",
            base_url="https://documents.example.invalid/v1/verify",
            auth_type="bearer_token",
            auth_secret_name="secret/tellus/document_verification_token",
            request_template={"method": "POST", "body": {"document_id": "{{documents.id}}"}},
            response_mapping={"status": "documents.verification_status"},
            allowed_domains=["documents.example.invalid"],
            pii_allowed=True,
        ),
        ConnectorConfig(
            connector_id="fraud_scoring_placeholder",
            name="Fraud scoring placeholder",
            base_url="https://fraud.example.invalid/v1/score",
            auth_type="api_key",
            auth_secret_name="secret/tellus/fraud_api_key",
            request_template={"method": "POST", "body": {"application_id": "{{application.id}}"}},
            response_mapping={"risk_band": "fraud.risk_band"},
            allowed_domains=["fraud.example.invalid"],
            pii_allowed=True,
        ),
    ]


def redact_payload(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: redact_payload(child) for key, child in value.items()}
    if isinstance(value, list):
        return [redact_payload(child) for child in value]
    if isinstance(value, str):
        return redact_sensitive_text(value)
    return value


def _default_mock_response(connector_id: str) -> dict[str, Any]:
    if "kyc" in connector_id:
        return {"status": "passed_placeholder", "risk_score": 12}
    if "kyb" in connector_id:
        return {"status": "manual_review_placeholder"}
    if "credit" in connector_id:
        return {"score_band": "prequalified_placeholder"}
    if "fraud" in connector_id:
        return {"risk_band": "low_placeholder"}
    return {"status": "mock_success"}
