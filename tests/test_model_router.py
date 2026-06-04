from services.api.core.config import Settings
from services.api.core.model_router import ModelRouter


def test_router_uses_coder_for_technical_tasks() -> None:
    router = ModelRouter(Settings(inference_backend="mock"))

    route = router.select_by_task("pull request generation", "debug SQL migration")

    assert route.model_key == "qwen3-coder-next"
    assert route.hf_model_id == "Qwen/Qwen3-Coder-Next"


def test_router_defaults_general_to_14b() -> None:
    router = ModelRouter(Settings(inference_backend="mock"))

    route = router.select_for_chat()

    assert route.model_key == "qwen3-14b"
    assert route.hf_model_id == "Qwen/Qwen3-14B"


def test_router_allows_general_32b() -> None:
    router = ModelRouter(
        Settings(
            inference_backend="mock",
            default_general_model="qwen3-32b",
        )
    )

    route = router.select_for_chat()

    assert route.model_key == "qwen3-32b"
    assert route.hf_model_id == "Qwen/Qwen3-32B"

