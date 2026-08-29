"""
RPC and transport error definitions for the aria2 infrastructure adapter.
"""


class Aria2RpcError(Exception):
    """Base exception for all aria2 RPC operations."""

    def __init__(self, message: str, code: int | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.code = code


class Aria2ConnectionError(Aria2RpcError):
    """Raised when connection to aria2 daemon fails (refused, timeout, offline)."""


class Aria2AuthenticationError(Aria2RpcError):
    """Raised when RPC authentication with secret token fails."""


class Aria2ProtocolError(Aria2RpcError):
    """Raised when an unparseable or malformed JSON-RPC / XML-RPC payload is received."""


class Aria2OptionValidationError(Aria2RpcError):
    """Raised when an option fails registry validation before RPC transmission."""


class Aria2EngineError(Aria2RpcError):
    """Raised when aria2 returns an engine error code (e.g. 1..32)."""

    def __init__(self, code: int, message: str) -> None:
        super().__init__(f"aria2 engine error [{code}]: {message}", code=code)
