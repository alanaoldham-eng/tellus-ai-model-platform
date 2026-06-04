# Licensing

This repository is for Tellus-owned wrapper code, prompts, safety logic, docs, tests, and deployment
scripts. It intentionally does not vendor model weights.

## Current Upstream Targets

As of June 4, 2026, the Hugging Face model cards for these targets advertise Apache-2.0 licensing:

- `Qwen/Qwen3-Coder-Next`: https://huggingface.co/Qwen/Qwen3-Coder-Next
- `Qwen/Qwen3-14B`: https://huggingface.co/Qwen/Qwen3-14B
- `Qwen/Qwen3-32B`: https://huggingface.co/Qwen/Qwen3-32B

Tellus must verify the exact upstream files for the revision used in production. Model cards and
license metadata can change.

## Required Preservation

For each deployed model revision, preserve:

- `LICENSE`.
- `NOTICE`, if present.
- `README.md` or model card.
- Attribution and citation files.
- Any license metadata included in the artifact.

Do not remove upstream copyright notices.

## Tellus Modifications

Tellus modifications should remain separate from upstream model code:

- Use API wrappers and adapters.
- Use prompt adapters and RAG before fine-tuning.
- Use submodules or documented clone scripts if upstream repos must be inspected.
- Avoid direct edits to upstream source unless there is a documented operational reason.

## Human Review

This documentation is not legal advice. Counsel or a qualified licensing reviewer should approve
the exact model, revision, deployment method, redistribution plan, and customer-facing terms before
production usage.

