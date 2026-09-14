"""CTF Agent TUI 入口 — 使用 Textual 框架的终端 UI。

启动方式:
    python tui_main.py

依赖:
    pip install textual>=1.0.0
"""
import sys
import os

# 确保项目根目录在 sys.path 中
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tui.app import CTFAgentApp


def main():
    app = CTFAgentApp()
    app.run()


if __name__ == "__main__":
    main()
