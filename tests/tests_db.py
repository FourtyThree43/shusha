import os
import shutil
import tempfile
import unittest
import uuid
from datetime import datetime
from unittest.mock import MagicMock

from shusha.models.db import StructsDB


class TestStructsDB(unittest.TestCase):

    @staticmethod
    def generate_test_gid():
        # Generate a UUID (Universally Unique Identifier)
        gid = str(uuid.uuid4().hex)

        # Take the first 16 characters as the GID (aria2 representation)
        test_gid = gid[:16]

        return test_gid

    def generate_test_download(self):
        # Generate a test download
        test_download = {
            "gid":
            self.test_gid,
            "status":
            "complete",
            "totalLength":
            "34896138",
            "completedLength":
            "34896138",
            "uploadLength":
            "0",
            "bitfield":
            "ffff80",
            "downloadSpeed":
            "0",
            "uploadSpeed":
            "0",
            "infoHash":
            "",
            "numSeeders":
            "0",
            "seeder":
            "0",
            "pieceLength":
            "2097152",
            "numPieces":
            "17",
            "connections":
            "0",
            "errorCode":
            "0",
            "errorMessage":
            "",
            "followedBy": [],
            "following":
            "",
            "belongsTo":
            "",
            "dir":
            "/downloads",
            "verifiedLength":
            "0",
            "verifyIntegrityPending":
            "0",
            "files": [{
                "index": 1,
                "path": "/downloads/file.txt",
                "length": 50,
                "completedLength": 50,
                "selected": 1,
                "uris": ["http://example.com/file.txt"],
            }],
            "bittorrent": {
                "announceList": [["http://tracker.example.com"]],
                "comment": "Test torrent",
                "creationDate": int(datetime.now().timestamp()),
                "mode": "sequential",
                "infoName": "test_info",
            },
        }

        return test_download

    def setUp(self):
        # Create a temporary database file for testing
        self.test_gid = self.generate_test_gid()
        self.temp_db_path = tempfile.mktemp()
        self.db = StructsDB(db_path=self.temp_db_path)

    def tearDown(self):
        # Close the database connection and remove the temporary database file
        self.db.close_connection()
        os.remove(self.temp_db_path)

    def test_create_tables(self):
        # Ensure that tables are created successfully
        self.assertTrue(os.path.exists(self.temp_db_path))

    def test_insert_and_retrieve_download_info(self):
        download_info = self.generate_test_download()
        gid = download_info["gid"]
        print(gid)
        # Insert download information
        with self.db.database_transaction() as conn:
            cursor = conn.cursor()
            self.db.insert_download_info(cursor, gid, download_info)

            # Retrieve download information
            res = self.db.get_download_info(gid)
            print(res)
            # res_dict = self.db.to_dict(res, self.db.DOWNLOAD_COLUMNS)
            # for download in res_dict:
            #     print(download)
            #     retrieved_info = dict(download)
            #     # print(retrieved_info)

            # Check if retrieved information matches the inserted information
            # self.assertEqual(retrieved_info["gid"], gid)
            # self.assertEqual(retrieved_info["status"], download_info["status"])
            # self.assertEqual(retrieved_info["totalLength"],
            #                  download_info["totalLength"])
            # self.assertEqual(retrieved_info["completedLength"],
            #                  download_info["completedLength"])
            # self.assertEqual(retrieved_info["dir"], download_info["dir"])
            # pass

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

        # Insert files information
        with self.db.database_transaction() as conn:
            cursor = conn.cursor()
            self.db.insert_file_info(cursor, file_info, gid)

        # Retrieve files information
        # retrieved_files = self.db.get_files_info(gid)

        # Check if retrieved information matches the inserted information
        # self.assertEqual(len(retrieved_files), 1)
        # retrieved_file_info = dict(retrieved_files[0])
        # self.assertEqual(retrieved_file_info["file_index"],
        #                  file_info["file_index"])
        # self.assertEqual(retrieved_file_info["path"], file_info["path"])
        # self.assertEqual(retrieved_file_info["length"], file_info["length"])
        # self.assertEqual(retrieved_file_info["completed_length"],
        #                  file_info["completed_length"])
        # self.assertEqual(retrieved_file_info["selected"],
        #                  file_info["selected"])
        # self.assertEqual(retrieved_file_info["uris"],
        #                  json.dumps(file_info["uris"]))
        pass

    def test_insert_and_retrieve_bittorrent_info(self):
        gid = self.test_gid
        bittorrent_info = {
            "announce_list": ["http://tracker.example.com"],
            "comment": "Test torrent",
            "creation_date": int(datetime.now().timestamp()),
            "mode": "sequential",
            "info_name": "test_info",
        }

        # Insert BitTorrent information
        with self.db.database_transaction() as conn:
            cursor = conn.cursor()
            self.db.insert_bittorrent_info(cursor, bittorrent_info, gid)

        # Retrieve BitTorrent information
        retrieved_bittorrents = self.db.get_bittorrent_info(gid)

        # Check if retrieved information matches the inserted information
        # self.assertEqual(len(retrieved_bittorrents), 1)
        # retrieved_bittorrent_info = list(retrieved_bittorrents[0])
        # self.assertEqual(retrieved_bittorrent_info["announce_list"],
        #                  json.dumps(bittorrent_info["announce_list"]))
        # self.assertEqual(retrieved_bittorrent_info["comment"],
        #                  bittorrent_info["comment"])
        # self.assertEqual(retrieved_bittorrent_info["creation_date"],
        #                  bittorrent_info["creation_date"])
        # self.assertEqual(retrieved_bittorrent_info["mode"],
        #                  bittorrent_info["mode"])
        # self.assertEqual(retrieved_bittorrent_info["info_name"],
        #                  bittorrent_info["info_name"])
        pass

    def test_update_download(self):
        gid = self.test_gid
        download_info = {"status": "in_progress", "downloadSpeed": 5000}

        # Insert download information
        with self.db.database_transaction() as conn:
            cursor = conn.cursor()
            self.db.insert_download_info(cursor, gid, {})

        # Update download information
        self.db.update_download(gid, download_info)

        # Retrieve updated information
        updated_info = self.db.get_download_info(gid)

        # Check if the status and download speed are updated
        # self.assertEqual(updated_info["status"], download_info["status"])
        # self.assertEqual(updated_info["downloadSpeed"],
        #                  download_info["downloadSpeed"])
        pass


if __name__ == '__main__':
    unittest.main()
