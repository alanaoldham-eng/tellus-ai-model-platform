from services.api.core.config import Settings


def test_tenant_api_keys_parse_json_mapping() -> None:
    settings = Settings(
        inference_backend="mock",
        tenant_api_keys='{"bank_a":"key_a","bank_b":"key_b"}',
    )

    assert settings.tenant_api_keys == {"bank_a": "key_a", "bank_b": "key_b"}


def test_tenant_api_keys_parse_comma_mapping() -> None:
    settings = Settings(
        inference_backend="mock",
        tenant_api_keys="bank_a:key_a,bank_b:key_b",
    )

    assert settings.tenant_api_keys == {"bank_a": "key_a", "bank_b": "key_b"}
