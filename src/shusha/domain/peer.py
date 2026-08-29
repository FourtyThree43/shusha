"""
BitTorrent peer model for Shusha 2.
"""

from dataclasses import dataclass

from shusha.domain.identifiers import PeerId
from shusha.domain.values import Bitfield, BitRate, Port


@dataclass(frozen=True, slots=True)
class Peer:
    """Connected BitTorrent peer node."""

    peer_id: PeerId
    ip: str
    port: Port
    bitfield: Bitfield | None
    am_choking: bool
    peer_choking: bool
    download_speed: BitRate
    upload_speed: BitRate
    seeder: bool
