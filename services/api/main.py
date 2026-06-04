from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from services.api.core.config import get_settings
from services.api.core.logging import RequestLoggingMiddleware, configure_logging
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
    return """
    <!doctype html>
    <html lang="en">
      <head>
        <meta charset="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <title>Tellus AI Model Platform</title>
        <style>
          body { font-family: system-ui, sans-serif; max-width: 760px; margin: 56px auto; padding: 0 24px; line-height: 1.55; }
          code { background: #f3f4f6; padding: 2px 5px; border-radius: 4px; }
          a { color: #155eef; }
        </style>
      </head>
      <body>
        <h1>Tellus AI Model Platform</h1>
        <p>The API is running. Protected endpoints require an <code>X-API-Key</code> header.</p>
        <ul>
          <li><a href="/health">Health check</a></li>
          <li><a href="/docs">Interactive API docs</a></li>
          <li><a href="/flow-builder/schema">FlowBuilder schema</a> requires API key</li>
        </ul>
      </body>
    </html>
    """


@app.get("/favicon.ico", include_in_schema=False)
@app.get("/favicon.png", include_in_schema=False)
async def favicon() -> Response:
    return Response(status_code=204)


app.include_router(health.router)
app.include_router(models.router)
app.include_router(chat.router)
app.include_router(code_agent.router)
app.include_router(flow_builder.router)
