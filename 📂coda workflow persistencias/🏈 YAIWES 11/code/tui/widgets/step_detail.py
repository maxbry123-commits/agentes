"""StepDetail — 步骤详情组合面板（思考 + 工具调用 + 输出 + 分析）。"""
from textual.containers import Vertical
from textual.widgets import Static, Button

from tui.snapshot import StepSnapshot
from tui.widgets.output_block import OutputBlock


class StepDetail(Vertical):
    """步骤详情 — 展示单步的思考/工具/输出/分析四部分，支持折叠。"""

    def compose(self):
        yield Button("▼ 思考", id="toggle-think", classes="section-toggle")
        yield Static("", id="detail-think")
        yield Button("查看完整思考", id="view-full-think", classes="full-view-btn")
        yield Button("▼ 工具调用", id="toggle-tools", classes="section-toggle")
        yield Static("", id="detail-tools")
        yield Button("▼ 输出", id="toggle-output", classes="section-toggle")
        yield OutputBlock(markup=False, id="detail-output")
        yield Button("▼ 分析", id="toggle-analysis", classes="section-toggle")
        yield Static("", id="detail-analysis")

    def on_mount(self):
        self._collapsed = {"think": False, "tools": False,
                           "output": False, "analysis": False}
        self._full_think = ""
        self.query_one("#view-full-think", Button).display = False
        # 初始占位内容 — 等待 Worker 线程产出首步快照
        self.query_one("#detail-think", Static).update("[dim]等待 Agent 初始化...[/]")
        self.query_one("#detail-tools", Static).update("[dim]—[/]")
        self.query_one("#detail-analysis", Static).update("[dim]等待首步完成...[/]")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        btn_id = event.button.id
        if btn_id == "view-full-think":
            self._show_full_think()
            return
        mapping = {
            "toggle-think": "detail-think",
            "toggle-tools": "detail-tools",
            "toggle-output": "detail-output",
            "toggle-analysis": "detail-analysis",
        }
        target_id = mapping.get(btn_id)
        if target_id:
            key = target_id.replace("detail-", "")
            self._collapsed[key] = not self._collapsed[key]
            widget = self.query_one(f"#{target_id}")
            widget.display = not self._collapsed[key]
            labels = {"think": "思考", "tools": "工具调用",
                      "output": "输出", "analysis": "分析"}
            icon = "▶" if self._collapsed[key] else "▼"
            event.button.label = f"{icon} {labels[key]}"

    def show_snapshot(self, snap: StepSnapshot):
        # 思考
        think_text = snap.think if snap.think else "(无)"
        self._full_think = snap.think
        self.query_one("#detail-think", Static).update(think_text[:500])
        self.query_one("#view-full-think", Button).display = len(snap.think) > 500

        # 工具调用
        if snap.tool_calls:
            tool_lines = []
            for tc in snap.tool_calls:
                name = tc.get("tool_name", "?")
                args = tc.get("arguments", {})
                args_str = ", ".join(f"{k}={v}" for k, v in list(args.items())[:3])
                tool_lines.append(f"  {name}({args_str})")
            tools_text = "\n".join(tool_lines)
        else:
            tools_text = "(无)"
        self.query_one("#detail-tools", Static).update(tools_text)

        # 输出
        self.query_one("#detail-output", OutputBlock).show_output(snap.output)

        # 分析
        analysis_text = snap.analysis[:1024] if snap.analysis else "(等待分析...)"
        self.query_one("#detail-analysis", Static).update(analysis_text)

    def _show_full_think(self):
        from tui.modals.think_detail import ThinkDetailModal
        if self._full_think:
            self.app.push_screen(ThinkDetailModal(self._full_think))
