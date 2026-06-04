# Tellus FlowBuilder

Tellus FlowBuilder is an AI-assisted regulated workflow builder for banks, fintechs, and regulated
organizations. It creates portable JSON workflow definitions that Tellus frontends can render later.
Its initial product target is Tellus banking modernization, not CAPIT.

This is not just a form builder. It is a configurable onboarding, origination, compliance-aware
intake, API orchestration, human review, and audit trail foundation.

## Initial Banking Use Cases

- New deposit account opening.
- Loan prequalification.
- Small business onboarding.
- KYC and KYB intake.
- Beneficial ownership collection.
- Document upload flows.
- Consent and disclosure capture.
- Existing customer product applications.
- Internal review workflows.

## Flow Lifecycle

1. Generate a draft from natural language.
2. Validate schema, connector safety, PII metadata, and regulated-flow warnings.
3. Simulate with test answers and mock API responses.
4. Review with bank compliance, legal, risk, operations, and security teams.
5. Publish only after explicit human approval.
6. Version every published flow.
7. Retain immutable audit events for generation, edits, review, publishing, archiving, connector
   changes, and API action execution.

## Persistent Store

The MVP uses SQLite through `TELLUS_AI_FLOW_STORE_PATH`, defaulting to
`./data/flow_builder.sqlite3`. The `data/` directory is ignored by Git and mounted by Docker
Compose. For Vercel or serverless runtime, set the path to writable runtime storage or replace the
repository with managed Postgres before production.

## Tenant-Scoped Access

FlowBuilder supports tenant-aware API access:

- `X-Tellus-Tenant-Id` scopes flow reads, versions, publish, validate, and simulate operations.
- `TELLUS_AI_TENANT_API_KEYS` can map tenant IDs to API keys.
- `TELLUS_AI_REQUIRE_TENANT_HEADER=true` can require all non-health requests to include tenant
  context.

## AI-Assisted Generation

`POST /flow-builder/generate` creates a draft flow. It does not publish. The generator starts from
banking templates and adds assumptions, missing requirements, risk flags, and recommended review
items. Model notes are optional and must never override schema validation or human review.

`POST /flow-builder/generate/stream` returns server-sent events with generation notes, risk flags,
and the final draft flow payload.

## Human Review

Publishing requires:

- `review_approved=true`.
- A reviewer identity.
- Validation with no blocking errors.

The published flow remains a configuration artifact. It is not a legal, compliance, lending, KYC,
KYB, AML, OFAC, FCRA, ECOA, UDAAP, GLBA, or privacy determination.
