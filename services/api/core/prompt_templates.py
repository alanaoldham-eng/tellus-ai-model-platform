from pathlib import Path

from services.api.core.config import Settings


PRODUCT_CONTEXTS = {
    "CAPIT": (
        "Tokenized environmental awareness project around plugged oil and gas wells. "
        "Uses blockchain rails, wallet onboarding, thirdweb-style app integration, and auditability."
    ),
    "Human Layer / Work OS": (
        "Human-in-the-loop work marketplace with task workflows, compliance-gated payouts, "
        "wallet onboarding, and audit logs."
    ),
    "Tellus Comply": (
        "Compliance readiness product for readiness snapshots, evidence tracking, gaps, reports, "
        "and verification artifacts."
    ),
    "Tellus Sustain": (
        "ESG readiness product using a similar platform layer to Tellus Comply with ESG-specific "
        "evidence and reporting."
    ),
    "Tellus Sign": "E-signature plus wallet-signature product.",
    "Tellus Gateway": "Wallet and onboarding gateway for Tellus ecosystem apps.",
}


class PromptTemplateLoader:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.prompt_root = settings.project_root / "prompts"

    def load_system_prompt(self, filename: str) -> str:
        path = self.prompt_root / "system" / filename
        return path.read_text(encoding="utf-8").strip()

    def general_assistant_prompt(
        self,
        product_context: str | None = None,
        system_prompt_override: str | None = None,
    ) -> str:
        base_prompt = (
            system_prompt_override.strip()
            if system_prompt_override
            else self.load_system_prompt("tellus_general_assistant.md")
        )
        return "\n\n".join(
            part
            for part in [
                base_prompt,
                self._product_context_block(product_context),
                self._non_overridable_guardrails(),
            ]
            if part
        )

    def developer_agent_prompt(self) -> str:
        return "\n\n".join(
            [
                self.load_system_prompt("tellus_developer_agent.md"),
                self._non_overridable_guardrails(),
            ]
        )

    def compliance_assistant_prompt(self, product_context: str | None = None) -> str:
        return "\n\n".join(
            [
                self.load_system_prompt("tellus_compliance_assistant.md"),
                self._product_context_block(product_context),
                self._non_overridable_guardrails(),
            ]
        )

    def _product_context_block(self, product_context: str | None) -> str:
        if not product_context:
            return self._all_product_contexts_block()

        normalized = product_context.strip().lower()
        for name, description in PRODUCT_CONTEXTS.items():
            if normalized == name.lower():
                return f"Tellus product context: {name}\n{description}"
        return f"Tellus product context provided by caller:\n{product_context.strip()}"

    @staticmethod
    def _all_product_contexts_block() -> str:
        lines = ["Tellus product context catalog:"]
        lines.extend(f"- {name}: {description}" for name, description in PRODUCT_CONTEXTS.items())
        lines.append("- LesBiGulfFriends.com: excluded unless explicitly enabled later.")
        return "\n".join(lines)

    @staticmethod
    def _non_overridable_guardrails() -> str:
        return (
            "Non-overridable Tellus guardrails: do not provide formal legal, medical, or "
            "financial advice; escalate compliance-sensitive decisions to human review; never "
            "request, expose, or retain secrets, private keys, wallet seed phrases, API keys, "
            "or credentials."
        )


def prompt_file_exists(settings: Settings, relative_path: str) -> bool:
    return (settings.project_root / relative_path).is_file()


def project_prompt_path(settings: Settings, relative_path: str) -> Path:
    return settings.project_root / relative_path

