"""Acquisition detection and classification engine (E09-I01).

Classifies raw text, URLs, magnet URIs, torrent files, metalinks, and media
streams into strongly typed AcquisitionRequest domain objects.
"""

from __future__ import annotations

import os
import re
import uuid
from urllib.parse import parse_qs, urlparse

from shusha.domain.acquisition import (
    AcquisitionRequest,
    AcquisitionStatus,
    DetectedKind,
    Provenance,
    SelectionPolicy,
    SourceKind,
)
from shusha.domain.identifiers import BackendId, make_acquisition_id

# Regex patterns for detection
MAGNET_REGEX = re.compile(
    r"^magnet:\?xt=urn:[a-zA-Z0-9]+:[a-zA-Z0-9]{32,40}.*",
    re.IGNORECASE,
)
URL_REGEX = re.compile(
    r"^(https?|ftp|sftp)://[^\s/$.?#].[^\s]*$",
    re.IGNORECASE,
)
EXTRACT_URLS_REGEX = re.compile(
    r"(?:https?|ftp|sftp)://[^\s\"\'<>]+|magnet:\?xt=urn:[a-zA-Z0-9]+:[a-zA-Z0-9]{32,40}[^\s\"\'<>]*",
    re.IGNORECASE,
)

# Common media hosting platforms
MEDIA_HOST_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(
        r"^(?:https?://)?(?:www\.)?(?:youtube\.com|youtu\.be)/watch\?", re.IGNORECASE
    ),
    re.compile(r"^(?:https?://)?(?:www\.)?youtu\.be/[a-zA-Z0-9_-]+", re.IGNORECASE),
    re.compile(
        r"^(?:https?://)?(?:www\.)?youtube\.com/shorts/[a-zA-Z0-9_-]+", re.IGNORECASE
    ),
    re.compile(r"^(?:https?://)?(?:www\.)?vimeo\.com/\d+", re.IGNORECASE),
    re.compile(
        r"^(?:https?://)?(?:www\.)?dailymotion\.com/video/[a-zA-Z0-9]+", re.IGNORECASE
    ),
    re.compile(
        r"^(?:https?://)?(?:www\.)?twitch\.tv/(?:videos/\d+|[a-zA-Z0-9_]+)",
        re.IGNORECASE,
    ),
    re.compile(r"^(?:https?://)?(?:www\.)?soundcloud\.com/[^/]+/[^/]+", re.IGNORECASE),
    re.compile(r"^(?:https?://)?(?:www\.)?tiktok\.com/@[^/]+/video/\d+", re.IGNORECASE),
    re.compile(
        r"^(?:https?://)?(?:www\.)?bilibili\.com/video/(?:av\d+|BV[a-zA-Z0-9]+)",
        re.IGNORECASE,
    ),
)

# Playlist patterns
PLAYLIST_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"^(?:https?://)?(?:www\.)?youtube\.com/playlist\?list=", re.IGNORECASE),
    re.compile(r"^(?:https?://)?(?:www\.)?soundcloud\.com/[^/]+/sets/", re.IGNORECASE),
    re.compile(r"^(?:https?://)?open\.spotify\.com/playlist/", re.IGNORECASE),
)

# Direct streaming manifest extensions
STREAM_EXTENSIONS = (".m3u8", ".mpd", ".f4m", ".ism/manifest")


class AcquisitionDetector:
    """Classifies input candidates into typed AcquisitionRequest items."""

    def __init__(self) -> None:
        pass

    def classify(self, raw_input: str) -> tuple[DetectedKind, dict[str, str]]:
        """Classify a single input string into a DetectedKind with extracted metadata."""
        clean = raw_input.strip()
        metadata: dict[str, str] = {}

        if not clean:
            return DetectedKind.UNKNOWN, metadata

        # 1. Magnet URI detection
        if clean.lower().startswith("magnet:?") or MAGNET_REGEX.match(clean):
            metadata["uri_type"] = "magnet"
            self._extract_magnet_metadata(clean, metadata)
            return DetectedKind.MAGNET_URI, metadata

        # 2. Metalink Content (XML) or Metalink File Path
        if clean.startswith("<?xml") and "<metalink" in clean:
            metadata["format"] = "metalink_xml"
            return DetectedKind.METALINK_FILE, metadata
        if clean.startswith("<metalink"):
            metadata["format"] = "metalink_xml"
            return DetectedKind.METALINK_FILE, metadata

        if os.path.exists(clean) and os.path.isfile(clean):
            lower_path = clean.lower()
            if lower_path.endswith((".metalink", ".meta4")):
                metadata["file_path"] = clean
                metadata["format"] = "metalink_file"
                return DetectedKind.METALINK_FILE, metadata
            if lower_path.endswith(".torrent"):
                metadata["file_path"] = clean
                metadata["format"] = "torrent_file"
                return DetectedKind.TORRENT_FILE, metadata

        # Check for bencoded torrent signature (starts with d...8:announce or d4:info)
        if (
            clean.startswith("d8:announce")
            or clean.startswith("d4:info")
            or (clean.startswith("d") and "8:announce" in clean[:100])
        ):
            metadata["format"] = "torrent_bencode"
            return DetectedKind.TORRENT_FILE, metadata

        # 3. URL Detection
        if URL_REGEX.match(clean):
            parsed = urlparse(clean)
            metadata["scheme"] = parsed.scheme.lower()
            metadata["hostname"] = parsed.hostname or ""
            metadata["path"] = parsed.path

            # Check if URL points directly to a .torrent or .metalink
            path_lower = parsed.path.lower()
            if path_lower.endswith(".torrent"):
                metadata["target_type"] = "torrent"
                return DetectedKind.TORRENT_FILE, metadata
            if path_lower.endswith((".metalink", ".meta4")):
                metadata["target_type"] = "metalink"
                return DetectedKind.METALINK_FILE, metadata

            # Check for playlist URLs
            query_params = parse_qs(parsed.query)
            if "list" in query_params:
                metadata["playlist_id"] = query_params["list"][0]
                return DetectedKind.PLAYLIST_URL, metadata

            for pattern in PLAYLIST_PATTERNS:
                if pattern.match(clean):
                    return DetectedKind.PLAYLIST_URL, metadata

            # Check for media stream manifest extensions
            if any(path_lower.endswith(ext) for ext in STREAM_EXTENSIONS):
                metadata["stream_manifest"] = "true"
                return DetectedKind.MEDIA_STREAM, metadata

            # Check for media hosting sites
            for pattern in MEDIA_HOST_PATTERNS:
                if pattern.match(clean):
                    metadata["media_host"] = parsed.hostname or ""
                    return DetectedKind.MEDIA_STREAM, metadata

            # Default direct URL (HTTP, HTTPS, FTP, SFTP)
            return DetectedKind.DIRECT_URL, metadata

        # 4. Multiline or raw text containing URLs
        extracted = EXTRACT_URLS_REGEX.findall(clean)
        if len(extracted) > 1:
            metadata["extracted_count"] = str(len(extracted))
            return DetectedKind.RAW_TEXT, metadata
        if len(extracted) == 1 and extracted[0] == clean:
            # Single extracted URL that didn't pass strict URL regex
            return DetectedKind.DIRECT_URL, metadata

        return DetectedKind.RAW_TEXT, metadata

    def detect(
        self,
        raw_input: str,
        source_kind: SourceKind = SourceKind.MANUAL,
        provenance: Provenance | None = None,
        preferred_backend: BackendId | None = None,
        selection_policy: SelectionPolicy = SelectionPolicy.AUTOMATIC,
        metadata: dict[str, str] | None = None,
    ) -> AcquisitionRequest:
        """Create a typed AcquisitionRequest from raw input."""
        detected_kind, extracted_meta = self.classify(raw_input)
        merged_metadata = dict(extracted_meta)
        if metadata:
            merged_metadata.update(metadata)

        acq_id = make_acquisition_id(f"acq-{uuid.uuid4().hex[:12]}")
        prov = provenance if provenance is not None else Provenance()

        return AcquisitionRequest(
            id=acq_id,
            source_kind=source_kind,
            raw_input=raw_input.strip(),
            detected_kind=detected_kind,
            status=AcquisitionStatus.DETECTED,
            metadata=merged_metadata,
            preferred_backend=preferred_backend,
            selection_policy=selection_policy,
            provenance=prov,
        )

    def detect_all(
        self,
        raw_input: str,
        source_kind: SourceKind = SourceKind.MANUAL,
        provenance: Provenance | None = None,
        preferred_backend: BackendId | None = None,
    ) -> list[AcquisitionRequest]:
        """Extract and detect multiple AcquisitionRequest items from bulk or multiline text."""
        clean = raw_input.strip()
        if not clean:
            return []

        # Find all embedded URLs and magnet links
        extracted = EXTRACT_URLS_REGEX.findall(clean)
        if extracted:
            return [
                self.detect(
                    item.strip(),
                    source_kind=source_kind,
                    provenance=provenance,
                    preferred_backend=preferred_backend,
                )
                for item in extracted
                if item.strip()
            ]

        # If no regex URLs/magnets matched, check if multiple lines contain file paths
        lines = [line.strip() for line in clean.splitlines() if line.strip()]
        if len(lines) > 1:
            return [
                self.detect(
                    line,
                    source_kind=source_kind,
                    provenance=provenance,
                    preferred_backend=preferred_backend,
                )
                for line in lines
            ]

        return [
            self.detect(
                clean,
                source_kind=source_kind,
                provenance=provenance,
                preferred_backend=preferred_backend,
            )
        ]

    def _extract_magnet_metadata(
        self, magnet_uri: str, metadata: dict[str, str]
    ) -> None:
        """Extract metadata parameters (dn, xt, tr) from a magnet URI."""
        try:
            parsed = urlparse(magnet_uri)
            params = parse_qs(parsed.query)
            if "dn" in params:
                metadata["display_name"] = params["dn"][0]
            if "xt" in params:
                metadata["exact_topic"] = params["xt"][0]
                xt_val = params["xt"][0]
                if "btih:" in xt_val.lower():
                    info_hash = xt_val.split(":")[-1]
                    metadata["info_hash"] = info_hash.lower()
            if "tr" in params:
                metadata["trackers"] = ",".join(params["tr"])
            if "xl" in params:
                metadata["exact_length"] = params["xl"][0]
        except Exception:
            pass
