"""Backend SDK for Shusha download backends."""

from shusha.backends.aria2 import ARIA2_CAPABILITIES, Aria2Backend, Aria2Supervisor
from shusha.backends.contract import (
    BackendDiagnostics,
    BackendIdentity,
    BackendProtocol,
)
from shusha.backends.errors import (
    BackendAuthenticationError,
    BackendCapabilityUnsupportedError,
    BackendConnectionError,
    BackendError,
    BackendExecutionError,
    BackendJobNotFoundError,
    BackendOptionValidationError,
    BackendTimeoutError,
)
from shusha.backends.fake import FakeBackend
from shusha.backends.options import (
    BackendOptionSpec,
    OptionMutability,
    OptionScope,
    OptionType,
)
from shusha.backends.registry import BackendRegistry
from shusha.backends.ytdlp import (
    YTDLP_CAPABILITIES,
    MediaFormat,
    MediaInspector,
    MediaMetadata,
    YtDlpAdapter,
    YtDlpBackend,
)

__all__ = [
    "ARIA2_CAPABILITIES",
    "YTDLP_CAPABILITIES",
    "Aria2Backend",
    "Aria2Supervisor",
    "BackendAuthenticationError",
    "BackendCapabilityUnsupportedError",
    "BackendConnectionError",
    "BackendDiagnostics",
    "BackendError",
    "BackendExecutionError",
    "BackendIdentity",
    "BackendJobNotFoundError",
    "BackendOptionSpec",
    "BackendOptionValidationError",
    "BackendProtocol",
    "BackendRegistry",
    "BackendTimeoutError",
    "FakeBackend",
    "MediaFormat",
    "MediaInspector",
    "MediaMetadata",
    "OptionMutability",
    "OptionScope",
    "OptionType",
    "YtDlpAdapter",
    "YtDlpBackend",
]
