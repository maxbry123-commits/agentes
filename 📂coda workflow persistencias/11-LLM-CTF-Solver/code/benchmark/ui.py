"""基准测试用 UI — 非交互模式，自动确认所有操作。"""

import re
import logging
from typing import Optional
from agent.user_interface import UserInterface

logger = logging.getLogger(__name__)


class BenchmarkUI(UserInterface):
    """自动化 UI：无阻塞、全部自动确认。"""

    def __init__(self, flag_regex: Optional[str] = None):
        self.flag_regex = flag_regex
        self.messages: list[str] = []

    def display(self, message: str):
        self.messages.append(message)
        logger.debug("[benchmark] %s", message[:200])

    def choose(self, prompt: str, options: list[str]) -> str:
        logger.info("[benchmark] 自动选择: %s → %s", prompt[:60], options[0])
        return options[0]

    def confirm(self, prompt: str, yes_label: str = "y", no_label: str = "n") -> bool:
        if self.flag_regex and re.search(self.flag_regex, prompt, re.IGNORECASE):
            logger.info("[benchmark] 自动确认 (匹配 flag 正则)")
            return True
        logger.info("[benchmark] 自动确认: %s", prompt[:60])
        return True

    def prompt_text(self, prompt: str) -> str:
        logger.info("[benchmark] 跳过输入: %s", prompt[:60])
        return ""
