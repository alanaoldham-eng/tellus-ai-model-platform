# Upstream Model License Notes

As of June 4, 2026, the Hugging Face model cards for the target Qwen models identify the license as
Apache-2.0. Tellus must verify and preserve the exact upstream files for the revision actually used
in production.

| Tellus model key | Upstream model | Current model-card license signal | Source |
| --- | --- | --- | --- |
| `qwen3-coder-next` | `Qwen/Qwen3-Coder-Next` | Apache-2.0 | https://huggingface.co/Qwen/Qwen3-Coder-Next |
| `qwen3-14b` | `Qwen/Qwen3-14B` | Apache-2.0 | https://huggingface.co/Qwen/Qwen3-14B |
| `qwen3-32b` | `Qwen/Qwen3-32B` | Apache-2.0 | https://huggingface.co/Qwen/Qwen3-32B |

## Production Review Checklist

- Pin the exact upstream revision or artifact digest.
- Preserve upstream `LICENSE`.
- Preserve upstream `NOTICE`, if present.
- Preserve upstream `README.md` or model card.
- Preserve citations and attribution text.
- Confirm commercial usage, redistribution, hosted inference, and customer-facing terms.
- Record reviewer, date, and approved deployment scope.

## Revision Ledger

Add entries here when a production model revision is approved.

| Date | Model | Revision or digest | Runtime | Reviewer | Notes |
| --- | --- | --- | --- | --- | --- |
| TBD | TBD | TBD | TBD | TBD | Pending legal/compliance review |

