import asyncio
import os
from typing import Any

from services.api.adapters.base import AdapterResponse, ModelAdapter
from services.api.adapters.mock_adapter import MockAdapter
from services.api.adapters.qwen_coder_next import CODER_MODEL_CONFIG, CODER_MODEL_KEY
from services.api.adapters.qwen_general import get_general_model_config, normalize_general_model
from services.api.core.config import Settings
from services.api.core.telemetry import estimate_usage


class TransformersAdapter(ModelAdapter):
    """Local development adapter for Hugging Face Transformers.

    This intentionally keeps imports inside the request path so production installs do not need
    Transformers, Torch, or Accelerate unless this backend is selected.
    """

    name = "transformers"

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
        hf_model = self._resolve_model(model)

        try:
            content = await asyncio.to_thread(self._generate_sync, messages, hf_model, options)
            return AdapterResponse(
                content=content,
                model=hf_model,
                usage=estimate_usage(messages, content),
                raw={"backend": self.name},
            )
        except Exception as exc:  # pragma: no cover - depends on optional heavyweight packages
            if not self.settings.mock_fallback_enabled:
                raise
            fallback_options = dict(options)
            fallback_options["fallback_reason"] = f"transformers_unavailable:{exc.__class__.__name__}"
            return await self.mock.generate(messages, model, fallback_options)

    def _generate_sync(
        self,
        messages: list[dict[str, str]],
        hf_model: str,
        options: dict[str, Any],
    ) -> str:
        from transformers import AutoModelForCausalLM, AutoTokenizer

        os.environ.setdefault("HF_HOME", self.settings.transformers_cache_dir)
        tokenizer = AutoTokenizer.from_pretrained(
            hf_model,
            token=self.settings.hf_token,
            cache_dir=self.settings.transformers_cache_dir,
        )
        model = AutoModelForCausalLM.from_pretrained(
            hf_model,
            torch_dtype="auto",
            device_map="auto",
            token=self.settings.hf_token,
            cache_dir=self.settings.transformers_cache_dir,
        )
        text = tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
        )
        model_inputs = tokenizer([text], return_tensors="pt").to(model.device)
        output_ids = model.generate(
            **model_inputs,
            max_new_tokens=int(options.get("max_tokens", 512)),
            temperature=float(options.get("temperature", 0.2)),
        )
        generated_ids = output_ids[0][len(model_inputs.input_ids[0]) :]
        return tokenizer.decode(generated_ids, skip_special_tokens=True)

    def _resolve_model(self, model: str) -> str:
        if model == CODER_MODEL_KEY:
            return str(CODER_MODEL_CONFIG["hf_model_id"])

        normalized = normalize_general_model(model)
        return str(get_general_model_config(normalized)["hf_model_id"])

