from fastapi import APIRouter, Depends

from services.api.core.config import Settings, get_settings
from services.api.schemas.models import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health(settings: Settings = Depends(get_settings)) -> HealthResponse:
    return HealthResponse(
        status="ok",
        environment=settings.env,
        backend=settings.inference_backend,
        enabled_model_roles=settings.enabled_roles,
        prompt_logging_enabled=settings.enable_prompt_logging,
    )

