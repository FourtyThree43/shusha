"""
End-to-End Integration Test Harness: Shusha 2 + Real aria2c Engine + Local HTTP Server.
Exercises the entire use-case pipeline from download submission to cryptographic verification.
"""

import contextlib
import functools
import hashlib
import http.server
import socket
import tempfile
import threading
import time
import unittest
from pathlib import Path

from shusha.application.services.post_action_service import PostActionService
from shusha.application.use_cases.download_use_cases import (
    AddDownloadRequest,
    AddDownloadUseCase,
    PauseDownloadUseCase,
    RemoveDownloadUseCase,
    ResumeDownloadUseCase,
)
from shusha.domain.states import DownloadState
from shusha.infrastructure.aria2.client import Aria2Client
from shusha.infrastructure.aria2.jsonrpc import JsonRpcTransport
from shusha.infrastructure.aria2.option_registry import OptionRegistry
from shusha.infrastructure.daemon.config import DaemonConfig
from shusha.infrastructure.daemon.discovery import find_aria2_executable
from shusha.infrastructure.daemon.manager import DaemonSupervisor
from shusha.infrastructure.persistence.database import DatabaseManager
from shusha.infrastructure.persistence.repositories.category_repository import (
    CategoryRepository,
)
from shusha.infrastructure.persistence.repositories.download_repository import (
    DownloadRepository,
)


def get_free_port() -> int:
    """Find a random available TCP port."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class TestE2ERealAria2(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.aria2_exe = find_aria2_executable()
        if not cls.aria2_exe:
            raise unittest.SkipTest("aria2c executable not found on host machine")

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)

        # 1. Create test payload
        self.payload_data = b"SHUSHA_INTEGRATION_TEST_PAYLOAD_" * 16384  # ~512 KiB
        self.expected_hash = hashlib.sha256(self.payload_data).hexdigest()
        self.served_file = self.temp_path / "test_file.bin"
        self.served_file.write_bytes(self.payload_data)

        # 2. Start local HTTP test server
        self.http_port = get_free_port()
        handler = functools.partial(
            http.server.SimpleHTTPRequestHandler, directory=str(self.temp_path)
        )
        self.httpd = http.server.ThreadingHTTPServer(
            ("127.0.0.1", self.http_port), handler
        )
        self.server_thread = threading.Thread(
            target=self.httpd.serve_forever, daemon=True
        )
        self.server_thread.start()

        # 3. Start isolated aria2c daemon
        self.aria2_port = get_free_port()
        self.secret = "integration_test_secret_43"
        self.download_dest = self.temp_path / "downloads"
        self.download_dest.mkdir()

        self.daemon_config = DaemonConfig(
            host="127.0.0.1",
            port=self.aria2_port,
            secret=self.secret,
            download_dir=self.download_dest,
            session_file=self.temp_path / "session.dat",
            input_file=self.temp_path / "session.dat",
            log_file=self.temp_path / "aria2.log",
        )
        self.supervisor = DaemonSupervisor(
            config=self.daemon_config,
            custom_executable=self.aria2_exe,
            pid_file=self.temp_path / "aria2.pid",
        )
        self.supervisor.start()

        # 4. Wire client and use cases
        rpc_endpoint = f"http://127.0.0.1:{self.aria2_port}/jsonrpc"
        self.transport = JsonRpcTransport(endpoint=rpc_endpoint, secret=self.secret)
        self.registry = OptionRegistry.get_default_registry()
        self.client = Aria2Client(transport=self.transport, registry=self.registry)

        self.db_manager = DatabaseManager(self.temp_path / "test.db")
        self.download_repo = DownloadRepository(self.db_manager)
        self.category_repo = CategoryRepository(self.db_manager)

        self.add_uc = AddDownloadUseCase(
            self.client,
            self.download_repo,
            self.category_repo,
            default_dir=self.download_dest,
        )
        self.pause_uc = PauseDownloadUseCase(self.client, self.download_repo)
        self.resume_uc = ResumeDownloadUseCase(self.client, self.download_repo)
        self.remove_uc = RemoveDownloadUseCase(self.client, self.download_repo)

    def tearDown(self):
        with contextlib.suppress(Exception):
            self.supervisor.stop()
        self.httpd.shutdown()
        self.temp_dir.cleanup()

    def test_full_download_lifecycle(self):
        # 1. Check daemon health
        health = self.supervisor.get_health()
        self.assertEqual(health.status.value, "HEALTHY")

        # 2. Add download
        file_url = f"http://127.0.0.1:{self.http_port}/test_file.bin"
        download_ids = self.add_uc.execute(AddDownloadRequest(uris=[file_url]))
        self.assertEqual(len(download_ids), 1)
        dl_id = download_ids[0]

        # 3. Poll until completed (timeout 15s)
        completed = False
        start_time = time.time()
        dl_record = self.download_repo.get_by_id(dl_id)
        self.assertIsNotNone(dl_record)
        assert dl_record is not None

        while time.time() - start_time < 15.0:
            status = self.client.tell_status(dl_record.gid)
            if status.state in (DownloadState.COMPLETED, DownloadState.REMOVED):
                completed = True
                break
            time.sleep(0.1)

        self.assertTrue(completed, "Download did not finish within timeout")

        # 4. Verify downloaded file integrity on disk
        target_path = self.download_dest / "test_file.bin"
        self.assertTrue(target_path.exists())
        self.assertEqual(target_path.stat().st_size, len(self.payload_data))

        # 5. Checksum verification service
        is_valid = PostActionService.verify_checksum(
            file_path=target_path,
            expected_hash=self.expected_hash,
            algorithm="sha256",
        )
        self.assertTrue(is_valid, "Downloaded payload hash mismatch!")

        # 6. Remove download
        self.remove_uc.execute(dl_id, delete_files=True)
        self.assertFalse(
            target_path.exists(), "Target file should have been removed from disk"
        )


if __name__ == "__main__":
    unittest.main()
