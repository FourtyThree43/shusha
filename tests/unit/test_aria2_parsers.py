"""
Unit tests for aria2 raw payload parsers.
"""

import unittest

from shusha.domain.states import DownloadState
from shusha.infrastructure.aria2.parsers import (
    map_aria2_status_to_state,
    parse_download_file,
    parse_download_source,
    parse_download_status,
    parse_global_stat,
    parse_peer,
    parse_server,
)


class TestAria2Parsers(unittest.TestCase):
    def test_status_mapping(self):
        self.assertEqual(
            map_aria2_status_to_state("active", seeder=False), DownloadState.ACTIVE
        )
        self.assertEqual(
            map_aria2_status_to_state("active", seeder=True), DownloadState.SEEDING
        )
        self.assertEqual(map_aria2_status_to_state("waiting"), DownloadState.QUEUED)
        self.assertEqual(map_aria2_status_to_state("paused"), DownloadState.PAUSED)
        self.assertEqual(map_aria2_status_to_state("complete"), DownloadState.COMPLETED)
        self.assertEqual(map_aria2_status_to_state("error"), DownloadState.FAILED)
        self.assertEqual(map_aria2_status_to_state("removed"), DownloadState.REMOVED)

    def test_parse_download_source(self):
        raw = {"uri": "https://example.com/file.iso", "status": "used"}
        src = parse_download_source(raw)
        self.assertEqual(src.uri.raw_uri, "https://example.com/file.iso")
        self.assertEqual(src.status.value, "USED")

    def test_parse_download_file(self):
        raw = {
            "index": "1",
            "path": "/tmp/test.zip",
            "length": "1048576",
            "completedLength": "524288",
            "selected": "true",
            "uris": [{"uri": "https://example.com/test.zip", "status": "used"}],
        }
        df = parse_download_file(raw)
        self.assertEqual(df.index, 1)
        self.assertEqual(df.length.bytes, 1048576)
        self.assertEqual(df.completed_length.bytes, 524288)
        self.assertTrue(df.selected)
        self.assertEqual(len(df.uris), 1)

    def test_parse_download_status(self):
        raw = {
            "gid": "2089b05ecca3d829",
            "status": "active",
            "totalLength": "1000000",
            "completedLength": "500000",
            "downloadSpeed": "50000",
            "uploadSpeed": "10000",
            "dir": "/home/user/downloads",
            "connections": "5",
            "files": [
                {
                    "index": "1",
                    "path": "/home/user/downloads/video.mp4",
                    "length": "1000000",
                    "completedLength": "500000",
                    "selected": "true",
                    "uris": [],
                }
            ],
            "bitfield": "ff",
        }
        dl = parse_download_status(raw)
        self.assertEqual(str(dl.gid), "2089b05ecca3d829")
        self.assertEqual(dl.name, "video.mp4")
        self.assertEqual(dl.state, DownloadState.ACTIVE)
        self.assertEqual(dl.completed_length.bytes, 500000)
        self.assertIsNotNone(dl.eta)
        self.assertEqual(dl.connections, 5)

    def test_parse_peer(self):
        raw = {
            "peerId": "peer-abc",
            "ip": "10.0.0.5",
            "port": "51413",
            "bitfield": "f0",
            "amChoking": "false",
            "peerChoking": "false",
            "downloadSpeed": "10000",
            "uploadSpeed": "5000",
            "seeder": "true",
        }
        p = parse_peer(raw)
        self.assertEqual(str(p.peer_id), "peer-abc")
        self.assertEqual(p.ip, "10.0.0.5")
        self.assertEqual(p.port.number, 51413)
        self.assertTrue(p.seeder)

    def test_parse_server(self):
        raw = {
            "index": "1",
            "servers": [
                {
                    "uri": "http://mirror.example.com/file",
                    "currentUri": "http://mirror.example.com/file",
                    "downloadSpeed": "250000",
                }
            ],
        }
        srv = parse_server(raw)
        self.assertEqual(srv.uri.raw_uri, "http://mirror.example.com/file")
        self.assertEqual(srv.download_speed.bytes_per_sec, 250000)

    def test_parse_global_stat(self):
        raw = {
            "downloadSpeed": "1048576",
            "uploadSpeed": "524288",
            "numActive": "3",
            "numWaiting": "2",
            "numStopped": "5",
            "numStoppedTotal": "10",
        }
        stat = parse_global_stat(raw)
        self.assertEqual(stat.download_speed.bytes_per_sec, 1048576)
        self.assertEqual(stat.num_active, 3)
        self.assertEqual(stat.num_waiting, 2)


if __name__ == "__main__":
    unittest.main()
