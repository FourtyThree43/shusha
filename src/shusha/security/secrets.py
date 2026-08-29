"""
Secure credential and token storage for Shusha 2.
Enforces strict filesystem permissions (0600) on secret stores.
"""

import contextlib
import json
import os
import secrets
from pathlib import Path


class SecretStore:
    """Secure local key-value store for passwords, tokens, and RPC secrets."""

    def __init__(self, storage_path: Path | None = None) -> None:
        if storage_path is None:
            config_dir = Path.home() / ".config" / "shusha"
            storage_path = config_dir / "secrets.json"
        self.storage_path = storage_path
        self._cache: dict[str, str] = {}
        self._loaded = False

    def _ensure_file(self) -> None:
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.storage_path.exists():
            self.storage_path.touch(mode=0o600, exist_ok=True)
            self.storage_path.write_text("{}", encoding="utf-8")
        else:
            with contextlib.suppress(Exception):
                os.chmod(self.storage_path, 0o600)

    def _load(self) -> None:
        if self._loaded:
            return
        if not self.storage_path.exists():
            self._cache = {}
            self._loaded = True
            return

        try:
            content = self.storage_path.read_text(encoding="utf-8")
            self._cache = json.loads(content)
        except Exception:
            self._cache = {}
        self._loaded = True

    def _save(self) -> None:
        self._ensure_file()
        content = json.dumps(self._cache, indent=2)
        self.storage_path.write_text(content, encoding="utf-8")
        with contextlib.suppress(Exception):
            os.chmod(self.storage_path, 0o600)

    def get(self, key: str, default: str | None = None) -> str | None:
        """Retrieve a secret by key."""
        self._load()
        return self._cache.get(key, default)

    def set(self, key: str, value: str) -> None:
        """Store a secret value."""
        self._load()
        self._cache[key] = value
        self._save()

    def delete(self, key: str) -> bool:
        """Remove a secret from store."""
        self._load()
        if key in self._cache:
            del self._cache[key]
            self._save()
            return True
        return False

    def get_or_generate_rpc_secret(self, key: str = "aria2_rpc_secret") -> str:
        """Retrieve existing RPC secret or generate a cryptographically strong 32-byte secret."""
        existing = self.get(key)
        if existing:
            return existing
        new_secret = secrets.token_urlsafe(32)
        self.set(key, new_secret)
        return new_secret
