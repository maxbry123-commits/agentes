"""ConfirmModal — 确认/取消弹窗，供 TextualUserInterface.confirm() 使用。"""
from textual.screen import ModalScreen
from textual.widgets import Label, Button
from textual.containers import Vertical, Horizontal


class ConfirmModal(ModalScreen[bool]):
    """二元确认弹窗。dismiss(True) 表示确认，dismiss(False) 表示取消。"""

    def __init__(self, prompt: str, yes_label: str = "批准", no_label: str = "取消"):
        super().__init__()
        self._prompt = prompt
        self._yes_label = yes_label
        self._no_label = no_label

    def compose(self):
        with Vertical(id="confirm-modal"):
            yield Label(self._prompt, id="confirm-prompt")
            with Horizontal(id="confirm-buttons"):
                yield Button(self._yes_label, variant="primary", id="yes-btn")
                yield Button(self._no_label, variant="error", id="no-btn")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "yes-btn":
            self.dismiss(True)
        else:
            self.dismiss(False)
