import hashlib
import os
import time
import yaml
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from config import Config, get_project_root
from rag.knowledge_base import KnowledgeBase
from agent.analyzer import Analyzer
from typing import Dict, Tuple, List, Optional
from agent.memory import Memory
from agent.checkpoint import CheckpointManager
from agent.attack_surface import AttackSurface
from agent.user_interface import UserInterface, CLIUserInterface
from utils.llm_request import LLMRequest
from jinja2 import Environment, FileSystemLoader
from utils.tools import ToolUtils
from utils.tool_cache import ToolCache
from utils.output_parser import parse as parse_tool_output
from ctf_tool.base_tool import BaseTool
from ctf_tool.flag_detector import detect_flag
from ctf_tool.mcp_adapter import MCPServerAdapter
from utils.skill_loader import load_skill_context
from utils.dynamic_resolver import extract_tool_mentions

logger = logging.getLogger(__name__)


class SolveAgent:
    def __init__(self, problem: str, agent_options: dict = None, knowledge_base=None, mode: str = "ctf",
                 checkpoint_data: Optional[dict] = None,
                 attack_surface: Optional[AttackSurface] = None,
                 ui: Optional[UserInterface] = None):
        self.config = Config.load_config()
        self.solve_llm = LLMRequest("solve_agent")
        self.problem = problem
        self.mode = mode
        # 阶段跟踪（recon → exploit，渗透测试多一个 report）
        self.current_phase = "recon"
        # 根据模式加载不同的 Prompt 文件
        prompt_file = "pentest_prompt.yaml" if mode == "pentest" else "prompt.yaml"
        prompt_path = os.path.join(get_project_root(), "prompts", self.config.get('prompt_version', 'v1'), prompt_file)
        with open(prompt_path, "r", encoding="utf-8") as f:
            self.prompt: dict = yaml.safe_load(f)
        self.env = Environment(loader=FileSystemLoader(
            os.path.join(get_project_root(), "prompts", self.config.get("prompt_version", "v1"))
        ))

        # 初始化记忆系统
        self.memory = Memory()
        # 动态加载工具和分类信息
        self.tools: Dict[str, BaseTool] = {}  # 工具名称 -> 工具实例
        self.function_configs: List[Dict] = []  # 函数调用配置列表
        self.tool_classification: Dict = {}  # 工具分类信息

        # 动态加载工具 (传递模式信息)
        self.analyzer = Analyzer(config=self.config, problem=self.problem, mode=mode)

        # 加载ctf_tools文件夹中的所有工具（按模式过滤）
        self.tool = ToolUtils(mode=mode)
        self.tools, self.function_configs = self.tool.load_tools()
        # 工具结果缓存（相同参数 TTL 内复用）
        self.tool_cache = ToolCache(
            ttl_seconds=self.config.get("tool_cache_ttl", 300)
        )

        # 环境探测 — Kali 可用工具/Python模块/网络（注入每步 prompt）
        self._env_context = ""
        self._probe_result = None  # 保留原始探测结果供 P2/P3 使用
        try:
            from utils.env_probe import probe_environment, format_env_context
            self._probe_result = probe_environment()
            self._env_context = format_env_context(self._probe_result)
            if self._env_context:
                logger.info("已加载环境上下文 (%d 字符)", len(self._env_context))
            # P2: 注入探测结果到动态工具解析器 — 已知存在/缺失的工具跳过 SSH 检查
            if self._probe_result:
                self.tool.inject_probe_state(
                    self._probe_result.get("tools_found", []),
                    self._probe_result.get("tools_missing", []),
                )
        except Exception as e:
            logger.warning("环境探测失败 (不影响解题): %s", e)

        # 预加载安全技能库上下文（仅在渗透模式下加载索引 + 路由表）
        self.skill_context = ""
        if self.mode == "pentest":
            try:
                self.skill_context = load_skill_context()
                if self.skill_context:
                    logger.info(f"已加载安全技能库上下文 ({len(self.skill_context)} 字符)")
            except Exception as e:
                logger.warning(f"加载技能库失败: {e}")

        # 用户界面（需在 _select_mode 之前初始化，因为模式选择用到 ui.choose）
        self.ui = ui or CLIUserInterface()

        # ---- 选项 ----
        options = agent_options or {}
        # auto_mode: True=自动, False=手动, None=未指定（稍后交互选择）
        self.auto_mode: Optional[bool] = options.get("auto_mode", None)
        self._stop_event = options.get("stop_event")
        self._interactive = options.get("interactive", False)
        self._max_steps = self.config.get("max_solve_steps", 100)

        # ---- Checkpoint 恢复 ----
        if checkpoint_data:
            self._restore_from_checkpoint(checkpoint_data)
            # 恢复后跳过模式选择（已决定）
        else:
            # 弹出模式选择（auto_mode 未指定时交互询问）
            self._select_mode()

        # 攻击面管理（仅渗透模式使用）
        if attack_surface is not None:
            self.attack_surface = attack_surface
        elif self.mode == "pentest":
            as_data = checkpoint_data.get("agent_state", {}).get("attack_surface") if checkpoint_data else None
            if as_data:
                self.attack_surface = AttackSurface.from_dict(as_data)
            else:
                self.attack_surface = AttackSurface()
        else:
            self.attack_surface = None

        # 知识库（可空，由 Workflow 传入；所有调用点均需做 None 防护）
        self.knowledge_base = knowledge_base

        # RAG 查询缓存（相同/相似 query 在 TTL 内复用）
        self._rag_cache: Dict[str, tuple] = {}
        self._rag_cache_ttl = 300

        # 步骤零上下文 — 解题开始前从知识库匹配的同类经验
        self._step_zero_context = ""

        # 添加flag确认回调函数
        self.confirm_flag_callback = None  # 将由Workflow设置

        # ---- 僵局检测与策略切换 ----
        if not checkpoint_data:
            self._init_stuck_detection()

        # 渗透模式: 漏洞验证调度（likely → 自动验证）
        self._pending_verification: Optional[Dict] = None  # {type, target, attempts}

    def _init_stuck_detection(self):
        """初始化僵局检测状态。"""
        self._step_count = 0
        self._stuck_counter = 0
        self._max_stuck_steps = self.config.get("max_stuck_steps", 5)
        self._recent_output_samples: List[str] = []  # 最近输出样本（用于语义相似度比较）
        self._recent_tools: List[str] = []
        self._tried_strategies: List[str] = []
        self._strategy_switch_count = 0
        self._checkpoint_interval = self.config.get("checkpoint_interval", 5)
        # v3: 思考内容循环检测 + 连续无进展终止
        self._recent_thoughts: List[str] = []  # 最近思考内容（检测 LLM 思维循环）
        self._consecutive_none_progress = 0  # 连续无进展计数
        self._max_consecutive_none = 5  # 连续无进展上限，超过强制终止
        self._last_combined_output = ""  # 上一步原始输出，用于输出变化检测
        self._recent_tool_errors: List[bool] = []  # 最近工具执行是否出错（僵局维度6）
        self._last_step_time: float = 0.0  # 上一步完成时间
        self._min_step_interval = 3.0  # 最小步间隔 (秒)，防止过速
        # 防缓存死锁: 检测 think 和 tool 的连续重复
        self._bypass_semantic_cache = False  # 下一次 LLM 调用是否绕过语义缓存
        self._last_think_normalized = ""     # 上一步 think 的归一化指纹
        self._consecutive_identical_think = 0  # 连续相同 think 的次数
        self._llm_failure_count = 0  # 连续 LLM 调用失败计数
        self._max_llm_failures = 3  # 连续失败上限

    # ── 阶段感知 ──────────────────────────────────────────────────

    @property
    def _min_recon_steps(self) -> int:
        """信息收集阶段最少步数（之后才允许切阶段）。"""
        return 4 if self.mode == "pentest" else 3

    @property
    def _think_template_key(self) -> str:
        """根据当前阶段返回对应的 think 模板键名，不存在时回退 think_next。"""
        phase_map = {
            "recon": "think_recon",
            "exploit": "think_exploit",
            "report": "think_report",
        }
        key = phase_map.get(self.current_phase, "think_next")
        if key not in self.prompt:
            key = "think_next"
        return key

    def _check_phase_transition(self, analysis: dict):
        """根据分析结果判断是否切换阶段。

        Recon → Exploit 条件（需同时满足最小步数）:
          - 僵局累计 ≥3 步，或
          - 僵局 ≥2 步且近期无新发现、无关键事实积累
        避免因单步无进展就过早切换。
        """
        if self.current_phase == "recon" and self._step_count >= self._min_recon_steps:
            # 评估侦察覆盖率（v2: 用 progress_level 替代 new_info）
            unique_tools = len(set(self._recent_tools[-6:])) if self._recent_tools else 0
            fact_count = len(self.memory.journal_entries) + len(self.memory._external_facts)
            progress = analysis.get("progress_level", "")
            has_recent_progress = progress in ("significant", "moderate")

            # 有足够覆盖率时不应切换（至少积累了关键事实或用过多种工具）
            has_coverage = has_recent_progress or fact_count >= 3 or unique_tools >= 3

            should_transition = False
            if self._stuck_counter >= 3:
                should_transition = True
            elif self._stuck_counter >= 2 and not has_coverage:
                should_transition = True

            if should_transition:
                self.current_phase = "exploit"
                logger.info("阶段切换: recon → exploit (步数=%d, stuck=%d, facts=%d, tools=%d)",
                            self._step_count, self._stuck_counter, fact_count, unique_tools)
                self.ui.display("\n[阶段切换] 进入漏洞利用阶段")
        elif self.current_phase == "exploit" and self.mode == "pentest":
            if analysis.get("terminate_all", False):
                self.current_phase = "report"
                logger.info("阶段切换: exploit → report")
                self.ui.display("\n[阶段切换] 进入报告收尾阶段")

    def _restore_from_checkpoint(self, data: dict):
        """从 checkpoint 恢复 agent 运行时状态。"""
        self._step_count = data["meta"]["step_count"]
        as_ = data["agent_state"]
        self.auto_mode = as_.get("auto_mode", self.auto_mode)
        self.current_phase = as_.get("current_phase", self.current_phase)
        self._stuck_counter = as_.get("stuck_counter", 0)
        self._max_stuck_steps = self.config.get("max_stuck_steps", 5)
        self._recent_tools = as_.get("recent_tools", [])
        self._recent_output_samples = as_.get("recent_output_samples", [])
        self._tried_strategies = as_.get("tried_strategies", [])
        self._strategy_switch_count = as_.get("strategy_switch_count", 0)
        self._checkpoint_interval = self.config.get("checkpoint_interval", 5)
        self._recent_thoughts = as_.get("recent_thoughts", [])
        self._consecutive_none_progress = as_.get("consecutive_none_progress", 0)
        self._max_consecutive_none = 5
        self._last_step_time = 0.0
        self._min_step_interval = 3.0
        self._last_combined_output = as_.get("last_combined_output", "")
        self._recent_tool_errors = as_.get("recent_tool_errors", [])
        self._bypass_semantic_cache = as_.get("bypass_semantic_cache", False)
        self._last_think_normalized = as_.get("last_think_normalized", "")
        self._consecutive_identical_think = as_.get("consecutive_identical_think", 0)
        self._llm_failure_count = as_.get("llm_failure_count", 0)
        self._max_llm_failures = 3
        mem = data.get("memory", {})
        self.memory.history = mem.get("history", [])
        self.memory.journal_entries = mem.get("journal_entries", [])
        self.memory.consolidated_narrative = mem.get("consolidated_narrative", "")
        self.memory._external_facts = mem.get("external_facts", [])
        self.memory.failed_attempts = mem.get("failed_attempts", {})
        logger.info("已从 checkpoint 恢复 (步数 %d, 日志 %d 条, 阶段=%s)",
                     self._step_count, len(self.memory.journal_entries), self.current_phase)

    def _save_checkpoint(self):
        """保存当前运行时 checkpoint（含攻击面和阶段状态）。"""
        extra = {"current_phase": self.current_phase}
        if self.attack_surface:
            extra["attack_surface"] = self.attack_surface.to_dict()
        CheckpointManager.save(self, self._step_count, self.problem, self.mode, extra=extra)

    def save_checkpoint(self):
        """公开接口：保存 checkpoint（供 TUI 快捷键调用）。"""
        self._save_checkpoint()

    def _clear_checkpoint(self):
        """成功解题后清除 checkpoint。"""
        CheckpointManager.clear_key(self.problem, self.mode)

    def clear_checkpoint(self):
        """公开接口：清除 checkpoint（供 TUI 调用）。"""
        self._clear_checkpoint()

    def _select_mode(self):
        """让用户选择交互模式（EOF/OSError 时自动退避为自动模式，真实错误向上传播）。"""
        import sys
        # 如果调用方已通过 agent_options 明确设置 auto_mode，跳过交互选择
        if self.auto_mode is not None:
            logger.info("auto_mode 已由外部指定 (%s)，跳过交互选择",
                        "自动" if self.auto_mode else "手动")
            return
        # 如果 stdin 不是 TTY 且未强制交互模式，直接使用自动模式
        is_tty = hasattr(sys.stdin, 'isatty') and sys.stdin.isatty()
        if not is_tty:
            logger.info("stdin 非 TTY，默认使用自动模式")
            self.auto_mode = True
            return
        try:
            choice = self.ui.choose(
                "请选择交互模式:",
                ["自动模式（Agent自动生成和执行所有操作）",
                 "手动模式（每一步需要操作者批准，可提供反馈引导方向）"],
            )
            self.auto_mode = "自动模式" in choice
            logger.info("已选择%s模式", "自动" if self.auto_mode else "手动")
        except (EOFError, OSError):
            logger.warning("非交互环境（stdin 不可读），默认使用自动模式")
            self.auto_mode = True

    def solve(self) -> str:
        """
        主解题函数 - 采用逐步执行方式
        :return: 获取的flag
        """
        if self._step_count == 0:
            logger.info("开始新解题流程")
            # 清除语义缓存防止跨会话污染（上次崩溃/中断的残留推理链）
            try:
                from utils.semantic_cache import reset_session_cache
                reset_session_cache()
            except Exception:
                pass
            # 重置成本计数器，防止跨任务累积导致新任务误熔断
            try:
                from utils.token_tracker import get_token_tracker
                get_token_tracker().reset()
            except Exception:
                pass
            # 步骤零：解题前从知识库匹配同类经验，作为初始上下文
            self._load_step_zero_context()
            # P2: 按题型自动激活匹配的 MCP 服务
            self._auto_activate_mcp()
        else:
            self.ui.display(f"\n从第 {self._step_count + 1} 步继续执行...")
            # M-13 + L-16 修复：恢复后重跑步骤零上下文加载 + MCP 自动激活
            # 根因：__init__ 中 _step_zero_context="" / _ctf_category 未设置，
            # 且这两个初始化只在 _step_count==0 分支跑，恢复后跳过 →
            # 早期中断恢复无同类经验参考 + 按题型激活的 MCP 工具丢失（"未找到工具"）
            # MCP 子进程本就无法跨进程恢复，重新激活是唯一稳策略
            try:
                self._load_step_zero_context()
                self._auto_activate_mcp()
            except Exception as e:
                logger.warning("恢复后重跑步骤零/MCP 激活失败 (不影响解题): %s", e)

        while True:
            # 检查外部终止信号
            if self._stop_event and self._stop_event.is_set():
                logger.info("收到外部终止信号")
                self._save_checkpoint()
                return "解题终止"

            self._step_count += 1
            if self._step_count > self._max_steps:
                logger.warning("达到最大步数 %d，强制终止", self._max_steps)
                self._save_checkpoint()
                return "解题终止：达到最大步数限制"

            # ── 成本熔断 ──
            max_cost = self.config.get("max_solve_cost_usd", 0)
            if max_cost > 0:
                from utils.token_tracker import get_token_tracker
                current_cost = get_token_tracker().snapshot()["cost"]
                if current_cost >= max_cost:
                    logger.warning("达到成本上限 $%.2f (已用 $%.2f)，保存 checkpoint 并终止",
                                   max_cost, current_cost)
                    self._save_checkpoint()
                    return f"解题终止：达到成本上限 ${max_cost}"

            self.ui.display(f"\n正在思考第 {self._step_count} 步...")

            # 生成下一步执行命令
            if self._stop_event and self._stop_event.is_set():
                self._save_checkpoint()
                return "解题终止"
            next_step = self.next_instruction()
            if not next_step:
                if self._llm_failure_count >= self._max_llm_failures:
                    logger.error("LLM 连续失败 %d 次，强制终止", self._llm_failure_count)
                    self._save_checkpoint()
                    return "解题终止：LLM 调用连续失败"
                self.ui.display("生成执行内容失败，重试中...")
                continue
            think, tool_calls = next_step

            # ── 防缓存死锁: 检测 LLM 思考循环 ──
            think_fingerprint = self._normalize_think(think)
            if think_fingerprint == self._last_think_normalized and think_fingerprint:
                self._consecutive_identical_think += 1
                if self._consecutive_identical_think >= 2:
                    logger.warning(
                        "检测到 LLM 思维循环 (%d 次相同 think)，绕过语义缓存",
                        self._consecutive_identical_think,
                    )
                    self._bypass_semantic_cache = True
                    self.tool_cache.invalidate(
                        tool_calls[0].get("tool_name", "")
                        if tool_calls else ""
                    )
            else:
                self._consecutive_identical_think = 0
                self._bypass_semantic_cache = False
            self._last_think_normalized = think_fingerprint

            # 手动模式：需要用户批准命令
            if not self.auto_mode:
                approved, next_step = self.manual_approval_step(next_step)
                if not approved:
                    self.ui.display("用户终止解题")
                    self._save_checkpoint()
                    return "解题终止"
                think, tool_calls = next_step

            # ── 执行所有工具（并行 + 缓存） ──
            tool_outputs: List[str] = []
            tools_used: List[str] = []
            if len(tool_calls) > 1:
                ordered_outputs: Dict[int, tuple] = {}
                executor = ThreadPoolExecutor(max_workers=min(len(tool_calls), 5))
                try:
                    fut_map = {
                        executor.submit(self._execute_single_tool, tc, think): i
                        for i, tc in enumerate(tool_calls)
                    }
                    for future in as_completed(fut_map):
                        idx = fut_map[future]
                        try:
                            ordered_outputs[idx] = future.result()
                        except Exception as e:
                            tc = tool_calls[idx]
                            ordered_outputs[idx] = (tc.get("tool_name", "?"), f"工具执行出错: {str(e)}")
                finally:
                    executor.shutdown(wait=True)

                for idx in range(len(tool_calls)):
                    tname, output = ordered_outputs[idx]
                    tool_outputs.append(f"--- [{tname}] ---\n{output}")
                    tools_used.append(tname)
            else:
                # 单工具直接执行，避免线程开销
                tc = tool_calls[0]
                tname, output = self._execute_single_tool(tc, think)
                tool_outputs.append(f"--- [{tname}] ---\n{output}")
                tools_used.append(tname)

            combined_output = "\n".join(tool_outputs)
            logger.info(f"工具输出:\n{combined_output}")

            # ── 工具错误率追踪（供僵局检测维度6使用） ──
            _lower_out = combined_output.lower()
            _is_error = any(kw in _lower_out for kw in (
                "工具执行出错", "connection refused", "timed out",
                "permission denied", "not found", "no such file",
                "invalid", "error", "traceback", "exception",
            ))
            self._recent_tool_errors.append(_is_error)
            if len(self._recent_tool_errors) > 10:
                self._recent_tool_errors.pop(0)

            # ── P3: 检测工具安装 — 动态更新环境上下文 ──
            if self._probe_result and combined_output:
                try:
                    from utils.env_probe import detect_new_installations
                    new_tools = detect_new_installations(combined_output)
                    for t in new_tools:
                        if t in self._probe_result.get("tools_missing", []):
                            self._probe_result["tools_missing"].remove(t)
                        if t not in self._probe_result.get("tools_found", []):
                            self._probe_result["tools_found"].append(t)
                        # 通知动态解析器该工具现在可用
                        if hasattr(self.tool, '_get_dynamic_resolver'):
                            self.tool._get_dynamic_resolver().mark_available(t)
                    if new_tools:
                        from utils.env_probe import format_env_context
                        self._env_context = format_env_context(self._probe_result)
                        logger.info("环境上下文已更新: 新安装工具 %s", new_tools)
                except Exception:
                    pass  # P3 失败不影响解题

            # ── Flag 正则预检测（在 LLM 分析前） ──
            pre_flag = detect_flag(combined_output) if self.mode == "ctf" else None
            if pre_flag:
                logger.info("正则预检测到 flag: %s", pre_flag)

            # 快速分析（零 LLM 成本，适用于简单场景）
            analysis_result = self._quick_analysis(combined_output, pre_flag)
            if analysis_result is None:
                # LLM 分析（仅当快速分析无法处理时）
                try:
                    analysis_result = self.analyzer.analyze_step_output(
                        self.memory, think, combined_output, self._step_count
                    )
                except Exception as e:
                    logger.warning("LLM 分析异常，降级为空分析: %s", e)
                    analysis_result = {"analysis": f"分析失败: {e}", "progress_level": "none"}
            else:
                logger.info("跳过 LLM 分析 (快速分析命中, 模式=%s)",
                            "flag" if pre_flag else ("短输出" if len(combined_output) < 200 else "枚举"))

            # ── P1: 凭据检测 — 自动提取密码/Token/哈希/密钥 ──
            if self.mode == "pentest" and self.attack_surface:
                self._detect_credentials(combined_output, analysis_result)

            # 安全网: 确保 analysis_result 是 dict（防止上游返回非预期类型导致 .get() 崩溃）
            if not isinstance(analysis_result, dict):
                logger.warning("analysis_result 类型异常 (%s)，使用空字典回退", type(analysis_result).__name__)
                analysis_result = {"analysis": str(analysis_result), "progress_level": "none"}

            # ── CTF 模式: 综合判定 flag（正则优先于 LLM） ──
            if self.mode == "ctf":
                llm_flag = analysis_result.get("flag", "")
                llm_found = analysis_result.get("flag_found", False)
                flag_candidate = pre_flag or llm_flag
                if pre_flag or llm_found:
                    logger.info("发现flag: %s (regex=%s, llm=%s)", flag_candidate, bool(pre_flag), llm_found)
                    if self.confirm_flag_callback and self.confirm_flag_callback(
                        flag_candidate
                    ):
                        self._clear_checkpoint()
                        return flag_candidate
                    else:
                        logger.info("用户确认flag不正确，继续解题")

            # ── 渗透模式: 收集漏洞发现 + 验证调度 ──
            if self.mode == "pentest" and analysis_result.get("vulnerability_found", False):
                vuln = analysis_result.get("vulnerability", {})
                if vuln and isinstance(vuln, dict):
                    conf = vuln.get("confidence", "")
                    logger.info(f"发现漏洞: {vuln.get('type', '未知')} ({vuln.get('severity', 'unknown')}) [{conf}]")
                    self.ui.display(f"\n⚠ 发现漏洞: {vuln.get('type', '未知')} — {vuln.get('severity', 'unknown')}")
                    self.ui.display(f"   置信度: {conf}")
                    self.ui.display(f"   受影响: {vuln.get('affected_component', 'N/A')}")

                    # ── 验证闭环: likely → 自动触发验证 ──
                    if self._pending_verification:
                        self._pending_verification["attempts"] += 1
                        if conf in ("confirmed", "possible"):
                            logger.info("漏洞验证完成: %s → %s",
                                       self._pending_verification["type"], conf)
                            self._pending_verification = None
                        elif conf == "likely" and self._pending_verification["attempts"] >= 2:
                            logger.info("漏洞验证未确认 (%d 次尝试)，放弃",
                                       self._pending_verification["attempts"])
                            self._pending_verification = None
                    elif conf == "likely":
                        self._pending_verification = {
                            "type": vuln.get("type", "unknown"),
                            "target": vuln.get("affected_component", "unknown"),
                            "attempts": 0,
                        }
                        self.ui.display(f"   [验证调度] 下一步将自动生成验证 payload")

            # ── 更新攻击面（渗透模式） ──
            if self.mode == "pentest" and self.attack_surface:
                for tool_call in tool_calls:
                    self.attack_surface.analyze_step(
                        tool_name=tool_call.get("tool_name"),
                        tool_args=tool_call.get("arguments", {}),
                        output=combined_output,
                        analysis=analysis_result,
                    )

            # ── 阶段切换检查 ──
            self._check_phase_transition(analysis_result)

            # ── 输出摘要（LLM 摘要替代硬截断，保留技术细节供后续决策使用） ──
            output_summary = self._summarize_output(combined_output)

            # 添加执行历史到记忆系统（多工具合并为一步）
            # 确定来源引用类型
            source_citation = "[AI推理]"
            if tools_used:
                source_citation = "[工具发现]"
            if self._step_zero_context and self._step_count <= 2:
                source_citation = "[经验库匹配]"  # 前几步受步骤零影响

            self.memory.add_step(
                {
                    "step": self._step_count,
                    "think": think,
                    "tool_name": ", ".join(tools_used) if len(tools_used) > 1 else tools_used[0],
                    "tool_args": tool_calls,
                    "output": combined_output,
                    "output_summary": output_summary,
                    "analysis": analysis_result,
                    "source_citation": source_citation,
                }
            )

            # ── 解题日志 — LLM 叙事追加（每步一次，永不压缩） ──
            try:
                primary_tool = tools_used[0] if tools_used else "none"
                self._write_journal_entry(
                    self._step_count, think, primary_tool,
                    tool_calls, combined_output, analysis_result,
                )
            except Exception as e:
                logger.warning("解题日志写入失败 (不影响解题): %s", e)

            # ── 步速控制：最小步间隔，防止 LLM 过快循环 ──
            now = time.time()
            if self._last_step_time > 0:
                elapsed = now - self._last_step_time
                if elapsed < self._min_step_interval:
                    time.sleep(self._min_step_interval - elapsed)
            self._last_step_time = time.time()

            # ── 思考内容循环检测 ──
            thought_intent = self._extract_thought_intent(think)
            self._recent_thoughts.append(thought_intent)
            if len(self._recent_thoughts) > 8:
                self._recent_thoughts.pop(0)

            # 僵局检测：检查是否在重复无进展的操作
            primary_tool = tools_used[0] if tools_used else "none"
            if self._detect_stuck_step(self._step_count, think, primary_tool, combined_output, analysis_result):
                self._stuck_counter += 1
                logger.warning(f"检测到可能的僵局 (第 {self._stuck_counter}/{self._max_stuck_steps} 次)")

                if self._stuck_counter >= self._max_stuck_steps:
                    logger.info("达到最大僵局次数，触发策略切换")
                    self._strategy_switch_count += 1
                    self._tried_strategies.append(think)
                    self._stuck_counter = 0
                    switch_instruction = self._build_switch_prompt()
                    self.memory.add_fact(f"[策略切换 #{self._strategy_switch_count}] {switch_instruction[:200]}")
            elif self._has_progress(analysis_result):
                self._stuck_counter = 0
                self._consecutive_none_progress = 0

            # ── 连续无进展检测：progress_level=none 连续 N 次 → 强制终止 ──
            # 例外: 输出显著变化（>30% 不同）视为有新进展，复位计数器
            # 解决多步攻击链中准备步骤（payload构造/监听器启动等）被误判为无进展的问题
            output_changed = self._output_significantly_changed(
                combined_output, self._last_combined_output
            )
            if analysis_result.get("progress_level", "") == "none":
                if output_changed:
                    logger.info("输出显著变化，复位连续无进展计数器（攻击链进行中）")
                    self._consecutive_none_progress = 0
                else:
                    self._consecutive_none_progress += 1
                    logger.warning("连续无进展: %d/%d", self._consecutive_none_progress, self._max_consecutive_none)
                    if self._consecutive_none_progress >= self._max_consecutive_none:
                        logger.warning("连续 %d 步无进展，强制终止 (exhausted)", self._max_consecutive_none)
                        self._save_checkpoint()
                        return "解题终止：连续多步无有效进展 (exhausted_methods)"
            else:
                self._consecutive_none_progress = 0
            self._last_combined_output = combined_output

            # ── TUI 步骤快照回调 ──
            if hasattr(self, '_on_step_done') and self._on_step_done:
                try:
                    snap = self._build_step_snapshot(
                        self._step_count, think, tool_calls,
                        combined_output, analysis_result, tools_used,
                    )
                    self._on_step_done(snap)
                except Exception:
                    pass

            # ── 终止条件 (模式感知) ──
            if self.mode == "pentest":
                if analysis_result.get("terminate_all", False):
                    self.ui.display("LLM 判断渗透测试覆盖率已足够，建议终止")
                    self._save_checkpoint()
                    return "渗透测试完成"
            else:
                if analysis_result.get("terminate", False):
                    self.ui.display("LLM建议提前终止解题")
                    self._save_checkpoint()
                    return "未找到flag：提前终止"

            # ── 自动存档 ──
            if self._step_count % self._checkpoint_interval == 0:
                self._save_checkpoint()

    def manual_approval_step(
        self, next_step: Tuple[str, list]
    ) -> Tuple[bool, Tuple[str, list]]:
        """手动模式：让用户无限次反馈/重思，直到 ta 主动选 1 或 3"""
        while True:
            think, tool_calls = next_step

            self.ui.display(f"\n思考: {think}")
            for tc in tool_calls:
                tc_name = tc.get("tool_name", "?")
                tc_args = tc.get("arguments", {})
                self.ui.display(f"  工具: {tc_name} | 参数: {tc_args}")

            choice = self.ui.choose(
                "选择操作:",
                ["批准并执行", "提供反馈并重新思考", "终止解题"],
            )
            if "批准" in choice:
                return True, next_step
            elif "反馈" in choice:
                feedback = self.ui.prompt_text("请提供改进建议: ")
                new_step = self.reflection(think, feedback)
                if new_step:
                    next_step = new_step
                else:
                    self.ui.display("（思考失败，可继续反馈或选 3 终止）")
            elif "终止" in choice:
                return False, None

    def reflection(self, think: str, feedback: str) -> Optional[Tuple[str, list]]:
        """根据用户反馈重新生成思考内容（v2: 单次调用直接产出工具调用）。"""
        history_summary = self.memory.get_summary(include_key_facts=True)
        template_key = "reflection"
        template = self.env.from_string(self.prompt.get(template_key, self.prompt.get("think_next", "")))
        think_prompt = template.render(
            question=self.problem,
            scope=self.problem,
            history_summary=history_summary,
            original_purpose=think,
            feedback=feedback,
            phase=self.current_phase,
            findings="" if self.mode != "pentest" else self.memory.get_summary(include_key_facts=True)[:500],
            tools_text=self._build_tools_text(),
            skills_text=self._build_skills_text(),
        )

        response = self.solve_llm.text_completion(prompt=think_prompt, json_check=False)
        think_content = response.choices[0].message.content
        logger.info(f"反思内容: {think_content[:200]}...")

        # 从反思内容中提取工具调用
        tool_calls = self._extract_tool_calls_from_content(think_content)
        if tool_calls:
            valid_calls = [tc for tc in tool_calls
                          if tc.get("tool_name", "") in self.tools or tc.get("tool_name", "") in self.tool._dynamic_tool_map]
            if valid_calls:
                return think_content, valid_calls

        # 回退：general_next
        mentioned = extract_tool_mentions(feedback)
        mentioned |= extract_tool_mentions(think_content)
        category_tools = self.tool.recommend_tools(think_content, 3, force_tools=mentioned)
        tool_calls = self.tool_general(history_summary, think_content, category_tools)
        if not tool_calls:
            return None
        return think_content, tool_calls

    def _build_tools_text(self, tool_configs: List[Dict] = None) -> str:
        """将工具配置序列化为紧凑文本注入 prompt（单行/工具，减少 ~70% token）。"""
        configs = tool_configs or self.function_configs
        lines = []
        for cfg in configs:
            func = cfg.get("function", cfg)
            name = func.get("name", "?")
            desc = (func.get("description") or "")[:150]
            params = func.get("parameters", {}).get("properties", {})
            required = func.get("parameters", {}).get("required", [])
            # 紧凑参数列表: param(type,req): 简述
            param_parts = []
            for pname, pinfo in params.items():
                ptype = pinfo.get('type', 'string')
                req = '*' if pname in required else ''
                pdesc = (pinfo.get('description') or '')[:200]
                entry = f"{pname}({ptype}{req})"
                if pdesc:
                    entry += f"={pdesc}"
                param_parts.append(entry)
            params_str = ", ".join(param_parts) if param_parts else "无参数"
            lines.append(f"- {name}: {desc} | 参数: {params_str}")
        text = "\n".join(lines)
        # 仅全量列表时追加懒加载 MCP 目录（LLM 看到后可主动触发加载）
        if tool_configs is None:
            catalog = self.tool.get_lazy_mcp_catalog()
            if catalog:
                text += "\n" + catalog
        return text

    @staticmethod
    def _build_api_tools(configs: List[Dict]) -> List[Dict]:
        """构建原生 function calling 的 tools 参数，剥离内部字段。"""
        result = []
        for cfg in configs:
            func = cfg.get("function", cfg)
            clean = {
                "name": func.get("name", ""),
                "description": (func.get("description") or "")[:1024],
                "parameters": func.get("parameters", {
                    "type": "object", "properties": {}, "required": [],
                }),
            }
            result.append({"type": "function", "function": clean})
        return result

    def _build_cache_fingerprint(self) -> str:
        """构建语义缓存的指纹文本 — 提取 prompt 中真正变化的决策核心。

        完整 prompt 在 40+ 轮后可达 8000+ tokens，超出 embedding API 上限（8192）。
        指纹仅包含 prompt 中 5% 的动态部分（题目锚点/阶段/最近工具/最近思考/输出），
        稳定在 800-1200 tokens，embedding API 不再 400。

        静态部分（env_context/tools_text/skills_text/template）占总 prompt 60%+，
        每步完全相同，不参与 embedding 不损失同会话重复检测能力。
        """
        parts = [self.problem[:400]]
        parts.append(f"phase={self.current_phase}")
        recent_tools = list(dict.fromkeys(self._recent_tools[-6:])) if self._recent_tools else []
        if recent_tools:
            parts.append(f"tools={','.join(recent_tools)}")
        if self._last_think_normalized:
            parts.append(f"think={self._last_think_normalized[:250]}")
        if self._recent_output_samples:
            # 去重保留最近 2 个输出样本
            seen = set()
            unique_outputs = []
            for o in reversed(self._recent_output_samples[-4:]):
                trimmed = o[:120]
                if trimmed not in seen:
                    unique_outputs.append(trimmed)
                    seen.add(trimmed)
            if unique_outputs:
                parts.append(f"output={'|'.join(reversed(unique_outputs[-2:]))}")
        return "\n".join(parts)

    def _build_skills_text(self) -> str:
        """构建技能上下文文本（每步注入，确保 LLM 始终有方法论引导）。"""
        return self.skill_context or ""

    def _extract_tool_calls_from_content(self, content: str) -> List[Dict]:
        """从思考内容中提取工具调用（堆栈法 JSON 解析，回退 XML）。"""
        import json
        for candidate in self._extract_json_blocks(content):
            try:
                data = json.loads(candidate)
            except json.JSONDecodeError:
                continue
            if isinstance(data, dict):
                if "tool_calls" in data and isinstance(data["tool_calls"], list):
                    return [{"tool_name": tc.get("name") or tc.get("tool_name", ""),
                             "arguments": tc.get("arguments", {})}
                            for tc in data["tool_calls"]]
                # 向后兼容：单工具格式
                if "name" in data or "tool_name" in data:
                    return [{"tool_name": data.get("name") or data.get("tool_name", ""),
                             "arguments": data.get("arguments", {})}]
        # 回退 XML 解析
        xml_calls = ToolUtils._parse_xml_tool_calls(content)
        if xml_calls:
            return xml_calls
        return []

    @staticmethod
    def _extract_json_blocks(text: str) -> List[str]:
        """堆栈法提取所有平衡括号的 JSON 对象块，按长度降序。"""
        blocks = []
        depth = 0
        start = -1
        for i, ch in enumerate(text):
            if ch == '{':
                if depth == 0:
                    start = i
                depth += 1
            elif ch == '}':
                if depth > 0:
                    depth -= 1
                    if depth == 0 and start >= 0:
                        blocks.append(text[start:i + 1])
        blocks.sort(key=len, reverse=True)
        return blocks

    def next_instruction(self) -> Optional[Tuple[str, list]]:
        """生成下一步执行命令（v2: think + tool selection 合并为单次调用）。

        :return: (思考内容, 工具调用列表) 或 None
        """
        # ── 同步最新的工具配置（动态工具和 MCP 懒加载后可能已变化） ──
        self.function_configs = (
            self.tool.local_function_configs
            + self.tool.mcp_function_configs
            + self.tool.get_dynamic_function_configs()
        )

        history_summary = self.memory.get_summary(include_key_facts=True)

        # 构建模板变量
        template_vars = {
            "question": self.problem,
            "scope": self.problem,
            "history_summary": history_summary,
            "phase": self.current_phase,
            "ctf_category": getattr(self, '_ctf_category', ''),
            "tools_text": self._build_tools_text(),
            "skills_text": self._build_skills_text(),
            "findings": self.memory.get_summary(include_key_facts=True)[:500] if self.mode == "pentest" else "",
        }

        template_key = self._think_template_key
        template = self.env.from_string(
            self.prompt.get(template_key, self.prompt.get("think_next", ""))
        )
        think_prompt = template.render(**template_vars)

        # 环境上下文 — Kali 能力地图（工具/模块/网络），每步注入
        if self._env_context:
            think_prompt = self._env_context + "\n" + think_prompt

        # 渗透模式：注入攻击面状态 + 凭据 + 优先级队列 + 凭据复用建议
        if self.mode == "pentest" and self.attack_surface:
            think_prompt += f"\n当前攻击面状态:\n{self.attack_surface.get_summary()}\n"
            creds = self.attack_surface.get_credentials_summary()
            if creds:
                think_prompt += f"\n{creds}\n"
            priority = self.attack_surface.get_priority_findings()
            if priority:
                think_prompt += f"\n{priority}"
            reuse = self.attack_surface.get_credential_reuse_suggestions()
            if reuse:
                think_prompt += f"\n{reuse}"

        # RAG 知识注入
        if self.knowledge_base:
            rag_query = self._build_rag_query()
            relevant_knowledge = self._get_rag_knowledge(rag_query)
            if relevant_knowledge:
                think_prompt += f"\n相关知识库内容:\n{relevant_knowledge}\n"

        # 步骤零上下文（仅初期注入）
        if self._step_zero_context and self._step_count <= 3:
            think_prompt += self._step_zero_context

        # ── 渗透模式: 漏洞验证调度 ──
        if self.mode == "pentest" and self._pending_verification:
            v = self._pending_verification
            think_prompt += (
                f"\n## 漏洞验证任务 (第 {v['attempts'] + 1}/2 次)\n"
                f"上一步发现疑似 **{v['type']}** 漏洞（目标: {v['target']}），"
                f"置信度为 'likely'。\n"
                f"请生成具体验证 payload 确认该漏洞是否真实存在，"
                f"执行后根据实际响应判定。不要只靠工具——需要拿到证据。\n"
            )

        # 调用 LLM (原生 tool_calls → 堆栈法 JSON → general_next 回退)
        use_cache = not getattr(self, '_bypass_semantic_cache', False)
        api_tools = self._build_api_tools(self.function_configs)
        # 语义缓存指纹 — 长 prompt (40+ 轮) 超过 embedding API 上限时不会触发
        cache_fingerprint = self._build_cache_fingerprint()
        try:
            response = self.solve_llm.text_completion(
                prompt=think_prompt, json_check=False, use_cache=use_cache,
                tools=api_tools if api_tools else None,
                cache_fingerprint=cache_fingerprint,
            )
        except Exception as e:
            self._llm_failure_count += 1
            logger.error("LLM 调用失败 (%d/%d): %s",
                         self._llm_failure_count, self._max_llm_failures, e)
            return None  # solve() 检查 failure_count 决定是否终止
        think_content = response.choices[0].message.content or ""
        content_preview = think_content[:200] if think_content else "(仅 tool_calls)"
        logger.info(f"思考内容: {content_preview}...")

        # 1. 优先检查原生 tool_calls
        msg = response.choices[0].message
        if hasattr(msg, "tool_calls") and msg.tool_calls:
            tool_calls = ToolUtils.parse_tool_calls(response)
            if tool_calls:
                valid_calls = []
                for tc in tool_calls:
                    tname = tc.get("tool_name", "")
                    if tname in self.tools or tname in self.tool._dynamic_tool_map:
                        valid_calls.append(tc)
                    else:
                        logger.warning("原生 tool_call '%s' 不在可用列表中，尝试动态发现", tname)
                        mentioned = {tname}
                        self.tool.inject_dynamic_tools(mentioned, think_content)
                        if tname in self.tool._dynamic_tool_map:
                            valid_calls.append(tc)
                if valid_calls:
                    self._llm_failure_count = 0
                    return think_content, valid_calls

        # 2. 文本提取（堆栈法 JSON → XML 回退）
        tool_calls = self._extract_tool_calls_from_content(think_content)
        if tool_calls:
            # 验证工具名有效性
            valid_calls = []
            for tc in tool_calls:
                tname = tc.get("tool_name", "")
                if tname in self.tools or tname in self.tool._dynamic_tool_map:
                    valid_calls.append(tc)
                else:
                    logger.warning("think 中的工具 '%s' 不在可用列表中，尝试动态发现", tname)
                    # 尝试动态注入
                    mentioned = {tname}
                    self.tool.inject_dynamic_tools(mentioned, think_content)
                    if tname in self.tool._dynamic_tool_map:
                        valid_calls.append(tc)
            if valid_calls:
                self._llm_failure_count = 0
                return think_content, valid_calls

        # 回退路径：think 中无有效工具调用 → 使用 general_next 再次生成
        logger.info("think 中未提取到有效工具调用，回退到 general_next")
        mentioned = extract_tool_mentions(think_content)
        tools = self.tool.recommend_tools(think_content, 3, force_tools=mentioned)
        try:
            tool_calls = self.tool_general(history_summary, think_content, tools)
        except Exception as e:
            self._llm_failure_count += 1
            logger.warning("tool_general 异常 (%d/%d): %s",
                           self._llm_failure_count, self._max_llm_failures, e)
            return None
        if not tool_calls:
            self._llm_failure_count += 1
            logger.warning(
                "未提取到有效工具调用 (%d/%d)",
                self._llm_failure_count, self._max_llm_failures,
            )
            return None
        self._llm_failure_count = 0
        return think_content, tool_calls

    def _get_rag_knowledge(self, query: str) -> str:
        """带缓存的 RAG 查询 — 相同 query 在 TTL (300s) 内复用。"""
        cache_key = hashlib.md5(query.encode()).hexdigest()[:16]
        now = time.time()
        if cache_key in self._rag_cache:
            ts, result = self._rag_cache[cache_key]
            if now - ts < self._rag_cache_ttl:
                logger.debug("RAG 缓存命中: %s", query[:60])
                return result
        result = self.knowledge_base.get_relevant_knowledge(query)
        self._rag_cache[cache_key] = (now, result)
        return result

    def _load_step_zero_context(self):
        """步骤零：解题前从知识库匹配同类经验，作为初始解题上下文。

        根据题目特征（CTF: 题型分类 | 渗透: 目标指纹）检索知识库，
        将历史解题记录作为初始上下文注入，帮助 Agent 更快定位方向。
        """
        if not self.knowledge_base or not self.problem:
            return
        try:
            if self.mode == "pentest":
                # 渗透模式: 检索目标指纹相关的渗透方法论
                query = f"渗透测试 {self.problem[:300]}"
            else:
                # CTF 模式: 使用题目分类
                from ctf_tool.challenge_classifier import classify as _classify
                import os as _os
                files = _os.listdir("attachments") if _os.path.isdir("attachments") else []
                classification = _classify(self.problem[:500], files, "")
                ctype = classification.get("primary_type", "")
                self._ctf_category = ctype  # 供 _auto_activate_mcp 使用
                query = f"CTF 解题 {ctype} {self.problem[:200]}"

            results = self.knowledge_base.search_knowledge(query, n_results=3)
            if results:
                lines = ["\n【历史同类解题参考】"]
                for i, r in enumerate(results, 1):
                    content = str(r.get('content', ''))[:2000]
                    lines.append(f"{i}. {content}")
                self._step_zero_context = "\n".join(lines) + "\n"
                logger.info("步骤零: 已加载同类经验 (%d 条)", len(results))
        except Exception as e:
            logger.debug("步骤零加载失败 (不影响解题): %s", e)

    def _auto_activate_mcp(self):
        """根据题目分类，从 config 中读取各 MCP 服务的 auto_activate_for 配置自动激活。"""
        ctype = getattr(self, '_ctf_category', '') or ''
        if not ctype:
            return
        ctype_lower = ctype.lower()
        for name, cfg in list(self.tool._lazy_mcp_servers.items()):
            auto_for = cfg.get("auto_activate_for", [])
            if any(t in ctype_lower for t in auto_for):
                ok = self.tool.load_mcp_lazy(name)
                if ok:
                    logger.info("题型自动激活 MCP: %s → %s", ctype, name)
                    self.function_configs = (
                        self.tool.local_function_configs
                        + self.tool.mcp_function_configs
                        + self.tool.get_dynamic_function_configs()
                    )

    def _build_rag_query(self) -> str:
        """构建 RAG 检索查询 — 拼接题目原文 + 最近步骤输出中的技术关键词。"""
        query = self.problem
        # 从最近历史步骤的原始输出中提取技术关键词（如 sha1, PHP, 参数名等）
        if self.memory.history:
            last_step = self.memory.history[-1]
            output_text = str(last_step.get("output", ""))
            # 截取输出前 200 字符（避开 HTML 标签，取文本内容）
            clean_output = " ".join(output_text[:300].split())[:200]
            if clean_output:
                query = self.problem + " " + clean_output
        return query[:800]

    def _execute_single_tool(self, tool_call: dict, think: str) -> tuple:
        """执行单个工具调用（带缓存，MCP 工具除外），返回 (tool_name, output_text)。"""
        tool_name = tool_call.get("tool_name")
        arguments: dict = tool_call.get("arguments", {})

        # MCP 工具（如 Burp HTTP 代理）不缓存 — 相同参数可能产生不同网络响应
        tool = self.tools.get(tool_name)
        is_mcp = isinstance(tool, MCPServerAdapter) if tool else False

        # 检查缓存（MCP 工具跳过）
        if not is_mcp:
            cached = self.tool_cache.get(tool_name, arguments)
            if cached is not None:
                logger.info("工具缓存命中: %s", tool_name)
                return tool_name, cached

        is_error = False
        if tool is not None:
            try:
                result = tool.execute(tool_name, arguments)
                if result:
                    output = parse_tool_output(tool_name, str(result))
                    _LLM_SUMMARY_THRESHOLD = self.config.get("llm_summary_threshold", 16384)
                    if len(output) > _LLM_SUMMARY_THRESHOLD:
                        output = self.tool.output_summary(
                            tool_name, tool_call, think, output
                        )
                else:
                    output = "注意！无输出内容！"
            except Exception as e:
                output = f"工具执行出错: {str(e)}"
                is_error = True
                # L-14 修复：工具抛异常时主动登记失败尝试，避免依赖 analysis.success 字段
                try:
                    self.memory.add_failed_attempt(tool_call.get("arguments", tool_call))
                except Exception:
                    pass
        else:
            dynamic_result = self.tool.execute_dynamic_tool(tool_name, arguments)
            if dynamic_result is not None:
                output = dynamic_result
            else:
                output = f"错误: 未找到工具 '{tool_name}'"
                is_error = True
                # L-14 修复：动态工具未找到也登记失败
                try:
                    self.memory.add_failed_attempt(tool_call.get("arguments", tool_call))
                except Exception:
                    pass

        # MCP 工具不缓存；错误输出不缓存（瞬态错误应允许重试）
        if not is_mcp and not is_error:
            self.tool_cache.set(tool_name, arguments, output)
        return tool_name, output

    def _summarize_output(self, output: str) -> Optional[str]:
        """使用 LLM 对长工具输出生成保留技术细节的摘要。

        短输出 (< output_summary_threshold) 直接返回 None，由 get_summary() 使用原文。
        长输出调用 LLM 摘要，保留: IP/端口/URL/路径/错误信息/凭据/flag/版本号。
        失败时返回 None，调用方降级为硬截断。
        """
        threshold = self.config.get("output_summary_threshold", 2048)
        if not output or len(output) <= threshold:
            return None
        max_chars = self.config.get("output_summary_max_chars", 800)
        prompt = (
            "Summarize the following tool execution output concisely. "
            "Preserve ALL security-relevant technical details:\n"
            "- IP addresses, ports, hostnames, URLs, API endpoints\n"
            "- File paths and key file contents (especially /etc/, /var/, /home/)\n"
            "- Error messages, stack traces, HTTP status codes\n"
            "- Credentials, tokens, hashes, keys, flags\n"
            "- Service banners, version numbers, technology stack info\n"
            "- Command output showing system state, user accounts, permissions\n"
            f"Keep the summary under {max_chars} characters. "
            "Write in the same language as the original output.\n\n"
            f"Output:\n{output}"
        )
        try:
            response = self.solve_llm.text_completion(
                prompt=prompt, json_check=False, use_cache=False,
            )
            summary = response.choices[0].message.content.strip()
            if len(summary) > max_chars * 2:
                summary = summary[:max_chars * 2]
            return summary
        except Exception as e:
            logger.warning("输出摘要生成失败: %s", e)
            return None

    def _write_journal_entry(self, step_count: int, think: str,
                             tool_name: str, tool_calls: list,
                             output: str, analysis: dict):
        """每步追加解题日志 — LLM 叙事，保留全部技术细节，永不截断。

        使用 flash 模型快速生成 150-350 字的叙事段落，
        写入 memory.journal_entries，供后续每一步 LLM 决策使用。
        """
        tool_args_str = str(tool_calls)[:400]
        analysis_text = analysis.get("analysis", "")[:300]
        output_preview = output[:2500]

        prompt = (
            f"你是一个解题日志记录器。请将以下第{step_count}步的执行过程和结果"
            "写成一个简洁的技术叙事段落（150-350字）。\n\n"
            "规则:\n"
            "1. 保留所有技术细节: IP/端口/版本/路径/返回码/错误信息/payload/文件内容/凭据\n"
            "2. 去掉JSON格式噪音，转为人话描述（如 '使用 nmap -sV 扫描端口' 而非展示原始JSON）\n"
            "3. 如果步骤无进展或仅确认已有信息，一句话带过\n"
            "4. 用中文输出\n\n"
            f"## 第{step_count}步\n\n"
            f"意图: {think[:300]}\n\n"
            f"工具: {tool_name}\n"
            f"参数: {tool_args_str}\n\n"
            f"输出:\n{output_preview}\n\n"
            f"分析结论: {analysis_text}"
        )

        try:
            # 用 flash 模型做叙事压缩，快速低成本
            from utils.llm_request import LLMRequest
            journal_llm = LLMRequest("pre_processor")
            response = journal_llm.text_completion(
                prompt=prompt, json_check=False, use_cache=False,
            )
            journal_text = response.choices[0].message.content.strip()
            self.memory.add_journal_entry(step_count, journal_text)
        except Exception as e:
            # 降级：用分析结论作为最简单的日志条目
            fallback = analysis.get("analysis", f"执行 {tool_name}")[:200]
            self.memory.add_journal_entry(step_count, fallback)
            logger.debug("解题日志 LLM 调用失败，使用降级: %s", e)

    def _detect_credentials(self, output: str, analysis: dict):
        """从工具输出和分析结果中检测凭据，自动存入攻击面管理器。

        覆盖: 密码/Token/API密钥/SSH私钥/数据库连接串/JWT/Hash。
        捕获后经 _is_valid_credential() 过滤纯数字/符号分隔线/HTTP 响应字段等误匹配。
        """
        import re
        patterns = [
            (r'(?:password|passwd|pass|pwd)\s*[:=]\s*(\S{3,60})', 'password'),
            (r'(?:token|api[_-]?key|apikey)\s*[:=]\s*(\S{8,80})', 'token'),
            (r'(?:secret|secret[_-]?key)\s*[:=]\s*(\S{6,80})', 'secret'),
            (r'-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----', 'private_key'),
            (r'(?:jwt|bearer)\s+([A-Za-z0-9\-_]+\.[A-Za-z0-9\-_]+\.[A-Za-z0-9\-_]+)', 'jwt'),
            (r'(?:mongodb|mysql|postgresql|postgres)://[^\s]+', 'db_connection'),
            (r'(?:hash|hash:)\s*([a-fA-F0-9]{32,})', 'hash'),
            (r'(?:admin|root|user):\s*([^\s]{3,40})', 'credential'),
        ]
        texts = [output[:3000]]
        vuln = analysis.get("vulnerability", {})
        if isinstance(vuln, dict) and vuln.get("evidence"):
            texts.append(str(vuln["evidence"]))

        for text in texts:
            for pat, ctype in patterns:
                for m in re.finditer(pat, text, re.IGNORECASE):
                    value = m.group(1) if m.lastindex else m.group(0)
                    value = value.strip()
                    if len(value) < 3 or not self._is_valid_credential(value):
                        continue
                    target = vuln.get("affected_component", "") if isinstance(vuln, dict) else ""
                    self.attack_surface.add_credential(
                        source="tool_output" if text == output[:3000] else "vuln_evidence",
                        cred_type=ctype, value=value, target=target,
                    )

    @staticmethod
    def _is_valid_credential(value: str) -> bool:
        """过滤凭据误匹配: 纯数字/符号分隔线/HTTP响应字段/大小标记。"""
        import re
        if value.isdigit() and (len(value) < 6 or value in ("22", "80", "443", "3306", "6379", "8080", "8443")):
            return False
        if re.match(r'^[=\-*#~_]{3,}$', value):
            return False
        if re.search(r'(?:Content-Type|X-Powered|Server:|Set-Cookie|diff=|响应|状态码|Response|charset)', value, re.I):
            return False
        if re.match(r'^\d+[BKMG]?$', value):
            return False
        return True

    def _quick_analysis(self, combined_output: str, pre_flag: Optional[str] = None) -> Optional[Dict]:
        """快速分析 — 无需 LLM 调用，直接构造分析结果。

        适用于三类场景:
          1. Flag 已被正则预检测命中
          2. 输出极短 (< 200 字符) 且非结构化
          3. 纯枚举输出（多行短内容，非 HTML/JSON/XML）
        返回 None 表示需要 LLM 分析。

        返回结果会自动包含模式对应字段（CTF: flag/terminate；渗透: vulnerability/should_continue）。
        """
        def _base(flag_found=False, analysis="", pre_flag_val=None):
            """构造模式感知的基础分析结果（v2: progress_level 替代 new_info/no_progress）。"""
            base = {
                "progress_level": "significant" if (flag_found or pre_flag_val) else "moderate",
                "analysis": analysis,
            }
            if self.mode == "pentest":
                base.update({
                    "vulnerability_found": False,
                    "vulnerability": None,
                    "attack_surface_covered": [],
                    "should_continue": True,
                    "terminate_all": False,
                })
            else:
                base.update({
                    "flag_found": flag_found or bool(pre_flag_val),
                    "flag": pre_flag_val or "",
                    "flag_confidence": "exact_match" if pre_flag_val else "",
                    "terminate": False,
                })
            return base

        # 1. Flag 已确认 → 直接返回
        if pre_flag:
            return _base(analysis=f"正则检测到 flag: {pre_flag}", pre_flag_val=pre_flag)

        # 2. HTML/JSON/XML 等结构化输出 → 必须走 LLM 分析，不能跳过
        stripped = combined_output.strip()
        if (stripped.startswith("<!") or stripped.startswith("<html")
                or stripped.startswith("<") and ("</" in stripped or "/>" in stripped)):
            return None  # HTML/XML 结构，LLM 需要分析
        if stripped.startswith("{") or stripped.startswith("["):
            return None  # JSON 结构，LLM 需要分析

        # 3. 极短输出 — 先做 flag 扫描，正则未命中但含 {…} 结构则交给 LLM 判断
        if len(combined_output) < 200:
            if self.mode == "ctf":
                short_flag = detect_flag(combined_output)
                if short_flag:
                    return _base(analysis=f"短输出中检测到 flag: {short_flag}", pre_flag_val=short_flag)
                # 正则未命中但含大括号对 → 可能是未知 flag 格式，LLM 识别兜底
                if "{" in stripped and "}" in stripped:
                    return None
            return _base(analysis=combined_output)

        # 4. 纯枚举输出（>20 行且总长度 <3000，不含 HTML 标签）
        if combined_output.count('\n') > 20 and len(combined_output) < 3000:
            line_count = combined_output.count('\n') + 1
            # 二次检测：枚举输出中可能包含 flag 行
            enum_flag = detect_flag(combined_output) if self.mode == "ctf" else None
            if enum_flag:
                return _base(analysis=f"枚举输出中检测到 flag: {enum_flag}", pre_flag_val=enum_flag)
            return _base(analysis=f"枚举结果 ({line_count} 项)")

        return None

    def tool_general(
        self, history_summary: str, think: str, tool_configs: List[Dict] = None
    ) -> List[Dict]:
        """生成工具调用（支持多工具）。返回工具调用列表。"""
        if tool_configs is None:
            tool_configs = self.function_configs
        template = self.env.from_string(self.prompt.get("general_next", ""))
        step_prompt = template.render(
            question=self.problem,
            scope=self.problem,
            solution_plan=think,
            history_summary=history_summary,
            tools_text=self._build_tools_text(tool_configs),
            attack_surface=self.attack_surface.get_summary() if self.mode == "pentest" and self.attack_surface else history_summary[:500],
            mode=self.mode,
            phase=self.current_phase,
        )
        response = self.solve_llm.text_completion(
            prompt=step_prompt,
            json_check=True,
        )
        return ToolUtils.parse_tool_calls(response) or []

    # ── 僵局检测与策略切换 ──────────────────────────────────────────

    @staticmethod
    def _normalize_think(think: str) -> str:
        """归一化 think 文本用于循环检测 — 去除 JSON/代码块/空白差异。"""
        import re
        t = think or ""
        # 移除 JSON 代码块
        t = re.sub(r'```json\s*\{.*?\}\s*```', '', t, flags=re.DOTALL)
        # 移除所有代码块
        t = re.sub(r'```.*?```', '', t, flags=re.DOTALL)
        # 移除 URL 中的变化参数
        t = re.sub(r'http://[\w.]+:\d+', 'URL', t)
        # 压缩空白
        t = re.sub(r'\s+', ' ', t).strip()
        return t[:200]

    @staticmethod
    def _extract_thought_intent(think: str) -> str:
        """从思考内容中提取意图指纹（仅提取关键操作/工具/URL/动作词，忽略连接词）。"""
        import re
        keywords = re.findall(
            r'(curl|http|https|jwt|token|flag|admin|login|decode|forge|爆破|扫描|枚举|访问|获取|伪造|解码|修改|绕过)',
            think.lower()
        )
        return " ".join(keywords)[:200] if keywords else think[:100]

    def _detect_stuck_step(self, step_count: int, think: str, tool_name: str,
                           output: str, analysis: dict) -> bool:
        """检测当前步骤是否表明解题陷入僵局。

        检测维度:
        1. LLM 标记无进展 (progress_level=none) — 需规则维度配合，防止同源误判
        2. 连续相同工具调用
        3. 输出内容语义相似度
        4. 思考内容意图循环 — 同一种思路≥3次出现
        5. 步骤数多但无进展
        6. 工具执行错误率 — ≥60% 最近步骤出错（纯规则，不依赖 LLM）
        """
        progress = analysis.get("progress_level", "")

        # 维度 2: 连续相同工具名出现多次
        self._recent_tools.append(tool_name or "none")
        if len(self._recent_tools) > 8:
            self._recent_tools.pop(0)

        _dim2_triggered = False
        if len(self._recent_tools) >= 4:
            from collections import Counter
            recent = self._recent_tools[-4:]
            most_common = Counter(recent).most_common(1)
            if most_common and most_common[0][1] >= 3:
                _dim2_triggered = True

        # 维度 3: 输出内容语义相似度 — 使用 SequenceMatcher 替代字节 hash
        sample = (output or "")[:300]
        self._recent_output_samples.append(sample)
        if len(self._recent_output_samples) > 5:
            self._recent_output_samples.pop(0)

        _dim3_triggered = False
        if len(self._recent_output_samples) >= 3:
            last3 = self._recent_output_samples[-3:]
            if last3[0] == last3[1] == last3[2] and last3[0]:
                _dim3_triggered = True
            from difflib import SequenceMatcher
            latest = self._recent_output_samples[-1]
            for prev in self._recent_output_samples[-4:-1]:
                if prev and latest and SequenceMatcher(None, prev, latest).ratio() > 0.85:
                    _dim3_triggered = True
                    break

        # 维度 4: 思考内容意图循环 — 相同意图重复 ≥3 次
        _dim4_triggered = False
        if len(self._recent_thoughts) >= 5:
            from collections import Counter
            thought_counts = Counter(self._recent_thoughts)
            if thought_counts.most_common(1)[0][1] >= 3:
                logger.warning("检测到 LLM 思维循环: '%s' 重复 %d 次",
                             thought_counts.most_common(1)[0][0][:80],
                             thought_counts.most_common(1)[0][1])
                _dim4_triggered = True

        # 维度 6: 工具执行错误率 ≥60%（纯规则，不依赖 LLM）
        _dim6_triggered = False
        if len(self._recent_tool_errors) >= 5:
            error_rate = sum(self._recent_tool_errors) / len(self._recent_tool_errors)
            if error_rate >= 0.6:
                _dim6_triggered = True
                logger.warning("工具错误率异常: %.0f%% (%d/%d)",
                             error_rate * 100, sum(self._recent_tool_errors),
                             len(self._recent_tool_errors))

        # 任何规则维度独立触发 → 直接判定僵局
        if _dim2_triggered or _dim3_triggered or _dim4_triggered or _dim6_triggered:
            return True

        # 维度 1: LLM 分析器标记无进展 — 需要规则维度配合（防止同源误判）
        # 前 5 步不依赖维度 1（探索期，单步失败正常）
        if progress == "none" and step_count >= 5:
            # 需要至少 1 个规则维度有微弱信号
            _any_rule_signal = (
                (len(self._recent_tools) >= 4 and
                 self._recent_tools[-4:].count(tool_name or "none") >= 2)
            )
            if _any_rule_signal:
                logger.info("维度1+规则信号确认僵局 (step=%d)", step_count)
                return True

        # 维度 5: 步骤数多但无进展 (step≥15)
        if step_count >= 15 and not self._has_progress(analysis):
            return True

        return False

    def _has_progress(self, analysis: dict) -> bool:
        """检查分析结果中是否有进展信号 (模式感知, v2 progress_level)。"""
        progress = analysis.get("progress_level", "")
        if progress in ("significant", "moderate"):
            return True
        if self.mode == "pentest":
            return any([
                analysis.get("vulnerability_found", False),
                bool(analysis.get("attack_surface_covered")),
            ])
        else:
            return any([
                analysis.get("flag_found", False),
                "flag{" in str(analysis.get("analysis", "")).lower(),
                "flag" in str(analysis.get("key_findings", "")).lower(),
            ])

    @staticmethod
    def _output_significantly_changed(current: str, previous: str = None,
                                      threshold: float = 0.3) -> bool:
        """检测工具输出是否与上一步显著不同（>30% 字符差异率）。

        用于连续无进展检测：即使分析器判定 progress_level=none，
        若输出实质变化（如攻击链中 payload 构造/监听器启动），
        说明 LLM 并非在原路循环，不应累加无进展计数。
        """
        if not previous or not current:
            return True  # 首步或无对比基准，保守视为有变化
        max_len = max(len(previous), len(current))
        if max_len == 0:
            return False
        # 字符级差异率（简单但有效，不依赖 LLM）
        diff = sum(1 for a, b in zip(previous, current) if a != b)
        diff += abs(len(previous) - len(current))
        return diff / max_len >= threshold

    def _build_step_snapshot(self, step_count: int, think: str,
                            tool_calls: list, combined_output: str,
                            analysis_result: dict, tools_used: list):
        """构建 StepSnapshot — 每步执行完毕后推送给 TUI。"""
        from tui.snapshot import StepSnapshot

        # 分析文本
        analysis_text = ""
        if isinstance(analysis_result, dict):
            analysis_text = analysis_result.get("analysis", "") or ""

        # Flag 信息 (CTF 模式)
        flag_found = False
        flag_value = ""
        if self.mode == "ctf" and isinstance(analysis_result, dict):
            flag_found = analysis_result.get("flag_found", False)
            flag_value = analysis_result.get("flag", "") or ""

        # 漏洞信息 (渗透模式)
        vulnerability = None
        if self.mode == "pentest" and isinstance(analysis_result, dict):
            if analysis_result.get("vulnerability_found"):
                vulnerability = analysis_result.get("vulnerability")

        # 攻击面摘要
        attack_surface_summary = ""
        if self.attack_surface:
            attack_surface_summary = self.attack_surface.get_summary()[:2048]

        # 缓存统计
        cache_stats = {
            "l1": len(getattr(self, '_recent_output_samples', [])),
            "l2": len(getattr(self, '_rag_cache', {})),
            "rag": len(getattr(self, '_rag_cache', {})),
        }

        # Token 用量统计
        token_stats = {}
        try:
            from utils.token_tracker import get_token_tracker
            token_stats = get_token_tracker().snapshot()
        except Exception:
            pass

        return StepSnapshot(
            step_num=step_count,
            phase=self.current_phase,
            think=(think or "")[:500],
            tool_calls=[
                {"tool_name": tc.get("tool_name", "?"),
                 "arguments": tc.get("arguments", {})}
                for tc in (tool_calls or [])
            ],
            output=(combined_output or "")[:8192],
            analysis=analysis_text[:1024],
            flag_found=flag_found,
            flag_value=flag_value,
            vulnerability=vulnerability,
            cache_stats=cache_stats,
            stuck_warning=self._stuck_counter > 0,
            attack_surface_summary=attack_surface_summary,
            token_stats=token_stats,
        )

    def _build_switch_prompt(self) -> str:
        """构建策略切换提示 (模式感知)。"""
        switch_level = min(self._strategy_switch_count, 3)

        if self.mode == "pentest":
            level_prompts = [
                "以上方法没有取得进展。请切换到完全不同的攻击面或测试类型继续探索。",
                "当前攻击面测试无果。请完全放弃当前方法，转向其他未测试的服务/端口/参数。",
                "当前攻击路径可能完全错误。请重新评估目标，考虑不同的漏洞类型或攻击向量（如从 Web 应用切换到 API/认证/基础设施层面）。",
            ]
        else:
            level_prompts = [
                "以上方法没有取得进展。请换一个完全不同的思路重新分析这道题。",
                "多次尝试仍未成功。请完全放弃当前方法，用截然不同的角度来看待这个问题。建议更换工具类别（如从 network 切换为 file analysis 或 crypto）。",
                "当前攻击面可能完全错误。请重新评估题目类型，考虑是否分类有误，尝试其他类别（如从 web 切换到 stego/forensics/crypto）的攻击方法。",
            ]

        instruction = level_prompts[switch_level] if switch_level < len(level_prompts) else level_prompts[-1]
        context = (
            f"你已经尝试了以下策略: {'; '.join(self._tried_strategies[-5:])}\n"
            if self._tried_strategies else ""
        )
        return f"{context}{instruction}"
