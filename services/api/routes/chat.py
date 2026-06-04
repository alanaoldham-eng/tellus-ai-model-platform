from fastapi import APIRouter, Depends, HTTPException

from services.api.core.config import Settings, get_settings
from services.api.core.model_router import ModelRouter
from services.api.core.prompt_templates import PromptTemplateLoader
from services.api.core.safety import assess_text, safety_block_message
from services.api.core.telemetry import estimate_usage
from services.api.schemas.chat import ChatRequest, ChatResponse

router = APIRouter(tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    settings: Settings = Depends(get_settings),
) -> ChatResponse:
    if not settings.enable_general_assistant:
        raise HTTPException(status_code=403, detail="General assistant endpoint is disabled.")

    model_router = ModelRouter(settings)
    prompt_loader = PromptTemplateLoader(settings)
    route = model_router.select_for_chat(request.requested_model)

    assessment_text = "\n".join(
        part
        for part in [
            request.message,
            request.product_context or "",
            request.system_prompt_override or "",
            request.tenant_id or "",
        ]
        if part
    )
    assessment = assess_text(assessment_text)
    if assessment.should_block:
        message = safety_block_message(assessment.flags)
        return ChatResponse(
            assistant_response=message,
            model_used=route.model_key,
            safety_flags=assessment.flags,
            token_usage=estimate_usage([], message),
        )

    system_prompt = prompt_loader.general_assistant_prompt(
        product_context=request.product_context,
        system_prompt_override=request.system_prompt_override,
    )
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": request.message},
    ]
    adapter_response = await model_router.generate(
        route,
        messages,
        {
            "role": "general",
            "product_context": request.product_context,
            "tenant_id": request.tenant_id,
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
        },
    )
    flags = sorted(set(assessment.flags + adapter_response.safety_flags))
    return ChatResponse(
        assistant_response=adapter_response.content,
        model_used=adapter_response.model,
        safety_flags=flags,
        token_usage=adapter_response.usage or estimate_usage(messages, adapter_response.content),
    )

