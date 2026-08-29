"""
Unit tests for the pure Python Shusha 2 Domain Layer.
"""

import unittest
from datetime import datetime, time

from shusha.domain import (
    Bitfield,
    BitRate,
    ByteSize,
    Category,
    CategoryId,
    CategoryRule,
    Checksum,
    DomainEvent,
    Download,
    DownloadCreatedEvent,
    DownloadFile,
    DownloadId,
    DownloadQueue,
    DownloadSource,
    DownloadState,
    Duration,
    Gid,
    InvalidStateTransitionError,
    MetalinkFile,
    MetalinkResource,
    Peer,
    PeerId,
    Percentage,
    Port,
    ScheduleWindow,
    TorrentMeta,
    Tracker,
    Uri,
    ValueObjectValidationError,
    can_transition,
    make_category_id,
    make_download_id,
    make_gid,
    validate_transition,
)


class TestDomainIdentifiers(unittest.TestCase):
    def test_gid_creation(self):
        gid = make_gid("2089b05ecca3d829")
        self.assertEqual(str(gid), "2089b05ecca3d829")
        with self.assertRaises(ValueError):
            make_gid("")

    def test_download_id_creation(self):
        dl_id = make_download_id("dl-abc-123")
        self.assertEqual(str(dl_id), "dl-abc-123")
        with self.assertRaises(ValueError):
            make_download_id("   ")

    def test_category_id_creation(self):
        cat_id = make_category_id(" ISOs ")
        self.assertEqual(str(cat_id), "isos")
        with self.assertRaises(ValueError):
            make_category_id("")


class TestDomainValues(unittest.TestCase):
    def test_byte_size_parsing_and_formatting(self):
        self.assertEqual(ByteSize.from_str("1024").bytes, 1024)
        self.assertEqual(ByteSize.from_str("1.5 MiB").bytes, int(1.5 * 1024 * 1024))
        self.assertEqual(ByteSize.from_str("2 GB").bytes, 2 * 1000 * 1000 * 1000)
        self.assertEqual(ByteSize.from_str("10M").bytes, 10 * 1024 * 1024)
        self.assertEqual(ByteSize.from_str("0").bytes, 0)
        self.assertEqual(ByteSize(0).human_readable(), "0 B")
        self.assertIn("MiB", ByteSize(5 * 1024 * 1024).human_readable(binary=True))
        self.assertIn("MB", ByteSize(5 * 1000 * 1000).human_readable(binary=False))

        # Arithmetic
        b1 = ByteSize(100)
        b2 = ByteSize(50)
        self.assertEqual((b1 + b2).bytes, 150)
        self.assertEqual((b1 - b2).bytes, 50)
        self.assertEqual((b2 - b1).bytes, 0)

        with self.assertRaises(ValueObjectValidationError):
            ByteSize(-10)

    def test_bit_rate(self):
        rate = BitRate.from_str("2.5 MB/s")
        self.assertGreater(rate.bytes_per_sec, 0)
        self.assertIn("/s", rate.human_readable())
        with self.assertRaises(ValueObjectValidationError):
            BitRate(-5)

    def test_duration_and_eta(self):
        completed = ByteSize(500)
        total = ByteSize(1500)
        speed = BitRate(100)
        eta = Duration.calculate_eta(completed, total, speed)
        self.assertIsNotNone(eta)
        assert eta is not None
        self.assertEqual(eta.seconds, 10)
        self.assertEqual(eta.human_readable(), "00:10")

        # Zero speed gives None
        self.assertIsNone(Duration.calculate_eta(completed, total, BitRate(0)))

    def test_percentage(self):
        p = Percentage.from_progress(ByteSize(50), ByteSize(100))
        self.assertEqual(p.value, 50.0)
        self.assertEqual(p.human_readable(), "50.0%")

        # Clamping
        p_over = Percentage(150.0)
        self.assertEqual(p_over.value, 100.0)

    def test_port(self):
        p = Port(6800)
        self.assertEqual(p.number, 6800)
        with self.assertRaises(ValueObjectValidationError):
            Port(0)
        with self.assertRaises(ValueObjectValidationError):
            Port(70000)

    def test_uri(self):
        u1 = Uri.parse("https://example.com/downloads/linux.iso")
        self.assertEqual(u1.scheme, "https")
        self.assertEqual(u1.host, "example.com")

        u2 = Uri.parse("magnet:?xt=urn:btih:1234567890abcdef")
        self.assertEqual(u2.scheme, "magnet")

        with self.assertRaises(ValueObjectValidationError):
            Uri.parse("invalid_scheme://file")

    def test_checksum(self):
        c = Checksum(
            "sha-256",
            "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        )
        self.assertEqual(c.algorithm, "sha-256")
        with self.assertRaises(ValueObjectValidationError):
            Checksum("sha-256", "not-a-hex-string-!")

    def test_bitfield(self):
        # 'f0' in hex is 11110000 in binary (8 pieces, 4 completed)
        bf = Bitfield("f0")
        self.assertEqual(bf.total_pieces, 8)
        self.assertEqual(bf.completed_pieces, 4)
        self.assertEqual(bf.completion_percentage.value, 50.0)
        self.assertTrue(bf.is_piece_complete(0))
        self.assertTrue(bf.is_piece_complete(1))
        self.assertTrue(bf.is_piece_complete(2))
        self.assertTrue(bf.is_piece_complete(3))
        self.assertFalse(bf.is_piece_complete(4))
        self.assertFalse(bf.is_piece_complete(7))
        self.assertFalse(bf.is_piece_complete(100))


class TestDomainStateMachine(unittest.TestCase):
    def test_valid_transitions(self):
        self.assertTrue(can_transition(DownloadState.NEW, DownloadState.STARTING))
        self.assertTrue(can_transition(DownloadState.STARTING, DownloadState.ACTIVE))
        self.assertTrue(can_transition(DownloadState.ACTIVE, DownloadState.PAUSED))
        self.assertTrue(can_transition(DownloadState.ACTIVE, DownloadState.COMPLETED))
        self.assertTrue(can_transition(DownloadState.ACTIVE, DownloadState.SEEDING))
        self.assertTrue(can_transition(DownloadState.PAUSED, DownloadState.RESUMING))
        self.assertTrue(can_transition(DownloadState.RESUMING, DownloadState.ACTIVE))

    def test_invalid_transitions(self):
        self.assertFalse(can_transition(DownloadState.COMPLETED, DownloadState.ACTIVE))
        self.assertFalse(can_transition(DownloadState.REMOVED, DownloadState.ACTIVE))
        with self.assertRaises(InvalidStateTransitionError):
            validate_transition(DownloadState.COMPLETED, DownloadState.ACTIVE)


class TestDownloadAggregate(unittest.TestCase):
    def test_download_entity_lifecycle(self):
        gid = make_gid("2089b05ecca3d829")
        dl_id = make_download_id("dl-1")
        source = DownloadSource.from_str("https://example.com/archive.tar.gz", "USED")
        file_item = DownloadFile(
            index=1,
            path="/downloads/archive.tar.gz",
            length=ByteSize(1000),
            completed_length=ByteSize(0),
            selected=True,
            uris=[source],
        )

        dl = Download(
            gid=gid,
            download_id=dl_id,
            name="archive.tar.gz",
            state=DownloadState.STARTING,
            total_length=ByteSize(1000),
            completed_length=ByteSize(0),
            download_speed=BitRate(0),
            upload_speed=BitRate(0),
            eta=None,
            files=[file_item],
            sources=[source],
        )

        self.assertTrue(dl.is_active is False)
        active_dl = dl.transition_to(DownloadState.ACTIVE)
        self.assertTrue(active_dl.is_active)

        # Update progress
        progress_dl = active_dl.update_progress(
            completed_length=ByteSize(500),
            total_length=ByteSize(1000),
            download_speed=BitRate(100),
            upload_speed=BitRate(0),
            connections=4,
        )
        self.assertEqual(progress_dl.progress.value, 50.0)
        self.assertEqual(progress_dl.connections, 4)
        self.assertIsNotNone(progress_dl.eta)

        # Complete
        comp_dl = progress_dl.transition_to(DownloadState.COMPLETED)
        self.assertTrue(comp_dl.is_completed)


class TestBitTorrentAndMetalink(unittest.TestCase):
    def test_torrent_meta(self):
        tracker = Tracker("http://tracker.example.com/announce", tier=0)
        meta = TorrentMeta(
            info_hash="abcdef0123456789",
            name="Fedora-Workstation.iso",
            piece_length=ByteSize(2 * 1024 * 1024),
            num_pieces=1000,
            total_length=ByteSize(2000 * 1024 * 1024),
            files=[],
            trackers=[tracker],
        )
        self.assertEqual(meta.name, "Fedora-Workstation.iso")
        self.assertEqual(len(meta.trackers), 1)

    def test_peer_model(self):
        peer = Peer(
            peer_id=PeerId("peer-1"),
            ip="192.168.1.100",
            port=Port(51413),
            bitfield=Bitfield("ff"),
            am_choking=False,
            peer_choking=False,
            download_speed=BitRate(1024 * 1024),
            upload_speed=BitRate(0),
            seeder=True,
        )
        self.assertTrue(peer.seeder)
        self.assertEqual(peer.port.number, 51413)

    def test_metalink_model(self):
        res = MetalinkResource(Uri.parse("https://mirror.org/file.zip"), priority=10)
        chk = Checksum(
            "sha-256",
            "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        )
        meta_file = MetalinkFile(
            name="file.zip",
            size=ByteSize(5000),
            checksums=[chk],
            resources=[res],
        )
        self.assertEqual(meta_file.name, "file.zip")
        self.assertEqual(len(meta_file.resources), 1)


class TestCategoryAndScheduler(unittest.TestCase):
    def test_category_rule_matching(self):
        rule = CategoryRule(
            extensions=["iso", "img"], host_patterns=["distrowatch.com"]
        )
        cat = Category(
            id=CategoryId("os-images"),
            name="OS Images",
            download_dir="/downloads/os",
            rule=rule,
        )

        self.assertTrue(
            cat.rule.matches("archlinux-2026.iso", "https://archlinux.org/rel.iso")
        )
        self.assertTrue(
            cat.rule.matches("download.php", "https://distrowatch.com/download.php")
        )
        self.assertFalse(cat.rule.matches("music.mp3", "https://spotify.com/song.mp3"))

    def test_schedule_window(self):
        # Window from 01:00 to 06:00
        window = ScheduleWindow(
            day_of_week=-1,  # Daily
            start_time=time(1, 0),
            end_time=time(6, 0),
            speed_limit=BitRate(1024 * 1024),
        )
        self.assertTrue(window.is_active_at(datetime(2026, 8, 29, 3, 30)))
        self.assertFalse(window.is_active_at(datetime(2026, 8, 29, 12, 0)))


class TestDownloadQueue(unittest.TestCase):
    def test_queue_reordering(self):
        q = DownloadQueue(max_active_downloads=3)
        dl1 = DownloadId("1")
        dl2 = DownloadId("2")
        dl3 = DownloadId("3")
        q.items = [dl1, dl2, dl3]

        q.move_to_bottom(dl1)
        self.assertEqual(q.items, [dl2, dl3, dl1])

        q.move_to_top(dl1)
        self.assertEqual(q.items, [dl1, dl2, dl3])

        q.move_down(dl1)
        self.assertEqual(q.items, [dl2, dl1, dl3])

        q.move_up(dl3)
        self.assertEqual(q.items, [dl2, dl3, dl1])


class TestDomainEvents(unittest.TestCase):
    def test_domain_event_creation(self):
        evt = DownloadCreatedEvent(
            download_id=DownloadId("dl-1"),
            gid=Gid("2089b05ecca3d829"),
            name="ubuntu.iso",
        )
        self.assertIsInstance(evt, DomainEvent)
        self.assertEqual(evt.name, "ubuntu.iso")
        self.assertIsNotNone(evt.timestamp)


if __name__ == "__main__":
    unittest.main()
