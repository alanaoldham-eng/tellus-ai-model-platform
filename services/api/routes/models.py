from fastapi import APIRouter, Depends

from services.api.core.config import Settings, get_settings
from services.api.core.model_router import ModelRouter
from services.api.schemas.models import ModelListResponse

router = APIRouter(tags=["models"])


@router.get("/models", response_model=ModelListResponse)
async def models(settings: Settings = Depends(get_settings)) -> ModelListResponse:
    router_service = ModelRouter(settings)
    return ModelListResponse(
        backend=settings.inference_backend,
        models=router_service.available_models(),
        routing_notes={
            "developer_workflows": [
                "coding",
                "repo analysis",
                "debugging",
                "pull request generation",
                "DevOps",
                "SQL generation",
                "architecture refactoring",
                "technical documentation",
            ],
            "general_workflows": [
                "general assistant",
                "product support",
                "onboarding",
                "user help",
                "internal business assistant",
                "compliance assistant drafts",
                "customer-facing Q&A",
            ],
        },
    )

