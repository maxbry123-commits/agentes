"""用户界面抽象接口 — 解耦 Agent 与输入输出方式。

默认提供 CLIUserInterface（print/input），未来可替换为 TUI / API 实现。
"""

import logging
from abc import ABC, abstractmethod
from typing import List, Tuple

logger = logging.getLogger(__name__)


class UserInterface(ABC):
    """用户界面抽象基类。"""

    @abstractmethod
    def display(self, message: str):
        """向用户显示一条消息。"""

    @abstractmethod
    def choose(self, prompt: str, options: List[str]) -> str:
        """让用户从选项列表中选择，返回选项文本（非编号）。"""

    @abstractmethod
    def confirm(self, prompt: str, yes_label: str = "y", no_label: str = "n") -> bool:
        """让用户确认是/否。"""

    @abstractmethod
    def prompt_text(self, prompt: str) -> str:
        """获取用户自由文本输入。"""

    def display_separator(self, char: str = "=", length: int = 48):
        """显示分隔线。"""
        self.display(char * length)


class CLIUserInterface(UserInterface):
    """命令行界面实现 — 使用 print / input。"""

    def display(self, message: str):
        print(message)

    def choose(self, prompt: str, options: List[str]) -> str:
        self.display(f"\n{prompt}")
        for i, opt in enumerate(options, 1):
            self.display(f"{i}. {opt}")
        while True:
            try:
                choice = input("请输入选项编号: ").strip()
            except (EOFError, OSError):
                logger.warning("非交互环境，默认选择第一项")
                return options[0]
            if choice.isdigit() and 1 <= int(choice) <= len(options):
                return options[int(choice) - 1]
            self.display(f"无效选项，请输入 1-{len(options)}")

    def confirm(self, prompt: str, yes_label: str = "y", no_label: str = "n") -> bool:
        self.display(prompt)
        while True:
            try:
                response = input(
                    f"输入 '{yes_label}' 确认, '{no_label}' 取消: "
                ).strip().lower()
            except (EOFError, OSError):
                logger.warning("非交互环境，默认取消")
                return False
            if response == yes_label:
                return True
            elif response == no_label:
                return False
            self.display(f"无效输入，请输入 '{yes_label}' 或 '{no_label}'")

    def prompt_text(self, prompt: str) -> str:
        try:
            return input(prompt).strip()
        except (EOFError, OSError):
            logger.warning("非交互环境，返回空字符串")
            return ""
