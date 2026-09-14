"""SolveScreen — TUI 核心执行屏，管理一个 SolveAgent 会话的完整生命周期。"""
import os
import time
import threading
import logging

from textual import work
from textual.screen import Screen
from textual.widgets import Header, Footer, Static
from textual.containers import Horizontal, Vertical
from textual.binding import Binding

from config import Config, get_project_root
from tui.snapshot import StepSnapshot
from tui.ui_interface import TextualUserInterface
from tui.widgets.phase_gauge import PhaseGauge
from tui.widgets.step_list import StepListView
from tui.widgets.step_detail import StepDetail
from tui.widgets.attack_surface_tree import AttackSurfaceTree
from tui.widgets.attack_path import AttackPathWidget
from agent.solve_agent import SolveAgent
from agent.checkpoint import CheckpointManager

logger = logging.getLogger(__name__)


class SolveScreen(Screen):
    """核心执行屏 — 左侧步骤列表 + 右侧详情面板。"""

    BINDINGS = [
        Binding("ctrl+s", "save_checkpoint", "存档"),
        Binding("space", "toggle_pause", "暂停/继续"),
        Binding("question_mark", "help", "帮助"),
        Binding("ctrl+q", "quit", "退出"),
        Binding("tab", "focus_next", "切换面板"),
    ]

    def __init__(self, mode: str, problem: str, checkpoint_data: dict = None,
                 auto_mode: bool = False):
        super().__init__()
        self._mode = mode
        self._problem = problem
        self._checkpoint_data = checkpoint_data
        self._auto_mode = auto_mode
        self._snapshots: list = []
        self._ui = None           # TextualUserInterface, created in on_mount
        self._agent = None        # SolveAgent, created in worker thread
        self._start_time = 0.0
        self._pause_event = threading.Event()
        self._pause_event.set()   # 初始状态：运行中（set = 不阻塞）
        self._paused = False
        self._stop_event = threading.Event()

    # ── 布局 ──────────────────────────────────────────────────────

    def compose(self):
        yield Header()
        with Horizontal(id="solve-body"):
            with Vertical(id="left-panel"):
                yield PhaseGauge()
                yield StepListView(id="step-list")
                yield AttackSurfaceTree("根", id="attack-surface-tree")
                yield AttackPathWidget(id="attack-path")
            with Vertical(id="right-panel"):
                yield StepDetail(id="step-detail")
        yield Static("", id="stats-bar")
        yield Footer()

    def on_mount(self):
        self.query_one(Header).sub_title = (
            f"[{self._mode.upper()}] {'自动' if self._auto_mode else '手动'}模式"
        )
        # 渗透模式显示攻击面树
        if self._mode != "pentest":
            tree = self.query_one("#attack-surface-tree", AttackSurfaceTree)
            tree.display = False
        # 启动前占位状态
        self.query_one("#stats-bar", Static).update("[dim]正在初始化 Agent...[/]")
        # 启动 solve worker
        self._start_time = time.time()
        self._ui = TextualUserInterface(self.app)
        self._run_solve()

    # ── Worker 线程 ───────────────────────────────────────────────

    @work(thread=True)
    async def _run_solve(self):
        """在 worker 线程中运行 solve() 主循环。"""
        config = Config.load_config()
        # 注入步骤回调
        agent = SolveAgent(
            problem=self._problem,
            agent_options={"auto_mode": self._auto_mode, "stop_event": self._stop_event},
            knowledge_base=None,  # Workflow 负责知识库，TUI 直接调 Agent 时跳过
            mode=self._mode,
            checkpoint_data=self._checkpoint_data,
            ui=self._ui,
        )
        self._agent = agent
        agent._on_step_done = self._make_step_callback()
        # 确认回调
        if self._mode == "ctf":
            agent.confirm_flag_callback = self._tui_confirm_flag

        try:
            result = agent.solve()
        except Exception as e:
            logger.exception("solve() 异常")
            result = f"解题异常: {e}"
        self.app.call_from_thread(self._show_result, result)

    def _make_step_callback(self):
        """构建步骤回调 — 在 worker 线程被调用时安全推送快照到主线程。"""
        app_ref = self.app
        pause_ev = self._pause_event

        def on_step(snap: StepSnapshot):
            app_ref.call_from_thread(self._on_step_snapshot, snap)
            # 暂停检查：如果 pause_event 被 clear，worker 在此阻塞
            pause_ev.wait()

        return on_step

    # ── 主线程 UI 更新 ────────────────────────────────────────────

    def _on_step_snapshot(self, snap: StepSnapshot):
        """在主线程中安全更新所有 Widget。"""
        self._snapshots.append(snap)
        step_list = self.query_one("#step-list", StepListView)
        step_list.add_step_snapshot(snap)

        self.query_one("#step-detail", StepDetail).show_snapshot(snap)

        phase_gauge = self.query_one(PhaseGauge)
        phase_gauge.update(snap.phase, snap.step_num)

        # 攻击面树更新
        if self._mode == "pentest" and self._agent and self._agent.attack_surface:
            try:
                tree = self.query_one("#attack-surface-tree", AttackSurfaceTree)
                tree.update_from_attack_surface(self._agent.attack_surface)
            except Exception:
                pass

        # 攻击路径图更新
        try:
            self.query_one("#attack-path", AttackPathWidget).update_from_snapshots(
                self._snapshots
            )
        except Exception:
            pass

        # Footer 统计（已在主线程，直接更新）
        self._update_footer(snap.step_num, snap.phase, snap.cache_stats,
                           snap.token_stats)

    def on_step_list_view_select_highlighted(self, event: StepListView.SelectHighlighted):
        """用户选中历史步骤时，回看对应详情。"""
        step_list = self.query_one("#step-list", StepListView)
        if step_list.index is not None and 0 <= step_list.index < len(self._snapshots):
            self.query_one("#step-detail", StepDetail).show_snapshot(
                self._snapshots[step_list.index]
            )

    def _show_result(self, result: str):
        """显示解题结果。"""
        elapsed = time.time() - self._start_time
        self.query_one("#step-detail", StepDetail).query_one(
            "#detail-analysis", Static
        ).update(f"[bold green]解题完成 ({elapsed:.1f}s)[/]\n\n{result}")
        self.notify(f"解题完成: {result[:80]}", title="结果", severity="information")

    # ── 公开回调（供 TextualUserInterface 使用） ──────────────────

    def add_log_line(self, text: str):
        """向 StepDetail 的输出区追加日志行。"""
        try:
            detail = self.query_one("#step-detail", StepDetail)
            output_block = detail.query_one("#detail-output")
            if hasattr(output_block, 'write'):
                output_block.write(text + "\n")
        except Exception as e:
            logger.debug("add_log_line 写入失败: %s", e)

    def _tui_confirm_flag(self, flag_candidate: str) -> bool:
        """TUI 环境的 flag 确认（通过 TextualUserInterface 的 confirm）。"""
        if self._auto_mode:
            return True
        return self._ui.confirm(
            f"发现 flag: {flag_candidate}\n请确认这个 flag 是否正确？",
            yes_label="y", no_label="n",
        )

    # ── 快捷键 ────────────────────────────────────────────────────

    def _update_footer(self, step_num: int = 0, phase: str = "",
                       cache_stats: dict = None, token_stats: dict = None):
        cs = cache_stats or {}
        ts = token_stats or {}
        try:
            parts = []
            if self._paused:
                parts.append("[bold yellow]⏸ 已暂停[/]")
            if step_num:
                parts.append(f"Step {step_num}")
            if phase:
                parts.append(f"Phase: {phase}")
            # Token 用量
            total_t = ts.get("total_tokens", 0)
            cost = ts.get("cost", 0)
            if total_t:
                if total_t >= 1000:
                    parts.append(f"Token: {total_t/1000:.1f}K")
                else:
                    parts.append(f"Token: {total_t}")
            if cost:
                parts.append(f"${cost:.2f}")
            # 缓存
            parts.append(f"L1:{cs.get('l1', 0)} RAG:{cs.get('rag', 0)}")
            self.query_one("#stats-bar", Static).update(" | ".join(parts))
        except Exception:
            pass

    def action_help(self):
        from tui.modals.help import HelpModal
        shortcuts = [
            ("Space", "暂停/继续 Agent 执行"),
            ("Enter", "查看选中步骤详情"),
            ("↑/k  ↓/j", "浏览步骤列表"),
            ("Tab", "切换左右面板焦点"),
            ("Ctrl+S", "保存 checkpoint 存档"),
            ("Ctrl+Q", "存档并退出"),
            ("?", "显示此帮助"),
        ]
        self.push_screen(HelpModal("解题屏快捷键", shortcuts))

    def action_toggle_pause(self):
        if self._paused:
            self._pause_event.set()
            self._paused = False
        else:
            self._pause_event.clear()
            self._paused = True
        # 基于最后已知快照更新 footer
        last = self._snapshots[-1] if self._snapshots else None
        self._update_footer(
            last.step_num if last else 0,
            last.phase if last else "",
            last.cache_stats if last else {},
            last.token_stats if last else {},
        )
        state = "继续" if not self._paused else "暂停"
        self.notify(f"Agent 已{state}", title="状态", severity="information")

    def action_save_checkpoint(self):
        if self._agent:
            self._agent.save_checkpoint()
            self.notify("Checkpoint 已保存", title="存档")

    def action_quit(self):
        self._stop_event.set()
        self._pause_event.set()  # 解除暂停，让 worker 正常退出
        if self._agent:
            self._agent.save_checkpoint()
        # 等待 worker 线程退出（最长 5s），避免 call_from_thread 异常
        import threading
        for t in threading.enumerate():
            if t is not threading.current_thread() and t.name.startswith("textual_work"):
                t.join(timeout=5)
                break
        self.app.exit()
