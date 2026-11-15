import os
import json
import yaml
import hashlib
import importlib
import inspect
import logging
import numpy as np
from config import Config, get_project_root
from typing import Dict, List, Tuple, Optional, Set
from ctf_tool.base_tool import BaseTool
from utils.llm_request import LLMRequest
from jinja2 import Environment, FileSystemLoader
from utils.text import fix_json_with_llm
from litellm import ModelResponse, ChatCompletionMessageToolCall
from utils.security import init_blacklist

logger = logging.getLogger(__name__)


class ToolUtils:
    def __init__(self, mode: str = "ctf"):
        self.config = Config.load_config()
        self.mode = mode
        self.analyzer_llm = LLMRequest("analyzer")
        self.embedding_llm = LLMRequest("embedding")
        self.summary_llm = LLMRequest("solve_agent")  # 复用于 output_summary
        self.tools = {} # 存储所有工具实例 {name: instance}
        self._dynamic_tool_map: Dict[str, dict] = {}  # 动态工具: tool_name -> {cfg, cmd}
        self._lazy_mcp_servers: Dict[str, dict] = {}  # 待懒加载的 MCP 服务

        # 分离两类配置
        self.local_function_configs = [] # 本地工具配置 (默认全注入)
        self.mcp_function_configs = []   # MCP工具配置 (需要检索)

        prompt_version = self.config.get("prompt_version", "v1")
        prompt_dir = os.path.join(get_project_root(), "prompts", prompt_version)
        prompt_path = os.path.join(prompt_dir, "prompt.yaml")
        with open(prompt_path, "r", encoding="utf-8") as f:
            self.prompt: dict = yaml.safe_load(f)

        # 初始化命令安全黑名单
        blacklist_rules = self.config.get("command_blacklist", None)
        init_blacklist(blacklist_rules)
        logger.info("命令安全黑名单已初始化 (%s 条规则)", len(blacklist_rules) if blacklist_rules else "默认")

        self.env = Environment(loader=FileSystemLoader(prompt_dir))

        # 向量缓存文件
        self.embeddings_cache_file = os.path.join(
            os.path.dirname(__file__), "..", "tool_embeddings_cache.json"
        )
        self._MAX_CACHED_TOOLS = 500  # 最多缓存 500 个工具向量
        self.tool_embeddings_map = self._load_embeddings_cache()

        # 动态工具解析器（延迟初始化，避免无 SSH 配置时创建无用连接）
        self._dynamic_resolver = None

    def _calculate_tool_hash(self, tool_config: Dict) -> str:
        """计算单个工具配置的哈希值，用于判断描述是否变更"""
        # 主要基于名字和描述计算hash
        info = {
            "name": tool_config["function"]["name"],
            "description": tool_config["function"].get("description", ""),
            "parameters": str(tool_config["function"].get("parameters", {}))
        }
        return hashlib.md5(json.dumps(info, sort_keys=True).encode()).hexdigest()

    def _load_embeddings_cache(self) -> Dict:
        """加载向量缓存，超过上限时截断。"""
        if os.path.exists(self.embeddings_cache_file):
            try:
                file_size = os.path.getsize(self.embeddings_cache_file)
                if file_size > 10 * 1024 * 1024:  # >10MB 跳过
                    logger.warning("向量缓存文件过大 (%.1fMB)，跳过加载", file_size / 1024 / 1024)
                    return {}
                with open(self.embeddings_cache_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if len(data) > self._MAX_CACHED_TOOLS:
                    logger.warning("向量缓存条目过多 (%d)，截断至 %d", len(data), self._MAX_CACHED_TOOLS)
                    keys = list(data.keys())[-self._MAX_CACHED_TOOLS:]
                    return {k: data[k] for k in keys}
                return data
            except Exception as e:
                logger.warning(f"加载向量缓存失败: {e}")
        return {}

    def _save_embeddings_cache(self):
        """保存向量缓存，超过上限时修剪。"""
        try:
            data = self.tool_embeddings_map
            if len(data) > self._MAX_CACHED_TOOLS:
                keys = list(data.keys())[-self._MAX_CACHED_TOOLS:]
                data = {k: data[k] for k in keys}
            with open(self.embeddings_cache_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False)
        except Exception as e:
            logger.error(f"保存向量缓存失败: {e}")

    def _get_embedding(self, text: str) -> List[float]:
        """调用模型获取向量 (参考 RAG Service)"""
        try:
            # 注意：这里假设 LLMRequest.embedding 返回格式与 litellm 或 openai 格式兼容
            # 如果是 list[str]，通常返回 data list
            response = self.embedding_llm.embedding(text=[text])
            # 根据 litellm 结构获取 embedding
            return response.data[0]["embedding"]
        except Exception as e:
            logger.error(f"获取嵌入向量失败: {e}")
            # 发生错误返回空向量或零向量，避免程序崩溃
            return []

    def _update_mcp_embeddings(self):
        """检查并更新 MCP 工具的向量"""
        has_updates = False
        
        for config in self.mcp_function_configs:
            tool_name = config["function"]["name"]
            description = config["function"].get("description", "")
            # 组合名称和描述以增强检索语义
            text_to_embed = f"{tool_name}: {description}"
            current_hash = self._calculate_tool_hash(config)
            
            # 检查缓存是否存在且未过期
            cached_data = self.tool_embeddings_map.get(tool_name)
            
            if not cached_data or cached_data.get("hash") != current_hash:
                logger.info(f"正在生成工具向量: {tool_name}")
                embedding = self._get_embedding(text_to_embed)
                if embedding:
                    self.tool_embeddings_map[tool_name] = {
                        "hash": current_hash,
                        "embedding": embedding,
                        "text": text_to_embed
                    }
                    has_updates = True
            
        if has_updates:
            self._save_embeddings_cache()
            logger.info("工具向量缓存已更新")

    def load_tools(self) -> Tuple[Dict, list]:
        """
        加载工具，区分本地工具和MCP工具
        返回: (所有工具实例字典, 所有工具配置列表)
        """
        config = Config.load_config()
        tools_dir = os.path.join(os.path.dirname(__file__), "..", "ctf_tool")

        # 重置列表
        self.local_function_configs = []
        self.mcp_function_configs = []
        self.tools = {}

        # 1. 加载本地工具 (Local Tools) - 默认全注入
        for file_name in os.listdir(tools_dir):
            if (
                file_name.endswith(".py")
                and file_name not in ["__init__.py", "base_tool.py", "mcp_adapter.py"]
            ):
                module_name = file_name[:-3]
                try:
                    module = importlib.import_module(f"ctf_tool.{module_name}")
                    for name, obj in inspect.getmembers(module):
                        if (
                            inspect.isclass(obj)
                            and issubclass(obj, BaseTool)
                            and obj != BaseTool
                        ):
                            # 实例化（用模块名匹配配置键）
                            if module_name in config.get("tool_config", {}):
                                tool_instance = obj(config["tool_config"][module_name])
                            else:
                                tool_instance = obj()

                            # 按模式过滤工具 — modes=None 表示全模式可用
                            tool_modes = getattr(tool_instance, 'modes', None)
                            if tool_modes is not None and self.mode not in tool_modes:
                                logger.debug("跳过工具 %s (模式 %s 不适用)",
                                             module_name, self.mode)
                                continue

                            tool_name = tool_instance.function_config["function"]["name"]

                            # 注入工具标签（帮助 LLM 理解工具用途）
                            tags = tool_instance.tags
                            if tags:
                                tool_instance.function_config["function"]["tags"] = list(tags)

                            # 注册到工具字典
                            self.tools[tool_name] = tool_instance
                            # 添加到本地配置列表
                            self.local_function_configs.append(tool_instance.function_config)
                            logger.info(f"已加载本地工具: {tool_name}")
                except Exception as e:
                    logger.error(f"加载本地工具{module_name}失败: {str(e)}")

        # 2. 加载 MCP 工具 (MCP Tools) - 支持懒加载
        mcp_servers: dict = config.get("mcp_server", {})
        for server_name, server_config in mcp_servers.items():
            if server_config.get("lazy", False):
                # 标记为懒加载，不立即连接
                server_config["name"] = server_name
                self._lazy_mcp_servers[server_name] = server_config
                logger.info(f"MCP服务器已注册(懒加载): {server_name}")
                continue

            try:
                self._connect_mcp_server(server_name, server_config)
            except Exception as e:
                logger.error(f"加载MCP服务器失败: {str(e)}")
                # 懒加载模式下失败不阻止启动，转为待加载
                server_config["name"] = server_name
                self._lazy_mcp_servers[server_name] = server_config

        # 3. 更新 MCP 工具的向量
        if self.mcp_function_configs:
            self._update_mcp_embeddings()

        # 返回所有工具供 invoke 使用，列表返回全部以防万一
        all_configs = self.local_function_configs + self.mcp_function_configs
        return self.tools, all_configs

    # ── MCP 连接辅助 ─────────────────────────────────────────────
    def _connect_mcp_server(self, server_name: str, server_config: dict):
        from ctf_tool.mcp_adapter import MCPServerAdapter
        server_config["name"] = server_name
        adapter = MCPServerAdapter(server_config)

        for mcp_tool_config in adapter.get_tool_configs():
            tool_name = mcp_tool_config["function"]["name"]
            self.tools[tool_name] = adapter
            self.mcp_function_configs.append(mcp_tool_config)

        # 新工具加入后更新向量缓存
        if self.mcp_function_configs:
            self._update_mcp_embeddings()
        logger.info(f"已加载MCP服务器: {server_name}")

    def load_mcp_lazy(self, server_name: str) -> bool:
        """按需加载指定的懒加载 MCP 服务器。"""
        if server_name not in self._lazy_mcp_servers:
            return False
        cfg = self._lazy_mcp_servers.pop(server_name)
        try:
            self._connect_mcp_server(server_name, cfg)
            return True
        except Exception as e:
            logger.error(f"懒加载MCP服务器失败 [{server_name}]: {e}")
            return False

    def get_lazy_mcp_catalog(self) -> str:
        """返回懒加载 MCP 服务的目录文本，注入 prompt 供 LLM 按需触发加载。

        描述从 config.json 的 mcp_server.<name>.catalog_desc 读取，
        未配置时使用服务名作为回退。
        """
        if not self._lazy_mcp_servers:
            return ""
        lines = ["## 可加载专用工具 (按需激活)"]
        for name in sorted(self._lazy_mcp_servers.keys()):
            cfg = self._lazy_mcp_servers[name]
            desc = cfg.get("catalog_desc", f"MCP服务: {name}")
            aliases = cfg.get("aliases", [])
            hint = f"（在思考中提到 '{name}'"
            if aliases:
                hint += f" 或 '{aliases[0]}'"
            hint += " 即可自动加载）"
            lines.append(f"- {name}: {desc}{hint}")
        return "\n".join(lines) + "\n"

    # ── 动态工具解析器 ────────────────────────────────────────────
    def _get_dynamic_resolver(self):
        if self._dynamic_resolver is None:
            from utils.dynamic_resolver import DynamicToolResolver
            ssh_cfg = self.config.get("tool_config", {}).get("ssh_shell", {})
            self._dynamic_resolver = DynamicToolResolver(ssh_cfg)
        return self._dynamic_resolver

    def inject_probe_state(self, tools_found: list, tools_missing: list):
        """注入 P1 环境探测结果到动态解析器 — 已知存在/缺失的工具跳过 SSH 检查。"""
        if tools_found or tools_missing:
            self._get_dynamic_resolver().set_known_state(tools_found, tools_missing)

    def inject_dynamic_tools(self, tool_names: Set[str], query: str = ""):
        """根据用户反馈中的工具名，动态发现并注入远程/MCP工具。

        这个方法在用户提到具体工具名时被调用，会：
        1. 检查 SSH 远程服务器上是否存在该工具
        2. 检查是否有匹配的懒加载 MCP 服务
        3. 将发现的工具注入到当前会话的工具列表
        """
        resolver = self._get_dynamic_resolver()

        # 1. SSH 远程工具发现
        if resolver.has_ssh:
            resolved = resolver.resolve(tool_names)
            for cfg in resolved:
                tname = cfg["function"]["name"]
                if tname not in self._dynamic_tool_map:
                    self._dynamic_tool_map[tname] = {
                        "cfg": cfg,
                        "remote_cmd": cfg["function"].get("_remote_cmd", ""),
                    }
                    logger.info(f"动态工具已注入: {tname}")

        # 2. 懒加载 MCP 服务匹配（增强：别名 + 子串匹配）
        lower_names = {n.lower() for n in tool_names}
        # 从各服务配置构建别名映射表
        alias_map: Dict[str, str] = {}
        for svc_name, svc_cfg in self._lazy_mcp_servers.items():
            for alias in svc_cfg.get("aliases", []):
                alias_map[alias.lower()] = svc_name
        for svc_name in list(self._lazy_mcp_servers.keys()):
            svc_lower = svc_name.lower()
            matched = svc_lower in lower_names
            if not matched:
                for name in lower_names:
                    if (alias_map.get(name) == svc_lower
                            or svc_lower in name or name in svc_lower):
                        matched = True
                        break
            if matched:
                ok = self.load_mcp_lazy(svc_name)
                if ok:
                    logger.info("MCP服务已按需加载: %s", svc_name)

    def get_dynamic_function_configs(self) -> List[dict]:
        """获取所有已注入的动态工具配置。"""
        return [d["cfg"] for d in self._dynamic_tool_map.values()]

    def execute_dynamic_tool(self, tool_name: str, arguments: dict) -> Optional[str]:
        """执行动态/远程工具。返回执行结果，如果不是动态工具返回 None。"""
        if tool_name not in self._dynamic_tool_map:
            return None

        info = self._dynamic_tool_map[tool_name]
        remote_cmd = info.get("remote_cmd", "")
        content = arguments.get("content", "")

        full_cmd = f"{remote_cmd} {content}" if content else remote_cmd

        # 安全检查
        from utils.security import get_blacklist
        try:
            get_blacklist().check_or_raise(full_cmd)
        except Exception as e:
            return f"命令被安全策略拦截: {e}"

        ssh_cfg = self._get_dynamic_resolver()._ssh_config
        host = ssh_cfg.get("host", "127.0.0.1")
        port = ssh_cfg.get("port", 22)
        username = ssh_cfg.get("username", "")
        password = ssh_cfg.get("password", "")

        try:
            import paramiko
        except ImportError:
            return "错误: paramiko 未安装，无法执行远程工具"

        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.WarningPolicy())
        try:
            client.connect(
                hostname=host, port=port, username=username, password=password,
                timeout=10, allow_agent=False, look_for_keys=False,
            )
            _, stdout, stderr = client.exec_command(full_cmd, timeout=30)
            out = stdout.read().decode("utf-8", errors="replace")
            err = stderr.read().decode("utf-8", errors="replace")
            return (out + "\n" + err).strip() or "(无输出)"
        except Exception as e:
            return f"远程工具执行失败 [{tool_name}]: {e}"
        finally:
            try:
                client.close()
            except Exception:
                pass

    # ── 工具推荐 ──────────────────────────────────────────────────
    def recommend_tools(self, query: str, top_k: int = 3,
                        force_tools: Optional[Set[str]] = None) -> List[Dict]:
        """
        根据查询内容推荐工具。
        逻辑：返回 [所有本地工具] + [名称匹配的 MCP 工具] + [Top-K 相似的 MCP 工具] + [动态工具]

        Args:
            query: 查询文本（思考内容）
            top_k: 向量相似度返回的 MCP 工具数
            force_tools: 强制包含的工具名集合（来自用户反馈中明确提及的工具）
        """
        result = list(self.local_function_configs)

        # 0. 动态工具注入（来自用户反馈中的工具名）
        if force_tools:
            self.inject_dynamic_tools(force_tools, query)
        dynamic_cfgs = self.get_dynamic_function_configs()
        if dynamic_cfgs:
            result.extend(dynamic_cfgs)

        if not self.mcp_function_configs:
            return result

        # 1. 名称精确匹配 —— 用户明确提到的 MCP 工具直接入选
        name_matched: List[dict] = []
        remaining: List[dict] = []
        if force_tools:
            lower_force = {n.lower() for n in force_tools}
            for cfg in self.mcp_function_configs:
                tname = cfg["function"]["name"]
                if tname.lower() in lower_force or any(
                    f in tname.lower() for f in lower_force
                ):
                    name_matched.append(cfg)
                else:
                    remaining.append(cfg)
        else:
            remaining = list(self.mcp_function_configs)

        # 2. 向量相似度
        query_embedding = self._get_embedding(query)
        if not query_embedding:
            logger.warning("无法获取查询向量，返回所有 MCP 工具")
            result.extend(name_matched)
            result.extend(remaining[:top_k])
            return result

        scores = []
        for config in (remaining if remaining else self.mcp_function_configs):
            tool_name = config["function"]["name"]
            cached = self.tool_embeddings_map.get(tool_name)
            if cached and "embedding" in cached:
                similarity = self._cosine_similarity(query_embedding, cached["embedding"])
                scores.append((similarity, config))
            else:
                scores.append((-1.0, config))

        scores.sort(key=lambda x: x[0], reverse=True)
        top_similar = [item[1] for item in scores[:top_k]]

        # 3. 合并：名称匹配 > 向量相似
        result.extend(name_matched)
        for cfg in top_similar:
            if cfg not in result:
                result.append(cfg)

        logger.info(
            "工具推荐: 本地=%d 动态=%d 名称匹配=%d 向量=%d",
            len(self.local_function_configs), len(dynamic_cfgs),
            len(name_matched), len(top_similar),
        )
        return result

    @staticmethod
    def _cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
        """计算余弦相似度"""
        if not vec_a or not vec_b:
            return 0.0
        try:
            a = np.array(vec_a)
            b = np.array(vec_b)
            norm_a = np.linalg.norm(a)
            norm_b = np.linalg.norm(b)
            if norm_a == 0 or norm_b == 0:
                return 0.0
            return float(np.dot(a, b) / (norm_a * norm_b))
        except Exception:
            return 0.0

    @staticmethod
    def parse_tool_response(response: ModelResponse) -> Dict:
        """统一解析工具调用响应（单工具，向后兼容）。"""
        calls = ToolUtils.parse_tool_calls(response)
        return calls[0] if calls else {}

    @staticmethod
    def _parse_xml_tool_calls(content: str) -> List[Dict]:
        """从 XML 格式解析工具调用（v2 prompt 输出格式）。

        格式: <tool_calls><tool_call name="..."><arg key="...">val</arg></tool_call></tool_calls>
        """
        import xml.etree.ElementTree as ET
        import re
        # 提取 <tool_calls> 块（可能被思考文本包围）
        m = re.search(r'<tool_calls>(.*?)</tool_calls>', content, re.DOTALL)
        if not m:
            return []
        try:
            root = ET.fromstring("<tool_calls>" + m.group(1) + "</tool_calls>")
        except ET.ParseError:
            return []
        result = []
        for tc in root.findall("tool_call"):
            name = tc.get("name", "")
            args = {}
            for arg in tc.findall("arg"):
                key = arg.get("key", "")
                val = arg.text or ""
                args[key] = val.strip()
            if name:
                result.append({"tool_name": name, "arguments": args})
        return result

    @staticmethod
    def parse_tool_calls(response: ModelResponse) -> List[Dict]:
        """解析工具调用响应，返回工具调用列表。支持原生 tool_calls / JSON / XML。"""
        message = response.choices[0].message

        # 1. 原生 tool_calls（兼容模式）
        if hasattr(message, "tool_calls") and message.tool_calls:
            result = []
            for tc in message.tool_calls:
                func_name = tc.function.name
                try:
                    args = json.loads(tc.function.arguments)
                except json.JSONDecodeError as e:
                    try:
                        args = fix_json_with_llm(tc.function.arguments, e)
                    except Exception:
                        args = {}
                result.append({"tool_name": func_name, "arguments": args})
            return result

        content = message.content.strip()

        # 2. 尝试 JSON 解析（优先）
        try:
            data = json.loads(content)
        except json.JSONDecodeError as e:
            try:
                content = fix_json_with_llm(content, e)
                data = json.loads(content)
            except Exception:
                data = None

        if data is not None:
            # 2a. tool_calls 数组格式
            if "tool_calls" in data and isinstance(data["tool_calls"], list):
                result = []
                for tc in data["tool_calls"]:
                    result.append({
                        "tool_name": tc.get("name") or tc.get("tool_name", ""),
                        "arguments": tc.get("arguments", {}),
                    })
                return result

            # 2b. 向后兼容：单工具格式
            if "name" in data or "tool_name" in data:
                return [{
                    "tool_name": data.get("name") or data.get("tool_name", ""),
                    "arguments": data.get("arguments", {}),
                }]

        # 3. 回退 XML 解析
        xml_calls = ToolUtils._parse_xml_tool_calls(content)
        if xml_calls:
            return xml_calls

        return []

    def output_summary(
        self, tool_name: str, tool_arg: str, think: str, tool_output: str
    ) -> str:
        raw = str(tool_output)
        # 小于 4KB 的输出直接返回原文，避免 LLM 摘要捏造/遗漏关键信息
        if len(raw) <= 4096:
            return raw
        prompt = (
            "你是一个CTF解题助手，任务是忠实地压缩工具输出。\n"
            "关键规则：\n"
            "1. 必须逐字保留 flag{...}、路径、端点、表单字段名、参数名、IP/端口等关键信息\n"
            "2. 禁止添加输出中没有的信息（如编造响应字节数、HTTP 状态码等）\n"
            "3. 输出中如果有 \"Flag:\" 或 \"flag{\" 相关内容，必须原样保留\n"
            "4. 压缩后尽量保持原文顺序，只删除冗余的 HTML 标签和格式化空白\n"
            f"思路：{think}\n"
            f"工具名称：{tool_name}\n"
            f"工具参数：{tool_arg}\n"
            f"工具输出：{raw[:20480]}"
        )
        try:
            response = self.summary_llm.text_completion(prompt, json_check=False)
            return response.choices[0].message.content
        except Exception:
            return raw