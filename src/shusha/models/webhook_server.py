"""Local HTTP Webhook Server for Browser Extensions and External IPC.

Runs a lightweight daemon HTTP server (default on port 6810) allowing browser extensions
(Chrome, Firefox, Edge), userscripts, and command-line tools to send downloads directly
into Shusha with custom HTTP headers, cookies, referer, and destination paths.
"""

from __future__ import annotations

import json
import threading
from collections.abc import Callable
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any

from shusha.models.logger import LoggerService

logger = LoggerService(__name__)


class WebhookRequestHandler(BaseHTTPRequestHandler):
    """Handles incoming HTTP POST /add and GET /health requests."""

    _download_callback: Callable[[dict[str, Any]], Any] | None = None

    def log_message(self, format: str, *args: Any) -> None:
        """Suppress default stdout logging."""

    def _send_json_response(self, status_code: int, payload: dict[str, Any]) -> None:
        """Send a JSON formatted response with CORS headers."""
        data = json.dumps(payload).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()
        self.wfile.write(data)

    def do_OPTIONS(self) -> None:
        """Handle CORS pre-flight requests."""
        self._send_json_response(200, {"status": "ok"})

    def do_GET(self) -> None:
        """Handle health check and status endpoints."""
        if self.path in ("/health", "/status", "/"):
            self._send_json_response(
                200,
                {
                    "app": "Shusha-DM",
                    "status": "online",
                    "version": "0.1.0",
                },
            )
        else:
            self._send_json_response(404, {"error": "Not Found"})

    def do_POST(self) -> None:
        """Handle incoming download submission."""
        if self.path not in ("/add", "/api/download", "/jsonrpc"):
            self._send_json_response(404, {"error": "Endpoint not found"})
            return

        try:
            content_len = int(self.headers.get("Content-Length", 0))
            if content_len == 0 or content_len > 1024 * 1024:
                self._send_json_response(400, {"error": "Invalid Content-Length"})
                return

            raw_body = self.rfile.read(content_len)
            payload = json.loads(raw_body.decode("utf-8"))

            if not isinstance(payload, dict):
                self._send_json_response(400, {"error": "Expected JSON object"})
                return

            url = payload.get("url") or payload.get("uri")
            if not url:
                self._send_json_response(
                    400, {"error": "Missing 'url' or 'uri' parameter"}
                )
                return

            if WebhookRequestHandler._download_callback:
                WebhookRequestHandler._download_callback(payload)

            self._send_json_response(
                200, {"status": "success", "message": "Download queued"}
            )

        except json.JSONDecodeError:
            self._send_json_response(400, {"error": "Invalid JSON body"})
        except Exception as e:
            logger.log(f"Webhook request processing error: {e}", level="error")
            self._send_json_response(500, {"error": str(e)})


class WebhookServer:
    """Daemon HTTP Webhook Server instance."""

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 6810,
        on_download_received: Callable[[dict[str, Any]], Any] | None = None,
    ) -> None:
        self.host = host
        self.port = port
        self.on_download_received = on_download_received
        self._server: HTTPServer | None = None
        self._thread: threading.Thread | None = None
        self._running = False

    def start(self) -> bool:
        """Start webhook listener thread.

        Returns:
            True if started successfully, False if port is unavailable.
        """
        if self._running:
            return True

        try:
            WebhookRequestHandler._download_callback = self.on_download_received
            self._server = HTTPServer((self.host, self.port), WebhookRequestHandler)
            self._running = True
            self._thread = threading.Thread(
                target=self._server.serve_forever, daemon=True
            )
            self._thread.start()
            logger.log(
                f"Webhook server running at http://{self.host}:{self.port}/",
                level="info",
            )
            return True
        except Exception as e:
            logger.log(
                f"Failed to start webhook server on {self.host}:{self.port}: {e}",
                level="warning",
            )
            self._running = False
            return False

    def stop(self) -> None:
        """Stop webhook server."""
        if not self._running or not self._server:
            return
        self._running = False
        try:
            self._server.shutdown()
            self._server.server_close()
        except Exception as e:
            logger.log(f"Error shutting down webhook server: {e}", level="debug")
        logger.log("Webhook server stopped.", level="info")

    def is_running(self) -> bool:
        """Check if webhook server is actively listening."""
        return self._running
