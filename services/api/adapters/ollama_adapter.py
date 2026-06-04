from typing import Any

import httpx

from services.api.adapters.base import AdapterResponse, ModelAdapter
from services.api.adapters.mock_adapter import MockAdapter
from services.api.adapters.qwen_coder_next import CODER_MODEL_KEY
from services.api.adapters.qwen_general import normalize_general_model
from services.api.core.config import Settings


class OllamaAdapter(ModelAdapter):
    name = "ollama"

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
        ollama_model = self._resolve_model(model)
        payload = {
            "model": ollama_model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": options.get("temperature", 0.2),
            },
        }

        try:
            async with httpx.AsyncClient(timeout=self.settings.request_timeout_seconds) as client:
                response = await client.post(
                    f"{self.settings.ollama_base_url.rstrip('/')}/api/chat",
                    json=payload,
                )
                response.raise_for_status()
            data = response.json()
            content = data.get("message", {}).get("content") or data.get("response", "")
            usage = self._usage_from_response(data)
            return AdapterResponse(
                content=content,
                model=ollama_model,
                usage=usage,
                raw={"backend": self.name},
            )
        except Exception as exc:  # pragma: no cover - exercised through integration environments
            if not self.settings.mock_fallback_enabled:
                raise
            fallback_options = dict(options)
            fallback_options["fallback_reason"] = f"ollama_unavailable:{exc.__class__.__name__}"
            return await self.mock.generate(messages, model, fallback_options)

    def _resolve_model(self, model: str) -> str:
        if model == CODER_MODEL_KEY:
            return self.settings.ollama_coder_model or "qwen3-coder-next"

        general_model = normalize_general_model(model)
        if self.settings.ollama_general_model:
            return self.settings.ollama_general_model
        if general_model == "qwen3-32b":
            return "qwen3:32b"
        return "qwen3:14b"

    @staticmethod
    def _usage_from_response(data: dict[str, Any]) -> dict[str, int | str] | None:
        prompt_tokens = data.get("prompt_eval_count")
        completion_tokens = data.get("eval_count")
        if prompt_tokens is None and completion_tokens is None:
            return None
        prompt_tokens = int(prompt_tokens or 0)
        completion_tokens = int(completion_tokens or 0)
        return {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": prompt_tokens + completion_tokens,
            "source": "ollama",
        }

