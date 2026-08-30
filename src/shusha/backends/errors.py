"""Typed exceptions and error models for Shusha backends (E05-I03)."""

from __future__ import annotations

from shusha.domain.errors import DomainError
from shusha.domain.identifiers import BackendId, JobId


class BackendError(DomainError):
    """Base exception for all backend-related operational failures."""

    def __init__(self, message: str, backend_id: BackendId | None = None) -> None:
        super().__init__(message)
        self.backend_id = backend_id


class BackendConnectionError(BackendError):
    """Raised when communication with the backend daemon/process fails."""


class BackendAuthenticationError(BackendError):
    """Raised when authentication credentials or RPC tokens are rejected."""


class BackendCapabilityUnsupportedError(BackendError):
    """Raised when an operation requires capabilities not supported by the backend."""

    def __init__(
        self,
        message: str,
        backend_id: BackendId | None = None,
        capability: str | None = None,
    ) -> None:
        super().__init__(message, backend_id=backend_id)
        self.capability = capability


class BackendJobNotFoundError(BackendError):
    """Raised when a specified Job ID is not recognized by the backend."""

    def __init__(
        self,
        job_id: JobId,
        backend_id: BackendId | None = None,
    ) -> None:
        super().__init__(
            f"Job {job_id} not found in backend {backend_id or 'unknown'}",
            backend_id=backend_id,
        )
        self.job_id = job_id


class BackendExecutionError(BackendError):
    """Raised when the backend reports an engine/download execution failure."""


class BackendOptionValidationError(BackendError):
    """Raised when option parameters fail schema validation or constraints."""

    def __init__(
        self,
        option_name: str,
        value: str,
        reason: str,
        backend_id: BackendId | None = None,
    ) -> None:
        super().__init__(
            f"Invalid option '{option_name}' with value '{value}': {reason}",
            backend_id=backend_id,
        )
        self.option_name = option_name
        self.value = value
        self.reason = reason


class BackendTimeoutError(BackendError):
    """Raised when a backend operation times out."""
