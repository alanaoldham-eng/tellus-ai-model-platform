# Fine-Tuning

Fine-tuning is intentionally scaffolded but disabled by default.

```env
TELLUS_AI_ENABLE_FINE_TUNING=false
```

## Prefer RAG and Prompt Adapters First

Tellus should fine-tune only after simpler approaches fail:

1. Improve Tellus system prompts.
2. Add product-specific prompt adapters.
3. Add retrieval augmented generation for product docs, policies, evidence stores, or tenant data.
4. Evaluate quality and safety.
5. Consider fine-tuning only for repeated patterns that RAG and prompting cannot solve.

## Good Fine-Tuning Candidates

- Stable house style for support responses.
- Structured developer-agent outputs.
- Compliance summary formatting.
- Product-specific classifications with low legal risk.

## Bad Fine-Tuning Candidates

- Raw client data.
- Secrets, tokens, keys, wallet seed phrases, or private credentials.
- Unreviewed legal, medical, financial, or regulatory advice.
- One-off product context that belongs in RAG.

## Data Format

Use JSONL chat examples:

```json
{"messages":[{"role":"system","content":"Tellus-safe system prompt."},{"role":"user","content":"User request."},{"role":"assistant","content":"Approved response."}],"metadata":{"product":"Tellus Comply","reviewed":true,"source":"internal_example_v1"}}
```

## Data Preparation

- Remove client identifiers unless explicitly approved.
- Redact PII and secrets.
- Label examples by product, tenant scope, reviewer, and date.
- Store review status.
- Keep rejected examples for evals, not training, unless transformed into safe counterexamples.

## Versioning

Fine-tuned adapters should be versioned independently from base models:

- Base model ID and revision.
- Adapter training dataset version.
- Training code version.
- Evaluation report.
- License review status.

Base model licenses and notices must remain intact.

