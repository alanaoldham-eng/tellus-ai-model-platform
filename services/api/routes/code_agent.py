from fastapi import APIRouter, Depends, HTTPException

from services.api.core.config import Settings, get_settings
from services.api.core.model_router import ModelRouter
from services.api.core.prompt_templates import PromptTemplateLoader
from services.api.core.safety import assess_text, safety_block_message
from services.api.core.telemetry import estimate_usage
from services.api.schemas.code_agent import CodeAgentRequest, CodeAgentResponse, FileSnippet

router = APIRouter(tags=["code-agent"])


@router.post("/code-agent", response_model=CodeAgentResponse)
async def code_agent(
    request: CodeAgentRequest,
    settings: Settings = Depends(get_settings),
) -> CodeAgentResponse:
    if not settings.enable_code_agent:
        raise HTTPException(status_code=403, detail="Code agent endpoint is disabled.")

    model_router = ModelRouter(settings)
    prompt_loader = PromptTemplateLoader(settings)
    route = model_router.select_for_code_agent()

    assessment_text = "\n".join(
        [
            request.repo_context,
            request.task_instructions,
            "\n".join(snippet.content for snippet in request.file_snippets),
            "\n".join(request.constraints),
            request.tenant_id or "",
        ]
    )
    assessment = assess_text(assessment_text)
    if assessment.should_block:
        message = safety_block_message(assessment.flags)
        return CodeAgentResponse(
            proposed_changes=[],
            explanation=message,
            test_plan=[],
            risk_notes=["Request blocked before model invocation."],
            files_touched=[],
            model_used=route.model_key,
            safety_flags=assessment.flags,
            token_usage=estimate_usage([], message),
        )

    messages = [
        {"role": "system", "content": prompt_loader.developer_agent_prompt()},
        {"role": "user", "content": _build_code_agent_user_prompt(request)},
    ]
    adapter_response = await model_router.generate(
        route,
        messages,
        {
            "role": "code_agent",
            "tenant_id": request.tenant_id,
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
        },
    )
    flags = sorted(set(assessment.flags + adapter_response.safety_flags))
    return CodeAgentResponse(
        proposed_changes=[adapter_response.content],
        explanation=(
            "The model response is returned as a proposed plan or diff candidate. "
            "No files are modified by this endpoint."
        ),
        test_plan=[
            "Run targeted tests for the touched module before applying changes.",
            "Run the repository's full test suite before merging.",
        ],
        risk_notes=[
            "Review generated changes before applying them.",
            "Confirm paths exist in the target repository; the model must not invent files.",
        ],
        files_touched=[],
        model_used=adapter_response.model,
        safety_flags=flags,
        token_usage=adapter_response.usage or estimate_usage(messages, adapter_response.content),
    )


def _build_code_agent_user_prompt(request: CodeAgentRequest) -> str:
    snippets = "\n\n".join(_format_snippet(snippet) for snippet in request.file_snippets)
    constraints = "\n".join(f"- {constraint}" for constraint in request.constraints)
    return "\n\n".join(
        part
        for part in [
            f"Repo context:\n{request.repo_context}",
            f"Task instructions:\n{request.task_instructions}",
            f"Constraints:\n{constraints}" if constraints else "Constraints:\n- Keep diffs small and reviewable.",
            f"File snippets:\n{snippets}" if snippets else "File snippets:\nNo snippets provided.",
        ]
        if part
    )


def _format_snippet(snippet: FileSnippet) -> str:
    language = snippet.language or "text"
    return f"Path: {snippet.path}\nLanguage: {language}\n```{language}\n{snippet.content}\n```"

