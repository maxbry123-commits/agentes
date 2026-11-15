"""
流程编排器
负责协调各Agent完成渗透测试流程
"""
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
import time
from datetime import datetime
import json
import os

from agents import (
    BaseAgent, AgentStatus, AgentResult, Task,
    ReconAgent, VulnAgent, ExploitAgent, ReportAgent, CoordinatorAgent
)
from llm import LLMFactory, BaseLLMClient
from tools import ToolManager
from .event_store import EventStore
from .interaction_bus import InteractionBus


class TestPhase(Enum):
    """测试阶段"""
    INIT = "init"
    RECON = "recon"
    VULN_ANALYSIS = "vuln_analysis"
    EXPLOITATION = "exploitation"
    POST_EXPLOIT = "post_exploit"
    REPORTING = "reporting"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class TestSession:
    """测试会话"""
    session_id: str
    target: str
    status: TestPhase = TestPhase.INIT
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    results: Dict = field(default_factory=dict)
    timeline: List[Dict] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    def add_event(self, phase: str, description: str, details: Dict = None):
        """添加时间线事件"""
        self.timeline.append({
            "timestamp": datetime.now().isoformat(),
            "phase": phase,
            "description": description,
            "details": details or {}
        })

    def to_dict(self) -> Dict:
        return {
            "session_id": self.session_id,
            "target": self.target,
            "status": self.status.value,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "results": self.results,
            "timeline": self.timeline,
            "errors": self.errors
        }


class Orchestrator:
    """
    流程编排器
    协调各Agent执行渗透测试流程
    """

    def __init__(self, config: Dict = None, model_config_manager=None):
        self.config = config or {}
        self.model_config_manager = model_config_manager
        self.llm_client = self._init_llm()
        self.tool_manager = ToolManager(self.config.get("tools", {}))
        self.event_store = EventStore()
        self.interaction_bus = InteractionBus(self.event_store)
        self.max_phase_rounds = self.config.get("agents", {}).get("coordinator", {}).get("max_rounds", 2)

        # 初始化Agents
        self.agents = self._init_agents()

        # 活动会话
        self.active_session: Optional[TestSession] = None
        self.sessions: Dict[str, TestSession] = {}

    @staticmethod
    def _phase_label(phase: str) -> str:
        labels = {
            "init": "初始化",
            "recon": "信息收集",
            "vuln": "漏洞分析",
            "exploit": "漏洞利用",
            "report": "报告生成",
        }
        return labels.get(phase, phase)

    def _emit_progress(
        self,
        progress_callback: Optional[Callable[[Dict[str, Any]], None]],
        payload: Dict[str, Any]
    ) -> None:
        if progress_callback:
            progress_callback(payload)

    @staticmethod
    def _build_round_result_payload(phase: str, current_result: AgentResult) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "success": current_result.success,
            "error": current_result.error,
            "data_preview": json.dumps(
                current_result.data,
                ensure_ascii=False,
                default=str
            )[:800] if current_result.data is not None else "",
        }

        if not isinstance(current_result.data, dict):
            return payload

        if phase == "exploit":
            results = current_result.data.get("results", {})
            attempts = results.get("attempts", []) if isinstance(results, dict) else []
            capture_attempt = next(
                (
                    item for item in attempts
                    if isinstance(item, dict) and item.get("type") == "web_flag_capture"
                ),
                {},
            )
            capture_details = capture_attempt.get("details", {}) if isinstance(capture_attempt, dict) else {}
            payload["result_data"] = {
                "target": current_result.data.get("target"),
                "flags": results.get("flags", []) if isinstance(results, dict) else [],
                "flag_payloads": capture_details.get("flag_payloads", []),
                "visited_urls": capture_details.get("visited_urls", []),
                "auth_method": capture_details.get("auth_method"),
                "credential": capture_details.get("credential"),
            }
            return payload

        if phase == "report":
            report_data = current_result.data.get("report")
            overview = report_data.get("executive_summary", {}).get("overview", "") if isinstance(report_data, dict) else ""
            payload["result_data"] = {
                "format": current_result.data.get("format"),
                "generated_at": current_result.data.get("generated_at"),
                "overview": overview,
            }
            return payload

        payload["result_data"] = current_result.data
        return payload

    def _should_short_circuit_phase(
        self,
        phase: str,
        result: Optional[AgentResult]
    ) -> Optional[str]:
        """基于阶段结果直接收敛，避免无意义的额外轮次"""
        if not result or not result.success:
            return None

        data = result.data or {}

        if phase == "recon":
            findings = data.get("results", {}) if isinstance(data, dict) else {}
            if findings.get("web") or findings.get("ports") or findings.get("services"):
                return "已获得足够的目标情报，信息收集阶段收敛"

        if phase == "vuln":
            vulns = data.get("vulnerabilities", []) if isinstance(data, dict) else []
            if vulns:
                return f"已识别 {len(vulns)} 个漏洞，漏洞分析阶段收敛"

        if phase == "exploit":
            exploit_results = data.get("results", {}) if isinstance(data, dict) else {}
            flags = exploit_results.get("flags", [])
            if flags:
                return f"已提取 Flag: {', '.join(flags)}"

        return None

    def _init_llm(self) -> BaseLLMClient:
        """初始化LLM客户端（全局默认客户端）"""
        llm_config = self.config.get("llm", {})
        provider = llm_config.get("provider", "deepseek")

        api_key = None
        api_keys = llm_config.get("api_keys", {})
        if provider in api_keys:
            key = api_keys[provider]
            # 处理环境变量
            if key.startswith("${") and key.endswith("}"):
                import os
                env_var = key[2:-1]
                api_key = os.getenv(env_var)
            else:
                api_key = key

        model = llm_config.get("models", {}).get(provider)

        return LLMFactory.create(
            provider=provider,
            api_key=api_key,
            model=model,
            timeout=llm_config.get("request", {}).get("timeout", 120)
        )

    def _get_agent_llm_client(self, agent_name: str) -> BaseLLMClient:
        """获取指定Agent的LLM客户端"""
        # 如果有模型配置管理器，尝试为该Agent创建独立客户端
        if self.model_config_manager:
            client = self.model_config_manager.create_llm_client(agent_name)
            if client:
                return client
        
        # 回退到全局客户端
        return self.llm_client

    def _init_agents(self) -> Dict[str, BaseAgent]:
        """初始化所有Agent"""
        agents = {
            "coordinator": CoordinatorAgent(
                self._get_agent_llm_client("coordinator"),
                config=self.config.get("agents", {}).get("coordinator", {}),
                event_bus=self.interaction_bus
            ),
            "recon": ReconAgent(
                self._get_agent_llm_client("recon"),
                scanner=self.tool_manager,
                config=self.config.get("agents", {}).get("recon", {}),
                event_bus=self.interaction_bus
            ),
            "vuln": VulnAgent(
                self._get_agent_llm_client("vuln"),
                scanner=self.tool_manager,
                config=self.config.get("agents", {}).get("vuln", {}),
                event_bus=self.interaction_bus
            ),
            "exploit": ExploitAgent(
                self._get_agent_llm_client("exploit"),
                tool_manager=self.tool_manager,
                config=self.config.get("agents", {}).get("exploit", {}),
                event_bus=self.interaction_bus
            ),
            "report": ReportAgent(
                self._get_agent_llm_client("report"),
                config=self.config.get("agents", {}).get("report", {}),
                event_bus=self.interaction_bus
            )
        }
        agents["coordinator"].team_agents = {
            name: agent for name, agent in agents.items() if name != "coordinator"
        }
        return agents

    def create_session(self, target: str) -> TestSession:
        """创建测试会话"""
        session_id = f"session_{int(time.time())}"
        session = TestSession(
            session_id=session_id,
            target=target
        )
        session.add_event("init", f"创建测试会话: {target}")
        self.sessions[session_id] = session
        self.active_session = session
        return session

    def run_test(
        self,
        target: str,
        mode: str = "auto",
        phases: List[str] = None,
        progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None
    ) -> Dict:
        """
        运行完整渗透测试

        Args:
            target: 目标IP/域名/URL
            mode: 运行模式 (auto, semi, manual)
            phases: 指定执行的阶段

        Returns:
            测试结果
        """
        # 默认执行所有阶段
        if phases is None:
            phases = ["recon", "vuln", "exploit", "report"]

        total_phases = max(len(phases), 1)

        # 创建会话
        session = self.create_session(target)
        self.interaction_bus.bind_session(
            session.session_id,
            target,
            {"mode": mode, "phases": phases}
        )
        self.interaction_bus.emit_event(
            session.session_id,
            event_type="session_started",
            summary=f"开始测试会话: {target}",
            agent="Orchestrator",
            details={"mode": mode, "phases": phases}
        )
        self._emit_progress(progress_callback, {
            "session_id": session.session_id,
            "status": "running",
            "progress": 2,
            "current_phase": "init",
            "current_phase_label": self._phase_label("init"),
            "status_detail": f"已创建测试会话，目标: {target}",
            "phase_index": 0,
            "phase_total": total_phases,
        })

        try:
            # 阶段1: 信息收集
            if "recon" in phases:
                phase_index = phases.index("recon")
                session.status = TestPhase.RECON
                session.add_event("recon", "开始信息收集")
                self._emit_progress(progress_callback, {
                    "session_id": session.session_id,
                    "status": "running",
                    "progress": int(5 + (phase_index / total_phases) * 90),
                    "current_phase": "recon",
                    "current_phase_label": self._phase_label("recon"),
                    "status_detail": "开始信息收集阶段",
                    "phase_index": phase_index + 1,
                    "phase_total": total_phases,
                })
                recon_result = self._run_recon(
                    target,
                    progress_callback=progress_callback,
                    phase_index=phase_index,
                    phase_total=total_phases
                )
                session.results["recon"] = recon_result.to_dict()
                self._emit_progress(progress_callback, {
                    "session_id": session.session_id,
                    "status": "running",
                    "progress": int(5 + ((phase_index + 1) / total_phases) * 90),
                    "current_phase": "recon",
                    "current_phase_label": self._phase_label("recon"),
                    "status_detail": "信息收集阶段完成",
                    "phase_index": phase_index + 1,
                    "phase_total": total_phases,
                })

                if not recon_result.success:
                    session.errors.append(f"信息收集失败: {recon_result.error}")

            # 阶段2: 漏洞分析
            if "vuln" in phases:
                phase_index = phases.index("vuln")
                session.status = TestPhase.VULN_ANALYSIS
                session.add_event("vuln", "开始漏洞分析")
                self._emit_progress(progress_callback, {
                    "session_id": session.session_id,
                    "status": "running",
                    "progress": int(5 + (phase_index / total_phases) * 90),
                    "current_phase": "vuln",
                    "current_phase_label": self._phase_label("vuln"),
                    "status_detail": "开始漏洞分析阶段",
                    "phase_index": phase_index + 1,
                    "phase_total": total_phases,
                })
                vuln_result = self._run_vuln_analysis(
                    target,
                    session.results.get("recon", {}),
                    progress_callback=progress_callback,
                    phase_index=phase_index,
                    phase_total=total_phases
                )
                session.results["vuln"] = vuln_result.to_dict()
                self._emit_progress(progress_callback, {
                    "session_id": session.session_id,
                    "status": "running",
                    "progress": int(5 + ((phase_index + 1) / total_phases) * 90),
                    "current_phase": "vuln",
                    "current_phase_label": self._phase_label("vuln"),
                    "status_detail": "漏洞分析阶段完成",
                    "phase_index": phase_index + 1,
                    "phase_total": total_phases,
                })

                if not vuln_result.success:
                    session.errors.append(f"漏洞分析失败: {vuln_result.error}")

            # 阶段3: 漏洞利用
            if "exploit" in phases:
                phase_index = phases.index("exploit")
                session.status = TestPhase.EXPLOITATION
                session.add_event("exploit", "开始漏洞利用")
                self._emit_progress(progress_callback, {
                    "session_id": session.session_id,
                    "status": "running",
                    "progress": int(5 + (phase_index / total_phases) * 90),
                    "current_phase": "exploit",
                    "current_phase_label": self._phase_label("exploit"),
                    "status_detail": "开始漏洞利用阶段",
                    "phase_index": phase_index + 1,
                    "phase_total": total_phases,
                })
                exploit_result = self._run_exploitation(
                    target,
                    session.results.get("recon", {}),
                    session.results.get("vuln", {}),
                    progress_callback=progress_callback,
                    phase_index=phase_index,
                    phase_total=total_phases
                )
                session.results["exploit"] = exploit_result.to_dict()
                self._emit_progress(progress_callback, {
                    "session_id": session.session_id,
                    "status": "running",
                    "progress": int(5 + ((phase_index + 1) / total_phases) * 90),
                    "current_phase": "exploit",
                    "current_phase_label": self._phase_label("exploit"),
                    "status_detail": "漏洞利用阶段完成",
                    "phase_index": phase_index + 1,
                    "phase_total": total_phases,
                })

                if not exploit_result.success:
                    session.errors.append(f"漏洞利用失败: {exploit_result.error}")

            # 阶段4: 报告生成
            if "report" in phases:
                phase_index = phases.index("report")
                session.status = TestPhase.REPORTING
                session.add_event("report", "生成测试报告")
                self._emit_progress(progress_callback, {
                    "session_id": session.session_id,
                    "status": "running",
                    "progress": int(5 + (phase_index / total_phases) * 90),
                    "current_phase": "report",
                    "current_phase_label": self._phase_label("report"),
                    "status_detail": "开始生成测试报告",
                    "phase_index": phase_index + 1,
                    "phase_total": total_phases,
                })
                report_result = self._run_report(
                    target,
                    session.results,
                    progress_callback=progress_callback,
                    phase_index=phase_index,
                    phase_total=total_phases
                )
                session.results["report"] = report_result.to_dict()
                self._emit_progress(progress_callback, {
                    "session_id": session.session_id,
                    "status": "running",
                    "progress": 95,
                    "current_phase": "report",
                    "current_phase_label": self._phase_label("report"),
                    "status_detail": "测试报告生成完成",
                    "phase_index": phase_index + 1,
                    "phase_total": total_phases,
                })

            session.status = TestPhase.COMPLETED
            session.add_event("completed", "测试完成")
            self.interaction_bus.emit_event(
                session.session_id,
                event_type="session_completed",
                summary="测试会话完成",
                agent="Orchestrator",
                details={"status": session.status.value}
            )
            self._emit_progress(progress_callback, {
                "session_id": session.session_id,
                "status": "completed",
                "progress": 100,
                "current_phase": "completed",
                "current_phase_label": "测试完成",
                "status_detail": "所有阶段执行完成",
                "phase_index": total_phases,
                "phase_total": total_phases,
            })

        except Exception as e:
            session.status = TestPhase.FAILED
            session.errors.append(str(e))
            session.add_event("failed", f"测试失败: {str(e)}")
            self.interaction_bus.emit_event(
                session.session_id,
                event_type="session_failed",
                summary=f"测试会话失败: {str(e)}",
                agent="Orchestrator",
                details={"error": str(e)}
            )
            self._emit_progress(progress_callback, {
                "session_id": session.session_id,
                "status": "failed",
                "progress": active_progress if 'active_progress' in locals() else 0,
                "current_phase": session.status.value,
                "current_phase_label": "测试失败",
                "status_detail": str(e),
                "phase_index": 0,
                "phase_total": total_phases,
                "error": str(e),
            })

        finally:
            session.end_time = datetime.now()

        # 保存结果
        self._save_session(session)

        return session.to_dict()

    def _run_recon(
        self,
        target: str,
        progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
        phase_index: int = 0,
        phase_total: int = 1
    ) -> AgentResult:
        """运行信息收集"""
        return self._run_phase_with_coordination(
            phase="recon",
            target=target,
            input_data={
                "target_type": "auto",
                "scan_depth": "normal"
            },
            progress_callback=progress_callback,
            phase_index=phase_index,
            phase_total=phase_total
        )

    def _run_vuln_analysis(
        self,
        target: str,
        recon_data: Dict,
        progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
        phase_index: int = 0,
        phase_total: int = 1
    ) -> AgentResult:
        """运行漏洞分析"""
        return self._run_phase_with_coordination(
            phase="vuln",
            target=target,
            input_data={
                "recon_data": recon_data.get("data", {})
            },
            progress_callback=progress_callback,
            phase_index=phase_index,
            phase_total=phase_total
        )

    def _run_exploitation(
        self,
        target: str,
        recon_data: Dict,
        vuln_data: Dict,
        progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
        phase_index: int = 0,
        phase_total: int = 1
    ) -> AgentResult:
        """运行漏洞利用"""
        return self._run_phase_with_coordination(
            phase="exploit",
            target=target,
            input_data={
                "recon_data": recon_data.get("data", {}),
                "vuln_data": vuln_data.get("data", {})
            },
            progress_callback=progress_callback,
            phase_index=phase_index,
            phase_total=phase_total
        )

    def _run_report(
        self,
        target: str,
        test_results: Dict,
        progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
        phase_index: int = 0,
        phase_total: int = 1
    ) -> AgentResult:
        """生成报告"""
        return self._run_phase_with_coordination(
            phase="report",
            target=target,
            input_data={
                "test_results": test_results,
                "format": "json"
            },
            progress_callback=progress_callback,
            phase_index=phase_index,
            phase_total=phase_total
        )

    def _run_phase_with_coordination(
        self,
        phase: str,
        target: str,
        input_data: Dict = None,
        progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
        phase_index: int = 0,
        phase_total: int = 1
    ) -> AgentResult:
        """带多轮协作观测的阶段执行"""
        agent = self.agents[phase]
        coordinator = self.agents.get("coordinator")
        session_id = self.active_session.session_id if self.active_session else None
        phase_input = {"target": target, **(input_data or {})}

        if not coordinator or not session_id:
            task = agent.create_task(
                name=phase,
                description=f"{phase}: {target}",
                input_data=phase_input
            )
            return agent.run_task(task)

        phase_context = dict(phase_input)
        current_result: Optional[AgentResult] = None
        current_round_id: Optional[str] = None
        phase_label = self._phase_label(phase)
        phase_base_progress = 5 + (phase_index / max(phase_total, 1)) * 90
        phase_span = 90 / max(phase_total, 1)

        for round_index in range(self.max_phase_rounds):
            round_number = round_index + 1
            round_ratio = round_index / max(self.max_phase_rounds, 1)
            self._emit_progress(progress_callback, {
                "status": "running",
                "progress": int(phase_base_progress + phase_span * (round_ratio + 0.1)),
                "current_phase": phase,
                "current_phase_label": phase_label,
                "status_detail": f"{phase_label} 第 {round_number} 轮协作规划中",
                "phase_index": phase_index + 1,
                "phase_total": phase_total,
                "round_index": round_number,
                "round_total": self.max_phase_rounds,
            })
            plan = coordinator.plan_phase_round(target, phase, phase_context)
            goal = plan.get("goal", f"{phase} 阶段协作")
            assignments = plan.get("assignments", [])
            participants = []
            for assignment in assignments:
                agent_name = assignment.get("agent")
                if agent_name and agent_name in self.agents and agent_name not in participants:
                    participants.append(self.agents[agent_name].name)
            if not participants:
                participants = [agent.name, coordinator.name]

            round_info = self.interaction_bus.start_round(
                session_id=session_id,
                phase=phase,
                goal=goal,
                participants=participants,
                metadata={
                    "round_index": round_index + 1,
                    "focus_points": plan.get("focus_points", [])
                }
            )
            current_round_id = round_info["round_id"]

            self.interaction_bus.send_message(
                session_id=session_id,
                round_id=current_round_id,
                sender=coordinator.name,
                receiver=agent.name,
                message_type="instruction",
                content=goal,
                payload={
                    "assignments": assignments,
                    "phase": phase,
                    "round_index": round_index + 1
                }
            )
            self._emit_progress(progress_callback, {
                "status": "running",
                "progress": int(phase_base_progress + phase_span * (round_ratio + 0.3)),
                "current_phase": phase,
                "current_phase_label": phase_label,
                "status_detail": f"{phase_label} 第 {round_number} 轮指令已下发",
                "phase_index": phase_index + 1,
                "phase_total": phase_total,
                "round_index": round_number,
                "round_total": self.max_phase_rounds,
                "current_round_id": current_round_id,
            })

            selected_assignment = next(
                (item for item in assignments if item.get("agent") == phase),
                None
            )
            task_instruction = (
                selected_assignment.get("instruction")
                if selected_assignment else f"执行 {phase} 阶段任务"
            )
            task = agent.create_task(
                name=f"{phase}_round_{round_index + 1}",
                description=task_instruction,
                input_data={
                    **phase_input,
                    "session_id": session_id,
                    "round_id": current_round_id,
                    "phase_context": phase_context,
                    "coordinator_goal": goal,
                    "round_index": round_index + 1
                }
            )
            self._emit_progress(progress_callback, {
                "status": "running",
                "progress": int(phase_base_progress + phase_span * (round_ratio + 0.5)),
                "current_phase": phase,
                "current_phase_label": phase_label,
                "status_detail": f"{phase_label} 第 {round_number} 轮执行中",
                "phase_index": phase_index + 1,
                "phase_total": phase_total,
                "round_index": round_number,
                "round_total": self.max_phase_rounds,
                "current_round_id": current_round_id,
            })
            current_result = agent.run_task(task)

            self.interaction_bus.send_message(
                session_id=session_id,
                round_id=current_round_id,
                sender=agent.name,
                receiver=coordinator.name,
                message_type="result",
                content=f"{phase} 阶段第 {round_index + 1} 轮已返回结果",
                payload=self._build_round_result_payload(phase, current_result)
            )
            self._emit_progress(progress_callback, {
                "status": "running",
                "progress": int(phase_base_progress + phase_span * (round_ratio + 0.7)),
                "current_phase": phase,
                "current_phase_label": phase_label,
                "status_detail": f"{phase_label} 第 {round_number} 轮结果已返回",
                "phase_index": phase_index + 1,
                "phase_total": phase_total,
                "round_index": round_number,
                "round_total": self.max_phase_rounds,
                "current_round_id": current_round_id,
                "last_round_success": current_result.success,
            })

            short_circuit_message = self._should_short_circuit_phase(phase, current_result)
            if short_circuit_message:
                self.interaction_bus.complete_round(
                    session_id=session_id,
                    round_id=current_round_id,
                    summary=short_circuit_message
                )
                self.interaction_bus.emit_event(
                    session_id=session_id,
                    round_id=current_round_id,
                    event_type="decision_finalized",
                    summary=short_circuit_message,
                    agent=coordinator.name,
                    details={
                        "phase": phase,
                        "rounds_used": round_number,
                        "short_circuit": True
                    }
                )
                self._emit_progress(progress_callback, {
                    "status": "running",
                    "progress": int(phase_base_progress + phase_span),
                    "current_phase": phase,
                    "current_phase_label": phase_label,
                    "status_detail": short_circuit_message,
                    "phase_index": phase_index + 1,
                    "phase_total": phase_total,
                    "round_index": round_number,
                    "round_total": self.max_phase_rounds,
                    "current_round_id": current_round_id,
                })
                break

            review = coordinator.review_phase_round(
                target=target,
                phase=phase,
                context=phase_context,
                phase_result=current_result.to_dict()
            )
            round_summary = review.get("summary", f"{phase} 阶段第 {round_index + 1} 轮完成")
            self.interaction_bus.complete_round(
                session_id=session_id,
                round_id=current_round_id,
                summary=round_summary
            )
            self._emit_progress(progress_callback, {
                "status": "running",
                "progress": int(phase_base_progress + phase_span * (round_ratio + 0.85)),
                "current_phase": phase,
                "current_phase_label": phase_label,
                "status_detail": round_summary,
                "phase_index": phase_index + 1,
                "phase_total": phase_total,
                "round_index": round_number,
                "round_total": self.max_phase_rounds,
                "current_round_id": current_round_id,
            })

            phase_context["last_round_review"] = review
            phase_context["last_round_result"] = current_result.to_dict()

            if not review.get("should_continue") or round_index + 1 >= self.max_phase_rounds:
                completion_message = review.get("completion_message") or round_summary
                self.interaction_bus.emit_event(
                    session_id=session_id,
                    round_id=current_round_id,
                    event_type="decision_finalized",
                    summary=completion_message,
                    agent=coordinator.name,
                    details={
                        "phase": phase,
                        "rounds_used": round_index + 1
                    }
                )
                self._emit_progress(progress_callback, {
                    "status": "running",
                    "progress": int(phase_base_progress + phase_span),
                    "current_phase": phase,
                    "current_phase_label": phase_label,
                    "status_detail": completion_message,
                    "phase_index": phase_index + 1,
                    "phase_total": phase_total,
                    "round_index": round_number,
                    "round_total": self.max_phase_rounds,
                    "current_round_id": current_round_id,
                })
                break

            follow_up_question = review.get("follow_up_question", "").strip()
            next_recipient = review.get("next_recipient", agent.name)
            if follow_up_question:
                self.interaction_bus.send_message(
                    session_id=session_id,
                    round_id=current_round_id,
                    sender=coordinator.name,
                    receiver=next_recipient if next_recipient in [a.name for a in self.agents.values()] else agent.name,
                    message_type="follow_up",
                    content=follow_up_question,
                    payload={"phase": phase}
                )

        return current_result or AgentResult(success=False, error=f"{phase} 阶段未生成结果")

    def _save_session(self, session: TestSession):
        """保存会话结果"""
        results_dir = self.config.get("system", {}).get("results_dir", "./results")
        os.makedirs(results_dir, exist_ok=True)

        filename = f"{session.session_id}.json"
        filepath = os.path.join(results_dir, filename)

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(session.to_dict(), f, ensure_ascii=False, indent=2)

    def run_phase(
        self,
        phase: str,
        target: str,
        input_data: Dict = None
    ) -> AgentResult:
        """
        运行单个测试阶段

        Args:
            phase: 阶段名称 (recon, vuln, exploit, report)
            target: 目标
            input_data: 输入数据

        Returns:
            AgentResult
        """
        if phase not in self.agents:
            return AgentResult(
                success=False,
                error=f"未知的测试阶段: {phase}"
            )

        agent = self.agents[phase]
        task = agent.create_task(
            name=phase,
            description=f"{phase}: {target}",
            input_data={"target": target, **(input_data or {})}
        )

        return agent.run_task(task)

    def get_agent_status(self) -> Dict[str, str]:
        """获取所有Agent状态"""
        return {
            name: agent.status.value
            for name, agent in self.agents.items()
        }

    def get_session_events(self, session_id: str, limit: Optional[int] = None) -> List[Dict]:
        """获取指定会话的交互事件"""
        return self.event_store.get_session_events(session_id, limit=limit)

    def get_recent_agent_events(self, limit: int = 50) -> List[Dict]:
        """获取最近的交互事件"""
        return self.event_store.get_recent_events(limit=limit)

    def get_session_rounds(self, session_id: str) -> List[Dict]:
        """获取会话轮次"""
        return self.event_store.get_rounds(session_id)

    def get_round_messages(self, session_id: str, round_id: str) -> List[Dict]:
        """获取轮次消息"""
        return self.event_store.get_round_messages(session_id, round_id)

    def get_latest_event(self, session_id: Optional[str] = None) -> Optional[Dict]:
        """获取最近一条事件"""
        return self.event_store.get_latest_event(session_id=session_id)

    def pause_session(self):
        """暂停当前会话"""
        if self.active_session:
            self.active_session.add_event("pause", "会话已暂停")

    def resume_session(self):
        """恢复当前会话"""
        if self.active_session:
            self.active_session.add_event("resume", "会话已恢复")

    def get_session(self, session_id: str) -> Optional[TestSession]:
        """获取指定会话"""
        return self.sessions.get(session_id)

    def list_sessions(self) -> List[Dict]:
        """列出所有会话"""
        return [
            {
                "session_id": s.session_id,
                "target": s.target,
                "status": s.status.value,
                "start_time": s.start_time.isoformat()
            }
            for s in self.sessions.values()
        ]
