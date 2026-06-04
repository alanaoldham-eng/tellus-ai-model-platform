# Deployment

## Local Development

```powershell
cd C:\Users\alana\OneDrive\Documents\Tellus\tellus-ai-model-platform
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
Copy-Item .env.example .env
uvicorn services.api.main:app --reload --host 127.0.0.1 --port 8000
```

## Docker

```powershell
Copy-Item .env.example .env
docker compose up --build api
```

## Ollama Backend

```powershell
ollama pull qwen3:14b
ollama pull qwen3:32b
```

```env
TELLUS_AI_INFERENCE_BACKEND=ollama
TELLUS_AI_OLLAMA_BASE_URL=http://localhost:11434
TELLUS_AI_OLLAMA_GENERAL_MODEL=qwen3:14b
```

Use an explicitly named local Ollama model for Qwen3-Coder-Next if needed:

```env
TELLUS_AI_OLLAMA_CODER_MODEL=qwen3-coder-next
```

## vLLM Backend

```env
TELLUS_AI_INFERENCE_BACKEND=vllm
TELLUS_AI_VLLM_BASE_URL=http://localhost:8001/v1
TELLUS_AI_VLLM_GENERAL_MODEL=Qwen/Qwen3-14B
TELLUS_AI_VLLM_CODER_MODEL=Qwen/Qwen3-Coder-Next
```

## llama.cpp Backend

Run a llama.cpp server outside this repo and point the API at it:

```env
TELLUS_AI_INFERENCE_BACKEND=llama_cpp
TELLUS_AI_LLAMA_CPP_BASE_URL=http://localhost:8080/v1
TELLUS_AI_LLAMA_CPP_GENERAL_MODEL=qwen3-14b
TELLUS_AI_LLAMA_CPP_CODER_MODEL=qwen3-coder-next
```

GGUF files must stay outside Git.

## Production Checklist

- Rotate `TELLUS_AI_API_KEY`.
- Disable prompt logging unless an approved privacy review allows it.
- Store model weights in external volumes.
- Pin upstream model revisions.
- Preserve upstream `LICENSE`, `NOTICE`, `README`, and model cards beside deployed artifacts.
- Add per-tenant rate limits and audit exports before public product traffic.

