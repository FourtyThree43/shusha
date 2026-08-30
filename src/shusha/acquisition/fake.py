"""Fake Acquisition Provider for deterministic unit/integration testing (RULE-025).

Provides deterministic simulation of clipboard, browser, drag/drop,
URL resolution, media inspection, and mock HTTP header inspection without
network access.
"""

from __future__ import annotations

from collections.abc import Sequence

from shusha.acquisition.detector import AcquisitionDetector
from shusha.acquisition.inspector import (
    AcquisitionInspector,
    InspectionResult,
)
from shusha.acquisition.policy import AcquisitionPolicyEngine
from shusha.acquisition.resolver import AcquisitionResolver, ResolutionResult
from shusha.backends.contract import BackendProtocol
from shusha.domain.acquisition import (
    AcquisitionRequest,
    Provenance,
    SourceKind,
)
from shusha.domain.values import ByteSize

# Pre-canned test vectors
SAMPLE_DIRECT_URL = "https://releases.ubuntu.com/24.04/ubuntu-24.04-desktop-amd64.iso"
SAMPLE_MAGNET_URI = (
    "magnet:?xt=urn:btih:a88fda5954e89178c372716a6a78b8180ed4dad3"
    "&dn=ubuntu-24.04-desktop-amd64.iso"
    "&tr=https%3A%2F%2Ftorrent.ubuntu.com%2Fannounce"
)
SAMPLE_MEDIA_URL = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
SAMPLE_PLAYLIST_URL = (
    "https://www.youtube.com/playlist?list=PLrEnWoR732-DY3XePkhmsP4Fv0r5sM8Q_"
)
SAMPLE_METALINK_XML = """<?xml version="1.0" encoding="utf-8"?>
<metalink version="3.0" xmlns="http://www.metalinker.org/">
  <files>
    <file name="example.tar.gz">
      <size>10485760</size>
      <verification>
        <hash type="sha-256">e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855</hash>
      </verification>
      <resources>
        <url type="http" location="us" priority="10">https://us.example.com/example.tar.gz</url>
        <url type="http" location="eu" priority="20">https://eu.example.com/example.tar.gz</url>
      </resources>
    </file>
  </files>
</metalink>"""
SAMPLE_TORRENT_BENCODE = (
    b"d8:announce27:http://tracker.example.com/4:info"
    b"d6:lengthi1048576e4:name11:example.iso12:piece lengthi262144e"
    b"6:pieces20:12345678901234567890ee"
)


class FakeHttpHeaderFetcher:
    """Deterministic in-memory HTTP header inspector for offline tests."""

    def __init__(self) -> None:
        self.responses: dict[str, tuple[int, dict[str, str], str | None]] = {
            SAMPLE_DIRECT_URL: (
                200,
                {
                    "content-type": "application/x-iso9660-image",
                    "content-length": "6100000000",
                    "content-disposition": 'attachment; filename="ubuntu-24.04-desktop-amd64.iso"',
                    "accept-ranges": "bytes",
                },
                None,
            ),
            "https://short.url/redirect": (
                302,
                {"location": SAMPLE_DIRECT_URL},
                SAMPLE_DIRECT_URL,
            ),
        }

    def set_response(
        self,
        url: str,
        status_code: int = 200,
        headers: dict[str, str] | None = None,
        redirect_url: str | None = None,
    ) -> None:
        """Configure mock HTTP response for a URL."""
        self.responses[url] = (
            status_code,
            headers
            or {"content-type": "application/octet-stream", "content-length": "1024"},
            redirect_url,
        )

    def fetch_headers(
        self, url: str, timeout: float = 5.0
    ) -> tuple[int, dict[str, str], str | None]:
        if url in self.responses:
            return self.responses[url]
        return (
            200,
            {"content-type": "application/octet-stream", "content-length": "1048576"},
            None,
        )


class FakeAcquisitionProvider:
    """Deterministic acquisition provider simulating all acquisition input channels."""

    def __init__(self) -> None:
        self.detector = AcquisitionDetector()
        self.fake_http = FakeHttpHeaderFetcher()
        self.inspector = AcquisitionInspector(http_fetcher=self.fake_http)
        self.resolver = AcquisitionResolver()
        self.policy = AcquisitionPolicyEngine()

    def simulate_clipboard_capture(self, text: str) -> AcquisitionRequest:
        """Simulate capturing an item from the system clipboard."""
        return self.detector.detect(
            raw_input=text,
            source_kind=SourceKind.CLIPBOARD,
            provenance=Provenance(source_application="FakeClipboard"),
        )

    def simulate_browser_extension_capture(
        self,
        url: str,
        origin: str = "chrome-extension://shusha-browser-ext",
        referrer: str | None = None,
        user_agent: str | None = None,
    ) -> AcquisitionRequest:
        """Simulate capturing a download request from a browser extension."""
        return self.detector.detect(
            raw_input=url,
            source_kind=SourceKind.BROWSER,
            provenance=Provenance(
                origin_url=origin,
                referrer=referrer,
                user_agent=user_agent or "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
                source_application="BrowserExtension",
            ),
        )

    def simulate_drag_and_drop(self, raw_input: str) -> AcquisitionRequest:
        """Simulate drag-and-drop ingestion of a file path, URL, or payload."""
        return self.detector.detect(
            raw_input=raw_input,
            source_kind=SourceKind.DRAG_DROP,
            provenance=Provenance(source_application="DesktopDragDrop"),
        )

    def simulate_media_inspection(
        self,
        request: AcquisitionRequest,
        title: str = "Test Video",
        formats: list[str] | None = None,
    ) -> InspectionResult:
        """Simulate fast deterministic media stream inspection."""
        fmt_list = formats or ["1080p_mp4", "720p_mp4", "audio_only_m4a"]
        return InspectionResult(
            acquisition_id=request.id,
            detected_kind=request.detected_kind,
            filename=f"{title.lower().replace(' ', '_')}.mp4",
            content_length=ByteSize(150_000_000),
            media_metadata={
                "title": title,
                "formats": ",".join(fmt_list),
                "duration_seconds": "300",
                "extractor": "fake_media_resolver",
            },
            is_valid=True,
        )

    def simulate_url_resolution(
        self,
        request: AcquisitionRequest,
        canonical_target: str | None = None,
        mirrors: list[str] | None = None,
        available_backends: Sequence[BackendProtocol] | None = None,
    ) -> ResolutionResult:
        """Simulate URL resolution with optional mock mirrors and target redirect."""
        res = self.resolver.resolve(
            request=request,
            inspection=self.inspector.inspect(request),
            available_backends=available_backends,
        )
        if canonical_target or mirrors:
            resolved_url = canonical_target or request.raw_input
            mirror_tuple = tuple(mirrors) if mirrors else ()
            res = ResolutionResult(
                acquisition_id=res.acquisition_id,
                original_input=res.original_input,
                canonical_url=resolved_url,
                mirrors=mirror_tuple or res.mirrors,
                candidate_backends=res.candidate_backends,
                resolved_kind=res.resolved_kind,
                metadata=res.metadata,
                is_resolved=res.is_resolved,
                error=res.error,
            )
        return res
