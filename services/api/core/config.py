from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Environment-driven application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
        populate_by_name=True,
    )

    env: str = Field(default="development", validation_alias="TELLUS_AI_ENV")
    default_general_model: str = Field(
        default="qwen3-14b",
        validation_alias="TELLUS_AI_DEFAULT_GENERAL_MODEL",
    )
    default_coder_model: str = Field(
        default="qwen3-coder-next",
        validation_alias="TELLUS_AI_DEFAULT_CODER_MODEL",
    )
    inference_backend: str = Field(default="mock", validation_alias="TELLUS_AI_INFERENCE_BACKEND")
    enable_code_agent: bool = Field(default=True, validation_alias="TELLUS_AI_ENABLE_CODE_AGENT")
    enable_general_assistant: bool = Field(
        default=True,
        validation_alias="TELLUS_AI_ENABLE_GENERAL_ASSISTANT",
    )
    enable_fine_tuning: bool = Field(
        default=False,
        validation_alias="TELLUS_AI_ENABLE_FINE_TUNING",
    )
    log_level: str = Field(default="info", validation_alias="TELLUS_AI_LOG_LEVEL")
    allowed_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:3000"],
        validation_alias="TELLUS_AI_ALLOWED_ORIGINS",
    )
    api_key: str = Field(default="replace_me", validation_alias="TELLUS_AI_API_KEY")
    enable_prompt_logging: bool = Field(
        default=False,
        validation_alias="TELLUS_AI_ENABLE_PROMPT_LOGGING",
    )
    mock_fallback_enabled: bool = Field(
        default=True,
        validation_alias="TELLUS_AI_MOCK_FALLBACK_ENABLED",
    )
    request_timeout_seconds: float = Field(
        default=60.0,
        validation_alias="TELLUS_AI_REQUEST_TIMEOUT_SECONDS",
    )

    ollama_base_url: str = Field(
        default="http://localhost:11434",
        validation_alias="TELLUS_AI_OLLAMA_BASE_URL",
    )
    ollama_general_model: str | None = Field(
        default=None,
        validation_alias="TELLUS_AI_OLLAMA_GENERAL_MODEL",
    )
    ollama_coder_model: str | None = Field(
        default=None,
        validation_alias="TELLUS_AI_OLLAMA_CODER_MODEL",
    )

    vllm_base_url: str = Field(
        default="http://localhost:8001/v1",
        validation_alias="TELLUS_AI_VLLM_BASE_URL",
    )
    vllm_api_key: str | None = Field(default=None, validation_alias="TELLUS_AI_VLLM_API_KEY")
    vllm_general_model: str | None = Field(
        default=None,
        validation_alias="TELLUS_AI_VLLM_GENERAL_MODEL",
    )
    vllm_coder_model: str | None = Field(
        default=None,
        validation_alias="TELLUS_AI_VLLM_CODER_MODEL",
    )

    llama_cpp_base_url: str = Field(
        default="http://localhost:8080/v1",
        validation_alias="TELLUS_AI_LLAMA_CPP_BASE_URL",
    )
    llama_cpp_api_key: str | None = Field(
        default=None,
        validation_alias="TELLUS_AI_LLAMA_CPP_API_KEY",
    )
    llama_cpp_general_model: str | None = Field(
        default=None,
        validation_alias="TELLUS_AI_LLAMA_CPP_GENERAL_MODEL",
    )
    llama_cpp_coder_model: str | None = Field(
        default=None,
        validation_alias="TELLUS_AI_LLAMA_CPP_CODER_MODEL",
    )

    transformers_cache_dir: str = Field(
        default="./hf_cache",
        validation_alias="TELLUS_AI_TRANSFORMERS_CACHE_DIR",
    )
    hf_token: str | None = Field(default=None, validation_alias="HF_TOKEN")

    @field_validator("allowed_origins", mode="before")
    @classmethod
    def parse_allowed_origins(cls, value: str | list[str]) -> list[str]:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @field_validator("inference_backend", mode="before")
    @classmethod
    def normalize_backend(cls, value: str) -> str:
        normalized = value.strip().lower().replace("-", "_")
        aliases = {
            "llamacpp": "llama_cpp",
            "llama.cpp": "llama_cpp",
            "hf": "transformers",
            "huggingface": "transformers",
        }
        return aliases.get(normalized, normalized)

    @property
    def project_root(self) -> Path:
        return Path(__file__).resolve().parents[3]

    @property
    def enabled_roles(self) -> list[str]:
        roles: list[str] = []
        if self.enable_general_assistant:
            roles.append("general_assistant")
        if self.enable_code_agent:
            roles.append("code_agent")
        return roles


@lru_cache
def get_settings() -> Settings:
    return Settings()
