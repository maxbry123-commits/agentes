"""OpenWhale 主入口 - 渗透测试智能体启动器"""

from __future__ import annotations

import asyncio
import os
import socket
import sys
import threading

from dotenv import load_dotenv
from loguru import logger
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from .agents import create_agent
from .util.logging_config import setup_logging
from .util.mcp_client import create_mcp_session
from .web.app import broadcast_message, run as run_web

console = Console()


def _pick_available_port(host: str, preferred_port: int, max_tries: int = 20) -> int:
    """选择可用端口，优先使用配置端口。"""
    for offset in range(max_tries):
        port = preferred_port + offset
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                sock.bind((host, port))
                return port
            except OSError:
                continue

    raise RuntimeError(f"无法在 {host} 上找到可用端口，起始端口: {preferred_port}")


def _banner() -> None:
    """输出启动横幅"""
    banner = Text()
    banner.append("🐋 OpenWhale", style="bold cyan")
    banner.append("  渗透测试智能体 v0.1.0", style="dim")
    console.print(Panel(banner, border_style="cyan", padding=(0, 2)))


def _load_config() -> dict[str, str]:
    """从环境变量加载配置（支持 .env 文件）"""
    load_dotenv()

    backend = os.getenv("AGENT_BACKEND", "openai_compat").lower()
    server_host = os.getenv("SERVER_HOST", "")
    mcp_server_url = os.getenv("MCP_SERVER_URL", "")
    if not mcp_server_url and server_host:
        if server_host.startswith("http://") or server_host.startswith("https://"):
            mcp_server_url = f"{server_host.rstrip('/')}/mcp"
        else:
            mcp_server_url = f"http://{server_host.rstrip('/')}/mcp"

    model_api_key = os.getenv("TOKENHUB_API_KEY") or os.getenv("OPENAI_API_KEY", "")

    required_vars = {
        "AGENT_TOKEN": os.getenv("AGENT_TOKEN", ""),
        "SERVER_HOST": server_host,
        "MCP_SERVER_URL": mcp_server_url,
    }

    if backend in {
        "openai",
        "openai_compat",
        "minimax",
        "chat_completions",
        "deepagents",
        "claude",
        "claude_code",
        "claude_sdk",
        "claude-agent-sdk",
    }:
        required_vars["MODEL_API_KEY"] = model_api_key

    optional_vars = {
        "AGENT_BACKEND": backend,
        "CHALLENGE_MCP_SERVER_NAME": os.getenv("CHALLENGE_MCP_SERVER_NAME", "challenge"),
        "MODEL_BASE_URL": os.getenv("MODEL_BASE_URL", "https://tokenhub.tencentmaas.com/v1"),
        "MODEL_NAME": os.getenv("MODEL_NAME", "MiniMax-M2.7"),
        "MODEL_ID": os.getenv("MODEL_ID", "ep-jsc7o0kw"),
        "DEEPAGENTS_TIMEOUT_SECONDS": os.getenv("DEEPAGENTS_TIMEOUT_SECONDS", "300"),
        "DEEPAGENTS_REPEAT_CALL_LIMIT": os.getenv("DEEPAGENTS_REPEAT_CALL_LIMIT", "4"),
        "DEEPAGENTS_RECURSION_LIMIT": os.getenv("DEEPAGENTS_RECURSION_LIMIT", "64"),
        "DEEPAGENTS_BASH_TIMEOUT_SECONDS": os.getenv("DEEPAGENTS_BASH_TIMEOUT_SECONDS", "120"),
        "DEEPAGENTS_BASH_MAX_OUTPUT_CHARS": os.getenv("DEEPAGENTS_BASH_MAX_OUTPUT_CHARS", "8000"),
        "DEEPAGENTS_TRACE_ENABLED": os.getenv("DEEPAGENTS_TRACE_ENABLED", "false"),
        "CLAUDE_API_KEY": os.getenv("CLAUDE_API_KEY", ""),
        "CLAUDE_BASE_URL": os.getenv("CLAUDE_BASE_URL", ""),
        "CLAUDE_MODEL": os.getenv("CLAUDE_MODEL") or os.getenv("MODEL_ID", "ep-jsc7o0kw"),
        "CLAUDE_CLI_PATH": os.getenv("CLAUDE_CLI_PATH", ""),
        "CLAUDE_TOOLS_PRESET": os.getenv("CLAUDE_TOOLS_PRESET", "claude_code"),
        "CLAUDE_PERMISSION_MODE": os.getenv("CLAUDE_PERMISSION_MODE", "bypassPermissions"),
        "CLAUDE_ALLOWED_TOOLS": os.getenv("CLAUDE_ALLOWED_TOOLS", ""),
        "CLAUDE_DISALLOWED_TOOLS": os.getenv("CLAUDE_DISALLOWED_TOOLS", ""),
        "EXTRA_MCP_SERVERS_JSON": os.getenv("EXTRA_MCP_SERVERS_JSON", ""),
        "EXTRA_MCP_SERVERS_FILE": os.getenv("EXTRA_MCP_SERVERS_FILE", ""),
        "LOG_LEVEL": os.getenv("LOG_LEVEL", "INFO"),
        "WEB_HOST": os.getenv("WEB_HOST", "0.0.0.0"),
        "WEB_PORT": os.getenv("WEB_PORT", "8080"),
        "WEB_ENABLED": os.getenv("WEB_ENABLED", "true"),
    }

    config = {**required_vars, **optional_vars}

    missing = [k for k, v in required_vars.items() if not v]
    if missing:
        console.print(
            f"[bold red]错误：缺少必需的环境变量: {', '.join(missing)}[/bold red]\n"
            "请复制 .env.example 为 .env 并填写相应配置。",
        )
        sys.exit(1)

    return config


async def _run_agent(config: dict[str, str]) -> None:
    """异步运行智能体主流程"""
    mcp_url = config["MCP_SERVER_URL"]
    agent_token = config["AGENT_TOKEN"]
    backend = config["AGENT_BACKEND"]

    def on_message(role: str, content: str) -> None:
        """消息回调：转发给 Web 前端"""
        broadcast_message(role, content)

    agent = create_agent(config, on_message=on_message)

    broadcast_message(
        "system",
        "OpenWhale 启动 | "
        f"AgentBackend: {backend} | MCP服务器: {mcp_url} | "
        + (
            f"模型: {config['MODEL_NAME']} ({config['MODEL_ID']}) | BaseURL: {config['MODEL_BASE_URL']}"
            if backend in {"openai", "openai_compat", "minimax", "chat_completions", "deepagents"}
            else f"Claude模型: {config['CLAUDE_MODEL']} | MiniMax网关: {config['MODEL_BASE_URL']}"
        ),
    )

    try:
        if backend in {"claude", "claude_code", "claude_sdk", "claude-agent-sdk"}:
            logger.info("开始执行 Claude Code SDK 赛题流程...")
            broadcast_message("system", "开始执行 Claude Code SDK 赛题流程...")

            report = await agent.run_competition()
        else:
            async with create_mcp_session(mcp_url, agent_token=agent_token) as mcp_session:
                logger.info("开始执行赛题流程...")
                broadcast_message("system", "开始执行赛题流程...")

                report = await agent.run_competition(mcp_session)

        logger.success("流程执行完成！")
        broadcast_message("system", "流程执行完成！")

        # 在控制台输出最终结果
        console.print(
            Panel(
                report.final_message or "(模型未输出最终文本)",
                title="[bold green]执行报告[/bold green]",
                border_style="green",
                padding=(1, 2),
            )
        )

    except Exception as e:
        logger.error(f"智能体运行失败: {e}")
        broadcast_message("system", f"错误: {e}")
        raise
    except KeyboardInterrupt:
        logger.warning("用户中断运行，已停止智能体")
        broadcast_message("system", "用户中断运行，已停止智能体")
        return


def main() -> None:
    """命令行入口"""
    _banner()

    # 加载配置
    config = _load_config()

    # 初始化日志
    setup_logging(config["LOG_LEVEL"])

    backend = config["AGENT_BACKEND"]
    if backend in {"openai", "openai_compat", "minimax", "chat_completions", "deepagents"}:
        model_info = f"模型: {config['MODEL_NAME']} ({config['MODEL_ID']}) | BaseURL: {config['MODEL_BASE_URL']}"
    else:
        claude_base_url = config["CLAUDE_BASE_URL"] or config["MODEL_BASE_URL"]
        model_info = (
            f"Claude模型: {config['CLAUDE_MODEL']} | Claude网关: {claude_base_url} | "
            f"permission_mode: {config['CLAUDE_PERMISSION_MODE']}"
        )

    logger.info(
        "配置加载完成 | "
        f"AgentBackend: {backend} | {model_info} | MCP: {config['MCP_SERVER_URL']}"
    )

    # 启动 Web 前端（后台线程）
    web_enabled = config["WEB_ENABLED"].lower() in ("1", "true", "yes")
    if web_enabled:
        preferred_port = int(config["WEB_PORT"])
        selected_port = _pick_available_port(config["WEB_HOST"], preferred_port)
        if selected_port != preferred_port:
            logger.warning(
                f"Web 端口 {preferred_port} 已占用，自动切换到 {selected_port}"
            )
            config["WEB_PORT"] = str(selected_port)

        web_thread = threading.Thread(
            target=run_web,
            kwargs={
                "host": config["WEB_HOST"],
                "port": int(config["WEB_PORT"]),
            },
            daemon=True,
        )
        web_thread.start()
        logger.info(f"Web 界面已启动: http://{config['WEB_HOST']}:{config['WEB_PORT']}")

    # 运行智能体
    asyncio.run(_run_agent(config))


if __name__ == "__main__":
    main()
