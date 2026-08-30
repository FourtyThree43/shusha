"""Acquisition resolution engine (E09-I03).

Resolves URL redirects, mirror endpoints, streaming media sources,
and determines compatible backend engine candidates based on capabilities.
"""

from __future__ import annotations

import urllib.parse
from collections.abc import Sequence
from dataclasses import dataclass, field

from shusha.acquisition.inspector import InspectionResult
from shusha.backends.contract import BackendProtocol
from shusha.domain.acquisition import AcquisitionRequest, DetectedKind
from shusha.domain.capability import Capability
from shusha.domain.identifiers import AcquisitionId, BackendId, make_backend_id


@dataclass(frozen=True, slots=True, kw_only=True)
class ResolutionResult:
    """Strongly typed outcome of resolving an acquisition item."""

    acquisition_id: AcquisitionId
    original_input: str
    canonical_url: str
    mirrors: tuple[str, ...] = field(default_factory=tuple)
    candidate_backends: tuple[BackendId, ...] = field(default_factory=tuple)
    resolved_kind: DetectedKind = DetectedKind.UNKNOWN
    metadata: dict[str, str] = field(default_factory=dict)
    is_resolved: bool = True
    error: str | None = None


class AcquisitionResolver:
    """Resolves acquisition requests into canonical targets and candidate backends."""

    def __init__(self) -> None:
        pass

    def resolve(
        self,
        request: AcquisitionRequest,
        inspection: InspectionResult | None = None,
        available_backends: Sequence[BackendProtocol] | None = None,
    ) -> ResolutionResult:
        """Resolve canonical target, mirrors, and compatible backend candidates."""
        orig_input = request.raw_input.strip()
        kind = inspection.detected_kind if inspection else request.detected_kind
        meta: dict[str, str] = dict(request.metadata)
        if inspection and inspection.media_metadata:
            meta.update(inspection.media_metadata)

        canonical_url = orig_input
        mirrors: list[str] = []

        # 1. Resolve redirect if inspection discovered one
        if inspection and inspection.redirect_url:
            canonical_url = inspection.redirect_url
            meta["redirect_resolved_from"] = orig_input

        # 2. Extract mirrors if Metalink inspection discovered resources
        if inspection and inspection.metalink_resources:
            # Sort by priority ascending (lower priority number = preferred in Metalink standard)
            sorted_res = sorted(inspection.metalink_resources, key=lambda r: r.priority)
            if sorted_res:
                canonical_url = sorted_res[0].uri.raw_uri
                mirrors = [r.uri.raw_uri for r in sorted_res]

        # 3. Clean and canonicalize URL parameters for direct URLs
        if kind == DetectedKind.DIRECT_URL:
            canonical_url = self._canonicalize_url(canonical_url)

        # 4. Resolve candidate backends based on capabilities
        candidate_backends = self._select_candidate_backends(
            kind=kind,
            available_backends=available_backends,
            preferred_backend=request.preferred_backend,
        )

        return ResolutionResult(
            acquisition_id=request.id,
            original_input=orig_input,
            canonical_url=canonical_url,
            mirrors=tuple(mirrors),
            candidate_backends=tuple(candidate_backends),
            resolved_kind=kind,
            metadata=meta,
            is_resolved=bool(candidate_backends or kind != DetectedKind.UNKNOWN),
            error=None
            if inspection is None or inspection.is_valid
            else inspection.error_message,
        )

    def _canonicalize_url(self, url: str) -> str:
        """Strip tracking parameters (utm_*, fbclid, etc.) from canonical direct download URLs."""
        try:
            parsed = urllib.parse.urlparse(url)
            if not parsed.query:
                return url
            query_tuples = urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)
            tracking_keys = {
                "utm_source",
                "utm_medium",
                "utm_campaign",
                "utm_term",
                "utm_content",
                "fbclid",
                "gclid",
            }
            cleaned_query = [
                (k, v) for k, v in query_tuples if k.lower() not in tracking_keys
            ]
            new_query = urllib.parse.urlencode(cleaned_query)
            return urllib.parse.urlunparse(
                (
                    parsed.scheme,
                    parsed.netloc,
                    parsed.path,
                    parsed.params,
                    new_query,
                    parsed.fragment,
                )
            )
        except Exception:
            return url

    def _select_candidate_backends(
        self,
        kind: DetectedKind,
        available_backends: Sequence[BackendProtocol] | None,
        preferred_backend: BackendId | None,
    ) -> list[BackendId]:
        """Determine candidate backends capable of handling this acquisition payload."""
        candidates: list[BackendId] = []

        if available_backends:
            for b in available_backends:
                bid = b.identity.id
                caps = b.capabilities

                if kind in (DetectedKind.MAGNET_URI, DetectedKind.TORRENT_FILE):
                    if caps.has(Capability.TORRENT) or caps.has(Capability.MAGNET):
                        candidates.append(bid)
                elif kind == DetectedKind.METALINK_FILE:
                    if caps.has(Capability.METALINK):
                        candidates.append(bid)
                elif kind in (DetectedKind.MEDIA_STREAM, DetectedKind.PLAYLIST_URL):
                    if caps.has(Capability.MEDIA_EXTRACTION):
                        candidates.append(bid)
                elif kind == DetectedKind.DIRECT_URL:
                    if caps.has(Capability.HTTP) or caps.has(Capability.BASIC_DOWNLOAD):
                        candidates.append(bid)
                else:
                    if caps.has(Capability.BASIC_DOWNLOAD):
                        candidates.append(bid)

        # If no registered backends provided, supply standard known engine candidates
        if not candidates:
            if preferred_backend:
                candidates.append(preferred_backend)
            elif kind in (
                DetectedKind.MAGNET_URI,
                DetectedKind.TORRENT_FILE,
                DetectedKind.METALINK_FILE,
            ):
                candidates.append(make_backend_id("aria2"))
            elif kind in (DetectedKind.MEDIA_STREAM, DetectedKind.PLAYLIST_URL):
                candidates.append(make_backend_id("yt-dlp"))
            elif kind == DetectedKind.DIRECT_URL:
                candidates.append(make_backend_id("aria2"))

        # Put preferred backend first if it's in candidates
        if preferred_backend and preferred_backend in candidates:
            candidates.remove(preferred_backend)
            candidates.insert(0, preferred_backend)

        return candidates
