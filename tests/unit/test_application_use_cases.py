"""
Unit tests for the application use cases and services.
"""

import tempfile
import unittest
from datetime import datetime, time
from pathlib import Path
from unittest.mock import MagicMock

from shusha.application.services.clipboard_service import (
    is_downloadable_link,
)
from shusha.application.services.post_action_service import PostActionService
from shusha.application.services.scheduler_service import SchedulerService
from shusha.application.services.sync_coordinator import SyncCoordinator
from shusha.application.use_cases.category_use_cases import (
    CategoryDTO,
    CreateCategoryUseCase,
    DeleteCategoryUseCase,
    UpdateCategoryUseCase,
)
from shusha.application.use_cases.download_use_cases import (
    AddDownloadRequest,
    AddDownloadUseCase,
    PauseDownloadUseCase,
    RemoveDownloadUseCase,
    ResumeDownloadUseCase,
)
from shusha.application.use_cases.queue_use_cases import (
    QueueAction,
    ReorderQueueUseCase,
    SetQueueLimitsUseCase,
)
from shusha.domain.category import Category, CategoryRule
from shusha.domain.download import Download
from shusha.domain.download_file import DownloadFile
from shusha.domain.identifiers import CategoryId, DownloadId, Gid
from shusha.domain.scheduler import ScheduleWindow
from shusha.domain.states import DownloadState
from shusha.domain.statistics import GlobalStatistics
from shusha.domain.values import BitRate, ByteSize
from shusha.infrastructure.persistence.database import DatabaseManager
from shusha.infrastructure.persistence.repositories.category_repository import (
    CategoryRepository,
)
from shusha.infrastructure.persistence.repositories.download_repository import (
    DownloadRepository,
)


class TestApplicationUseCases(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test.db"
        self.db_manager = DatabaseManager(self.db_path)
        self.download_repo = DownloadRepository(self.db_manager)
        self.category_repo = CategoryRepository(self.db_manager)
        self.mock_client = MagicMock()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_add_download_use_case_with_category_matching(self):
        # Create category for ISO files
        cat = Category(
            id=CategoryId("iso"),
            name="ISO",
            download_dir="/downloads/iso",
            rule=CategoryRule(extensions=["iso"], host_patterns=[]),
        )
        self.category_repo.save(cat)

        self.mock_client.add_uri.return_value = Gid("2089b05ecca3d829")
        self.mock_client.tell_status.return_value = Download(
            gid=Gid("2089b05ecca3d829"),
            download_id=DownloadId("dl-2089b05ecca3d829"),
            name="ubuntu.iso",
            state=DownloadState.QUEUED,
        )

        use_case = AddDownloadUseCase(
            client=self.mock_client,
            download_repo=self.download_repo,
            category_repo=self.category_repo,
        )

        req = AddDownloadRequest(uris=["https://releases.ubuntu.com/24.04/ubuntu.iso"])
        dl_ids = use_case.execute(req)

        self.assertEqual(len(dl_ids), 1)
        self.mock_client.add_uri.assert_called_once()
        saved = self.download_repo.get_by_id(dl_ids[0])
        self.assertIsNotNone(saved)
        assert saved is not None
        self.assertEqual(saved.category_id, CategoryId("iso"))

    def test_pause_and_resume_download_use_cases(self):
        dl = Download(
            gid=Gid("123"),
            download_id=DownloadId("dl-123"),
            name="file.zip",
            state=DownloadState.ACTIVE,
        )
        self.download_repo.save(dl)

        pause_uc = PauseDownloadUseCase(self.mock_client, self.download_repo)
        pause_uc.execute(DownloadId("dl-123"))
        self.mock_client.pause.assert_called_with(Gid("123"), force=False)
        paused_saved = self.download_repo.get_by_id(DownloadId("dl-123"))
        self.assertIsNotNone(paused_saved)
        assert paused_saved is not None
        self.assertEqual(paused_saved.state, DownloadState.PAUSED)

        resume_uc = ResumeDownloadUseCase(self.mock_client, self.download_repo)
        resume_uc.execute(DownloadId("dl-123"))
        self.mock_client.unpause.assert_called_with(Gid("123"))
        resumed_saved = self.download_repo.get_by_id(DownloadId("dl-123"))
        self.assertIsNotNone(resumed_saved)
        assert resumed_saved is not None
        self.assertEqual(resumed_saved.state, DownloadState.ACTIVE)

    def test_remove_download_use_case_with_file_deletion(self):
        dummy_file = Path(self.temp_dir.name) / "test.bin"
        dummy_file.write_bytes(b"12345")

        dl = Download(
            gid=Gid("123"),
            download_id=DownloadId("dl-123"),
            name="test.bin",
            state=DownloadState.COMPLETED,
            files=[
                DownloadFile(
                    index=1,
                    path=str(dummy_file),
                    length=ByteSize(5),
                    completed_length=ByteSize(5),
                    selected=True,
                    uris=[],
                )
            ],
        )
        self.download_repo.save(dl)

        remove_uc = RemoveDownloadUseCase(self.mock_client, self.download_repo)
        remove_uc.execute(DownloadId("dl-123"), delete_files=True)

        self.assertIsNone(self.download_repo.get_by_id(DownloadId("dl-123")))
        self.assertFalse(dummy_file.exists())

    def test_category_use_cases(self):
        create_uc = CreateCategoryUseCase(self.category_repo)
        cat_id = create_uc.execute(
            CategoryDTO(
                name="Documents",
                download_dir="/downloads/docs",
                extensions=["pdf", "docx"],
                host_patterns=[],
            )
        )
        self.assertEqual(str(cat_id), "documents")

        update_uc = UpdateCategoryUseCase(self.category_repo)
        update_uc.execute(
            cat_id,
            CategoryDTO(
                name="Documents Updated",
                download_dir="/downloads/docs2",
                extensions=["pdf", "epub"],
                host_patterns=[],
            ),
        )
        cat = self.category_repo.get_by_id(cat_id)
        self.assertIsNotNone(cat)
        assert cat is not None
        self.assertEqual(cat.download_dir, "/downloads/docs2")

        delete_uc = DeleteCategoryUseCase(self.category_repo)
        self.assertTrue(delete_uc.execute(cat_id))

    def test_queue_use_cases(self):
        dl = Download(
            gid=Gid("123"),
            download_id=DownloadId("dl-123"),
            name="file.zip",
            state=DownloadState.QUEUED,
        )
        self.download_repo.save(dl)

        reorder_uc = ReorderQueueUseCase(self.mock_client, self.download_repo)
        reorder_uc.execute(DownloadId("dl-123"), QueueAction.TOP)
        self.mock_client.change_position.assert_called_with(Gid("123"), 0, "POS_SET")

        limits_uc = SetQueueLimitsUseCase(self.mock_client)
        limits_uc.execute(max_concurrent_downloads=8, max_download_speed="5M")
        self.mock_client.change_global_option.assert_called_with(
            {
                "max-concurrent-downloads": "8",
                "max-overall-download-limit": "5M",
            }
        )

    def test_scheduler_service(self):
        window = ScheduleWindow(
            day_of_week=-1,
            start_time=time(1, 0),
            end_time=time(5, 0),
            speed_limit=BitRate(1000000),
        )
        service = SchedulerService(client=self.mock_client, windows=[window])

        # Active time (03:00)
        service.evaluate_at(datetime(2026, 8, 29, 3, 0))
        self.mock_client.change_global_option.assert_called_with(
            {
                "max-overall-download-limit": "1000000",
                "max-overall-upload-limit": "1000000",
            }
        )

        # Inactive time (12:00)
        service.evaluate_at(datetime(2026, 8, 29, 12, 0))
        self.mock_client.change_global_option.assert_called_with(
            {
                "max-overall-download-limit": "0",
                "max-overall-upload-limit": "0",
            }
        )

    def test_clipboard_detection(self):
        self.assertTrue(is_downloadable_link("https://example.com/file.zip"))
        self.assertTrue(
            is_downloadable_link(
                "magnet:?xt=urn:btih:0123456789abcdef0123456789abcdef01234567"
            )
        )
        self.assertFalse(is_downloadable_link("random text not a link"))

    def test_post_action_hash_verification(self):
        test_file = Path(self.temp_dir.name) / "sample.txt"
        test_file.write_text("shusha-rocks", encoding="utf-8")

        computed_hash = PostActionService.calculate_file_hash(test_file, "sha256")
        self.assertTrue(
            PostActionService.verify_checksum(test_file, computed_hash, "sha256")
        )
        self.assertFalse(
            PostActionService.verify_checksum(test_file, "wrong-hash", "sha256")
        )

    def test_sync_coordinator(self):
        dl = Download(
            gid=Gid("123"),
            download_id=DownloadId("dl-123"),
            name="file.zip",
            state=DownloadState.ACTIVE,
        )
        self.mock_client.tell_active.return_value = [dl]
        self.mock_client.tell_waiting.return_value = []
        self.mock_client.tell_stopped.return_value = []
        self.mock_client.get_global_stat.return_value = GlobalStatistics(
            download_speed=BitRate(100),
            upload_speed=BitRate(0),
            num_active=1,
            num_waiting=0,
            num_stopped=0,
            num_stopped_total=0,
        )

        coordinator = SyncCoordinator(
            client=self.mock_client, download_repo=self.download_repo
        )
        observed_downloads = []
        coordinator.subscribe_downloads(lambda dls: observed_downloads.extend(dls))

        coordinator.poll_once()
        self.assertEqual(len(observed_downloads), 1)
        self.assertEqual(observed_downloads[0].name, "file.zip")


if __name__ == "__main__":
    unittest.main()
