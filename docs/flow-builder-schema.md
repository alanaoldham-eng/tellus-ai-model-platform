# FlowBuilder Schema

FlowBuilder uses portable JSON definitions represented by `FlowDefinition`.

## Flow Metadata

Required or supported metadata:

- `flow_id`
- `tenant_id`
- `name`
- `description`
- `industry`
- `flow_type`
- `version`
- `status`: `draft`, `review`, `published`, `archived`
- `created_by`
- `created_at`
- `updated_at`

## Steps

Each step supports:

- `step_id`
- `title`
- `description`
- `order`
- `visible_if`
- `sections`
- `fields`
- `actions`
- `next_step_logic`

## Fields

Supported field types:

- `text`
- `textarea`
- `email`
- `phone`
- `date`
- `number`
- `currency`
- `select`
- `multiselect`
- `radio`
- `checkbox`
- `address`
- `ssn_last4`
- `tax_id`
- `file_upload`
- `signature`
- `consent_checkbox`
- `disclosure_acknowledgment`
- `business_entity`
- `beneficial_owner`
- `api_lookup`
- `computed`

Fields support validation, conditional visibility, conditional enablement, options, data bindings,
PII classification, retention policy metadata, and audit requirements.

## Conditions

Supported operators:

- `equals`
- `not_equals`
- `contains`
- `greater_than`
- `less_than`
- `between`
- `exists`
- `not_exists`
- `in`
- `not_in`
- `and`
- `or`
- `not`

Example:

```json
{
  "operator": "not_equals",
  "field": "citizenship_status",
  "value": "US Citizen"
}
```

Example manual review routing:

```json
{
  "operator": "less_than",
  "field": "applicant_age",
  "value": 18
}
```

## Actions

Supported triggers:

- `on_step_load`
- `on_field_change`
- `on_step_submit`
- `before_final_submit`
- `after_final_submit`
- `on_manual_review`
- `on_decline`
- `on_approval`

Supported action types:

- `call_api`
- `set_field_value`
- `show_step`
- `hide_step`
- `route_to_step`
- `route_to_manual_review`
- `calculate_value`
- `create_audit_event`
- `generate_disclosure_packet`
- `require_human_review`
- `submit_application`

## JSON Schema

The runtime JSON schema is available from `FlowDefinition.model_json_schema()` in
`services/api/core/flow_builder/flow_schema.py`.

The stricter API export is available at:

```text
GET /flow-builder/schema
```

The exported schema includes a JSON Schema draft marker, Tellus contract metadata, and recursive
`additionalProperties=false` constraints for renderer and validation clients.

## Renderer Contract

Frontends should retrieve the renderer contract from:

```text
GET /flow-builder/renderer-contract
```

The contract identifies supported field types, action types, frontend events, submission payload
shape, accessibility requirements, and PII handling expectations for Tellus banking modernization
frontends. CAPIT is explicitly not a FlowBuilder target.
