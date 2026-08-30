"""Fake test plugin fixtures for deterministic verification (Epic E10 / E14 / RULE-025)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from shusha.domain.acquisition import AcquisitionRequest
from shusha.domain.capability import Capability, CapabilitySet
from shusha.domain.job import Job
from shusha.plugins.loader import PluginBase
from shusha.plugins.manifest import PluginManifest, PluginPermission
from shusha.plugins.sandbox import PluginContext


def create_fake_manifest(
    *,
    id: str = "fake-plugin",
    name: str = "Fake Test Plugin",
    version: str = "1.0.0",
    api_version: str = "2.0.0",
    entrypoint: str = "fake_plugin:FakePlugin",
    description: str = "Fake plugin for deterministic testing",
    author: str = "Shusha Test Suite",
    license: str = "MIT",
    capabilities: CapabilitySet | None = None,
    permissions: set[PluginPermission] | None = None,
    config_schema: dict[str, Any] | None = None,
    is_trusted: bool = False,
) -> PluginManifest:
    """Create a valid PluginManifest for tests."""
    return PluginManifest(
        id=id,
        name=name,
        version=version,
        api_version=api_version,
        entrypoint=entrypoint,
        description=description,
        author=author,
        license=license,
        capabilities=capabilities
        or CapabilitySet.from_iterable([Capability.BASIC_DOWNLOAD]),
        permissions=frozenset(permissions or set()),
        config_schema=config_schema or {},
        is_trusted=is_trusted,
    )


class FakeURLTransformPlugin(PluginBase):
    """Test plugin that rewrites download URLs with TRANSFORM permission."""

    def __init__(self, prefix: str = "https://mirror.example.com/") -> None:
        self.prefix = prefix
        self.loaded = False
        self.unloaded = False

    def on_load(self, context: PluginContext) -> None:
        self.loaded = True

    def on_unload(self) -> None:
        self.unloaded = True

    def transform_url(self, url: str) -> str:
        if url.startswith("http://insecure.example.com/"):
            return url.replace(
                "http://insecure.example.com/", "https://secure.example.com/"
            )
        if not url.startswith("http"):
            return f"{self.prefix}{url}"
        return url


class FakeRequestFilterPlugin(PluginBase):
    """Test plugin that filters out disallowed acquisition requests."""

    def __init__(
        self, blocked_keywords: tuple[str, ...] = ("blocked", "malware")
    ) -> None:
        self.blocked_keywords = blocked_keywords

    def filter_request(self, request: AcquisitionRequest) -> bool:
        return all(kw not in request.raw_input.lower() for kw in self.blocked_keywords)


class FakeAuditLoggerPlugin(PluginBase):
    """Test plugin that records job lifecycle events into memory and storage."""

    def __init__(self) -> None:
        self.created_jobs: list[Job] = []
        self.completed_jobs: list[Job] = []
        self.failed_jobs: list[tuple[Job, str]] = []
        self.context: PluginContext | None = None

    def on_load(self, context: PluginContext) -> None:
        self.context = context

    def on_job_created(self, job: Job) -> None:
        self.created_jobs.append(job)
        if self.context and self.context.manifest.has_permission(
            PluginPermission.STORAGE
        ):
            self.context.storage.set(f"job_created_{job.id}", job.name)

    def on_job_completed(self, job: Job) -> None:
        self.completed_jobs.append(job)
        if self.context and self.context.manifest.has_permission(
            PluginPermission.STORAGE
        ):
            self.context.storage.set(f"job_completed_{job.id}", job.name)

    def on_job_failed(self, job: Job, error_message: str) -> None:
        self.failed_jobs.append((job, error_message))


class FakeNotificationPlugin(PluginBase):
    """Test plugin that triggers user notifications."""

    def __init__(self) -> None:
        self.context: PluginContext | None = None

    def on_load(self, context: PluginContext) -> None:
        self.context = context

    def notify_user(self, title: str, message: str) -> bool:
        if not self.context:
            return False
        return self.context.send_notification(title, message)


class FakeUnprivilegedPlugin(PluginBase):
    """Test plugin with NO declared permissions to verify sandbox enforcement."""

    def __init__(self) -> None:
        self.context: PluginContext | None = None

    def on_load(self, context: PluginContext) -> None:
        self.context = context

    def try_storage(self) -> None:
        if self.context:
            self.context.storage.set("key", "val")

    def try_notification(self) -> None:
        if self.context:
            self.context.send_notification("Test", "No permission")

    def try_clipboard_read(self) -> str:
        if self.context:
            return self.context.read_clipboard()
        return ""

    def try_network(self) -> bytes:
        if self.context:
            return self.context.fetch_url("https://example.com")
        return b""


def create_fake_plugin_directory(
    base_dir: Path,
    manifest: PluginManifest,
    code: str = "# Plugin entrypoint\n",
) -> Path:
    """Create a temporary plugin directory on disk containing manifest and code."""
    plugin_dir = base_dir / manifest.id
    plugin_dir.mkdir(parents=True, exist_ok=True)

    manifest_file = plugin_dir / "plugin.json"
    manifest_file.write_text(json.dumps(manifest.to_dict(), indent=2), encoding="utf-8")

    py_file = plugin_dir / "plugin.py"
    py_file.write_text(code, encoding="utf-8")

    return plugin_dir
