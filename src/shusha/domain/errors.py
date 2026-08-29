"""
Domain exceptions and error models for Shusha 2.
"""

from dataclasses import dataclass


class DomainError(Exception):
    """Base exception for all domain-level errors."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class InvalidStateTransitionError(DomainError):
    """Raised when an invalid download state transition is requested."""

    def __init__(self, current_state: str, target_state: str) -> None:
        super().__init__(
            f"Cannot transition download from state '{current_state}' to '{target_state}'."
        )
        self.current_state = current_state
        self.target_state = target_state


class InvalidIdentifierError(DomainError):
    """Raised when an identifier fails syntax or semantic validation."""


class DownloadNotFoundError(DomainError):
    """Raised when a download entity is requested but cannot be found."""

    def __init__(self, download_id: str) -> None:
        super().__init__(f"Download '{download_id}' not found.")
        self.download_id = download_id


class CategoryRuleConflictError(DomainError):
    """Raised when a category rule conflicts with an existing category."""


class ValueObjectValidationError(DomainError):
    """Raised when a value object fails parsing or range constraints."""


@dataclass(frozen=True, slots=True)
class ErrorDetail:
    code: int
    symbol: str
    message: str
    recoverable: bool
