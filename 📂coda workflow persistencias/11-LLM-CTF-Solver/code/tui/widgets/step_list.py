"""StepListView — 步骤列表，左侧面板用 ListView 展示步骤摘要。"""
from textual.widgets import ListView, ListItem, Label
from textual.binding import Binding
from textual.message import Message

from tui.snapshot import StepSnapshot


class StepListView(ListView):
    """步骤列表 — 每行显示步骤号 + 摘要，选中项在右侧详情面板渲染。"""

    BINDINGS = [
        Binding("up,k", "cursor_up", "上一条"),
        Binding("down,j", "cursor_down", "下一条"),
        Binding("enter", "select_step", "查看详情"),
    ]

    def on_mount(self):
        self.border_title = "步骤列表"

    def add_step_snapshot(self, snap: StepSnapshot):
        label = self._format_label(snap)
        self.append(ListItem(Label(label)))
        self.index = len(self) - 1

    def action_select_step(self):
        self.post_message(self.SelectHighlighted())

    class SelectHighlighted(Message):
        """选中当前高亮步骤的消息。"""

    @staticmethod
    def _format_label(snap: StepSnapshot) -> str:
        if snap.flag_found:
            return f"[bold gold1]#{snap.step_num:02d} FLAG FOUND[/]"
        if snap.vulnerability and isinstance(snap.vulnerability, dict):
            sev = snap.vulnerability.get("severity", "")
            if sev in ("critical", "high"):
                vtype = snap.vulnerability.get("type", "?")
                return f"[bold red]#{snap.step_num:02d} {vtype}[/]"
        if snap.stuck_warning:
            return f"[yellow]#{snap.step_num:02d} 僵局[/]"
        phase_icon = {"recon": "S", "exploit": "E", "report": "R"}.get(snap.phase, ".")
        think_preview = snap.think[:40].replace("\n", " ") if snap.think else ""
        return f"#{snap.step_num:02d} [{phase_icon}] {think_preview}"
