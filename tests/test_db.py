import os
import tempfile
import unittest
import uuid
from datetime import datetime

from shusha.models.db import StructsDB


class TestStructsDB(unittest.TestCase):
    @staticmethod
    def generate_test_gid():
        gid = str(uuid.uuid4().hex)
        return gid[:16]

    def generate_test_download(self):
        return {
            "gid": self.test_gid,
            "status": "complete",
            "totalLength": 34896138,
            "completedLength": 34896138,
            "uploadLength": 0,
            "bitfield": "ffff80",
            "downloadSpeed": 0,
            "uploadSpeed": 0,
            "infoHash": "",
            "numSeeders": 0,
            "seeder": 0,
            "pieceLength": 2097152,
            "numPieces": 17,
            "connections": 0,
            "errorCode": 0,
            "errorMessage": "",
            "followedBy": [],
            "following": "",
            "belongsTo": "",
            "dir": "/downloads",
            "verifiedLength": 0,
            "verifyIntegrityPending": 0,
            "files": [
                {
                    "file_index": 1,
                    "path": "/downloads/file.txt",
                    "length": 50,
                    "completed_length": 50,
                    "selected": 1,
                    "uris": ["http://example.com/file.txt"],
                }
            ],
            "bittorrent": [
                {
                    "announce_list": ["http://tracker.example.com"],
                    "comment": "Test torrent",
                    "creation_date": int(datetime.now().timestamp()),
                    "mode": "sequential",
                    "info_name": "test_info",
                }
            ],
        }

    def setUp(self):
        self.test_gid = self.generate_test_gid()
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_db_path = os.path.join(self.temp_dir.name, "test_structs.db")
        self.db = StructsDB(db_path=self.temp_db_path)

    def tearDown(self):
        self.db.close_connection()
        self.temp_dir.cleanup()

    def test_create_tables(self):
        self.assertTrue(os.path.exists(self.temp_db_path))

    def test_insert_and_retrieve_download_info(self):
        download_info = self.generate_test_download()
        gid = download_info["gid"]

        with self.db.database_transaction() as conn:
            cursor = conn.cursor()
            self.db.insert_download_info(cursor, gid, download_info)

        res = self.db.get_download_info(gid)
        self.assertIsNotNone(res)
        res_dict = self.db.to_dict([res], self.db.DOWNLOAD_COLUMNS)[0]
        self.assertEqual(res_dict["gid"], gid)
        self.assertEqual(res_dict["status"], "complete")
        self.assertEqual(res_dict["totalLength"], 34896138)

    def test_insert_and_retrieve_files_info(self):
        gid = self.test_gid
        file_info = {
            "file_index": 1,
            "path": "/downloads/file.txt",
            "length": 50,
            "completed_length": 50,
            "selected": 1,
            "uris": ["http://example.com/file.txt"],
        }

        with self.db.database_transaction() as conn:
            cursor = conn.cursor()
            self.db.insert_file_info(cursor, file_info, gid)

        retrieved_files = self.db.get_files_info(gid)
        self.assertEqual(len(retrieved_files), 1)
        retrieved_file_dict = self.db.to_dict(retrieved_files, self.db.FILES_COLUMNS)[0]
        self.assertEqual(retrieved_file_dict["file_index"], 1)
        self.assertEqual(retrieved_file_dict["path"], "/downloads/file.txt")

    def test_insert_and_retrieve_bittorrent_info(self):
        gid = self.test_gid
        bittorrent_info = {
            "announce_list": ["http://tracker.example.com"],
            "comment": "Test torrent",
            "creation_date": int(datetime.now().timestamp()),
            "mode": "sequential",
            "info_name": "test_info",
        }

        with self.db.database_transaction() as conn:
            cursor = conn.cursor()
            self.db.insert_bittorrent_info(cursor, bittorrent_info, gid)

        retrieved_bittorrents = self.db.get_bittorrent_info(gid)
        self.assertEqual(len(retrieved_bittorrents), 1)
        retrieved_bt_dict = self.db.to_dict(
            retrieved_bittorrents, self.db.BITTORRENT_COLUMNS
        )[0]
        self.assertEqual(retrieved_bt_dict["comment"], "Test torrent")
        self.assertEqual(retrieved_bt_dict["info_name"], "test_info")

    def test_store_and_get_all_downloads(self):
        download_info = self.generate_test_download()
        gid = download_info["gid"]
        self.db.store_download_info(gid, download_info)

        all_downloads = self.db.get_all_downloads()
        self.assertEqual(len(all_downloads), 1)

    def test_update_download(self):
        download_info = self.generate_test_download()
        gid = download_info["gid"]

        with self.db.database_transaction() as conn:
            cursor = conn.cursor()
            self.db.insert_download_info(cursor, gid, download_info)

        self.db.update_download(gid, {"status": "paused", "downloadSpeed": 5000})
        updated = self.db.get_download_info(gid)
        self.assertIsNotNone(updated)
        updated_dict = self.db.to_dict([updated], self.db.DOWNLOAD_COLUMNS)[0]
        self.assertEqual(updated_dict["status"], "paused")
        self.assertEqual(updated_dict["downloadSpeed"], 5000)

    def test_reset_database(self):
        download_info = self.generate_test_download()
        gid = download_info["gid"]
        self.db.store_download_info(gid, download_info)
        self.db.reset_database()
        self.assertEqual(len(self.db.get_all_downloads()), 0)


if __name__ == "__main__":
    unittest.main()
