"""
WebSocket Notification and Real-time Event Client for aria2.
Pure Python standard library implementation with reconnection and event dispatching.
"""

import contextlib
import json
import logging
import socket
import threading
import time
from collections.abc import Callable
from typing import cast
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

type EventCallback = Callable[[str, dict[str, str]], None]


class Aria2WebSocketClient:
    """Threaded WebSocket client for receiving real-time aria2 notifications."""

    def __init__(
        self,
        endpoint: str = "ws://127.0.0.1:6800/jsonrpc",
        secret: str | None = None,
        auto_reconnect: bool = True,
        reconnect_interval: float = 3.0,
    ) -> None:
        self.endpoint = endpoint
        self.secret = secret.strip() if secret else None
        self.auto_reconnect = auto_reconnect
        self.reconnect_interval = reconnect_interval

        self._running = False
        self._connected = False
        self._thread: threading.Thread | None = None
        self._socket: socket.socket | None = None
        self._listeners: dict[str, list[EventCallback]] = {}
        self._lock = threading.Lock()

    @property
    def is_connected(self) -> bool:
        return self._connected

    def on(self, event_name: str, callback: EventCallback) -> None:
        """Register a callback for an aria2 notification event."""
        with self._lock:
            if event_name not in self._listeners:
                self._listeners[event_name] = []
            if callback not in self._listeners[event_name]:
                self._listeners[event_name].append(callback)

    def off(self, event_name: str, callback: EventCallback) -> None:
        """Unregister a callback for an aria2 notification event."""
        with self._lock:
            if (
                event_name in self._listeners
                and callback in self._listeners[event_name]
            ):
                self._listeners[event_name].remove(callback)

    def _dispatch_event(self, event_name: str, params: dict[str, str]) -> None:
        """Invoke all registered callbacks for an event safely."""
        with self._lock:
            callbacks = list(self._listeners.get(event_name, []))
            all_callbacks = list(self._listeners.get("*", []))

        for cb in callbacks + all_callbacks:
            try:
                cb(event_name, params)
            except Exception as e:
                logger.error(
                    f"Error in WebSocket event callback for {event_name}: {e}",
                    exc_info=True,
                )

    def _handle_raw_message(self, message_str: str) -> None:
        """Parse raw WebSocket frame and dispatch events."""
        try:
            data = json.loads(message_str)
        except Exception:
            return

        if isinstance(data, dict):
            method = data.get("method")
            if isinstance(method, str) and method.startswith("aria2.on"):
                params_list = data.get("params", [])
                event_params: dict[str, str] = {}
                if (
                    isinstance(params_list, list)
                    and params_list
                    and isinstance(params_list[0], dict)
                ):
                    event_params = cast(dict[str, str], params_list[0])
                self._dispatch_event(method, event_params)

    def _connect_and_listen(self) -> None:
        """Connection loop handling handshake, streaming, and reconnections."""
        parsed = urlparse(self.endpoint)
        host = parsed.hostname or "127.0.0.1"
        port = parsed.port or 6800
        path = parsed.path or "/jsonrpc"

        while self._running:
            sock: socket.socket | None = None
            try:
                sock = socket.create_connection((host, port), timeout=5.0)
                # WebSocket client handshake (RFC 6455 simplified for local IPC)
                key = "dGhlIHNhbXBsZSBub25jZQ=="
                handshake = (
                    f"GET {path} HTTP/1.1\r\n"
                    f"Host: {host}:{port}\r\n"
                    "Upgrade: websocket\r\n"
                    "Connection: Upgrade\r\n"
                    f"Sec-WebSocket-Key: {key}\r\n"
                    "Sec-WebSocket-Version: 13\r\n"
                    "\r\n"
                )
                sock.sendall(handshake.encode("utf-8"))

                # Read handshake response
                response_data = b""
                sock.settimeout(5.0)
                while b"\r\n\r\n" not in response_data:
                    chunk = sock.recv(1024)
                    if not chunk:
                        raise ConnectionError(
                            "Connection closed during WebSocket handshake"
                        )
                    response_data += chunk

                if b"101 Switching Protocols" not in response_data:
                    raise ConnectionError("WebSocket handshake rejected by server")

                self._socket = sock
                self._connected = True
                sock.settimeout(2.0)

                buffer = bytearray()
                while self._running:
                    try:
                        chunk = sock.recv(4096)
                        if not chunk:
                            break
                        buffer.extend(chunk)

                        # Process frames in buffer
                        while len(buffer) >= 2:
                            b1 = buffer[0]
                            b2 = buffer[1]
                            payload_len = b2 & 0x7F
                            offset = 2

                            if payload_len == 126:
                                if len(buffer) < 4:
                                    break
                                payload_len = int.from_bytes(buffer[2:4], "big")
                                offset = 4
                            elif payload_len == 127:
                                if len(buffer) < 10:
                                    break
                                payload_len = int.from_bytes(buffer[2:10], "big")
                                offset = 10

                            is_masked = bool(b2 & 0x80)
                            if is_masked:
                                if len(buffer) < offset + 4:
                                    break
                                mask = buffer[offset : offset + 4]
                                offset += 4

                            if len(buffer) < offset + payload_len:
                                break

                            payload = buffer[offset : offset + payload_len]
                            del buffer[: offset + payload_len]

                            if is_masked:
                                payload = bytearray(
                                    b ^ mask[i % 4] for i, b in enumerate(payload)
                                )

                            opcode = b1 & 0x0F
                            if opcode == 0x1:  # Text frame
                                text = payload.decode("utf-8", errors="ignore")
                                self._handle_raw_message(text)
                            elif opcode == 0x8:  # Close frame
                                break
                            elif opcode == 0x9:  # Ping frame
                                # Send pong
                                pong = bytearray([0x8A, 0x00])
                                sock.sendall(pong)

                    except TimeoutError:
                        continue
                    except OSError:
                        break

            except Exception:
                pass
            finally:
                self._connected = False
                if sock:
                    with contextlib.suppress(Exception):
                        sock.close()
                self._socket = None

            if self._running and self.auto_reconnect:
                time.sleep(self.reconnect_interval)

    def start(self) -> None:
        """Start the background notification listener thread."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(
            target=self._connect_and_listen, daemon=True, name="Aria2WebSocketListener"
        )
        self._thread.start()

    def stop(self) -> None:
        """Stop the background listener thread."""
        self._running = False
        self._connected = False
        if self._socket:
            with contextlib.suppress(Exception):
                self._socket.close()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)
        self._thread = None
