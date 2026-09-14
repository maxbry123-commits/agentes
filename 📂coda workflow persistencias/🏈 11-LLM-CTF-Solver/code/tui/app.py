"""CTFAgentApp — Textual App 入口，管理 Screen 栈和全局状态。"""
import logging
import os
from textual.app import App
from textual.binding import Binding

logger = logging.getLogger(__name__)


class CTFAgentApp(App):
    """CTF Agent TUI 主应用。"""

    CSS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "styles", "theme.tcss")

    BINDINGS = [
        Binding("question_mark", "help", "帮助"),
        Binding("ctrl+q", "quit", "退出"),
    ]

    def on_mount(self):
        from tui.screens.session_list import SessionListScreen
        self.push_screen(SessionListScreen())

    # ── 帮助 ─────────────────────────────────────────────────────

    def action_help(self):
        from tui.modals.help import HelpModal
        shortcuts = [
            ("n", "新建会话"),
            ("Ctrl+K", "知识库管理"),
            ("Enter", "恢复选中会话"),
            ("d", "删除选中会话"),
            ("↑/k  ↓/j", "上下导航"),
            ("Tab", "切换面板焦点"),
            ("Space", "暂停/继续执行 (解题屏)"),
            ("Ctrl+S", "存档当前进度"),
            ("Ctrl+Q", "退出"),
            ("?", "显示此帮助"),
        ]
        self.push_screen(HelpModal("快捷键帮助", shortcuts))

    # ── 供 TextualUserInterface 回调 ─────────────────────────────

    def add_log_line(self, text: str):
        """由 TextualUserInterface.display() 调用 — 在主线程追加日志。"""
        try:
            current = self.screen
            if hasattr(current, 'add_log_line'):
                current.add_log_line(text)
        except Exception as e:
            logger.debug("app.add_log_line 失败: %s", e)
