# Security

## Controls In This MVP

- API key middleware protects every endpoint except `/health`, docs, and OpenAPI metadata.
- CORS is configured through `TELLUS_AI_ALLOWED_ORIGINS`.
- Request logging records method, path, status, and duration only.
- Prompt logging is disabled by default.
- Safety checks run before model invocation.
- Redaction helpers cover common secrets, private keys, wallet seed phrases, tokens, API keys,
  email addresses, and phone numbers.

## Safety Flags

The safety layer detects:

- Legal advice risk.
- Financial advice risk.
- Medical advice risk.
- Private key exposure.
- Instructions to bypass security.
- Malware or credential theft requests.

Private keys, security bypass, malware, and credential theft requests are blocked before model
invocation.

## Production Additions

- Tenant-scoped API keys or service-to-service auth.
- Rate limiting.
- Audit event export.
- DLP scanning for prompt and output streams.
- Secret manager integration.
- Centralized logs with redaction enforced at the collector.
- Security review for any prompt logging or trace storage.

