"""Acquisition inspection engine (E09-I02).

Inspects incoming payloads (HTTP headers, MIME types, torrent info hashes,
metalink resources, media metadata) without executing irreversible downloads.
"""

from __future__ import annotations

import contextlib
import hashlib
import io
import os
import re
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Protocol, runtime_checkable

from shusha.domain.acquisition import AcquisitionRequest, DetectedKind
from shusha.domain.download_file import DownloadFile
from shusha.domain.identifiers import AcquisitionId
from shusha.domain.metalink import MetalinkFile, MetalinkResource
from shusha.domain.torrent import TorrentMeta, Tracker
from shusha.domain.values import ByteSize, Checksum, Uri


@dataclass(frozen=True, slots=True, kw_only=True)
class InspectionResult:
    """Strongly typed outcome of inspecting an acquisition payload."""

    acquisition_id: AcquisitionId
    detected_kind: DetectedKind
    content_type: str | None = None
    content_length: ByteSize | None = None
    filename: str | None = None
    is_seekable: bool = False
    redirect_url: str | None = None
    info_hash: str | None = None
    torrent_meta: TorrentMeta | None = None
    metalink_resources: tuple[MetalinkResource, ...] = field(default_factory=tuple)
    metalink_files: tuple[MetalinkFile, ...] = field(default_factory=tuple)
    media_metadata: dict[str, str] = field(default_factory=dict)
    headers: dict[str, str] = field(default_factory=dict)
    is_valid: bool = True
    error_message: str | None = None


@runtime_checkable
class HttpHeaderFetcher(Protocol):
    """Protocol for fetching HTTP response headers and redirect targets."""

    def fetch_headers(
        self, url: str, timeout: float = 5.0
    ) -> tuple[int, dict[str, str], str | None]:
        """Return (status_code, headers_dict, final_redirect_url)."""
        ...


class DefaultHttpHeaderFetcher:
    """Production HTTP header fetcher using urllib with strict timeout and no body consumption."""

    def fetch_headers(
        self, url: str, timeout: float = 5.0
    ) -> tuple[int, dict[str, str], str | None]:
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Shusha/2.0 AcquisitionInspector",
                "Accept-Encoding": "identity",
            },
            method="HEAD",
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout) as response:
                status_code: int = getattr(response, "status", 200)
                final_url: str | None = (
                    response.geturl() if response.geturl() != url else None
                )
                headers = {k.lower(): str(v) for k, v in response.headers.items()}
                return status_code, headers, final_url
        except urllib.error.HTTPError as err:
            headers = (
                {k.lower(): str(v) for k, v in err.headers.items()}
                if err.headers
                else {}
            )
            return err.code, headers, None
        except Exception:
            return 0, {}, None


# --- Pure Python Bencode Parser for Torrents ---


def _decode_bencode(data: bytes) -> tuple[Any, int]:
    """Lightweight pure-Python bencode decoder returning (parsed_object, bytes_consumed)."""
    if not data:
        raise ValueError("Empty bencode payload")

    token = data[:1]
    if token == b"i":
        end = data.find(b"e", 1)
        if end == -1:
            raise ValueError("Malformed bencoded integer")
        return int(data[1:end]), end + 1

    if token == b"l":
        items: list[Any] = []
        pos = 1
        while pos < len(data) and data[pos : pos + 1] != b"e":
            item, consumed = _decode_bencode(data[pos:])
            items.append(item)
            pos += consumed
        if pos >= len(data) or data[pos : pos + 1] != b"e":
            raise ValueError("Unterminated bencoded list")
        return items, pos + 1

    if token == b"d":
        d: dict[bytes, Any] = {}
        pos = 1
        while pos < len(data) and data[pos : pos + 1] != b"e":
            key, consumed = _decode_bencode(data[pos:])
            if not isinstance(key, bytes):
                raise ValueError("Bencoded dictionary keys must be byte strings")
            pos += consumed
            val, consumed = _decode_bencode(data[pos:])
            pos += consumed
            d[key] = val
        if pos >= len(data) or data[pos : pos + 1] != b"e":
            raise ValueError("Unterminated bencoded dict")
        return d, pos + 1

    # Byte string: length:contents
    colon = data.find(b":")
    if colon != -1 and data[:colon].isdigit():
        length = int(data[:colon])
        start = colon + 1
        end = start + length
        if end > len(data):
            raise ValueError("Bencoded string length exceeds available bytes")
        return data[start:end], end

    raise ValueError(f"Unexpected bencode token: {token!r}")


def _encode_bencode(obj: Any) -> bytes:
    """Lightweight pure-Python bencode serializer for info_hash calculation."""
    if isinstance(obj, int):
        return f"i{obj}e".encode("ascii")
    if isinstance(obj, bytes):
        return f"{len(obj)}:".encode("ascii") + obj
    if isinstance(obj, str):
        b = obj.encode("utf-8")
        return f"{len(b)}:".encode("ascii") + b
    if isinstance(obj, list):
        return b"l" + b"".join(_encode_bencode(i) for i in obj) + b"e"
    if isinstance(obj, dict):
        out = io.BytesIO()
        out.write(b"d")
        for k in sorted(obj.keys()):
            kb = k if isinstance(k, bytes) else str(k).encode("utf-8")
            out.write(f"{len(kb)}:".encode("ascii") + kb)
            out.write(_encode_bencode(obj[k]))
        out.write(b"e")
        return out.getvalue()
    raise TypeError(f"Object of type {type(obj)} is not bencode serializable")


class AcquisitionInspector:
    """Inspects acquisition requests and extracts typed metadata safely."""

    def __init__(self, http_fetcher: HttpHeaderFetcher | None = None) -> None:
        self._http_fetcher: HttpHeaderFetcher = (
            http_fetcher if http_fetcher is not None else DefaultHttpHeaderFetcher()
        )

    def inspect(self, request: AcquisitionRequest) -> InspectionResult:
        """Inspect the request according to its detected kind."""
        kind = request.detected_kind

        try:
            if kind == DetectedKind.MAGNET_URI:
                return self._inspect_magnet(request)
            if kind == DetectedKind.TORRENT_FILE:
                return self._inspect_torrent(request)
            if kind == DetectedKind.METALINK_FILE:
                return self._inspect_metalink(request)
            if kind in (DetectedKind.MEDIA_STREAM, DetectedKind.PLAYLIST_URL):
                return self._inspect_media_stream(request)
            if kind == DetectedKind.DIRECT_URL:
                return self._inspect_http_url(request)
            if kind == DetectedKind.RAW_TEXT:
                return self._inspect_raw_text(request)

            return InspectionResult(
                acquisition_id=request.id,
                detected_kind=kind,
                is_valid=True,
            )
        except Exception as err:
            return InspectionResult(
                acquisition_id=request.id,
                detected_kind=kind,
                is_valid=False,
                error_message=f"Inspection failed: {err}",
            )

    def _inspect_magnet(self, request: AcquisitionRequest) -> InspectionResult:
        """Inspect a magnet URI to extract info hash, name, and trackers."""
        raw = request.raw_input.strip()
        parsed = urllib.parse.urlparse(raw)
        params = urllib.parse.parse_qs(parsed.query)

        info_hash: str | None = None
        xt_list = params.get("xt", [])
        for xt in xt_list:
            if "btih:" in xt.lower():
                info_hash = xt.split(":")[-1].lower()
                break

        display_name = params.get("dn", [None])[0]
        trackers = params.get("tr", [])
        exact_len_str = params.get("xl", [None])[0]
        content_length = (
            ByteSize(int(exact_len_str))
            if exact_len_str and exact_len_str.isdigit()
            else None
        )

        tracker_objs = [Tracker(url=tr, tier=i) for i, tr in enumerate(trackers)]
        torrent_meta = None
        if info_hash:
            torrent_meta = TorrentMeta(
                info_hash=info_hash,
                name=display_name or f"magnet-{info_hash[:8]}",
                piece_length=ByteSize(0),
                num_pieces=0,
                total_length=content_length or ByteSize(0),
                files=[],
                trackers=tracker_objs,
            )

        return InspectionResult(
            acquisition_id=request.id,
            detected_kind=DetectedKind.MAGNET_URI,
            filename=display_name,
            content_length=content_length,
            info_hash=info_hash,
            torrent_meta=torrent_meta,
            is_valid=bool(info_hash),
            error_message=None
            if info_hash
            else "Missing BitTorrent info hash (xt=urn:btih:)",
        )

    def _inspect_torrent(self, request: AcquisitionRequest) -> InspectionResult:
        """Inspect torrent payload from file path, raw bencode string, or URL."""
        raw = request.raw_input.strip()

        data: bytes | None = None
        if os.path.exists(raw) and os.path.isfile(raw):
            with open(raw, "rb") as f:
                data = f.read()
        elif raw.startswith("d") and ("8:announce" in raw or "4:info" in raw):
            data = raw.encode("utf-8", errors="surrogateescape")

        if data is None:
            # Torrent file URL or path that doesn't exist locally yet
            if raw.startswith(("http://", "https://", "ftp://")):
                return self._inspect_http_url(request)
            return InspectionResult(
                acquisition_id=request.id,
                detected_kind=DetectedKind.TORRENT_FILE,
                filename=os.path.basename(raw),
                is_valid=True,
            )

        # Parse bencoded torrent data
        decoded, _ = _decode_bencode(data)
        if not isinstance(decoded, dict):
            return InspectionResult(
                acquisition_id=request.id,
                detected_kind=DetectedKind.TORRENT_FILE,
                is_valid=False,
                error_message="Root bencoded structure is not a dictionary",
            )

        info_dict = decoded.get(b"info")
        if not isinstance(info_dict, dict):
            return InspectionResult(
                acquisition_id=request.id,
                detected_kind=DetectedKind.TORRENT_FILE,
                is_valid=False,
                error_message="Missing 'info' dictionary in torrent file",
            )

        # Compute info_hash
        info_bytes = _encode_bencode(info_dict)
        info_hash = hashlib.sha1(info_bytes).hexdigest().lower()

        name_bytes = info_dict.get(b"name", b"unnamed")
        name = (
            name_bytes.decode("utf-8", errors="replace")
            if isinstance(name_bytes, bytes)
            else str(name_bytes)
        )

        piece_len = int(info_dict.get(b"piece length", 0))
        pieces_raw = info_dict.get(b"pieces", b"")
        num_pieces = len(pieces_raw) // 20 if isinstance(pieces_raw, bytes) else 0

        files: list[DownloadFile] = []
        total_bytes = 0

        if b"files" in info_dict and isinstance(info_dict[b"files"], list):
            for i, f_entry in enumerate(info_dict[b"files"]):
                if isinstance(f_entry, dict):
                    f_len = int(f_entry.get(b"length", 0))
                    total_bytes += f_len
                    path_parts = [
                        p.decode("utf-8", errors="replace")
                        for p in f_entry.get(b"path", [])
                        if isinstance(p, bytes)
                    ]
                    f_path = "/".join(path_parts) if path_parts else f"file_{i}"
                    files.append(
                        DownloadFile(
                            index=i,
                            path=f_path,
                            length=ByteSize(f_len),
                            completed_length=ByteSize(0),
                            selected=True,
                            uris=[],
                        )
                    )
        elif b"length" in info_dict:
            f_len = int(info_dict[b"length"])
            total_bytes = f_len
            files.append(
                DownloadFile(
                    index=0,
                    path=name,
                    length=ByteSize(f_len),
                    completed_length=ByteSize(0),
                    selected=True,
                    uris=[],
                )
            )

        trackers: list[Tracker] = []
        if b"announce" in decoded and isinstance(decoded[b"announce"], bytes):
            trackers.append(
                Tracker(
                    url=decoded[b"announce"].decode("utf-8", errors="replace"), tier=0
                )
            )
        if b"announce-list" in decoded and isinstance(decoded[b"announce-list"], list):
            for tier_idx, tier_list in enumerate(decoded[b"announce-list"]):
                if isinstance(tier_list, list):
                    for tr in tier_list:
                        if isinstance(tr, bytes):
                            tr_url = tr.decode("utf-8", errors="replace")
                            if not any(t.url == tr_url for t in trackers):
                                trackers.append(Tracker(url=tr_url, tier=tier_idx))

        comment = (
            decoded.get(b"comment", b"").decode("utf-8", errors="replace")
            if isinstance(decoded.get(b"comment"), bytes)
            else None
        )
        created_by = (
            decoded.get(b"created by", b"").decode("utf-8", errors="replace")
            if isinstance(decoded.get(b"created by"), bytes)
            else None
        )
        creation_date = None
        if b"creation date" in decoded and isinstance(decoded[b"creation date"], int):
            with contextlib.suppress(Exception):
                creation_date = datetime.fromtimestamp(decoded[b"creation date"])

        meta = TorrentMeta(
            info_hash=info_hash,
            name=name,
            piece_length=ByteSize(piece_len),
            num_pieces=num_pieces,
            total_length=ByteSize(total_bytes),
            files=files,
            trackers=trackers,
            comment=comment,
            creation_date=creation_date,
            created_by=created_by,
        )

        return InspectionResult(
            acquisition_id=request.id,
            detected_kind=DetectedKind.TORRENT_FILE,
            filename=name,
            content_length=ByteSize(total_bytes),
            info_hash=info_hash,
            torrent_meta=meta,
            is_valid=True,
        )

    def _inspect_metalink(self, request: AcquisitionRequest) -> InspectionResult:
        """Inspect a Metalink 3.0 / 4.0 XML file or string."""
        raw = request.raw_input.strip()

        xml_content: str | None = None
        if os.path.exists(raw) and os.path.isfile(raw):
            with open(raw, encoding="utf-8", errors="replace") as f:
                xml_content = f.read()
        elif raw.startswith("<") or raw.startswith("<?xml"):
            xml_content = raw

        if not xml_content:
            return InspectionResult(
                acquisition_id=request.id,
                detected_kind=DetectedKind.METALINK_FILE,
                filename=os.path.basename(raw) if not raw.startswith("http") else None,
                is_valid=True,
            )

        try:
            root = ET.fromstring(xml_content)
        except Exception as err:
            return InspectionResult(
                acquisition_id=request.id,
                detected_kind=DetectedKind.METALINK_FILE,
                is_valid=False,
                error_message=f"XML parsing error in Metalink: {err}",
            )

        # Handle XML namespaces
        resources: list[MetalinkResource] = []
        files: list[MetalinkFile] = []
        total_size = 0

        # Metalink v4 (<metalink xmlns="urn:ietf:params:xml:ns:metalink">) or v3 (<metalink version="3.0">)
        file_elements = root.findall(".//{*}file")
        if not file_elements:
            file_elements = root.findall(".//file")

        for f_elem in file_elements:
            f_name = f_elem.attrib.get("name", "unnamed_metalink_file")
            size_elem = f_elem.find("{*}size")
            if size_elem is None:
                size_elem = f_elem.find("size")

            f_size = 0
            if (
                size_elem is not None
                and size_elem.text
                and size_elem.text.strip().isdigit()
            ):
                f_size = int(size_elem.text.strip())
            total_size += f_size

            # Checksums
            checksums: list[Checksum] = []
            hash_elems = (
                f_elem.findall(".//{*}hash")
                or f_elem.findall(".//hash")
                or f_elem.findall("{*}hash")
                or f_elem.findall("hash")
            )
            for h in hash_elems:
                h_algo = h.attrib.get("type", "sha-256")
                h_val = (h.text or "").strip()
                if h_val:
                    with contextlib.suppress(Exception):
                        checksums.append(Checksum(algorithm=h_algo, digest=h_val))

            # Resources (mirrors)
            f_resources: list[MetalinkResource] = []
            url_elems = (
                f_elem.findall(".//{*}url")
                or f_elem.findall(".//url")
                or f_elem.findall("{*}url")
                or f_elem.findall("url")
            )
            for u in url_elems:
                u_text = (u.text or "").strip()
                if u_text:
                    try:
                        u_prio = int(u.attrib.get("priority", "100"))
                        u_loc = u.attrib.get("location")
                        res = MetalinkResource(
                            uri=Uri.parse(u_text), priority=u_prio, location=u_loc
                        )
                        f_resources.append(res)
                        resources.append(res)
                    except Exception:
                        pass

            files.append(
                MetalinkFile(
                    name=f_name,
                    size=ByteSize(f_size),
                    checksums=checksums,
                    resources=f_resources,
                )
            )

        main_filename = files[0].name if files else "metalink_content"
        return InspectionResult(
            acquisition_id=request.id,
            detected_kind=DetectedKind.METALINK_FILE,
            filename=main_filename,
            content_length=ByteSize(total_size) if total_size > 0 else None,
            metalink_resources=tuple(resources),
            metalink_files=tuple(files),
            is_valid=True,
        )

    def _inspect_http_url(self, request: AcquisitionRequest) -> InspectionResult:
        """Inspect HTTP/HTTPS/FTP URL headers via non-destructive HEAD request."""
        url = request.raw_input.strip()
        status_code, headers, redirect_url = self._http_fetcher.fetch_headers(url)

        content_type = headers.get("content-type")
        content_length_str = headers.get("content-length")
        content_length = (
            ByteSize(int(content_length_str))
            if content_length_str and content_length_str.isdigit()
            else None
        )

        # Parse filename from Content-Disposition header if present
        filename = None
        content_disp = headers.get("content-disposition", "")
        if "filename=" in content_disp.lower():
            match = re.search(
                r'filename\*?=(?:UTF-8\'\')?["\']?([^"\';]+)["\']?',
                content_disp,
                re.IGNORECASE,
            )
            if match:
                filename = urllib.parse.unquote(match.group(1).strip())

        if not filename:
            # Fallback to URL path basename
            path = urllib.parse.urlparse(redirect_url or url).path
            filename = os.path.basename(path) or None

        is_seekable = headers.get("accept-ranges", "").lower() == "bytes"

        # Check if HTTP HEAD returned a torrent or metalink MIME type
        detected_kind = request.detected_kind
        if content_type:
            if "application/x-bittorrent" in content_type:
                detected_kind = DetectedKind.TORRENT_FILE
            elif (
                "application/metalink+xml" in content_type
                or "application/metalink4+xml" in content_type
            ):
                detected_kind = DetectedKind.METALINK_FILE

        is_valid = (
            status_code in (200, 206, 301, 302, 303, 307, 308) or status_code == 0
        )
        error_msg = f"HTTP {status_code}" if (status_code >= 400) else None

        return InspectionResult(
            acquisition_id=request.id,
            detected_kind=detected_kind,
            content_type=content_type,
            content_length=content_length,
            filename=filename,
            is_seekable=is_seekable,
            redirect_url=redirect_url,
            headers=headers,
            is_valid=is_valid,
            error_message=error_msg,
        )

    def _inspect_media_stream(self, request: AcquisitionRequest) -> InspectionResult:
        """Inspect media streaming URL or playlist."""
        url = request.raw_input.strip()
        parsed = urllib.parse.urlparse(url)
        meta: dict[str, str] = {
            "hostname": parsed.hostname or "",
            "is_stream": "true",
        }

        query = urllib.parse.parse_qs(parsed.query)
        if "v" in query:
            meta["video_id"] = query["v"][0]
        if "list" in query:
            meta["playlist_id"] = query["list"][0]

        return InspectionResult(
            acquisition_id=request.id,
            detected_kind=request.detected_kind,
            filename=f"media_{parsed.hostname}_{query.get('v', ['item'])[0]}",
            media_metadata=meta,
            is_valid=True,
        )

    def _inspect_raw_text(self, request: AcquisitionRequest) -> InspectionResult:
        """Inspect raw text payload."""
        return InspectionResult(
            acquisition_id=request.id,
            detected_kind=DetectedKind.RAW_TEXT,
            is_valid=True,
        )
