"""Plugin sandbox and permission validation boundary (Epic E10 / RULE-012)."""

from __future__ import annotations

import json
import logging
import urllib.request
from collections.abc import Callable
from pathlib import Path
from typing import Any, TypeVar

from shusha.plugins.manifest import (
    PluginError,
    PluginExecutionError,
    PluginManifest,
    PluginPermission,
    PluginPermissionDeniedError,
)

logger = logging.getLogger(__name__)

T = TypeVar("T")


class PluginPermissionValidator:
    """Validator enforcing declarative plugin permissions and security policies."""

    def check_permission(
        self, manifest: PluginManifest, permission: PluginPermission | str
    ) -> bool:
        """Return True if manifest declares specified permission."""
        return manifest.has_permission(permission)

    def require_permission(
        self, manifest: PluginManifest, permission: PluginPermission | str
    ) -> None:
        """Raise PluginPermissionDeniedError if manifest lacks specified permission."""
        if not self.check_permission(manifest, permission):
            raise PluginPermissionDeniedError(
                permission=permission, plugin_id=manifest.id
            )

    def validate_manifest_permissions(self, manifest: PluginManifest) -> None:
        """Validate security policies regarding elevated permissions."""
        restricted_permissions = {
            PluginPermission.PROCESS,
            PluginPermission.CREDENTIALS,
        }
        for perm in manifest.permissions:
            if perm in restricted_permissions and not manifest.is_trusted:
                raise PluginPermissionDeniedError(
                    permission=f"Privileged permission '{perm.value}' requires trusted plugin flag",
                    plugin_id=manifest.id,
                )


class PluginStorage:
    """Safe, isolated directory-scoped storage for sandboxed plugins."""

    def __init__(
        self,
        base_dir: Path,
        manifest: PluginManifest,
        validator: PluginPermissionValidator | None = None,
    ) -> None:
        self._manifest = manifest
        self._validator = validator or PluginPermissionValidator()
        self._plugin_dir = (base_dir / manifest.id).resolve()
        self._kv_file = self._plugin_dir / "storage_kv.json"

    def _ensure_permitted(self) -> None:
        self._validator.require_permission(self._manifest, PluginPermission.STORAGE)
        self._plugin_dir.mkdir(parents=True, exist_ok=True)

    def _resolve_safe_path(self, rel_path: str | Path) -> Path:
        self._ensure_permitted()
        resolved = (self._plugin_dir / rel_path).resolve()
        if not str(resolved).startswith(str(self._plugin_dir)):
            raise PluginPermissionDeniedError(
                permission=f"Path traversal denied: '{rel_path}' escapes plugin storage sandbox",
                plugin_id=self._manifest.id,
            )
        return resolved

    def get(self, key: str, default: str | None = None) -> str | None:
        """Retrieve key from key-value store."""
        data = self._read_kv()
        return data.get(key, default)

    def set(self, key: str, value: str) -> None:
        """Store key in key-value store."""
        data = self._read_kv()
        data[key] = value
        self._write_kv(data)

    def delete(self, key: str) -> bool:
        """Delete key from key-value store."""
        data = self._read_kv()
        if key in data:
            del data[key]
            self._write_kv(data)
            return True
        return False

    def list_keys(self) -> list[str]:
        """List all stored keys."""
        return sorted(self._read_kv().keys())

    def read_bytes(self, rel_path: str | Path) -> bytes:
        """Read binary data from sandboxed file path."""
        path = self._resolve_safe_path(rel_path)
        if not path.exists() or not path.is_file():
            raise FileNotFoundError(f"File not found: {rel_path}")
        return path.read_bytes()

    def write_bytes(self, rel_path: str | Path, data: bytes) -> None:
        """Write binary data to sandboxed file path."""
        path = self._resolve_safe_path(rel_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)

    def list_files(self) -> list[str]:
        """List all files in sandbox directory relative to root."""
        self._ensure_permitted()
        results: list[str] = []
        for file_path in self._plugin_dir.rglob("*"):
            if file_path.is_file() and file_path != self._kv_file:
                results.append(str(file_path.relative_to(self._plugin_dir)))
        return sorted(results)

    def _read_kv(self) -> dict[str, str]:
        self._ensure_permitted()
        if not self._kv_file.exists():
            return {}
        try:
            return json.loads(self._kv_file.read_text(encoding="utf-8"))
        except Exception:
            return {}

    def _write_kv(self, data: dict[str, str]) -> None:
        self._ensure_permitted()
        self._kv_file.write_text(json.dumps(data, indent=2), encoding="utf-8")


class PluginContext:
    """Restricted execution context provided to loaded plugins."""

    def __init__(
        self,
        *,
        manifest: PluginManifest,
        config: dict[str, Any] | None = None,
        storage: PluginStorage,
        validator: PluginPermissionValidator | None = None,
        notification_sink: Callable[[str, str], None] | None = None,
        clipboard_getter: Callable[[], str] | None = None,
        clipboard_setter: Callable[[str], None] | None = None,
    ) -> None:
        self.plugin_id = manifest.id
        self.manifest = manifest
        self.config = dict(config or {})
        self.storage = storage
        self.logger = logging.getLogger(f"shusha.plugins.{manifest.id}")
        self._validator = validator or PluginPermissionValidator()
        self._notification_sink = notification_sink
        self._clipboard_getter = clipboard_getter
        self._clipboard_setter = clipboard_setter

    def send_notification(self, title: str, message: str) -> bool:
        """Emit a user-facing notification if granted NOTIFICATIONS permission."""
        self._validator.require_permission(
            self.manifest, PluginPermission.NOTIFICATIONS
        )
        if self._notification_sink:
            self._notification_sink(title, message)
            return True
        self.logger.info("Notification [%s]: %s", title, message)
        return True

    def read_clipboard(self) -> str:
        """Read clipboard contents if granted CLIPBOARD permission."""
        self._validator.require_permission(self.manifest, PluginPermission.CLIPBOARD)
        if self._clipboard_getter:
            return self._clipboard_getter()
        return ""

    def write_clipboard(self, text: str) -> None:
        """Write text to clipboard if granted CLIPBOARD permission."""
        self._validator.require_permission(self.manifest, PluginPermission.CLIPBOARD)
        if self._clipboard_setter:
            self._clipboard_setter(text)

    def fetch_url(self, url: str, timeout: float = 10.0) -> bytes:
        """Fetch remote resource bytes if granted NETWORK permission."""
        self._validator.require_permission(self.manifest, PluginPermission.NETWORK)
        if not (url.startswith("http://") or url.startswith("https://")):
            raise ValueError(f"Unsupported URL scheme for fetch_url: {url}")

        req = urllib.request.Request(
            url, headers={"User-Agent": "Shusha-Plugin-Sandbox/1.0"}
        )
        with urllib.request.urlopen(req, timeout=timeout) as response:
            return response.read()


class PluginSandbox:
    """Execution sandbox isolating plugin execution and catching failures."""

    def __init__(self, validator: PluginPermissionValidator | None = None) -> None:
        self.validator = validator or PluginPermissionValidator()

    def execute_isolated(
        self,
        plugin_id: str,
        func: Callable[..., T],
        *args: Any,
        **kwargs: Any,
    ) -> T:
        """Execute a plugin callable with exception isolation."""
        try:
            return func(*args, **kwargs)
        except PluginError:
            raise
        except Exception as err:
            logger.exception("Plugin '%s' raised exception: %s", plugin_id, err)
            raise PluginExecutionError(
                f"Plugin '{plugin_id}' execution failed: {err}",
                plugin_id=plugin_id,
            ) from err
