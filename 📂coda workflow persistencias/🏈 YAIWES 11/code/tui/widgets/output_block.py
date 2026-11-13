"""OutputBlock — 工具输出渲染（RichLog + flag 高亮）。"""
import re
from textual.widgets import RichLog
from textual.widget import Widget


class OutputBlock(RichLog):
    """工具输出渲染 — 自动 flag 高亮 + 超长截断。"""

    def on_mount(self):
        self.border_title = "工具输出"

    def show_output(self, text: str):
        self.clear()
        if not text:
            self.write("[dim](无输出)[/]")
            return
        # flag 红色高亮
        highlighted = re.sub(
            r'(flag\{[^}]+\})', r'[bold red]\1[/]', text, flags=re.I
        )
        if len(highlighted) > 8192:
            highlighted = highlighted[:8192] + "\n\n[dim]... (输出过长已截断)[/]"
        self.write(highlighted)
