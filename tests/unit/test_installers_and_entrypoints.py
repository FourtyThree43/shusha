"""Unit tests for browser host installer, CLI flags, and entry points (Epic E18)."""

from __future__ import annotations

import io
from unittest.mock import patch

from shusha.infrastructure.os_integration.browser_host_installer import (
    build_chrome_manifest,
    build_firefox_manifest,
    get_manifest_directories,
    get_native_host_executable,
    install_native_messaging_manifests,
)
from shusha.interfaces.cli.main import main as cli_main
from shusha.interfaces.cli.parser import build_parser


class TestBrowserHostInstaller:
    """Tests for WebExtensions Native Messaging Host installer."""

    def test_build_manifests(self) -> None:
        host_path = "/usr/bin/shusha-host"
        chrome_manifest = build_chrome_manifest(host_path)
        assert chrome_manifest["name"] == "com.fourtythree43.shusha"
        assert chrome_manifest["path"] == host_path
        assert "allowed_origins" in chrome_manifest

        firefox_manifest = build_firefox_manifest(host_path)
        assert firefox_manifest["name"] == "com.fourtythree43.shusha"
        assert firefox_manifest["path"] == host_path
        assert "allowed_extensions" in firefox_manifest

    def test_get_native_host_executable(self) -> None:
        exe = get_native_host_executable()
        assert exe is not None
        assert len(exe) > 0

    def test_get_manifest_directories(self) -> None:
        dirs = get_manifest_directories()
        assert len(dirs) >= 1
        for name, path in dirs:
            assert isinstance(name, str)
            assert path is not None

    def test_install_dry_run(self) -> None:
        results = install_native_messaging_manifests(dry_run=True)
        assert len(results) >= 1
        assert any("[DRY-RUN]" in r for r in results)


class TestCliEntrypointsAndFlags:
    """Tests for top-level CLI flags and subcommands."""

    def test_parser_gui_and_tui_flags(self) -> None:
        parser = build_parser()

        args_gui = parser.parse_args(["--gui"])
        assert args_gui.gui is True

        args_tui = parser.parse_args(["--tui"])
        assert args_tui.tui is True

        args_host = parser.parse_args(["install-host", "--dry-run"])
        assert args_host.command == "install-host"
        assert args_host.dry_run is True

        args_update = parser.parse_args(["update"])
        assert args_update.command == "update"

    def test_cli_install_host_dry_run_execution(self) -> None:
        out = io.StringIO()
        with patch("sys.stdout", out):
            cli_main(["install-host", "--dry-run"])
        output = out.getvalue()
        assert "[DRY-RUN]" in output

    def test_cli_update_execution(self) -> None:
        out = io.StringIO()
        with patch("sys.stdout", out):
            cli_main(["update"])
        output = out.getvalue()
        assert "curl" in output or "install.sh" in output or "version" in output

    def test_display_availability_detection(self) -> None:
        from shusha.interfaces.cli.dispatcher import is_display_available

        with (
            patch("platform.system", return_value="Linux"),
            patch.dict("os.environ", {"DISPLAY": ":0"}),
        ):
            assert is_display_available() is True

        with (
            patch("platform.system", return_value="Linux"),
            patch.dict("os.environ", {}, clear=True),
        ):
            assert is_display_available() is False

    def test_bare_invocation_launches_gui_when_display_available(self) -> None:
        from shusha.interfaces.cli.dispatcher import handle_cli

        parser = build_parser()
        args = parser.parse_args([])

        with (
            patch(
                "shusha.interfaces.cli.dispatcher.is_display_available",
                return_value=True,
            ),
            patch("shusha.interfaces.cli.dispatcher.run_gui") as mock_gui,
        ):
            res = handle_cli(args)
            assert res == 0
            assert mock_gui.called

    def test_bare_invocation_launches_tui_when_headless(self) -> None:
        from shusha.interfaces.cli.dispatcher import handle_cli

        parser = build_parser()
        args = parser.parse_args([])

        with (
            patch(
                "shusha.interfaces.cli.dispatcher.is_display_available",
                return_value=False,
            ),
            patch("shusha.interfaces.tui.ShushaTUIApp.run") as mock_tui,
        ):
            res = handle_cli(args)
            assert res == 0
            assert mock_tui.called
