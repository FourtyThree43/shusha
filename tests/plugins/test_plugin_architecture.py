"""Comprehensive test suite for Plugin Architecture (Epic E10 / E14)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from shusha.application.event_bus import EventBus
from shusha.domain.acquisition import AcquisitionRequest, SourceKind
from shusha.domain.capability import Capability, CapabilitySet
from shusha.domain.events import PluginFailedEvent, PluginLoadedEvent
from shusha.domain.identifiers import make_acquisition_id, make_backend_id, make_job_id
from shusha.domain.job import Job
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
)
from shusha.plugins.loader import (
    PluginLoader,
    PluginState,
)
from shusha.plugins.manifest import (
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
    PluginStorage,
)


class TestPluginManifest:
    """Tests for PluginManifest validation, serialization, and permissions."""

    def test_valid_manifest_creation_and_serialization(self) -> None:
        manifest = PluginManifest(
            id="sample-plugin",
            name="Sample Plugin",
            version="1.2.3",
            api_version="2.0.0",
            entrypoint="sample:SamplePlugin",
            description="A sample test plugin",
            author="Developer",
            license="Apache-2.0",
            capabilities=CapabilitySet.from_iterable(
                [Capability.HTTP, Capability.TORRENT]
            ),
            permissions=frozenset(
                [
                    PluginPermission.STORAGE,
                    PluginPermission.TRANSFORM,
                ]
            ),
            config_schema={"timeout": {"type": "integer", "default": 30}},
            is_trusted=True,
        )

        manifest.validate()
        assert manifest.id == "sample-plugin"
        assert manifest.has_permission(PluginPermission.STORAGE)
        assert manifest.has_permission("transform")
        assert not manifest.has_permission(PluginPermission.NETWORK)
        assert manifest.has_capability(Capability.HTTP)

        data = manifest.to_dict()
        assert data["id"] == "sample-plugin"
        assert "storage" in data["permissions"]

        restored = PluginManifest.from_dict(data)
        assert restored.id == manifest.id
        assert restored.permissions == manifest.permissions
        assert restored.capabilities.has(Capability.HTTP)

    def test_invalid_manifest_id_fails(self) -> None:
        with pytest.raises(PluginManifestValidationError, match="Invalid plugin ID"):
            PluginManifest(
                id="invalid ID with spaces!",
                name="Test",
                version="1.0.0",
                api_version="2.0.0",
                entrypoint="mod:Plugin",
            ).validate()

    def test_empty_manifest_name_fails(self) -> None:
        with pytest.raises(PluginManifestValidationError, match="name cannot be empty"):
            PluginManifest(
                id="valid-id",
                name="",
                version="1.0.0",
                api_version="2.0.0",
                entrypoint="mod:Plugin",
            ).validate()

    def test_invalid_manifest_version_fails(self) -> None:
        with pytest.raises(
            PluginManifestValidationError, match="Invalid plugin version"
        ):
            PluginManifest(
                id="valid-id",
                name="Test",
                version="not_semver",
                api_version="2.0.0",
                entrypoint="mod:Plugin",
            ).validate()

    def test_invalid_manifest_entrypoint_fails(self) -> None:
        with pytest.raises(
            PluginManifestValidationError, match="entrypoint cannot be empty"
        ):
            PluginManifest(
                id="valid-id",
                name="Test",
                version="1.0.0",
                api_version="2.0.0",
                entrypoint="",
            ).validate()


class TestPluginPermissionValidator:
    """Tests for PluginPermissionValidator enforcement."""

    def test_check_and_require_permission_success(self) -> None:
        manifest = create_fake_manifest(
            permissions={PluginPermission.NETWORK, PluginPermission.STORAGE}
        )
        validator = PluginPermissionValidator()

        assert validator.check_permission(manifest, PluginPermission.NETWORK) is True
        assert validator.check_permission(manifest, "network") is True
        validator.require_permission(manifest, PluginPermission.STORAGE)

    def test_require_permission_failure(self) -> None:
        manifest = create_fake_manifest(permissions={PluginPermission.STORAGE})
        validator = PluginPermissionValidator()

        with pytest.raises(PluginPermissionDeniedError) as exc_info:
            validator.require_permission(manifest, PluginPermission.NOTIFICATIONS)

        assert exc_info.value.permission == PluginPermission.NOTIFICATIONS
        assert exc_info.value.plugin_id == manifest.id

    def test_untrusted_plugin_with_privileged_permission_fails(self) -> None:
        manifest = create_fake_manifest(
            permissions={PluginPermission.PROCESS},
            is_trusted=False,
        )
        validator = PluginPermissionValidator()
        with pytest.raises(
            PluginPermissionDeniedError, match="requires trusted plugin flag"
        ):
            validator.validate_manifest_permissions(manifest)

    def test_trusted_plugin_with_privileged_permission_allowed(self) -> None:
        manifest = create_fake_manifest(
            permissions={PluginPermission.PROCESS},
            is_trusted=True,
        )
        validator = PluginPermissionValidator()
        validator.validate_manifest_permissions(manifest)


class TestPluginStorageSandbox:
    """Tests for sandboxed directory and KV store isolation."""

    def test_storage_requires_permission(self, tmp_path: Path) -> None:
        unprivileged_manifest = create_fake_manifest(permissions=set())
        storage = PluginStorage(base_dir=tmp_path, manifest=unprivileged_manifest)

        with pytest.raises(PluginPermissionDeniedError):
            storage.set("key", "value")

        with pytest.raises(PluginPermissionDeniedError):
            storage.write_bytes("data.bin", b"hello")

    def test_storage_kv_operations(self, tmp_path: Path) -> None:
        manifest = create_fake_manifest(permissions={PluginPermission.STORAGE})
        storage = PluginStorage(base_dir=tmp_path, manifest=manifest)

        assert storage.get("nonexistent") is None
        assert storage.get("nonexistent", "default") == "default"

        storage.set("user_token", "abc-123")
        assert storage.get("user_token") == "abc-123"
        assert storage.list_keys() == ["user_token"]

        assert storage.delete("user_token") is True
        assert storage.get("user_token") is None
        assert storage.delete("user_token") is False

    def test_storage_file_operations_and_traversal_prevention(
        self, tmp_path: Path
    ) -> None:
        manifest = create_fake_manifest(permissions={PluginPermission.STORAGE})
        storage = PluginStorage(base_dir=tmp_path, manifest=manifest)

        storage.write_bytes("folder/test.txt", b"sandboxed payload")
        assert storage.read_bytes("folder/test.txt") == b"sandboxed payload"
        assert "folder/test.txt" in storage.list_files()

        with pytest.raises(PluginPermissionDeniedError, match="Path traversal denied"):
            storage.write_bytes("../outside.txt", b"evil")


class TestPluginContextSandbox:
    """Tests for PluginContext permission gating."""

    def test_send_notification_permission(self, tmp_path: Path) -> None:
        notification_sink = MagicMock()
        manifest_with_perm = create_fake_manifest(
            permissions={PluginPermission.NOTIFICATIONS, PluginPermission.STORAGE}
        )
        storage = PluginStorage(base_dir=tmp_path, manifest=manifest_with_perm)
        ctx = PluginContext(
            manifest=manifest_with_perm,
            storage=storage,
            notification_sink=notification_sink,
        )

        assert ctx.send_notification("Title", "Message") is True
        notification_sink.assert_called_once_with("Title", "Message")

        manifest_without_perm = create_fake_manifest(
            permissions={PluginPermission.STORAGE}
        )
        ctx_denied = PluginContext(
            manifest=manifest_without_perm,
            storage=storage,
            notification_sink=notification_sink,
        )
        with pytest.raises(PluginPermissionDeniedError):
            ctx_denied.send_notification("Title", "Denied")

    def test_clipboard_permissions(self, tmp_path: Path) -> None:
        getter = MagicMock(return_value="https://clip.example.com")
        setter = MagicMock()

        manifest_with_perm = create_fake_manifest(
            permissions={PluginPermission.CLIPBOARD, PluginPermission.STORAGE}
        )
        storage = PluginStorage(base_dir=tmp_path, manifest=manifest_with_perm)
        ctx = PluginContext(
            manifest=manifest_with_perm,
            storage=storage,
            clipboard_getter=getter,
            clipboard_setter=setter,
        )

        assert ctx.read_clipboard() == "https://clip.example.com"
        ctx.write_clipboard("new_clip")
        setter.assert_called_once_with("new_clip")

        manifest_denied = create_fake_manifest(permissions={PluginPermission.STORAGE})
        ctx_denied = PluginContext(manifest=manifest_denied, storage=storage)
        with pytest.raises(PluginPermissionDeniedError):
            ctx_denied.read_clipboard()
        with pytest.raises(PluginPermissionDeniedError):
            ctx_denied.write_clipboard("test")

    def test_fetch_url_requires_network_permission(self, tmp_path: Path) -> None:
        manifest = create_fake_manifest(permissions={PluginPermission.STORAGE})
        storage = PluginStorage(base_dir=tmp_path, manifest=manifest)
        ctx = PluginContext(manifest=manifest, storage=storage)

        with pytest.raises(PluginPermissionDeniedError):
            ctx.fetch_url("https://example.com")


class TestPluginHookManager:
    """Tests for typed extension points and execution isolation."""

    def test_transform_url_sequential_execution(self) -> None:
        hook_mgr = PluginHookManager()
        manifest = create_fake_manifest(
            id="url-plugin", permissions={PluginPermission.TRANSFORM}
        )

        def add_param(url: str) -> str:
            return f"{url}?ref=plugin1"

        def change_host(url: str) -> str:
            return url.replace("example.com", "mirror.com")

        hook_mgr.register_hook(
            plugin_id="url-plugin",
            hook_name=PluginHookName.TRANSFORM_URL,
            handler=add_param,
            manifest=manifest,
            priority=10,
        )
        hook_mgr.register_hook(
            plugin_id="url-plugin",
            hook_name=PluginHookName.TRANSFORM_URL,
            handler=change_host,
            manifest=manifest,
            priority=20,
        )

        result = hook_mgr.run_transform_url("https://example.com/file.zip")
        assert result == "https://mirror.com/file.zip?ref=plugin1"

    def test_filter_request_behavior(self) -> None:
        hook_mgr = PluginHookManager()
        manifest = create_fake_manifest(
            id="filter-plugin", permissions={PluginPermission.TRANSFORM}
        )

        filter_plugin = FakeRequestFilterPlugin(blocked_keywords=("malware", "blocked"))
        hook_mgr.register_hook(
            plugin_id="filter-plugin",
            hook_name=PluginHookName.FILTER_REQUEST,
            handler=filter_plugin.filter_request,
            manifest=manifest,
        )

        allowed_req = AcquisitionRequest(
            id=make_acquisition_id("acq-1"),
            source_kind=SourceKind.MANUAL,
            raw_input="https://good.org/file.iso",
        )
        assert hook_mgr.run_filter_request(allowed_req) is True

        blocked_req = AcquisitionRequest(
            id=make_acquisition_id("acq-2"),
            source_kind=SourceKind.MANUAL,
            raw_input="https://bad.org/malware.exe",
        )
        assert hook_mgr.run_filter_request(blocked_req) is False

    def test_on_job_completed_and_failure_isolation(self) -> None:
        hook_mgr = PluginHookManager()
        job = Job(
            id=make_job_id("j-100"),
            backend_id=make_backend_id("aria2"),
            name="archive.tar.gz",
        )

        received_jobs: list[Job] = []

        def failing_handler(j: Job) -> None:
            raise RuntimeError("Handler crashed unexpectedly!")

        def healthy_handler(j: Job) -> None:
            received_jobs.append(j)

        hook_mgr.register_hook(
            "broken-plugin", PluginHookName.ON_JOB_COMPLETED, failing_handler
        )
        hook_mgr.register_hook(
            "good-plugin", PluginHookName.ON_JOB_COMPLETED, healthy_handler
        )

        # Should not raise exception even though one handler failed
        hook_mgr.run_on_job_completed(job)
        assert len(received_jobs) == 1
        assert received_jobs[0].id == job.id

    def test_unregister_plugin_hooks(self) -> None:
        hook_mgr = PluginHookManager()
        hook_mgr.register_hook(
            "plugin-a", PluginHookName.TRANSFORM_URL, lambda u: u + "/a"
        )
        hook_mgr.register_hook(
            "plugin-b", PluginHookName.TRANSFORM_URL, lambda u: u + "/b"
        )

        assert len(hook_mgr.get_hooks(PluginHookName.TRANSFORM_URL)) == 2
        hook_mgr.unregister_plugin_hooks("plugin-a")
        assert len(hook_mgr.get_hooks(PluginHookName.TRANSFORM_URL)) == 1
        assert (
            hook_mgr.get_hooks(PluginHookName.TRANSFORM_URL)[0].plugin_id == "plugin-b"
        )


class TestPluginLoader:
    """Tests for PluginLoader discovery, loading, lifecycle, and event emission."""

    def test_load_and_unload_plugin_with_event_bus(self, tmp_path: Path) -> None:
        event_bus = EventBus()
        loaded_events: list[PluginLoadedEvent] = []
        event_bus.subscribe(PluginLoadedEvent, loaded_events.append)

        loader = PluginLoader(event_bus=event_bus, storage_base_dir=tmp_path)
        manifest = create_fake_manifest(
            id="audit-plugin",
            permissions={PluginPermission.STORAGE},
        )
        plugin_instance = FakeAuditLoggerPlugin()

        loaded = loader.load_plugin(
            manifest=manifest,
            entrypoint_obj=plugin_instance,
        )

        assert loaded.state == PluginState.ACTIVE
        assert loader.is_plugin_active("audit-plugin") is True
        assert len(loaded_events) == 1
        assert loaded_events[0].plugin_id == "audit-plugin"

        # Verify hooks automatically registered
        job = Job(
            id=make_job_id("job-1"),
            backend_id=make_backend_id("aria2"),
            name="video.mp4",
        )
        loader.hook_manager.run_on_job_created(job)
        assert len(plugin_instance.created_jobs) == 1

        # Verify storage key written by plugin on job created
        assert loaded.context.storage.get(f"job_created_{job.id}") == "video.mp4"

        # Unload plugin
        unloaded = loader.unload_plugin("audit-plugin")
        assert unloaded is True
        assert loader.is_plugin_active("audit-plugin") is False
        assert loader.get_plugin("audit-plugin") is None

    def test_discover_plugins_from_directory(self, tmp_path: Path) -> None:
        manifest_a = create_fake_manifest(id="plugin-alpha", name="Alpha")
        manifest_b = create_fake_manifest(id="plugin-beta", name="Beta")

        create_fake_plugin_directory(tmp_path, manifest_a)
        create_fake_plugin_directory(tmp_path, manifest_b)

        loader = PluginLoader(search_paths=[tmp_path])
        discovered = loader.discover_plugins()

        discovered_ids = {m.id for m in discovered}
        assert "plugin-alpha" in discovered_ids
        assert "plugin-beta" in discovered_ids

    def test_load_plugin_failure_emits_event(self, tmp_path: Path) -> None:
        event_bus = EventBus()
        failed_events: list[PluginFailedEvent] = []
        event_bus.subscribe(PluginFailedEvent, failed_events.append)

        loader = PluginLoader(event_bus=event_bus, storage_base_dir=tmp_path)
        manifest = create_fake_manifest(
            id="bad-plugin",
            permissions={PluginPermission.PROCESS},
            is_trusted=False,  # Will fail permission validation!
        )

        with pytest.raises(PluginLoadError):
            loader.load_plugin(manifest=manifest)

        assert len(failed_events) == 1
        assert failed_events[0].plugin_id == "bad-plugin"

    def test_disable_and_enable_plugin(self, tmp_path: Path) -> None:
        loader = PluginLoader(storage_base_dir=tmp_path)
        manifest = create_fake_manifest(
            id="toggle-plugin", permissions={PluginPermission.TRANSFORM}
        )
        plugin = FakeURLTransformPlugin()
        loader.load_plugin(manifest=manifest, entrypoint_obj=plugin)

        assert (
            loader.hook_manager.run_transform_url("file.iso")
            == "https://mirror.example.com/file.iso"
        )

        loader.disable_plugin("toggle-plugin")
        plug = loader.get_plugin("toggle-plugin")
        assert plug is not None
        assert plug.state == PluginState.DISABLED
        assert loader.is_plugin_active("toggle-plugin") is False
        # Hook is unregistered while disabled:
        assert loader.hook_manager.run_transform_url("file.iso") == "file.iso"

        loader.enable_plugin("toggle-plugin")
        assert loader.is_plugin_active("toggle-plugin") is True
        assert (
            loader.hook_manager.run_transform_url("file.iso")
            == "https://mirror.example.com/file.iso"
        )

    def test_disable_nonexistent_plugin_raises(self) -> None:
        loader = PluginLoader()
        with pytest.raises(PluginNotFoundError):
            loader.disable_plugin("unknown-id")


class TestFakePluginFixtures:
    """Tests for deterministic fake plugin fixtures."""

    def test_fake_unprivileged_plugin_sandbox_rejection(self, tmp_path: Path) -> None:
        manifest = create_fake_manifest(id="unprivileged", permissions=set())
        plugin = FakeUnprivilegedPlugin()
        loader = PluginLoader(storage_base_dir=tmp_path)
        loader.load_plugin(manifest=manifest, entrypoint_obj=plugin)

        with pytest.raises(PluginPermissionDeniedError):
            plugin.try_storage()

        with pytest.raises(PluginPermissionDeniedError):
            plugin.try_notification()

        with pytest.raises(PluginPermissionDeniedError):
            plugin.try_clipboard_read()

        with pytest.raises(PluginPermissionDeniedError):
            plugin.try_network()

    def test_fake_notification_plugin(self, tmp_path: Path) -> None:
        manifest = create_fake_manifest(
            id="notifier",
            permissions={PluginPermission.NOTIFICATIONS, PluginPermission.STORAGE},
        )
        plugin = FakeNotificationPlugin()
        loader = PluginLoader(storage_base_dir=tmp_path)
        loader.load_plugin(manifest=manifest, entrypoint_obj=plugin)

        assert plugin.notify_user("Shusha", "Download Ready") is True
