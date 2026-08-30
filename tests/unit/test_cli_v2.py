"""
Comprehensive unit and integration tests for Shusha CLI (Epic E13).
Verifies CommandBus & QueryBus dispatch, exit codes, and JSON/JSONL output stability.
"""

from __future__ import annotations

import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from shusha.acquisition.detector import AcquisitionDetector
from shusha.acquisition.inspector import AcquisitionInspector
from shusha.acquisition.resolver import AcquisitionResolver
from shusha.application.command_bus import CommandBus
from shusha.application.commands import (
    PauseJobCommand,
)
from shusha.application.queries import (
    ListJobsQuery,
)
from shusha.application.query_bus import QueryBus
from shusha.backends.contract import (
    BackendDiagnostics,
    BackendIdentity,
    BackendProtocol,
)
from shusha.domain.capability import Capability, CapabilitySet
from shusha.domain.errors import DownloadNotFoundError
from shusha.domain.identifiers import (
    JobId,
    make_backend_id,
    make_category_id,
)
from shusha.domain.job import Job, JobProgress
from shusha.domain.states import DownloadState
from shusha.domain.values import BitRate, ByteSize, Duration
from shusha.interfaces.cli.context import CliContext, build_cli_context
from shusha.interfaces.cli.dispatcher import handle_cli
from shusha.interfaces.cli.parser import build_parser


class FakeTestBackend(BackendProtocol):
    """Fake backend implementation for CLI tests."""

    def __init__(self, backend_id: str = "fake") -> None:
        self._identity = BackendIdentity(
            id=make_backend_id(backend_id),
            name="Fake CLI Backend",
            version="1.0.0",
        )
        self._capabilities = CapabilitySet.from_iterable(
            [Capability.HTTP, Capability.BASIC_DOWNLOAD]
        )

    @property
    def identity(self) -> BackendIdentity:
        return self._identity

    @property
    def capabilities(self) -> CapabilitySet:
        return self._capabilities

    def initialize(self, config: dict | None = None) -> None:
        pass

    def shutdown(self) -> None:
        pass

    def ping(self) -> bool:
        return True

    def submit_job(self, job: Job) -> Job:
        return job

    def pause_job(self, job_id: JobId) -> Job:
        raise NotImplementedError

    def resume_job(self, job_id: JobId) -> Job:
        raise NotImplementedError

    def cancel_job(self, job_id: JobId) -> Job:
        raise NotImplementedError

    def remove_job(self, job_id: JobId, delete_files: bool = False) -> None:
        pass

    def get_job_status(self, job_id: JobId) -> Job:
        raise NotImplementedError

    def get_diagnostics(self) -> BackendDiagnostics:
        return BackendDiagnostics(
            healthy=True,
            uptime_seconds=123.4,
            active_jobs=1,
            details={"engine": "fake"},
        )

    def get_supported_options(self) -> list:
        return []


class TestCliV2(unittest.TestCase):
    """Test suite for Epic E13 CLI framework, commands, formats, and dispatch."""

    def setUp(self) -> None:
        self.parser = build_parser()
        self.cli_ctx = build_cli_context()
        self.lifecycle_service = self.cli_ctx.lifecycle_service
        self.backend_registry = self.cli_ctx.backend_registry
        self.fake_backend = FakeTestBackend("aria2")
        self.backend_registry.register(self.fake_backend, default=True)

        # Pre-populate sample jobs for testing
        self.job1 = self.lifecycle_service.create_job(
            name="ubuntu-24.04.iso",
            source_input="https://releases.ubuntu.com/24.04/ubuntu.iso",
            backend_id=make_backend_id("aria2"),
            category_id=make_category_id("iso"),
        )
        self.lifecycle_service.start_job(self.job1.id)
        self.lifecycle_service.update_progress(
            self.job1.id,
            JobProgress(
                total_length=ByteSize(2 * 1024 * 1024 * 1024),  # 2 GiB
                completed_length=ByteSize(1024 * 1024 * 1024),  # 1 GiB
                download_speed=BitRate(10 * 1024 * 1024),  # 10 MB/s
                upload_speed=BitRate(0),
                eta=Duration(100),
            ),
        )

        self.job2 = self.lifecycle_service.create_job(
            name="document.pdf",
            source_input="https://example.com/document.pdf",
            backend_id=make_backend_id("aria2"),
            category_id=make_category_id("docs"),
        )
        self.lifecycle_service.pause_job(self.job2.id)

    # --- 1. Parser and Top-Level Flags ---

    def test_version_and_help(self) -> None:
        with self.assertRaises(SystemExit) as cm:
            self.parser.parse_args(["--version"])
        self.assertEqual(cm.exception.code, 0)

        with self.assertRaises(SystemExit) as cm:
            self.parser.parse_args(["--help"])
        self.assertEqual(cm.exception.code, 0)

    # --- 2. Add Command (E13-I02) ---

    def test_add_single_uri(self) -> None:
        args = self.parser.parse_args(["add", "https://example.com/test.zip"])
        with patch("sys.stdout", new_callable=io.StringIO) as mock_out:
            code = handle_cli(args, cli_context=self.cli_ctx)
            self.assertEqual(code, 0)
            self.assertIn("✔ Added download:", mock_out.getvalue())

    def test_add_multiple_uris(self) -> None:
        args = self.parser.parse_args(
            ["add", "https://example.com/a.zip", "https://example.com/b.zip", "--json"]
        )
        with patch("sys.stdout", new_callable=io.StringIO) as mock_out:
            code = handle_cli(args, cli_context=self.cli_ctx)
            self.assertEqual(code, 0)
            data = json.loads(mock_out.getvalue())
            self.assertIsInstance(data, list)
            self.assertEqual(len(data), 2)
            self.assertEqual(data[0]["status"], "queued")
            self.assertEqual(data[1]["status"], "queued")

    def test_add_with_options(self) -> None:
        args = self.parser.parse_args(
            [
                "add",
                "https://example.com/archive.tar.gz",
                "--dir",
                "/tmp/downloads",
                "--category",
                "archives",
                "--backend",
                "aria2",
                "--name",
                "my_custom_archive",
                "--split",
                "8",
                "--jsonl",
            ]
        )
        with patch("sys.stdout", new_callable=io.StringIO) as mock_out:
            code = handle_cli(args, cli_context=self.cli_ctx)
            self.assertEqual(code, 0)
            line = mock_out.getvalue().strip()
            item = json.loads(line)
            self.assertIn("id", item)
            self.assertEqual(item.get("name"), "my_custom_archive")

    def test_add_no_arguments_error(self) -> None:
        args = self.parser.parse_args(["add"])
        with (
            patch("sys.stderr", new_callable=io.StringIO) as mock_err,
            patch("sys.stdout", new_callable=io.StringIO),
        ):
            code = handle_cli(args, cli_context=self.cli_ctx)
            self.assertEqual(code, 1)
            self.assertIn("Error:", mock_err.getvalue())

    # --- 3. List Command (E13-I02, E13-I04) ---

    def test_list_tabular(self) -> None:
        args = self.parser.parse_args(["list"])
        with patch("sys.stdout", new_callable=io.StringIO) as mock_out:
            code = handle_cli(args, cli_context=self.cli_ctx)
            self.assertEqual(code, 0)
            out = mock_out.getvalue()
            self.assertIn("ID", out)
            self.assertIn("NAME", out)
            self.assertIn("STATE", out)
            self.assertIn("ubuntu-24.04.iso", out)
            self.assertIn("document.pdf", out)

    def test_list_filtered_by_state(self) -> None:
        args = self.parser.parse_args(["list", "--state", "active", "--json"])
        with patch("sys.stdout", new_callable=io.StringIO) as mock_out:
            code = handle_cli(args, cli_context=self.cli_ctx)
            self.assertEqual(code, 0)
            data = json.loads(mock_out.getvalue())
            self.assertEqual(len(data), 1)
            self.assertEqual(data[0]["name"], "ubuntu-24.04.iso")
            self.assertEqual(data[0]["state"], "ACTIVE")

    def test_list_json_stability(self) -> None:
        args = self.parser.parse_args(["list", "--json"])
        with patch("sys.stdout", new_callable=io.StringIO) as mock_out:
            code = handle_cli(args, cli_context=self.cli_ctx)
            self.assertEqual(code, 0)
            data = json.loads(mock_out.getvalue())
            self.assertIsInstance(data, list)
            self.assertEqual(len(data), 2)
            first = data[0]
            # Verify stable schema keys
            required_keys = {
                "id",
                "name",
                "state",
                "backend_id",
                "progress",
                "completed_bytes",
                "total_bytes",
                "download_speed",
            }
            for k in required_keys:
                self.assertIn(k, first)

    def test_list_jsonl_streaming(self) -> None:
        args = self.parser.parse_args(["list", "--jsonl"])
        with patch("sys.stdout", new_callable=io.StringIO) as mock_out:
            code = handle_cli(args, cli_context=self.cli_ctx)
            self.assertEqual(code, 0)
            lines = [line for line in mock_out.getvalue().splitlines() if line.strip()]
            self.assertEqual(len(lines), 2)
            for line in lines:
                parsed = json.loads(line)
                self.assertIn("id", parsed)
                self.assertIn("name", parsed)

    # --- 4. Status Command (E13-I02) ---

    def test_status_single_job_tabular(self) -> None:
        args = self.parser.parse_args(["status", str(self.job1.id)])
        with patch("sys.stdout", new_callable=io.StringIO) as mock_out:
            code = handle_cli(args, cli_context=self.cli_ctx)
            self.assertEqual(code, 0)
            out = mock_out.getvalue()
            self.assertIn(f"Job ID:          {self.job1.id}", out)
            self.assertIn("Name:            ubuntu-24.04.iso", out)
            self.assertIn("State:           ACTIVE", out)
            self.assertIn("50.0%", out)

    def test_status_single_job_json(self) -> None:
        args = self.parser.parse_args(["status", str(self.job1.id), "--json"])
        with patch("sys.stdout", new_callable=io.StringIO) as mock_out:
            code = handle_cli(args, cli_context=self.cli_ctx)
            self.assertEqual(code, 0)
            data = json.loads(mock_out.getvalue())
            self.assertEqual(data["id"], str(self.job1.id))
            self.assertEqual(data["name"], "ubuntu-24.04.iso")
            self.assertEqual(data["state"], "ACTIVE")
            self.assertAlmostEqual(data["progress"], 50.0)

    def test_status_not_found_error(self) -> None:
        args = self.parser.parse_args(["status", "job-nonexistent-id"])
        with (
            patch("sys.stderr", new_callable=io.StringIO) as mock_err,
            patch("sys.stdout", new_callable=io.StringIO),
        ):
            code = handle_cli(args, cli_context=self.cli_ctx)
            self.assertEqual(code, 1)
            self.assertIn(
                "Downloads not found: job-nonexistent-id", mock_err.getvalue()
            )

    # --- 5. Pause, Resume, Cancel, Remove, Retry (E13-I02) ---

    def test_pause_and_resume_job(self) -> None:
        # Pause job 1
        args_pause = self.parser.parse_args(["pause", str(self.job1.id), "--json"])
        with patch("sys.stdout", new_callable=io.StringIO) as mock_out:
            code = handle_cli(args_pause, cli_context=self.cli_ctx)
            self.assertEqual(code, 0)
            res = json.loads(mock_out.getvalue())
            self.assertEqual(res[0]["status"], "paused")

        updated_job = self.lifecycle_service.get_job(self.job1.id)
        self.assertEqual(updated_job.state, DownloadState.PAUSED)

        # Resume job 1
        args_resume = self.parser.parse_args(["resume", str(self.job1.id), "--json"])
        with patch("sys.stdout", new_callable=io.StringIO) as mock_out:
            code = handle_cli(args_resume, cli_context=self.cli_ctx)
            self.assertEqual(code, 0)
            res = json.loads(mock_out.getvalue())
            self.assertEqual(res[0]["status"], "resumed")

        updated_job = self.lifecycle_service.get_job(self.job1.id)
        self.assertEqual(updated_job.state, DownloadState.ACTIVE)

    def test_cancel_job(self) -> None:
        args_cancel = self.parser.parse_args(["cancel", str(self.job1.id), "--json"])
        with patch("sys.stdout", new_callable=io.StringIO) as mock_out:
            code = handle_cli(args_cancel, cli_context=self.cli_ctx)
            self.assertEqual(code, 0)
            res = json.loads(mock_out.getvalue())
            self.assertEqual(res[0]["status"], "cancelled")

        updated_job = self.lifecycle_service.get_job(self.job1.id)
        self.assertEqual(updated_job.state, DownloadState.REMOVED)

    def test_retry_job(self) -> None:
        # First cancel job
        self.lifecycle_service.cancel_job(self.job1.id)
        # Now retry
        args_retry = self.parser.parse_args(["retry", str(self.job1.id), "--json"])
        with patch("sys.stdout", new_callable=io.StringIO) as mock_out:
            code = handle_cli(args_retry, cli_context=self.cli_ctx)
            self.assertEqual(code, 0)
            res = json.loads(mock_out.getvalue())
            self.assertEqual(res[0]["status"], "retried")

        updated_job = self.lifecycle_service.get_job(self.job1.id)
        self.assertEqual(updated_job.state, DownloadState.QUEUED)

    def test_remove_job(self) -> None:
        args_remove = self.parser.parse_args(
            ["remove", str(self.job2.id), "--files", "--json"]
        )
        with patch("sys.stdout", new_callable=io.StringIO) as mock_out:
            code = handle_cli(args_remove, cli_context=self.cli_ctx)
            self.assertEqual(code, 0)
            res = json.loads(mock_out.getvalue())
            self.assertEqual(res[0]["status"], "removed")
            self.assertTrue(res[0]["deleted_files"])

        with self.assertRaises(DownloadNotFoundError):
            self.lifecycle_service.get_job(self.job2.id)

    # --- 6. Resolution without Immediate Execution (E13-I03) ---

    def test_resolve_url_inspection_no_execution(self) -> None:
        initial_job_count = len(self.lifecycle_service.list_jobs())

        url = "https://example.com/downloads/setup.exe?utm_source=test"
        args = self.parser.parse_args(["resolve", url])
        with patch("sys.stdout", new_callable=io.StringIO) as mock_out:
            code = handle_cli(args, cli_context=self.cli_ctx)
            self.assertEqual(code, 0)
            out = mock_out.getvalue()
            self.assertIn("Original Input:", out)
            self.assertIn("Canonical Target:", out)
            self.assertIn("Detected Kind:", out)
            self.assertIn("Candidate Backends:", out)
            self.assertIn("direct_url", out.lower())

        # Verify NO new download job was started or added to lifecycle service
        final_job_count = len(self.lifecycle_service.list_jobs())
        self.assertEqual(initial_job_count, final_job_count)

    def test_resolve_json_output(self) -> None:
        url = (
            "magnet:?xt=urn:btih:da39a3ee5e6b4b0d3255bfef95601890afd80709&dn=sample.iso"
        )
        args = self.parser.parse_args(["resolve", url, "--json"])
        with patch("sys.stdout", new_callable=io.StringIO) as mock_out:
            code = handle_cli(args, cli_context=self.cli_ctx)
            self.assertEqual(code, 0)
            data = json.loads(mock_out.getvalue())
            self.assertEqual(data["detected_kind"], "magnet_uri")
            self.assertEqual(data["original_input"], url)
            self.assertTrue(data["is_resolved"])
            self.assertIn("aria2", data["candidate_backends"])

    def test_resolve_jsonl_output(self) -> None:
        url = "https://example.com/playlist.m3u8"
        args = self.parser.parse_args(["resolve", url, "--jsonl"])
        with patch("sys.stdout", new_callable=io.StringIO) as mock_out:
            code = handle_cli(args, cli_context=self.cli_ctx)
            self.assertEqual(code, 0)
            line = mock_out.getvalue().strip()
            data = json.loads(line)
            self.assertEqual(data["detected_kind"], "media_stream")

    # --- 7. Diagnostics / Doctor (E13-I05) ---

    def test_doctor_and_diagnostics_subcommands(self) -> None:
        # 1. doctor human
        args_doc = self.parser.parse_args(["doctor"])
        with patch("sys.stdout", new_callable=io.StringIO) as mock_out:
            code = handle_cli(args_doc, cli_context=self.cli_ctx)
            self.assertEqual(code, 0)
            self.assertIn("System Diagnostics", mock_out.getvalue())

        # 2. diagnostics alias with JSON output
        args_diag = self.parser.parse_args(["diagnostics", "--json"])
        with patch("sys.stdout", new_callable=io.StringIO) as mock_out:
            code = handle_cli(args_diag, cli_context=self.cli_ctx)
            self.assertEqual(code, 0)
            report = json.loads(mock_out.getvalue())
            self.assertIn("system", report)
            self.assertIn("shusha_version", report)
            self.assertIn("backends", report)
            self.assertIn("aria2", report["backends"])
            self.assertTrue(report["backends"]["aria2"]["healthy"])

    # --- 8. Hash Calculation Subcommand ---

    def test_hash_subcommand(self) -> None:
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"Shusha 2 Hash Test Data")
            f_path = Path(f.name)

        try:
            # Table format
            args = self.parser.parse_args(["hash", str(f_path)])
            with patch("sys.stdout", new_callable=io.StringIO) as mock_out:
                code = handle_cli(args, cli_context=self.cli_ctx)
                self.assertEqual(code, 0)
                self.assertIn("MD5:", mock_out.getvalue())
                self.assertIn("SHA256:", mock_out.getvalue())

            # JSON format
            args_json = self.parser.parse_args(["hash", str(f_path), "--json"])
            with patch("sys.stdout", new_callable=io.StringIO) as mock_out:
                code = handle_cli(args_json, cli_context=self.cli_ctx)
                self.assertEqual(code, 0)
                hashes = json.loads(mock_out.getvalue())
                self.assertIn("md5", hashes)
                self.assertIn("sha1", hashes)
                self.assertIn("sha256", hashes)
        finally:
            f_path.unlink(missing_ok=True)

    # --- 9. CommandBus / QueryBus Routing Check (RULE-022) ---

    def test_bus_routing_architecture(self) -> None:
        mock_cmd_bus = MagicMock(spec=CommandBus)
        mock_query_bus = MagicMock(spec=QueryBus)

        mock_query_bus.dispatch.return_value = [self.job1]
        mock_cmd_bus.dispatch.return_value = self.job1

        ctx = CliContext(
            command_bus=mock_cmd_bus,
            query_bus=mock_query_bus,
            event_bus=self.cli_ctx.event_bus,
            lifecycle_service=self.lifecycle_service,
            backend_registry=self.backend_registry,
            detector=AcquisitionDetector(),
            inspector=AcquisitionInspector(),
            resolver=AcquisitionResolver(),
        )

        # 1. list routes to QueryBus.dispatch(ListJobsQuery)
        args_list = self.parser.parse_args(["list"])
        handle_cli(args_list, cli_context=ctx)
        mock_query_bus.dispatch.assert_called_once()
        self.assertIsInstance(mock_query_bus.dispatch.call_args[0][0], ListJobsQuery)

        # 2. pause routes to CommandBus.dispatch(PauseJobCommand)
        args_pause = self.parser.parse_args(["pause", "job-101"])
        handle_cli(args_pause, cli_context=ctx)
        mock_cmd_bus.dispatch.assert_called_once()
        self.assertIsInstance(mock_cmd_bus.dispatch.call_args[0][0], PauseJobCommand)


if __name__ == "__main__":
    unittest.main()
