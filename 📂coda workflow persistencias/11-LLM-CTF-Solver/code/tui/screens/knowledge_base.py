"""KnowledgeBaseScreen — RAG 知识库管理屏：搜索/浏览/添加/删除。"""
import logging
from textual.screen import Screen
from textual.widgets import Header, Footer, ListView, ListItem, Label, Input, Button, Static
from textual.containers import Vertical, Horizontal
from textual.binding import Binding

logger = logging.getLogger(__name__)


class KnowledgeBaseScreen(Screen):
    """知识库管理屏 — 浏览、搜索、添加、删除知识条目。"""

    BINDINGS = [
        Binding("ctrl+q", "quit", "返回"),
        Binding("slash", "focus_search", "搜索"),
        Binding("d", "delete_entry", "删除选中"),
        Binding("n", "add_entry", "添加条目"),
        Binding("r", "refresh", "刷新列表"),
        Binding("question_mark", "help", "帮助"),
    ]

    def __init__(self):
        super().__init__()
        self._entries: list = []     # 所有条目 [{id, content, metadata}]
        self._kb = None              # KnowledgeBase 实例
        self._kb_available = False

    # ── 布局 ──────────────────────────────────────────────────────

    def compose(self):
        yield Header()
        with Horizontal(id="kb-body"):
            with Vertical(id="kb-left"):
                with Horizontal(id="kb-search-bar"):
                    yield Input(placeholder="搜索知识库...", id="kb-search-input")
                    yield Button("搜索", variant="primary", id="kb-search-btn")
                    yield Button("全部", variant="default", id="kb-all-btn")
                yield ListView(id="kb-list")
                with Horizontal(id="kb-actions"):
                    yield Button("添加条目 (n)", variant="success", id="kb-add-btn")
                    yield Button("删除选中 (d)", variant="error", id="kb-del-btn")
            with Vertical(id="kb-right"):
                yield Static("选择一个条目查看详情", id="kb-detail")
        yield Static("", id="stats-bar")
        yield Footer()

    def on_mount(self):
        self.query_one(Header).sub_title = "知识库管理"
        self._init_kb()
        self._load_all()

    # ── 知识库初始化 ──────────────────────────────────────────────

    def _init_kb(self):
        try:
            from rag.knowledge_base import KnowledgeBase
            self._kb = KnowledgeBase()
            self._kb_available = self._kb.collection is not None
        except Exception as e:
            logger.warning("知识库初始化失败: %s", e)
            self._kb_available = False
            self.query_one("#kb-detail", Static).update(
                "[bold red]知识库不可用[/]\n\n"
                "请检查:\n"
                "1. chromadb 是否已安装\n"
                "2. 向量存储目录是否可访问"
            )

    # ── 数据加载 ──────────────────────────────────────────────────

    def _load_all(self):
        """加载所有条目。"""
        self._entries = []
        lst = self.query_one("#kb-list", ListView)
        lst.clear()

        if not self._kb_available or self._kb is None:
            lst.append(ListItem(Label("[dim]知识库不可用[/]")))
            self._update_footer()
            return

        try:
            data = self._kb.collection.get(limit=200)
        except Exception as e:
            logger.warning("获取知识库条目失败: %s", e)
            lst.append(ListItem(Label("[dim]加载失败[/]")))
            self._update_footer()
            return

        if not data or not data.get("ids"):
            lst.append(ListItem(Label("[dim](知识库为空)[/]")))
            self._update_footer()
            return

        ids = data["ids"]
        docs = data.get("documents", [])
        metas = data.get("metadatas", [])

        for i in range(len(ids)):
            entry = {
                "id": ids[i],
                "content": docs[i] if i < len(docs) else "",
                "metadata": metas[i] if i < len(metas) else {},
            }
            self._entries.append(entry)
            lst.append(ListItem(Label(self._format_entry(entry))))

        self._update_footer()

    def _do_search(self):
        """执行搜索。"""
        query = self.query_one("#kb-search-input", Input).value.strip()
        lst = self.query_one("#kb-list", ListView)
        lst.clear()

        if not query:
            self._load_all()
            return

        if not self._kb_available or self._kb is None:
            return

        try:
            results = self._kb.search_knowledge(query, n_results=20)
        except Exception as e:
            logger.warning("搜索失败: %s", e)
            lst.append(ListItem(Label("[dim]搜索失败[/]")))
            self._update_footer()
            return

        self._entries = []
        if not results:
            lst.append(ListItem(Label("[dim]无匹配结果[/]")))
        else:
            for r in results:
                entry = {
                    "id": r.get("metadata", {}).get("id", ""),
                    "content": r.get("content", ""),
                    "metadata": r.get("metadata", {}),
                    "score": r.get("relevance_score", 0),
                }
                self._entries.append(entry)
                score_str = f" [{r.get('relevance_score', 0):.0%}]"
                lst.append(ListItem(Label(self._format_entry(entry) + score_str)))

        self._update_footer()

    # ── 条目格式化 ────────────────────────────────────────────────

    @staticmethod
    def _format_entry(entry: dict) -> str:
        meta = entry.get("metadata", {})
        etype = meta.get("type", "unknown")
        if etype == "tool_knowledge":
            prefix = "[bold cyan]工具[/]"
            name = meta.get("tool_name", "")
            return f"{prefix} {name}" if name else f"{prefix} 工具知识"
        elif etype == "general_knowledge" or etype == "seed_knowledge":
            tags = meta.get("tags", "")
            tag_str = f" [{tags}]" if tags else ""
            prefix = "[bold green]通用[/]"
            return f"{prefix}{tag_str}"
        else:
            content = entry.get("content", "")
            preview = content[:60].replace("\n", " ")
            return f"[dim]{preview}[/]"

    # ── 详情展示 ──────────────────────────────────────────────────

    def _show_detail(self, entry: dict):
        meta = entry.get("metadata", {})
        etype = meta.get("type", "unknown")
        content = entry.get("content", "")
        entry_id = entry.get("id", "")

        lines = [
            f"[bold]ID:[/] {entry_id}",
            f"[bold]类型:[/] {etype}",
        ]

        if etype == "tool_knowledge":
            lines.append(f"[bold]工具名:[/] {meta.get('tool_name', '?')}")
        if meta.get("tags"):
            lines.append(f"[bold]标签:[/] {meta.get('tags', '')}")
        if meta.get("timestamp"):
            lines.append(f"[bold]时间:[/] {meta.get('timestamp', '')[:19]}")
        if meta.get("category"):
            lines.append(f"[bold]分类:[/] {meta.get('category', '')}")
        if entry.get("score") is not None:
            lines.append(f"[bold]相关度:[/] {entry['score']:.1%}")

        lines.append("")
        lines.append(f"[bold]内容:[/]\n{content}")

        self.query_one("#kb-detail", Static).update("\n".join(lines))

    def _update_footer(self):
        try:
            total = len(self._entries)
            text = f"共 {total} 条" + (" | 知识库不可用" if not self._kb_available else "")
            self.query_one("#stats-bar", Static).update(text)
        except Exception:
            pass

    # ── 事件处理 ──────────────────────────────────────────────────

    def on_button_pressed(self, event: Button.Pressed) -> None:
        bid = event.button.id
        if bid == "kb-search-btn":
            self._do_search()
        elif bid == "kb-all-btn":
            self.query_one("#kb-search-input", Input).value = ""
            self._load_all()
        elif bid == "kb-add-btn":
            self.action_add_entry()
        elif bid == "kb-del-btn":
            self.action_delete_entry()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "kb-search-input":
            self._do_search()

    def on_list_view_highlighted(self, event: ListView.Highlighted) -> None:
        """选中条目时显示详情。"""
        if event.item is None:
            return
        idx = self.query_one("#kb-list", ListView).index
        if idx is not None and 0 <= idx < len(self._entries):
            self._show_detail(self._entries[idx])

    # ── 快捷键动作 ────────────────────────────────────────────────

    def action_focus_search(self):
        self.query_one("#kb-search-input", Input).focus()

    def action_add_entry(self):
        if not self._kb_available:
            self.notify("知识库不可用", severity="error")
            return
        from tui.modals.add_knowledge import AddKnowledgeModal
        self.app.push_screen(AddKnowledgeModal(), self._on_add_done)

    def _on_add_done(self, data: dict | None):
        if not data or not self._kb:
            return
        try:
            if data["type"] == "tool":
                self._kb.add_tool_knowledge(
                    tool_name=data["tool_name"],
                    usage_examples=data.get("usage_examples", []),
                )
            else:
                self._kb.add_general_knowledge(
                    content=data["content"],
                    tags=data.get("tags", []),
                )
            self.notify("条目已添加", title="成功", severity="information")
            self._load_all()
        except Exception as e:
            logger.warning("添加条目失败: %s", e)
            self.notify(f"添加失败: {e}", title="错误", severity="error")

    def action_delete_entry(self):
        if not self._kb_available or not self._kb:
            self.notify("知识库不可用", severity="error")
            return
        lst = self.query_one("#kb-list", ListView)
        if lst.index is None or lst.index >= len(self._entries):
            self.notify("请先选择要删除的条目", severity="warning")
            return
        entry = self._entries[lst.index]
        from tui.modals.confirm import ConfirmModal
        preview = entry.get("content", "")[:60].replace("\n", " ")
        self.app.push_screen(
            ConfirmModal(f"确认删除此条目?\n\n{preview}", "删除", "取消"),
            lambda result: self._do_delete(entry) if result else None,
        )

    def _do_delete(self, entry: dict):
        if not self._kb:
            return
        try:
            self._kb.collection.delete(ids=[entry["id"]])
            self.notify("条目已删除", title="成功", severity="information")
            self._load_all()
            self.query_one("#kb-detail", Static).update("选择一个条目查看详情")
        except Exception as e:
            logger.warning("删除条目失败: %s", e)
            self.notify(f"删除失败: {e}", title="错误", severity="error")

    def action_refresh(self):
        self.query_one("#kb-search-input", Input).value = ""
        self._load_all()
        self.query_one("#kb-detail", Static).update("选择一个条目查看详情")

    def action_help(self):
        from tui.modals.help import HelpModal
        shortcuts = [
            ("/", "聚焦搜索框"),
            ("Enter", "搜索 / 查看详情"),
            ("n", "添加知识条目"),
            ("d", "删除选中条目"),
            ("r", "刷新列表"),
            ("Ctrl+Q", "返回会话列表"),
            ("?", "显示此帮助"),
        ]
        self.push_screen(HelpModal("知识库管理快捷键", shortcuts))

    def action_quit(self):
        self.dismiss()
