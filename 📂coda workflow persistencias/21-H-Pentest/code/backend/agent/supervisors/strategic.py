"""
Strategic Supervisor - 战略层Agent
负责：制定渗透测试计划、分配子任务、整合结果
"""
from typing import Dict, Any, List, Optional
from agent.core.llm import LLMClient
from agent.core.output import OutputManager
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum


class TaskStatus(str, Enum):
    """任务状态"""
    PENDING = "pending"
    READY = "ready"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    BLOCKED = "blocked"


class TaskPriority(str, Enum):
    """任务优先级"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class Task:
    """任务节点"""
    id: str
    name: str
    description: str
    phase: str
    priority: TaskPriority
    status: TaskStatus = TaskStatus.PENDING
    dependencies: List[str] = None
    estimated_rounds: int = 1
    actual_rounds: int = 0
    tools_required: List[str] = None
    expected_outcomes: List[str] = None
    actual_outcomes: List[str] = None
    error_message: str = None
    created_at: str = None
    started_at: str = None
    completed_at: str = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []
        if self.tools_required is None:
            self.tools_required = []
        if self.expected_outcomes is None:
            self.expected_outcomes = []
        if self.actual_outcomes is None:
            self.actual_outcomes = []
        if self.metadata is None:
            self.metadata = {}
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'phase': self.phase,
            'priority': self.priority.value if isinstance(self.priority, TaskPriority) else self.priority,
            'status': self.status.value if isinstance(self.status, TaskStatus) else self.status,
            'dependencies': self.dependencies,
            'estimated_rounds': self.estimated_rounds,
            'actual_rounds': self.actual_rounds,
            'tools_required': self.tools_required,
            'expected_outcomes': self.expected_outcomes,
            'actual_outcomes': self.actual_outcomes,
            'error_message': self.error_message,
            'created_at': self.created_at,
            'started_at': self.started_at,
            'completed_at': self.completed_at,
            'metadata': self.metadata
        }


@dataclass
class TaskPlan:
    """任务计划"""
    id: str
    target_url: str
    mode: str
    tasks: List[Task]
    phases: List[str]
    current_phase: str = None
    current_task_id: str = None
    total_estimated_rounds: int = 0
    total_actual_rounds: int = 0
    created_at: str = None
    updated_at: str = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()
        if self.updated_at is None:
            self.updated_at = datetime.now().isoformat()
        if self.metadata is None:
            self.metadata = {}
        # 🔥 修复：先检查phases是否为None
        if self.current_phase is None and self.phases and len(self.phases) > 0:
            self.current_phase = self.phases[0]
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'id': self.id,
            'target_url': self.target_url,
            'mode': self.mode,
            'tasks': [task.to_dict() if isinstance(task, Task) else task for task in (self.tasks or [])],
            'phases': self.phases or [],
            'current_phase': self.current_phase,
            'current_task_id': self.current_task_id,
            'total_estimated_rounds': self.total_estimated_rounds,
            'total_actual_rounds': self.total_actual_rounds,
            'total_tasks': len(self.tasks) if self.tasks else 0,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'metadata': self.metadata
        }


class StrategicSupervisor:
    """战略督导 - 制定测试策略和计划"""
    
    def __init__(
        self, 
        target_url: str,
        mode: str,
        llm_client: LLMClient,
        output_manager: OutputManager
    ):
        self.target_url = target_url
        self.mode = mode
        self.llm = llm_client
        self.output = output_manager
        self.context_mgr = None  # 🔥 将由Agent注入
        
        self.current_plan = None
        self.task_history = []
    
    async def create_test_plan(self, conversation_history: List[Dict] = None, preprocess_results: Dict[str, Any] = None) -> TaskPlan:
        """
        创建渗透测试计划（🔥 返回TaskPlan对象）
        
        Args:
            conversation_history: 完整对话历史
            preprocess_results: 预处理结果（包含目标信息、漏洞扫描等）
        
        Returns:
            TaskPlan对象
        """
        self.output.log("info", "📋 Strategic Supervisor: 制定测试计划...")
        
        # 🔥 构建完整上下文
        messages = conversation_history if conversation_history else []
        
        # 🔥🔥🔥 构建预处理信息摘要
        preprocess_summary = ""
        if preprocess_results:
            preprocess_summary = "\n\n## 预处理信息\n"
            
            # 目标信息
            if 'basic_info' in preprocess_results:
                basic = preprocess_results['basic_info']
                preprocess_summary += f"- 状态码: {basic.get('status_code')}\n"
                preprocess_summary += f"- 服务器: {basic.get('server', 'Unknown')}\n"
                if basic.get('title'):
                    preprocess_summary += f"- 页面标题: {basic.get('title')}\n"
            
            # Nuclei扫描结果
            if 'nuclei_scan' in preprocess_results:
                nuclei = preprocess_results['nuclei_scan']
                if nuclei.get('vulnerabilities'):
                    preprocess_summary += f"\n**Nuclei发现 {len(nuclei['vulnerabilities'])} 个漏洞:**\n"
                    for vuln in nuclei['vulnerabilities'][:3]:  # 只显示前3个
                        preprocess_summary += f"  - {vuln.get('name')} ({vuln.get('severity')})\n"
            
            # 目录扫描结果
            if 'directory_scan' in preprocess_results:
                dir_scan = preprocess_results['directory_scan']
                if dir_scan.get('found_paths'):
                    preprocess_summary += f"\n**发现 {len(dir_scan['found_paths'])} 个路径:**\n"
                    for path in dir_scan['found_paths'][:5]:  # 只显示前5个
                        preprocess_summary += f"  - {path}\n"
        
        prompt = f"""作为高级渗透测试战略专家，为目标 {self.target_url} 制定详细的测试计划。

## 目标信息
- URL: {self.target_url}
- 模式: {self.mode.upper()}
{preprocess_summary}

## 要求
请按照以下阶段制定计划，每个阶段包含具体任务：

1. **reconnaissance** (信息收集阶段)
   - 目标识别
   - 技术栈探测
   - 目录结构分析

2. **exploitation** (漏洞利用阶段)
   - 常见漏洞检测
   - 配置错误检查
   - 漏洞利用

3. **post_exploitation** (后渗透阶段)
   - 数据提取
   - 权限提升

请以JSON格式输出计划，格式：
{{
    "tasks": [
        {{
            "id": "task_001",
            "name": "任务名称（用中文）",
            "description": "详细描述（用中文）",
            "phase": "reconnaissance",
            "priority": "high",
            "estimated_rounds": 2,
            "tools_required": ["execute_python"],
            "expected_outcomes": ["预期结果（用中文）"]
        }}
    ]
}}

**重要**：
1. 只输出JSON，不要任何额外说明
2. 确保JSON格式正确
3. tasks数组至少包含3个任务
4. **所有name、description、expected_outcomes必须用中文**
"""
        
        # 🔥 添加prompt到消息
        messages.append({'role': 'user', 'content': prompt})
        
        # 🔥 检查tokens，大于120k*0.8就压缩
        if self.context_mgr:
            current_tokens = self.context_mgr.count_messages_tokens(messages)
            threshold = int(120000 * 0.8)  # 96000
            
            if current_tokens > threshold:
                self.output.log("warning", f"⚠️  Strategic: 对话tokens过大 ({current_tokens}/{threshold})")
                self.output.log("info", "🗜️  触发LangChain智能压缩...")
                
                messages = await self.context_mgr.smart_compress(
                    messages,
                    keep_recent=5,
                    target_ratio=0.5
                )
                
                new_tokens = self.context_mgr.count_messages_tokens(messages)
                self.output.log("success", f"✅ 压缩完成: {current_tokens} -> {new_tokens} tokens")
        
        # 🔥 调用LLM（🔥🔥🔥 全流式输出）
        response = await self.llm.chat(
            messages=messages,
            temperature=0.5,
            stream=True,  # 🔥🔥🔥 全流式输出
            response_format={"type": "json_object"}  # 🔥🔥🔥 强制JSON输出
        )
        
        plan_text = response.get('content', '')
        
        # 🔥🔥🔥 解析JSON并构建TaskPlan对象
        import json
        import uuid
        try:
            # 提取JSON部分
            if '```json' in plan_text:
                json_str = plan_text.split('```json')[1].split('```')[0].strip()
            elif '```' in plan_text:
                json_str = plan_text.split('```')[1].split('```')[0].strip()
            else:
                json_str = plan_text
            
            plan_data = json.loads(json_str)
            
            # 🔥 构建Task对象列表
            tasks = []
            for task_data in plan_data.get('tasks', []):
                task = Task(
                    id=task_data.get('id', f"task_{len(tasks)+1:03d}"),
                    name=task_data.get('name', '未命名任务'),
                    description=task_data.get('description', ''),
                    phase=task_data.get('phase', 'reconnaissance'),
                    priority=TaskPriority(task_data.get('priority', 'medium')),
                    status=TaskStatus.PENDING,
                    dependencies=task_data.get('dependencies', []),
                    estimated_rounds=task_data.get('estimated_rounds', 1),
                    tools_required=task_data.get('tools_required', []),
                    expected_outcomes=task_data.get('expected_outcomes', [])
                )
                tasks.append(task)
            
            # 🔥 构建TaskPlan对象
            task_plan = TaskPlan(
                id=str(uuid.uuid4()),
                target_url=self.target_url,
                mode=self.mode,
                tasks=tasks,
                phases=['reconnaissance', 'exploitation', 'post_exploitation'],
                current_phase='reconnaissance',
                total_estimated_rounds=sum(t.estimated_rounds for t in tasks)
            )
            
            self.current_plan = task_plan
            
            # 🔥🔥🔥 广播到前端（使用to_dict()）
            self.output.plan(task_plan.to_dict())
            
            self.output.log("success", f"✅ 测试计划已生成: {len(tasks)} 个任务")
            
            return task_plan
        
        except Exception as e:
            self.output.log("warning", f"⚠️  计划解析失败: {e}")
            # 返回默认计划
            return self._get_default_task_plan()
    
    def _get_default_task_plan(self) -> TaskPlan:
        """🔥 默认任务计划（返回TaskPlan对象）"""
        import uuid
        
        tasks = [
            Task(
                id="task_001",
                name="获取目标响应",
                description="访问目标URL，获取HTTP响应头和页面内容",
                phase="reconnaissance",
                priority=TaskPriority.HIGH,
                estimated_rounds=1,
                tools_required=["execute_python"],
                expected_outcomes=["HTTP响应头", "页面内容"]
            ),
            Task(
                id="task_002",
                name="技术栈识别",
                description="分析响应头和页面内容，识别框架和语言",
                phase="reconnaissance",
                priority=TaskPriority.HIGH,
                dependencies=["task_001"],
                estimated_rounds=1,
                tools_required=["execute_python"],
                expected_outcomes=["技术栈信息"]
            ),
            Task(
                id="task_003",
                name="SQL注入测试",
                description="对输入点进行SQL注入测试",
                phase="exploitation",
                priority=TaskPriority.HIGH,
                dependencies=["task_002"],
                estimated_rounds=2,
                tools_required=["execute_python"],
                expected_outcomes=["发现注入点"]
            ),
            Task(
                id="task_004",
                name="数据提取",
                description="利用漏洞提取敏感数据或FLAG",
                phase="post_exploitation",
                priority=TaskPriority.CRITICAL,
                dependencies=["task_003"],
                estimated_rounds=2,
                tools_required=["execute_python"],
                expected_outcomes=["FLAG或敏感数据"]
            )
        ]
        
        task_plan = TaskPlan(
            id=str(uuid.uuid4()),
            target_url=self.target_url,
            mode=self.mode,
            tasks=tasks,
            phases=['reconnaissance', 'exploitation', 'post_exploitation'],
            current_phase='reconnaissance',
            total_estimated_rounds=sum(t.estimated_rounds for t in tasks)
        )
        
        # 🔥 广播到前端
        self.output.plan(task_plan.to_dict())
        
        return task_plan
    
    async def analyze_progress(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        分析当前进度和结果
        
        Args:
            results: 执行结果列表
        
        Returns:
            分析报告和下一步建议
        """
        self.output.log("info", "📊 Strategic Supervisor: 分析进度...")
        
        # 统计结果
        total_tasks = len(results)
        successful = len([r for r in results if r.get('status') == 'success'])
        failed = len([r for r in results if r.get('status') == 'failed'])
        
        vulnerabilities = []
        flags = []
        
        for r in results:
            if 'vulnerability' in r:
                vulnerabilities.append(r['vulnerability'])
            if 'flag' in r:
                flags.append(r['flag'])
        
        analysis = {
            'total_tasks': total_tasks,
            'successful': successful,
            'failed': failed,
            'vulnerabilities_found': len(vulnerabilities),
            'flags_found': len(flags),
            'completion_rate': successful / total_tasks if total_tasks > 0 else 0
        }
        
        # 发送战略分析到前端
        self.output.strategic(analysis, round_num=0)
        
        return analysis
    
    async def adjust_strategy(self, analysis: Dict[str, Any]) -> List[str]:
        """
        根据分析结果调整策略（🔥 返回changes列表）
        
        Returns:
            changes: 计划变更列表
        """
        completion_rate = analysis.get('completion_rate', 0)
        vulns_found = analysis.get('vulnerabilities_found', 0)
        
        suggestions = []
        
        if completion_rate < 0.5:
            suggestions.append("当前进度较慢，建议调整策略")
        
        if vulns_found == 0:
            suggestions.append("未发现漏洞，建议尝试更多测试向量")
        
        if vulns_found > 0:
            suggestions.append("已发现漏洞，优先深入利用")
        
        return suggestions
    
    async def adjust_plan(self, conversation_history: list = None, execution_results: list = None, current_round: int = 0) -> Dict[str, Any]:
        """
        🔥🔥🔥 动态调整计划（使用LLM智能分析）
        
        Returns:
            {
                'changes': [
                    {'action': 'add_task', 'task': {...}},
                    {'action': 'skip_task', 'task_id': '...', 'reason': '...'},
                    {'action': 'update_priority', 'task_id': '...', 'new_priority': '...'}
                ]
            }
        """
        if not self.llm or not conversation_history or not self.current_plan:
            return {'changes': []}
        
        try:
            messages = conversation_history.copy()
            
            # 当前计划摘要
            plan_summary = f"""当前计划：
- 总任务数: {len(self.current_plan.tasks)}
- 当前阶段: {self.current_plan.current_phase}
- 任务状态: {[(t.name, t.status.value) for t in self.current_plan.tasks[:5]]}
"""
            
            # 最近执行结果
            recent_results = execution_results[-3:] if execution_results else []
            results_summary = "\n".join([f"- Round {r.get('round')}: {r.get('status')}" for r in recent_results])
            
            prompt = f"""分析Worker的执行进度，决定是否需要调整计划。

{plan_summary}

最近执行结果：
{results_summary if results_summary else '暂无'}

请分析：
1. 哪些任务已经完成？（标记为完成）
2. 哪些任务正在执行？（更新进度）
3. 是否需要添加新任务？
4. 是否有任务应该跳过？

以JSON格式输出：
{{
    "needs_adjustment": true/false,
    "reason": "调整原因（用中文）",
    "changes": [
        {{
            "action": "complete_task",
            "task_id": "task_001",
            "reason": "任务已完成（用中文）"
        }},
        {{
            "action": "update_progress",
            "task_id": "task_002",
            "completed_rounds": 2,
            "reason": "更新进度（用中文）"
        }},
        {{
            "action": "start_task",
            "task_id": "task_003",
            "reason": "开始执行（用中文）"
        }},
        {{
            "action": "add_task",
            "task": {{
                "id": "task_new_001",
                "name": "任务名（用中文）",
                "description": "描述（用中文）",
                "phase": "reconnaissance",
                "priority": "high",
                "estimated_rounds": 2
            }}
        }},
        {{
            "action": "skip_task",
            "task_id": "task_004",
            "reason": "跳过原因（用中文）"
        }}
    ]
}}

**重要**：
1. 只输出JSON
2. 如无需调整，needs_adjustment=false, changes=[]
3. action可为: complete_task, update_progress, start_task, add_task, skip_task, update_priority
4. **所有reason、name、description必须用中文**
5. **优先标记已完成的任务，然后更新正在进行的任务进度**
"""
            messages.append({'role': 'user', 'content': prompt})
            
            response = await self.llm.chat(
                messages=messages,
                temperature=0.5,
                stream=True,  # 🔥 全流式输出
                response_format={"type": "json_object"}
            )
            
            # 解析JSON
            import json
            content = response.get('content', '{}')
            if '```json' in content:
                content = content.split('```json')[1].split('```')[0].strip()
            elif '```' in content:
                content = content.split('```')[1].split('```')[0].strip()
            
            result = json.loads(content)
            
            if not result.get('needs_adjustment', False):
                self.output.log("info", "ℹ️  当前计划无需调整")
                return {'changes': []}
            
            changes = result.get('changes', [])
            self.output.log("success", f"✅ 计划需要调整: {len(changes)} 项变更")
            
            return {'changes': changes}
            
        except Exception as e:
            self.output.log("warning", f"⚠️  计划调整失败: {e}")
            import traceback
            traceback.print_exc()
            return {'changes': []}
    
    async def replace_plan(self, changes: list) -> TaskPlan:
        """
        🔥🔥🔥 根据changes更新计划（直接修改self.current_plan）
        
        Args:
            changes: 变更列表
        
        Returns:
            更新后的TaskPlan
        """
        if not self.current_plan or not changes:
            return self.current_plan
        
        import uuid
        from datetime import datetime
        
        for change in changes:
            action = change.get('action')
            
            if action == 'add_task':
                # 添加新任务
                task_data = change.get('task', {})
                priority_str = task_data.get('priority', 'medium') or 'medium'  # 🔥 防止None
                new_task = Task(
                    id=task_data.get('id', f"task_{uuid.uuid4().hex[:8]}"),
                    name=task_data.get('name', '未命名任务'),
                    description=task_data.get('description', ''),
                    phase=task_data.get('phase', 'reconnaissance'),
                    priority=TaskPriority(priority_str),
                    status=TaskStatus.PENDING,
                    estimated_rounds=task_data.get('estimated_rounds', 1),
                    tools_required=task_data.get('tools_required', []),
                    expected_outcomes=task_data.get('expected_outcomes', [])
                )
                self.current_plan.tasks.append(new_task)
                self.output.log("success", f"➕ 添加新任务: {new_task.name}")
            
            elif action == 'skip_task':
                # 跳过任务
                task_id = change.get('task_id')
                reason = change.get('reason', '')
                for task in self.current_plan.tasks:
                    if task.id == task_id:
                        task.status = TaskStatus.SKIPPED
                        self.output.log("info", f"⏭️  跳过任务: {task.name} - {reason}")
                        break
            
            elif action == 'update_priority':
                # 更新优先级
                task_id = change.get('task_id')
                new_priority = change.get('new_priority', 'medium') or 'medium'  # 🔥 防止None
                for task in self.current_plan.tasks:
                    if task.id == task_id:
                        task.priority = TaskPriority(new_priority)
                        self.output.log("info", f"🔺 更新优先级: {task.name} -> {new_priority}")
                        break
            
            elif action == 'complete_task':
                # 🔥 标记任务为完成
                task_id = change.get('task_id')
                for task in self.current_plan.tasks:
                    if task.id == task_id:
                        task.status = TaskStatus.COMPLETED
                        task.completed_rounds = task.estimated_rounds  # 设置为预估轮数
                        self.output.log("success", f"✅ 任务已完成: {task.name}")
                        break
            
            elif action == 'update_progress':
                # 🔥 更新任务进度
                task_id = change.get('task_id')
                completed_rounds = change.get('completed_rounds', 0)
                for task in self.current_plan.tasks:
                    if task.id == task_id:
                        task.completed_rounds = completed_rounds
                        # 如果完成轮数达到预估轮数，自动标记为完成
                        if completed_rounds >= task.estimated_rounds:
                            task.status = TaskStatus.COMPLETED
                            self.output.log("success", f"✅ 任务已完成: {task.name} ({completed_rounds}/{task.estimated_rounds})")
                        else:
                            task.status = TaskStatus.IN_PROGRESS
                            self.output.log("info", f"📊 任务进度更新: {task.name} ({completed_rounds}/{task.estimated_rounds})")
                        break
            
            elif action == 'start_task':
                # 🔥 开始执行任务
                task_id = change.get('task_id')
                for task in self.current_plan.tasks:
                    if task.id == task_id:
                        task.status = TaskStatus.IN_PROGRESS
                        self.output.log("info", f"▶️  开始任务: {task.name}")
                        break
        
        # 更新updated_at
        self.current_plan.updated_at = datetime.now().isoformat()
        
        return self.current_plan
