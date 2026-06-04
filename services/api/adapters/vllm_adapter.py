from typing import Any

import httpx

from services.api.adapters.base import AdapterResponse, ModelAdapter
from services.api.adapters.mock_adapter import MockAdapter
from services.api.adapters.qwen_coder_next import CODER_MODEL_CONFIG, CODER_MODEL_KEY
from services.api.adapters.qwen_general import get_general_model_config, normalize_general_model
from services.api.core.config import Settings


class VLLMAdapter(ModelAdapter):
    name = "vllm"

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.mock = MockAdapter()

    async def generate(
        self,
        messages: list[dict[str, str]],
        model: str,
        options: dict[str, Any] | None = None,
    ) -> AdapterResponse:
        options = options or {}
        vllm_model = self._resolve_model(model)
        payload = {
            "model": vllm_model,
            "messages": messages,
            "temperature": options.get("temperature", 0.2),
            "max_tokens": options.get("max_tokens", 1024),
        }
        headers: dict[str, str] = {}
        if self.settings.vllm_api_key:
            headers["Authorization"] = f"Bearer {self.settings.vllm_api_key}"

        try:
            async with httpx.AsyncClient(timeout=self.settings.request_timeout_seconds) as client:
                response = await client.post(
                    f"{self.settings.vllm_base_url.rstrip('/')}/chat/completions",
                    json=payload,
                    headers=headers,
                )
                response.raise_for_status()
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            return AdapterResponse(
                content=content,
                model=vllm_model,
                usage=data.get("usage"),
                raw={"backend": self.name, "id": data.get("id")},
            )
        except Exception as exc:  # pragma: no cover - exercised through integration environments
            if not self.settings.mock_fallback_enabled:
                raise
            fallback_options = dict(options)
            fallback_options["fallback_reason"] = f"vllm_unavailable:{exc.__class__.__name__}"
            return await self.mock.generate(messages, model, fallback_options)

    def _resolve_model(self, model: str) -> str:
        if model == CODER_MODEL_KEY:
            return self.settings.vllm_coder_model or str(CODER_MODEL_CONFIG["hf_model_id"])

        normalized = normalize_general_model(model)
        return self.settings.vllm_general_model or str(
            get_general_model_config(normalized)["hf_model_id"]
        )

