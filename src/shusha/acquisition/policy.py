"""Acquisition Policy Engine (E09-I04).

Evaluates source, payload type, domain rules, MIME types, and backend capabilities
to recommend optimal backend engines for acquisition requests.
"""

from __future__ import annotations

import fnmatch
import os
import re
import urllib.parse
from dataclasses import dataclass

from shusha.acquisition.inspector import InspectionResult
from shusha.backends.registry import BackendRegistry
from shusha.domain.acquisition import (
    AcquisitionRequest,
    DetectedKind,
    SelectionPolicy,
    SourceKind,
)
from shusha.domain.capability import Capability
from shusha.domain.identifiers import BackendId, make_backend_id


@dataclass(frozen=True, slots=True, kw_only=True)
class AcquisitionRule:
    """Configurable routing rule matching input attributes to a target backend."""

    name: str
    target_backend: BackendId
    priority: int = 100
    source_kinds: frozenset[SourceKind] | None = None
    detected_kinds: frozenset[DetectedKind] | None = None
    mime_types: tuple[str, ...] | None = None
    url_patterns: tuple[str, ...] | None = None
    domains: tuple[str, ...] | None = None
    extensions: tuple[str, ...] | None = None
    enabled: bool = True


class AcquisitionPolicyEngine:
    """Evaluates rules and engine capabilities to route acquisition requests."""

    def __init__(self, default_backend_id: BackendId | None = None) -> None:
        self._rules: dict[str, AcquisitionRule] = {}
        self._default_backend_id: BackendId = (
            default_backend_id
            if default_backend_id is not None
            else make_backend_id("aria2")
        )
        self._init_default_rules()

    def _init_default_rules(self) -> None:
        """Register default out-of-the-box routing rules."""
        # Torrent & Magnet -> aria2
        self.register_rule(
            AcquisitionRule(
                name="default_torrents_magnets",
                target_backend=make_backend_id("aria2"),
                priority=10,
                detected_kinds=frozenset(
                    {
                        DetectedKind.TORRENT_FILE,
                        DetectedKind.MAGNET_URI,
                    }
                ),
                extensions=(".torrent",),
                mime_types=("application/x-bittorrent",),
            )
        )
        # Metalink -> aria2
        self.register_rule(
            AcquisitionRule(
                name="default_metalink",
                target_backend=make_backend_id("aria2"),
                priority=10,
                detected_kinds=frozenset({DetectedKind.METALINK_FILE}),
                extensions=(".metalink", ".meta4"),
                mime_types=("application/metalink+xml", "application/metalink4+xml"),
            )
        )
        # Streaming Media & Playlists -> yt-dlp
        self.register_rule(
            AcquisitionRule(
                name="default_media_streaming",
                target_backend=make_backend_id("yt-dlp"),
                priority=10,
                detected_kinds=frozenset(
                    {
                        DetectedKind.MEDIA_STREAM,
                        DetectedKind.PLAYLIST_URL,
                    }
                ),
                domains=(
                    "youtube.com",
                    "youtu.be",
                    "vimeo.com",
                    "twitch.tv",
                    "soundcloud.com",
                    "tiktok.com",
                    "dailymotion.com",
                    "bilibili.com",
                ),
            )
        )

    def register_rule(self, rule: AcquisitionRule) -> None:
        """Register or update a routing rule."""
        self._rules[rule.name] = rule

    def unregister_rule(self, rule_name: str) -> None:
        """Remove a routing rule by name."""
        self._rules.pop(rule_name, None)

    def get_rule(self, rule_name: str) -> AcquisitionRule | None:
        """Retrieve a rule by name."""
        return self._rules.get(rule_name)

    def list_rules(self) -> list[AcquisitionRule]:
        """Return all registered rules sorted by priority descending."""
        return sorted(self._rules.values(), key=lambda r: r.priority, reverse=True)

    def evaluate(
        self,
        request: AcquisitionRequest,
        inspection: InspectionResult | None = None,
        registry: BackendRegistry | None = None,
    ) -> BackendId:
        """Evaluate policies and return the recommended BackendId."""
        # 1. Explicit selection policy
        if (
            request.selection_policy == SelectionPolicy.EXPLICIT
            and request.preferred_backend is not None
            and (
                registry is None or registry.get(request.preferred_backend) is not None
            )
        ):
            return request.preferred_backend

        kind = inspection.detected_kind if inspection else request.detected_kind
        content_type = inspection.content_type if inspection else None
        target_url = (
            inspection.redirect_url
            if (inspection and inspection.redirect_url)
            else request.raw_input
        )
        filename = (
            inspection.filename
            if (inspection and inspection.filename)
            else os.path.basename(urllib.parse.urlparse(target_url).path)
        )
        domain = urllib.parse.urlparse(target_url).hostname or ""

        # 2. Rule-based evaluation (sorted by priority descending)
        for rule in self.list_rules():
            if not rule.enabled:
                continue

            if self._matches_rule(
                rule=rule,
                source_kind=request.source_kind,
                detected_kind=kind,
                content_type=content_type,
                target_url=target_url,
                filename=filename,
                domain=domain,
            ):
                target_id = rule.target_backend
                # Check backend availability if registry provided
                if registry is None or registry.get(target_id) is not None:
                    return target_id

        # 3. Capability-based fallback via BackendRegistry if available
        if registry is not None:
            if kind in (DetectedKind.TORRENT_FILE, DetectedKind.MAGNET_URI):
                torrent_backends = registry.find_by_capability(Capability.TORRENT)
                if torrent_backends:
                    return torrent_backends[0].identity.id

            if kind == DetectedKind.METALINK_FILE:
                metalink_backends = registry.find_by_capability(Capability.METALINK)
                if metalink_backends:
                    return metalink_backends[0].identity.id

            if kind in (DetectedKind.MEDIA_STREAM, DetectedKind.PLAYLIST_URL):
                media_backends = registry.find_by_capability(
                    Capability.MEDIA_EXTRACTION
                )
                if media_backends:
                    return media_backends[0].identity.id

            default_backend = registry.get_default()
            if default_backend is not None:
                return default_backend.identity.id

        # 4. Fallback defaults
        if kind in (DetectedKind.MEDIA_STREAM, DetectedKind.PLAYLIST_URL):
            return make_backend_id("yt-dlp")

        return self._default_backend_id

    def _matches_rule(
        self,
        rule: AcquisitionRule,
        source_kind: SourceKind,
        detected_kind: DetectedKind,
        content_type: str | None,
        target_url: str,
        filename: str | None,
        domain: str,
    ) -> bool:
        """Check if all non-None criteria in rule match the item."""
        if rule.source_kinds is not None and source_kind not in rule.source_kinds:
            return False

        if rule.detected_kinds is not None and detected_kind not in rule.detected_kinds:
            return False

        if rule.mime_types is not None:
            if not content_type:
                return False
            matched = any(
                fnmatch.fnmatch(content_type.lower(), pattern.lower())
                for pattern in rule.mime_types
            )
            if not matched:
                return False

        if rule.domains is not None:
            clean_domain = domain.lower()
            matched = any(
                clean_domain == d.lower() or clean_domain.endswith(f".{d.lower()}")
                for d in rule.domains
            )
            if not matched:
                return False

        if rule.extensions is not None:
            clean_fn = (filename or "").lower()
            clean_url = target_url.lower()
            matched = any(
                clean_fn.endswith(ext.lower()) or clean_url.endswith(ext.lower())
                for ext in rule.extensions
            )
            if not matched:
                return False

        if rule.url_patterns is not None:
            matched = any(
                re.search(pat, target_url, re.IGNORECASE) is not None
                for pat in rule.url_patterns
            )
            if not matched:
                return False

        return True
