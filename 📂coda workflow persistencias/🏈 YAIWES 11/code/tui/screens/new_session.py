"""NewSessionScreen — 新建会话屏：输入题目/授权范围 + 选择模式。"""
import os
from textual.screen import Screen
from textual.widgets import Header, Footer, Label, TextArea, Button, RadioSet, RadioButton
from textual.containers import Vertical, Horizontal
from textual.binding import Binding


class NewSessionScreen(Screen):
    """新建会话屏 — 输入题目或授权范围文本，选择 CTF/Pentest 模式。"""

    BINDINGS = [
        Binding("ctrl+q", "quit", "退出"),
    ]

    def compose(self):
        yield Header()
        with Vertical(id="new-session-container"):
            yield Label("[bold]新建会话[/]", id="ns-title")

            yield Label("运行模式:")
            with RadioSet(id="ns-mode"):
                yield RadioButton("CTF 解题", value="ctf")
                yield RadioButton("渗透测试", value="pentest")

            yield Label("交互模式:")
            with RadioSet(id="ns-auto-mode"):
                yield RadioButton("自动模式 (推荐)", value=True)
                yield RadioButton("手动模式 (每步确认)", value=False)

            yield Label("题目/授权范围文本 (可直接粘贴):")
            yield TextArea(id="ns-problem")

            with Horizontal(id="ns-buttons"):
                yield Button("从 question.txt 加载", variant="default", id="ns-load-file")
                yield Button("开始执行", variant="primary", id="ns-start")
                yield Button("返回", variant="error", id="ns-back")
        yield Footer()

    def on_mount(self):
        self.query_one(Header).sub_title = "新建会话"
        # 尝试预加载 question.txt
        self._try_load_file()

    def _try_load_file(self):
        for fname in ("question.txt", "scope.txt"):
            if os.path.isfile(fname):
                try:
                    with open(fname, "r", encoding="utf-8") as f:
                        content = f.read()
                    if content.strip():
                        self.query_one("#ns-problem", TextArea).text = content
                        return
                except Exception:
                    pass

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "ns-start":
            self._start()
        elif event.button.id == "ns-load-file":
            self._try_load_file()
        elif event.button.id == "ns-back":
            self.dismiss()

    def _start(self):
        mode_set = self.query_one("#ns-mode", RadioSet)
        mode = "ctf"
        if mode_set.pressed_button is not None:
            mode = mode_set.pressed_button.value or "ctf"

        auto_set = self.query_one("#ns-auto-mode", RadioSet)
        auto_mode = True  # 默认自动
        if auto_set.pressed_button is not None:
            auto_mode = auto_set.pressed_button.value is True

        problem = self.query_one("#ns-problem", TextArea).text.strip()
        if not problem:
            self.notify("请先输入题目或授权范围文本", severity="error")
            return

        # 保存到对应文件
        input_file = "scope.txt" if mode == "pentest" else "question.txt"
        try:
            with open(input_file, "w", encoding="utf-8") as f:
                f.write(problem)
        except Exception:
            pass

        from tui.screens.solve import SolveScreen
        self.app.push_screen(SolveScreen(mode, problem, auto_mode=auto_mode))
