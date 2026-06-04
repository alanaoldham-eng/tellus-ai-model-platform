# Tellus Integration

Tellus apps should call this platform as an internal service rather than importing model runtime
code directly.

## Product Context

Pass product context in each request:

- `CAPIT`.
- `Human Layer / Work OS`.
- `Tellus Comply`.
- `Tellus Sustain`.
- `Tellus Sign`.
- `Tellus Gateway`.

`LesBiGulfFriends.com` is out of scope unless explicitly enabled later.

## Chat Request

```json
{
  "message": "Draft an onboarding summary for Tellus Gateway.",
  "product_context": "Tellus Gateway",
  "tenant_id": "optional-tenant-id"
}
```

## Code Agent Request

```json
{
  "repo_context": "FastAPI service with routes and tests.",
  "task_instructions": "Review the model router and propose tests.",
  "file_snippets": [],
  "constraints": ["small reviewable changes"]
}
```

## Response Handling

Tellus apps should:

- Display safety flags in internal tooling.
- Treat compliance, legal, medical, financial, and certification content as drafts.
- Keep human review in workflows where required.
- Avoid storing prompts or outputs containing tenant secrets.

