from services.api.core.safety import assess_text, redact_sensitive_text


def test_redacts_common_secrets() -> None:
    text = "token=hf_abcdefghijklmnopqrstuvwxyz123456 and email alana@example.com"

    redacted = redact_sensitive_text(text)

    assert "hf_" not in redacted
    assert "alana@example.com" not in redacted
    assert "[REDACTED_HF_TOKEN]" in redacted
    assert "[REDACTED_EMAIL]" in redacted


def test_detects_private_key_exposure_as_blocking() -> None:
    assessment = assess_text("my private key is 0x" + "a" * 64)

    assert "private_key_exposure" in assessment.flags
    assert assessment.should_block is True


def test_detects_compliance_sensitive_legal_risk_without_blocking() -> None:
    assessment = assess_text("Can you provide legal advice on this regulatory decision?")

    assert "legal_advice_risk" in assessment.flags
    assert assessment.should_block is False

