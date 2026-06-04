from collections.abc import Sequence


def estimate_token_count(text: str) -> int:
    return max(1, len(text) // 4)


def estimate_usage(messages: Sequence[dict[str, str]], completion: str) -> dict[str, int | str]:
    prompt_text = "\n".join(message.get("content", "") for message in messages)
    prompt_tokens = estimate_token_count(prompt_text)
    completion_tokens = estimate_token_count(completion)
    return {
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": prompt_tokens + completion_tokens,
        "source": "estimated",
    }

