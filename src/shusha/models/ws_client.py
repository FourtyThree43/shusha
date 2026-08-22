"""JSON-RPC and WebSocket client for aria2.

This module implements a pure Python lightweight WebSocket and JSON-RPC 2.0 client
designed for bidirectional communication with the aria2 daemon. It supports:
- Real-time asynchronous push notifications (e.g. `aria2.onDownloadStart`, `aria2.onDownloadComplete`).
- High-efficiency `system.multicall` batch queries.
- Resilient fallback between WebSocket and HTTP JSON-RPC transports.
"""

from __future__ import annotations

import base64
import json
import os
import socket
import struct
import threading
import urllib.error
import urllib.request
from collections.abc import Callable
from typing import Any

from shusha.models.logger import LoggerService

logger = LoggerService(__name__)

EventCallback = Callable[[str, dict[str, Any]], None]


class JsonRpcException(Exception):
    """Exception raised for JSON-RPC protocol or aria2 error responses."""

    def __init__(self, code: int, message: str, data: Any = None) -> None:
        super().__init__(f"JSON-RPC Error [{code}]: {message}")
        self.code = code
        self.message = message
        self.data = data


class Aria2WsClient:
    """Lightweight pure-Python WebSocket client for aria2 JSON-RPC events and RPC calls."""

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6800,
        secret: str | None = None,
        timeout: float = 5.0,
    ) -> None:
        """Initialize the WebSocket client.

        Args:
            host: Hostname of the aria2 daemon.
            port: Port number for the aria2 RPC interface.
            secret: Optional RPC secret token.
            timeout: Socket connection and read timeout in seconds.
        """
        self.host = host
        self.port = port
        self.secret = secret
        self.timeout = timeout

        self._sock: socket.socket | None = None
        self._connected = False
        self._running = False
        self._listener_thread: threading.Thread | None = None
        self._lock = threading.Lock()
        self._req_id = 0

        # Pending RPC request waiting queues: req_id -> (Event, response_holder)
        self._pending_requests: dict[str, tuple[threading.Event, list[Any]]] = {}

        # Registered event listeners: event_name -> list of callbacks
        self._event_listeners: dict[str, list[EventCallback]] = {}

    @property
    def is_connected(self) -> bool:
        """Return whether the WebSocket is actively connected."""
        return self._connected

    def on(self, event_name: str, callback: EventCallback) -> None:
        """Register a callback for an aria2 notification event.

        Args:
            event_name: Notification name (e.g. 'aria2.onDownloadComplete').
            callback: Callable taking (event_name, event_params_dict).
        """
        with self._lock:
            self._event_listeners.setdefault(event_name, []).append(callback)

    def off(self, event_name: str, callback: EventCallback | None = None) -> None:
        """Unregister an event listener.

        Args:
            event_name: Notification name.
            callback: Specific callback to remove, or None to remove all for event.
        """
        with self._lock:
            if event_name in self._event_listeners:
                if callback is None:
                    del self._event_listeners[event_name]
                else:
                    self._event_listeners[event_name] = [
                        cb for cb in self._event_listeners[event_name] if cb != callback
                    ]

    def _dispatch_event(self, event_name: str, params: dict[str, Any]) -> None:
        """Dispatch received event to all registered listeners."""
        with self._lock:
            callbacks = list(self._event_listeners.get(event_name, []))
            all_callbacks = list(self._event_listeners.get("*", []))

        for cb in callbacks + all_callbacks:
            try:
                cb(event_name, params)
            except Exception as e:
                logger.log(f"Error in event listener for {event_name}: {e}", level="error")

    def connect(self) -> bool:
        """Establish WebSocket connection with aria2 daemon.

        Returns:
            True if connection succeeded, False otherwise.
        """
        if self._connected:
            return True

        try:
            sock = socket.create_connection((self.host, self.port), timeout=self.timeout)
            # Perform WebSocket handshake
            key = base64.b64encode(os.urandom(16)).decode("ascii")
            handshake = (
                f"GET /jsonrpc HTTP/1.1\r\n"
                f"Host: {self.host}:{self.port}\r\n"
                f"Upgrade: websocket\r\n"
                f"Connection: Upgrade\r\n"
                f"Sec-WebSocket-Key: {key}\r\n"
                f"Sec-WebSocket-Version: 13\r\n"
                f"\r\n"
            )
            sock.sendall(handshake.encode("ascii"))
            response = b""
            while b"\r\n\r\n" not in response:
                chunk = sock.recv(1024)
                if not chunk:
                    break
                response += chunk

            if b" 101 " not in response:
                sock.close()
                logger.log(f"WebSocket handshake failed on {self.host}:{self.port}", level="debug")
                return False

            self._sock = sock
            self._connected = True
            self._running = True

            self._listener_thread = threading.Thread(
                target=self._listen_loop, daemon=True, name="Aria2WsListener"
            )
            self._listener_thread.start()
            logger.log(f"WebSocket connected to ws://{self.host}:{self.port}/jsonrpc", level="info")
            return True

        except Exception as e:
            logger.log(f"Could not connect WebSocket: {e}", level="debug")
            self._connected = False
            return False

    def close(self) -> None:
        """Close the WebSocket connection cleanly."""
        self._running = False
        self._connected = False
        if self._sock:
            try:
                # Send close frame
                self._send_frame(b"", opcode=0x8)
                self._sock.close()
            except Exception:
                pass
            self._sock = None

    def _send_frame(self, data: bytes, opcode: int = 0x1) -> None:
        """Send a client WebSocket frame with 4-byte masking."""
        if not self._sock:
            raise ConnectionError("WebSocket is not connected")

        length = len(data)
        mask = os.urandom(4)

        if length <= 125:
            header = bytearray([0x80 | opcode, 0x80 | length])
        elif length <= 65535:
            header = bytearray([0x80 | opcode, 0x80 | 126]) + struct.pack("!H", length)
        else:
            header = bytearray([0x80 | opcode, 0x80 | 127]) + struct.pack("!Q", length)

        header.extend(mask)

        # Apply mask
        masked_data = bytearray(length)
        for i in range(length):
            masked_data[i] = data[i] ^ mask[i % 4]

        with self._lock:
            self._sock.sendall(header + masked_data)

    def _recv_exact(self, num_bytes: int) -> bytes:
        """Read exact number of bytes from socket."""
        if not self._sock:
            raise ConnectionError("Socket closed")
        buf = bytearray()
        while len(buf) < num_bytes:
            chunk = self._sock.recv(num_bytes - len(buf))
            if not chunk:
                raise ConnectionError("Socket closed by remote peer")
            buf.extend(chunk)
        return bytes(buf)

    def _recv_frame(self) -> tuple[int, bytes]:
        """Receive a single WebSocket frame from server."""
        header = self._recv_exact(2)
        b1, b2 = header[0], header[1]
        opcode = b1 & 0x0F
        is_masked = bool(b2 & 0x80)
        payload_len = b2 & 0x7F

        if payload_len == 126:
            payload_len = struct.unpack("!H", self._recv_exact(2))[0]
        elif payload_len == 127:
            payload_len = struct.unpack("!Q", self._recv_exact(8))[0]

        mask = self._recv_exact(4) if is_masked else None
        data = self._recv_exact(payload_len)

        if mask:
            unmasked = bytearray(payload_len)
            for i in range(payload_len):
                unmasked[i] = data[i] ^ mask[i % 4]
            data = bytes(unmasked)

        return opcode, data

    def _listen_loop(self) -> None:
        """Background loop reading WebSocket frames and routing messages."""
        while self._running and self._sock:
            try:
                opcode, data = self._recv_frame()
                if opcode == 0x8:  # Close frame
                    break
                elif opcode == 0x9:  # Ping frame -> reply Pong
                    self._send_frame(data, opcode=0xA)
                    continue
                elif opcode == 0xA:  # Pong
                    continue
                elif opcode == 0x1:  # Text JSON payload
                    text = data.decode("utf-8")
                    self._handle_message(text)

            except Exception as e:
                if self._running:
                    logger.log(f"WebSocket read error: {e}", level="debug")
                break

        self._connected = False
        logger.log("WebSocket listener stopped", level="debug")

    def _handle_message(self, text: str) -> None:
        """Process incoming JSON-RPC response or notification."""
        try:
            msg = json.loads(text)
        except json.JSONDecodeError:
            return

        # Notification (method without id)
        if "method" in msg and "id" not in msg:
            method = msg["method"]
            params = msg.get("params", [{}])
            event_data = params[0] if params and isinstance(params, list) else {}
            self._dispatch_event(method, event_data)
            return

        # RPC Response (with id)
        if "id" in msg:
            req_id = str(msg["id"])
            if req_id in self._pending_requests:
                event, holder = self._pending_requests[req_id]
                holder.append(msg)
                event.set()

    def call(self, method: str, *params: Any) -> Any:
        """Execute a JSON-RPC method call over WebSocket (with HTTP fallback).

        Args:
            method: aria2 method name (e.g. 'aria2.tellActive').
            *params: Arguments for the method.

        Returns:
            The 'result' field of the JSON-RPC response.

        Raises:
            JsonRpcException: If the call failed or returned an error.
        """
        # Ensure secret token parameter is attached
        call_params: list[Any] = []
        if self.secret:
            call_params.append(f"token:{self.secret}")
        call_params.extend(params)

        self._req_id += 1
        req_id = f"req_{self._req_id}"
        payload = {
            "jsonrpc": "2.0",
            "id": req_id,
            "method": method,
            "params": call_params,
        }

        # Try WebSocket first if connected
        if self._connected:
            try:
                event = threading.Event()
                holder: list[Any] = []
                self._pending_requests[req_id] = (event, holder)

                data = json.dumps(payload).encode("utf-8")
                self._send_frame(data)

                if event.wait(timeout=self.timeout) and holder:
                    res = holder[0]
                    self._pending_requests.pop(req_id, None)
                    if "error" in res:
                        err = res["error"]
                        raise JsonRpcException(
                            err.get("code", -1),
                            err.get("message", "Unknown error"),
                            err.get("data"),
                        )
                    return res.get("result")

            except Exception as ws_err:
                logger.log(f"WS call fallback to HTTP on {method}: {ws_err}", level="debug")
            finally:
                self._pending_requests.pop(req_id, None)

        # Fallback to HTTP JSON-RPC
        return self._http_call(payload)

    def _http_call(self, payload: dict[str, Any]) -> Any:
        """Perform fallback JSON-RPC call over standard HTTP POST."""
        url = f"http://{self.host}:{self.port}/jsonrpc"
        req_bytes = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=req_bytes,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                if "error" in data:
                    err = data["error"]
                    raise JsonRpcException(
                        err.get("code", -1),
                        err.get("message", "Unknown error"),
                        err.get("data"),
                    )
                return data.get("result")
        except urllib.error.URLError as e:
            raise ConnectionError(f"HTTP JSON-RPC connection failed to {url}: {e}") from e

    def multicall(self, methods_and_params: list[tuple[str, list[Any]]]) -> list[Any]:
        """Execute multiple JSON-RPC calls in a single network batch via `system.multicall`.

        Args:
            methods_and_params: List of tuples `(method_name, [params])`.

        Returns:
            List of results corresponding to each batched method call.
        """
        calls: list[dict[str, Any]] = []
        for method, params in methods_and_params:
            call_params: list[Any] = []
            if self.secret:
                call_params.append(f"token:{self.secret}")
            call_params.extend(params)
            calls.append({"methodName": method, "params": call_params})

        raw_results = self.call("system.multicall", calls)
        results: list[Any] = []
        if isinstance(raw_results, list):
            for item in raw_results:
                if isinstance(item, list) and len(item) > 0:
                    results.append(item[0])
                else:
                    results.append(item)
        return results
