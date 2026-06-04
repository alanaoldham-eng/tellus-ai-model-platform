from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from services.api.core.config import get_settings
from services.api.core.logging import RequestLoggingMiddleware, configure_logging
from services.api.core.security import APIKeyMiddleware
from services.api.routes import chat, code_agent, health, models

settings = get_settings()
configure_logging(settings)

app = FastAPI(
    title="Tellus AI Model Platform",
    version="0.1.0",
    description="Internal API for Tellus Qwen model routing, adapters, prompts, and safety.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-API-Key"],
)
app.add_middleware(RequestLoggingMiddleware, settings=settings)
app.add_middleware(APIKeyMiddleware, settings=settings)

app.include_router(health.router)
app.include_router(models.router)
app.include_router(chat.router)
app.include_router(code_agent.router)

