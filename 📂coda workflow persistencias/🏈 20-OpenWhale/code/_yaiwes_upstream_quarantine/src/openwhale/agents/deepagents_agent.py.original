"""DeepAgents 智能体实现。"""

from __future__ import annotations

import asyncio
import json
import subprocess
from typing import Any
from pathlib import Path

from deepagents import create_deep_agent
from langchain_core.messages import AIMessage, AIMessageChunk
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.errors import GraphRecursionError
from loguru import logger
from mcp import ClientSession

from ..util.mcp_client import call_tool
from .base import AgentRunResult, BaseChallengeAgent
from .prompts import MISSION_PROMPT, SYSTEM_PROMPT


class DeepAgentsChallengeAgent(BaseChallengeAgent):
    """基于 DeepAgents 的挑战赛智能体。"""

    _child_wrapper_tools = {
        "start_current_challenge",
        "stop_current_challenge",
        "view_current_hint",
        "submit_current_flag",
        "refresh_challenge_status",
    }

    def __init__(
        self,
        config: dict[str, str],
        max_iterations: int = 16,
        on_message=None,
    ) -> None:
        model_name = config.get("MODEL_NAME", "MiniMax-M2.7")
        super().__init__(model_name=model_name, max_iterations=max_iterations, on_message=on_message)
        self.config = config
        self._mcp_session: ClientSession | None = None
        self._workspace_root = Path(__file__).resolve().parents[3]
        self._tool_call_counters: dict[str, int] = {}
        self._repeat_call_limit = int(config.get("DEEPAGENTS_REPEAT_CALL_LIMIT", "4"))
        self._timeout_seconds = int(config.get("DEEPAGENTS_TIMEOUT_SECONDS", "300"))
        self._recursion_limit = int(
            config.get("DEEPAGENTS_RECURSION_LIMIT", str(max(self.max_iterations * 8, 64)))
        )
        self._trace_enabled = config.get("DEEPAGENTS_TRACE_ENABLED", "false").lower() in ("1", "true", "yes")
        self._trace_verbose = config.get("DEEPAGENTS_TRACE_VERBOSE", "false").lower() in ("1", "true", "yes")
        self._bash_timeout_seconds = int(config.get("DEEPAGENTS_BASH_TIMEOUT_SECONDS", "120"))
        self._bash_max_output_chars = int(config.get("DEEPAGENTS_BASH_MAX_OUTPUT_CHARS", "8000"))
        self._emitted_assistant_messages: set[str] = set()

    def format_tools(self, tools: list[Any]) -> list[Any]:
        return tools

    async def complete_turn(self, messages: list[dict[str, Any]], tools: Any):  # pragma: no cover
        raise NotImplementedError("DeepAgents backend does not use manual turn completion")

    def _emit_trace_event(self, event: dict[str, Any]) -> None:
        event_name = str(event.get("event", "unknown"))
        node_name = str(event.get("name", ""))
        data = event.get("data")

        if event_name.endswith("tool_start"):
            if node_name.endswith("_tool"):
                return
            if node_name in self._child_wrapper_tools:
                return
            input_data = data.get("input") if isinstance(data, dict) else data
            tool_name = node_name or "tool"
            self._emit("tool_call", f"调用工具: {tool_name}，参数: {str(input_data)[:500]}")
            return

        if event_name.endswith("tool_end"):
            if node_name.endswith("_tool"):
                return
            if node_name in self._child_wrapper_tools:
                return
            output_data = data.get("output") if isinstance(data, dict) else data
            tool_name = node_name or "tool"
            self._emit("tool_result", f"[{tool_name}] 结果: {str(output_data)[:500]}")
            return

        if event_name.endswith("llm_end"):
            output_data = data.get("output") if isinstance(data, dict) else data
            for text in self._extract_assistant_texts(output_data):
                if text not in self._emitted_assistant_messages:
                    self._emitted_assistant_messages.add(text)
                    self._emit("assistant", text)

            if self._trace_enabled:
                self._emit("trace", f"模型结束: {node_name or 'model'} | 输出: {str(output_data)[:300]}")
            return

        if event_name.endswith("chain_stream") or event_name.endswith("llm_stream"):
            chunk = data.get("chunk") if isinstance(data, dict) else data
            for text in self._extract_assistant_texts(chunk):
                if text not in self._emitted_assistant_messages:
                    self._emitted_assistant_messages.add(text)
                    self._emit("assistant", text)

            if not self._trace_enabled:
                return

            if self._trace_verbose:
                text = getattr(chunk, "content", None) or getattr(chunk, "text", None) or str(chunk)
                if text and str(text).strip():
                    self._emit("trace", f"流式片段: {str(text)[:200]}")
            return

        if not self._trace_enabled:
            return

        if event_name.endswith("chain_start"):
            self._emit("trace", f"流程开始: {node_name or 'graph'}")
            return

        if event_name.endswith("chain_end"):
            self._emit("trace", f"流程结束: {node_name or 'graph'}")
            return

        if event_name.endswith("llm_start"):
            self._emit("trace", f"模型开始: {node_name or 'model'}")
            return

        if not self._trace_verbose:
            return

    async def _collect_final_message(self, result: dict[str, Any]) -> tuple[str, int]:
        final_response = ""
        iterations = 0
        for message in result.get("messages", []):
            if isinstance(message, AIMessage):
                iterations += 1
                content = message.content
                if isinstance(content, str) and content.strip():
                    final_response = content.strip()
                    if final_response not in self._emitted_assistant_messages:
                        self._emitted_assistant_messages.add(final_response)
                        self._emit("assistant", final_response)

        return final_response, iterations

    def _extract_assistant_texts(self, payload: Any) -> list[str]:
        texts: list[str] = []

        def _walk(node: Any) -> None:
            if node is None:
                return

            if isinstance(node, AIMessage):
                if isinstance(node.content, str) and node.content.strip():
                    texts.append(node.content.strip())
                return

            if isinstance(node, AIMessageChunk):
                if isinstance(node.content, str) and node.content.strip():
                    texts.append(node.content.strip())
                return

            if isinstance(node, dict):
                role = node.get("role")
                content = node.get("content")
                if role == "assistant" and isinstance(content, str) and content.strip():
                    texts.append(content.strip())
                for value in node.values():
                    _walk(value)
                return

            if isinstance(node, (list, tuple, set)):
                for item in node:
                    _walk(item)

        _walk(payload)
        return texts

    @staticmethod
    def _try_parse_json(text: str) -> dict[str, Any] | None:
        try:
            data = json.loads(text)
            if isinstance(data, dict):
                return data
        except Exception:  # noqa: BLE001
            return None
        return None

    async def _run_streamed_deep_agent(self, deep_agent: Any, mission_prompt: str) -> AgentRunResult:
        self._emitted_assistant_messages.clear()
        events: list[dict[str, Any]] = []

        async def _run_stream() -> None:
            async for event in deep_agent.astream_events(
                {"messages": [{"role": "user", "content": mission_prompt}]},
                config={"recursion_limit": self._recursion_limit},
                version="v2",
            ):
                if isinstance(event, dict):
                    events.append(event)
                    self._emit_trace_event(event)

        try:
            await asyncio.wait_for(_run_stream(), timeout=self._timeout_seconds)
        except GraphRecursionError as exc:
            recursion_msg = (
                f"DeepAgents 触发递归上限（{self._recursion_limit}），已主动中止。"
                "这表示模型仍在持续探索/调用工具，未收敛到停止条件。"
                f" 原始错误: {exc}"
            )
            self._emit("system", recursion_msg)
            return AgentRunResult(final_message=recursion_msg, iterations=0)
        except TimeoutError:
            timeout_msg = (
                f"DeepAgents 执行超时（>{self._timeout_seconds}s），已主动中止。"
                "这通常意味着模型陷入了探索循环，可调小 recursion_limit 或调整提示词。"
            )
            self._emit("system", timeout_msg)
            return AgentRunResult(final_message=timeout_msg, iterations=0)

        result: dict[str, Any] = {}
        for event in reversed(events):
            if event.get("event", "").endswith("chain_end") and isinstance(event.get("data"), dict):
                maybe_output = event["data"].get("output")
                if isinstance(maybe_output, dict):
                    result = maybe_output
                    break

        if not result:
            result = {"messages": []}

        final_response, iterations = await self._collect_final_message(result)
        return AgentRunResult(final_message=final_response, iterations=iterations)

    async def _run_single_challenge_agent(self, model: ChatOpenAI, challenge: dict[str, Any]) -> AgentRunResult:
        code = str(challenge.get("code", ""))
        title = str(challenge.get("title", ""))
        entrypoint = challenge.get("entrypoint")

        @tool
        async def start_current_challenge() -> str:
            """启动当前子智能体绑定的赛题实例。"""
            return await self._call_mcp("start_challenge", {"code": code})

        @tool
        async def stop_current_challenge() -> str:
            """停止当前子智能体绑定的赛题实例。"""
            return await self._call_mcp("stop_challenge", {"code": code})

        @tool
        async def view_current_hint() -> str:
            """查看当前子智能体绑定赛题的提示信息。"""
            return await self._call_mcp("view_hint", {"code": code})

        @tool
        async def submit_current_flag(flag: str) -> str:
            """提交当前赛题 flag。只有在远程响应中明确看到 flag{...} 时才能提交。"""
            return await self._call_mcp("submit_flag", {"code": code, "flag": flag})

        @tool
        async def refresh_challenge_status() -> str:
            """刷新当前题状态，确认是否已得分。"""
            return await self._call_mcp("list_challenges", {})

        @tool("Bash")
        async def bash_tool(command: str, cwd: str | None = None, timeout_seconds: int | None = None) -> str:
            """在本地执行 Bash 命令（用于远程 HTTP 侦察、请求脚本、结果记录）。"""
            return await self._run_bash(command, cwd=cwd, timeout_seconds=timeout_seconds)

        child_system_prompt = (
            SYSTEM_PROMPT
            + "\n\n你是主智能体分配出来的子智能体，只负责一个赛题，不要切换到其他赛题。"
            + f"\n当前赛题: {title} (code={code})"
            + f"\n当前入口信息: {entrypoint}"
            + "\n必须按流程执行：start -> 远程侦察/利用 -> submit_flag -> stop。"
        )

        child_mission_prompt = (
            f"你当前只处理赛题 {title} (code={code})。"
            "先启动实例，然后基于远程黑盒进行侦察和利用，必要时可查看提示。"
            "仅当远程响应中明确出现 flag{...} 才提交。"
            "完成后停止实例并输出该题结果与证据。"
        )

        child_agent = create_deep_agent(
            model=model,
            system_prompt=child_system_prompt,
            tools=[
                bash_tool,
                start_current_challenge,
                stop_current_challenge,
                view_current_hint,
                submit_current_flag,
                refresh_challenge_status,
            ],
        )

        self._emit("system", f"[主智能体] 子智能体已分配: {title} ({code})")
        report = await self._run_streamed_deep_agent(child_agent, child_mission_prompt)

        # 无论子智能体内是否停止实例，主流程都兜底停止一次，确保资源释放。
        try:
            await self._call_mcp("stop_challenge", {"code": code})
        except Exception as exc:  # noqa: BLE001
            self._emit("system", f"[主智能体] 赛题 {code} 停止实例失败（可忽略）: {exc}")

        return report

    async def _call_mcp(self, tool_name: str, arguments: dict[str, Any]) -> str:
        if self._mcp_session is None:
            raise RuntimeError("MCP session not initialized")

        self._emit("tool_call", f"调用工具: {tool_name}，参数: {json.dumps(arguments, ensure_ascii=False)}")

        call_key = f"{tool_name}:{json.dumps(arguments, ensure_ascii=False, sort_keys=True)}"
        count = self._tool_call_counters.get(call_key, 0) + 1
        self._tool_call_counters[call_key] = count
        if count > self._repeat_call_limit:
            repeated_msg = (
                f"检测到重复调用: {tool_name} 参数未变化，已连续 {count} 次。"
                "请停止重复调用，转向下一步分析或尝试其他工具。"
            )
            self._emit("tool_result", f"[{tool_name}] 结果: {repeated_msg}")
            return repeated_msg

        result = await call_tool(self._mcp_session, tool_name, arguments)

        if hasattr(result, "content") and isinstance(result.content, list):
            parts: list[str] = []
            for item in result.content:
                text = getattr(item, "text", None)
                if text:
                    parts.append(text)
                else:
                    parts.append(str(item))
            result_text = "\n".join(parts)
            self._emit("tool_result", f"[{tool_name}] 结果: {result_text[:500]}")
            return result_text

        result_text = str(result)
        self._emit("tool_result", f"[{tool_name}] 结果: {result_text[:500]}")
        return result_text

    def _render_bash_result(
        self,
        command: str,
        cwd: Path,
        timeout_seconds: int,
        completed_process: subprocess.CompletedProcess[str] | None,
        error: str | None = None,
    ) -> str:
        if error is not None:
            return json.dumps(
                {
                    "command": command,
                    "cwd": str(cwd),
                    "timeout_seconds": timeout_seconds,
                    "error": error,
                },
                ensure_ascii=False,
                indent=2,
            )

        assert completed_process is not None
        stdout = completed_process.stdout or ""
        stderr = completed_process.stderr or ""
        if len(stdout) > self._bash_max_output_chars:
            stdout = stdout[: self._bash_max_output_chars] + "\n... [stdout truncated]"
        if len(stderr) > self._bash_max_output_chars:
            stderr = stderr[: self._bash_max_output_chars] + "\n... [stderr truncated]"

        return json.dumps(
            {
                "command": command,
                "cwd": str(cwd),
                "timeout_seconds": timeout_seconds,
                "returncode": completed_process.returncode,
                "stdout": stdout,
                "stderr": stderr,
            },
            ensure_ascii=False,
            indent=2,
        )

    async def _run_bash(self, command: str, cwd: str | None = None, timeout_seconds: int | None = None) -> str:
        workdir = Path(cwd).expanduser().resolve() if cwd else self._workspace_root
        timeout = timeout_seconds or self._bash_timeout_seconds

        if not workdir.exists():
            return self._render_bash_result(
                command=command,
                cwd=workdir,
                timeout_seconds=timeout,
                completed_process=None,
                error=f"cwd 不存在: {workdir}",
            )

        def _execute() -> subprocess.CompletedProcess[str]:
            return subprocess.run(
                ["bash", "-lc", command],
                cwd=str(workdir),
                capture_output=True,
                text=True,
                timeout=timeout,
            )

        try:
            completed_process = await asyncio.to_thread(_execute)
        except subprocess.TimeoutExpired:
            return self._render_bash_result(
                command=command,
                cwd=workdir,
                timeout_seconds=timeout,
                completed_process=None,
                error=f"命令执行超时（>{timeout} 秒）",
            )
        except Exception as exc:  # noqa: BLE001
            return self._render_bash_result(
                command=command,
                cwd=workdir,
                timeout_seconds=timeout,
                completed_process=None,
                error=f"命令执行失败: {exc}",
            )

        return self._render_bash_result(
            command=command,
            cwd=workdir,
            timeout_seconds=timeout,
            completed_process=completed_process,
        )

    async def run_competition(self, mcp_session: ClientSession) -> AgentRunResult:
        logger.info("=== 开始 DeepAgents 闯关流程 ===")
        self._mcp_session = mcp_session

        model = ChatOpenAI(
            model=self.config["MODEL_ID"],
            api_key=self.config["MODEL_API_KEY"],
            base_url=self.config["MODEL_BASE_URL"],
            temperature=0.2,
        )

        self._emit("system", f"模型已就绪: {self.model_name} ({self.config['MODEL_ID']})")
        self._emit(
            "system",
            (
                f"DeepAgents 防护参数: timeout={self._timeout_seconds}s, "
                f"recursion_limit={self._recursion_limit}, "
                f"repeat_call_limit={self._repeat_call_limit}, "
                f"trace_enabled={self._trace_enabled}"
            ),
        )
        self._emit("user", MISSION_PROMPT)

        # 主智能体先获取题单，再为每个未完成题分配一个子智能体执行。
        challenges_text = await self._call_mcp("list_challenges", {})
        challenges_data = self._try_parse_json(challenges_text) or {}
        challenges = challenges_data.get("challenges", []) if isinstance(challenges_data.get("challenges", []), list) else []

        unsolved: list[dict[str, Any]] = []
        for challenge in challenges:
            if not isinstance(challenge, dict):
                continue
            if challenge.get("flag_got_count", 0) < challenge.get("flag_count", 1):
                unsolved.append(challenge)

        if not unsolved:
            msg = "所有当前可见赛题已完成，无需继续执行。"
            self._emit("system", msg)
            return AgentRunResult(final_message=msg, iterations=0)

        self._emit("system", f"[主智能体] 待处理赛题数: {len(unsolved)}")

        summaries: list[str] = []
        total_iterations = 0

        for idx, challenge in enumerate(unsolved, start=1):
            code = str(challenge.get("code", ""))
            title = str(challenge.get("title", ""))
            self._emit("system", f"[主智能体] 分配子智能体 {idx}/{len(unsolved)}: {title} ({code})")

            child_report = await self._run_single_challenge_agent(model, challenge)
            total_iterations += child_report.iterations

            status_text = await self._call_mcp("list_challenges", {})
            status_data = self._try_parse_json(status_text) or {}
            solved = False
            for item in status_data.get("challenges", []) if isinstance(status_data.get("challenges", []), list) else []:
                if isinstance(item, dict) and str(item.get("code", "")) == code:
                    solved = item.get("flag_got_count", 0) >= item.get("flag_count", 1)
                    break

            summaries.append(
                f"- {title} ({code}): {'已完成' if solved else '未完成'} | 子智能体总结: {child_report.final_message or '(无输出)'}"
            )

        final_message = "主从模式执行完成。各子智能体结果:\n" + "\n".join(summaries)
        self._emit("assistant", final_message)
        return AgentRunResult(final_message=final_message, iterations=total_iterations)
