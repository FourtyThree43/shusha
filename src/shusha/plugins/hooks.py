"""Typed plugin extension points and hook manager (Epic E10 / E14)."""

from __future__ import annotations

import logging
from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from shusha.domain.acquisition import AcquisitionRequest
from shusha.domain.job import Job
from shusha.plugins.manifest import PluginManifest, PluginPermission
from shusha.plugins.sandbox import PluginPermissionValidator

logger = logging.getLogger(__name__)


class PluginHookName(StrEnum):
    """Authoritative names for typed plugin extension points."""

    ON_ACQUISITION_DETECTED = "on_acquisition_detected"
    ON_JOB_CREATED = "on_job_created"
    ON_JOB_COMPLETED = "on_job_completed"
    ON_JOB_FAILED = "on_job_failed"
    TRANSFORM_URL = "transform_url"
    FILTER_REQUEST = "filter_request"


@dataclass(frozen=True, slots=True)
class RegisteredHook:
    """Descriptor of a registered plugin hook handler."""

    plugin_id: str
    hook_name: str
    handler: Callable[..., Any]
    manifest: PluginManifest | None = None
    priority: int = 100


class PluginHookManager:
    """Central registry and dispatch manager for typed plugin extension hooks."""

    def __init__(self, validator: PluginPermissionValidator | None = None) -> None:
        self._hooks: dict[str, list[RegisteredHook]] = defaultdict(list)
        self._validator = validator or PluginPermissionValidator()

    def register_hook(
        self,
        plugin_id: str,
        hook_name: PluginHookName | str,
        handler: Callable[..., Any],
        manifest: PluginManifest | None = None,
        priority: int = 100,
    ) -> None:
        """Register a callback for an extension hook with permission checking."""
        normalized_name = str(hook_name).lower()
        if manifest and normalized_name in (
            PluginHookName.TRANSFORM_URL,
            PluginHookName.FILTER_REQUEST,
        ):
            self._validator.require_permission(manifest, PluginPermission.TRANSFORM)

        hook = RegisteredHook(
            plugin_id=plugin_id,
            hook_name=normalized_name,
            handler=handler,
            manifest=manifest,
            priority=priority,
        )
        self._hooks[normalized_name].append(hook)
        self._hooks[normalized_name].sort(key=lambda h: h.priority)

    def unregister_plugin_hooks(self, plugin_id: str) -> None:
        """Unregister all hooks associated with a specific plugin."""
        for hook_name in list(self._hooks.keys()):
            self._hooks[hook_name] = [
                h for h in self._hooks[hook_name] if h.plugin_id != plugin_id
            ]

    def clear(self) -> None:
        """Clear all registered hooks."""
        self._hooks.clear()

    def get_hooks(self, hook_name: PluginHookName | str) -> list[RegisteredHook]:
        """Return registered hooks for a hook name."""
        return list(self._hooks.get(str(hook_name).lower(), []))

    # --- Typed Extension Point Invocations ---

    def run_transform_url(self, url: str) -> str:
        """Pass URL through registered transform_url hooks sequentially."""
        current_url = url
        for hook in self.get_hooks(PluginHookName.TRANSFORM_URL):
            try:
                res = hook.handler(current_url)
                if isinstance(res, str) and res.strip():
                    current_url = res.strip()
            except Exception as err:
                logger.exception(
                    "Error executing transform_url hook from plugin '%s': %s",
                    hook.plugin_id,
                    err,
                )
        return current_url

    def run_filter_request(self, request: AcquisitionRequest) -> bool:
        """Execute request filters. Returns False if any hook rejects the request."""
        for hook in self.get_hooks(PluginHookName.FILTER_REQUEST):
            try:
                res = hook.handler(request)
                if res is False:
                    logger.info(
                        "Request %s filtered/rejected by plugin '%s'",
                        request.id,
                        hook.plugin_id,
                    )
                    return False
            except Exception as err:
                logger.exception(
                    "Error executing filter_request hook from plugin '%s': %s",
                    hook.plugin_id,
                    err,
                )
        return True

    def run_on_acquisition_detected(
        self, request: AcquisitionRequest
    ) -> AcquisitionRequest:
        """Execute on_acquisition_detected hooks sequentially."""
        current_request = request
        for hook in self.get_hooks(PluginHookName.ON_ACQUISITION_DETECTED):
            try:
                res = hook.handler(current_request)
                if isinstance(res, AcquisitionRequest):
                    current_request = res
            except Exception as err:
                logger.exception(
                    "Error executing on_acquisition_detected hook from plugin '%s': %s",
                    hook.plugin_id,
                    err,
                )
        return current_request

    def run_on_job_created(self, job: Job) -> Job:
        """Execute on_job_created hooks sequentially."""
        current_job = job
        for hook in self.get_hooks(PluginHookName.ON_JOB_CREATED):
            try:
                res = hook.handler(current_job)
                if isinstance(res, Job):
                    current_job = res
            except Exception as err:
                logger.exception(
                    "Error executing on_job_created hook from plugin '%s': %s",
                    hook.plugin_id,
                    err,
                )
        return current_job

    def run_on_job_completed(self, job: Job) -> None:
        """Broadcast job completion to registered hooks."""
        for hook in self.get_hooks(PluginHookName.ON_JOB_COMPLETED):
            try:
                hook.handler(job)
            except Exception as err:
                logger.exception(
                    "Error executing on_job_completed hook from plugin '%s': %s",
                    hook.plugin_id,
                    err,
                )

    def run_on_job_failed(self, job: Job, error_message: str) -> None:
        """Broadcast job failure to registered hooks."""
        for hook in self.get_hooks(PluginHookName.ON_JOB_FAILED):
            try:
                hook.handler(job, error_message)
            except Exception as err:
                logger.exception(
                    "Error executing on_job_failed hook from plugin '%s': %s",
                    hook.plugin_id,
                    err,
                )
