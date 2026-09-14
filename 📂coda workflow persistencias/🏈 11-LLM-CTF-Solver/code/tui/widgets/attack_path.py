"""AttackPathWidget — 攻击路径 ASCII 可视化。"""
from textual.widgets import RichLog
from textual.containers import Vertical
from textual.widgets import Static


class AttackPathWidget(Vertical):
    """攻击路径可视化 — 用 ASCII 流程图展示从侦察到利用的完整攻击链。"""

    PHASE_ICONS = {"recon": "S", "exploit": "E", "report": "R"}
    PHASE_COLORS = {"recon": "cyan", "exploit": "yellow", "report": "green"}
    SEVERITY_ICONS = {"critical": "!!", "high": "! ", "medium": "- ",
                      "low": "  ", "info": "  "}

    def compose(self):
        yield Static("[bold]攻击路径[/]", id="attack-path-title")
        yield RichLog(markup=True, id="attack-path-log", max_lines=200, wrap=True)

    def on_mount(self):
        self.border_title = "攻击路径"
        self._last_step_count = 0

    def update_from_snapshots(self, snapshots: list):
        """基于步骤快照列表刷新攻击路径图（增量更新）。"""
        log = self.query_one("#attack-path-log", RichLog)
        new_count = len(snapshots)
        if new_count <= self._last_step_count:
            return
        # 只渲染新增的步骤
        for snap in snapshots[self._last_step_count:]:
            self._render_step(log, snap)
        self._last_step_count = new_count

    def _render_step(self, log: RichLog, snap):
        pc = self.PHASE_COLORS.get(snap.phase, "dim")
        pi = self.PHASE_ICONS.get(snap.phase, "?")

        # 步骤头
        header = f"[bold {pc}]#{snap.step_num:02d} [{pi}] {self._phase_label(snap.phase)}[/]"

        # 漏洞标记
        if snap.vulnerability and isinstance(snap.vulnerability, dict):
            sev = snap.vulnerability.get("severity", "info")
            vtype = snap.vulnerability.get("type", "?")
            si = self.SEVERITY_ICONS.get(sev, "  ")
            sev_color = {"critical": "bold red", "high": "red",
                         "medium": "yellow", "low": "dim", "info": "dim"}.get(sev, "dim")
            header += f"  [{sev_color}]{si} {sev.upper()}: {vtype}[/]"

        # Flag 标记
        if snap.flag_found:
            header += "  [bold gold1]FLAG[/]"

        log.write(header)

        # 工具调用摘要
        if snap.tool_calls:
            tool_names = [tc.get("tool_name", "?") for tc in snap.tool_calls]
            log.write(f"  [dim]工具: {', '.join(tool_names)}[/]")

        # 关键输出摘要（从 think 或 output 提取一行摘要）
        summary = self._extract_summary(snap)
        if summary:
            log.write(f"  [dim]{summary}[/]")

        # 阶段间分隔符
        log.write("")

    @staticmethod
    def _phase_label(phase: str) -> str:
        return {"recon": "侦察", "exploit": "利用", "report": "报告"}.get(phase, phase)

    @staticmethod
    def _extract_summary(snap) -> str:
        """从快照中提取一行摘要信息。"""
        # 优先使用 think 的前 80 字符
        if snap.think:
            clean = snap.think.strip().split("\n")[0][:80]
            if clean:
                return clean
        # 回退到 output 的第一行
        if snap.output:
            first_line = snap.output.strip().split("\n")[0][:80]
            if first_line:
                return first_line
        return ""
