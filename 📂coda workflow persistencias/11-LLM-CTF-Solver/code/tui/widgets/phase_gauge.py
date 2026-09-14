"""PhaseGauge — 阶段进度指示器，显示当前阶段名称和步数。"""
from textual.widgets import Static
from textual.containers import Vertical


class PhaseGauge(Vertical):
    """阶段进度指示器 — 显示当前阶段名称、色条和步数。"""

    PHASES = {
        "recon": ("信息收集", "cyan"),
        "exploit": ("漏洞利用", "yellow"),
        "report": ("报告收尾", "green"),
    }

    def __init__(self):
        super().__init__(id="phase-gauge")
        self._phase = "recon"
        self._step_count = 0

    def compose(self):
        yield Static("", id="phase-label")
        yield Static("", id="phase-bar")
        yield Static("", id="phase-step")

    def update(self, phase: str, step_count: int):
        self._phase = phase
        self._step_count = step_count
        phase_name, color = self.PHASES.get(phase, ("未知", "dim"))
        bar_width = 20
        filled = min(step_count // 3, bar_width)
        bar = f"[{color}]{'█' * filled}{'░' * (bar_width - filled)}[/]"
        self.query_one("#phase-label", Static).update(f"[bold {color}]{phase_name}[/]")
        self.query_one("#phase-bar", Static).update(bar)
        self.query_one("#phase-step", Static).update(f"[{color}]第 {step_count} 步[/]")
