"""工具与权限配置辅助模块。"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from loguru import logger


def parse_csv(value: str) -> list[str]:
    """将逗号分隔字符串解析为列表。"""
    return [item.strip() for item in value.split(",") if item.strip()]


def default_allowed_tools(challenge_server_name: str = "challenge") -> list[str]:
    """默认自动授权工具：包含 Bash 和挑战赛 MCP 工具。"""
    return [
        "Bash",
        f"mcp__{challenge_server_name}__list_challenges",
        f"mcp__{challenge_server_name}__start_challenge",
        f"mcp__{challenge_server_name}__stop_challenge",
        f"mcp__{challenge_server_name}__submit_flag",
        f"mcp__{challenge_server_name}__view_hint",
    ]


def load_extra_mcp_servers(config: dict[str, str]) -> dict[str, Any]:
    """从 JSON 字符串或文件中加载额外 MCP 服务器配置。"""
    raw_json = config.get("EXTRA_MCP_SERVERS_JSON", "").strip()
    file_path = config.get("EXTRA_MCP_SERVERS_FILE", "").strip()

    if raw_json:
        try:
            data = json.loads(raw_json)
            if isinstance(data, dict):
                return data
            logger.warning("EXTRA_MCP_SERVERS_JSON 不是对象，已忽略")
        except json.JSONDecodeError as exc:
            logger.error(f"解析 EXTRA_MCP_SERVERS_JSON 失败: {exc}")

    if file_path:
        path = Path(file_path)
        if not path.exists():
            logger.warning(f"EXTRA_MCP_SERVERS_FILE 不存在: {file_path}")
            return {}
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                return data
            logger.warning("EXTRA_MCP_SERVERS_FILE 内容不是对象，已忽略")
        except Exception as exc:  # noqa: BLE001
            logger.error(f"读取 EXTRA_MCP_SERVERS_FILE 失败: {exc}")

    return {}


def build_mcp_servers(config: dict[str, str], challenge_server_name: str = "challenge") -> dict[str, Any]:
    """构建 Claude SDK 使用的 MCP 服务器配置。"""
    mcp_servers: dict[str, Any] = {
        challenge_server_name: {
            "type": "http",
            "url": config["MCP_SERVER_URL"],
            "headers": {"Authorization": f"Bearer {config['AGENT_TOKEN']}"},
        }
    }
    mcp_servers.update(load_extra_mcp_servers(config))
    return mcp_servers
