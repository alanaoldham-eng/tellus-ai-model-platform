from services.api.core.config import Settings
from services.api.core.prompt_templates import PromptTemplateLoader


def test_general_prompt_includes_product_context() -> None:
    loader = PromptTemplateLoader(Settings(inference_backend="mock"))

    prompt = loader.general_assistant_prompt(product_context="CAPIT")

    assert "Tellus general assistant" in prompt
    assert "plugged oil and gas wells" in prompt
    assert "human review" in prompt


def test_developer_prompt_requires_repo_inspection() -> None:
    loader = PromptTemplateLoader(Settings(inference_backend="mock"))

    prompt = loader.developer_agent_prompt()

    assert "Inspect the repository structure" in prompt
    assert "small reviewable diffs" in prompt

