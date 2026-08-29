"""
Post-download action service: checksum verification, sound cues, system notifications.
"""

import hashlib
import logging
import subprocess
from collections.abc import Sequence
from pathlib import Path

logger = logging.getLogger(__name__)


class PostActionService:
    """Handles post-completion actions and verification on downloaded artifacts."""

    @staticmethod
    def calculate_file_hash(file_path: Path, algorithm: str = "sha256") -> str:
        """Compute the cryptographic digest of a local file in streaming blocks."""
        if not file_path.exists() or not file_path.is_file():
            raise FileNotFoundError(
                f"Target file for hash verification not found: '{file_path}'"
            )

        h = hashlib.new(algorithm.lower().replace("-", ""))
        with open(file_path, "rb") as f:
            while chunk := f.read(65536):
                h.update(chunk)
        return h.hexdigest().lower()

    @classmethod
    def verify_checksum(
        cls, file_path: Path, expected_hash: str, algorithm: str = "sha256"
    ) -> bool:
        """Verify that a file matches an expected checksum."""
        actual = cls.calculate_file_hash(file_path, algorithm)
        return actual == expected_hash.strip().lower()

    @staticmethod
    def execute_custom_command(command_args: Sequence[str]) -> bool:
        """Execute a safe post-download program using explicit argument arrays."""
        if not command_args:
            return False
        try:
            subprocess.run(
                list(command_args),
                check=True,
                shell=False,
                timeout=30.0,
            )
            return True
        except Exception as e:
            logger.error("Failed to execute post-download hook: %s", e)
            return False
