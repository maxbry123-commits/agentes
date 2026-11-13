"""AddKnowledgeModal — 添加知识库条目弹窗。"""
from typing import List
from textual.screen import ModalScreen
from textual.widgets import Label, Input, Button, RadioSet, RadioButton
from textual.containers import Vertical, Horizontal


class AddKnowledgeModal(ModalScreen[dict]):
    """添加知识条目弹窗 — 支持工具知识和通用知识两种类型。"""

    def __init__(self):
        super().__init__()
        self._result: dict = {}

    def compose(self):
        with Vertical(id="add-kb-modal"):
            yield Label("[bold]添加知识条目[/]", id="akb-title")

            yield Label("类型:")
            with RadioSet(id="akb-type"):
                yield RadioButton("工具知识", value="tool")
                yield RadioButton("通用知识", value="general")

            yield Label("标签 (逗号分隔):")
            yield Input(placeholder="例如: web, sql, recon", id="akb-tags")

            yield Label("内容:")
            yield Input(placeholder="知识内容或描述", id="akb-content")

            # 工具知识专用字段
            yield Label("工具名称 (工具知识必填):", id="akb-tool-label")
            yield Input(placeholder="例如: nmap", id="akb-tool-name")

            yield Label("使用示例 (分号分隔):", id="akb-examples-label")
            yield Input(placeholder="例如: nmap -sV target; nmap -A target", id="akb-examples")

            with Horizontal(id="akb-buttons"):
                yield Button("添加", variant="primary", id="akb-add")
                yield Button("取消", variant="error", id="akb-cancel")

    def on_mount(self):
        self._toggle_tool_fields()

    def on_radio_set_changed(self, event: RadioSet.Changed) -> None:
        self._toggle_tool_fields()

    def _toggle_tool_fields(self):
        rs = self.query_one("#akb-type", RadioSet)
        is_tool = rs.pressed_button is not None and rs.pressed_button.value == "tool"
        for wid in ("akb-tool-label", "akb-tool-name",
                     "akb-examples-label", "akb-examples"):
            self.query_one(f"#{wid}").display = is_tool

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "akb-cancel":
            self.dismiss(None)
            return

        rs = self.query_one("#akb-type", RadioSet)
        is_tool = rs.pressed_button is not None and rs.pressed_button.value == "tool"
        content = self.query_one("#akb-content", Input).value.strip()
        tags_str = self.query_one("#akb-tags", Input).value.strip()

        if not content:
            self.notify("内容不能为空", severity="error")
            return

        tags = [t.strip() for t in tags_str.split(",") if t.strip()]

        if is_tool:
            tool_name = self.query_one("#akb-tool-name", Input).value.strip()
            if not tool_name:
                self.notify("工具名称不能为空", severity="error")
                return
            examples_str = self.query_one("#akb-examples", Input).value.strip()
            examples = [e.strip() for e in examples_str.split(";") if e.strip()]
            self.dismiss({
                "type": "tool",
                "tool_name": tool_name,
                "content": content,
                "usage_examples": examples,
                "tags": tags,
            })
        else:
            self.dismiss({
                "type": "general",
                "content": content,
                "tags": tags,
            })

    def key_escape(self) -> None:
        self.dismiss(None)
