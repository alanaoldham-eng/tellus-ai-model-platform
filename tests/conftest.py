import os
from uuid import uuid4
from pathlib import Path

os.environ["TELLUS_AI_INFERENCE_BACKEND"] = "mock"
os.environ["TELLUS_AI_API_KEY"] = "replace_me"
os.environ["TELLUS_AI_ENABLE_PROMPT_LOGGING"] = "false"
os.environ["TELLUS_AI_FLOW_STORE_PATH"] = f".pytest_cache/flow_builder_test_{uuid4().hex}.sqlite3"

try:
    Path(os.environ["TELLUS_AI_FLOW_STORE_PATH"]).unlink(missing_ok=True)
except PermissionError:
    pass

from services.api.core.config import get_settings  # noqa: E402

get_settings.cache_clear()
