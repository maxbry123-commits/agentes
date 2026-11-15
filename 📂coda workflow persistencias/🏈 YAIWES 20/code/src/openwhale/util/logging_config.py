"""日志配置 - 使用 loguru + rich 管理日志"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from loguru import logger
from rich.console import Console
from rich.logging import RichHandler

console = Console()

LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)


def setup_logging(log_level: str = "INFO") -> None:
    """初始化日志配置：控制台使用 rich，文件保存全量日志"""
    logger.remove()

    logger.add(
        RichHandler(console=console, rich_tracebacks=True, show_path=False),
        level=log_level,
        format="{message}",
        colorize=False,
    )

    log_file = LOG_DIR / f"openwhale_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    logger.add(
        str(log_file),
        level="DEBUG",
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level:<8} | {name}:{function}:{line} - {message}",
        encoding="utf-8",
        retention="30 days",
    )

    logger.info(f"日志初始化完成，日志文件: {log_file}")
