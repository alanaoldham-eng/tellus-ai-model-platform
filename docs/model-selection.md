# Model Selection

## Developer Workflows

Use `qwen3-coder-next` for:

- Coding.
- Repo analysis.
- Debugging.
- Pull request generation.
- DevOps.
- SQL generation.
- Architecture refactoring.
- Technical documentation.

Target upstream model: `Qwen/Qwen3-Coder-Next`.

## General Tellus Assistants

Use `qwen3-14b` by default for:

- General assistant workflows.
- Product support.
- Onboarding.
- User help.
- Internal business assistant workflows.
- Compliance assistant drafts.
- Customer-facing Q&A.

Target upstream model: `Qwen/Qwen3-14B`.

## Stronger General Reasoning

Use `qwen3-32b` only when the deployment has enough hardware and the task benefits from stronger
reasoning. It is configurable with:

```env
TELLUS_AI_DEFAULT_GENERAL_MODEL=qwen3-32b
```

Target upstream model: `Qwen/Qwen3-32B`.

## Routing Policy

The router selects Qwen3-Coder-Next for technical automation and Qwen3 14B or 32B for product and
business assistant tasks. Product-specific behavior should come from product context and prompt
adapters, not from editing upstream model code.

