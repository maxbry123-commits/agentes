"""pytest 全局配置 — 将项目根目录加入 sys.path。"""

import sys
import os

# 将项目根目录加入导入路径，使测试代码可以直接 `from ctf_tool.xxx import ...`
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
