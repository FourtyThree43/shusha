"""
Typed XML-RPC Compatibility Transport for aria2.
Uses standard library xmlrpc.client with custom HTTP timeout transport.
"""

import http.client
import xmlrpc.client
from typing import Any

from shusha.infrastructure.aria2.errors import (
    Aria2AuthenticationError,
    Aria2ConnectionError,
    Aria2EngineError,
    Aria2ProtocolError,
)


class TimeoutTransport(xmlrpc.client.Transport):
    """Custom XML-RPC Transport with explicit socket timeout."""

    def __init__(self, timeout: float = 10.0) -> None:
        super().__init__()
        self.timeout = timeout

    def make_connection(self, host: Any) -> http.client.HTTPConnection:
        # Tuple format (host, port) or string
        conn = http.client.HTTPConnection(host, timeout=self.timeout)
        return conn


class XmlRpcTransport:
    """Synchronous XML-RPC compatibility transport client."""

    def __init__(
        self,
        endpoint: str = "http://127.0.0.1:6800/rpc",
        secret: str | None = None,
        timeout: float = 10.0,
    ) -> None:
        self.endpoint = endpoint
        self.secret = secret.strip() if secret else None
        self.timeout = timeout
        transport = TimeoutTransport(timeout=timeout)
        self._proxy = xmlrpc.client.ServerProxy(
            self.endpoint,
            transport=transport,
            allow_none=True,
            encoding="utf-8",
        )

    def _prepare_params(self, params: list[object] | None) -> list[object]:
        res: list[object] = []
        if self.secret:
            res.append(f"token:{self.secret}")
        if params:
            res.extend(params)
        return res

    def call(self, method: str, params: list[object] | None = None) -> object:
        """Execute an XML-RPC method on aria2."""
        prepared_params = self._prepare_params(params)
        try:
            rpc_func = getattr(self._proxy, method)
            return rpc_func(*prepared_params)
        except xmlrpc.client.Fault as e:
            if "Unauthorized" in e.faultString:
                raise Aria2AuthenticationError(
                    f"Authentication failed: {e.faultString}", code=e.faultCode
                ) from e
            raise Aria2EngineError(code=e.faultCode, message=e.faultString) from e
        except (xmlrpc.client.ProtocolError, OSError, TimeoutError) as e:
            raise Aria2ConnectionError(
                f"XML-RPC connection failed to {self.endpoint}: {e}"
            ) from e
        except Exception as e:
            raise Aria2ProtocolError(f"Unexpected XML-RPC error: {e}") from e
