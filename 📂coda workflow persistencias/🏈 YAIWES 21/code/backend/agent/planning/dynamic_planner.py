"""
动态计划器 - 基于预处理信息生成和动态调整任务计划
支持因果任务计划(Causal Task Plan)和全局攻击路径规划(Global Attack Plan)
"""
import json
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum
from dataclasses import dataclass, asdict
from datetime import datetime
# 🔥 适配新后端：移除旧的logger导入，使用print
import logging
logger = logging.getLogger(__name__)

def log_message(msg_type: str, content: str):
    """兼容旧代码的log_message"""
    logger.info(f"[{msg_type}] {content}")

def log_error(error_type: str, content: str):
    """兼容旧代码的log_error"""
    logger.error(f"[{error_type}] {content}")


class TaskStatus(str, Enum):
    """任务状态"""
    PENDING = "pending"          # 待执行
    READY = "ready"              # 就绪(依赖已满足)
    IN_PROGRESS = "in_progress"  # 执行中
    COMPLETED = "completed"      # 已完成
    FAILED = "failed"            # 失败
    SKIPPED = "skipped"          # 跳过
    BLOCKED = "blocked"          # 阻塞(依赖未满足)


class TaskPriority(str, Enum):
    """任务优先级"""
    CRITICAL = "critical"  # 关键任务(如已发现漏洞的利用)
    HIGH = "high"          # 高优先级
    MEDIUM = "medium"      # 中等优先级
    LOW = "low"            # 低优先级


@dataclass
class Task:
    """任务节点"""
    id: str                              # 任务ID
    name: str                            # 任务名称
    description: str                     # 任务描述
    phase: str                           # 所属阶段(reconnaissance/exploitation/post_exploitation)
    priority: TaskPriority               # 优先级
    status: TaskStatus = TaskStatus.PENDING
    dependencies: List[str] = None       # 依赖的任务ID列表(因果关系)
    estimated_rounds: int = 1            # 预估轮数
    actual_rounds: int = 0               # 实际执行轮数
    tools_required: List[str] = None     # 需要的工具列表
    expected_outcomes: List[str] = None  # 期望结果
    actual_outcomes: List[str] = None    # 实际结果
    error_message: str = None            # 错误信息
    created_at: str = None               # 创建时间
    started_at: str = None               # 开始时间
    completed_at: str = None             # 完成时间
    metadata: Dict[str, Any] = None      # 元数据
    
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
        # 🔥🔥🔥 手动构建字典，确保所有字段都正确序列化
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
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Task':
        """从字典创建"""
        # 处理枚举类型
        if 'priority' in data and isinstance(data['priority'], str):
            data['priority'] = TaskPriority(data['priority'])
        if 'status' in data and isinstance(data['status'], str):
            data['status'] = TaskStatus(data['status'])
        return cls(**data)


@dataclass
class TaskPlan:
    """任务计划"""
    id: str                          # 计划ID
    target_url: str                  # 目标URL
    mode: str                        # 模式(ctf/realworld)
    tasks: List[Task]                # 任务列表
    phases: List[str]                # 阶段列表
    current_phase: str = None        # 当前阶段
    current_task_id: str = None      # 当前执行的任务ID
    total_estimated_rounds: int = 0  # 总预估轮数
    total_actual_rounds: int = 0     # 总实际轮数
    created_at: str = None           # 创建时间
    updated_at: str = None           # 更新时间
    metadata: Dict[str, Any] = None  # 元数据
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()
        if self.updated_at is None:
            self.updated_at = datetime.now().isoformat()
        if self.metadata is None:
            self.metadata = {}
        if self.phases is None or len(self.phases) == 0:
            self.phases = ["reconnaissance", "exploitation", "post_exploitation"]
        if self.current_phase is None and len(self.phases) > 0:
            self.current_phase = self.phases[0]
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        # 🔥🔥🔥 关键修复：直接手动构建字典，不使用asdict（避免双重序列化）
        return {
            'id': self.id,
            'target_url': self.target_url,
            'mode': self.mode,
            'tasks': [task.to_dict() if isinstance(task, Task) else task for task in self.tasks],
            'phases': self.phases,
            'current_phase': self.current_phase,
            'current_task_id': self.current_task_id,
            'total_estimated_rounds': self.total_estimated_rounds,
            'total_actual_rounds': self.total_actual_rounds,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TaskPlan':
        """从字典创建"""
        # 转换Task对象
        if 'tasks' in data:
            data['tasks'] = [Task.from_dict(t) if isinstance(t, dict) else t for t in data['tasks']]
        return cls(**data)
    
    def get_next_task(self) -> Optional[Task]:
        """🔥 获取下一个应该执行的任务（基于依赖和优先级）"""
        # 首先查找所有in_progress的任务
        in_progress = [t for t in self.tasks if t.status == 'in_progress']
        if in_progress:
            # 按优先级排序，返回最高优先级的
            in_progress.sort(key=lambda t: ['low', 'medium', 'high', 'critical'].index(t.priority.value))
            return in_progress[-1]
        
        # 然后查找可以开始的pending任务（依赖已完成）
        pending = [t for t in self.tasks if t.status == 'pending']
        ready_tasks = []
        for task in pending:
            # 检查所有依赖是否已完成
            if not task.dependencies:
                ready_tasks.append(task)
            else:
                deps_completed = all(
                    any(t.id == dep_id and t.status == 'completed' for t in self.tasks)
                    for dep_id in task.dependencies
                )
                if deps_completed:
                    ready_tasks.append(task)
        
        if ready_tasks:
            # 按优先级排序
            ready_tasks.sort(key=lambda t: ['low', 'medium', 'high', 'critical'].index(t.priority.value))
            return ready_tasks[-1]  # 返回最高优先级
        
        return None


class DynamicPlanner:
    """动态计划器 - LLM驱动的任务规划和调整"""
    
    def __init__(self, llm_client, mode_manager, knowledge_base):
        """
        初始化动态计划器
        
        Args:
            llm_client: LLM客户端
            mode_manager: 模式管理器
            knowledge_base: 知识库
        """
        self.llm = llm_client
        self.mode_manager = mode_manager
        self.knowledge = knowledge_base
        self.current_plan: Optional[TaskPlan] = None

        # 🔥 新增：记录决策历史（供 Meta 监督使用）
        self.decision_history: List[Dict[str, Any]] = []

        # 🔥 加载配置
        self._load_config()

        log_message('system', '动态计划器初始化完成')

    def _load_config(self):
        """从配置文件加载planner配置"""
        try:
            # 🔥 适配新后端：使用默认配置
            self.planner_max_tokens = 8192
            log_message('system', f'✅ Planner配置: max_tokens={self.planner_max_tokens}')
        except Exception as e:
            log_error('PlannerConfigError', f'加载planner配置失败: {e}')
            self.planner_max_tokens = 8192

    def _get_planner_max_tokens(self) -> int:
        """获取planner的max_tokens配置"""
        return getattr(self, 'planner_max_tokens', 8192)
    
    async def generate_initial_plan(self, 
                             target_url: str,
                             preprocess_info: Dict[str, Any],
                             max_rounds: int,
                             available_tools: Optional[List[Dict[str, Any]]] = None,
                             task_id: Optional[str] = None) -> TaskPlan:  # 🔥🔥🔥 必须传递以支持任务取消
        """
        生成初始任务计划 - 由LLM根据预处理信息生成
        
        Args:
            target_url: 目标URL
            preprocess_info: 预处理收集的信息
            max_rounds: 最大轮数限制
            available_tools: 可用工具列表
        
        Returns:
            TaskPlan对象
        """
        import time
        t_start = time.time()
        log_message('planning', '🧠 开始生成初始任务计划...')
        
        # 构建计划生成提示词
        t1 = time.time()
        planning_prompt = self._build_planning_prompt(
            target_url, 
            preprocess_info, 
            max_rounds,
            available_tools  # 🔥 传入可用工具
        )
        log_message('planning', f'⏱️  构建 Planning Prompt 耗时: {time.time()-t1:.2f}s')
        
        # 🔥 打印详细的Planning Prompt给用户看
        log_message('planning', '\n' + '='*70)
        log_message('planning', '📋 【发送给LLM的完整计划生成提示】')
        log_message('planning', '='*70)
        print(planning_prompt[:3000])  # 打印前3000字符
        if len(planning_prompt) > 3000:
            print(f"\n... (提示词总长度: {len(planning_prompt)} 字符)")
        log_message('planning', '='*70 + '\n')
        
        # 调用LLM生成计划
        log_message('planning', '📡 调用LLM生成任务计划...')
        log_message('planning', '⏳ LLM正在生成计划（流式输出）...')
        print("\n" + "="*70)
        print("🤖 LLM计划生成中...")
        print("="*70)
        
        # 🔥 添加重试机制（最多3次）
        max_retries = 3
        for attempt in range(max_retries):
            try:
                if attempt > 0:
                    log_message('planning', f'⏳ 第 {attempt+1} 次尝试生成计划...')
                
                t2 = time.time()
                # 🔥 适配新后端：直接使用传入的llm_client
                planner_llm = self.llm
                
                # 🔥🔥🔥 使用 Prompt Cache 优化
                system_prompt = self._get_planner_system_prompt()
                cacheable_messages = planner_llm.build_cacheable_messages(
                    messages=[],  # 动态历史为空
                    system_prompt=system_prompt,  # 静态系统提示词
                    tools_description=None,  # Planner不使用工具
                    static_context=None
                )
                # 添加动态用户提示
                cacheable_messages.append({'role': 'user', 'content': planning_prompt})
                
                # 🔥🔥🔥 使用异步LLM调用
                response = await chat_async(
                    llm_client=planner_llm,
                    messages=cacheable_messages,  # 🔥 使用优化后的消息
                temperature=0.1,
                stream=True,
                max_tokens=self._get_planner_max_tokens(),
                response_format={"type": "json_object"},
                task_id=task_id
            )
                log_message('planning', f'⏱️  LLM调用耗时: {time.time()-t2:.2f}s')
                
                # 🔥🔥🔥 关键：立即打印LLM返回的原始内容
                print("\n" + "="*80)
                print("📡 LLM计划生成响应原始数据")
                print("="*80)
                print(f"response 类型: {type(response)}")
                print(f"response 内容: {response}")
                print("="*80 + "\n")
                
                print("="*70 + "\n")
                break  # 成功，退出重试循环
                
            except Exception as llm_error:
                log_error('PlanningError', f'第 {attempt+1} 次LLM调用失败: {llm_error}')
                if attempt < max_retries - 1:
                    log_message('planning', '⏳ 将在 2 秒后重试...')
                    time.sleep(2)
                else:
                    log_message('planning', '⚠️ LLM调用失败，使用后备计划')
                    return self._create_fallback_plan(target_url, max_rounds, preprocess_info)
        
        # 解析LLM返回的计划
        try:
            t3 = time.time()
            # 🔥 LLM返回的是字典 {'content': '...', 'tool_calls': ...}
            response_content = response.get('content', '') if isinstance(response, dict) else str(response)
            log_message('planning', f'⏱️  提取response耗时: {time.time()-t3:.2f}s')
            
            # 🔥🔥🔥 关键修复：完整打印LLM返回内容，不截断
            print("\n" + "="*80)
            print("🔥🔥🔥 LLM生成计划的完整输出")
            print("="*80)
            print(response_content)  # 🔥 打印完整内容，不截断
            print("="*80)
            print(f"📊 总长度: {len(response_content)} 字符")
            print("="*80 + "\n")
            
            # 同时使用logger记录
            log_message('planning', f'📝 LLM返回完整内容：\n{response_content}')
            
            # 提取JSON内容（可能被```json```包裹）
            import re
            json_match = re.search(r'```json\s*({.*?})\s*```', response_content, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
                log_message('planning', '✅ 找到JSON代码块')
                print("\n✅ 找到JSON代码块，提取内容：")
                print("-"*80)
                print(json_str[:1000])  # 打印前1000字符
                if len(json_str) > 1000:
                    print(f"\n... (JSON总长度: {len(json_str)} 字符)")
                print("-"*80 + "\n")
            else:
                # 直接尝试解析
                json_str = response_content
                log_message('planning', '⚠️ 未找到```json```包裹，直接解析')
                print("\n⚠️ 未找到```json```包裹，将直接解析整个内容\n")
            
            # 尝试解析JSON
            print("🔍 开始解析JSON...")
            plan_data = json.loads(json_str)
            print("✅ JSON解析成功！")
            print(f"📋 计划数据：")
            print(f"   - tasks: {len(plan_data.get('tasks', []))} 个")
            print(f"   - phases: {plan_data.get('phases', [])}")
            print(f"   - total_estimated_rounds: {plan_data.get('total_estimated_rounds', '?')}")
            print()
            
            task_plan = self._parse_llm_plan(
                plan_data, 
                target_url, 
                self.mode_manager.mode.value
            )
            
            self.current_plan = task_plan
            
            log_message('planning', f'✅ 初始计划生成完成: {len(task_plan.tasks)} 个任务')
            log_message('planning', f'   - 阶段数: {len(task_plan.phases)}')
            log_message('planning', f'   - 预估总轮数: {task_plan.total_estimated_rounds}')
            
            return task_plan
            
        except json.JSONDecodeError as e:
            log_error('PlanningError', f'解析LLM计划失败: {e}')
            print(f"\n❌ JSON解析失败：{e}")
            print(f"🔍 尝试解析的内容：")
            print("-"*80)
            print(json_str[:500])
            print("-"*80 + "\n")
            # 返回默认计划
            return self._create_fallback_plan(target_url, max_rounds, preprocess_info)
    
    async def adjust_plan(self,
                   current_round: int,
                   execution_results: List[Dict[str, Any]],
                   discoveries: List[Dict[str, Any]],
                   tool_calls: Optional[List[Dict]] = None,  # 🔥 当前轮工具调用
                   tool_results: Optional[List[Dict]] = None,  # 🔥 当前轮工具结果
                   recent_conversations: Optional[List[Dict]] = None,  # 🔥🔥🔥 完整对话历史（从开始到现在）
                   recent_tool_results_all: Optional[List[Dict]] = None,  # 🔥 最近3轮工具结果
                   task_id: Optional[str] = None  # 🔥🔥🔥 必须传递以支持任务取消
                   ) -> Tuple[TaskPlan, List[str], List[str]]:
        """
        动态调整任务计划 - 根据执行结果由LLM智能调整
        🔥 优化：同时评估任务完成度和调整计划，一次LLM调用完成两项工作
        
        Args:
            current_round: 当前轮次
            execution_results: 最近的执行结果列表
            discoveries: 新发现的信息(漏洞、敏感信息等)
            tool_calls: 本轮执行的工具调用列表（用于任务完成度评估）
            tool_results: 本轮工具执行结果（用于任务完成度评估）
            recent_conversations: 🔥🔥🔥 完整对话历史（从任务开始到现在的所有对话）
            recent_tool_results_all: 最近3轮的工具结果
        
        Returns:
            (调整后的TaskPlan, 调整说明列表, 已完成任务ID列表)
        """
        if not self.current_plan:
            log_message('warning', '无当前计划，跳过调整')
            return None, [], []
        
        log_message('planning', f'🔄 Round {current_round}: 评估任务完成度 + 调整计划...')
        
        # 构建调整请求提示词（🔥 包含任务完成度评估 + 完整对话历史）
        adjustment_prompt = self._build_adjustment_prompt(
            self.current_plan,
            current_round,
            execution_results,
            discoveries,
            tool_calls,      # 🔥 当前轮工具调用
            tool_results,    # 🔥 当前轮工具结果
            recent_conversations,      # 🔥 最近3轮完整对话
            recent_tool_results_all    # 🔥 最近3轮工具结果
        )
        
        # 调用LLM判断是否需要调整
        log_message('planning', '📡 调用LLM评估计划调整...')
        # 🔥 适配新后端：直接使用传入的llm_client
        planner_llm = self.llm
        
        # 🔥🔥🔥 使用 Prompt Cache 优化
        system_prompt = self._get_adjuster_system_prompt()
        cacheable_messages = planner_llm.build_cacheable_messages(
            messages=[],
            system_prompt=system_prompt,
            tools_description=None,
            static_context=None
        )
        cacheable_messages.append({'role': 'user', 'content': adjustment_prompt})
        
        # 🔥🔥🔥 打印调用前的信息
        print(f"\n{'='*80}")
        print(f"🤖 计划调整LLM调用开始")
        print(f"{'='*80}")
        print(f"流式: True")
        print(f"{'='*80}\n")
        
        try:
            # 🔥🔥🔥 适配新后端：使用llm.chat方法
            response_raw = await planner_llm.chat(
                llm_client=planner_llm,
                messages=cacheable_messages,  # 🔥 使用优化后的消息
            temperature=0.1,
            stream=True,
            max_tokens=self._get_planner_max_tokens(),
            response_format={"type": "json_object"},
            timeout_override=120,
            task_id=task_id
        )
        except TimeoutError as timeout_err:
            # 🔥🔥🔥 处理超时：返回默认“不调整”
            log_message('warning', f'⚠️  计划调整LLM超时: {timeout_err}')
            log_message('planning', '🚀 超时后默认不调整计划，继续执行现有计划')
            
            # 返回默认响应：不需要调整
            return {
                'needs_adjustment': False,
                'reason': f'LLM超时，默认不调整: {str(timeout_err)}',
                'adjustments': [],
                'priority_changes': []
            }
        
        # 🔥🔥🔥 打印LLM返回的原始响应
        print(f"\n{'='*80}")
        print(f"📡 计划调整LLM响应")
        print(f"{'='*80}")
        print(f"响应类型: {type(response)}")
        print(f"响应keys: {response.keys() if isinstance(response, dict) else 'N/A'}")
        print(f"{'='*80}\n")
        
        # 解析调整决策
        try:
            # 🔥 提取content
            response_content = response.get('content', '') if isinstance(response, dict) else str(response)
            
            # 🔥🔥🔥 打印完整内容
            print(f"\n{'='*80}")
            print(f"🔥 计划调整LLM完整响应内容")
            print(f"{'='*80}")
            print(response_content)
            print(f"{'='*80}")
            print(f"📊 总长度: {len(response_content)} 字符")
            print(f"{'='*80}\n")
            
            # 🔥 保存LLM的计划调整决策到数据库（用于前端显示）
            try:
                import sys
                import os
                from pathlib import Path
                # 使用相对路径：从当前文件找到项目根目录
                project_root = Path(__file__).parent.parent.absolute()
                backend_path = str(project_root / "backend")
                if backend_path not in sys.path:
                    sys.path.insert(0, backend_path)
                from app.db.database import SessionLocal
                from app.services.message_service import MessageService
                
                # 尝试获取task_id（可能在agent中设置）
                task_id = getattr(self, '_task_id', None)
                if not task_id:
                    # 尝试从self.llm获取
                    task_id = getattr(self.llm, '_task_id', None)
                
                if task_id:
                    db = SessionLocal()
                    try:
                        MessageService.save_llm_response(
                            db=db,
                            task_id=task_id,
                            content=f"📋 **计划调整决策**\n\n{response_content}",
                            round_num=current_round,
                            has_tool_calls=False
                        )
                        log_message('planning', '✅ 计划调整决策已保存到数据库')
                    finally:
                        db.close()
            except Exception as save_error:
                log_message('warning', f'⚠️ 保存计划调整决策失败: {save_error}')
            
            # 提取JSON内容 - 智能多模式提取
            import re
            import logging
            logger = logging.getLogger(__name__)
            
            json_str = None
            
            # 方法1: 提取 ```json ... ``` 代码块
            json_match = re.search(r'```json\s*({.*?})\s*```', response_content, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
                logger.info('✅ 提取方式1: 找到 ```json 代码块')
            
            # 方法2: 提取 ``` ... ``` 代码块（无json标记）
            if not json_str:
                json_match = re.search(r'```\s*({.*?})\s*```', response_content, re.DOTALL)
                if json_match:
                    json_str = json_match.group(1)
                    logger.info('✅ 提取方式2: 找到 ``` 代码块')
            
            # 方法3: 直接提取完整的 JSON 对象（从第一个 { 到最后一个 }）
            if not json_str:
                # 找到第一个 { 的位置
                first_brace = response_content.find('{')
                if first_brace != -1:
                    # 从这个位置开始，找到匹配的 }
                    brace_count = 0
                    start = first_brace
                    end = -1
                    for i in range(first_brace, len(response_content)):
                        if response_content[i] == '{':
                            brace_count += 1
                        elif response_content[i] == '}':
                            brace_count -= 1
                            if brace_count == 0:
                                end = i + 1
                                break
                    
                    if end != -1:
                        json_str = response_content[start:end]
                        logger.info('✅ 提取方式3: 通过括号匹配提取JSON对象')
            
            # 方法4: 使用正则提取 needs_adjustment 开始的对象
            if not json_str:
                json_match = re.search(r'({\s*["\']needs_adjustment["\'].*?})(?:\s*```)?', response_content, re.DOTALL)
                if json_match:
                    json_str = json_match.group(1)
                    logger.info('✅ 提取方式4: 通过 needs_adjustment 字段定位')
            
            # 方法5: 最后尝试整个内容
            if not json_str:
                json_str = response_content
                logger.warning('⚠️ 提取方式5: 所有方法失败，尝试直接解析整个内容')
            
            # 清理 JSON 字符串
            json_str = json_str.strip()
            
            # 🔥🔥🔥 关键调试：打印JSON内容
            log_message('debug', f'🔍 尝试解析的JSON: {json_str[:500]}...')
            
            adjustment_data = json.loads(json_str)
            
            # 🔥🔥🔥 打印解析结果 - 使用logger.info确保输出
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f'✅ JSON解析成功')
            logger.info(f'🔥🔥🔥 完整的 adjustment_data: {json.dumps(adjustment_data, ensure_ascii=False)[:1000]}')
            
            log_message('planning', f'✅ JSON解析成功')
            log_message('planning', f'🔥🔥🔥 完整的 adjustment_data: {json.dumps(adjustment_data, ensure_ascii=False)[:1000]}')
            
            # 🔥🔥🔥 新增：处理任务完成度评估
            completed_task_ids = []
            if 'task_completion' in adjustment_data:
                task_completion_data = adjustment_data.get('task_completion', {})
                completed_tasks_list = task_completion_data.get('completed_tasks', [])
                
                logger.info(f'📊 任务完成度评估: {len(completed_tasks_list)} 个任务需要评估')
                log_message('planning', f'📊 任务完成度评估: {len(completed_tasks_list)} 个任务需要评估')
                
                for task_data in completed_tasks_list:
                    task_id = task_data.get('task_id')
                    completed = task_data.get('completed', False)
                    outcomes = task_data.get('actual_outcomes', [])
                    reason = task_data.get('reason', '')
                    
                    if completed:
                        # 查找任务并更新状态
                        task = self._find_task(task_id)
                        if task and task.status != TaskStatus.COMPLETED:
                            task.status = TaskStatus.COMPLETED
                            task.actual_outcomes = outcomes
                            task.completed_at = datetime.now().isoformat()
                            completed_task_ids.append(task_id)
                            
                            logger.info(f'✅ 任务完成: {task.name}')
                            logger.info(f'   理由: {reason}')
                            logger.info(f'   成果: {", ".join(outcomes[:3])}')
                            
                            log_message('planning', f'✅ 任务完成: {task.name}')
                            log_message('planning', f'   理由: {reason}')
                            log_message('planning', f'   成果: {", ".join(outcomes[:3])}')
            
            # 🔥🔥🔥 处理计划调整
            plan_adjustment_data = adjustment_data.get('plan_adjustment', adjustment_data)  # 🔥 向后兼容：如果没有plan_adjustment字段，则使用整个adjustment_data
            
            logger.info(f'   - needs_adjustment: {plan_adjustment_data.get("needs_adjustment", False)}')
            logger.info(f'   - reason: {plan_adjustment_data.get("reason", "")[:100]}...')
            logger.info(f'   - adjustments 数量: {len(plan_adjustment_data.get("adjustments", []))}')
            
            log_message('planning', f'   - needs_adjustment: {plan_adjustment_data.get("needs_adjustment", False)}')
            log_message('planning', f'   - reason: {plan_adjustment_data.get("reason", "")[:100]}...')
            log_message('planning', f'   - adjustments 数量: {len(plan_adjustment_data.get("adjustments", []))}')
            
            if not plan_adjustment_data.get('needs_adjustment', False):
                logger.info(f'⚠️ 计划无需调整（needs_adjustment={plan_adjustment_data.get("needs_adjustment")}），继续执行')
                log_message('planning', f'⚠️ 计划无需调整（needs_adjustment={plan_adjustment_data.get("needs_adjustment")}），继续执行')
                # 🔥🔥🔥 新增：打印完整的 adjustment_data 便于调试
                log_message('debug', f'🔍 完整的 adjustment_data: {json.dumps(adjustment_data, ensure_ascii=False, indent=2)}')
                return self.current_plan, [], completed_task_ids  # 🔥 返回完成的任务ID
            
            # 应用调整
            changes = self._apply_adjustments(plan_adjustment_data)  # 🔥 修复：传入 plan_adjustment_data
            
            # 🔥🔥🔥 关键调试：打印调整后的计划状态
            log_message('planning', f'✅ 计划已调整: {len(changes)} 项变更')
            for change in changes:
                log_message('planning', f'   - {change}')
            
            log_message('planning', f'📊 调整后计划状态: 总任务数={len(self.current_plan.tasks)}, 阶段={self.current_plan.phases}, 当前阶段={self.current_plan.current_phase}, 预估轮数={self.current_plan.total_estimated_rounds}')
            log_message('planning', f'   📝 任务列表: {", ".join([f"{t.name}({t.status})" for t in self.current_plan.tasks])}')
            
            return self.current_plan, changes, completed_task_ids  # 🔥 返回完成的任务ID
            
        except json.JSONDecodeError as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f'❌ JSON解析失败: {e}')
            logger.error(f'❗ JSON解析失败的内容: {json_str[:1000] if "json_str" in locals() else "N/A"}')
            log_error('PlanningError', f'解析调整结果失败: {e}')
            log_message('error', f'🔥🔥🔥 JSON解析失败的内容: {json_str[:1000] if "json_str" in locals() else "N/A"}')
            return self.current_plan, [], []  # 🔥 返回空的完成任务列表
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f'❌ 调整计划时发生异常: {e}')
            import traceback
            logger.error(traceback.format_exc())
            log_error('PlanningError', f'调整计划时发生异常: {e}')
            log_message('error', traceback.format_exc())
            return self.current_plan, [], []  # 🔥 返回空的完成任务列表
    
    def get_next_task(self) -> Optional[Task]:
        """
        获取下一个应该执行的任务
        
        Returns:
            下一个Task对象，如果没有则返回None
        """
        if not self.current_plan:
            return None
        
        # 1. 查找就绪的任务(依赖已满足)
        ready_tasks = []
        for task in self.current_plan.tasks:
            if task.status in [TaskStatus.PENDING, TaskStatus.BLOCKED]:
                # 检查依赖是否满足
                if self._are_dependencies_met(task):
                    task.status = TaskStatus.READY
                    ready_tasks.append(task)
        
        if not ready_tasks:
            log_message('planning', '⚠️ 无就绪任务')
            return None
        
        # 2. 按优先级和阶段排序
        ready_tasks.sort(key=lambda t: (
            self._priority_value(t.priority),
            self._phase_value(t.phase)
        ))
        
        next_task = ready_tasks[0]
        log_message('planning', f'📋 下一任务: {next_task.name} (优先级: {next_task.priority.value})')
        
        return next_task
    
    def mark_task_completed(self, 
                           task_id: str, 
                           actual_rounds: int,
                           outcomes: List[str]):
        """标记任务完成"""
        task = self._find_task(task_id)
        if task:
            task.status = TaskStatus.COMPLETED
            task.actual_rounds = actual_rounds
            task.actual_outcomes = outcomes
            task.completed_at = datetime.now().isoformat()
            self.current_plan.total_actual_rounds += actual_rounds
            self.current_plan.updated_at = datetime.now().isoformat()
            
            log_message('planning', f'✅ 任务完成: {task.name} (耗时 {actual_rounds} 轮)')
    
    def mark_task_failed(self, task_id: str, error: str):
        """标记任务失败"""
        task = self._find_task(task_id)
        if task:
            task.status = TaskStatus.FAILED
            task.error_message = error
            task.completed_at = datetime.now().isoformat()
            self.current_plan.updated_at = datetime.now().isoformat()
            
            log_message('planning', f'❌ 任务失败: {task.name} - {error}')
    
    def _build_planning_prompt(self, 
                               target_url: str,
                               preprocess_info: Dict[str, Any],
                               max_rounds: int,
                               available_tools: Optional[List[Dict[str, Any]]] = None) -> str:
        """构建初始计划生成提示词"""
        # 🔥 只提取关键信息，不包含完整HTML
        key_info = {
            'target': preprocess_info.get('target'),
            'status': preprocess_info.get('page_data', {}).get('status'),
            'forms': preprocess_info.get('features', {}).get('forms', []),
            'framework': preprocess_info.get('features', {}).get('framework', []),
            'matches': preprocess_info.get('matches', [])[:5],  # 只前5个漏洞
            'structured_vulnerabilities': preprocess_info.get('structured_vulnerabilities', [])[:5],
            'cookies': preprocess_info.get('llm_context', {}).get('cookies', []),
            'cookie_type': preprocess_info.get('llm_context', {}).get('cookie_deserialization_type', 'unknown')
        }
        
        # 🔥 构建可用工具列表
        tools_section = ""
        if available_tools:
            tools_section = "\n## 🛠️ 环境中可用的工具\n"
            tools_section += "请在计划中**只使用以下工具**，不要指定不存在的工具：\n\n"
            
            # 🔥 available_tools现在的格式: [{'name': '...', 'description': '...'}, ...]
            for tool in available_tools:
                tool_name = tool.get('name', '未知工具')
                tool_desc = tool.get('description', '无描述')
                
                # 格式化工具描述，保留参数信息
                if '\n参数:' in tool_desc:
                    # 保留完整的工具描述
                    tools_section += f"- **{tool_name}**: {tool_desc}\n"
                else:
                    # 简单描述
                    tools_section += f"- **{tool_name}**: {tool_desc}\n"
            
            tools_section += "\n"  # 添加空行分隔
        
        return f"""# 任务：生成简洁高效的渗透测试任务计划

⚠️ **重要原则：**
1. **简洁优先** - 初始计划只需3-5个核心任务，不要过度规划
2. **聚焦高价值** - 优先验证预处理发现的漏洞
3. **动态扩展** - 执行过程中根据结果动态添加后续任务

## 目标信息
- URL: {target_url}
- 模式: {self.mode_manager.mode.value.upper()}
- 最大轮数限制: {max_rounds}
{tools_section}
## 预处理收集的信息（关键摘要）
```json
{json.dumps(key_info, ensure_ascii=False, indent=2)}
```

## 要求
请生成一个**简洁高效**的任务计划（3-5个核心任务），以JSON格式返回。

**❌ 不要做：**
- 不要一次性生成所有可能的任务
- 不要为每个预处理发现都生成任务
- 不要生成超过5个初始任务

**✅ 应该做：**
- 只生成最高优先级的3-5个核心任务
- 每个任务应该是独立可执行的
- 后续任务会根据执行结果动态添加

**JSON格式：**

1. **因果任务依赖关系**：明确任务之间的依赖关系
2. **优先级排序**：根据已知信息确定优先级
3. **工具选择**：**只从上面的可用工具列表中选择**
4. **预期结果**：定义每个任务的成功标准

Please以JSON格式返回，结构如下：
```json
{{
  "phases": ["reconnaissance", "exploitation", "post_exploitation"],
  "tasks": [
    {{
      "id": "task_001",
      "name": "HTTP请求测试",
      "description": "使用execute_python工具获取页面信息",
      "phase": "reconnaissance",
      "priority": "high",
      "dependencies": [],
      "estimated_rounds": 1,
      "tools_required": ["execute_python"],
      "expected_outcomes": ["页面响应", "表单信息"]
    }}
  ],
  "total_estimated_rounds": 15,
  "strategy_notes": "首先进行信息收集..."
}}
```

**重要**：
- 🛑 **tools_required必须从上面的可用工具列表中选择，不要编造不存在的工具！**
- 确保任务之间的依赖关系合理
- 根据{self.mode_manager.mode.value}模式调整策略（CTF=激进快速，RealWorld=隐蔽全面）
- 合理分配轮数，总和不超过{max_rounds}
"""
    
    def _build_adjustment_prompt(self,
                                plan: TaskPlan,
                                current_round: int,
                                execution_results: List[Dict[str, Any]],
                                discoveries: List[Dict[str, Any]],
                                tool_calls: Optional[List[Dict]] = None,  # 🔥 当前轮工具调用
                                tool_results: Optional[List[Dict]] = None,  # 🔥 当前轮工具结果
                                recent_conversations: Optional[List[Dict]] = None,  # 🔥 最近3轮完整对话
                                recent_tool_results_all: Optional[List[Dict]] = None  # 🔥 最近3轮工具结果
                                ) -> str:
        """构建计划调整提示词（🔥 包含任务完成度评估）"""
        # 获取当前计划状态
        completed_tasks = [t for t in plan.tasks if t.status == TaskStatus.COMPLETED]
        pending_tasks = [t for t in plan.tasks if t.status in [TaskStatus.PENDING, TaskStatus.READY, TaskStatus.BLOCKED]]
        in_progress_tasks = [t for t in plan.tasks if t.status == TaskStatus.IN_PROGRESS]
        
        # 🔥🔥🔥 新增：构建任务完成度评估部分
        task_evaluation_section = ""
        if tool_calls and tool_results:
            # 获取工具执行信息
            tool_names = [tc.get('function', {}).get('name', 'unknown') for tc in tool_calls]
            # 🔥🔥🔥 不截断! Planner需要看到完整的工具输出才能准确评估任务完成度
            results_summary = "\n".join([
                f"- {tr.get('tool_name', 'unknown')}:\n{str(tr.get('result', ''))}"
                for tr in tool_results
            ])
            
            # 需要评估的任务（in_progress + 最近的pending）
            tasks_to_evaluate = in_progress_tasks[:3]  # 最多3个
            
            tasks_info = ""
            for i, task in enumerate(tasks_to_evaluate, 1):
                tasks_info += f"""
{i}. **{task.name}** (ID: {task.id})
   - 目标: {task.description}
   - 期望结果: {', '.join(task.expected_outcomes) if task.expected_outcomes else '未指定'}
   - 当前状态: {task.status}
"""
            
            if tasks_info:  # 只有当有任务需要评估时才添加这一部分
                task_evaluation_section = f"""
## 📊 任务完成度评估

### 本轮执行的工具：
{', '.join(tool_names)}

### 工具执行结果：
{results_summary}

### 需要评估的任务：
{tasks_info}

**判断标准**：
- ✅ **SQL注入类任务**：登录成功 = SQL注入成功 → 完成
- ✅ **信息收集类任务**：获取了有价值信息 → 完成
- ✅ **RCE类任务**：执行了命令并获得结果 → 完成
- ❌ **真正未完成**：工具执行失败、结果完全不相关、没有任何实际成果

"""
        
        # 🔥 格式化最近3轮完整对话历史
        conversations_section = ""
        if recent_conversations:
            # 使用本地格式化方法
            conversations_formatted = ""
            for conv in recent_conversations:
                messages = conv.get('messages', [])
                for msg in messages:
                    role = msg.get('role', 'unknown')
                    if role == 'user':
                        conversations_formatted += f"\n👤 **User:** {msg.get('content', '')}\n"
                    elif role == 'assistant':
                        conversations_formatted += f"\n🤖 **Worker:** {msg.get('content', '')}\n"
                        if msg.get('tool_calls'):
                            conversations_formatted += "\n🛠️ **调用工具:**\n"
                            for tc in msg['tool_calls']:
                                tool_name = tc.get('function', {}).get('name', '?')
                                conversations_formatted += f"  - {tool_name}\n"
                    elif role == 'tool':
                        tool_name = msg.get('name', '?')
                        # 🔥🔥🔥 不截断! Planner需要看到完整的工具结果才能准确评估任务完成度
                        content = str(msg.get('content', ''))  # 不截断
                        conversations_formatted += f"\n⚙️ **工具结果 ({tool_name}):** {content}\n"

            conversations_section = f"""
## 🔥🔥🔥 最近3轮完整对话历史（关键！）
**必须仔细阅读Worker的对话，了解实际执行情况！**

{conversations_formatted}

"""

        return f"""# 任务：综合评估与计划调整

🔥 **你需要完成两件事：**
1. **评估任务完成度**：根据工具执行结果，判断哪些任务已完成
2. **调整计划**：根据执行结果和新发现，决定是否需要调整计划

{conversations_section}
{task_evaluation_section}
## 当前进度
- 轮次: {current_round}/{plan.total_estimated_rounds}
- 已完成任务: {len(completed_tasks)}/{len(plan.tasks)}
- 待执行任务: {len(pending_tasks)}

## 最近执行结果
```json
{json.dumps(execution_results[-5:], ensure_ascii=False, indent=2)}
```

## 新发现
```json
{json.dumps(discoveries, ensure_ascii=False, indent=2)}
```

## 当前计划
```json
{json.dumps(plan.to_dict(), ensure_ascii=False, indent=2)}
```

## 要求
请评估是否需要调整计划，并返回JSON格式。

**🔥 核心策略：发现驱动（Discovery-Driven Planning）**

**调整原则：**
1. **新攻击面优先** - 发现新的可利用点时（路径/功能/参数/凭据），立即创建探索任务
2. **广度优于深度** - 有新发现时，优先探索所有攻击面，而不是深入单一漏洞
3. **价值动态排序** - 根据实时信息重新评估任务价值，调整优先级
4. **因果链延续** - 基于执行结果生成下一步任务，保持攻击链连贯性

**决策思路：**
- **分析执行结果**：识别关键信息（新URL、凭据、漏洞特征等）
- **评估成功/失败**：判断测试是否有效，是否开启新路径
- **🔥 成功向前**：漏洞确认后，跳过验证任务，直接生成深度利用任务
- **🔥 失败放弃**：测试无效时，跳过后续相关任务，避免浪费资源
- **优先级重排**：根据新信息调整任务优先级
- **生成新任务**：基于发现创建具体可执行的下一步任务

**返回格式（必须严格遵守）：**
```json
{{
  "task_completion": {{
    "completed_tasks": [
      {{
        "task_id": "task_001",
        "task_name": "任务名称",
        "completed": true,
        "actual_outcomes": ["成果1", "成果2"],
        "reason": "完成原因"
      }}
    ]
  }},
  "plan_adjustment": {{
    "needs_adjustment": true,
    "reason": "简洁说明调整的核心原因",
    "adjustments": [
    // 🔥🔥🔥 方式1: 整体重新规划（发现重大突破时使用）
    {{
      "type": "replace_plan",
      "new_tasks": [
        {{
          "id": "task_xxx",
          "name": "任务名称",
          "description": "具体描述",
          "phase": "exploitation/post_exploitation",
          "priority": "critical/high/medium/low",
          "dependencies": [],
          "estimated_rounds": 1,
          "tools_required": ["工具名称"],
          "expected_outcomes": ["期望结果"]
        }}
      ],
      "reason": "为什么需要整体重新规划"
    }},
    
    // 方式2: 局部调整（小改动时使用）
    {{
      "type": "add_task",
      "task": {{
        "id": "task_xxx",
        "name": "任务名称",
        "description": "具体描述",
        "phase": "exploitation",
        "priority": "high",
        "dependencies": [],
        "estimated_rounds": 1,
        "tools_required": ["工具名称"],
        "expected_outcomes": ["期望结果"]
      }},
      "reason": "添加理由"
    }},
    {{
      "type": "skip_task",
      "task_id": "task_xxx",
      "reason": "跳过理由"
    }},
    {{
      "type": "update_priority",
      "task_id": "task_xxx",
      "new_priority": "critical",
      "reason": "提升理由"
    }}
  ],
  "strategy_update": "一句话概括策略变化"
  }}
}}
```

**⚠️ 重要提醒：**
- 🔥 **task_completion**: 必须根据工具执行结果判断任务是否完成，即使没有任务完成也要返回空数组 `[]`
- 🔥 **plan_adjustment.needs_adjustment**: 如果为 `true`，则 `adjustments` 数组不能为空！
- 🔥 **必须提供至少一个调整项（replace_plan/add_task/skip_task/update_priority）**
- 🔥 **如果不需要任何调整，直接返回 `needs_adjustment: false`**

**🔥 调整类型说明：**
1. **replace_plan** - 整体重新规划，删除所有旧任务（保留已完成），用新任务列表替换
2. **add_task** - 添加单个新任务到现有计划
3. **skip_task** - 跳过某个任务
4. **update_priority** - 调整任务优先级
5. **add_dependency** - 添加任务依赖
6. **update_phase** - 切换阶段

**💡 何时使用replace_plan：**
- ✅ 发现重大突破，旧计划大部分已过时
- ✅ 攻击方向完全改变
- ✅ 获得新的关键访问权限或信息
- ✅ 需要重新设计3个以上的任务时
- ❌ 只是调整1-2个任务 → 用add_task/skip_task即可

**💡 何时使用add_task/skip_task：**
- ✅ 发现新的攻击点，需要添加测试任务
- ✅ 某个任务已无意义，直接跳过
- ✅ 局部优化现有计划
- ❌ 需要大规模重组 → 用replace_plan
"""
    
    def _get_planner_system_prompt(self) -> str:
        """获取计划生成的系统提示词 - 像人类黑客一样制定计划"""
        # 🔥 根据模式调整目标
        mode = self.mode_manager.mode.value
        
        if mode == "ctf":
            goal_desc = f"""🏆 **CTF模式目标：**
- 主要目标：找到真实的FLAG（必须是目标系统实际输出的，不是示例或模板）
- 成功标准：获取可验证的有效FLAG内容 例如flag{{xxxx-uuid5}},xxx{{大小写字母+数字}}
- 攻击风格：快速、直接、不担心隐蔽

⚠️ **重要：严格验证FLAG真实性**
- 必须是从文件、数据库、HTTP响应等实际获取的数据
- 警惕示例性文本（如test_flag、example_flag等）
- 确保FLAG格式符合目标平台要求"""
        else:  # realworld
            goal_desc = """🎯 **RealWorld模式目标：**
- 主要目标：获取系统实际控制权
  - Shell访问（执行系统命令）
  - Webshell上传
  - 数据库权限
  - 敏感文件读取（/etc/passwd, .env, config.php）
  - API密钥、数据库凭据
- 成功标准：证明漏洞存在并能被利用
- 攻击风格：专业、隐蔽、有证据
- ⚠️ 不是CTF，不要找FLAG！"""
        
        return f"""🧠 你是一个顶级渗透测试专家，即将对一个目标进行渗透测试。

{goal_desc}

💡 **人类黑客的思考方式：**

1. **先看看有什么** - 快速浏览预处理信息
   - 有什么明显的漏洞？
   - 有什么可疑的功能？
   - 有什么有价值的线索？

2. **想一想从哪入手** - 选择突破口
   - 哪个漏洞最可能成功？
   - 哪个路径最接近FLAG？
   - 哪个方法最省时间？

3. **规划前几步** - 不要过度计划
   - 只设计最初头3-5个步骤
   - 后面的事边做边看
   - 根据结果动态调整

4. **保持灵活** - 计划只是参考
   - 不是每个预处理发现都要测
   - 不是每个漏洞都要验证
   - 只抓最有价值的

⚡ **计划原则：**

✅ **应该做：**
- 优先测试预处理中发现的明显漏洞
- 从最可能成功的开始
- 每个任务都要有明确目标
- 把复杂任务拆分成小步骤
- 使用execute_python手动测试，确认后再用工具

❌ **不要做：**
- 不要一次性生成所有可能的任务
- 不要为每个预处理发现都生成任务
- 不要生成超过5个初始任务
- 不要过度细化步骤
- 不要固定逆序，优先级可动态调整

📝 **任务设计指南：**

每个任务应该：
- 有一个清晰的目标（要达到什么效果）
- 有具体的执行方法（用什么工具）
- 有明确的成功标准（怎么知道完成了）

优先级分配：
- **CRITICAL**: 直接能拿到FLAG的（已知后台、确认的shell等）
- **HIGH**: 高成功率的漏洞利用（SQL注入、文件上传等）
- **MEDIUM**: 需要探索的方向（新功能、未测路径等）
- **LOW**: 信息收集类任务

🔄 **依赖关系：**
只在真正必须的时候设置依赖：
- 后续任务必须用到前面的结果
- 例：必须先登录才能访问后台

不需要依赖：
- 多个独立的漏洞测试可以并行
- 优先级已经说明了顺序

📊 **输出格式：**
``json
{
  "phases": ["reconnaissance", "exploitation", "post_exploitation"],
  "tasks": [
    {
      "id": "task_001",
      "name": "简洁的任务名称",
      "description": "具体要做什么，怎么做",
      "phase": "exploitation",
      "priority": "high",
      "dependencies": [],
      "estimated_rounds": 1,
      "tools_required": ["execute_python"],
      "expected_outcomes": ["期望的结果1", "期望的结果2"]
    }
  ],
  "total_estimated_rounds": 10,
  "strategy_notes": "整体策略说明，像人类一样的自然语言"
}
```

⚠️ **记住：**
- 你是专家，不是执行机器
- 用直觉和经验指导，不用模板
- 计划要简洁、灵活、目标明确
- 目标只有一个：高效地找到FLAG
"""

    
    def _get_adjuster_system_prompt(self) -> str:
        """获取计划调整的系统提示词 - 完全自主决策，仿人类思维"""
        # 🔥 根据模式调整目标描述
        mode = self.mode_manager.mode.value
        
        if mode == "ctf":
            goal_text = "距离获取真实FLAG还有多远"
            final_goal = "高效地找到真实的目标FLAG（非示例）"
        else:  # realworld
            goal_text = "距离获得系统控制权还有多远（Shell、敏感文件、数据库等）"
            final_goal = "证明漏洞存在并能被利用，不是找FLAG"
        
        return f"""🧠 你是一个顶级渗透测试专家，拥有丰富的实战经验。

🎯 **你的核心使命：**
像人类黑客一样思考，根据实际情况灵活调整攻击策略。

💡 **人类黑客的思维模式：**

1. **直觉感知** - 快速抓取关键信息
   - 发现新的攻击面？立即分析价值
   - 看到成功的测试结果？考虑深入利用
   - 遇到失败？**首先考虑绕过，而不是放弃**
     - 🔥 **文件上传/注入漏洞受阻 → 尝试3-5种绕过技术**
     - 🔥 **WAF拦截 → 测试编码/混淆/特殊字符**
     - 🔥 **只有明确证实漏洞不存在才放弃**

2. **目标导向** - 始终朝着目标前进
   - 哪个路径最可能实现目标？
   - 当前的发现如何帮助我接近目标？
   - 这个任务还有意义吗？还是应该转向别的方向？
   - 我现在{goal_text}？

3. **经验驱动** - 从结果中学习
   - SQL注入成功？该提取数据了
   - 🔥 **漏洞测试失败？分析失败原因，调整payload继续测试**
     - 过滤"<?" → 测试短标签、<script language="php">、.htaccess
     - WAF拦截 → 测试编码、大小写变形、注释符
   - 🔥 **只有尝试3-5种绕过后仍失败，才考虑放弃**
   - 发现后台？优先级最高，其他都往后放

4. **灵活应变** - 不固守原计划
   - 计划只是参考，不是铁律
   - 发现更好的机会？立即抓住
   - 原计划不可行？🔥 **首先尝试绕过，再考虑放弃**
   - 🔥 **关键原则：深度优先于广度，绕过优先于放弃**

5. **效率优先** - 不做无用功
   - 已经确认的事不要重复验证
   - 🔥 **漏洞测试受阻 ≠ 明显无效，应深度绕过**
   - 🔥 **只有尝试3-5种绕过后仍失败，才是“明显无效”**
   - 把时间花在刀刽上

⚡ **你的决策权力：**
- ✅ 决定是否需要调整计划（没有规则限制，完全自主）
- ✅ 根据实际情况调整任务优先级
- ✅ 跳过无意义的任务
- ✅ 添加新的高价值任务
- ✅ 改变整体策略方向

💭 **决策流程（完全自然，不是模板）：**

第一步：看看发生了什么
- 最近执行了什么工具？结果如何？
- 有没有新发现？（漏洞、凭据、路径、FLAG线索）
- 当前任务进展如何？

第二步：思考一下
- 这些信息对我有什么帮助？
- 我现在距离目标还有多远？
- 有没有更好的机会出现？
- 当前计划还合理吗？

第三步：做出决定
- 如果当前计划很好，就继续
- 如果有更重要的事，就调整优先级
- 如果发现新机会，就添加新任务
- 如果路不通，就跳过无效任务

🚨 **关键原则：**
1. **无需每次都调整** - 只有当真的需要时才调
2. **不要过度规划** - 一次只设计下1-3步
3. **以结果为导向** - 看实际效果，不看理论
4. 🔥🔥🔥 **深度优先于广度** - 漏洞受阻时，**尝试3-5种绕过技术再放弃**
   - 🚨 **禁止尝试1次就skip_task！**
   - ✅ 文件上传/SQL注入/XSS/命令注入 → 必须测试3-5种变种
   - ✅ 如果Payload Master已经提供了变种建议，**必须逐个测试**
   - ❌ 不要因为1-2次失败就转向其他漏洞
5. **抽象思维** - 看到本质，不被表象迷惑

📊 **输出要求（严格遵守）：**

⚠️ **必须只输出纯JSON，不要任何其他内容！**
- ❌ 不要输出思考过程
- ❌ 不要输出解释文字
- ❌ 不要使用Markdown代码块
- ✅ 直接输出JSON对象

正确的输出格式示例：
{{
  "needs_adjustment": true,
  "reason": "简洁说明为什么需要调整",
  "adjustments": [
    {{
      "type": "skip_task",
      "task_id": "task_005",
      "reason": "跳过理由"
    }}
  ],
  "strategy_update": "整体策略调整说明"
}}

⚠️ **记住：**
- 你是专家，不是机器人
- 用人类的直觉和经验去决策
- 没有固定模式，每次都是新的分析
- 目标只有一个：{final_goal}
- **输出必须是纯JSON，不要任何额外内容！**
"""

    
    def _parse_llm_plan(self, 
                       plan_data: Dict[str, Any],
                       target_url: str,
                       mode: str) -> TaskPlan:
        """解析LLM生成的计划数据"""
        tasks = []
        for task_data in plan_data.get('tasks', []):
            task = Task(
                id=task_data.get('id', f"task_{len(tasks)+1:03d}"),
                name=task_data['name'],
                description=task_data['description'],
                phase=task_data.get('phase', 'reconnaissance'),
                priority=TaskPriority(task_data.get('priority', 'medium')),
                dependencies=task_data.get('dependencies', []),
                estimated_rounds=task_data.get('estimated_rounds', 1),
                tools_required=task_data.get('tools_required', []),
                expected_outcomes=task_data.get('expected_outcomes', []),
                metadata=task_data.get('metadata', {})
            )
            tasks.append(task)
        
        plan = TaskPlan(
            id=f"plan_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            target_url=target_url,
            mode=mode,
            tasks=tasks,
            phases=plan_data.get('phases', ["reconnaissance", "exploitation", "post_exploitation"]),
            total_estimated_rounds=plan_data.get('total_estimated_rounds', sum(t.estimated_rounds for t in tasks)),
            metadata={
                'strategy_notes': plan_data.get('strategy_notes', ''),
                'llm_confidence': plan_data.get('confidence', 0.8)
            }
        )
        
        return plan
    
    def _apply_adjustments(self, adjustment_data: Dict[str, Any]) -> List[str]:
        """应用LLM提出的调整（带容错处理）"""
        changes = []
        
        # 🔥🔥🔥 关键调试：打印接收到的调整数据
        log_message('info', f'🔧 _apply_adjustments 被调用')
        log_message('info', f'   - needs_adjustment: {adjustment_data.get("needs_adjustment")}')
        log_message('info', f'   - adjustments 数量: {len(adjustment_data.get("adjustments", []))}')
        if adjustment_data.get('adjustments'):
            for i, adj in enumerate(adjustment_data.get('adjustments', []), 1):
                log_message('info', f'   - 调整{i}: type={adj.get("type")}, reason={adj.get("reason", "")[:50]}...')
        
        # 🔥🔥🔥 记录决策历史（供 Meta 监督使用）
        if adjustment_data.get('adjustments'):
            self.decision_history.append({
                'reason': adjustment_data.get('reason', ''),
                'adjustments': adjustment_data.get('adjustments', []),
                'timestamp': datetime.now().isoformat()
            })
            # 只保留最近 10 个决策
            if len(self.decision_history) > 10:
                self.decision_history = self.decision_history[-10:]
        
        # 🔥🔥🔥 记录原始输入，便于调试
        log_message('debug', f'🔍 计划调整原始数据: {json.dumps(adjustment_data, ensure_ascii=False, indent=2)}')
        
        adjustments = adjustment_data.get('adjustments', [])
        if not adjustments:
            # 🔥🔥🔥 关键修复：即使adjustments为空，也要检查needs_adjustment字段
            if adjustment_data.get('needs_adjustment', False):
                log_message('warning', '⚠️ LLM说需要调整(needs_adjustment=true)，但adjustments数组为空！这是LLM的输出错误。')
                log_message('warning', f'   原因: {adjustment_data.get("reason", "未说明")}')
                log_message('warning', '   已忽略此次调整，继续执行原计划')
            else:
                log_message('info', 'ℹ️ 没有需要应用的调整')
            return changes
        
        log_message('info', f'🔧 开始应用 {len(adjustments)} 个调整...')
        
        for i, adj in enumerate(adjustments, 1):
            adj_type = adj.get('type')
            
            log_message('info', f'🔍 处理第 {i} 个调整: type={adj_type}')
            
            if not adj_type:
                log_message('warning', f'⚠️ 调整{i}缺少type字段，跳过: {adj}')
                continue
            
            try:
                # 🔥🔥🔥 新增: 整体重新规划
                if adj_type == 'replace_plan':
                    log_message('info', f'🔥 检测到 replace_plan 类型，开始处理...')
                    
                    if 'new_tasks' not in adj:
                        log_message('warning', f'⚠️ replace_plan缺少new_tasks字段，跳过: {adj}')
                        continue
                    
                    try:
                        new_tasks_data = adj['new_tasks']
                        log_message('info', f'📊 解析到 {len(new_tasks_data)} 个新任务')
                        
                        # 🔥 打印第一个任务的详细信息
                        if new_tasks_data:
                            log_message('debug', f'🔍 第一个新任务: {json.dumps(new_tasks_data[0], ensure_ascii=False)}')
                        
                        new_tasks = [Task.from_dict(task_data) for task_data in new_tasks_data]
                        log_message('info', f'✅ 成功创建 {len(new_tasks)} 个 Task 对象')
                        
                        # 🔥 保留已完成的任务（作为历史记录）
                        completed_tasks = [t for t in self.current_plan.tasks if t.status == TaskStatus.COMPLETED]
                        
                        # 🔥 替换为新任务列表
                        self.current_plan.tasks = completed_tasks + new_tasks
                        
                        # 🔥🔥🔥 关键修复：重新计算阶段和预估轮数
                        all_phases = set()
                        total_rounds = 0
                        for task in self.current_plan.tasks:
                            all_phases.add(task.phase)
                            if task.status != TaskStatus.COMPLETED:
                                total_rounds += task.estimated_rounds
                        
                        # 更新阶段列表（保持顺序：reconnaissance -> exploitation -> post_exploitation）
                        phase_order = ['reconnaissance', 'exploitation', 'post_exploitation']
                        self.current_plan.phases = [p for p in phase_order if p in all_phases]
                        
                        # 如果有新任务，设置当前阶段为新任务的第一个阶段
                        if new_tasks:
                            self.current_plan.current_phase = new_tasks[0].phase
                        
                        # 更新预估总轮数
                        self.current_plan.total_estimated_rounds = total_rounds
                        
                        reason = adj.get('reason', '未说明')
                        changes.append(f"整体重新规划: 保留{len(completed_tasks)}个已完成任务，添加{len(new_tasks)}个新任务，预估{total_rounds}轮 - {reason}")
                        log_message('info', f'🔥 {changes[-1]}')
                        log_message('info', f'   📊 新计划: 总任务数={len(self.current_plan.tasks)}, 阶段={self.current_plan.phases}, 当前阶段={self.current_plan.current_phase}')
                        
                        # 🔥🔥🔥 关键验证：立即检查修改是否成功
                        log_message('debug', f'🔍 验证 replace_plan 执行结果:')
                        log_message('debug', f'   - self.current_plan.tasks 长度: {len(self.current_plan.tasks)}')
                        log_message('debug', f'   - self.current_plan.phases: {self.current_plan.phases}')
                        log_message('debug', f'   - self.current_plan.current_phase: {self.current_plan.current_phase}')
                        log_message('debug', f'   - self.current_plan.total_estimated_rounds: {self.current_plan.total_estimated_rounds}')
                        log_message('debug', f'   - 任务列表: {", ".join([f"{t.id}({t.name})" for t in self.current_plan.tasks])}')
                        
                        # 🔥 重新规划时直接跳出，不再处理其他调整
                        break
                    except Exception as e:
                        log_message('error', f'❌ 整体重新规划失败: {e}')
                        import traceback
                        log_message('error', traceback.format_exc())
                        continue
                
                elif adj_type == 'add_task':
                    # 🔥🔥🔥 恢复add_task功能 - 基于新发现添加任务
                    if 'task' not in adj:
                        log_message('warning', f'⚠️ add_task调整缺少task字段，跳过: {adj}')
                        continue
                    
                    try:
                        task_data = adj['task']
                        task = Task.from_dict(task_data)
                        
                        # 🔥 检查是否已存在相同ID的任务
                        existing_task = self._find_task(task.id)
                        if existing_task:
                            # 覆盖老任务
                            idx = self.current_plan.tasks.index(existing_task)
                            self.current_plan.tasks[idx] = task
                            reason = adj.get('reason', '未说明')
                            changes.append(f"更新任务: {task.name} (覆盖老任务) - {reason}")
                            log_message('info', f'✅ {changes[-1]}')
                        else:
                            # 添加新任务
                            self.current_plan.tasks.append(task)
                            reason = adj.get('reason', '未说明')
                            changes.append(f"添加新任务: {task.name} - {reason}")
                            log_message('info', f'✅ {changes[-1]}')
                    except Exception as e:
                        log_message('error', f'❌ 添加任务失败: {e}, 任务数据: {adj.get("task")}')
                        continue
                
                elif adj_type == 'update_priority':
                    task_id = adj.get('task_id')
                    if not task_id:
                        log_message('warning', f'⚠️ update_priority缺少task_id，跳过: {adj}')
                        continue
                    
                    task = self._find_task(task_id)
                    if not task:
                        log_message('warning', f'⚠️ 未找到任务 {task_id}，跳过')
                        continue
                    
                    old_priority = task.priority
                    new_priority_str = adj.get('new_priority') or adj.get('priority')
                    if not new_priority_str:
                        log_message('warning', f'⚠️ update_priority缺少new_priority，跳过: {adj}')
                        continue
                    
                    try:
                        task.priority = TaskPriority(new_priority_str)
                        reason = adj.get('reason', '未说明')
                        changes.append(f"更新优先级: {task.name} ({old_priority.value} → {task.priority.value}) - {reason}")
                        log_message('info', f'✅ {changes[-1]}')
                    except ValueError as e:
                        log_message('warning', f'⚠️ 无效的优先级: {new_priority_str}, 错误: {e}')
                
                elif adj_type == 'skip_task':
                    task_id = adj.get('task_id')
                    if not task_id:
                        log_message('warning', f'⚠️ skip_task缺少task_id，跳过: {adj}')
                        continue
                    
                    task = self._find_task(task_id)
                    if not task:
                        log_message('warning', f'⚠️ 未找到任务 {task_id}，跳过')
                        continue
                    
                    task.status = TaskStatus.SKIPPED
                    reason = adj.get('reason', '未说明')
                    task.metadata['skip_reason'] = reason
                    changes.append(f"跳过任务: {task.name} - {reason}")
                    log_message('info', f'✅ {changes[-1]}')
                
                elif adj_type == 'add_dependency':
                    task_id = adj.get('task_id')
                    if not task_id:
                        log_message('warning', f'⚠️ add_dependency缺少task_id，跳过: {adj}')
                        continue
                    
                    task = self._find_task(task_id)
                    if not task:
                        log_message('warning', f'⚠️ 未找到任务 {task_id}，跳过')
                        continue
                    
                    dep_id = adj.get('dependency') or adj.get('depends_on')
                    if not dep_id:
                        log_message('warning', f'⚠️ add_dependency缺少dependency，跳过: {adj}')
                        continue
                    
                    task.dependencies.append(dep_id)
                    reason = adj.get('reason', '未说明')
                    changes.append(f"添加依赖: {task.name} 依赖于 {dep_id} - {reason}")
                    log_message('info', f'✅ {changes[-1]}')
                
                elif adj_type == 'update_phase':
                    new_phase = adj.get('new_phase') or adj.get('phase')
                    if not new_phase:
                        log_message('warning', f'⚠️ update_phase缺少new_phase，跳过: {adj}')
                        continue
                    
                    self.current_plan.current_phase = new_phase
                    reason = adj.get('reason', '未说明')
                    changes.append(f"切换阶段: {new_phase} - {reason}")
                    log_message('info', f'✅ {changes[-1]}')
                
                else:
                    log_message('warning', f'⚠️ 未知的调整类型: {adj_type}，跳过: {adj}')
            
            except Exception as e:
                log_message('error', f'❌ 应用调整{i}失败: {e}, 调整内容: {adj}')
                import traceback
                log_message('error', traceback.format_exc())
                continue
        
        if changes:
            self.current_plan.updated_at = datetime.now().isoformat()
            log_message('info', f'✅ 成功应用 {len(changes)} 个调整')
            
            # 🔥🔥🔥 自动检测阶段切换
            self._auto_update_phase()
        else:
            log_message('info', 'ℹ️ 没有有效的调整被应用')
        
        return changes
    
    def _auto_update_phase(self):
        """🔥 自动更新阶段：如果当前阶段的所有任务都完成了，切换到下一阶段"""
        if not self.current_plan:
            return
        
        current_phase = self.current_plan.current_phase
        phases = self.current_plan.phases
        
        # 获取当前阶段的所有任务
        current_phase_tasks = [
            t for t in self.current_plan.tasks 
            if t.phase == current_phase
        ]
        
        if not current_phase_tasks:
            return
        
        # 检查当前阶段是否全部完成
        all_completed = all(
            t.status in [TaskStatus.COMPLETED, TaskStatus.SKIPPED] 
            for t in current_phase_tasks
        )
        
        if all_completed:
            # 查找下一个阶段
            try:
                current_index = phases.index(current_phase)
                if current_index < len(phases) - 1:
                    next_phase = phases[current_index + 1]
                    log_message('info', f'🔄 当前阶段 {current_phase} 的所有任务已完成，切换到 {next_phase}')
                    self.current_plan.current_phase = next_phase
                else:
                    log_message('info', f'✅ 所有阶段已完成！')
            except ValueError:
                pass
    
    def _are_dependencies_met(self, task: Task) -> bool:
        """检查任务依赖是否满足"""
        if not task.dependencies:
            return True
        
        for dep_id in task.dependencies:
            dep_task = self._find_task(dep_id)
            if not dep_task or dep_task.status != TaskStatus.COMPLETED:
                return False
        return True
    
    def _find_task(self, task_id: str) -> Optional[Task]:
        """查找任务"""
        if not self.current_plan:
            return None
        for task in self.current_plan.tasks:
            if task.id == task_id:
                return task
        return None
    
    def _priority_value(self, priority: TaskPriority) -> int:
        """优先级数值映射(越小越优先)"""
        mapping = {
            TaskPriority.CRITICAL: 0,
            TaskPriority.HIGH: 1,
            TaskPriority.MEDIUM: 2,
            TaskPriority.LOW: 3
        }
        return mapping.get(priority, 99)
    
    def _phase_value(self, phase: str) -> int:
        """阶段数值映射"""
        mapping = {
            'reconnaissance': 0,
            'exploitation': 1,
            'post_exploitation': 2
        }
        return mapping.get(phase, 99)
    
    def _create_fallback_plan(self, target_url: str, max_rounds: int, preprocess_info: Dict[str, Any] = None) -> TaskPlan:
        """创建默认后备计划 - 🔥 基于预处理信息生成，不是固定模板"""
        log_message('warning', '使用基于预处理的后备计划')
        
        default_tasks = []
        task_id_counter = 1
        
        # 🔥 如果有预处理信息，基于它生成任务
        if preprocess_info:
            # 1. 基础信息收集任务
            default_tasks.append(Task(
                id=f"task_{task_id_counter:03d}",
                name="目标基础信息收集",
                description=f"收集 {target_url} 的基础信息、表单、参数",
                phase="reconnaissance",
                priority=TaskPriority.HIGH,
                estimated_rounds=1,
                tools_required=["execute_python"],
                expected_outcomes=["页面结构", "表单字段"]
            ))
            task_id_counter += 1
            
            # 2. 根据预处理发现的漏洞生成任务
            matches = preprocess_info.get('matches', [])
            structured_vulns = preprocess_info.get('structured_vulnerabilities', [])
            
            # 优先使用结构化漏洞
            vulns_to_test = structured_vulns if structured_vulns else matches
            
            for vuln in vulns_to_test[:5]:  # 最多5个漏洞
                vuln_type = vuln.get('vulnerability_type') or vuln.get('type', 'Unknown')
                severity = vuln.get('severity', 'MEDIUM')

                # 🔥 修复：confidence可能是dict（structured_vulns）或float（matches）
                confidence_raw = vuln.get('confidence', {})
                if isinstance(confidence_raw, dict):
                    confidence = confidence_raw.get('level', 'medium')
                elif isinstance(confidence_raw, (int, float)):
                    # 将float置信度转换为level
                    if confidence_raw >= 0.8:
                        confidence = 'HIGH'
                    elif confidence_raw >= 0.6:
                        confidence = 'MEDIUM'
                    else:
                        confidence = 'LOW'
                else:
                    confidence = 'medium'
                
                # 根据严重程度设置优先级
                if severity == 'CRITICAL':
                    priority = TaskPriority.CRITICAL
                    est_rounds = 3
                elif severity == 'HIGH':
                    priority = TaskPriority.HIGH  
                    est_rounds = 2
                else:
                    priority = TaskPriority.MEDIUM
                    est_rounds = 1
                
                default_tasks.append(Task(
                    id=f"task_{task_id_counter:03d}",
                    name=f"{vuln_type}漏洞测试",
                    description=f"测试 {vuln_type} 漏洞 (严重程度: {severity}, 置信度: {confidence})",
                    phase="exploitation",
                    priority=priority,
                    dependencies=[f"task_001"],
                    estimated_rounds=est_rounds,
                    tools_required=self._get_tools_for_vuln(vuln_type),
                    expected_outcomes=["漏洞验证", "利用成功"]
                ))
                task_id_counter += 1
            
            # 3. 添加后渗透任务
            if len(default_tasks) > 1:  # 如果有漏洞任务
                # 🔥 根据模式设置不同的期望结果
                if self.mode_manager.mode.value == 'realworld':
                    expected_outcomes = ["敏感数据", "数据库访问", "系统控制权"]
                else:  # CTF模式
                    expected_outcomes = ["FLAG", "敏感数据", "Shell访问"]
                
                default_tasks.append(Task(
                    id=f"task_{task_id_counter:03d}",
                    name="深度利用与数据提取",
                    description="利用发现的漏洞获取敏感数据或系统访问权限",
                    phase="post_exploitation",
                    priority=TaskPriority.CRITICAL,
                    dependencies=[f"task_{task_id_counter-1:03d}"],  # 依赖最后一个漏洞任务
                    estimated_rounds=3,
                    tools_required=["execute_python", "run_command"],
                    expected_outcomes=expected_outcomes
                ))
        else:
            # 没有预处理信息，使用最基础的任务
            default_tasks = [
                Task(
                    id="task_001",
                    name="目标探测",
                    description="探测目标基本信息",
                    phase="reconnaissance",
                    priority=TaskPriority.HIGH,
                    estimated_rounds=2,
                    tools_required=["execute_python"],
                    expected_outcomes=["HTTP响应", "服务器信息"]
                ),
                Task(
                    id="task_002",
                    name="漏洞扫描",
                    description="扫描常见漏洞",
                    phase="reconnaissance",
                    priority=TaskPriority.HIGH,
                    dependencies=["task_001"],
                    estimated_rounds=3,
                    tools_required=["nuclei"],
                    expected_outcomes=["漏洞列表"]
                ),
                Task(
                    id="task_003",
                    name="漏洞利用",
                    description="尝试利用发现的漏洞",
                    phase="exploitation",
                    priority=TaskPriority.CRITICAL,
                    dependencies=["task_002"],
                    estimated_rounds=5,
                    tools_required=["custom_exploit"],
                    expected_outcomes=["获取权限", "FLAG"]
                )
            ]
        
        total_est = sum(t.estimated_rounds for t in default_tasks)
        
        fallback_plan = TaskPlan(
            id=f"fallback_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            target_url=target_url,
            mode=self.mode_manager.mode.value,
            tasks=default_tasks,
            phases=["reconnaissance", "exploitation", "post_exploitation"],
            total_estimated_rounds=min(total_est, max_rounds),
            metadata={'is_fallback': True, 'based_on_preprocess': bool(preprocess_info)}
        )
        
        # 🔥🔥🔥 关键修复：fallback plan也必须设置current_plan
        self.current_plan = fallback_plan
        log_message('planning', '⚠️ 使用fallback计划，已设置current_plan')
        
        return fallback_plan
    
    def _get_tools_for_vuln(self, vuln_type: str) -> List[str]:
        """根据漏洞类型返回需要的工具"""
        vuln_lower = vuln_type.lower()
        
        if 'sql' in vuln_lower:
            return ["run_sqlmap", "execute_python"]
        elif 'ssti' in vuln_lower or 'template' in vuln_lower:
            return ["run_fenjing", "execute_python"]
        elif 'lfi' in vuln_lower or 'file' in vuln_lower:
            return ["exploit_lfi", "execute_python"]
        elif 'rce' in vuln_lower or 'command' in vuln_lower:
            return ["run_command", "execute_python"]
        elif 'xxe' in vuln_lower:
            return ["exploit_xxe", "execute_python"]
        else:
            return ["execute_python", "search_knowledge"]
    
    def _clean_for_json(self, data: Any) -> Any:
        """
        转换数据中不可 JSON 序列化的对象为结构化数据
        保留有用信息，不是简单清理
        
        Args:
            data: 需要转换的数据
        
        Returns:
            可JSON序列化的数据
        """
        if data is None:
            return None
        
        # BeautifulSoup对象 → 提取结构化信息
        if hasattr(data, '__class__') and 'BeautifulSoup' in str(data.__class__):
            # 提取有用的结构化信息，而不是简单转字符串
            try:
                return {
                    '_type': 'html_structure',
                    'text': data.get_text()[:2000],  # 文本内容
                    'title': data.title.string if data.title else None,
                    'forms_count': len(data.find_all('form')),
                    'inputs_count': len(data.find_all('input')),
                    'links_count': len(data.find_all('a')),
                    'scripts_count': len(data.find_all('script')),
                    'has_forms': len(data.find_all('form')) > 0,
                    'tag_summary': f"{data.name if hasattr(data, 'name') else 'document'}"
                }
            except:
                return {'_type': 'html_structure', 'raw': str(data)[:1000]}
        
        # Tag对象（BeautifulSoup的子元素）
        if hasattr(data, 'name') and hasattr(data, 'attrs'):
            try:
                return {
                    '_type': 'html_tag',
                    'tag': data.name,
                    'attrs': dict(data.attrs) if hasattr(data, 'attrs') else {},
                    'text': data.get_text()[:500] if hasattr(data, 'get_text') else str(data)[:500]
                }
            except:
                return str(data)[:500]
        
        # 字典 - 递归转换
        if isinstance(data, dict):
            result = {}
            for key, value in data.items():
                # 保留所有字段，只转换值
                result[key] = self._clean_for_json(value)
            return result
        
        # 列表/元组 - 递归转换
        if isinstance(data, (list, tuple)):
            return [self._clean_for_json(item) for item in data]
        
        # 基本类型 - 直接返回
        if isinstance(data, (str, int, float, bool)):
            return data
        
        # 其他对象 - 尝试序列化，失败则提取repr信息
        try:
            json.dumps(data)
            return data
        except (TypeError, ValueError):
            # 尝试提取对象的有用信息
            if hasattr(data, '__dict__'):
                try:
                    return {
                        '_type': data.__class__.__name__,
                        **{k: self._clean_for_json(v) for k, v in data.__dict__.items() if not k.startswith('_')}
                    }
                except:
                    pass
            return {'_type': type(data).__name__, '_repr': str(data)[:500]}
