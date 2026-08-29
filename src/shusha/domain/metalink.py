"""
Metalink domain models for Shusha 2.
"""

from dataclasses import dataclass

from shusha.domain.values import ByteSize, Checksum, Uri


@dataclass(frozen=True, slots=True)
class MetalinkResource:
    """A mirror or P2P source within a Metalink XML description."""

    uri: Uri
    priority: int = 100
    location: str | None = None


@dataclass(frozen=True, slots=True)
class MetalinkFile:
    """A target file described within a Metalink container."""

    name: str
    size: ByteSize
    checksums: list[Checksum]
    resources: list[MetalinkResource]
