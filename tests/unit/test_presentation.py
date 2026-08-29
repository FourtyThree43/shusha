"""
Unit and headless smoke tests for presentation components and dispatcher.
"""

import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import MagicMock

from shusha.application.services.sync_coordinator import SyncCoordinator
from shusha.application.use_cases.category_use_cases import (
    AssignCategoryUseCase,
    CreateCategoryUseCase,
    DeleteCategoryUseCase,
    UpdateCategoryUseCase,
)
from shusha.application.use_cases.download_use_cases import (
    AddDownloadUseCase,
    ChangeDownloadOptionsUseCase,
    InspectDownloadUseCase,
    PauseDownloadUseCase,
    RemoveDownloadUseCase,
    ResumeDownloadUseCase,
)
from shusha.application.use_cases.queue_use_cases import (
    ReorderQueueUseCase,
    SetQueueLimitsUseCase,
)
from shusha.domain.download import Download
from shusha.domain.identifiers import DownloadId, Gid
from shusha.domain.states import DownloadState
from shusha.domain.values import BitRate, ByteSize
from shusha.infrastructure.aria2.client import Aria2Client
from shusha.infrastructure.configuration.settings_store import SettingsStore
from shusha.infrastructure.daemon.manager import DaemonSupervisor
from shusha.infrastructure.persistence.database import DatabaseManager
from shusha.infrastructure.persistence.repositories.category_repository import (
    CategoryRepository,
)
from shusha.infrastructure.persistence.repositories.download_repository import (
    DownloadRepository,
)
from shusha.presentation.app_context import AppContext
from shusha.presentation.dispatcher import UiDispatcher


class TestPresentation(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "ui_test.db"
        self.db_manager = DatabaseManager(self.db_path)
        self.download_repo = DownloadRepository(self.db_manager)
        self.category_repo = CategoryRepository(self.db_manager)
        self.settings_store = SettingsStore(self.db_manager)
        self.mock_client = MagicMock(spec=Aria2Client)
        self.mock_daemon = MagicMock(spec=DaemonSupervisor)
        self.sync_coordinator = SyncCoordinator(self.mock_client, self.download_repo)

        self.ctx = AppContext(
            client=self.mock_client,
            daemon_supervisor=self.mock_daemon,
            download_repo=self.download_repo,
            category_repo=self.category_repo,
            settings_store=self.settings_store,
            sync_coordinator=self.sync_coordinator,
            add_download_uc=AddDownloadUseCase(
                self.mock_client, self.download_repo, self.category_repo
            ),
            pause_download_uc=PauseDownloadUseCase(
                self.mock_client, self.download_repo
            ),
            resume_download_uc=ResumeDownloadUseCase(
                self.mock_client, self.download_repo
            ),
            remove_download_uc=RemoveDownloadUseCase(
                self.mock_client, self.download_repo
            ),
            inspect_download_uc=InspectDownloadUseCase(
                self.mock_client, self.download_repo
            ),
            change_options_uc=ChangeDownloadOptionsUseCase(
                self.mock_client, self.download_repo
            ),
            create_category_uc=CreateCategoryUseCase(self.category_repo),
            update_category_uc=UpdateCategoryUseCase(self.category_repo),
            delete_category_uc=DeleteCategoryUseCase(self.category_repo),
            assign_category_uc=AssignCategoryUseCase(
                self.download_repo, self.category_repo
            ),
            reorder_queue_uc=ReorderQueueUseCase(self.mock_client, self.download_repo),
            set_queue_limits_uc=SetQueueLimitsUseCase(self.mock_client),
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_app_context_initialization(self):
        self.assertIsNotNone(self.ctx.client)
        self.assertIsNotNone(self.ctx.add_download_uc)
        self.assertIsNotNone(self.ctx.sync_coordinator)

    def test_ui_dispatcher_run_in_background(self):
        mock_root = MagicMock()
        dispatcher = UiDispatcher(mock_root)

        result_container = []

        def task():
            time.sleep(0.05)
            return "done"

        def on_success(res):
            result_container.append(res)

        dispatcher.run_in_background(task, on_success=on_success)
        time.sleep(0.1)

        # Ensure root.after was called to dispatch on_success
        self.assertTrue(mock_root.after.called)

    def test_domain_to_presentation_formatting(self):
        dl = Download(
            gid=Gid("2089b05ecca3d829"),
            download_id=DownloadId("dl-1"),
            name="debian.iso",
            state=DownloadState.ACTIVE,
            completed_length=ByteSize(500 * 1024 * 1024),
            total_length=ByteSize(1000 * 1024 * 1024),
            download_speed=BitRate(10 * 1024 * 1024),
        )

        self.assertEqual(dl.progress.human_readable(), "50.0%")
        self.assertEqual(dl.download_speed.human_readable(), "10.00 MiB/s")
        self.assertEqual(dl.state.value, "ACTIVE")


if __name__ == "__main__":
    unittest.main()
