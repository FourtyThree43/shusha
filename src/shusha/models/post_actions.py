"""Post-download automation, notification sounds, and system power management.

Provides cross-platform implementations for:
- Completion alert sounds (Linux, macOS, Windows).
- Custom post-download hook commands with variable substitution ({file}, {dir}, {gid}).
- Automated system shutdown / sleep on queue completion.
"""

from __future__ import annotations

import platform
import shutil
import subprocess
from pathlib import Path

from shusha.models.logger import LoggerService

logger = LoggerService(__name__)


class PostActions:
    """Handles post-download triggers, shell commands, sounds, and system power management."""

    @classmethod
    def play_alert_sound(cls) -> None:
        """Play a short completion alert chime across Linux, macOS, and Windows."""
        system = platform.system()
        try:
            if system == "Windows":
                import winsound
                beep_fn = getattr(winsound, "MessageBeep", None)
                if callable(beep_fn):
                    beep_fn(getattr(winsound, "MB_ICONASTERISK", 0))
            elif system == "Darwin":
                # macOS
                subprocess.Popen(["afplay", "/System/Library/Sounds/Glass.aiff"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:
                # Linux (try paplay, aplay, or terminal beep)
                if shutil.which("paplay"):
                    sound_path = "/usr/share/sounds/freedesktop/stereo/complete.oga"
                    if Path(sound_path).exists():
                        subprocess.Popen(["paplay", sound_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    else:
                        print("\a", end="", flush=True)
                elif shutil.which("aplay"):
                    print("\a", end="", flush=True)
                else:
                    print("\a", end="", flush=True)
        except Exception as e:
            logger.log(f"Alert sound notice: {e}", level="debug")

    @classmethod
    def execute_completion_command(
        cls,
        command_template: str,
        file_path: str = "",
        dir_path: str = "",
        gid: str = "",
    ) -> bool:
        """Execute a user-configured completion shell script or command.

        Replaces variables:
        - {file}: Full target path of the downloaded file.
        - {dir}: Directory containing the downloaded file.
        - {gid}: Download task GID.

        Args:
            command_template: Shell command string template.
            file_path: Downloaded file path.
            dir_path: Containing folder.
            gid: GID string.

        Returns:
            True if subprocess was dispatched successfully.
        """
        if not command_template:
            return False

        formatted_cmd = (
            command_template.replace("{file}", str(file_path))
            .replace("{dir}", str(dir_path))
            .replace("{gid}", str(gid))
        )

        try:
            logger.log(f"Executing post-download command: {formatted_cmd}", level="info")
            subprocess.Popen(formatted_cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
        except Exception as e:
            logger.log(f"Error executing post-download command: {e}", level="error")
            return False

    @classmethod
    def shutdown_system(cls) -> bool:
        """Execute system shutdown command."""
        system = platform.system()
        try:
            if system == "Windows":
                subprocess.Popen(["shutdown", "/s", "/t", "60"])
            elif system == "Darwin":
                subprocess.Popen(["osascript", "-e", 'tell application "System Events" to shut down'])
            else:
                subprocess.Popen(["shutdown", "-h", "+1"])
            logger.log("System shutdown sequence initiated.", level="warning")
            return True
        except Exception as e:
            logger.log(f"Failed to initiate system shutdown: {e}", level="error")
            return False

    @classmethod
    def sleep_system(cls) -> bool:
        """Put the system into sleep / standby mode."""
        system = platform.system()
        try:
            if system == "Windows":
                subprocess.Popen(["rundll32.exe", "powrprof.dll,SetSuspendState", "0,1,0"])
            elif system == "Darwin":
                subprocess.Popen(["pmset", "sleepnow"])
            else:
                subprocess.Popen(["systemctl", "suspend"])
            logger.log("System sleep initiated.", level="info")
            return True
        except Exception as e:
            logger.log(f"Failed to initiate system sleep: {e}", level="error")
            return False
