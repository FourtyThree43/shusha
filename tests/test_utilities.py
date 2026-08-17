import tempfile
import unittest
from datetime import timedelta
from pathlib import Path
from unittest.mock import patch

from shusha.models.utilities import (
    bool_or_value,
    bool_to_str,
    cache_dir,
    config_dir,
    data_dir,
    download_dir,
    format_eta,
    format_size,
    format_speed,
    get_version,
    load_configuration,
    log_dir,
    sizeof_fmt,
    timedelta_fmt,
)


class TestUtilities(unittest.TestCase):
    def test_bool_or_value(self):
        self.assertTrue(bool_or_value("true"))
        self.assertFalse(bool_or_value("false"))
        self.assertEqual(bool_or_value("other"), "other")
        self.assertEqual(bool_or_value(123), 123)

    def test_bool_to_str(self):
        self.assertEqual(bool_to_str(True), "true")
        self.assertEqual(bool_to_str(False), "false")
        self.assertEqual(bool_to_str("value"), "value")

    def test_sizeof_fmt(self):
        self.assertEqual(sizeof_fmt(500), "500.00 B")
        self.assertEqual(sizeof_fmt(1024), "1.00 KiB")
        self.assertEqual(sizeof_fmt(1048576), "1.00 MiB")
        self.assertEqual(sizeof_fmt(1073741824), "1.00 GiB")

    def test_format_speed(self):
        self.assertEqual(format_speed(1024), "1.00 KiB/s")

    def test_format_size(self):
        self.assertEqual(format_size(2048), "2.00 KiB")

    def test_timedelta_fmt(self):
        td = timedelta(days=1, hours=2, minutes=3, seconds=4)
        formatted = timedelta_fmt(td)
        self.assertEqual(formatted, "1D2H:3M:4S")

        td2 = timedelta(days=2, hours=2, minutes=3, seconds=4)
        self.assertEqual(timedelta_fmt(td2), "2D:2H:3M:4S")

    def test_format_eta(self):
        self.assertEqual(format_eta(timedelta.max), "-")
        td = timedelta(minutes=5, seconds=30)
        self.assertTrue(len(format_eta(td)) > 0)

    def test_directories(self):
        self.assertIsInstance(download_dir(), Path)
        self.assertIsInstance(config_dir("shusha"), Path)
        self.assertIsInstance(data_dir("shusha"), Path)
        self.assertIsInstance(cache_dir("shusha"), Path)
        self.assertIsInstance(log_dir("shusha"), Path)

    def test_get_version(self):
        ver = get_version()
        self.assertIsInstance(ver, str)

    def test_load_configuration(self):
        with (
            tempfile.TemporaryDirectory() as tmp_dir,
            patch("shusha.models.utilities.user_config_dir", return_value=tmp_dir),
        ):
            config = load_configuration()
            self.assertIn("DEFAULT", config)
            self.assertIn("aria2", config["DEFAULT"])
            self.assertEqual(config["DEFAULT"]["aria2"]["port"], 6800)


if __name__ == "__main__":
    unittest.main()
