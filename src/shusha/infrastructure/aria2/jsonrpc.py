"""
Typed JSON-RPC 2.0 Transport Client for aria2.
Uses standard library urllib.request with robust error mapping.
"""

import json
import urllib.error
import urllib.request
import uuid
from typing import cast

from shusha.infrastructure.aria2.errors import (
    Aria2AuthenticationError,
    Aria2ConnectionError,
    Aria2EngineError,
    Aria2ProtocolError,
    Aria2RpcError,
)


class JsonRpcTransport:
    """Synchronous JSON-RPC 2.0 transport client."""

    def __init__(
        self,
        endpoint: str = "http://127.0.0.1:6800/jsonrpc",
        secret: str | None = None,
        timeout: float = 10.0,
    ) -> None:
        self.endpoint = endpoint.rstrip("/")
        self.secret = secret.strip() if secret else None
        self.timeout = timeout

    def _prepare_params(self, params: list[object] | None) -> list[object]:
        """Prepend RPC secret token if configured."""
        res: list[object] = []
        if self.secret:
            res.append(f"token:{self.secret}")
        if params:
            res.extend(params)
        return res

    def call(self, method: str, params: list[object] | None = None) -> object:
        """Execute a single JSON-RPC 2.0 method invocation."""
        req_id = str(uuid.uuid4())
        prepared_params = self._prepare_params(params)

        payload = {
            "jsonrpc": "2.0",
            "id": req_id,
            "method": method,
            "params": prepared_params,
        }

        data_bytes = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            self.endpoint,
            data=data_bytes,
            headers={
                "Content-Type": "application/json",
                "User-Agent": "Shusha/2.0",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                resp_bytes = resp.read()
        except urllib.error.HTTPError as e:
            if e.code in (401, 403):
                raise Aria2AuthenticationError(
                    "Authentication failed: invalid RPC secret", code=e.code
                ) from e
            raise Aria2ConnectionError(
                f"HTTP error from aria2 daemon: {e.code} {e.reason}", code=e.code
            ) from e
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            raise Aria2ConnectionError(
                f"Failed to connect to aria2 daemon at {self.endpoint}: {e}"
            ) from e

        try:
            resp_json = json.loads(resp_bytes.decode("utf-8"))
        except Exception as e:
            raise Aria2ProtocolError(f"Malformed JSON response from aria2: {e}") from e

        if not isinstance(resp_json, dict):
            raise Aria2ProtocolError("Expected JSON-RPC response object")

        if resp_json.get("error"):
            err_dict = cast(dict[str, object], resp_json["error"])
            code = int(str(err_dict.get("code", 1)))
            message = str(err_dict.get("message", "Unknown error"))
            if code == 1 and "Unauthorized" in message:
                raise Aria2AuthenticationError(
                    f"Authentication failed: {message}", code=code
                )
            raise Aria2EngineError(code=code, message=message)

        if "result" not in resp_json:
            raise Aria2ProtocolError("JSON-RPC response missing 'result' field")

        return resp_json["result"]

    def multicall(self, calls: list[tuple[str, list[object]]]) -> list[object]:
        """Execute multiple JSON-RPC calls in a single batch request."""
        if not calls:
            return []

        multicall_params: list[dict[str, object]] = []
        for method, params in calls:
            multicall_params.append(
                {
                    "methodName": method,
                    "params": self._prepare_params(params),
                }
            )

        req_id = str(uuid.uuid4())
        payload = {
            "jsonrpc": "2.0",
            "id": req_id,
            "method": "system.multicall",
            "params": [multicall_params],
        }

        data_bytes = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            self.endpoint,
            data=data_bytes,
            headers={
                "Content-Type": "application/json",
                "User-Agent": "Shusha/2.0",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                resp_bytes = resp.read()
        except Exception as e:
            raise Aria2ConnectionError(f"Multicall failed: {e}") from e

        resp_json = json.loads(resp_bytes.decode("utf-8"))
        results_raw = resp_json.get("result", [])

        # system.multicall returns a list of single-element lists: [[res1], [res2], ...]
        results: list[object] = []
        for r in results_raw:
            if isinstance(r, list) and len(r) == 1:
                results.append(r[0])
            elif isinstance(r, dict) and "faultString" in r:
                raise Aria2RpcError(str(r.get("faultString")))
            else:
                results.append(r)

        return results
