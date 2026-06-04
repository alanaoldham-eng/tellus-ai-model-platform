# FlowBuilder Security

## Safeguards

- AI generation is draft-only.
- Human approval is required before publish.
- Every published flow receives a version record.
- Audit events are persisted in the MVP SQLite repository layer.
- Connector credentials are referenced by secret name only.
- No real vendor credentials are included.
- Sensitive log metadata is redacted before audit storage.
- Sensitive fields require PII classification and retention metadata.
- Regulated banking and lending flows include review warnings and risk flags.

## Audit Events

FlowBuilder records:

- `flow_generated`
- `flow_edited`
- `flow_reviewed`
- `flow_published`
- `flow_archived`
- `connector_added`
- `connector_changed`
- `api_action_executed`

The SQLite MVP is intended for local development and small controlled pilots. Production banking
modernization deployments should move the same repository interface to managed Postgres or another
approved durable store with backups, encryption, monitoring, and retention controls.

## PII Handling

Sensitive fields should be classified as:

- `moderate`
- `high`
- `restricted`

High and restricted fields require retention policy metadata. Restricted examples include SSN last
4, tax ID, beneficial owner data, signatures, uploaded identity documents, and government ID values.

## Regulatory Risk Warnings

FlowBuilder flags workflows involving banking, lending, KYC, KYB, AML, OFAC, FCRA, ECOA, UDAAP,
GLBA, privacy, disclosures, and data retention. These flags are prompts for review, not compliance
determinations.

## Model Safety Limits

The AI can help draft workflow configuration, but it must not:

- Claim a flow is legally compliant.
- Create prohibited-basis eligibility logic.
- Invent vendor credentials.
- Store secrets in flow JSON.
- Replace bank compliance, legal, risk, or security approval.
