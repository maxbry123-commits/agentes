"""ChoiceModal — 多选一弹窗，供 TextualUserInterface.choose() 使用。"""
from typing import List
from textual.screen import ModalScreen
from textual.widgets import Label, Button
from textual.containers import Vertical


class ChoiceModal(ModalScreen[str]):
    """多选一弹窗。dismiss(option_text) 返回选中的选项文本。"""

    def __init__(self, prompt: str, options: List[str]):
        super().__init__()
        self._prompt = prompt
        self._options = options

    def compose(self):
        with Vertical(id="choice-modal"):
            yield Label(self._prompt, id="choice-prompt")
            for i, opt in enumerate(self._options):
                yield Button(opt, id=f"choice-{i}")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        idx = int(event.button.id.split("-")[1])
        self.dismiss(self._options[idx])
