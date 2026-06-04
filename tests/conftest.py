import os

os.environ["TELLUS_AI_INFERENCE_BACKEND"] = "mock"
os.environ["TELLUS_AI_API_KEY"] = "replace_me"
os.environ["TELLUS_AI_ENABLE_PROMPT_LOGGING"] = "false"

from services.api.core.config import get_settings  # noqa: E402

get_settings.cache_clear()

