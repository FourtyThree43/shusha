"""Authoritative aria2 Reference Backend Adapter (Epic E07)."""

from __future__ import annotations

import logging
from dataclasses import replace
from pathlib import Path
from typing import Any

from shusha.backends.aria2.options import load_aria2_options
from shusha.backends.aria2.supervisor import Aria2Supervisor
from shusha.backends.contract import (
    BackendDiagnostics,
    BackendIdentity,
    BackendProtocol,
)
from shusha.backends.errors import (
    BackendConnectionError,
    BackendExecutionError,
    BackendJobNotFoundError,
)
from shusha.backends.options import BackendOptionSpec
from shusha.domain.artifact import Artifact, ArtifactKind, ArtifactStatus
from shusha.domain.capability import Capability, CapabilitySet
from shusha.domain.identifiers import (
    JobId,
    make_artifact_id,
    make_backend_id,
    make_gid,
)
from shusha.domain.job import Job, JobProgress
from shusha.domain.states import DownloadState
from shusha.infrastructure.aria2.client import Aria2Client
from shusha.infrastructure.aria2.errors import (
    Aria2ConnectionError,
    Aria2DownloadNotFoundError,
    Aria2RpcError,
)
from shusha.infrastructure.aria2.jsonrpc import JsonRpcTransport

logger = logging.getLogger(__name__)

ARIA2_CAPABILITIES = CapabilitySet.from_iterable(
    [
        Capability.BASIC_DOWNLOAD,
        Capability.PAUSE_RESUME,
        Capability.CANCEL,
        Capability.RETRY,
        Capability.QUEUE,
        Capability.SCHEDULING,
        Capability.MULTIPLE_SOURCES,
        Capability.SEGMENTATION,
        Capability.HTTP,
        Capability.HTTPS,
        Capability.FTP,
        Capability.SFTP,
        Capability.TORRENT,
        Capability.MAGNET,
        Capability.METALINK,
        Capability.TORRENT_FILES,
        Capability.TORRENT_PEERS,
        Capability.TORRENT_TRACKERS,
        Capability.SERVER_STATUS,
        Capability.PIECE_STATUS,
        Capability.CHECKSUM,
        Capability.COOKIES,
        Capability.AUTHENTICATION,
        Capability.PROXY,
        Capability.RATE_LIMIT,
        Capability.FILE_SELECTION,
        Capability.INPUT_FILE,
        Capability.SESSION_SAVE,
        Capability.REMOTE_RPC,
        Capability.METADATA,
    ]
)


class Aria2Backend(BackendProtocol):
    """Full-featured backend adapter for aria2 daemon and RPC."""

    def __init__(
        self,
        client: Aria2Client | None = None,
        supervisor: Aria2Supervisor | None = None,
        backend_id: str = "aria2",
        manage_supervisor: bool = False,
    ) -> None:
        self._identity = BackendIdentity(
            id=make_backend_id(backend_id),
            name="aria2 Reference Backend",
            version="1.37.0",
            description="High-performance multi-source & multi-protocol download acquisition engine",
            vendor="aria2 project",
        )
        self._capabilities = ARIA2_CAPABILITIES
        self._client = client or Aria2Client(transport=JsonRpcTransport())
        self._supervisor = supervisor
        self._manage_supervisor = manage_supervisor
        self._job_gid_map: dict[JobId, str] = {}
        self._gid_job_map: dict[str, JobId] = {}

    @property
    def identity(self) -> BackendIdentity:
        return self._identity

    @property
    def capabilities(self) -> CapabilitySet:
        return self._capabilities

    def initialize(self, config: dict[str, Any] | None = None) -> None:
        """Initialize transport and start local supervisor if configured."""
        if config:
            host = config.get("host", "127.0.0.1")
            port = int(config.get("port", 6800))
            secret = config.get("secret", "")
            use_ssl = bool(config.get("use_ssl", False))
            proto = "https" if use_ssl else "http"
            endpoint = f"{proto}://{host}:{port}/jsonrpc"
            self._client = Aria2Client(
                transport=JsonRpcTransport(
                    endpoint=endpoint,
                    secret=secret or None,
                )
            )

        if self._manage_supervisor and self._supervisor:
            self._supervisor.start()

    def shutdown(self) -> None:
        """Stop supervised process if managed."""
        if self._manage_supervisor and self._supervisor:
            self._supervisor.stop()

    def ping(self) -> bool:
        """Verify liveness of aria2 RPC endpoint."""
        try:
            res = self._client.get_version()
            if not res:
                return False
            if hasattr(res, "version"):
                return bool(res.version)
            if isinstance(res, (tuple, list)) and len(res) > 0:
                return bool(res[0])
            return bool(res)
        except Exception:
            return False

    def submit_job(self, job: Job) -> Job:
        """Submit a new download to aria2 via addUri, addTorrent, or addMetalink."""
        source_input = (
            job.source.uri.raw_uri
            if job.source
            else (job.request.raw_input if job.request else "")
        )

        try:
            gid = self._client.add_uri([source_input], options=job.metadata)
            gid_str = str(gid)
            self._job_gid_map[job.id] = gid_str
            self._gid_job_map[gid_str] = job.id

            updated_backend_data = dict(job.backend_data)
            updated_backend_data["aria2_gid"] = gid_str

            return replace(
                job,
                state=DownloadState.ACTIVE,
                backend_data=updated_backend_data,
            )
        except Aria2ConnectionError as err:
            raise BackendConnectionError(
                f"Failed to connect to aria2: {err}", backend_id=self.identity.id
            ) from err
        except Aria2RpcError as err:
            raise BackendExecutionError(
                f"aria2 RPC error on submit: {err}", backend_id=self.identity.id
            ) from err

    def pause_job(self, job_id: JobId) -> Job:
        """Pause a running download in aria2."""
        gid = self._get_gid(job_id)
        try:
            self._client.pause(make_gid(gid))
            return self.get_job_status(job_id)
        except Aria2RpcError as err:
            raise BackendExecutionError(
                f"Failed to pause job {job_id}: {err}", backend_id=self.identity.id
            ) from err

    def resume_job(self, job_id: JobId) -> Job:
        """Resume / unpause a paused download in aria2."""
        gid = self._get_gid(job_id)
        try:
            self._client.unpause(make_gid(gid))
            return self.get_job_status(job_id)
        except Aria2RpcError as err:
            raise BackendExecutionError(
                f"Failed to resume job {job_id}: {err}", backend_id=self.identity.id
            ) from err

    def cancel_job(self, job_id: JobId) -> Job:
        """Remove / cancel a download in aria2."""
        gid = self._get_gid(job_id)
        try:
            self._client.remove(make_gid(gid), force=True)
            return self.get_job_status(job_id)
        except Aria2RpcError as err:
            raise BackendExecutionError(
                f"Failed to cancel job {job_id}: {err}", backend_id=self.identity.id
            ) from err

    def remove_job(self, job_id: JobId, delete_files: bool = False) -> None:
        """Remove completed or stopped download result from aria2 memory."""
        gid = self._get_gid(job_id)
        try:
            self._client.remove_download_result(make_gid(gid))
        except Aria2RpcError:
            pass  # Already removed
        finally:
            if job_id in self._job_gid_map:
                del self._job_gid_map[job_id]
            if gid in self._gid_job_map:
                del self._gid_job_map[gid]

    def get_job_status(self, job_id: JobId) -> Job:
        """Query aria2 tellStatus and map response to backend-neutral Job entity."""
        gid = self._get_gid(job_id)
        try:
            dl = self._client.tell_status(make_gid(gid))
            artifacts: list[Artifact] = []

            for idx, f in enumerate(dl.files):
                art = Artifact(
                    id=make_artifact_id(f"art-{gid}-{idx}"),
                    job_id=job_id,
                    kind=ArtifactKind.FILE,
                    name=Path(f.path).name if f.path else dl.name,
                    path=f.path,
                    size=f.length,
                    status=ArtifactStatus.VERIFIED
                    if dl.is_completed
                    else ArtifactStatus.PENDING,
                )
                artifacts.append(art)

            progress = JobProgress(
                total_length=dl.total_length,
                completed_length=dl.completed_length,
                download_speed=dl.download_speed,
                upload_speed=dl.upload_speed,
                eta=dl.eta,
            )

            return Job(
                id=job_id,
                backend_id=self.identity.id,
                name=dl.name,
                state=dl.state,
                progress=progress,
                outputs=artifacts,
                category_id=dl.category_id,
                error_message=dl.error_message,
                backend_data={"aria2_gid": gid},
            )
        except Aria2DownloadNotFoundError as err:
            raise BackendJobNotFoundError(job_id, backend_id=self.identity.id) from err
        except Aria2ConnectionError as err:
            raise BackendConnectionError(
                f"Connection error querying job {job_id}: {err}",
                backend_id=self.identity.id,
            ) from err
        except Aria2RpcError as err:
            raise BackendExecutionError(
                f"RPC error querying job {job_id}: {err}", backend_id=self.identity.id
            ) from err

    def get_diagnostics(self) -> BackendDiagnostics:
        """Fetch aria2 global statistics and version diagnostics."""
        try:
            stat = self._client.get_global_stat()
            ver = self._client.get_version()
            if hasattr(ver, "version"):
                ver_str = str(ver.version)
            elif isinstance(ver, (tuple, list)) and len(ver) > 0:
                ver_str = str(ver[0])
            else:
                ver_str = str(ver) if ver else "unknown"
            return BackendDiagnostics(
                healthy=True,
                active_jobs=stat.num_active,
                details={
                    "version": ver_str,
                    "num_active": str(stat.num_active),
                    "num_waiting": str(stat.num_waiting),
                    "num_stopped": str(stat.num_stopped),
                    "download_speed": stat.download_speed.human_readable(),
                    "upload_speed": stat.upload_speed.human_readable(),
                },
            )
        except Exception as err:
            return BackendDiagnostics(
                healthy=False,
                details={"error": str(err)},
            )

    def get_supported_options(self) -> list[BackendOptionSpec]:
        """Return the authoritative 198-option specification catalogue."""
        return load_aria2_options()

    def _get_gid(self, job_id: JobId) -> str:
        if job_id in self._job_gid_map:
            return self._job_gid_map[job_id]
        raise BackendJobNotFoundError(job_id, backend_id=self.identity.id)
