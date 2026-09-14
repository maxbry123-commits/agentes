"""
日志工具
"""
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional


class ColoredFormatter(logging.Formatter):
    """彩色日志格式化器"""

    # ANSI颜色代码
    COLORS = {
        'DEBUG': '\033[36m',    # 青色
        'INFO': '\033[32m',     # 绿色
        'WARNING': '\033[33m',  # 黄色
        'ERROR': '\033[31m',    # 红色
        'CRITICAL': '\033[35m', # 紫色
    }
    RESET = '\033[0m'

    def format(self, record):
        # 添加颜色
        if record.levelname in self.COLORS:
            record.levelname = f"{self.COLORS[record.levelname]}{record.levelname}{self.RESET}"

        return super().format(record)


class Logger:
    """
    日志管理器
    """

    _instance = None
    _initialized = False

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(
        self,
        name: str = "AI_Pentest",
        level: str = "INFO",
        log_file: Optional[str] = None
    ):
        if self._initialized:
            return

        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, level.upper()))

        # 避免重复添加处理器
        if not self.logger.handlers:
            self._setup_handlers(log_file)

        self._initialized = True

    def _setup_handlers(self, log_file: Optional[str]):
        """设置日志处理器"""
        # 控制台处理器
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG)
        console_format = ColoredFormatter(
            "%(asctime)s | %(levelname)-8s | %(message)s",
            datefmt="%H:%M:%S"
        )
        console_handler.setFormatter(console_format)
        self.logger.addHandler(console_handler)

        # 文件处理器
        if log_file:
            self._add_file_handler(log_file)

    def _add_file_handler(self, log_file: str):
        """添加文件处理器"""
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_format = logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        file_handler.setFormatter(file_format)
        self.logger.addHandler(file_handler)

    def debug(self, message: str):
        self.logger.debug(message)

    def info(self, message: str):
        self.logger.info(message)

    def warning(self, message: str):
        self.logger.warning(message)

    def error(self, message: str):
        self.logger.error(message)

    def critical(self, message: str):
        self.logger.critical(message)

    def success(self, message: str):
        """成功消息（绿色）"""
        self.logger.info(f"\033[32m[SUCCESS]\033[0m {message}")

    def phase(self, phase_name: str):
        """阶段标记"""
        self.logger.info(f"\n{'='*60}")
        self.logger.info(f"  阶段: {phase_name}")
        self.logger.info(f"{'='*60}\n")

    def result(self, title: str, data: dict):
        """结果输出"""
        self.logger.info(f"\n📊 {title}:")
        for key, value in data.items():
            self.logger.info(f"   - {key}: {value}")

    def table(self, headers: list, rows: list):
        """表格输出"""
        # 计算列宽
        widths = [len(h) for h in headers]
        for row in rows:
            for i, cell in enumerate(row):
                widths[i] = max(widths[i], len(str(cell)))

        # 输出表头
        header_line = " | ".join(h.ljust(w) for h, w in zip(headers, widths))
        self.logger.info(f"\n   {header_line}")
        self.logger.info(f"   {'-'*len(header_line)}")

        # 输出数据
        for row in rows:
            row_line = " | ".join(str(c).ljust(w) for c, w in zip(row, widths))
            self.logger.info(f"   {row_line}")


# 全局日志实例
_logger_instance: Optional[Logger] = None


def get_logger(
    name: str = "AI_Pentest",
    level: str = "INFO",
    log_file: Optional[str] = None
) -> Logger:
    """
    获取日志实例

    Args:
        name: 日志器名称
        level: 日志级别
        log_file: 日志文件路径

    Returns:
        Logger实例
    """
    global _logger_instance

    if _logger_instance is None:
        _logger_instance = Logger(name, level, log_file)

    return _logger_instance


def init_logging(config: dict):
    """
    从配置初始化日志

    Args:
        config: 配置字典
    """
    system_config = config.get("system", {})
    level = system_config.get("log_level", "INFO")
    log_file = system_config.get("log_file")

    return get_logger(level=level, log_file=log_file)
