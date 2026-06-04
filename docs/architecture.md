# Architecture

Tellus AI Model Platform is an internal API facade between Tellus products and configured inference
backends.

The repo contains:

- FastAPI routes for health, model discovery, general chat, and developer-agent workflows.
- Model routing that maps product and task intent to Qwen model roles.
- Adapter interfaces for mock, Ollama, vLLM, llama.cpp, and local Transformers.
- Tellus-owned prompt templates.
- Safety, redaction, auth, logging, and deployment scaffolding.

The repo does not contain:

- Model weights.
- Fine-tuned checkpoints.
- Hugging Face tokens.
- Customer data.
- Vendor source edits.

## Request Flow

1. Tellus product calls the internal API with an API key.
2. Middleware applies CORS, API key validation, and request metadata logging.
3. The route assesses request safety before model invocation.
4. The prompt loader applies Tellus system prompts and product context.
5. The model router chooses the configured model role.
6. The selected backend adapter calls the runtime or falls back to mock when enabled.
7. The API returns content, model used, safety flags, and token usage when available.

## Separation From Upstream

Tellus code lives in `services/`, `prompts/`, `docs/`, `scripts/`, `evals/`, and `tests/`.
Upstream model metadata and weights must live outside Git or in ignored directories such as
`upstream/`, `models/`, or `hf_cache/`.

