import re
from dataclasses import dataclass


@dataclass(frozen=True)
class SafetyAssessment:
    flags: list[str]
    should_block: bool
    redacted_text: str


SECRET_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (
        re.compile(
            r"-----BEGIN [A-Z ]*PRIVATE KEY-----.*?-----END [A-Z ]*PRIVATE KEY-----",
            re.IGNORECASE | re.DOTALL,
        ),
        "[REDACTED_PRIVATE_KEY]",
    ),
    (re.compile(r"\b(hf_[A-Za-z0-9_\-]{20,})\b"), "[REDACTED_HF_TOKEN]"),
    (re.compile(r"\b(sk-[A-Za-z0-9_\-]{20,})\b"), "[REDACTED_API_KEY]"),
    (re.compile(r"\b(gh[pousr]_[A-Za-z0-9_]{20,})\b"), "[REDACTED_GITHUB_TOKEN]"),
    (re.compile(r"\b(xox[baprs]-[A-Za-z0-9\-]{20,})\b"), "[REDACTED_SLACK_TOKEN]"),
    (re.compile(r"(?i)\bbearer\s+[A-Za-z0-9_\-\.=]{20,}"), "Bearer [REDACTED_TOKEN]"),
    (re.compile(r"\bAKIA[0-9A-Z]{16}\b"), "[REDACTED_AWS_ACCESS_KEY]"),
    (re.compile(r"0x[a-fA-F0-9]{64}\b"), "[REDACTED_PRIVATE_KEY_HEX]"),
    (
        re.compile(r"(?i)\b(seed phrase|mnemonic)\s*[:=]\s*([a-z]+(?:\s+[a-z]+){11,23})"),
        r"\1: [REDACTED_SEED_PHRASE]",
    ),
    (
        re.compile(r"\b[A-Z0-9._%+\-]+@[A-Z0-9.\-]+\.[A-Z]{2,}\b", re.IGNORECASE),
        "[REDACTED_EMAIL]",
    ),
    (
        re.compile(r"(?<!\d)(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}(?!\d)"),
        "[REDACTED_PHONE]",
    ),
]

FLAG_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    (
        "legal_advice_risk",
        re.compile(
            r"\b(legal advice|lawsuit|sue|contract liability|regulatory decision|attorney|"
            r"lawyer|formal certification|court filing)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "financial_advice_risk",
        re.compile(
            r"\b(financial advice|investment advice|buy this stock|sell this stock|tax strategy|"
            r"portfolio allocation|security token advice)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "medical_advice_risk",
        re.compile(
            r"\b(medical advice|diagnose|prescribe|dosage|treatment plan|clinical decision)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "private_key_exposure",
        re.compile(
            r"(-----BEGIN [A-Z ]*PRIVATE KEY-----|0x[a-fA-F0-9]{64}\b|"
            r"(?i:\b(seed phrase|mnemonic)\s*[:=]))"
        ),
    ),
    (
        "security_bypass_request",
        re.compile(
            r"\b(bypass security|disable authentication|evade detection|privilege escalation|"
            r"break into|exploit a live system)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "malware_or_credential_theft_request",
        re.compile(
            r"\b(keylogger|credential theft|steal passwords|phishing kit|malware payload|"
            r"ransomware|exfiltrate credentials|dump browser passwords)\b",
            re.IGNORECASE,
        ),
    ),
]

BLOCKING_FLAGS = {
    "private_key_exposure",
    "security_bypass_request",
    "malware_or_credential_theft_request",
}


def redact_sensitive_text(text: str) -> str:
    redacted = text
    for pattern, replacement in SECRET_PATTERNS:
        redacted = pattern.sub(replacement, redacted)
    return redacted


def assess_text(text: str) -> SafetyAssessment:
    flags = [flag for flag, pattern in FLAG_PATTERNS if pattern.search(text)]
    unique_flags = sorted(set(flags))
    return SafetyAssessment(
        flags=unique_flags,
        should_block=any(flag in BLOCKING_FLAGS for flag in unique_flags),
        redacted_text=redact_sensitive_text(text),
    )


def safety_block_message(flags: list[str]) -> str:
    joined = ", ".join(flags) if flags else "safety risk"
    return (
        "I cannot send this request to a model because the safety layer detected "
        f"{joined}. Remove secrets or reframe the request for a legitimate defensive, "
        "reviewable workflow."
    )

