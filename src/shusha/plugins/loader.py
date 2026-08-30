"""Plugin discovery, lifecycle management, and loader (Epic E10 / E14)."""

from __future__ import annotations

import importlib
import json
import logging
from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

from shusha.application.event_bus import EventBus
from shusha.domain.events import PluginFailedEvent, PluginLoadedEvent
from shusha.plugins.hooks import PluginHookManager, PluginHookName
from shusha.plugins.manifest import (
    PluginLoadError,
    PluginManifest,
    PluginNotFoundError,
)
from shusha.plugins.sandbox import (
    PluginContext,
    PluginPermissionValidator,
    PluginStorage,
)

logger = logging.getLogger(__name__)


class PluginState(StrEnum):
    """Lifecycle states of a plugin within Shusha."""

    DISCOVERED = "discovered"
    LOADED = "loaded"
    ACTIVE = "active"
    DISABLED = "disabled"
    FAILED = "failed"
    UNLOADED = "unloaded"


@runtime_checkable
class PluginProtocol(Protocol):
    """Protocol defining the lifecycle interface for Shusha plugins."""

    def on_load(self, context: PluginContext) -> None:
        """Invoked when the plugin is loaded into the host environment."""
        ...

    def on_unload(self) -> None:
        """Invoked when the plugin is unloaded to release resources."""
        ...


class PluginBase:
    """Optional base class for plugins providing default empty lifecycle hooks."""

    def on_load(self, context: PluginContext) -> None:
        """Hook called upon plugin loading."""
        pass

    def on_unload(self) -> None:
        """Hook called upon plugin unloading."""
        pass

    def register_hooks(self, hook_manager: PluginHookManager) -> None:
        """Hook called to register custom extension handlers."""
        pass


@dataclass(slots=True, kw_only=True)
class LoadedPlugin:
    """Descriptor and state snapshot of a loaded plugin instance."""

    manifest: PluginManifest
    instance: Any
    context: PluginContext
    state: PluginState = PluginState.LOADED
    error_message: str | None = None
    loaded_at: datetime = field(default_factory=lambda: datetime.now(UTC))


class PluginLoader:
    """Manages plugin discovery, validation, lifecycle, and hook binding."""

    def __init__(
        self,
        *,
        hook_manager: PluginHookManager | None = None,
        event_bus: EventBus | None = None,
        validator: PluginPermissionValidator | None = None,
        storage_base_dir: Path | None = None,
        search_paths: Sequence[Path] | None = None,
    ) -> None:
        self._validator = validator or PluginPermissionValidator()
        self._hook_manager = hook_manager or PluginHookManager(
            validator=self._validator
        )
        self._event_bus = event_bus
        self._storage_base_dir = storage_base_dir or (
            Path.home() / ".shusha" / "plugin_data"
        )
        self._search_paths = list(search_paths or [])
        self._plugins: dict[str, LoadedPlugin] = {}

    @property
    def hook_manager(self) -> PluginHookManager:
        return self._hook_manager

    @property
    def validator(self) -> PluginPermissionValidator:
        return self._validator

    def discover_plugins(
        self, search_paths: Sequence[Path] | None = None
    ) -> list[PluginManifest]:
        """Scan directory paths for plugin manifest files."""
        paths_to_scan = list(search_paths or self._search_paths)
        manifests: list[PluginManifest] = []

        manifest_filenames = ("plugin.json", "manifest.json", "manifest.toml")
        for base_path in paths_to_scan:
            if not base_path.exists() or not base_path.is_dir():
                continue
            for item in base_path.iterdir():
                if item.is_dir():
                    for name in manifest_filenames:
                        candidate = item / name
                        if candidate.exists() and candidate.is_file():
                            try:
                                manifest = self._load_manifest_file(candidate)
                                manifests.append(manifest)
                            except Exception as err:
                                logger.warning(
                                    "Failed to parse manifest at %s: %s",
                                    candidate,
                                    err,
                                )
                elif item.is_file() and item.name in manifest_filenames:
                    try:
                        manifest = self._load_manifest_file(item)
                        manifests.append(manifest)
                    except Exception as err:
                        logger.warning(
                            "Failed to parse manifest file %s: %s", item, err
                        )

        return manifests

    def _load_manifest_file(self, file_path: Path) -> PluginManifest:
        text = file_path.read_text(encoding="utf-8")
        if file_path.suffix == ".json":
            raw_data = json.loads(text)
        elif file_path.suffix == ".toml":
            import tomllib

            raw_data = tomllib.loads(text)
        else:
            raw_data = json.loads(text)
        return PluginManifest.from_dict(raw_data)

    def load_plugin(
        self,
        manifest: PluginManifest,
        config: dict[str, Any] | None = None,
        entrypoint_obj: Any | None = None,
    ) -> LoadedPlugin:
        """Load, validate, instantiate, and activate a plugin."""
        plugin_id = manifest.id

        # 1. Unload existing if previously loaded
        if plugin_id in self._plugins:
            self.unload_plugin(plugin_id)

        try:
            # 2. Validate manifest and permissions
            manifest.validate()
            self._validator.validate_manifest_permissions(manifest)

            # 3. Resolve entrypoint object or module
            instance = self._resolve_entrypoint(manifest.entrypoint, entrypoint_obj)

            # 4. Create isolated storage and context
            storage = PluginStorage(
                base_dir=self._storage_base_dir,
                manifest=manifest,
                validator=self._validator,
            )
            context = PluginContext(
                manifest=manifest,
                config=config,
                storage=storage,
                validator=self._validator,
            )

            # 5. Initialize plugin
            if hasattr(instance, "on_load") and callable(instance.on_load):
                instance.on_load(context)

            # 6. Bind hooks automatically
            self._bind_plugin_hooks(manifest, instance)

            # 7. Record active plugin
            loaded = LoadedPlugin(
                manifest=manifest,
                instance=instance,
                context=context,
                state=PluginState.ACTIVE,
            )
            self._plugins[plugin_id] = loaded

            # 8. Emit event
            if self._event_bus:
                self._event_bus.publish(
                    PluginLoadedEvent(
                        plugin_id=manifest.id,
                        version=manifest.version,
                        capabilities=manifest.capabilities,
                    )
                )

            logger.info(
                "Plugin '%s' (v%s) loaded and activated successfully",
                manifest.id,
                manifest.version,
            )
            return loaded

        except Exception as err:
            logger.exception("Failed to load plugin '%s': %s", plugin_id, err)
            if self._event_bus:
                self._event_bus.publish(
                    PluginFailedEvent(
                        plugin_id=plugin_id,
                        error_message=str(err),
                    )
                )
            raise PluginLoadError(
                f"Failed to load plugin '{plugin_id}': {err}",
                plugin_id=plugin_id,
            ) from err

    def _resolve_entrypoint(
        self, entrypoint_str: str, entrypoint_obj: Any | None
    ) -> Any:
        if entrypoint_obj is not None:
            if isinstance(entrypoint_obj, type):
                return entrypoint_obj()
            return entrypoint_obj

        if ":" in entrypoint_str:
            module_name, class_name = entrypoint_str.split(":", 1)
            mod = importlib.import_module(module_name)
            cls = getattr(mod, class_name)
            return cls() if isinstance(cls, type) else cls
        else:
            mod = importlib.import_module(entrypoint_str)
            if hasattr(mod, "Plugin"):
                cls = mod.Plugin
                return cls() if isinstance(cls, type) else cls
            return mod

    def _bind_plugin_hooks(self, manifest: PluginManifest, instance: Any) -> None:
        """Bind hook methods declared on instance to PluginHookManager."""
        # 1. Custom hook registration method
        if hasattr(instance, "register_hooks") and callable(instance.register_hooks):
            instance.register_hooks(self._hook_manager)

        # 2. Convention-based hook discovery
        hook_mappings = {
            "on_acquisition_detected": PluginHookName.ON_ACQUISITION_DETECTED,
            "on_job_created": PluginHookName.ON_JOB_CREATED,
            "on_job_completed": PluginHookName.ON_JOB_COMPLETED,
            "on_job_failed": PluginHookName.ON_JOB_FAILED,
            "transform_url": PluginHookName.TRANSFORM_URL,
            "filter_request": PluginHookName.FILTER_REQUEST,
        }

        for attr_name, hook_name in hook_mappings.items():
            if hasattr(instance, attr_name) and callable(getattr(instance, attr_name)):
                self._hook_manager.register_hook(
                    plugin_id=manifest.id,
                    hook_name=hook_name,
                    handler=getattr(instance, attr_name),
                    manifest=manifest,
                )

    def unload_plugin(self, plugin_id: str) -> bool:
        """Unload and clean up a running plugin."""
        loaded = self._plugins.get(plugin_id)
        if not loaded:
            return False

        try:
            if hasattr(loaded.instance, "on_unload") and callable(
                loaded.instance.on_unload
            ):
                loaded.instance.on_unload()
        except Exception as err:
            logger.warning("Error during on_unload for plugin '%s': %s", plugin_id, err)

        self._hook_manager.unregister_plugin_hooks(plugin_id)
        loaded.state = PluginState.UNLOADED
        del self._plugins[plugin_id]
        logger.info("Plugin '%s' unloaded", plugin_id)
        return True

    def get_plugin(self, plugin_id: str) -> LoadedPlugin | None:
        """Retrieve loaded plugin descriptor by ID."""
        return self._plugins.get(plugin_id)

    def get_active_plugins(self) -> list[LoadedPlugin]:
        """Return list of all currently active plugins."""
        return [p for p in self._plugins.values() if p.state == PluginState.ACTIVE]

    def is_plugin_active(self, plugin_id: str) -> bool:
        """Check if plugin is loaded and active."""
        p = self._plugins.get(plugin_id)
        return p is not None and p.state == PluginState.ACTIVE

    def disable_plugin(self, plugin_id: str) -> None:
        """Temporarily deactivate plugin and unregister its hooks."""
        loaded = self._plugins.get(plugin_id)
        if not loaded:
            raise PluginNotFoundError(
                f"Plugin '{plugin_id}' not found.", plugin_id=plugin_id
            )
        self._hook_manager.unregister_plugin_hooks(plugin_id)
        loaded.state = PluginState.DISABLED

    def enable_plugin(self, plugin_id: str) -> None:
        """Re-activate disabled plugin and restore its hooks."""
        loaded = self._plugins.get(plugin_id)
        if not loaded:
            raise PluginNotFoundError(
                f"Plugin '{plugin_id}' not found.", plugin_id=plugin_id
            )
        self._bind_plugin_hooks(loaded.manifest, loaded.instance)
        loaded.state = PluginState.ACTIVE
