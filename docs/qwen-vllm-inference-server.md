# Qwen vLLM Inference Server Setup

Tellus AI Model Platform runs on Vercel, but Vercel should not host Qwen model weights. The
production pattern is:

1. Host Qwen on a GPU inference service.
2. Expose an OpenAI-compatible vLLM `/v1` API.
3. Store that endpoint URL and API key in Vercel environment variables.
4. Let the public FlowBuilder demo call the model through the FastAPI server, never from browser
   JavaScript.

## Recommended First Path: RunPod Serverless vLLM

RunPod's vLLM workers expose an OpenAI-compatible API. The base URL format is:

```text
https://api.runpod.ai/v2/<ENDPOINT_ID>/openai/v1
```

Use that whole value as:

```text
TELLUS_AI_VLLM_BASE_URL=https://api.runpod.ai/v2/<ENDPOINT_ID>/openai/v1
```

Do not append `/chat/completions`; the Tellus adapter appends that path.

### 1. Create Required Accounts and Tokens

- Create or open a RunPod account.
- Create a RunPod API key.
- Create a Hugging Face read token if the model or deployment flow requires one.
- Do not commit either token to Git.

### 2. Create a vLLM Endpoint

In RunPod:

1. Open the vLLM Serverless deployment flow.
2. Select the latest vLLM worker/template.
3. Set the model to:

```text
Qwen/Qwen3-14B
```

4. Set max model length to `8192` for the first demo. This reduces memory pressure and is enough
   for FlowBuilder prompts.
5. Choose a GPU with enough VRAM. For the first working deployment, prefer a 48 GB or 80 GB GPU
   class. After it works, optimize cost with quantized variants or lower context.
6. Add `HF_TOKEN` as a secret/environment variable if needed.
7. Create the endpoint and wait for the model to initialize.

### 3. Record Endpoint Settings

After RunPod creates the endpoint, record:

```text
ENDPOINT_ID=<your RunPod endpoint id>
RUNPOD_API_KEY=<your RunPod API key>
```

Your Tellus values become:

```text
TELLUS_AI_INFERENCE_BACKEND=vllm
TELLUS_AI_VLLM_BASE_URL=https://api.runpod.ai/v2/<ENDPOINT_ID>/openai/v1
TELLUS_AI_VLLM_API_KEY=<RUNPOD_API_KEY>
TELLUS_AI_VLLM_GENERAL_MODEL=Qwen/Qwen3-14B
TELLUS_AI_ENABLE_PUBLIC_MODEL_DEMO=true
```

### 4. Test the vLLM Endpoint Before Vercel

From this repo:

```powershell
$env:TELLUS_AI_VLLM_BASE_URL = "https://api.runpod.ai/v2/<ENDPOINT_ID>/openai/v1"
$env:TELLUS_AI_VLLM_API_KEY = "<RUNPOD_API_KEY>"
$env:TELLUS_AI_VLLM_GENERAL_MODEL = "Qwen/Qwen3-14B"

.\scripts\test_vllm_endpoint.ps1
```

Expected result:

- `/models` returns a model list.
- `/chat/completions` returns assistant text.

### 5. Set Vercel Environment Variables

In Vercel Project Settings > Environment Variables, set:

```text
TELLUS_AI_ENABLE_PUBLIC_MODEL_DEMO=true
TELLUS_AI_INFERENCE_BACKEND=vllm
TELLUS_AI_VLLM_BASE_URL=https://api.runpod.ai/v2/<ENDPOINT_ID>/openai/v1
TELLUS_AI_VLLM_API_KEY=<RUNPOD_API_KEY>
TELLUS_AI_VLLM_GENERAL_MODEL=Qwen/Qwen3-14B
TELLUS_AI_PUBLIC_DEMO_RATE_LIMIT_PER_MINUTE=6
TELLUS_AI_PUBLIC_DEMO_MAX_PROMPT_CHARS=1200
TELLUS_AI_PUBLIC_DEMO_ALLOWED_ORIGINS=https://tellus-ai-model-platform.vercel.app,https://www.tellusdigital.io
```

Redeploy the Vercel project after changing environment variables.

## Alternative: GPU VM or Pod with Docker

If you use a GPU VM instead of RunPod Serverless, run the official vLLM OpenAI-compatible Docker
image on a GPU host:

```bash
docker run --runtime nvidia --gpus all \
  -v ~/.cache/huggingface:/root/.cache/huggingface \
  --env "HF_TOKEN=$HF_TOKEN" \
  -p 8000:8000 \
  --ipc=host \
  vllm/vllm-openai:latest \
  --model Qwen/Qwen3-14B \
  --served-model-name Qwen/Qwen3-14B \
  --max-model-len 8192 \
  --gpu-memory-utilization 0.90
```

Put a TLS proxy in front of it, then set:

```text
TELLUS_AI_VLLM_BASE_URL=https://qwen-vllm.yourdomain.com/v1
```

Do not expose an unauthenticated vLLM server publicly. Require a bearer token or put it behind a
private network/API gateway.

## Cost and Sizing Notes

- Use `Qwen/Qwen3-14B` first for the public demo.
- Keep max model length modest (`8192`) until the demo is stable.
- Prefer 48 GB+ VRAM for the first full-precision deployment.
- Consider an AWQ/GPTQ quantized Qwen variant later if cost becomes an issue, but verify the exact
  Hugging Face model ID and license before switching.
- Keep `TELLUS_AI_PUBLIC_DEMO_RATE_LIMIT_PER_MINUTE` low for public traffic.
- Watch RunPod/Vercel logs during first launch; model cold starts can take several minutes.

## Troubleshooting

### Vercel still shows fallback mode

Check `/flow-builder/demo` and generate a flow. If the status says template fallback, inspect
`generation_metadata.fallback_reason` in the network response.

Common reasons:

- `TELLUS_AI_ENABLE_PUBLIC_MODEL_DEMO` is not `true`.
- `TELLUS_AI_INFERENCE_BACKEND` is still `mock`.
- `TELLUS_AI_VLLM_BASE_URL` is wrong.
- `TELLUS_AI_VLLM_API_KEY` is missing or invalid.
- RunPod endpoint is still cold-starting.
- The model returned non-JSON and the server rejected the plan.

### RunPod returns invalid model

Make sure `TELLUS_AI_VLLM_GENERAL_MODEL` matches the deployed model name or the served model name
configured in the vLLM endpoint.

### Timeouts

Increase:

```text
TELLUS_AI_REQUEST_TIMEOUT_SECONDS=120
```

Then redeploy.

## References

- RunPod vLLM OpenAI compatibility: https://docs.runpod.io/serverless/vllm/openai-compatibility
- RunPod vLLM setup: https://docs.runpod.io/serverless/vllm/get-started
- vLLM Docker deployment: https://docs.vllm.ai/en/latest/deployment/docker/
- Modal OpenAI-compatible vLLM example: https://modal.com/docs/examples/vllm_inference
