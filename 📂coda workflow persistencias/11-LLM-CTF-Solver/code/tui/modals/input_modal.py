"""InputModal — 自由文本输入弹窗，供 TextualUserInterface.prompt_text() 使用。"""
from textual.screen import ModalScreen
from textual.widgets import Label, Input, Button
from textual.containers import Vertical, Horizontal


class InputModal(ModalScreen[str]):
    """自由文本输入弹窗。dismiss(text) 返回用户输入的文本，取消返回空字符串。"""

    def __init__(self, prompt: str):
        super().__init__()
        self._prompt = prompt

    def compose(self):
        with Vertical(id="input-modal"):
            yield Label(self._prompt, id="input-prompt")
            yield Input(id="input-field")
            with Horizontal(id="input-buttons"):
                yield Button("确认", variant="primary", id="input-ok")
                yield Button("取消", variant="error", id="input-cancel")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "input-ok":
            value = self.query_one("#input-field", Input).value
            self.dismiss(value)
        else:
            self.dismiss("")
