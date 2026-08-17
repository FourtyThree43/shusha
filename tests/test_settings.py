import tempfile
import unittest
from unittest.mock import patch

from shusha.models.settings import AppSettings


class TestSettings(unittest.TestCase):
    def test_settings_methods(self):
        with (
            tempfile.TemporaryDirectory() as tmp_dir,
            patch("shusha.models.utilities.user_config_dir", return_value=tmp_dir),
        ):
            settings = AppSettings()
            self.assertIsInstance(settings.get_aria2_config(), dict)
            self.assertIsInstance(settings.get_aria2_options(), dict)
            self.assertIsInstance(settings.get_aria2_http_options(), dict)

            settings.set_download_dir("/tmp/downloads")
            self.assertEqual(settings.get_download_dir(), "/tmp/downloads")

            settings.set_logs_dir("/tmp/logs")
            self.assertEqual(settings.get_logs_dir(), "/tmp/logs")

            settings.update_settings({"custom_key": "custom_val"})
            self.assertEqual(
                settings.config_dict["USER"].get("custom_key"), "custom_val"
            )

            settings.save_settings()


if __name__ == "__main__":
    unittest.main()
