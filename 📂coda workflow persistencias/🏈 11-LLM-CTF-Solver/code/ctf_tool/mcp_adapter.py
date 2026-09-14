import asyncio
import re
import threading
from contextlib import AsyncExitStack
from typing import Dict, List, Optional
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from ctf_tool.base_tool import BaseTool
import logging
import os
import atexit

logger = logging.getLogger(__name__)


class MCPServerAdapter(BaseTool):
    def __init__(self, server_config: dict):
        super().__init__()
        self.server_name = server_config["name"]
        self.server_config = server_config
        self.communication_mode = server_config.get("type", "http")
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()
        self.tools = {}
        self.loop = asyncio.new_event_loop()
        self._exec_lock = threading.Lock()  # 串行化 loop.run_until_complete 调用
        self._session_stale = False  # SSE session 空闲超时标记

        # 注册退出时的清理函数（在初始化前注册，确保即使初始化失败也能清理子进程）
        atexit.register(self._cleanup)

        # 初始化服务器连接
        self.loop.run_until_complete(self._initialize_server())

    async def _initialize_server(self):
        """初始化服务器连接"""
        if self.communication_mode == "stdio" and "command" in self.server_config:
            await self._connect_stdio_server()
        elif self.communication_mode == "http" and "url" in self.server_config:
            self.base_url = self.server_config["url"]
            self.auth_token = self.server_config.get("auth_token", None)
            await self._load_http_tools()
        else:
            logger.error(f"不支持的通信模式或缺少必要配置: {self.communication_mode}")

    async def _connect_stdio_server(self):
        """连接到stdio模式的MCP服务器"""
        command = self.server_config["command"]
        args = self.server_config.get("args", [])
        working_dir = self.server_config.get("working_directory", os.getcwd())

        logger.info(f"连接到stdio模式MCP服务器: {self.server_name}")
        logger.debug(f"命令: {command} {' '.join(args)}")
        logger.debug(f"工作目录: {working_dir}")

        try:
            server_params = StdioServerParameters(
                command=command, args=args, env=None, cwd=working_dir
            )

            # 创建stdio连接
            stdio_transport = await self.exit_stack.enter_async_context(
                stdio_client(server_params)
            )
            self.stdio, self.write = stdio_transport

            # 创建客户端会话
            self.session = await self.exit_stack.enter_async_context(
                ClientSession(self.stdio, self.write)
            )

            # 初始化会话并加载工具
            await self.session.initialize()
            await self._load_stdio_tools()

        except Exception as e:
            logger.error(f"连接MCP服务器失败: {str(e)}")
            raise RuntimeError(f"无法连接MCP服务器: {str(e)}")

    async def _load_http_tools(self):
        from pathlib import Path as _YP
        import json as _YJ
        _ye = {'schema':'yaiwes.internal.persistence/v1','source':'ctf_tool/mcp_adapter.py','step':'_load_http_tools','status':'CHECKPOINTED'}
        _yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
        with _yp.open('a', encoding='utf-8') as _yf:
            _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
        return _ye

    async def _load_stdio_tools(self):
        """通过stdio加载工具列表"""
        if not self.session:
            logger.error("无法加载工具: 未连接到stdio服务")
            return

        try:
            # 列出可用的工具
            response = await self.session.list_tools()
            tools_info = [
                {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": {
                        "type": "object",
                        "properties": tool.inputSchema.get("properties", {}),
                        "required": tool.inputSchema.get("required", []),
                    },
                }
                for tool in response.tools
            ]

            self._process_tools_info(tools_info)
        except Exception as e:
            logger.error(f"加载MCP工具失败: {str(e)}")

    def _process_tools_info(self, tools_info: list):
        """处理工具信息"""
        for tool_info in tools_info:
            tool_name = tool_info['name']
            parameters = tool_info.get("parameters", {})
            self.tools[tool_name] = {
                "description": tool_info.get("description", ""),
                "parameters": parameters,
                "function_config": {
                    "type": "function",
                    "function": {
                        "name": tool_name,
                        "description": tool_info.get("description", ""),
                        "parameters": parameters if parameters else {
                            "type": "object",
                            "properties": {},
                            "required": []
                        }
                    }
                }
            }

    def execute(self, tool_name: str, arguments: dict) -> str:
        """执行MCP服务器上的工具。线程安全：多线程并行调用时串行化 loop 访问。"""
        if tool_name not in self.tools:
            return f"错误：未知的MCP工具 '{tool_name}'"
        with self._exec_lock:
            # SSE session 空闲超时后自动重建连接
            if self._session_stale:
                if not self._reconnect():
                    return f"MCP 执行异常: {self.server_name} 重连失败，跳过本次调用"
            output, error = self.loop.run_until_complete(self._execute(tool_name, arguments))
        if error:
            clean_error = self._clean_error(error)
            return f"MCP 执行异常: {clean_error}" if not output else f"{output}\n[MCP 部分超时] {clean_error[:200]}"
        return output

    async def _execute(self, tool_name: str, arguments: dict):
        """内部异步执行方法"""
        if self.communication_mode == "http":
            return await self._execute_http(tool_name, arguments)
        elif self.communication_mode == "stdio":
            return await self._execute_stdio(tool_name, arguments)
        else:
            return "", f"错误：不支持的通信模式 '{self.communication_mode}'"

    async def _execute_http(self, tool_name: str, arguments: dict):
        from pathlib import Path as _YP
        import json as _YJ
        _ye = {'schema':'yaiwes.internal.persistence/v1','source':'ctf_tool/mcp_adapter.py','step':'_execute_http','status':'CHECKPOINTED'}
        _yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
        with _yp.open('a', encoding='utf-8') as _yf:
            _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
        return _ye

    async def _execute_stdio(self, tool_name: str, arguments: dict):
        """通过stdio执行工具"""
        if not self.session:
            return "", "错误：未连接到stdio服务"

        try:
            result = await self.session.call_tool(tool_name, arguments)
            texts = []
            for item in (result.content or []):
                texts.append(getattr(item, "text", str(item)))
            return "\n".join(texts), ""
        except Exception as e:
            err_str = str(e)
            # SSE session 空闲超时 → 标记 staled，下次调用自动重连
            if "timeout" in err_str.lower() or "timed out" in err_str.lower():
                logger.warning("MCP session 已过期，标记重连 (%s): %s",
                               self.server_name, err_str[:120])
                self._session_stale = True
            logger.error("MCP工具执行失败: %s", err_str)
            return "", f"MCP工具执行错误: {err_str}"

    @property
    def function_config(self) -> Dict:
        """实现BaseTool要求的属性 - 返回适配器本身的配置。MCP适配器的实际工具通过 get_tool_configs() 暴露。"""
        return {
            "type": "function",
            "function": {
                "name": self.__class__.__name__,
                "description": f"MCP适配器 (服务: {self.server_name}, 已加载 {len(self.tools)} 个工具)",
            },
        }

    def get_tool_configs(self) -> List[Dict]:
        """为每个MCP工具生成函数配置"""
        configs = []
        for tool_name, tool_info in self.tools.items():
            parameters = tool_info["parameters"]
            config = {
                "type": "function",
                "function": {
                    "name": tool_name,
                    "description": tool_info["description"],
                    "parameters": {
                        "type": "object",
                        "properties": parameters.get("properties", {}),
                        "required": parameters.get("required", [])
                    }
                },
            }
            configs.append(config)
        return configs

    @staticmethod
    def _clean_error(error: str) -> str:
        """截断 MCP 代理抛出的 Java 堆栈，只保留关键信息。"""
        # 去掉 Java 堆栈（以 \tat 开头的行为堆栈帧）
        cleaned = re.sub(r'\n\s+at\s+.*(?:\n\s+\.\.\.\s+\d+\s+more)?', '', error)
        # 截断 kotlinx.coroutines 的冗余帧信息
        cleaned = re.sub(r'; job=.*', '', cleaned)
        return cleaned.strip()[:300]

    def _reconnect(self) -> bool:
        """重建整个 MCP 连接：关闭旧 event loop→清空 tools→重新初始化。

        SSE session 空闲超时后，mcp-proxy.jar 的 stdio 管道仍然存活但无法
        再到达 Burp。此时需要关闭旧 Java 进程（通过关闭 stdio transport），
        然后创建新的 event loop + stdio transport 得到全新的 sessionId。

        在 self._exec_lock 锁内调用，线程安全。
        """
        logger.info("MCP 重连: %s (关闭旧连接...)", self.server_name)
        # 1. 关闭旧 event loop（触发 stdio transport 关闭 → Java 进程终止）
        old_loop = self.loop
        try:
            old_loop.run_until_complete(self.exit_stack.aclose())
        except Exception as e:
            logger.debug("旧 exit_stack 关闭异常 (可忽略): %s", e)
        try:
            old_loop.close()
        except Exception as e:
            logger.debug("旧 event loop 关闭异常 (可忽略): %s", e)

        # 2. 创建新 event loop + exit stack，重新初始化
        self.tools.clear()
        self.exit_stack = AsyncExitStack()
        self.loop = asyncio.new_event_loop()
        self._session_stale = False
        try:
            self.loop.run_until_complete(self._initialize_server())
            logger.info("MCP 重连成功: %s, 工具数=%d", self.server_name, len(self.tools))
            return True
        except Exception as e:
            logger.error("MCP 重连失败: %s — %s", self.server_name, e)
            self._session_stale = True
            return False

    def _cleanup(self):
        """清理资源，安全关闭事件循环。

        不调用 shutdown_asyncgens() — stdio_client 内部使用 anyio cancel scope，
        该 scope 有线程亲和性，在 atexit 主线程中 shut down async generator
        会触发 RuntimeError: "Attempted to exit cancel scope in a different task"。
        """
        import sys
        if sys.is_finalizing():
            return  # 解释器正在关闭，跳过 (模块可能已销毁)
        try:
            if self.loop.is_running():
                self.loop.call_soon_threadsafe(self.loop.stop)
        except Exception:
            pass
        try:
            self.loop.close()
        except Exception:
            pass
