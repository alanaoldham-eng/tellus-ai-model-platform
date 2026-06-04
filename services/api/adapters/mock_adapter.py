from typing import Any

from services.api.adapters.base import AdapterResponse, ModelAdapter
from services.api.core.telemetry import estimate_usage


class MockAdapter(ModelAdapter):
    name = "mock"

    async def generate(
        self,
        messages: list[dict[str, str]],
        model: str,
        options: dict[str, Any] | None = None,
    ) -> AdapterResponse:
        options = options or {}
        role = options.get("role", "general")
        fallback_reason = options.get("fallback_reason")

        if role == "code_agent":
            content = (
                "Mock code-agent response: no repository files were modified. I would first inspect "
                "the repo structure, identify the smallest reviewable change, run targeted tests, "
                "and report risks before proposing a diff."
            )
        else:
            product_context = options.get("product_context") or "Tellus"
            content = (
                f"Mock assistant response for {product_context}: I can help draft clear, "
                "business-safe guidance while flagging compliance-sensitive decisions for human review."
            )

        flags = ["mock_response"]
        if fallback_reason:
            flags.append("mock_fallback")

        return AdapterResponse(
            content=content,
            model=f"{model} ({self.name})",
            usage=estimate_usage(messages, content),
            safety_flags=flags,
            raw={"fallback_reason": fallback_reason} if fallback_reason else None,
        )

