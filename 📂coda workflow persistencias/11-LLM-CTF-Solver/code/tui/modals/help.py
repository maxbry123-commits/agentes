"""HelpModal — 快捷键帮助弹窗。"""
from textual.screen import ModalScreen
from textual.widgets import Static, Button
from textual.containers import Vertical


class HelpModal(ModalScreen[None]):
    """显示当前上下文的快捷键列表。"""

    def __init__(self, title: str = "快捷键帮助", shortcuts: list = None):
        super().__init__()
        self._title = title
        self._shortcuts = shortcuts or []

    def compose(self):
        lines = [f"[bold]{self._title}[/]\n"]
        for key, desc in self._shortcuts:
            lines.append(f"  [bold cyan]{key:<16}[/] {desc}")
        text = "\n".join(lines) if len(lines) > 1 else "无可用快捷键"
        with Vertical(id="help-modal"):
            yield Static(text, id="help-content")
            yield Button("关闭 (Esc)", variant="primary", id="help-close")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss()

    def key_escape(self) -> None:
        self.dismiss()
