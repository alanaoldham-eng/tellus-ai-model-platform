from typing import Any

from pydantic import BaseModel, Field


class FileSnippet(BaseModel):
    path: str = Field(..., min_length=1)
    content: str = Field(..., min_length=1)
    language: str | None = None


class CodeAgentRequest(BaseModel):
    repo_context: str = Field(..., min_length=1)
    task_instructions: str = Field(..., min_length=1)
    file_snippets: list[FileSnippet] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    tenant_id: str | None = None
    temperature: float = Field(default=0.1, ge=0.0, le=2.0)
    max_tokens: int = Field(default=2048, ge=1, le=16384)


class CodeAgentResponse(BaseModel):
    proposed_changes: list[str] = Field(default_factory=list)
    explanation: str
    test_plan: list[str] = Field(default_factory=list)
    risk_notes: list[str] = Field(default_factory=list)
    files_touched: list[str] = Field(default_factory=list)
    model_used: str
    safety_flags: list[str] = Field(default_factory=list)
    token_usage: dict[str, Any] | None = None

