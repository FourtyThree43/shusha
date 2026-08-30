"""Unit and pipeline integration tests for the Acquisition Platform (Epic E09)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from shusha.acquisition.detector import AcquisitionDetector
from shusha.acquisition.fake import (
    SAMPLE_DIRECT_URL,
    SAMPLE_MAGNET_URI,
    SAMPLE_MEDIA_URL,
    SAMPLE_METALINK_XML,
    SAMPLE_PLAYLIST_URL,
    SAMPLE_TORRENT_BENCODE,
    FakeAcquisitionProvider,
    FakeHttpHeaderFetcher,
)
from shusha.acquisition.inbox import AcquisitionInbox
from shusha.acquisition.inspector import AcquisitionInspector
from shusha.acquisition.policy import AcquisitionPolicyEngine, AcquisitionRule
from shusha.acquisition.resolver import AcquisitionResolver
from shusha.backends.fake import FakeBackend
from shusha.backends.registry import BackendRegistry
from shusha.domain.acquisition import (
    AcquisitionStatus,
    DetectedKind,
    SelectionPolicy,
    SourceKind,
)
from shusha.domain.capability import Capability, CapabilitySet
from shusha.domain.identifiers import make_backend_id
from shusha.domain.values import ByteSize


class TestAcquisitionDetector:
    """Test suite for AcquisitionDetector classifying raw inputs."""

    def setup_method(self) -> None:
        self.detector = AcquisitionDetector()

    def test_detect_direct_http_url(self) -> None:
        url = "https://example.com/downloads/archive.tar.gz"
        req = self.detector.detect(url, source_kind=SourceKind.MANUAL)

        assert req.detected_kind == DetectedKind.DIRECT_URL
        assert req.raw_input == url
        assert req.status == AcquisitionStatus.DETECTED
        assert req.metadata.get("scheme") == "https"
        assert req.metadata.get("hostname") == "example.com"

    def test_detect_magnet_uri(self) -> None:
        req = self.detector.detect(SAMPLE_MAGNET_URI, source_kind=SourceKind.CLIPBOARD)

        assert req.detected_kind == DetectedKind.MAGNET_URI
        assert req.source_kind == SourceKind.CLIPBOARD
        assert (
            req.metadata.get("info_hash") == "a88fda5954e89178c372716a6a78b8180ed4dad3"
        )
        assert req.metadata.get("display_name") == "ubuntu-24.04-desktop-amd64.iso"
        assert "torrent.ubuntu.com" in req.metadata.get("trackers", "")

    def test_detect_torrent_file_path(self, tmp_path: Path) -> None:
        torrent_file = tmp_path / "test.torrent"
        torrent_file.write_bytes(SAMPLE_TORRENT_BENCODE)

        req = self.detector.detect(str(torrent_file), source_kind=SourceKind.DRAG_DROP)

        assert req.detected_kind == DetectedKind.TORRENT_FILE
        assert req.source_kind == SourceKind.DRAG_DROP
        assert req.metadata.get("format") == "torrent_file"

    def test_detect_metalink_file_path(self, tmp_path: Path) -> None:
        metalink_file = tmp_path / "test.metalink"
        metalink_file.write_text(SAMPLE_METALINK_XML, encoding="utf-8")

        req = self.detector.detect(
            str(metalink_file), source_kind=SourceKind.LOCAL_FILE
        )

        assert req.detected_kind == DetectedKind.METALINK_FILE
        assert req.metadata.get("format") == "metalink_file"

    def test_detect_metalink_xml_content(self) -> None:
        req = self.detector.detect(SAMPLE_METALINK_XML, source_kind=SourceKind.MANUAL)

        assert req.detected_kind == DetectedKind.METALINK_FILE
        assert req.metadata.get("format") == "metalink_xml"

    def test_detect_media_streaming_urls(self) -> None:
        yt_req = self.detector.detect(SAMPLE_MEDIA_URL)
        assert yt_req.detected_kind == DetectedKind.MEDIA_STREAM

        vimeo_req = self.detector.detect("https://vimeo.com/76979871")
        assert vimeo_req.detected_kind == DetectedKind.MEDIA_STREAM

        twitch_req = self.detector.detect("https://www.twitch.tv/videos/123456789")
        assert twitch_req.detected_kind == DetectedKind.MEDIA_STREAM

        m3u8_req = self.detector.detect("https://stream.example.com/live/index.m3u8")
        assert m3u8_req.detected_kind == DetectedKind.MEDIA_STREAM

    def test_detect_playlist_url(self) -> None:
        req = self.detector.detect(SAMPLE_PLAYLIST_URL)
        assert req.detected_kind == DetectedKind.PLAYLIST_URL
        assert "playlist_id" in req.metadata

    def test_detect_all_from_multiline_text(self) -> None:
        raw_text = f"""
        Check out these links:
        {SAMPLE_DIRECT_URL}
        {SAMPLE_MAGNET_URI}
        {SAMPLE_MEDIA_URL}
        Some other text
        """
        requests = self.detector.detect_all(raw_text, source_kind=SourceKind.CLIPBOARD)

        assert len(requests) == 3
        assert requests[0].detected_kind == DetectedKind.DIRECT_URL
        assert requests[1].detected_kind == DetectedKind.MAGNET_URI
        assert requests[2].detected_kind == DetectedKind.MEDIA_STREAM


class TestAcquisitionInspector:
    """Test suite for AcquisitionInspector non-destructive inspection."""

    def setup_method(self) -> None:
        self.fake_http = FakeHttpHeaderFetcher()
        self.inspector = AcquisitionInspector(http_fetcher=self.fake_http)
        self.detector = AcquisitionDetector()

    def test_inspect_http_direct_url(self) -> None:
        req = self.detector.detect(SAMPLE_DIRECT_URL)
        result = self.inspector.inspect(req)

        assert result.is_valid is True
        assert result.content_type == "application/x-iso9660-image"
        assert result.content_length == ByteSize(6100000000)
        assert result.filename == "ubuntu-24.04-desktop-amd64.iso"
        assert result.is_seekable is True

    def test_inspect_http_redirect(self) -> None:
        req = self.detector.detect("https://short.url/redirect")
        result = self.inspector.inspect(req)

        assert result.is_valid is True
        assert result.redirect_url == SAMPLE_DIRECT_URL

    def test_inspect_magnet_uri(self) -> None:
        req = self.detector.detect(SAMPLE_MAGNET_URI)
        result = self.inspector.inspect(req)

        assert result.is_valid is True
        assert result.info_hash == "a88fda5954e89178c372716a6a78b8180ed4dad3"
        assert result.filename == "ubuntu-24.04-desktop-amd64.iso"
        assert result.torrent_meta is not None
        assert len(result.torrent_meta.trackers) == 1

    def test_inspect_bencoded_torrent(self, tmp_path: Path) -> None:
        torrent_file = tmp_path / "sample.torrent"
        torrent_file.write_bytes(SAMPLE_TORRENT_BENCODE)

        req = self.detector.detect(str(torrent_file))
        result = self.inspector.inspect(req)

        assert result.is_valid is True
        assert result.detected_kind == DetectedKind.TORRENT_FILE
        assert result.filename == "example.iso"
        assert result.content_length == ByteSize(1048576)
        assert result.info_hash is not None
        assert result.torrent_meta is not None
        assert len(result.torrent_meta.trackers) == 1

    def test_inspect_metalink_xml(self) -> None:
        req = self.detector.detect(SAMPLE_METALINK_XML)
        result = self.inspector.inspect(req)

        assert result.is_valid is True
        assert result.detected_kind == DetectedKind.METALINK_FILE
        assert result.filename == "example.tar.gz"
        assert result.content_length == ByteSize(10485760)
        assert len(result.metalink_resources) == 2
        assert result.metalink_resources[0].priority == 10
        assert result.metalink_resources[1].priority == 20

    def test_inspect_media_stream(self) -> None:
        req = self.detector.detect(SAMPLE_MEDIA_URL)
        result = self.inspector.inspect(req)

        assert result.is_valid is True
        assert result.media_metadata.get("video_id") == "dQw4w9WgXcQ"
        assert result.media_metadata.get("is_stream") == "true"


class TestAcquisitionResolver:
    """Test suite for AcquisitionResolver URL resolution and backend discovery."""

    def setup_method(self) -> None:
        self.resolver = AcquisitionResolver()
        self.detector = AcquisitionDetector()
        self.fake_http = FakeHttpHeaderFetcher()
        self.inspector = AcquisitionInspector(http_fetcher=self.fake_http)

    def test_resolve_redirect_url(self) -> None:
        req = self.detector.detect("https://short.url/redirect")
        insp = self.inspector.inspect(req)
        res = self.resolver.resolve(req, inspection=insp)

        assert res.is_resolved is True
        assert res.canonical_url == SAMPLE_DIRECT_URL
        assert res.original_input == "https://short.url/redirect"

    def test_resolve_metalink_mirrors(self) -> None:
        req = self.detector.detect(SAMPLE_METALINK_XML)
        insp = self.inspector.inspect(req)
        res = self.resolver.resolve(req, inspection=insp)

        assert res.is_resolved is True
        assert len(res.mirrors) == 2
        assert res.mirrors[0] == "https://us.example.com/example.tar.gz"
        assert res.mirrors[1] == "https://eu.example.com/example.tar.gz"

    def test_canonicalize_tracking_urls(self) -> None:
        dirty_url = "https://example.com/download.zip?utm_source=twitter&utm_medium=social&key=123"
        req = self.detector.detect(dirty_url)
        res = self.resolver.resolve(req)

        assert "utm_source" not in res.canonical_url
        assert "utm_medium" not in res.canonical_url
        assert "key=123" in res.canonical_url

    def test_resolve_candidate_backends(self) -> None:
        aria2_backend = FakeBackend(
            backend_id=make_backend_id("aria2"),
            capabilities=CapabilitySet.from_iterable(
                [
                    Capability.HTTP,
                    Capability.HTTPS,
                    Capability.TORRENT,
                    Capability.MAGNET,
                    Capability.METALINK,
                ]
            ),
        )
        ytdlp_backend = FakeBackend(
            backend_id=make_backend_id("yt-dlp"),
            capabilities=CapabilitySet.from_iterable(
                [
                    Capability.MEDIA_EXTRACTION,
                    Capability.FORMAT_SELECTION,
                    Capability.PLAYLIST,
                ]
            ),
        )

        backends = [aria2_backend, ytdlp_backend]

        # Torrent candidate selection
        torrent_req = self.detector.detect(SAMPLE_MAGNET_URI)
        t_res = self.resolver.resolve(torrent_req, available_backends=backends)
        assert make_backend_id("aria2") in t_res.candidate_backends
        assert make_backend_id("yt-dlp") not in t_res.candidate_backends

        # Media candidate selection
        media_req = self.detector.detect(SAMPLE_MEDIA_URL)
        m_res = self.resolver.resolve(media_req, available_backends=backends)
        assert make_backend_id("yt-dlp") in m_res.candidate_backends
        assert make_backend_id("aria2") not in m_res.candidate_backends


class TestAcquisitionPolicyEngine:
    """Test suite for AcquisitionPolicyEngine routing rules."""

    def setup_method(self) -> None:
        self.policy = AcquisitionPolicyEngine()
        self.detector = AcquisitionDetector()
        self.registry = BackendRegistry()

        self.aria2_backend = FakeBackend(
            backend_id=make_backend_id("aria2"),
            capabilities=CapabilitySet.from_iterable(
                [
                    Capability.HTTP,
                    Capability.HTTPS,
                    Capability.TORRENT,
                    Capability.MAGNET,
                    Capability.METALINK,
                    Capability.BASIC_DOWNLOAD,
                ]
            ),
        )
        self.ytdlp_backend = FakeBackend(
            backend_id=make_backend_id("yt-dlp"),
            capabilities=CapabilitySet.from_iterable(
                [
                    Capability.MEDIA_EXTRACTION,
                    Capability.FORMAT_SELECTION,
                ]
            ),
        )

        self.registry.register(self.aria2_backend, default=True)
        self.registry.register(self.ytdlp_backend)

    def test_default_routing_torrents_to_aria2(self) -> None:
        req = self.detector.detect(SAMPLE_MAGNET_URI)
        target = self.policy.evaluate(req, registry=self.registry)
        assert target == "aria2"

    def test_default_routing_media_to_ytdlp(self) -> None:
        req = self.detector.detect(SAMPLE_MEDIA_URL)
        target = self.policy.evaluate(req, registry=self.registry)
        assert target == "yt-dlp"

    def test_explicit_routing_precedence(self) -> None:
        req = self.detector.detect(
            SAMPLE_MEDIA_URL,
            preferred_backend=make_backend_id("custom-engine"),
            selection_policy=SelectionPolicy.EXPLICIT,
        )
        # Without registry restriction, explicit selection is respected
        target = self.policy.evaluate(req)
        assert target == "custom-engine"

    def test_custom_rule_highest_priority(self) -> None:
        # Register rule routing *.iso to custom backend
        custom_backend = FakeBackend(
            backend_id=make_backend_id("fast-iso-downloader"),
            capabilities=CapabilitySet.from_iterable([Capability.BASIC_DOWNLOAD]),
        )
        self.registry.register(custom_backend)

        rule = AcquisitionRule(
            name="route_iso_files",
            target_backend=make_backend_id("fast-iso-downloader"),
            priority=500,
            extensions=(".iso",),
        )
        self.policy.register_rule(rule)

        req = self.detector.detect("https://example.com/linux.iso")
        target = self.policy.evaluate(req, registry=self.registry)
        assert target == "fast-iso-downloader"


class TestAcquisitionInbox:
    """Test suite for AcquisitionInbox state management and deduplication."""

    def setup_method(self) -> None:
        self.event_bus = MagicMock()
        self.inbox = AcquisitionInbox(event_bus=self.event_bus, deduplicate=True)
        self.detector = AcquisitionDetector()

    def test_add_and_get_request(self) -> None:
        req = self.detector.detect(SAMPLE_DIRECT_URL)
        self.inbox.add(req)

        fetched = self.inbox.get(req.id)
        assert fetched is not None
        assert fetched.id == req.id
        assert len(self.inbox) == 1
        assert self.event_bus.publish.called

    def test_deduplicate_active_request(self) -> None:
        req1 = self.detector.detect(SAMPLE_DIRECT_URL)
        self.inbox.add(req1)

        req2 = self.detector.detect(SAMPLE_DIRECT_URL)
        added2 = self.inbox.add(req2)

        # Same input returned, no duplicate added
        assert added2.id == req1.id
        assert len(self.inbox) == 1

    def test_valid_lifecycle_transitions(self) -> None:
        req = self.detector.detect(SAMPLE_DIRECT_URL)
        self.inbox.add(req)

        # DETECTED -> INSPECTING
        u1 = self.inbox.update_status(req.id, AcquisitionStatus.INSPECTING)
        assert u1.status == AcquisitionStatus.INSPECTING

        # INSPECTING -> RESOLVED
        u2 = self.inbox.update_status(
            req.id,
            AcquisitionStatus.RESOLVED,
            preferred_backend=make_backend_id("aria2"),
        )
        assert u2.status == AcquisitionStatus.RESOLVED
        assert u2.preferred_backend == "aria2"

        # RESOLVED -> ACCEPTED
        u3 = self.inbox.accept(req.id)
        assert u3.status == AcquisitionStatus.ACCEPTED

    def test_invalid_lifecycle_transition_raises(self) -> None:
        req = self.detector.detect(SAMPLE_DIRECT_URL)
        self.inbox.add(req)
        self.inbox.accept(req.id)

        # Cannot transition from ACCEPTED to INSPECTING
        with pytest.raises(ValueError, match="Invalid acquisition transition"):
            self.inbox.update_status(req.id, AcquisitionStatus.INSPECTING)

    def test_expire_old_requests(self) -> None:
        req = self.detector.detect(SAMPLE_DIRECT_URL)
        self.inbox.add(req)

        # Expire items older than 0.0 seconds
        expired = self.inbox.expire_older_than(-1.0)
        assert len(expired) == 1
        assert expired[0].status == AcquisitionStatus.EXPIRED


class TestFakeAcquisitionProvider:
    """Test suite for FakeAcquisitionProvider (RULE-025)."""

    def setup_method(self) -> None:
        self.fake_provider = FakeAcquisitionProvider()

    def test_simulate_clipboard(self) -> None:
        req = self.fake_provider.simulate_clipboard_capture(SAMPLE_DIRECT_URL)
        assert req.source_kind == SourceKind.CLIPBOARD
        assert req.detected_kind == DetectedKind.DIRECT_URL
        assert req.provenance.source_application == "FakeClipboard"

    def test_simulate_browser_extension(self) -> None:
        req = self.fake_provider.simulate_browser_extension_capture(
            url=SAMPLE_MEDIA_URL,
            origin="chrome-extension://test-ext",
            referrer="https://youtube.com",
        )
        assert req.source_kind == SourceKind.BROWSER
        assert req.detected_kind == DetectedKind.MEDIA_STREAM
        assert req.provenance.origin_url == "chrome-extension://test-ext"
        assert req.provenance.referrer == "https://youtube.com"

    def test_simulate_drag_and_drop(self) -> None:
        req = self.fake_provider.simulate_drag_and_drop(SAMPLE_MAGNET_URI)
        assert req.source_kind == SourceKind.DRAG_DROP
        assert req.detected_kind == DetectedKind.MAGNET_URI

    def test_simulate_media_inspection(self) -> None:
        req = self.fake_provider.detector.detect(SAMPLE_MEDIA_URL)
        insp = self.fake_provider.simulate_media_inspection(req, title="Sample Clip")
        assert insp.filename == "sample_clip.mp4"
        assert "formats" in insp.media_metadata
