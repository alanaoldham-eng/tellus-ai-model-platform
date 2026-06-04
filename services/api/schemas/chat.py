from typing import Any

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    product_context: str | None = None
    tenant_id: str | None = None
    system_prompt_override: str | None = None
    requested_model: str | None = None
    temperature: float = Field(default=0.2, ge=0.0, le=2.0)
    max_tokens: int = Field(default=1024, ge=1, le=8192)


class ChatResponse(BaseModel):
    assistant_response: str
    model_used: str
    safety_flags: list[str] = Field(default_factory=list)
    token_usage: dict[str, Any] | None = None

