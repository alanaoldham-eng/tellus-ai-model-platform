from typing import Any

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str
    environment: str
    backend: str
    enabled_model_roles: list[str]
    prompt_logging_enabled: bool


class ModelInfo(BaseModel):
    model_key: str
    display_name: str
    hf_model_id: str
    role: str
    backend: str
    default: bool
    use_cases: list[str] = Field(default_factory=list)


class ModelListResponse(BaseModel):
    backend: str
    models: list[ModelInfo]
    routing_notes: dict[str, Any]

