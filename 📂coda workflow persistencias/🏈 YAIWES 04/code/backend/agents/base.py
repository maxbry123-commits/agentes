"""
Agent基类
提供所有Agent的通用功能和方法
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import json
import time
from datetime import datetime

from llm import BaseLLMClient, Message, LLMFactory


class AgentStatus(Enum):
    """Agent执行状态"""
    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    WAITING = "waiting"


class TaskPriority(Enum):
    """任务优先级"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class Task:
    """任务数据结构"""
    id: str
    name: str
    description: str
    status: AgentStatus = AgentStatus.IDLE
    priority: TaskPriority = TaskPriority.NORMAL
    input_data: Dict = field(default_factory=dict)
    output_data: Dict = field(default_factory=dict)
    error: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    dependencies: List[str] = field(default_factory=list)


@dataclass
class AgentResult:
    """Agent执行结果"""
    success: bool
    data: Any = None
    error: Optional[str] = None
    logs: List[str] = field(default_factory=list)
    metadata: Dict = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return {
            "success": self.success,
            "data": self.data,
            "error": self.error,
            "logs": self.logs,
            "metadata": self.metadata
        }


class BaseAgent(ABC):
    """
    自动化Agent基类
    所有具体Agent继承此类
    """

    # Agent类型标识
    AGENT_TYPE = "base"

    # 系统提示词模板
    SYSTEM_PROMPT = """你是一个专业的安全测试助手，专注于渗透测试和漏洞挖掘。
你的职责是帮助用户进行安全评估，提供专业的建议和分析。
请确保所有操作都在合法授权的范围内进行。"""

    def __init__(
        self,
        llm_client: BaseLLMClient,
        name: str = None,
        config: Dict = None,
        event_bus = None,
    ):
        self.llm_client = llm_client
        self.name = name or self.__class__.__name__
        self.config = config or {}
        self.event_bus = event_bus
        self.status = AgentStatus.IDLE
        self.current_task: Optional[Task] = None
        self.conversation_history: List[Message] = []
        self.execution_logs: List[str] = []
        self.current_session_id: Optional[str] = None
        self.current_round_id: Optional[str] = None

    def set_event_context(
        self,
        session_id: Optional[str] = None,
        round_id: Optional[str] = None
    ):
        """设置事件上下文"""
        if session_id:
            self.current_session_id = session_id
        self.current_round_id = round_id

    def emit_event(
        self,
        event_type: str,
        summary: str,
        details: Dict = None,
        round_id: Optional[str] = None,
        session_id: Optional[str] = None
    ):
        """发送结构化事件"""
        if not self.event_bus:
            return None

        resolved_session_id = session_id or self.current_session_id
        resolved_round_id = round_id if round_id is not None else self.current_round_id
        if not resolved_session_id:
            return None

        return self.event_bus.emit_event(
            session_id=resolved_session_id,
            round_id=resolved_round_id,
            event_type=event_type,
            summary=summary,
            agent=self.name,
            details=details or {}
        )

    def send_message(
        self,
        receiver: str,
        message_type: str,
        content: str,
        payload: Dict = None,
        round_id: Optional[str] = None,
        session_id: Optional[str] = None
    ):
        """向其他Agent发送消息"""
        if not self.event_bus:
            return None

        resolved_session_id = session_id or self.current_session_id
        resolved_round_id = round_id if round_id is not None else self.current_round_id
        if not resolved_session_id or not resolved_round_id:
            return None

        return self.event_bus.send_message(
            session_id=resolved_session_id,
            round_id=resolved_round_id,
            sender=self.name,
            receiver=receiver,
            message_type=message_type,
            content=content,
            payload=payload or {}
        )

    def add_log(self, message: str, level: str = "INFO"):
        """添加执行日志"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{level}] {message}"
        self.execution_logs.append(log_entry)
        print(log_entry)
        self.emit_event(
            event_type="log",
            summary=message,
            details={"level": level}
        )

    @abstractmethod
    def execute(self, task: Task) -> AgentResult:
        """
        执行Agent任务
        子类必须实现此方法
        """
        pass

    def analyze_with_llm(
        self,
        prompt: str,
        system_prompt: str = None,
        require_json: bool = False,
        json_schema: Dict = None
    ) -> Any:
        """
        使用LLM进行分析

        Args:
            prompt: 用户提示
            system_prompt: 系统提示
            require_json: 是否要求返回JSON
            json_schema: JSON schema定义

        Returns:
            LLM响应内容
        """
        messages = [Message("user", prompt)]
        prompt_preview = prompt[:500]
        self.emit_event(
            event_type="thinking_started",
            summary="开始进行LLM分析",
            details={
                "require_json": require_json,
                "prompt_preview": prompt_preview,
            }
        )

        try:
            if require_json and json_schema:
                result = self.llm_client.chat_with_json(messages, json_schema)
                self.emit_event(
                    event_type="thinking_completed",
                    summary="LLM结构化分析完成",
                    details={
                        "result_preview": json.dumps(result, ensure_ascii=False)[:500]
                    }
                )
                return result

            response = self.llm_client.chat(
                messages,
                system_prompt=system_prompt or self.SYSTEM_PROMPT
            )
            self.emit_event(
                event_type="thinking_completed",
                summary="LLM分析完成",
                details={"result_preview": response.content[:500]}
            )
            return response.content
        except Exception as e:
            self.emit_event(
                event_type="thinking_failed",
                summary=f"LLM分析失败: {str(e)}",
                details={"prompt_preview": prompt_preview}
            )
            raise

    def create_task(
        self,
        name: str,
        description: str,
        input_data: Dict = None,
        priority: TaskPriority = TaskPriority.NORMAL,
        dependencies: List[str] = None
    ) -> Task:
        """创建新任务"""
        task_id = f"{self.AGENT_TYPE}_{name}_{int(time.time())}"
        return Task(
            id=task_id,
            name=name,
            description=description,
            input_data=input_data or {},
            priority=priority,
            dependencies=dependencies or []
        )

    def run_task(self, task: Task) -> AgentResult:
        """运行任务"""
        self.set_event_context(
            session_id=task.input_data.get("session_id"),
            round_id=task.input_data.get("round_id")
        )
        self.status = AgentStatus.RUNNING
        self.current_task = task
        task.status = AgentStatus.RUNNING
        task.started_at = datetime.now()

        self.add_log(f"开始执行任务: {task.name}")
        self.emit_event(
            event_type="task_started",
            summary=f"开始执行任务: {task.name}",
            details={
                "task_id": task.id,
                "description": task.description,
                "priority": task.priority.name.lower(),
            }
        )

        try:
            result = self.execute(task)
            if result.success:
                self.status = AgentStatus.COMPLETED
                task.status = AgentStatus.COMPLETED
                task.output_data = result.data
                self.emit_event(
                    event_type="task_completed",
                    summary=f"任务执行完成: {task.name}",
                    details={
                        "task_id": task.id,
                        "data_preview": json.dumps(result.data, ensure_ascii=False, default=str)[:500]
                        if result.data is not None else ""
                    }
                )
            else:
                self.status = AgentStatus.FAILED
                task.status = AgentStatus.FAILED
                task.error = result.error
                self.emit_event(
                    event_type="task_failed",
                    summary=f"任务执行失败: {task.name}",
                    details={"task_id": task.id, "error": result.error}
                )
            task.completed_at = datetime.now()
            return result

        except Exception as e:
            self.status = AgentStatus.FAILED
            task.status = AgentStatus.FAILED
            task.error = str(e)
            task.completed_at = datetime.now()
            self.add_log(f"任务执行失败: {str(e)}", "ERROR")
            self.emit_event(
                event_type="task_failed",
                summary=f"任务执行异常: {task.name}",
                details={"task_id": task.id, "error": str(e)}
            )
            return AgentResult(success=False, error=str(e))

    def reset(self):
        """重置Agent状态"""
        self.status = AgentStatus.IDLE
        self.current_task = None
        self.conversation_history = []
        # 保留执行日志

    def get_capabilities(self) -> List[str]:
        """获取Agent能力列表"""
        return []


class SequentialAgent(BaseAgent):
    """顺序执行多个子任务的Agent"""

    def __init__(self, llm_client: BaseLLMClient, sub_agents: List[BaseAgent], **kwargs):
        super().__init__(llm_client, **kwargs)
        self.sub_agents = sub_agents

    def execute(self, task: Task) -> AgentResult:
        """顺序执行子Agent"""
        results = []
        for agent in self.sub_agents:
            subtask = self.create_task(
                name=f"{task.name}_{agent.AGENT_TYPE}",
                description=f"执行{agent.name}",
                input_data=task.input_data
            )
            result = agent.run_task(subtask)
            results.append(result)

            if not result.success:
                return AgentResult(
                    success=False,
                    error=f"子Agent {agent.name} 执行失败: {result.error}",
                    data={"sub_results": results}
                )

        return AgentResult(success=True, data={"sub_results": results})


class ParallelAgent(BaseAgent):
    """并行执行多个子任务的Agent"""

    def __init__(self, llm_client: BaseLLMClient, sub_agents: List[BaseAgent], **kwargs):
        super().__init__(llm_client, **kwargs)
        self.sub_agents = sub_agents

    def execute(self, task: Task) -> AgentResult:
        """并行执行子Agent"""
        import concurrent.futures

        results = []
        errors = []

        def run_agent(agent):
            subtask = self.create_task(
                name=f"{task.name}_{agent.AGENT_TYPE}",
                description=f"执行{agent.name}",
                input_data=task.input_data
            )
            return agent.run_task(subtask)

        with concurrent.futures.ThreadPoolExecutor(max_workers=len(self.sub_agents)) as executor:
            future_to_agent = {
                executor.submit(run_agent, agent): agent
                for agent in self.sub_agents
            }

            for future in concurrent.futures.as_completed(future_to_agent):
                agent = future_to_agent[future]
                try:
                    result = future.result()
                    results.append(result)
                    if not result.success:
                        errors.append(f"{agent.name}: {result.error}")
                except Exception as e:
                    errors.append(f"{agent.name}: {str(e)}")

        if errors:
            return AgentResult(
                success=False,
                error="; ".join(errors),
                data={"results": results}
            )

        return AgentResult(success=True, data={"results": results})
