"""
Unit and integration tests for Shusha 2 persistence, repositories, and secrets.
"""

import stat
import tempfile
import unittest
from pathlib import Path

from shusha.domain.category import Category, CategoryRule
from shusha.domain.download import Download
from shusha.domain.download_file import DownloadFile
from shusha.domain.download_source import DownloadSource, SourceStatus
from shusha.domain.identifiers import CategoryId, DownloadId, Gid
from shusha.domain.states import DownloadState
from shusha.domain.values import BitRate, ByteSize, Uri
from shusha.infrastructure.configuration.settings_store import (
    SettingsStore,
)
from shusha.infrastructure.persistence.database import DatabaseManager
from shusha.infrastructure.persistence.repositories.category_repository import (
    CategoryRepository,
)
from shusha.infrastructure.persistence.repositories.download_repository import (
    DownloadRepository,
)
from shusha.security.redaction import (
    redact_dict_secrets,
    redact_string_secrets,
    redact_url_credentials,
)
from shusha.security.secrets import SecretStore


class TestPersistenceAndRepositories(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_shusha.db"
        self.db_manager = DatabaseManager(self.db_path)
        self.download_repo = DownloadRepository(self.db_manager)
        self.category_repo = CategoryRepository(self.db_manager)
        self.settings_store = SettingsStore(self.db_manager)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_database_permissions(self):
        with self.db_manager.session():
            pass
        file_stat = self.db_path.stat()
        # Ensure only owner read/write (0600)
        mode = stat.S_IMODE(file_stat.st_mode)
        self.assertEqual(mode, 0o600)

    def test_category_repository_crud(self):
        cat = Category(
            id=CategoryId("iso-images"),
            name="ISO Images",
            download_dir="/downloads/iso",
            rule=CategoryRule(extensions=["iso", "img"], host_patterns=["distro.org"]),
            icon_name="disc",
        )
        self.category_repo.save(cat)

        fetched = self.category_repo.get_by_id(CategoryId("iso-images"))
        self.assertIsNotNone(fetched)
        assert fetched is not None
        self.assertEqual(fetched.name, "ISO Images")
        self.assertEqual(fetched.rule.extensions, ["iso", "img"])

        all_cats = self.category_repo.list_all()
        self.assertEqual(len(all_cats), 1)

        deleted = self.category_repo.delete(CategoryId("iso-images"))
        self.assertTrue(deleted)
        self.assertIsNone(self.category_repo.get_by_id(CategoryId("iso-images")))

    def test_download_repository_crud(self):
        cat = Category(
            id=CategoryId("videos"),
            name="Videos",
            download_dir="/downloads/videos",
            rule=CategoryRule(extensions=["mp4", "mkv"], host_patterns=[]),
        )
        self.category_repo.save(cat)

        source = DownloadSource(
            Uri.parse("https://example.com/video.mp4"), SourceStatus.USED
        )
        df = DownloadFile(
            index=1,
            path="/downloads/videos/video.mp4",
            length=ByteSize(50000000),
            completed_length=ByteSize(25000000),
            selected=True,
            uris=[source],
        )

        dl = Download(
            gid=Gid("2089b05ecca3d829"),
            download_id=DownloadId("dl-video-1"),
            name="video.mp4",
            state=DownloadState.ACTIVE,
            total_length=ByteSize(50000000),
            completed_length=ByteSize(25000000),
            download_speed=BitRate(1048576),
            upload_speed=BitRate(0),
            eta=None,
            files=[df],
            sources=[source],
            category_id=CategoryId("videos"),
            dir_path="/downloads/videos",
        )

        self.download_repo.save(dl)

        fetched = self.download_repo.get_by_id(DownloadId("dl-video-1"))
        self.assertIsNotNone(fetched)
        assert fetched is not None
        self.assertEqual(fetched.name, "video.mp4")
        self.assertEqual(fetched.state, DownloadState.ACTIVE)
        self.assertEqual(fetched.completed_length.bytes, 25000000)
        self.assertEqual(len(fetched.files), 1)
        self.assertEqual(len(fetched.sources), 1)
        self.assertEqual(fetched.category_id, CategoryId("videos"))

        # Gid lookup
        by_gid = self.download_repo.get_by_gid(Gid("2089b05ecca3d829"))
        self.assertIsNotNone(by_gid)

        # Filtering
        active_list = self.download_repo.list_by_state(DownloadState.ACTIVE)
        self.assertEqual(len(active_list), 1)
        stopped_list = self.download_repo.list_by_state(DownloadState.COMPLETED)
        self.assertEqual(len(stopped_list), 0)

        # Category filter
        cat_list = self.download_repo.list_by_category(CategoryId("videos"))
        self.assertEqual(len(cat_list), 1)

        # Search
        search_res = self.download_repo.search("video")
        self.assertEqual(len(search_res), 1)

        # Delete
        self.assertTrue(self.download_repo.delete(DownloadId("dl-video-1")))
        self.assertIsNone(self.download_repo.get_by_id(DownloadId("dl-video-1")))

    def test_settings_store(self):
        settings = self.settings_store.load_settings()
        self.assertEqual(settings.theme, "darkly")

        settings.theme = "cosmo"
        settings.max_active_downloads = 10
        self.settings_store.save_settings(settings)

        reloaded = self.settings_store.load_settings()
        self.assertEqual(reloaded.theme, "cosmo")
        self.assertEqual(reloaded.max_active_downloads, 10)


class TestSecurityAndRedaction(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.secret_path = Path(self.temp_dir.name) / "secrets.json"
        self.secret_store = SecretStore(self.secret_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_secret_store(self):
        secret = self.secret_store.get_or_generate_rpc_secret()
        self.assertGreater(len(secret), 20)

        retrieved = self.secret_store.get("aria2_rpc_secret")
        self.assertEqual(secret, retrieved)

        # File permissions check
        file_stat = self.secret_path.stat()
        mode = stat.S_IMODE(file_stat.st_mode)
        self.assertEqual(mode, 0o600)

    def test_url_redaction(self):
        url = "http://alice:supersecretpass@192.168.1.1:6800/jsonrpc"
        redacted = redact_url_credentials(url)
        self.assertNotIn("supersecretpass", redacted)
        self.assertIn("alice:******@", redacted)

    def test_string_secret_redaction(self):
        cmd = "aria2c --rpc-secret=mysecret123 --dir=/downloads"
        redacted = redact_string_secrets(cmd, known_secrets=["mysecret123"])
        self.assertNotIn("mysecret123", redacted)
        self.assertIn("--rpc-secret=******", redacted)

    def test_dict_secret_redaction(self):
        data = {
            "name": "Fedora",
            "rpc_secret": "mysecret",
            "proxy": {"http_passwd": "pass123", "host": "10.0.0.1"},
            "sources": ["http://user:secret@example.com/file.zip"],
        }
        redacted = redact_dict_secrets(data)
        self.assertEqual(redacted["rpc_secret"], "******")
        self.assertEqual(redacted["proxy"]["http_passwd"], "******")
        self.assertNotIn("secret", redacted["sources"][0])


if __name__ == "__main__":
    unittest.main()
