"""Plugin manifest model and permission definitions (Epic E10 / E14)."""

from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from shusha.domain.capability import Capability, CapabilitySet
from shusha.domain.errors import DomainError

PLUGIN_ID_REGEX = re.compile(r"^[a-zA-Z0-9_-]{2,64}$")
SEMVER_REGEX = re.compile(r"^\d+\.\d+(\.\d+)?(-[a-zA-Z0-9_.-]+)?$")
CURRENT_API_VERSION = "2.0.0"
SUPPORTED_API_VERSIONS: frozenset[str] = frozenset({"1.0", "1.0.0", "2.0", "2.0.0"})


class PluginPermission(StrEnum):
    """Permissions declared in plugin manifest to access protected subsystems."""

    NETWORK = "network"
    STORAGE = "storage"
    NOTIFICATIONS = "notifications"
    CLIPBOARD = "clipboard"
    UI_EXTENSION = "ui_extension"
    TRANSFORM = "transform"
    PROCESS = "process"
    CREDENTIALS = "credentials"


class PluginError(DomainError):
    """Base exception for all plugin platform operations."""

    def __init__(self, message: str, plugin_id: str | None = None) -> None:
        super().__init__(message)
        self.plugin_id = plugin_id


class PluginManifestValidationError(PluginError):
    """Raised when a plugin manifest fails schema or integrity validation."""


class PluginPermissionDeniedError(PluginError):
    """Raised when a plugin attempts an action without declared permissions."""

    def __init__(
        self, permission: PluginPermission | str, plugin_id: str | None = None
    ) -> None:
        super().__init__(
            f"Permission '{permission}' was denied for plugin '{plugin_id or 'unknown'}'.",
            plugin_id=plugin_id,
        )
        self.permission = permission


class PluginLoadError(PluginError):
    """Raised when plugin discovery, loading, or initialization fails."""


class PluginExecutionError(PluginError):
    """Raised when an active plugin hook or execution routine fails."""


class PluginNotFoundError(PluginError):
    """Raised when referencing an unregistered or missing plugin."""


@dataclass(frozen=True, slots=True, kw_only=True)
class PluginManifest:
    """Authoritative metadata and permission declaration for Shusha plugins."""

    id: str
    version: str
    api_version: str
    name: str
    entrypoint: str
    description: str = ""
    author: str = ""
    license: str = ""
    backend_type: str | None = None
    capabilities: CapabilitySet = field(default_factory=CapabilitySet)
    permissions: frozenset[PluginPermission] = field(default_factory=frozenset)
    config_schema: dict[str, Any] = field(default_factory=dict)
    is_trusted: bool = False

    def validate(self) -> None:
        """Validate all manifest constraints."""
        if not self.id or not PLUGIN_ID_REGEX.match(self.id):
            raise PluginManifestValidationError(
                f"Invalid plugin ID '{self.id}'. Must be 2-64 alphanumeric characters, underscores or dashes.",
                plugin_id=self.id,
            )
        if not self.name or not self.name.strip():
            raise PluginManifestValidationError(
                "Plugin name cannot be empty.", plugin_id=self.id
            )
        if not self.version or not SEMVER_REGEX.match(self.version):
            raise PluginManifestValidationError(
                f"Invalid plugin version '{self.version}'. Must be semantic version format (e.g. 1.0.0).",
                plugin_id=self.id,
            )
        if not self.api_version or not (
            self.api_version in SUPPORTED_API_VERSIONS
            or SEMVER_REGEX.match(self.api_version)
        ):
            raise PluginManifestValidationError(
                f"Invalid or unsupported api_version '{self.api_version}'. Supported: {sorted(SUPPORTED_API_VERSIONS)}",
                plugin_id=self.id,
            )
        if not self.entrypoint or not self.entrypoint.strip():
            raise PluginManifestValidationError(
                "Plugin entrypoint cannot be empty.", plugin_id=self.id
            )

    def has_permission(self, permission: PluginPermission | str) -> bool:
        """Check if manifest grants specified permission."""
        if isinstance(permission, str):
            try:
                perm = PluginPermission(permission.lower())
            except ValueError:
                return False
        else:
            perm = permission
        return perm in self.permissions

    def has_capability(self, capability: Capability | str) -> bool:
        """Check if manifest declares specified capability."""
        return self.capabilities.has(capability)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PluginManifest:
        """Parse and construct a PluginManifest from dictionary/JSON."""
        raw_perms = data.get("permissions", [])
        parsed_perms: set[PluginPermission] = set()
        for p in raw_perms:
            if isinstance(p, PluginPermission):
                parsed_perms.add(p)
            elif isinstance(p, str):
                try:
                    parsed_perms.add(PluginPermission(p.lower()))
                except ValueError as err:
                    raise PluginManifestValidationError(
                        f"Unknown permission '{p}' in plugin manifest.",
                        plugin_id=data.get("id"),
                    ) from err

        raw_caps = data.get("capabilities", [])
        if isinstance(raw_caps, CapabilitySet):
            caps = raw_caps
        elif isinstance(raw_caps, Iterable) and not isinstance(raw_caps, (str, bytes)):
            caps = CapabilitySet.from_iterable(raw_caps)
        else:
            caps = CapabilitySet()

        manifest = cls(
            id=str(data.get("id", "")).strip(),
            name=str(data.get("name", "")).strip(),
            version=str(data.get("version", "")).strip(),
            api_version=str(data.get("api_version", CURRENT_API_VERSION)).strip(),
            entrypoint=str(data.get("entrypoint", "")).strip(),
            description=str(data.get("description", "")).strip(),
            author=str(data.get("author", "")).strip(),
            license=str(data.get("license", "")).strip(),
            backend_type=data.get("backend_type"),
            capabilities=caps,
            permissions=frozenset(parsed_perms),
            config_schema=dict(data.get("config_schema", {})),
            is_trusted=bool(data.get("is_trusted", False)),
        )
        manifest.validate()
        return manifest

    def to_dict(self) -> dict[str, Any]:
        """Serialize manifest to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "version": self.version,
            "api_version": self.api_version,
            "entrypoint": self.entrypoint,
            "description": self.description,
            "author": self.author,
            "license": self.license,
            "backend_type": self.backend_type,
            "capabilities": self.capabilities.to_list(),
            "permissions": sorted(p.value for p in self.permissions),
            "config_schema": self.config_schema,
            "is_trusted": self.is_trusted,
        }
