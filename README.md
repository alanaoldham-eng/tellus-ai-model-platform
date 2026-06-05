# Tellus AI Model Platform

Tellus AI Model Platform is the internal API layer for using open-source Qwen models across Tellus Digital products without committing model weights into product repositories.

This repository contains Tellus-owned wrappers, adapters, prompt templates, safety checks, docs, eval fixtures, and deployment scripts. Model weights are downloaded separately into ignored local storage such as `models/`, `hf_cache/`, Ollama storage, or an external model volume.

## Supported Models

| Role | Default | Upstream target | Tellus use cases |
| --- | --- | --- | --- |
| Developer agent | `qwen3-coder-next` | `Qwen/Qwen3-Coder-Next` | Code assistance, repo analysis, PR review, DevOps, SQL generation, technical automation |
| General assistant | `qwen3-14b` | `Qwen/Qwen3-14B` | Product assistants, onboarding, user help, internal business assistant, compliance drafts |
| Stronger general reasoning | opt-in `qwen3-32b` | `Qwen/Qwen3-32B` | Heavier reasoning when hardware and cost allow |

The API starts with a mock fallback so Tellus apps can integrate immediately before local model runtimes are installed.

## Quick Start on Windows 11

From VS Code PowerShell:

```powershell
cd C:\Users\alana\OneDrive\Documents\Tellus\tellus-ai-model-platform
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e ".[dev]"
Copy-Item .env.example .env
uvicorn services.api.main:app --reload --host 127.0.0.1 --port 8000
```

Open [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health).

Run tests:

```powershell
pytest
```

## Example API Calls

Health does not require an API key:

```powershell
curl http://127.0.0.1:8000/health
```

Models:

```powershell
curl -H "X-API-Key: replace_me" http://127.0.0.1:8000/models
```

General chat:

```powershell
curl -X POST http://127.0.0.1:8000/chat `
  -H "Content-Type: application/json" `
  -H "X-API-Key: replace_me" `
  -d "{\"message\":\"Draft a concise onboarding note for Tellus BankBridge.\",\"product_context\":\"Tellus BankBridge\"}"
```

Code agent:

```powershell
curl -X POST http://127.0.0.1:8000/code-agent `
  -H "Content-Type: application/json" `
  -H "X-API-Key: replace_me" `
  -d "{\"repo_context\":\"FastAPI service\",\"task_instructions\":\"Review the health route and propose tests.\",\"file_snippets\":[],\"constraints\":[\"small diff\"]}"
```

## Runtime Backends

Set `TELLUS_AI_INFERENCE_BACKEND` to one of:

- `mock`: deterministic local responses for integration tests and early product wiring.
- `ollama`: calls a local Ollama server.
- `vllm`: calls an OpenAI-compatible vLLM server.
- `llama_cpp`: calls a llama.cpp OpenAI-compatible server.
- `transformers`: local Hugging Face Transformers, intended only for development.

The service does not require all runtimes to be installed. If a configured runtime is unavailable and `TELLUS_AI_MOCK_FALLBACK_ENABLED=true`, the API returns a mock response with a fallback safety flag.

## Ollama Configuration

Install Ollama separately, then pull models outside this Git repo:

```powershell
ollama pull qwen3:14b
ollama pull qwen3:32b
```

If you use a custom Qwen3-Coder-Next Ollama model name, set:

```env
TELLUS_AI_OLLAMA_CODER_MODEL=qwen3-coder-next
```

## vLLM Configuration

Run vLLM separately with model storage outside Git. For the public FlowBuilder demo on Vercel,
use a separate GPU inference endpoint; see [docs/qwen-vllm-inference-server.md](docs/qwen-vllm-inference-server.md).

```powershell
docker compose --profile vllm up vllm
```

Then set:

```env
TELLUS_AI_INFERENCE_BACKEND=vllm
TELLUS_AI_VLLM_BASE_URL=http://localhost:8001/v1
TELLUS_AI_VLLM_GENERAL_MODEL=Qwen/Qwen3-14B
TELLUS_AI_VLLM_CODER_MODEL=Qwen/Qwen3-Coder-Next
```

## Hugging Face Transformers Configuration

Transformers is local-dev only and may download large files into ignored cache/model directories:

```powershell
pip install -e ".[transformers]"
```

```env
TELLUS_AI_INFERENCE_BACKEND=transformers
TELLUS_AI_TRANSFORMERS_CACHE_DIR=./hf_cache
```

## Model Licensing and Usage Notes

## Repository License

Tellus-authored source code, prompts, adapters, orchestration logic, product workflows, documentation, and configuration in this repository are proprietary and confidential unless a specific file says otherwise.

Third-party open-source software, model artifacts, dependencies, and upstream materials remain governed by their own licenses. Those notices are tracked in `LICENSES/`, dependency manifests, model cards, and upstream repositories.

Tellus proprietary code in this repository is copyright Tellus Digital, LLC.
Unless a separate written agreement or file-level license says otherwise, the Tellus-authored code in this repository is proprietary and confidential.

This repository may integrate with Apache-2.0 licensed open model artifacts, including Qwen model artifacts such as `Qwen/Qwen3-Coder-Next`, `Qwen/Qwen3-14B`, and `Qwen/Qwen3-32B`, subject to verification of the exact upstream model card, `LICENSE`, `NOTICE`, and `README` files for the model revision actually deployed.

Use of upstream Apache-2.0 model artifacts does not automatically make Tellus-authored application code Apache-2.0. However, Tellus must comply with all applicable upstream license obligations when downloading, modifying, fine-tuning, deploying, or redistributing upstream model artifacts.

Required operating rules:

- Do not commit model weights, checkpoints, GGUF files, tokens, API keys, or local credentials.
- Preserve upstream `LICENSE`, `NOTICE`, `README`, model cards, and attribution files with downloaded or deployed model artifacts.
- Keep Tellus wrappers, prompts, adapters, product logic, and proprietary orchestration code separate from upstream model artifacts.
- Store upstream legal notes in `LICENSES/`.
- Use `scripts/clone_upstream_models.sh` or documented clone/download procedures when reviewing upstream metadata.
- Have counsel review commercial usage before production deployment or redistribution.


## Security Notes

- API key middleware protects all endpoints except `/health`.
- CORS is controlled by `TELLUS_AI_ALLOWED_ORIGINS`.
- Request bodies and prompts are not logged by default.
- Redaction helpers cover common secrets, private keys, wallet seed phrases, API keys, bearer tokens, email addresses, and phone numbers.
- Safety checks flag legal, financial, medical, private-key, security-bypass, malware, and credential-theft risks.

## Tellus App Integration

Tellus products should call this service as an internal API. Product-specific context should be passed in each request rather than hard-coded in model adapters.

Initial product targets:

- Tellus BankBridge
- CAPIT
- Human Layer / Work OS
- Tellus Comply
- Tellus Sustain
- Tellus Sign
- Tellus Gateway



## Roadmap

- Add RAG adapters for product docs and tenant-scoped evidence stores.
- Add streaming responses.
- Add structured tool-calling for developer workflows.
- Add per-tenant rate limits and audit event exports.
- Add production deployment manifests after infrastructure target selection.
- Add fine-tuning jobs only after RAG and prompt adapters are proven insufficient.

