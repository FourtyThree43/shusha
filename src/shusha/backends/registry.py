"""Backend Registry for discovery, registration, and routing (E05-I02)."""

from __future__ import annotations

import logging

from shusha.backends.contract import BackendProtocol
from shusha.domain.acquisition import AcquisitionRequest, DetectedKind
from shusha.domain.capability import Capability
from shusha.domain.identifiers import BackendId

logger = logging.getLogger(__name__)


class BackendRegistry:
    """Central registry for discovering, selecting, and routing to backends."""

    def __init__(self) -> None:
        self._backends: dict[BackendId, BackendProtocol] = {}
        self._default_backend_id: BackendId | None = None

    def register(self, backend: BackendProtocol, default: bool = False) -> None:
        """Register a backend instance."""
        bid = backend.identity.id
        self._backends[bid] = backend
        if default or self._default_backend_id is None:
            self._default_backend_id = bid
        logger.info(
            "Registered backend '%s' (version %s)", bid, backend.identity.version
        )

    def unregister(self, backend_id: BackendId) -> None:
        """Unregister a backend."""
        if backend_id in self._backends:
            del self._backends[backend_id]
            if self._default_backend_id == backend_id:
                self._default_backend_id = (
                    next(iter(self._backends.keys())) if self._backends else None
                )

    def get(self, backend_id: BackendId) -> BackendProtocol | None:
        """Retrieve backend by its ID."""
        return self._backends.get(backend_id)

    def get_default(self) -> BackendProtocol | None:
        """Retrieve the current default backend."""
        if not self._default_backend_id:
            return None
        return self._backends.get(self._default_backend_id)

    def set_default(self, backend_id: BackendId) -> None:
        """Set the default backend ID."""
        if backend_id not in self._backends:
            raise KeyError(f"Backend '{backend_id}' is not registered.")
        self._default_backend_id = backend_id

    def list_backends(self) -> list[BackendProtocol]:
        """List all registered backends."""
        return list(self._backends.values())

    def find_by_capability(self, capability: Capability | str) -> list[BackendProtocol]:
        """Find all registered backends supporting a given capability."""
        return [b for b in self._backends.values() if b.capabilities.has(capability)]

    def select_for_request(self, request: AcquisitionRequest) -> BackendProtocol | None:
        """Select the most appropriate backend for an incoming acquisition request."""
        # 1. Explicit preference
        if request.preferred_backend and request.preferred_backend in self._backends:
            return self._backends[request.preferred_backend]

        # 2. Rule-based routing based on detected payload
        if (
            request.detected_kind == DetectedKind.TORRENT_FILE
            or request.detected_kind == DetectedKind.MAGNET_URI
        ):
            torrent_backends = self.find_by_capability(Capability.TORRENT)
            if torrent_backends:
                return torrent_backends[0]

        if request.detected_kind == DetectedKind.METALINK_FILE:
            metalink_backends = self.find_by_capability(Capability.METALINK)
            if metalink_backends:
                return metalink_backends[0]

        if request.detected_kind in (
            DetectedKind.MEDIA_STREAM,
            DetectedKind.PLAYLIST_URL,
        ):
            media_backends = self.find_by_capability(Capability.MEDIA_EXTRACTION)
            if media_backends:
                return media_backends[0]

        # 3. Fallback to default backend
        return self.get_default()
