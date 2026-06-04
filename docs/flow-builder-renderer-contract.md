# FlowBuilder Renderer Contract

Tellus FlowBuilder outputs portable JSON definitions. Banking modernization frontends should render
those definitions through the renderer contract exposed at:

```text
GET /flow-builder/renderer-contract
```

## Target Products

Target: Tellus banking modernization products.

Non-target: CAPIT.

## Renderer Responsibilities

- Render steps in ascending `order`.
- Evaluate `visible_if` and `enabled_if` before displaying steps, sections, and fields.
- Keep hidden fields out of user-visible review screens unless required by bank policy.
- Run client-side validation for visible required fields, then rely on backend validation before
  publish or submit.
- Display draft, review, published, and archived statuses clearly.
- Never display connector secret names to applicants.
- Never ask bank users or applicants to paste API credentials into a flow.
- Surface human-review warnings for regulated banking, lending, KYC, KYB, AML, OFAC, FCRA, ECOA,
  UDAAP, GLBA, privacy, and retention risks.

## Submission Payload

```json
{
  "flow_id": "flow_abc123",
  "flow_version": 1,
  "tenant_id": "bank_tenant",
  "answers": {
    "field_id": "answer value"
  },
  "renderer_metadata": {
    "renderer_name": "tellus-bank-workflow-renderer",
    "renderer_version": "0.1.0",
    "session_id": "session-id"
  }
}
```

## Frontend Events

- `flow_loaded`
- `step_viewed`
- `field_changed`
- `step_submitted`
- `manual_review_routed`
- `connector_mock_previewed`
- `application_submitted`

