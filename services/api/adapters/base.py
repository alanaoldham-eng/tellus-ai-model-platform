from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel, Field


class AdapterResponse(BaseModel):
    content: str
    model: str
    usage: dict[str, Any] | None = None
    safety_flags: list[str] = Field(default_factory=list)
    raw: dict[str, Any] | None = None


class ModelAdapter(ABC):
    name: str

    @abstractmethod
    async def generate(
        self,
        messages: list[dict[str, str]],
        model: str,
        options: dict[str, Any] | None = None,
    ) -> AdapterResponse:
        """Generate a model response from chat-style messages."""

