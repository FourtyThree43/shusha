import logging
import tempfile
import unittest
from pathlib import Path

from shusha.models.logger import LoggerService


class TestLogger(unittest.TestCase):
    def test_logger_service(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            log_file = Path(tmp_dir) / "test.log"
            logger_svc = LoggerService("TestLogger", log_file_path=str(log_file))
            self.assertEqual(logger_svc.logger.name, "TestLogger")
            self.assertIsInstance(logger_svc.logger, logging.Logger)

            # Log messages at various levels
            logger_svc.log("Debug msg", level="debug")
            logger_svc.log("Info msg", level="info")
            logger_svc.log("Warning msg", level="warning")
            logger_svc.log("Error msg", level="error")
            logger_svc.log("Critical msg", level="critical")


if __name__ == "__main__":
    unittest.main()
