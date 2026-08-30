"""
CLI Application Context and Bus Configuration (Epic E13).
Wires CommandBus, QueryBus, EventBus, JobLifecycleService, BackendRegistry,
and Acquisition Services into a unified application container.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from shusha.acquisition.detector import AcquisitionDetector
from shusha.acquisition.inspector import AcquisitionInspector
from shusha.acquisition.resolver import AcquisitionResolver, ResolutionResult
from shusha.application.command_bus import CommandBus
from shusha.application.commands import (
    CancelJobCommand,
    CreateJobCommand,
    CreateJobGroupCommand,
    PauseJobCommand,
    RemoveJobCommand,
    ResumeJobCommand,
    RetryJobCommand,
    StartJobCommand,
)
from shusha.application.event_bus import EventBus
from shusha.application.queries import (
    GetCapabilitiesQuery,
    GetDiagnosticsQuery,
    GetGlobalStatisticsQuery,
    GetJobGroupQuery,
    GetJobQuery,
    ListJobsQuery,
    ResolveAcquisitionQuery,
)
from shusha.application.query_bus import QueryBus
from shusha.application.services.job_lifecycle import JobLifecycleService
from shusha.application.use_cases.download_use_cases import AddDownloadRequest
from shusha.backends.aria2.adapter import Aria2Backend
from shusha.backends.registry import BackendRegistry
from shusha.domain.download import Download
from shusha.domain.errors import DownloadNotFoundError
from shusha.domain.identifiers import (
    DownloadId,
    make_backend_id,
)
from shusha.domain.job import Job
from shusha.infrastructure.diagnostics import generate_diagnostics_report
from shusha.presentation.app_context import AppContext

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class CliContext:
    """Dependency container for CLI operation handling."""

    command_bus: CommandBus
    query_bus: QueryBus
    event_bus: EventBus
    lifecycle_service: JobLifecycleService
    backend_registry: BackendRegistry
    detector: AcquisitionDetector
    inspector: AcquisitionInspector
    resolver: AcquisitionResolver
    app_context: AppContext | None = None
    extra_handlers: dict[str, Any] = field(default_factory=dict)


def build_cli_context(app_context: AppContext | None = None) -> CliContext:
    """Build and wire application command/query buses for CLI operations."""
    event_bus = EventBus()
    lifecycle_service = JobLifecycleService(event_bus)
    backend_registry = BackendRegistry()

    # Register default aria2 backend
    if app_context:
        aria2_backend = Aria2Backend(
            client=app_context.client,
            supervisor=getattr(app_context, "daemon_supervisor", None),
        )
        backend_registry.register(aria2_backend, default=True)

    detector = AcquisitionDetector()
    inspector = AcquisitionInspector()
    resolver = AcquisitionResolver()

    command_bus = CommandBus()
    query_bus = QueryBus()

    # Register Command Handlers
    def handle_create_job(cmd: CreateJobCommand) -> list[str] | Job:
        if (
            app_context
            and hasattr(app_context, "add_download_uc")
            and app_context.add_download_uc
        ):
            cat_id = cmd.category_id
            req = AddDownloadRequest(
                uris=[cmd.source_input] if cmd.source_input else None,
                custom_dir=None,
                category_id=cat_id,
                options=cmd.options,
            )
            created_ids = app_context.add_download_uc.execute(req)
            return [str(cid) for cid in created_ids]

        bid = cmd.backend_id or make_backend_id("aria2")
        job = lifecycle_service.create_job(
            name=cmd.name,
            source_input=cmd.source_input,
            backend_id=bid,
            category_id=cmd.category_id,
            group_id=cmd.group_id,
            options=cmd.options,
        )
        return job

    def handle_start_job(cmd: StartJobCommand) -> Job:
        return lifecycle_service.start_job(cmd.job_id)

    def handle_pause_job(cmd: PauseJobCommand) -> None:
        if (
            app_context
            and hasattr(app_context, "pause_download_uc")
            and app_context.pause_download_uc
        ):
            app_context.pause_download_uc.execute(
                DownloadId(str(cmd.job_id)), force=False
            )
            return
        lifecycle_service.pause_job(cmd.job_id)

    def handle_resume_job(cmd: ResumeJobCommand) -> None:
        if (
            app_context
            and hasattr(app_context, "resume_download_uc")
            and app_context.resume_download_uc
        ):
            app_context.resume_download_uc.execute(DownloadId(str(cmd.job_id)))
            return
        lifecycle_service.resume_job(cmd.job_id)

    def handle_cancel_job(cmd: CancelJobCommand) -> None:
        if (
            app_context
            and hasattr(app_context, "remove_download_uc")
            and app_context.remove_download_uc
        ):
            app_context.remove_download_uc.execute(
                DownloadId(str(cmd.job_id)), delete_files=False, force=True
            )
            return
        lifecycle_service.cancel_job(cmd.job_id)

    def handle_remove_job(cmd: RemoveJobCommand) -> None:
        if (
            app_context
            and hasattr(app_context, "remove_download_uc")
            and app_context.remove_download_uc
        ):
            app_context.remove_download_uc.execute(
                DownloadId(str(cmd.job_id)), delete_files=cmd.delete_files, force=False
            )
            return
        lifecycle_service.remove_job(cmd.job_id, delete_files=cmd.delete_files)

    def handle_retry_job(cmd: RetryJobCommand) -> Job:
        return lifecycle_service.retry_job(cmd.job_id)

    def handle_create_job_group(cmd: CreateJobGroupCommand) -> Any:
        return None

    command_bus.register(CreateJobCommand, handle_create_job)
    command_bus.register(StartJobCommand, handle_start_job)
    command_bus.register(PauseJobCommand, handle_pause_job)
    command_bus.register(ResumeJobCommand, handle_resume_job)
    command_bus.register(CancelJobCommand, handle_cancel_job)
    command_bus.register(RemoveJobCommand, handle_remove_job)
    command_bus.register(RetryJobCommand, handle_retry_job)
    command_bus.register(CreateJobGroupCommand, handle_create_job_group)

    # Register Query Handlers
    def handle_get_job(query: GetJobQuery) -> Job | Download | None:
        if (
            app_context
            and hasattr(app_context, "download_repo")
            and app_context.download_repo
        ):
            try:
                dl = app_context.download_repo.get_by_id(DownloadId(str(query.job_id)))
                if dl is not None:
                    return dl
            except Exception:
                pass
        try:
            return lifecycle_service.get_job(query.job_id)
        except DownloadNotFoundError:
            return None

    def handle_list_jobs(query: ListJobsQuery) -> list[Job | Download]:
        if (
            app_context
            and hasattr(app_context, "download_repo")
            and app_context.download_repo
        ):
            res: list[Job | Download]
            if query.category_id:
                res = list(
                    app_context.download_repo.list_by_category(query.category_id)
                )
            elif query.state:
                res = list(app_context.download_repo.list_by_state(query.state))
            else:
                res = list(app_context.download_repo.list_all())
            return res

        jobs = lifecycle_service.list_jobs(
            state=query.state,
            backend_id=query.backend_id,
            category_id=query.category_id,
        )
        return list(jobs[query.offset : query.offset + query.limit])

    def handle_resolve_acquisition(query: ResolveAcquisitionQuery) -> ResolutionResult:
        req = detector.detect(
            raw_input=query.raw_input,
            preferred_backend=query.preferred_backend,
        )
        inspection = inspector.inspect(req)
        backends = backend_registry.list_backends()
        return resolver.resolve(req, inspection=inspection, available_backends=backends)

    def handle_get_diagnostics(query: GetDiagnosticsQuery) -> dict[str, Any]:
        db_m = (
            app_context.download_repo.db_manager
            if app_context and hasattr(app_context, "download_repo")
            else None
        )
        settings_s = (
            app_context.settings_store
            if app_context and hasattr(app_context, "settings_store")
            else None
        )
        report = generate_diagnostics_report(db_manager=db_m, settings_store=settings_s)

        if query.include_backends:
            backends_diag: dict[str, Any] = {}
            for b in backend_registry.list_backends():
                try:
                    diag = b.get_diagnostics()
                    backends_diag[str(b.identity.id)] = {
                        "name": b.identity.name,
                        "healthy": diag.healthy,
                        "uptime_seconds": diag.uptime_seconds,
                        "active_jobs": diag.active_jobs,
                        "details": diag.details,
                    }
                except Exception as e:
                    backends_diag[str(b.identity.id)] = {
                        "healthy": False,
                        "error": str(e),
                    }
            report["backends"] = backends_diag

        return report

    def handle_get_capabilities(query: GetCapabilitiesQuery) -> Any:
        if query.backend_id:
            backend = backend_registry.get(query.backend_id)
            return backend.capabilities if backend else None
        return {
            str(b.identity.id): b.capabilities for b in backend_registry.list_backends()
        }

    def handle_get_global_statistics(query: GetGlobalStatisticsQuery) -> Any:
        return {}

    def handle_get_job_group(query: GetJobGroupQuery) -> Any:
        return None

    query_bus.register(GetJobQuery, handle_get_job)
    query_bus.register(ListJobsQuery, handle_list_jobs)
    query_bus.register(ResolveAcquisitionQuery, handle_resolve_acquisition)
    query_bus.register(GetDiagnosticsQuery, handle_get_diagnostics)
    query_bus.register(GetCapabilitiesQuery, handle_get_capabilities)
    query_bus.register(GetGlobalStatisticsQuery, handle_get_global_statistics)
    query_bus.register(GetJobGroupQuery, handle_get_job_group)

    return CliContext(
        command_bus=command_bus,
        query_bus=query_bus,
        event_bus=event_bus,
        lifecycle_service=lifecycle_service,
        backend_registry=backend_registry,
        detector=detector,
        inspector=inspector,
        resolver=resolver,
        app_context=app_context,
    )
