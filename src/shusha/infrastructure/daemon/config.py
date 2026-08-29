"""
Configuration generator and argument builder for aria2 daemon supervision.
"""

from dataclasses import dataclass, field
from pathlib import Path

from shusha.infrastructure.aria2.option_registry import OptionRegistry


@dataclass(slots=True)
class DaemonConfig:
    """Daemon launch options and configuration settings."""

    host: str = "127.0.0.1"
    port: int = 6800
    secret: str | None = None
    download_dir: Path = field(default_factory=lambda: Path.home() / "Downloads")
    session_file: Path | None = None
    input_file: Path | None = None
    log_file: Path | None = None
    max_concurrent_downloads: int = 5
    max_connection_per_server: int = 16
    split: int = 16
    min_split_size: str = "1M"
    listen_all: bool = False
    extra_options: dict[str, str] = field(default_factory=dict)

    def to_options_dict(self) -> dict[str, str]:
        """Convert structured daemon config to option dictionary."""
        opts: dict[str, str] = {
            "enable-rpc": "true",
            "rpc-listen-port": str(self.port),
            "rpc-listen-all": "true" if self.listen_all else "false",
            "rpc-allow-origin-all": "true",
            "dir": str(self.download_dir),
            "max-concurrent-downloads": str(self.max_concurrent_downloads),
            "max-connection-per-server": str(self.max_connection_per_server),
            "split": str(self.split),
            "min-split-size": self.min_split_size,
            "auto-save-interval": "30",
            "save-session-interval": "30",
            "check-integrity": "true",
            "continue": "true",
        }

        if self.secret:
            opts["rpc-secret"] = self.secret

        if self.session_file:
            opts["save-session"] = str(self.session_file)

        if self.input_file and self.input_file.exists():
            opts["input-file"] = str(self.input_file)

        if self.log_file:
            opts["log"] = str(self.log_file)
            opts["log-level"] = "notice"

        # Apply user overrides
        for k, v in self.extra_options.items():
            clean_k = k.lstrip("-")
            opts[clean_k] = str(v)

        return opts

    def build_cli_arguments(self, registry: OptionRegistry | None = None) -> list[str]:
        """Generate CLI arguments array for subprocess invocation."""
        reg = registry or OptionRegistry.get_default_registry()
        opts = self.to_options_dict()
        return reg.serialize_for_cli(opts)

    def build_redacted_arguments(
        self, registry: OptionRegistry | None = None
    ) -> list[str]:
        """Generate CLI arguments with secrets redacted for safe logging."""
        reg = registry or OptionRegistry.get_default_registry()
        args: list[str] = []
        opts = self.to_options_dict()
        for k, v in opts.items():
            clean_k = k.lstrip("-")
            if reg.is_sensitive(clean_k):
                args.append(f"--{clean_k}=******")
            else:
                args.append(f"--{clean_k}={v}")
        return args

    def generate_conf_content(self, registry: OptionRegistry | None = None) -> str:
        """Generate aria2.conf configuration string."""
        reg = registry or OptionRegistry.get_default_registry()
        opts = self.to_options_dict()
        return reg.serialize_for_config_file(opts)
