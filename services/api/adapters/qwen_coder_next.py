CODER_MODEL_KEY = "qwen3-coder-next"

CODER_MODEL_CONFIG = {
    "display_name": "Qwen3-Coder-Next",
    "hf_model_id": "Qwen/Qwen3-Coder-Next",
    "role": "code_agent",
    "default": True,
    "use_cases": [
        "coding",
        "repo analysis",
        "debugging",
        "pull request generation",
        "DevOps",
        "SQL generation",
        "architecture refactoring",
        "technical documentation",
    ],
}


def normalize_coder_model(model_name: str) -> str:
    normalized = model_name.strip().lower()
    aliases = {
        "qwen/qwen3-coder-next": CODER_MODEL_KEY,
        "qwen3-coder": CODER_MODEL_KEY,
        "qwen3-coder-next": CODER_MODEL_KEY,
    }
    return aliases.get(normalized, CODER_MODEL_KEY)

