"""
Data redaction and masking utilities to prevent secret leakage in logs and diagnostics.
"""

import re
from typing import Any
from urllib.parse import urlparse, urlunparse

SENSITIVE_FIELD_NAMES = {
    "rpc_secret",
    "rpc-secret",
    "secret",
    "password",
    "passwd",
    "http_passwd",
    "http-passwd",
    "ftp_passwd",
    "ftp-passwd",
    "proxy_passwd",
    "proxy-passwd",
    "token",
    "auth_header",
    "authorization",
}


def redact_url_credentials(url: str) -> str:
    """Mask credentials in URLs (e.g. 'http://user:pass@host' -> 'http://user:******@host')."""
    try:
        parsed = urlparse(url)
        if parsed.password:
            netloc = parsed.netloc.replace(f":{parsed.password}@", ":******@")
            return urlunparse(parsed._replace(netloc=netloc))
        return url
    except Exception:
        return url


def redact_string_secrets(text: str, known_secrets: list[str] | None = None) -> str:
    """Mask known secret tokens and common pattern tokens in text."""
    redacted = text
    if known_secrets:
        for secret in known_secrets:
            if secret and len(secret) >= 3:
                redacted = redacted.replace(secret, "******")

    # Mask --rpc-secret=... patterns
    redacted = re.sub(r"(--rpc-secret=)([^\s]+)", r"\1******", redacted)
    # Mask token:... JSON-RPC params
    redacted = re.sub(r'("token:)([^"]+)(")', r"\1******\3", redacted)
    return redacted


def redact_dict_secrets(
    data: dict[str, Any], extra_sensitive_keys: set[str] | None = None
) -> dict[str, Any]:
    """Recursively mask sensitive values in dictionary structures."""
    sensitive_keys = SENSITIVE_FIELD_NAMES | (extra_sensitive_keys or set())
    clean: dict[str, Any] = {}

    for k, v in data.items():
        k_lower = str(k).lower().replace("_", "-")
        if k_lower in sensitive_keys or any(
            s in k_lower for s in ("passwd", "secret", "token")
        ):
            clean[k] = "******"
        elif isinstance(v, dict):
            clean[k] = redact_dict_secrets(v, extra_sensitive_keys)
        elif isinstance(v, list):
            clean[k] = [
                redact_dict_secrets(item, extra_sensitive_keys)
                if isinstance(item, dict)
                else (redact_url_credentials(item) if isinstance(item, str) else item)
                for item in v
            ]
        elif isinstance(v, str):
            clean[k] = redact_url_credentials(v)
        else:
            clean[k] = v

    return clean
