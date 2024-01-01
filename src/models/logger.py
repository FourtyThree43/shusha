import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path


class LoggerService:
    LOG_DIR = Path("logs")
    LOG_FILE_PATH = LOG_DIR / "shusha.log"
    LOG_FORMAT = '%(asctime)s | %(levelname)s | %(message)s'
    LOG_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
    MAX_BYTES = 5 * 1024 * 1024  # 5 MB

    def __init__(self, logger_name="shusha", log_file_path=None):
        self.logger = logging.getLogger(logger_name)
        self.logger.setLevel(logging.DEBUG)

        self._ensure_log_directory(log_file_path)
        self._setup_handlers(log_file_path)

    def _ensure_log_directory(self, log_file_path):
        if log_file_path:
            log_directory = Path(log_file_path).parent
            log_directory.mkdir(parents=True, exist_ok=True)
        else:
            self.LOG_DIR.mkdir(parents=True, exist_ok=True)

    def _setup_handlers(self, log_file_path):
        for handler in logging.root.handlers[:]:
            logging.root.removeHandler(handler)

        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)

        # Create file handler and set level to DEBUG
        file_handler = RotatingFileHandler(log_file_path or self.LOG_FILE_PATH,
                                           maxBytes=self.MAX_BYTES,
                                           backupCount=2)
        file_handler.setLevel(logging.DEBUG)

        # Create formatter
        formatter = logging.Formatter(fmt=self.LOG_FORMAT,
                                      datefmt=self.LOG_DATE_FORMAT)

        # Add formatter to handlers
        console_handler.setFormatter(formatter)
        file_handler.setFormatter(formatter)

        # Add handlers to logger
        self.logger.addHandler(console_handler)
        self.logger.addHandler(file_handler)

    def log(self, message, level="info"):
        """
        Log a message using the logging module.

        Args:
            message (str): The log message.
            level (str): The log level (default is "info").
        """
        log_level = level.upper()

        if log_level == "DEBUG":
            self.logger.debug(message)
        elif log_level == "INFO":
            self.logger.info(message)
        elif log_level == "WARNING":
            self.logger.warning(message)
        elif log_level == "ERROR":
            self.logger.error(message)
        elif log_level == "CRITICAL":
            self.logger.critical(message)
        else:
            self.logger.warning(
                f"Invalid log level: {level}. Defaulting to 'info'.")
            self.logger.info(message)


if __name__ == "__main__":
    # Example usage
    logger_service = LoggerService()

    logger_service.log("This is an info message.")
    logger_service.log("This is an debug message.", level="debug")
    logger_service.log("This is a warning message.", level="warning")
    logger_service.log("This is an error message.", level="error")
