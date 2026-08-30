"""Safe, strongly typed subprocess adapter for yt-dlp (Epic E08-I01)."""

from __future__ import annotations

import json
import logging
import subprocess
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from shusha.backends.errors import (
    BackendConnectionError,
    BackendExecutionError,
    BackendTimeoutError,
)
from shusha.domain.identifiers import make_backend_id

logger = logging.getLogger(__name__)


class YtDlpAdapter:
    """Safe, typed subprocess executor for the yt-dlp media engine."""

    def __init__(
        self,
        executable: str = "yt-dlp",
        default_timeout: float = 60.0,
    ) -> None:
        self._executable = executable
        self._default_timeout = default_timeout
        self._backend_id = make_backend_id("ytdlp")

    @property
    def executable(self) -> str:
        """Configured executable path or binary name."""
        return self._executable

    def check_available(self) -> bool:
        """Check if yt-dlp binary is installed and executable."""
        try:
            cmd = [self._executable, "--version"]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10.0,
                check=False,
            )
            return result.returncode == 0
        except subprocess.SubprocessError, FileNotFoundError, OSError:
            return False

    def get_version(self) -> str:
        """Retrieve yt-dlp version string."""
        try:
            cmd = [self._executable, "--version"]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10.0,
                check=False,
            )
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip()
        except (subprocess.SubprocessError, FileNotFoundError, OSError) as err:
            logger.debug("Failed to retrieve yt-dlp version: %s", err)
        return "unknown"

    def extract_info(
        self,
        url: str,
        *,
        flat_playlist: bool = False,
        extra_args: Sequence[str] | None = None,
        timeout: float | None = None,
    ) -> dict[str, Any]:
        """Extract media metadata as a JSON dictionary without downloading."""
        clean_url = url.strip()
        if not clean_url:
            raise BackendExecutionError(
                "Media URL cannot be empty.", backend_id=self._backend_id
            )

        cmd: list[str] = [
            self._executable,
            "--dump-json",
            "--no-warnings",
            "--no-download",
        ]

        if flat_playlist:
            cmd.append("--flat-playlist")

        if extra_args:
            cmd.extend(extra_args)

        # End of options delimiter to prevent option injection
        cmd.extend(["--", clean_url])

        effective_timeout = timeout if timeout is not None else self._default_timeout

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=effective_timeout,
                check=False,
            )
        except FileNotFoundError as err:
            raise BackendConnectionError(
                f"yt-dlp executable not found at '{self._executable}'",
                backend_id=self._backend_id,
            ) from err
        except subprocess.TimeoutExpired as err:
            raise BackendTimeoutError(
                f"yt-dlp extract_info timed out after {effective_timeout}s for URL: {clean_url}",
                backend_id=self._backend_id,
            ) from err
        except OSError as err:
            raise BackendExecutionError(
                f"yt-dlp process execution failed: {err}",
                backend_id=self._backend_id,
            ) from err

        if result.returncode != 0:
            err_msg = (
                result.stderr.strip()
                or result.stdout.strip()
                or f"Exit code {result.returncode}"
            )
            raise BackendExecutionError(
                f"yt-dlp extract_info failed: {err_msg}",
                backend_id=self._backend_id,
            )

        output_str = result.stdout.strip()
        if not output_str:
            raise BackendExecutionError(
                "yt-dlp returned empty output.", backend_id=self._backend_id
            )

        # Handle potential multiple JSON lines (e.g. flat-playlist items)
        lines = [line.strip() for line in output_str.splitlines() if line.strip()]
        if len(lines) > 1:
            entries: list[dict[str, Any]] = []
            for idx, line in enumerate(lines):
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError as err:
                    logger.warning("Failed to decode JSON line %d: %s", idx, err)
            return {
                "_type": "playlist",
                "entries": entries,
                "title": entries[0].get("playlist_title") if entries else "Playlist",
                "id": entries[0].get("playlist_id") if entries else "playlist",
            }

        try:
            data = json.loads(lines[0])
            if not isinstance(data, dict):
                raise BackendExecutionError(
                    f"Expected JSON dictionary from yt-dlp, got {type(data).__name__}",
                    backend_id=self._backend_id,
                )
            return data
        except json.JSONDecodeError as err:
            raise BackendExecutionError(
                f"Failed to parse yt-dlp JSON output: {err}",
                backend_id=self._backend_id,
            ) from err

    def build_download_args(
        self,
        url: str,
        *,
        output_dir: str | Path | None = None,
        format_id: str | None = None,
        output_template: str | None = None,
        extract_audio: bool = False,
        audio_format: str | None = None,
        audio_quality: str | None = None,
        write_subtitles: bool = False,
        subtitle_langs: Sequence[str] | None = None,
        write_thumbnail: bool = False,
        embed_thumbnail: bool = False,
        embed_metadata: bool = False,
        rate_limit: str | None = None,
        extra_args: Sequence[str] | None = None,
    ) -> list[str]:
        """Construct safe command-line argument array for yt-dlp download execution."""
        clean_url = url.strip()
        cmd: list[str] = [self._executable, "--no-warnings"]

        if output_dir:
            cmd.extend(["-P", str(output_dir)])

        if output_template:
            cmd.extend(["-o", output_template])

        if format_id:
            cmd.extend(["-f", format_id])

        if extract_audio:
            cmd.append("-x")
            if audio_format:
                cmd.extend(["--audio-format", audio_format])
            if audio_quality:
                cmd.extend(["--audio-quality", audio_quality])

        if write_subtitles:
            cmd.append("--write-subs")
            if subtitle_langs:
                cmd.extend(["--sub-langs", ",".join(subtitle_langs)])

        if write_thumbnail:
            cmd.append("--write-thumbnail")

        if embed_thumbnail:
            cmd.append("--embed-thumbnail")

        if embed_metadata:
            cmd.append("--embed-metadata")

        if rate_limit:
            cmd.extend(["-r", rate_limit])

        if extra_args:
            cmd.extend(extra_args)

        cmd.extend(["--", clean_url])
        return cmd
