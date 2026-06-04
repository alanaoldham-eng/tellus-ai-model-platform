GENERAL_MODELS = {
    "qwen3-14b": {
        "display_name": "Qwen3 14B",
        "hf_model_id": "Qwen/Qwen3-14B",
        "role": "general_assistant",
        "default": True,
        "use_cases": [
            "general assistant",
            "product support",
            "onboarding",
            "user help",
            "internal business assistant",
            "compliance assistant drafts",
            "customer-facing Q&A",
        ],
    },
    "qwen3-32b": {
        "display_name": "Qwen3 32B",
        "hf_model_id": "Qwen/Qwen3-32B",
        "role": "general_assistant",
        "default": False,
        "use_cases": [
            "stronger reasoning",
            "complex product support",
            "multi-step compliance drafts",
            "internal business assistant",
            "customer-facing Q&A when hardware allows",
        ],
    },
}


def normalize_general_model(model_name: str) -> str:
    normalized = model_name.strip().lower()
    aliases = {
        "14b": "qwen3-14b",
        "qwen-3-14b": "qwen3-14b",
        "qwen/qwen3-14b": "qwen3-14b",
        "32b": "qwen3-32b",
        "qwen-3-32b": "qwen3-32b",
        "qwen/qwen3-32b": "qwen3-32b",
    }
    return aliases.get(normalized, normalized)


def get_general_model_config(model_name: str) -> dict[str, object]:
    normalized = normalize_general_model(model_name)
    return GENERAL_MODELS.get(normalized, GENERAL_MODELS["qwen3-14b"])

