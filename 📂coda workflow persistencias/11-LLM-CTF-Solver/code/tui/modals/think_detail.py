"""ThinkDetailModal — 查看完整思考内容弹窗。"""
from textual.screen import ModalScreen
from textual.widgets import RichLog, Button
from textual.containers import Vertical


class ThinkDetailModal(ModalScreen[None]):
    """展示完整思考内容（不受 500 字符截断限制，支持滚动）。"""

    def __init__(self, think_text: str):
        super().__init__()
        self._think_text = think_text

    def compose(self):
        with Vertical(id="think-detail-modal"):
            yield RichLog(self._think_text, id="think-full-content", highlight=True)
            yield Button("关闭 (Esc)", variant="primary", id="think-close")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss()

    def key_escape(self) -> None:
        self.dismiss()
