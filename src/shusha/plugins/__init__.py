"""Shusha Plugin Architecture package (Epic E10 / E14)."""

from __future__ import annotations

from shusha.plugins.fixtures import (
    FakeAuditLoggerPlugin,
    FakeNotificationPlugin,
    FakeRequestFilterPlugin,
    FakeUnprivilegedPlugin,
    FakeURLTransformPlugin,
    create_fake_manifest,
    create_fake_plugin_directory,
)
from shusha.plugins.hooks import (
    PluginHookManager,
    PluginHookName,
    RegisteredHook,
)
from shusha.plugins.loader import (
    LoadedPlugin,
    PluginBase,
    PluginLoader,
    PluginProtocol,
    PluginState,
)
from shusha.plugins.manifest import (
    PluginError,
    PluginExecutionError,
    PluginLoadError,
    PluginManifest,
    PluginManifestValidationError,
    PluginNotFoundError,
    PluginPermission,
    PluginPermissionDeniedError,
)
from shusha.plugins.sandbox import (
    PluginContext,
    PluginPermissionValidator,
    PluginSandbox,
    PluginStorage,
)

__all__ = [
    "FakeAuditLoggerPlugin",
    "FakeNotificationPlugin",
    "FakeRequestFilterPlugin",
    "FakeURLTransformPlugin",
    "FakeUnprivilegedPlugin",
    "LoadedPlugin",
    "PluginBase",
    "PluginContext",
    "PluginError",
    "PluginExecutionError",
    "PluginHookManager",
    "PluginHookName",
    "PluginLoadError",
    "PluginLoader",
    "PluginManifest",
    "PluginManifestValidationError",
    "PluginNotFoundError",
    "PluginPermission",
    "PluginPermissionDeniedError",
    "PluginPermissionValidator",
    "PluginProtocol",
    "PluginSandbox",
    "PluginState",
    "PluginStorage",
    "RegisteredHook",
    "create_fake_manifest",
    "create_fake_plugin_directory",
]
