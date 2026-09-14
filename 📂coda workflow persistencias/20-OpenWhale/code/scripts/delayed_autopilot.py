"""延时遥控脚本：等待后启动智能体，并循环运行直到赛题全部完成。"""

from __future__ import annotations

import asyncio
import json
import os
import shlex
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

from openwhale.util.mcp_client import call_tool, create_mcp_session


def _extract_result_text(result: Any) -> str:
    if result is None:
        return ""

    if hasattr(result, "content"):
        content = result.content
        if isinstance(content, list):
            parts: list[str] = []
            for item in content:
                text = getattr(item, "text", None)
                if text:
                    parts.append(text)
                else:
                    parts.append(str(item))
            return "\n".join(parts)
        return str(content)

    return str(result)


async def _list_challenges(mcp_url: str, agent_token: str) -> dict[str, Any]:
    async with create_mcp_session(mcp_url, agent_token=agent_token) as session:
        result = await call_tool(session, "list_challenges", {})
    text = _extract_result_text(result)
    data = json.loads(text)
    if not isinstance(data, dict):
        raise ValueError("list_challenges 返回格式异常")
    return data


def _build_config() -> dict[str, Any]:
    load_dotenv()

    server_host = os.getenv("SERVER_HOST", "").strip()
    mcp_url = os.getenv("MCP_SERVER_URL", "").strip()
    if not mcp_url and server_host:
        if server_host.startswith("http://") or server_host.startswith("https://"):
            mcp_url = f"{server_host.rstrip('/')}/mcp"
        else:
            mcp_url = f"http://{server_host.rstrip('/')}/mcp"

    config = {
        "agent_token": os.getenv("AGENT_TOKEN", "").strip(),
        "mcp_url": mcp_url,
        "start_delay": int(os.getenv("AUTOPILOT_START_DELAY_SECONDS", "60")),
        "cycle_interval": int(os.getenv("AUTOPILOT_CYCLE_INTERVAL_SECONDS", "5")),
        "max_cycles": int(os.getenv("AUTOPILOT_MAX_CYCLES", "0")),
        "command": os.getenv("AUTOPILOT_AGENT_COMMAND", "uv run openwhale").strip(),
    }

    missing = [k for k in ("agent_token", "mcp_url") if not config[k]]
    if missing:
        raise ValueError(f"缺少必要配置: {', '.join(missing)}")

    return config


def _run_agent_once(command: str, cwd: Path) -> int:
    print(f"\n[autopilot] 启动智能体命令: {command}")
    args = shlex.split(command)
    process = subprocess.run(args, cwd=str(cwd), check=False)
    return process.returncode


async def _main() -> int:
    config = _build_config()
    project_root = Path(__file__).resolve().parents[1]

    delay = config["start_delay"]
    if delay > 0:
        print(f"[autopilot] 已启动，{delay} 秒后开始首轮执行...")
        time.sleep(delay)

    cycle = 0
    while True:
        data = await _list_challenges(config["mcp_url"], config["agent_token"])
        total = int(data.get("total_challenges", 0))
        solved = int(data.get("solved_challenges", 0))
        print(f"[autopilot] 当前完成进度: {solved}/{total}")

        if total > 0 and solved >= total:
            print("[autopilot] 所有赛题已完成，停止循环。")
            return 0

        cycle += 1
        max_cycles = config["max_cycles"]
        if max_cycles > 0 and cycle > max_cycles:
            print(f"[autopilot] 达到最大轮次 {max_cycles}，停止循环。")
            return 0

        return_code = _run_agent_once(config["command"], project_root)
        if return_code != 0:
            print(f"[autopilot] 智能体退出码: {return_code}，将继续下一轮。")

        interval = config["cycle_interval"]
        if interval > 0:
            print(f"[autopilot] 等待 {interval} 秒后进入下一轮...")
            time.sleep(interval)


def main() -> None:
    try:
        code = asyncio.run(_main())
    except KeyboardInterrupt:
        print("\n[autopilot] 用户中断，已停止。")
        code = 130
    except Exception as exc:  # noqa: BLE001
        print(f"[autopilot] 运行失败: {exc}")
        code = 1

    raise SystemExit(code)


if __name__ == "__main__":
    main()
