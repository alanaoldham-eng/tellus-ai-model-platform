import os
from pathlib import Path

os.environ["TELLUS_AI_INFERENCE_BACKEND"] = "mock"
os.environ["TELLUS_AI_API_KEY"] = "replace_me"
os.environ["TELLUS_AI_ENABLE_PROMPT_LOGGING"] = "false"
os.environ["TELLUS_AI_FLOW_STORE_PATH"] = ".pytest_cache/flow_builder_test.sqlite3"

Path(".pytest_cache/flow_builder_test.sqlite3").unlink(missing_ok=True)

from services.api.core.config import get_settings  # noqa: E402

get_settings.cache_clear()
