# FlowBuilder API Connectors

FlowBuilder connector configuration supports safe placeholders for external API orchestration.

## Connector Fields

- `connector_id`
- `name`
- `base_url`
- `auth_type`: `none`, `api_key`, `bearer_token`, `oauth2`, `mTLS_placeholder`
- `auth_secret_name`
- `headers`
- `request_template`
- `response_mapping`
- `timeout_seconds`
- `retry_policy`
- `allowed_domains`
- `pii_allowed`
- `audit_logging_required`

## Secrets Handling

No real API keys, bearer tokens, OAuth client secrets, certificates, passwords, or credentials may
be stored in flow JSON. Credentials must be referenced by secret name only, such as:

```json
{
  "auth_type": "api_key",
  "auth_secret_name": "secret/tellus/kyc_api_key"
}
```

Headers such as `Authorization` or `X-API-Key` are rejected by validation because they risk storing
credentials directly in the workflow definition.

## Mock Connectors

`POST /flow-builder/test-connector` runs in mock mode by default. Live connector execution is
disabled in this MVP.
Mock connector tests create redacted audit events and do not persist vendor credentials.

Placeholder connector families:

- KYC API call.
- KYB API call.
- OFAC/sanctions screen.
- Core banking create-customer.
- Core banking create-account.
- Credit bureau soft-pull.
- Document verification.
- Fraud scoring.

## Example KYC Connector

```json
{
  "connector_id": "kyc_placeholder",
  "name": "KYC API placeholder",
  "base_url": "https://kyc.example.invalid/v1/checks",
  "auth_type": "api_key",
  "auth_secret_name": "secret/tellus/kyc_api_key",
  "request_template": {
    "method": "POST",
    "body": {
      "applicant_id": "{{applicant.id}}"
    }
  },
  "response_mapping": {
    "status": "kyc.status",
    "risk_score": "kyc.risk_score"
  },
  "allowed_domains": ["kyc.example.invalid"],
  "pii_allowed": true,
  "audit_logging_required": true
}
```
