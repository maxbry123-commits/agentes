import sys
import logging
from threading import Lock
from rich.logging import RichHandler


class InfoOnlyFilter(logging.Filter):
    def filter(self, record):
        return record.levelno == logging.INFO


class LoggerManager:
    _instance = None
    _lock = Lock()

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
            return cls._instance

    def __init__(self, mode: str, level):
        if mode == "debug":
            self._setup_debug_logger(level)
        else:
            self._setup_plain_logger(level)

    def _setup_debug_logger(self, level: str):
        logger = logging.getLogger("isek")
        logger.setLevel(level)
        logger.handlers.clear()

        handler = logging.StreamHandler(sys.stdout)
        log_format = "%(asctime)s | %(levelname)s | %(filename)s:%(funcName)s:%(lineno)d | %(message)s"
        handler.setFormatter(logging.Formatter(log_format, datefmt="%Y-%m-%d %H:%M:%S"))
        logger.addHandler(handler)
        logger.propagate = False

    def _setup_plain_logger(self, level: str):
        handler = RichHandler(
            rich_tracebacks=True,
            markup=True,
            show_path=False,
            show_time=False,
            show_level=True,
        )

        handler.addFilter(InfoOnlyFilter())
        handler.setFormatter(logging.Formatter("[blue]%(message)s[/]", datefmt="[%X]"))
        logger = logging.getLogger("isek")
        logger.setLevel(level)
        logger.handlers.clear()
        logger.addHandler(handler)
        logger.propagate = False

    @classmethod
    def plain_mode(cls, level="INFO"):
        return cls(mode="plain", level=level)

    @classmethod
    def debug_mode(cls, level="DEBUG"):
        return cls(mode="debug", level=level)

    @staticmethod
    def get_logger():
        return logging.getLogger("isek")


LoggerManager.plain_mode()
log = LoggerManager.get_logger()
