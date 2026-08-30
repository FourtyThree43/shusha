"""Unit and security validation tests for Browser Native Messaging Bridge (RULE-013)."""

from __future__ import annotations

import io
import json
import struct

import pytest

from shusha.acquisition.browser.bridge import (
    BrowserBridge,
    BrowserBridgeConfig,
    BrowserMessage,
    BrowserResponse,
    read_native_message,
    write_native_message,
)
from shusha.acquisition.detector import AcquisitionDetector
from shusha.acquisition.inbox import AcquisitionInbox
from shusha.domain.acquisition import SourceKind
from shusha.domain.identifiers import make_acquisition_id


class TestBrowserBridge:
    """Test suite for BrowserBridge security validation and request processing."""

    def setup_method(self) -> None:
        self.detector = AcquisitionDetector()
        self.inbox = AcquisitionInbox()
        self.config = BrowserBridgeConfig(
            allowed_origins=frozenset({"chrome-extension://official-extension-id"}),
            allowed_extension_ids=frozenset({"official-extension-id"}),
            auth_token="secret-12345",
            require_auth=False,
            allow_any_extension=True,
        )
        self.bridge = BrowserBridge(
            config=self.config,
            detector=self.detector,
            inbox=self.inbox,
        )

    def test_handle_ping(self) -> None:
        msg = BrowserMessage(request_type="ping")
        res = self.bridge.handle_message(msg)

        assert res.success is True
        assert res.request_type == "ping"
        assert res.data.get("status") == "online"

    def test_handle_acquire_direct_url(self) -> None:
        msg = BrowserMessage(
            request_type="acquire",
            payload={
                "url": "https://example.com/file.zip",
                "referrer": "https://example.com/downloads",
                "filename": "custom_file.zip",
            },
            origin="chrome-extension://official-extension-id",
        )
        res = self.bridge.handle_message(msg)

        assert res.success is True
        assert res.request_type == "acquire"
        assert res.acquisition_id is not None
        assert res.data.get("detected_kind") == "direct_url"

        # Check item in inbox
        item = self.inbox.get(make_acquisition_id(res.acquisition_id))
        assert item is not None
        assert item.source_kind == SourceKind.BROWSER
        assert item.metadata.get("custom_filename") == "custom_file.zip"
        assert item.provenance.origin_url == "chrome-extension://official-extension-id"
        assert item.provenance.referrer == "https://example.com/downloads"

    def test_handle_acquire_batch(self) -> None:
        msg = BrowserMessage(
            request_type="acquire_batch",
            payload={
                "urls": [
                    "https://example.com/file1.zip",
                    "https://example.com/file2.zip",
                    "https://example.com/file3.zip",
                ]
            },
        )
        res = self.bridge.handle_message(msg)

        assert res.success is True
        assert res.request_type == "acquire_batch"
        assert res.data.get("count") == 3
        assert len(res.data.get("acquisition_ids", [])) == 3
        assert len(self.inbox) == 3

    def test_handle_get_status(self) -> None:
        # First acquire an item
        acq_msg = BrowserMessage(
            request_type="acquire",
            payload={"url": "https://example.com/test.iso"},
        )
        acq_res = self.bridge.handle_message(acq_msg)
        acq_id = acq_res.acquisition_id

        # Query status
        query_msg = BrowserMessage(
            request_type="get_status",
            payload={"acquisition_id": acq_id},
        )
        query_res = self.bridge.handle_message(query_msg)

        assert query_res.success is True
        assert query_res.data.get("status") == "detected"

    def test_reject_unauthorized_origin(self) -> None:
        strict_config = BrowserBridgeConfig(
            allowed_origins=frozenset({"chrome-extension://official-extension-id"}),
            allowed_extension_ids=frozenset({"official-extension-id"}),
            allow_any_extension=False,
        )
        strict_bridge = BrowserBridge(
            config=strict_config,
            detector=self.detector,
            inbox=self.inbox,
        )

        msg = BrowserMessage(
            request_type="acquire",
            payload={"url": "https://example.com/file.zip"},
            origin="chrome-extension://unauthorized-extension-id",
        )
        res = strict_bridge.handle_message(msg)

        assert res.success is False
        assert "not authorized" in str(res.error)

    def test_require_auth_token(self) -> None:
        auth_config = BrowserBridgeConfig(
            auth_token="secure-token-xyz",
            require_auth=True,
            allow_any_extension=True,
        )
        auth_bridge = BrowserBridge(
            config=auth_config,
            detector=self.detector,
            inbox=self.inbox,
        )

        # Invalid token
        msg_bad = BrowserMessage(
            request_type="ping",
            auth_token="wrong-token",
        )
        res_bad = auth_bridge.handle_message(msg_bad)
        assert res_bad.success is False
        assert "authentication token" in str(res_bad.error)

        # Valid token
        msg_good = BrowserMessage(
            request_type="ping",
            auth_token="secure-token-xyz",
        )
        res_good = auth_bridge.handle_message(msg_good)
        assert res_good.success is True

    def test_reject_forbidden_url_schemes(self) -> None:
        forbidden_urls = [
            "javascript:alert(1)",
            "file:///etc/passwd",
            "data:text/html,<html></html>",
            "blob:https://example.com/uuid",
        ]

        for bad_url in forbidden_urls:
            msg = BrowserMessage(
                request_type="acquire",
                payload={"url": bad_url},
            )
            res = self.bridge.handle_message(msg)
            assert res.success is False
            assert "Disallowed URL scheme" in str(res.error)

    def test_reject_control_characters_in_url(self) -> None:
        msg = BrowserMessage(
            request_type="acquire",
            payload={"url": "https://example.com/file\r\nInject-Header: evil"},
        )
        res = self.bridge.handle_message(msg)
        assert res.success is False
        assert "control characters" in str(res.error)

    def test_sanitize_filename_traversal(self) -> None:
        clean1 = self.bridge.sanitize_filename("../../evil.sh")
        assert clean1 is not None
        assert clean1 == "_.._evil.sh" or (
            ".." not in (clean1 or "") and "/" not in (clean1 or "")
        )

        clean2 = self.bridge.sanitize_filename("/etc/shadow")
        assert clean2 is not None
        assert "/" not in (clean2 or "")


class TestNativeMessagingFraming:
    """Test suite for reading/writing 4-byte length prefixed Native Messaging streams."""

    def test_read_native_message(self) -> None:
        payload = {"request_type": "ping", "origin": "chrome-extension://test"}
        json_bytes = json.dumps(payload).encode("utf-8")
        length_prefix = struct.pack("@I", len(json_bytes))

        stream = io.BytesIO(length_prefix + json_bytes)
        parsed = read_native_message(stream)

        assert parsed["request_type"] == "ping"
        assert parsed["origin"] == "chrome-extension://test"

    def test_write_native_message(self) -> None:
        stream = io.BytesIO()
        resp = BrowserResponse(
            success=True,
            request_type="ping",
            data={"version": "2.0.0"},
        )

        write_native_message(resp, stream=stream)
        stream.seek(0)

        length_prefix = stream.read(4)
        msg_len = struct.unpack("@I", length_prefix)[0]
        json_data = stream.read(msg_len)
        parsed = json.loads(json_data.decode("utf-8"))

        assert parsed["success"] is True
        assert parsed["request_type"] == "ping"
        assert parsed["data"]["version"] == "2.0.0"

    def test_read_empty_stream_raises_eof(self) -> None:
        stream = io.BytesIO(b"")
        with pytest.raises(EOFError):
            read_native_message(stream)
