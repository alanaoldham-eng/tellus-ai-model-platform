from fastapi import Depends, FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from services.api.core.config import Settings, get_settings
from services.api.core.logging import RequestLoggingMiddleware, configure_logging
from services.api.core.public_demo import (
    FlowBuilderDemoGenerateRequest,
    FlowBuilderDemoSimulateRequest,
    build_flow_builder_demo,
    simulate_flow_builder_demo,
)
from services.api.core.public_pages import flow_builder_demo_page, landing_page
from services.api.core.security import APIKeyMiddleware
from services.api.routes import chat, code_agent, flow_builder, health, models

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
    allow_headers=["Authorization", "Content-Type", "X-API-Key", "X-Tellus-Tenant-Id"],
)
app.add_middleware(RequestLoggingMiddleware, settings=settings)
app.add_middleware(APIKeyMiddleware, settings=settings)


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def root() -> str:
    return landing_page()


@app.get("/flow-builder/demo", response_class=HTMLResponse, include_in_schema=False)
async def flow_builder_demo() -> str:
    return flow_builder_demo_page()


@app.post("/flow-builder/demo/generate", include_in_schema=False)
async def flow_builder_demo_generate(
    payload: FlowBuilderDemoGenerateRequest,
    request: Request,
    settings: Settings = Depends(get_settings),
) -> dict:
    return await build_flow_builder_demo(settings, payload, request)


@app.post("/flow-builder/demo/simulate", include_in_schema=False)
async def flow_builder_demo_simulate(
    payload: FlowBuilderDemoSimulateRequest,
    request: Request,
    settings: Settings = Depends(get_settings),
) -> dict:
    return simulate_flow_builder_demo(settings, payload, request)


@app.get("/favicon.ico", include_in_schema=False)
@app.get("/favicon.png", include_in_schema=False)
async def favicon() -> Response:
    return Response(status_code=204)


app.include_router(health.router)
app.include_router(models.router)
app.include_router(chat.router)
app.include_router(code_agent.router)
app.include_router(flow_builder.router)
