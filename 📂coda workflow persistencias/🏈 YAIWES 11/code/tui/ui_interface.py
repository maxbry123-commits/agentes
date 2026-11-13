"""TextualUserInterface — UserInterface 的 Textual TUI 实现。

在 solve() worker 线程中被调用，通过 call_from_thread() 安全地操作 TUI。
blocking 方法 (confirm / choose / prompt_text) 使用 threading.Event 阻塞 worker 线程
同时不阻塞 Textual 事件循环。
"""
import threading
from typing import TYPE_CHECKING, List

from agent.user_interface import UserInterface

if TYPE_CHECKING:
    from tui.app import CTFAgentApp


class TextualUserInterface(UserInterface):
    """Textual 版 UI — 运行在 solve() worker 线程中，通过 call_from_thread 操作 TUI。"""

    def __init__(self, app: "CTFAgentApp"):
        self._app = app
        self._event = threading.Event()
        self._modal_result: object = None

    # ── 非阻塞方法 ──────────────────────────────────────────────

    def display(self, message: str):
        """向主日志区追加文本（非阻塞）。"""
        self._app.call_from_thread(self._app.add_log_line, message)

    def display_separator(self, char: str = "=", length: int = 48):
        self.display(char * length)

    # ── 阻塞方法 ────────────────────────────────────────────────

    def _await_modal(self, modal):
        """通用模式：推送 modal → 阻塞 worker 线程 → 等待 dismiss 回调唤醒。

        带 300s 超时保护 — 若 modal 因渲染异常未能 dismiss，worker 不会永久死锁。
        """
        import logging
        self._modal_result = None
        self._event.clear()
        self._app.call_from_thread(self._app.push_screen, modal, self._on_modal_done)
        if not self._event.wait(timeout=300):
            logging.getLogger(__name__).warning("模态弹窗超时 (300s)，返回默认值")
        return self._modal_result

    def _on_modal_done(self, result: object):
        self._modal_result = result
        self._event.set()

    def confirm(self, prompt: str, yes_label: str = "y", no_label: str = "n") -> bool:
        from tui.modals.confirm import ConfirmModal
        return self._await_modal(ConfirmModal(prompt, yes_label, no_label)) is True

    def choose(self, prompt: str, options: List[str]) -> str:
        from tui.modals.choice import ChoiceModal
        result = self._await_modal(ChoiceModal(prompt, list(options)))
        return result if isinstance(result, str) else ""

    def prompt_text(self, prompt: str) -> str:
        from tui.modals.input_modal import InputModal
        result = self._await_modal(InputModal(prompt))
        return result if isinstance(result, str) else ""
