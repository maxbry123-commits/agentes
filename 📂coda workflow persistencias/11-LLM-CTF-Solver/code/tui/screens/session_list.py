"""SessionListScreen — 会话列表屏，启动默认屏：新建/恢复/删除会话。"""
import json
from datetime import datetime
from textual.screen import Screen
from textual.widgets import Header, Footer, ListView, ListItem, Label, Button
from textual.containers import Vertical, Horizontal
from textual.binding import Binding

from agent.checkpoint import CheckpointManager


class SessionListScreen(Screen):
    """会话列表屏 — 浏览历史 checkpoint、新建会话。"""

    BINDINGS = [
        Binding("n", "new_session", "新建会话"),
        Binding("enter", "resume_session", "恢复选中"),
        Binding("d", "delete_session", "删除选中"),
        Binding("ctrl+k", "knowledge_base", "知识库"),
        Binding("ctrl+q", "quit", "退出"),
    ]

    def compose(self):
        yield Header()
        with Vertical(id="session-container"):
            yield Label("[bold]历史会话[/]", id="session-title")
            yield ListView(id="session-list")
            with Horizontal(id="session-buttons"):
                yield Button("新建会话", variant="primary", id="new-btn")
                yield Button("恢复会话", variant="success", id="resume-btn")
                yield Button("删除", variant="error", id="delete-btn")
                yield Button("知识库", variant="warning", id="kb-btn")
        yield Footer()

    def on_mount(self):
        self.query_one(Header).sub_title = "CTF Agent TUI"
        self._refresh_list()

    def _refresh_list(self):
        lst = self.query_one("#session-list", ListView)
        lst.clear()
        checkpoints = CheckpointManager.list_checkpoints()
        if not checkpoints:
            lst.append(ListItem(Label("[dim](无历史会话)[/]")))
            return
        for ck in checkpoints:
            ts = datetime.fromtimestamp(ck['created_at']).strftime("%m-%d %H:%M")
            label = f"[{ck['mode'].upper()}] {ck['summary']} ({ts})"
            lst.append(ListItem(Label(label)))
        self._checkpoints = checkpoints

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "new-btn":
            self.action_new_session()
        elif event.button.id == "resume-btn":
            self.action_resume_session()
        elif event.button.id == "delete-btn":
            self.action_delete_session()
        elif event.button.id == "kb-btn":
            self.action_knowledge_base()

    def action_new_session(self):
        from tui.screens.new_session import NewSessionScreen
        self.app.push_screen(NewSessionScreen())

    def action_knowledge_base(self):
        from tui.screens.knowledge_base import KnowledgeBaseScreen
        self.app.push_screen(KnowledgeBaseScreen())

    def action_resume_session(self):
        lst = self.query_one("#session-list", ListView)
        if lst.index is not None and hasattr(self, '_checkpoints'):
            idx = lst.index
            if 0 <= idx < len(self._checkpoints):
                ck = self._checkpoints[idx]
                self._start_solve_from_checkpoint(ck)

    def action_delete_session(self):
        lst = self.query_one("#session-list", ListView)
        if lst.index is not None and hasattr(self, '_checkpoints'):
            idx = lst.index
            if 0 <= idx < len(self._checkpoints):
                ck = self._checkpoints[idx]
                from tui.modals.confirm import ConfirmModal
                self.app.push_screen(
                    ConfirmModal(f"确认删除会话: {ck['summary']}?", "删除", "取消"),
                    lambda result: self._do_delete(ck) if result else None,
                )

    def _do_delete(self, ck: dict):
        CheckpointManager.remove(ck["path"])
        self.notify(f"已删除: {ck['summary']}")
        self._refresh_list()

    def _start_solve_from_checkpoint(self, ck: dict):
        path = ck["path"]
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            self.notify("无法加载 checkpoint", severity="error")
            return
        mode = data["meta"]["mode"]
        problem = data["meta"]["problem_text"]
        # 从存档恢复交互模式（旧 checkpoint 可能无此字段，默认自动）
        auto_mode = data.get("agent_state", {}).get("auto_mode", True)
        from tui.screens.solve import SolveScreen
        self.app.push_screen(SolveScreen(mode, problem, checkpoint_data=data,
                                          auto_mode=auto_mode))
