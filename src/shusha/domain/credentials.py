"""Domain model for secure credential references."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum

from shusha.domain.identifiers import CredentialId


class CredentialKind(StrEnum):
    """Classification of credential reference."""

    PASSWORD = "password"
    TOKEN = "token"
    BEARER_TOKEN = "bearer_token"
    PRIVATE_KEY = "private_key"
    CERTIFICATE = "certificate"
    RPC_SECRET = "rpc_secret"
    PROXY_AUTH = "proxy_auth"
    HTTP_AUTH = "http_auth"


class CredentialScope(StrEnum):
    """Scope of credential validity."""

    GLOBAL = "global"
    BACKEND = "backend"
    DOMAIN = "domain"
    JOB = "job"


@dataclass(frozen=True, slots=True, kw_only=True)
class CredentialReference:
    """Safe, indirect reference to sensitive credentials stored securely."""

    id: CredentialId
    kind: CredentialKind
    store_key: str
    scope: CredentialScope = CredentialScope.DOMAIN
    label: str = ""
    domain_pattern: str | None = None
    description: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def matches_domain(self, domain: str) -> bool:
        """Check if credential applies to a given domain or hostname."""
        if not self.domain_pattern or self.scope == CredentialScope.GLOBAL:
            return True
        import fnmatch

        return fnmatch.fnmatch(domain.lower(), self.domain_pattern.lower())
