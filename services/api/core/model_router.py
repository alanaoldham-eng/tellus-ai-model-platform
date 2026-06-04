from dataclasses import dataclass
from typing import Any

from services.api.adapters.base import AdapterResponse, ModelAdapter
from services.api.adapters.llama_cpp_adapter import LlamaCppAdapter
from services.api.adapters.mock_adapter import MockAdapter
from services.api.adapters.ollama_adapter import OllamaAdapter
from services.api.adapters.qwen_coder_next import CODER_MODEL_CONFIG, CODER_MODEL_KEY
from services.api.adapters.qwen_general import (
    GENERAL_MODELS,
    get_general_model_config,
    normalize_general_model,
)
from services.api.adapters.transformers_adapter import TransformersAdapter
from services.api.adapters.vllm_adapter import VLLMAdapter
from services.api.core.config import Settings


TECHNICAL_ROUTING_KEYWORDS = {
    "coding",
    "code",
    "repo analysis",
    "repository",
    "debugging",
    "debug",
    "pull request",
    "pr review",
    "devops",
    "sql",
    "architecture refactoring",
    "refactor",
    "technical documentation",
    "deployment",
}

GENERAL_ROUTING_KEYWORDS = {
    "general assistant",
    "product support",
    "onboarding",
    "user help",
    "business assistant",
    "compliance assistant",
    "customer-facing",
}


@dataclass(frozen=True)
class ModelRoute:
    role: str
    model_key: str
    hf_model_id: str
    backend: str
    use_cases: list[str]


class ModelRouter:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.adapter = self._build_adapter(settings.inference_backend)

    def select_for_chat(self, requested_model: str | None = None) -> ModelRoute:
        model_key = normalize_general_model(requested_model or self.settings.default_general_model)
        if model_key not in GENERAL_MODELS:
            model_key = "qwen3-14b"
        config = get_general_model_config(model_key)
        return ModelRoute(
            role="general_assistant",
            model_key=model_key,
            hf_model_id=str(config["hf_model_id"]),
            backend=self.settings.inference_backend,
            use_cases=list(config["use_cases"]),
        )

    def select_for_code_agent(self) -> ModelRoute:
        return ModelRoute(
            role="code_agent",
            model_key=CODER_MODEL_KEY,
            hf_model_id=str(CODER_MODEL_CONFIG["hf_model_id"]),
            backend=self.settings.inference_backend,
            use_cases=list(CODER_MODEL_CONFIG["use_cases"]),
        )

    def select_by_task(self, task_type: str, text: str = "") -> ModelRoute:
        normalized = f"{task_type} {text}".lower()
        if any(keyword in normalized for keyword in TECHNICAL_ROUTING_KEYWORDS):
            return self.select_for_code_agent()
        return self.select_for_chat()

    def available_models(self) -> list[dict[str, Any]]:
        models: list[dict[str, Any]] = []
        if self.settings.enable_general_assistant:
            for model_key, config in GENERAL_MODELS.items():
                models.append(
                    {
                        "model_key": model_key,
                        "display_name": config["display_name"],
                        "hf_model_id": config["hf_model_id"],
                        "role": config["role"],
                        "backend": self.settings.inference_backend,
                        "default": model_key == self.settings.default_general_model,
                        "use_cases": config["use_cases"],
                    }
                )
        if self.settings.enable_code_agent:
            models.append(
                {
                    "model_key": CODER_MODEL_KEY,
                    "display_name": CODER_MODEL_CONFIG["display_name"],
                    "hf_model_id": CODER_MODEL_CONFIG["hf_model_id"],
                    "role": CODER_MODEL_CONFIG["role"],
                    "backend": self.settings.inference_backend,
                    "default": True,
                    "use_cases": CODER_MODEL_CONFIG["use_cases"],
                }
            )
        return models

    async def generate(
        self,
        route: ModelRoute,
        messages: list[dict[str, str]],
        options: dict[str, Any] | None = None,
    ) -> AdapterResponse:
        return await self.adapter.generate(messages, route.model_key, options or {})

    def _build_adapter(self, backend: str) -> ModelAdapter:
        if backend == "ollama":
            return OllamaAdapter(self.settings)
        if backend == "vllm":
            return VLLMAdapter(self.settings)
        if backend == "llama_cpp":
            return LlamaCppAdapter(self.settings)
        if backend == "transformers":
            return TransformersAdapter(self.settings)
        return MockAdapter()
