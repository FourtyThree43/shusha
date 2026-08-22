"""Torrent and Magnet URI creator module.

Enables creating .torrent metadata and generating magnet:?xt=urn:btih:... URIs
from local files and directories with configurable piece sizes, tracker lists,
web seeds, comments, and DHT private flags.
"""

from __future__ import annotations

import hashlib
import os
from pathlib import Path
from typing import Any
from urllib.parse import quote

from shusha.models.logger import LoggerService
from shusha.models.tracker_service import TrackerService

logger = LoggerService(__name__)


def bencode(data: Any) -> bytes:
    """Encode Python data structures into Bencode format."""
    if isinstance(data, int):
        return f"i{data}e".encode("ascii")
    if isinstance(data, (bytes, bytearray)):
        return f"{len(data)}:".encode("ascii") + bytes(data)
    if isinstance(data, str):
        encoded = data.encode("utf-8")
        return f"{len(encoded)}:".encode("ascii") + encoded
    if isinstance(data, list):
        return b"l" + b"".join(bencode(item) for item in data) + b"e"
    if isinstance(data, dict):
        items = sorted(data.items(), key=lambda kv: kv[0].encode("utf-8") if isinstance(kv[0], str) else kv[0])
        return b"d" + b"".join(bencode(k) + bencode(v) for k, v in items) + b"e"
    raise TypeError(f"Cannot bencode object of type {type(data)}")


class TorrentCreator:
    """Creates BitTorrent (.torrent) metadata and magnet URIs from local filesystem targets."""

    @classmethod
    def create_torrent_file(
        cls,
        target_path: str | Path,
        output_file: str | Path | None = None,
        piece_length: int = 512 * 1024,  # 512 KiB default
        trackers: list[str] | None = None,
        web_seeds: list[str] | None = None,
        comment: str = "Created with Shusha Download Manager",
        created_by: str = "Shusha-DM",
        is_private: bool = False,
    ) -> tuple[Path, str]:
        """Create a .torrent file and return its path and Magnet URI.

        Args:
            target_path: Path to single file or directory to package.
            output_file: Optional target .torrent output path.
            piece_length: Piece length in bytes (power of 2, e.g. 512KB, 1MB, 2MB).
            trackers: Optional list of tracker URLs.
            web_seeds: Optional list of HTTP/HTTPS web seed URLs.
            comment: Optional torrent description comment.
            created_by: Client creator tag.
            is_private: If True, disables DHT and PEX (private tracker flag).

        Returns:
            Tuple of (Path to written .torrent file, Magnet URI string).
        """
        source = Path(target_path).resolve()
        if not source.exists():
            raise FileNotFoundError(f"Target path does not exist: {source}")

        tracker_list = trackers or TrackerService.get_trackers()[:10]
        announce = tracker_list[0] if tracker_list else "udp://tracker.opentrackr.org:1337/announce"
        announce_list = [[t] for t in tracker_list]

        # Calculate piece hashes
        files_info: list[dict[str, Any]] = []
        piece_hashes = bytearray()
        buffer = bytearray()

        if source.is_file():
            file_len = source.stat().st_size
            with open(source, "rb") as f:
                while chunk := f.read(piece_length - len(buffer)):
                    buffer.extend(chunk)
                    if len(buffer) == piece_length:
                        piece_hashes.extend(hashlib.sha1(buffer).digest())
                        buffer.clear()
            if buffer:
                piece_hashes.extend(hashlib.sha1(buffer).digest())
                buffer.clear()

            info_dict: dict[str, Any] = {
                "name": source.name,
                "length": file_len,
                "piece length": piece_length,
                "pieces": bytes(piece_hashes),
            }
        else:
            # Multi-file directory
            all_files: list[Path] = []
            for root, _, filenames in os.walk(source):
                for fn in sorted(filenames):
                    all_files.append(Path(root) / fn)

            for fp in all_files:
                flen = fp.stat().st_size
                rel_parts = fp.relative_to(source).parts
                files_info.append({"length": flen, "path": list(rel_parts)})

                with open(fp, "rb") as f:
                    while chunk := f.read(piece_length - len(buffer)):
                        buffer.extend(chunk)
                        if len(buffer) == piece_length:
                            piece_hashes.extend(hashlib.sha1(buffer).digest())
                            buffer.clear()

            if buffer:
                piece_hashes.extend(hashlib.sha1(buffer).digest())
                buffer.clear()

            info_dict = {
                "name": source.name,
                "files": files_info,
                "piece length": piece_length,
                "pieces": bytes(piece_hashes),
            }

        if is_private:
            info_dict["private"] = 1

        # Calculate InfoHash
        info_bencoded = bencode(info_dict)
        info_hash = hashlib.sha1(info_bencoded).hexdigest()

        torrent_dict: dict[str, Any] = {
            "announce": announce,
            "announce-list": announce_list,
            "info": info_dict,
            "created by": created_by,
            "comment": comment,
        }

        if web_seeds:
            torrent_dict["url-list"] = web_seeds

        # Determine output file path
        if output_file:
            out_path = Path(output_file).resolve()
        else:
            out_path = source.parent / f"{source.name}.torrent"

        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_bytes(bencode(torrent_dict))

        # Construct Magnet URI
        magnet_uri = f"magnet:?xt=urn:btih:{info_hash}&dn={quote(source.name)}"
        for tr in tracker_list[:5]:
            magnet_uri += f"&tr={quote(tr)}"

        logger.log(f"Created torrent {out_path} (InfoHash: {info_hash})", level="info")
        return out_path, magnet_uri
