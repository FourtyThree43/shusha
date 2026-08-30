"""Native Messaging and Acquisition Bridge for WebExtensions (RULE-013).

Provides rigorous origin validation, authentication, URL sanitization,
request type dispatching, and Native Messaging I/O framing for browser extensions.
"""

from __future__ import annotations

import json
import logging
import re
import struct
import sys
import urllib.parse
from dataclasses import dataclass, field
from typing import Any, BinaryIO

from shusha.acquisition.detector import AcquisitionDetector
from shusha.acquisition.inbox import AcquisitionInbox
from shusha.domain.acquisition import Provenance, SourceKind
from shusha.domain.identifiers import make_acquisition_id

logger = logging.getLogger(__name__)

ALLOWED_SCHEMES = frozenset({"http", "https", "ftp", "sftp", "magnet"})
ALLOWED_REQUEST_TYPES = frozenset({"ping", "acquire", "acquire_batch", "get_status"})


@dataclass(frozen=True, slots=True, kw_only=True)
class BrowserBridgeConfig:
    """Configuration for browser extension access control and security validation."""

    allowed_origins: frozenset[str] = field(default_factory=frozenset)
    allowed_extension_ids: frozenset[str] = field(default_factory=frozenset)
    auth_token: str | None = None
    require_auth: bool = False
    allow_any_extension: bool = (
        True  # Defaults to True for development, False in hardened prod
    )


@dataclass(frozen=True, slots=True, kw_only=True)
class BrowserMessage:
    """Strongly typed incoming browser extension request."""

    request_type: str
    payload: dict[str, Any] = field(default_factory=dict)
    origin: str = ""
    auth_token: str | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class BrowserResponse:
    """Strongly typed response sent back to browser extension."""

    success: bool
    request_type: str
    acquisition_id: str | None = None
    data: dict[str, Any] = field(default_factory=dict)
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize response to dictionary for JSON transmission."""
        res: dict[str, Any] = {
            "success": self.success,
            "request_type": self.request_type,
        }
        if self.acquisition_id:
            res["acquisition_id"] = self.acquisition_id
        if self.data:
            res["data"] = self.data
        if self.error:
            res["error"] = self.error
        return res


class BrowserValidationError(Exception):
    """Raised when incoming browser message fails security or structural validation."""


class BrowserBridge:
    """Native messaging bridge validating and processing browser acquisition events."""

    def __init__(
        self,
        config: BrowserBridgeConfig | None = None,
        detector: AcquisitionDetector | None = None,
        inbox: AcquisitionInbox | None = None,
    ) -> None:
        self.config = config if config is not None else BrowserBridgeConfig()
        self.detector = detector if detector is not None else AcquisitionDetector()
        self.inbox = inbox

    def validate_message(self, message: BrowserMessage) -> None:
        """Validate origin, request type, authentication token, and payload shape."""
        # 1. Validate request type
        req_type = message.request_type.strip().lower()
        if req_type not in ALLOWED_REQUEST_TYPES:
            raise BrowserValidationError(
                f"Unsupported or unauthorized request type: '{message.request_type}'"
            )

        # 2. Validate Origin / Extension ID
        if not self.config.allow_any_extension:
            origin = message.origin.strip()
            if not origin:
                raise BrowserValidationError(
                    "Missing browser origin header / identifier."
                )

            origin_valid = False
            if self.config.allowed_origins and origin in self.config.allowed_origins:
                origin_valid = True
            elif self.config.allowed_extension_ids:
                # Extract extension ID from chrome-extension://<id> or moz-extension://<id>
                for ext_id in self.config.allowed_extension_ids:
                    if ext_id in origin:
                        origin_valid = True
                        break

            if not origin_valid:
                raise BrowserValidationError(f"Origin '{origin}' is not authorized.")

        # 3. Validate Authentication Token
        if self.config.require_auth and (
            not self.config.auth_token or message.auth_token != self.config.auth_token
        ):
            raise BrowserValidationError("Invalid or missing authentication token.")

        # 4. Validate Payload structure
        if not isinstance(message.payload, dict):
            raise BrowserValidationError(
                "Message payload must be a JSON dictionary object."
            )

    def sanitize_url(self, raw_url: str) -> str:
        """Validate and sanitize URL from browser extension."""
        clean = raw_url.strip()
        if not clean:
            raise BrowserValidationError("URL cannot be empty.")

        # Check for control characters or line breaks
        if re.search(r"[\r\n\x00-\x1f]", clean):
            raise BrowserValidationError("URL contains forbidden control characters.")

        if clean.lower().startswith("magnet:?"):
            return clean

        parsed = urllib.parse.urlparse(clean)
        scheme = parsed.scheme.lower()
        if scheme not in ALLOWED_SCHEMES:
            raise BrowserValidationError(
                f"Disallowed URL scheme '{scheme}'. Only {sorted(ALLOWED_SCHEMES)} are supported."
            )

        if not parsed.hostname:
            raise BrowserValidationError("URL missing valid hostname.")

        return clean

    def sanitize_filename(self, filename: str | None) -> str | None:
        """Sanitize filename to prevent directory traversal and path injection."""
        if not filename:
            return None
        # Remove directory separators and null bytes
        clean = (
            filename.strip().replace("\x00", "").replace("/", "_").replace("\\", "_")
        )
        # Remove traversal tokens
        clean = re.sub(r"^\.+", "", clean)
        return clean.strip() or None

    def handle_message(
        self, raw_input: dict[str, Any] | BrowserMessage
    ) -> BrowserResponse:
        """Process incoming browser message and return a typed BrowserResponse."""
        if isinstance(raw_input, BrowserMessage):
            msg = raw_input
        elif isinstance(raw_input, dict):
            payload_val = raw_input.get("payload")
            payload_dict: dict[str, Any] = (
                payload_val if isinstance(payload_val, dict) else dict(raw_input)
            )
            msg = BrowserMessage(
                request_type=str(
                    raw_input.get("request_type") or raw_input.get("type") or ""
                ),
                payload=payload_dict,
                origin=str(raw_input.get("origin", "")),
                auth_token=raw_input.get("auth_token") or raw_input.get("token"),
            )
        else:
            return BrowserResponse(
                success=False,
                request_type="unknown",
                error="Invalid message format: expected JSON object.",
            )

        try:
            self.validate_message(msg)
        except BrowserValidationError as err:
            return BrowserResponse(
                success=False,
                request_type=msg.request_type or "unknown",
                error=str(err),
            )

        req_type = msg.request_type.strip().lower()

        # Handle "ping"
        if req_type == "ping":
            return BrowserResponse(
                success=True,
                request_type="ping",
                data={"version": "2.0.0", "status": "online"},
            )

        # Handle "acquire"
        if req_type == "acquire":
            return self._handle_acquire(msg)

        # Handle "acquire_batch"
        if req_type == "acquire_batch":
            return self._handle_acquire_batch(msg)

        # Handle "get_status"
        if req_type == "get_status":
            return self._handle_get_status(msg)

        return BrowserResponse(
            success=False,
            request_type=req_type,
            error=f"Unhandled request type: {req_type}",
        )

    def _handle_acquire(self, msg: BrowserMessage) -> BrowserResponse:
        """Handle single URL download acquisition from browser."""
        url = msg.payload.get("url")
        if not url or not isinstance(url, str):
            return BrowserResponse(
                success=False,
                request_type="acquire",
                error="Payload missing required 'url' field.",
            )

        try:
            sanitized_url = self.sanitize_url(url)
        except BrowserValidationError as err:
            return BrowserResponse(
                success=False,
                request_type="acquire",
                error=str(err),
            )

        referrer = msg.payload.get("referrer")
        user_agent = msg.payload.get("user_agent")
        cookies = msg.payload.get("cookies")
        custom_filename = self.sanitize_filename(msg.payload.get("filename"))

        meta: dict[str, str] = {}
        if cookies:
            meta["cookies"] = str(cookies)
        if custom_filename:
            meta["custom_filename"] = custom_filename

        prov = Provenance(
            origin_url=msg.origin or None,
            referrer=str(referrer) if referrer else None,
            user_agent=str(user_agent) if user_agent else None,
            source_application="BrowserExtension",
        )

        req = self.detector.detect(
            raw_input=sanitized_url,
            source_kind=SourceKind.BROWSER,
            provenance=prov,
            metadata=meta,
        )

        if self.inbox is not None:
            req = self.inbox.add(req)

        return BrowserResponse(
            success=True,
            request_type="acquire",
            acquisition_id=str(req.id),
            data={
                "detected_kind": str(req.detected_kind.value),
                "status": str(req.status.value),
            },
        )

    def _handle_acquire_batch(self, msg: BrowserMessage) -> BrowserResponse:
        """Handle batch acquisition of multiple URLs from browser."""
        urls = msg.payload.get("urls")
        if not urls or not isinstance(urls, list):
            return BrowserResponse(
                success=False,
                request_type="acquire_batch",
                error="Payload missing required 'urls' list.",
            )

        acquisition_ids: list[str] = []
        for raw_url in urls:
            if not isinstance(raw_url, str):
                continue
            try:
                sanitized_url = self.sanitize_url(raw_url)
                req = self.detector.detect(
                    raw_input=sanitized_url,
                    source_kind=SourceKind.BROWSER,
                    provenance=Provenance(
                        origin_url=msg.origin or None,
                        source_application="BrowserExtension",
                    ),
                )
                if self.inbox is not None:
                    req = self.inbox.add(req)
                acquisition_ids.append(str(req.id))
            except BrowserValidationError:
                continue

        return BrowserResponse(
            success=True,
            request_type="acquire_batch",
            data={
                "count": len(acquisition_ids),
                "acquisition_ids": acquisition_ids,
            },
        )

    def _handle_get_status(self, msg: BrowserMessage) -> BrowserResponse:
        """Query status of an acquisition request."""
        acq_id = msg.payload.get("acquisition_id")
        if not acq_id or not isinstance(acq_id, str):
            return BrowserResponse(
                success=False,
                request_type="get_status",
                error="Payload missing 'acquisition_id'.",
            )

        if self.inbox is None:
            return BrowserResponse(
                success=False,
                request_type="get_status",
                error="No AcquisitionInbox attached to bridge.",
            )

        item = self.inbox.get(make_acquisition_id(acq_id))
        if item is None:
            return BrowserResponse(
                success=False,
                request_type="get_status",
                error=f"Acquisition '{acq_id}' not found.",
            )

        return BrowserResponse(
            success=True,
            request_type="get_status",
            acquisition_id=str(item.id),
            data={
                "status": str(item.status.value),
                "detected_kind": str(item.detected_kind.value),
                "preferred_backend": str(item.preferred_backend)
                if item.preferred_backend
                else None,
            },
        )


# --- Native Messaging Byte-level Framing Helpers ---


def read_native_message(stream: BinaryIO = sys.stdin.buffer) -> dict[str, Any]:
    """Read a 4-byte length-prefixed JSON message from the standard input stream."""
    raw_length = stream.read(4)
    if not raw_length or len(raw_length) < 4:
        raise EOFError("Native messaging input stream closed or empty.")

    message_length = struct.unpack("@I", raw_length)[0]
    if message_length == 0 or message_length > 10 * 1024 * 1024:  # 10 MB limit
        raise ValueError(f"Invalid native message length: {message_length} bytes")

    data = stream.read(message_length)
    if len(data) < message_length:
        raise EOFError("Incomplete message data received from native host stream.")

    return json.loads(data.decode("utf-8"))


def write_native_message(
    response: dict[str, Any] | BrowserResponse, stream: BinaryIO = sys.stdout.buffer
) -> None:
    """Write a 4-byte length-prefixed JSON response to the standard output stream."""
    data_dict = (
        response.to_dict() if isinstance(response, BrowserResponse) else response
    )
    encoded = json.dumps(data_dict).encode("utf-8")
    stream.write(struct.pack("@I", len(encoded)))
    stream.write(encoded)
    stream.flush()
