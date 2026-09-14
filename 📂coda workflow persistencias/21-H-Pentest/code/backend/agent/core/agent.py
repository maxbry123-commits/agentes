"""
Pentest Agent - 完整版（集成所有工具 + 多Agent + 上下文管理）
"""
import asyncio
from typing import Dict, Any, Optional, List
from multiprocessing import Event
from datetime import datetime

from .llm import LLMClient
from .output import OutputManager
from .context_manager import ContextManager
from .flag_detector import FlagDetector
from ..tools import ExecutePython, KnowledgeBase, DirectoryScanner, NucleiScanner
from ..supervisors.strategic import StrategicSupervisor
from ..supervisors.meta import MetaSupervisor
from ..supervisors.payload_master import PayloadMaster


class PentestAgent:
    """渗透测试Agent - 完整版（工具+沙箱+知识库）"""
    
    def __init__(
        self,
        task_id: str,
        target_url: str,
        mode: str,
        config: Dict[str, Any],
        output_manager: OutputManager,
        stop_event: Event
    ):
        self.task_id = task_id
        self.target_url = target_url
        self.mode = mode
        self.config = config
        self.output = output_manager
        self.stop_event = stop_event
        
        # 配置
        self.max_rounds = config.get('max_rounds', 10)
        self.current_round = 0
        
        # 🔥🔥🔥 自定义目标和FLAG提交配置
        self.custom_objective = config.get('custom_objective')
        self.flag_submit_url = config.get('flag_submit_url')
        self.flag_submit_method = config.get('flag_submit_method', 'POST')
        self.token = config.get('token')
        self.challenge_code = config.get('challenge_code')
        
        # LLM客户端（带流式输出回调）
        from app.core.config import settings
        
        # 🔥🔥🔥 打印一次初始化信息
        self.output.log("info", f"🤖 初始化LLM系统: Worker={settings.WORKER_MODEL}, Strategic={settings.STRATEGIC_MODEL or settings.WORKER_MODEL}")
        
        # 🔥🔥🔥 Worker LLM（快速模型）
        self.llm = LLMClient(
            model=config.get('model', settings.WORKER_MODEL),
            temperature=config.get('temperature', settings.WORKER_TEMPERATURE),
            max_tokens=config.get('max_tokens', settings.WORKER_MAX_TOKENS),
            output_callback=self._on_llm_stream_chunk,  # 实时广播
            stop_event=stop_event  # 🔥🔥🔥 传递停止事件
        )
        
        # 🔥🔥🔥 Strategic LLM（强模型用于规划）
        self.strategic_llm = LLMClient(
            model=settings.STRATEGIC_MODEL or settings.WORKER_MODEL,
            temperature=settings.STRATEGIC_TEMPERATURE,
            max_tokens=settings.STRATEGIC_MAX_TOKENS,
            stop_event=stop_event
            # 🔥 不设置output_callback，避免流式输出混淆
        )
        
        # 🔥🔥🔥 Meta LLM（强模型用于监督）
        self.meta_llm = LLMClient(
            model=settings.META_MODEL or settings.WORKER_MODEL,
            temperature=settings.META_TEMPERATURE,
            max_tokens=settings.META_MAX_TOKENS,
            stop_event=stop_event
            # 🔥 不设置output_callback，避免流式输出混淆
        )
        
        # 🔥🔥🔥 Payload Master LLM（独立实例，不给工具）
        self.payload_llm = LLMClient(
            model=settings.META_MODEL or settings.WORKER_MODEL,  # 使用强模型
            temperature=0.7,
            max_tokens=settings.META_MAX_TOKENS,
            stop_event=stop_event,
            output_callback=self._on_llm_stream_chunk  # 🔥 流式输出到前端
            # 🔥🔥🔥 关键：不给tools，所以不会输出<tool_call>
        )
        
        # 🔥🔥🔥 Report LLM（独立实例，负责分析对话提取漏洞）
        self.report_llm = LLMClient(
            model=settings.META_MODEL or settings.WORKER_MODEL,  # 使用强模型
            temperature=0.3,  # 低温度，更准确
            max_tokens=settings.META_MAX_TOKENS,
            stop_event=stop_event
            # 不设置output_callback，避免流式输出
        )
        
        # 上下文管理器（LangChain压缩）
        self.context_mgr = ContextManager(
            model=settings.CONTEXT_MODEL,  # 使用轻量模型
            max_tokens=config.get('max_context_tokens', 8000)
        )
        
        # Supervisor系统（🔥 使用独立的LLM）
        self.strategic_supervisor = StrategicSupervisor(
            target_url=target_url,
            mode=mode,
            llm_client=self.strategic_llm,  # 🔥 使用Strategic LLM
            output_manager=output_manager
        )
        
        self.meta_supervisor = MetaSupervisor(
            llm_client=self.meta_llm,  # 🔥 使用Meta LLM
            output_manager=output_manager,
            max_rounds=self.max_rounds,
            mode=mode  # 🔥 传递模式参数
        )
        
        self.payload_master = PayloadMaster(
            output_manager=output_manager,
            llm_client=self.payload_llm  # 🔥🔥🔥 使用独立的Payload LLM（无工具）
        )
        
        # 🔥🔥🔥 Report Supervisor（负责漏洞检测和报告生成）
        from ..supervisors.report_supervisor import ReportSupervisor
        self.report_supervisor = ReportSupervisor(
            llm_client=self.report_llm,
            output_manager=output_manager
        )
        
        # 🔥 注入context_mgr到Supervisor
        self.strategic_supervisor.context_mgr = self.context_mgr
        self.meta_supervisor.context_mgr = self.context_mgr
        self.report_supervisor.context_mgr = self.context_mgr  # 🔥 Report也需要压缩
        # payload_master不需要context_mgr
        
        # FLAG检测器
        self.flag_detector = FlagDetector()
        
        # 消息历史
        self.messages = []
        
        # 工具系统
        self.tools = {}
        self.tool_instances = {}
        
        # 结果
        self.flags_found = []
        self.vulnerabilities = []
        self.vulns_found = set()  # 🔥 漏洞去重
    
    async def run(self) -> Dict[str, Any]:
        """运行渗透测试（完整架构：预处理→计划→每轮调整→每3轮Meta注入）"""
        self.output.log("info", f"🎯 目标: {self.target_url}")
        self.output.log("info", f"📋 最大轮数: {self.max_rounds}")
        
        # 🔥🔥🔥 检查是否为恢复模式
        is_resume = self.config.get('resume', False)
        start_round = self.config.get('current_round', 0)
        
        if is_resume:
            self.output.log("info", f"🔄 恢复模式：从第{start_round}轮继续")
            
            # 🔥 1. 初始化工具（恢复也需要工具）
            await self._initialize_tools()
            
            # 🔥 2. 加载历史对话
            await self._load_history_from_db()
            self.output.log("success", f"✅ 已加载 {len(self.messages)} 条历史消息")
            
            # 🔥 3. 检查是否需要压缩
            current_tokens = self.context_mgr.count_messages_tokens(self.messages)
            self.output.log("info", f"📊 历史对诏tokens: {current_tokens}")
            
            if current_tokens > 120000 * 0.8:
                self.output.log("warning", f"⚠️  历史对诏过大，触发压缩...")
                self.messages = await self.context_mgr.smart_compress(
                    self.messages,
                    keep_recent=10,
                    target_ratio=0.5
                )
                new_tokens = self.context_mgr.count_messages_tokens(self.messages)
                self.output.log("success", f"✅ 压缩完成: {current_tokens} -> {new_tokens} tokens")
        else:
            # 🔥 正常模式：执行预处理和计划生成
            # 初始化工具
            await self._initialize_tools()
        
            # ============================================================
            # 🔍 阶段1：预处理（信息收集）
            # ============================================================
            self.output.log("info", "\n" + "="*60)
            self.output.log("info", "🔍 阶段1：预处理 - 自动信息收集")
            self.output.log("info", "="*60)
            
            preprocess_results = await self._run_preprocess()
            
            # ============================================================
            # 📋 阶段2：Strategic Supervisor生成初始计划
            # ============================================================
            self.output.log("info", "\n" + "="*60)
            self.output.log("info", "📋 阶段2：Strategic Supervisor生成计划")
            self.output.log("info", "="*60)
            
            # 🔥🔥🔥 传递当前对话历史 + 预处理结果
            test_plan = await self.strategic_supervisor.create_test_plan(
                conversation_history=self.messages.copy(),
                preprocess_results=preprocess_results  # 🔥 传递预处理结果
            )
            
            # 🔥🔥🔥 保存到Strategic Supervisor的current_plan
            self.strategic_supervisor.current_plan = test_plan
            
            # 🔥🔥🔥 广播计划到前端（卡片显示）- 转换为dict
            if hasattr(test_plan, 'to_dict'):
                plan_dict = test_plan.to_dict()
                self.output.plan(plan_dict)
                # 🔥🔥🔥 保存到数据库（直接覆盖）
                await self._save_plan_to_db(plan_dict)
            else:
                self.output.plan(test_plan)
                await self._save_plan_to_db(test_plan)
            self.output.log("success", "✅ 测试计划已生成")
            
            # ============================================================
            # 💉 阶段3：注入Worker - 预处理结果+计划
            # ============================================================
            self.output.log("info", "\n" + "="*60)
            self.output.log("info", "💉 阶段3：注入Worker上下文")
            self.output.log("info", "="*60)
            
            # 系统提示（包含预处理结果和计划）
            self.messages.append({
                'role': 'system',
                'content': self._get_system_prompt_with_context(preprocess_results, test_plan)
            })
            
            self.output.log("success", "✅ Worker上下文初始化完成")
        
        # ============================================================
        # 🔄 主循环：Worker执行 + 每轮调整 + 每3轮Meta注入
        # ============================================================
        execution_results = []
        
        # 🔥 恢复模式：从 start_round 开始；正常模式：从 1 开始
        start_from = start_round if is_resume else 1
        
        for round_num in range(start_from, self.max_rounds + 1):
            if self.stop_event.is_set():
                self.output.log("warning", "⏹️  收到停止信号")
                break
            
            self.current_round = round_num
            self.output.progress(round_num, self.max_rounds, "running", f"第 {round_num} 轮")
            self.output.log("info", f"\n{'='*60}\n🔄 Round {round_num}/{self.max_rounds}\n{'='*60}")
            
            # 🔥 检查暂停状态
            await self._check_pause_state()
            
            # 🔥 检查人工干预
            await self._check_human_intervention()
            
            # 🗜️ 智能上下文压缩（每轮检测）
            current_tokens = self.context_mgr.count_messages_tokens(self.messages)
            self.output.log("debug", f"📊 当前tokens: {current_tokens}")
            
            # 策略1：单次LLM调用超限检测
            if current_tokens > self.llm.max_tokens * 0.8:
                self.output.log("warning", f"⚠️  接近单次max_tokens限制 ({current_tokens}/{self.llm.max_tokens})")
                self.output.log("info", "🗜️  触发压缩...")
                self.messages = await self.context_mgr.compress_messages(
                    self.messages,
                    target_tokens=int(self.llm.max_tokens * 0.6)
                )
            
            # 策略2：全对话超120k*0.8触发全量压缩
            if current_tokens > 120000 * 0.8:
                self.output.log("warning", f"⚠️  全对话tokens过大 ({current_tokens}/96000)")
                self.output.log("info", "🗜️  触发全量智能压缩...")
                self.messages = await self.context_mgr.smart_compress(
                    self.messages,
                    keep_recent=10,
                    target_ratio=0.5
                )
            
            # 🤖 Worker执行：LLM思考＋工具调用
            response = await self._llm_think_and_act(round_num)
            
            # 记录执行结果
            execution_results.append({
                'round': round_num,
                'response': response,
                'tool_calls': len(response.get('tool_calls', [])),
                'status': 'success' if response.get('tool_calls') else 'no_action',
                'type': 'execution'  # 🔥 添加type字段
            })
            
            # 🧠 每3轮：Meta Supervisor注入洞察
            if round_num % 3 == 0 and round_num > 1:
                self.output.log("info", "🧠 Meta Supervisor: 生成元层洞察并注入...")
                
                # 🔥 传递完整对话历史
                meta_insights = await self.meta_supervisor.generate_meta_insights(
                    execution_data={
                        'total_rounds': round_num,
                        'total_time': round_num * 30,  # 估算
                        'tool_usage': self._collect_tool_usage(),
                        'success_rate': self._calculate_success_rate(execution_results)
                    },
                    conversation_history=self.messages.copy()
                )
                
                if meta_insights:
                    # 💉 注入Meta洞察到Worker上下文
                    meta_content = "\n".join(meta_insights)
                    self.messages.append({
                        'role': 'system',
                        'content': f"🧠 **Meta Supervisor洞察**：\n{meta_content}"
                    })
                    
                    # 🔥 广播到前端（卡片显示）
                    self.output.meta_insights(meta_insights, round_num)
                    self.output.log("success", f"✅ Meta洞察已注入: {len(meta_insights)}条")
            
            # 🔥🔥🔥 每3轮：Payload Master提供指导（在Worker执行后）
            if self.payload_master.should_provide_guidance(round_num):
                self.output.log("info", "🎯 Payload Master: 提供测试指导...")
                
                # 🔥🔥🔥 传递完整对话历史，让Payload Master自己判断漏洞类型
                guidance = await self.payload_master.generate_payload_guidance(
                    conversation_history=self.messages.copy(),
                    round_num=round_num
                )
                
                if guidance.get('suggested_payloads'):
                    self.output.log("success", f"✅ Payload指导已生成: {guidance.get('vuln_type', 'unknown')}")
            
            # 📊 每轮：Strategic动态调整计划（在Worker执行后）
            if round_num > 1:
                self.output.log("info", "📊 Strategic Supervisor: 动态调整计划...")
                
                # 🔥🔥🔥 调用adjust_plan，返回changes
                adjust_result = await self.strategic_supervisor.adjust_plan(
                    conversation_history=self.messages.copy(),
                    execution_results=execution_results,
                    current_round=round_num
                )
                
                changes = adjust_result.get('changes', [])
                if changes:
                    # 🔥🔥🔥 执行replace_plan更新计划
                    updated_plan = await self.strategic_supervisor.replace_plan(changes)
                    
                    # 🔥🔥🔥 广播更新后的计划到前端（直接覆盖）
                    if hasattr(updated_plan, 'to_dict'):
                        plan_dict = updated_plan.to_dict()
                        self.output.plan(plan_dict)
                        await self._save_plan_to_db(plan_dict)
                    
                    # 🔥 注入调整信息到Worker
                    adjustment_note = f"📊 **计划已调整**: {len(changes)}项变更"
                    self.messages.append({
                        'role': 'system',
                        'content': adjustment_note
                    })
                    self.output.log("success", f"✅ 计划已调整: {len(changes)}项变更")
            
            # 🔥🔥🔥 Meta自主决策：是否强制停止
            meta_decision = await self.meta_supervisor.should_force_stop(
                current_round=round_num,
                execution_results=execution_results,
                conversation_history=self.messages.copy(),
                flags_found=self.flags_found
            )
            
            if meta_decision['should_stop']:
                reason = meta_decision.get('reason', '未知原因')
                confidence = meta_decision.get('confidence', 0.5)
                self.output.log("success", f"✅ Meta Supervisor决定停止: {reason} (置信度: {confidence:.2f})")
                break
            
            # 检查是否完成
            if self._check_completion(response):
                self.output.log("success", "✅ 检测到完成标记")
                break
        
        # 清理工具
        await self._cleanup_tools()
        
        # 🔥 生成完整报告
        self.output.log("info", "📄 生成渗透测试报告...")
        report = await self._generate_comprehensive_report(execution_results)
        
        # 🔥🔥🔥 广播报告到前端
        self.output._send('report', report)
        
        # 🔥 保存报告到数据库
        await self._save_report_to_db(report)
        
        return report
    
    async def _on_llm_stream_chunk(self, chunk: str):
        """
LLM流式输出回调（实时广播到前端）
        
        Args:
            chunk: LLM输出的内容块
        """
        # 实时发送流式块到前端
        self.output.llm_stream(chunk)
    
    async def _initialize_tools(self):
        """初始化工具系统（🔥 从配置文件动态注册）"""
        self.output.log("info", "🔧 初始化工具系统...")
        
        # 🔥 加载工具配置
        import json
        import os
        
        config_path = os.path.join(os.path.dirname(__file__), '../../config/tools_config.json')
        try:
            with open(config_path, 'r') as f:
                tools_config = json.load(f)
        except Exception as e:
            self.output.log("warning", f"⚠️  加载工具配置失败: {e}，使用默认")
            tools_config = {}
        
        # 🔥🔥🔥 所有工具实例都创建（用于预处理）
        all_tool_instances = {
            'execute_python': ExecutePython(session_id=self.task_id),
            'query_knowledge': KnowledgeBase(),
            'nuclei_scan': NucleiScanner(),
            'directory_scan': DirectoryScanner()
        }
        
        # 🔥 保存所有工具实例（预处理需要）
        self.all_tool_instances = all_tool_instances
        
        # 🔥 只有enabled的工具才注册给LLM
        self.tool_instances = {}
        for tool_name, tool_instance in all_tool_instances.items():
            config = tools_config.get(tool_name, {})
            if config.get('enabled', True):  # 默认启用
                self.tool_instances[tool_name] = tool_instance
                self.output.log("success", f"✅ 已注册: {tool_name} - {config.get('description', '')}")
            else:
                self.output.log("info", f"⏸️  已禁用: {tool_name} - {config.get('description', '')}")
        
        # 初始化所有工具（包括被禁用的）
        for name, tool in all_tool_instances.items():
            try:
                if hasattr(tool, 'initialize'):
                    await tool.initialize()
                    self.output.log("success", f"✅ {name} 初始化成功")
            except Exception as e:
                self.output.log("warning", f"⚠️  {name} 初始化失败: {e}")
        
        # 🔥 只把enabled的工具转换为OpenAI工具格式
        self.tools = [tool.to_openai_tool() for tool in self.tool_instances.values()]
        
        self.output.log("success", f"✅ 工具系统就绪: {len(self.tools)}个工具")
    
    async def _cleanup_tools(self):
        """清理工具资源"""
        # 🔥 清理所有工具实例
        for name, tool in self.all_tool_instances.items():
            try:
                if hasattr(tool, 'cleanup'):
                    await tool.cleanup()
            except Exception as e:
                self.output.log("warning", f"⚠️  {name} 清理失败: {e}")
    
    async def _llm_think_and_act(self, round_num: int) -> Dict[str, Any]:
        """LLM思考＋工具调用循环"""
        self.output.log("info", "🧠 LLM思考中...")
        
        # 🔥🔥🔥 检查是否需要添加初始user消息（智谱AI要求）
        # 如果只有system消息，必须加一个user消息
        if len(self.messages) > 0 and all(msg['role'] == 'system' for msg in self.messages):
            self.output.log("debug", "⚠️  检测到只有system消息，添加初始user消息")
            self.messages.append({
                'role': 'user',
                'content': '开始执行渗透测试，请根据上述信息开始分析和测试。'
            })
        
        # 调用LLM（带工具）
        response = await self.llm.chat(
            messages=self.messages,
            tools=self.tools if self.tools else None,
            stream=True
        )
        
        # 发送思考内容到前端
        if response.get('content'):
            self.output.llm_thinking(response['content'], round_num)
        
        # 🔥🔥🔥 添加到历史（必须包含tool_calls！）
        assistant_msg = {
            'role': 'assistant',
            'content': response.get('content', '')
        }
        
        # 🔥 如果有工具调用，必须添加tool_calls字段
        if response.get('tool_calls'):
            assistant_msg['tool_calls'] = response['tool_calls']
        
        self.messages.append(assistant_msg)
        
        # 🔥🔥🔥 广播到前端显示（卡片）
        self.output.conversation_message(
            role='assistant',
            content=response.get('content', ''),
            tool_calls=response.get('tool_calls'),
            round_num=round_num
        )
        
        # 处理工具调用
        if response.get('tool_calls'):
            self.output.log("info", f"🔧 检测到 {len(response['tool_calls'])} 个工具调用")
            
            for tool_call in response['tool_calls']:
                await self._execute_tool(tool_call, round_num)
        
        return response
    
    async def _execute_tool(self, tool_call: Dict[str, Any], round_num: int):
        """执行工具调用"""
        import json
        
        tool_name = tool_call['function']['name']
        tool_args_str = tool_call['function']['arguments']
        
        try:
            tool_args = json.loads(tool_args_str)
        except Exception as e:
            self.output.log("warning", f"⚠️  JSON解析失败: {e}")
            self.output.log("debug", f"原始参数: {tool_args_str[:200]}...")
            tool_args = {}
        
        self.output.log("info", f"🔧 调用工具: {tool_name}")
        self.output.log("debug", f"   参数: {tool_args}")
        
        # 查找工具
        if tool_name not in self.tool_instances:
            result = f"❌ 工具不存在: {tool_name}"
        else:
            try:
                tool = self.tool_instances[tool_name]
                result = await tool.execute(**tool_args)
                self.output.log("success", f"✅ {tool_name} 执行成功")
            except Exception as e:
                result = f"❌ 工具执行失败: {str(e)}"
                self.output.log("error", result)
        
        # 发送工具执行结果到前端
        self.output.tool_execution(
            tool_name=tool_name,
            args=tool_args,
            result=result,
            round_num=round_num
        )
        
        # 🔥 FLAG检测（自动检测工具输出中的FLAG）
        detected_flags = self.flag_detector.detect(result)
        for flag in detected_flags:
            if flag not in self.flags_found:
                self.flags_found.append(flag)
                self.output.flag(flag)
                self.output.log("success", f"🚩 发现FLAG: {flag}")
        
        # 添加工具结果到对话历史
        tool_msg = {
            'role': 'tool',
            'tool_call_id': tool_call['id'],
            'name': tool_name,
            'content': result[:30000]  # 🔥 限制长度为30000字符
        }
        self.messages.append(tool_msg)
        
        # 🔥🔥🔥 广播到前端显示（卡片）
        self.output.conversation_message(
            role='tool',
            content=result[:30000],  # 🔥 限制长度为30000字符
            tool_call_id=tool_call['id'],
            tool_name=tool_name,
            round_num=round_num
        )
    
    def _get_system_prompt_with_context(self, preprocess_results: Dict[str, Any], test_plan: Dict[str, Any]) -> str:
        """
        获取系统提示（包含预处理结果和计划）
        
        🔥 注入：
        1. 预处理结果（页面数据、特征、漏洞、主动探测）
        2. 测试计划（阶段和任务）
        """
        base_prompt = self._get_system_prompt()
        
        # ============================================================
        # 1. 预处理结果详细信息
        # ============================================================
        preprocess_section = "\n\n" + "="*70 + "\n"
        preprocess_section += "🔍 **预处理结果** (已完成自动扫描）\n"
        preprocess_section += "="*70 + "\n\n"
        
        # 1.1 页面数据
        page_data = preprocess_results.get('page_data', {})
        if page_data:
            preprocess_section += "### 📝 页面分析\n"
            preprocess_section += f"- 状态码: {page_data.get('status_code', 'N/A')}\n"
            preprocess_section += f"- HTML长度: {page_data.get('html_length_truncated', 0)} 字符 (原始: {page_data.get('html_length_original', 0)})\n"
            
            cookies = page_data.get('cookies', [])
            if cookies:
                preprocess_section += f"- Cookies: {len(cookies)}个\n"
                for cookie in cookies[:3]:
                    preprocess_section += f"  * {cookie.get('name')}={cookie.get('value')[:30]}...\n"
            
            headers = page_data.get('headers', {})
            if headers:
                server = headers.get('Server', 'Unknown')
                powered_by = headers.get('X-Powered-By', 'Unknown')
                preprocess_section += f"- Server: {server}\n"
                if powered_by != 'Unknown':
                    preprocess_section += f"- X-Powered-By: {powered_by}\n"
            
            # HTML预览
            html = page_data.get('html', '')
            if html:
                preprocess_section += f"\n**HTML内容预览** (前3000字符，已移除CSS):\n```html\n{html[:3000]}\n```\n"
        
        # 1.2 特征提取
        features = preprocess_results.get('features', {})
        if features:
            preprocess_section += "\n### 🔎 特征提取\n"
            preprocess_section += f"- 表单数量: {features.get('form_count', 0)}个\n"
            
            forms = features.get('forms', [])
            if forms:
                preprocess_section += "\n**表单详情**:\n"
                for i, form in enumerate(forms, 1):
                    preprocess_section += f"\n表单 {i}:\n"
                    preprocess_section += f"  - Action: {form.get('action', '')}\n"
                    preprocess_section += f"  - Method: {form.get('method', 'GET')}\n"
                    preprocess_section += f"  - 字段:\n"
                    for inp in form.get('inputs', []):
                        preprocess_section += f"    * name={inp.get('name')}, type={inp.get('type')}\n"
            
            if features.get('has_login'):
                preprocess_section += "\n⚠️  **检测到登录表单** - 可尝试凭据爆破\n"
            
            technologies = features.get('technologies', [])
            if technologies:
                preprocess_section += f"\n- 技术栈: {', '.join(technologies)}\n"
        
        # 1.3 漏洞扫描结果
        vulns = preprocess_results.get('vulnerabilities', [])
        if vulns:
            preprocess_section += f"\n### 🔥 Nuclei扫描结果\n"
            preprocess_section += f"- 发现漏洞: {len(vulns)}个\n\n"
            for vuln in vulns[:5]:  # 只显示前5个
                preprocess_section += f"  [{vuln.get('severity', 'N/A')}] {vuln.get('name', 'N/A')}\n"
                if vuln.get('description'):
                    preprocess_section += f"    描述: {vuln.get('description')[:100]}\n"
        
        # 1.4 主动探测结果
        active_probe = preprocess_results.get('active_probe', {})
        if active_probe.get('credential_test'):
            cred_test = active_probe['credential_test']
            if cred_test.get('success'):
                valid_creds = cred_test.get('valid_credentials', [])
                preprocess_section += f"\n### 🔑 凭据爆破结果\n"
                preprocess_section += f"✅ **登录成功**! 找到 {len(valid_creds)} 组有效凭据:\n\n"
                for cred in valid_creds:
                    preprocess_section += f"  - {cred.get('username')}:{cred.get('password')}\n"
                    preprocess_section += f"    重定向: {cred.get('redirect', 'N/A')}\n"
                preprocess_section += "\n⚠️  **建议**: 立即使用此凭据登录，查看认证后的功能\n"
        
        # ============================================================
        # 2. 测试计划
        # ============================================================
        plan_section = "\n\n" + "="*70 + "\n"
        plan_section += "📋 **测试计划** (分阶段执行)\n"
        plan_section += "="*70 + "\n\n"
        
        # 🔥🔥🔥 处理TaskPlan对象：转换为dict或直接使用属性
        if hasattr(test_plan, 'to_dict'):
            # TaskPlan对象，转换为dict
            plan_dict = test_plan.to_dict()
            tasks = plan_dict.get('tasks', [])
            phases = plan_dict.get('phases', [])
            
            # 按阶段组织任务
            for phase in phases:
                plan_section += f"### {phase}\n\n"
                phase_tasks = [t for t in tasks if t.get('phase') == phase]
                
                for i, task in enumerate(phase_tasks, 1):
                    task_name = task.get('name', '')
                    task_desc = task.get('description', '')
                    task_priority = task.get('priority', 'medium')
                    plan_section += f"{i}. **{task_name}** (Priority: {task_priority.upper()})\n"
                    plan_section += f"   - 描述: {task_desc}\n"
                    plan_section += f"   - 预估轮数: {task.get('estimated_rounds', 1)}\n\n"
        else:
            # 旧的dict格式（兼容）
            phases = test_plan.get('phases', [])
            for phase in phases:
                phase_name = phase.get('name', '')
                phase_priority = phase.get('priority', 'normal')
                plan_section += f"### {phase_name} (Priority: {phase_priority.upper()})\n\n"
                
                tasks = phase.get('tasks', [])
                for i, task in enumerate(tasks, 1):
                    task_name = task.get('task', '')
                    task_tool = task.get('tool', '')
                    task_expected = task.get('expected', '')
                    plan_section += f"{i}. **{task_name}**\n"
                    plan_section += f"   - 工具: {task_tool}\n"
                    plan_section += f"   - 预期: {task_expected}\n\n"
        
        # ============================================================
        # 3. 重要提示
        # ============================================================
        tips_section = "\n\n" + "="*70 + "\n"
        tips_section += "⚠️  **重要提示**\n"
        tips_section += "="*70 + "\n\n"
        tips_section += "1. 以上预处理信息已经提供了很多线索，优先利用这些信息\n"
        tips_section += "2. 按照测试计划逐步执行，不要跳过关键步骤\n"
        tips_section += "3. 如果发现有效凭据，立即登录并探索认证后功能\n"
        tips_section += "4. 如果Nuclei发现了漏洞，优先验证和利用这些漏洞\n"
        tips_section += "5. 使用execute_python工具灵活编写测试代码，不要限制想象力\n"
        tips_section += "6. CTF模式下，积极寻找flag{{...}}格式的内容\n"
        tips_section += "\n现在开始执行渗透测试！\n"
        
        return base_prompt + preprocess_section + plan_section + tips_section
    
    async def _run_preprocess(self) -> Dict[str, Any]:
        """运行智能预处理阶段（使用SmartPreprocessor）"""
        from ..preprocessing.smart_preprocessor import SmartPreprocessor
        
        # 🔥🔥🔥 使用all_tool_instances，包括nuclei_scan
        preprocessor = SmartPreprocessor(
            target_url=self.target_url,
            tool_instances=self.all_tool_instances,  # 🔥 使用所有工具
            output_manager=self.output
        )
        
        # 执行完整的智能预处理
        results = await preprocessor.analyze()
        
        return results
    
    def _format_plan_for_frontend(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        """
        将Strategic返回的计划转换为TaskPlanViewer需要的格式
        
        Strategic格式:
        {
            'phases': [
                {'name': '信息收集', 'priority': 'high', 'tasks': [...]}
            ]
        }
        
        TaskPlanViewer格式:
        {
            'id': str,
            'target_url': str,
            'mode': str,
            'phases': ['reconnaissance', 'exploitation', ...],  # 阶段名称数组
            'current_phase': str,
            'total_tasks': int,
            'total_estimated_rounds': int,
            'tasks': [  # 平铺的任务列表
                {
                    'id': str,
                    'name': str,
                    'description': str,
                    'phase': str,
                    'priority': str,
                    'status': str,
                    'dependencies': [],
                    'estimated_rounds': int,
                    'actual_rounds': int
                }
            ]
        }
        """
        import uuid
        
        # 提取阶段名称
        phases = plan.get('phases', [])
        phase_names = [p.get('name', '') for p in phases]
        
        # 将所有任务平铺
        tasks = []
        total_estimated_rounds = 0
        
        for phase_idx, phase in enumerate(phases):
            phase_name = phase.get('name', f'Phase{phase_idx}')
            phase_priority = phase.get('priority', 'medium')
            phase_tasks = phase.get('tasks', [])
            
            for task_idx, task in enumerate(phase_tasks):
                task_id = str(uuid.uuid4())
                task_name = task.get('task', f'Task {task_idx}')
                task_description = task.get('expected', '')
                task_tool = task.get('tool', '')
                
                # 估计轮数（根据任务优先级）
                estimated_rounds = 3 if phase_priority == 'high' else 2
                total_estimated_rounds += estimated_rounds
                
                tasks.append({
                    'id': task_id,
                    'name': task_name,
                    'description': f"{task_description}\n工具: {task_tool}",
                    'phase': phase_name,
                    'priority': phase_priority,
                    'status': 'pending' if phase_idx == 0 and task_idx == 0 else 'pending',
                    'dependencies': [],
                    'estimated_rounds': estimated_rounds,
                    'actual_rounds': 0
                })
        
        # 构建前端格式
        formatted_plan = {
            'id': self.task_id,
            'target_url': self.target_url,
            'mode': self.mode,
            'phases': phase_names,
            'current_phase': phase_names[0] if phase_names else '',
            'total_tasks': len(tasks),
            'total_estimated_rounds': total_estimated_rounds,
            'tasks': tasks
        }
        
        return formatted_plan
    
    def _collect_tool_usage(self) -> Dict[str, int]:
        """统计工具使用情况"""
        usage = {}
        for msg in self.messages:
            if msg.get('role') == 'tool':
                tool_name = msg.get('name', 'unknown')
                usage[tool_name] = usage.get(tool_name, 0) + 1
        return usage
    
    def _calculate_success_rate(self, results: List[Dict]) -> float:
        """计算成功率"""
        if not results:
            return 0.0
        successful = sum(1 for r in results if r.get('status') == 'success')
        return successful / len(results)
    
    def _get_system_prompt(self) -> str:
        """获取基础系统提示"""
        prompt = f"""你是一个高级渗透测试专家，正在对目标 {self.target_url} 进行全面的安全评估。

## 目标信息
- URL: {self.target_url}
- 模式: {self.mode.upper()}
- 最大轮数: {self.max_rounds}
"""

        # 🔥🔥🔥 注入自定义目标
        if self.custom_objective:
            prompt += f"""
## 🎯 自定义测试目标
{self.custom_objective}

**重要**：优先完成上述自定义目标，这是本次测试的主要任务。
"""

        # 🔥🔥🔥 注入FLAG提交配置
        if self.flag_submit_url:
            prompt += f"""
## 🚩 FLAG提交配置
- FLAG提交URL: {self.flag_submit_url}
- 提交方法: {self.flag_submit_method}
"""
            if self.token:
                prompt += f"- 认证Token: {self.token[:20]}...\n"
            if self.challenge_code:
                prompt += f"- 题目代码: {self.challenge_code}\n"
            
            prompt += """
**找到FLAG后必须立即提交！** 使用execute_python工具发送提交请求。
"""

        prompt += """
## 可用工具
### 1. execute_python
在隔离的Docker沙箱中执行Python代码。
- 可使用: requests, beautifulsoup4, pycryptodome, pyjwt等
- 适用于: HTTP请求、数据解析、加密解密、漏洞验证
- 示例: 发送带payload的请求、解析响应、SQL注入测试

### 2. kali_execute  
执行Kali Linux渗透测试工具。
- 可用工具: nmap, sqlmap, nikto, dirb, gobuster等
- 适用于: 端口扫描、目录爆破、SQL注入、漏洞扫描
- 示例: nmap -sV target.com, sqlmap -u "url" --batch

### 3. nuclei_scan (🔥新)
使用Nuclei进行自动化漏洞扫描，支持11000+模板。
- 支持严重程度过滤: critical, high, medium, low
- 支持标签过滤: cve, sqli, xss, lfi, rce, ssti等
- 适用于: 快速发现常见漏洞、CVE漏洞、配置错误
- 示例: nuclei_scan(target="http://example.com", severity="critical,high")

### 4. directory_scan (🔥新)
扫描Web目录和文件，发现隐藏路径、备份文件、敏感信息。
- 适用于: 发现隐藏管理页面、备份文件、配置文件
- 支持多种文件扩展名：php, asp, jsp, html, js等
- 示例: directory_scan(target="http://example.com", extensions="php,asp")

### 5. query_knowledge
查询渗透测试知识库。
- 类别: sql_injection, xss, lfi, rce, ssti等
- 适用于: 获取Payload、漏洞利用技巧、绕过方法
- 示例: 查询SQL注入Payload、XSS绕过技巧

## 工作流程
1. **信息收集**: 使用requests/nmap获取目标信息
2. **漏洞扫描**: 结合工具和手工测试发现漏洞
3. **漏洞利用**: 使用知识库Payload进行exploit
4. **获取FLAG**: 如果是CTF模式，寻找flag{{}}
5. **生成报告**: 总结发现的漏洞和利用过程

## 重要提示
- 优先使用execute_python进行灵活的自定义测试
- 合理组合使用多个工具提高效率
- 发现漏洞后立即尝试利用
- CTF模式下积极寻找flag
- 遇到问题时查询知识库获取帮助
- 完成后输出 <<<END>>> 标记

现在开始渗透测试！"""
        
        return prompt
    
    def _check_completion(self, response: Dict[str, Any]) -> bool:
        """检查是否完成"""
        content = response.get('content', '').lower()
        return '<<<END' in content or '测试完成' in content
    
    async def _generate_comprehensive_report(self, execution_results: List[Dict]) -> Dict[str, Any]:
        """
        🔥 生成完整渗透测试报告（与前端字段一致）
        
        前端需要的字段：
        - summary: 摘要
        - vulnerabilities: 漏洞列表
        - flags_found: FLAG列表
        - statistics: 统计信息
        - timeline: 时间线
        - recommendations: 建议
        """
        # 基本信息
        total_rounds = len(execution_results)
        successful_rounds = len([r for r in execution_results if r.get('status') == 'success'])
        
        # 🔥🔥🔥 调用Report Supervisor分析对话，提取漏洞和攻击路径
        self.output.log("info", "🔍 Report Supervisor: 分析对话提取漏洞和攻击路径...")
        vulnerabilities, attack_path = await self.report_supervisor.extract_vulnerabilities(
            conversation_history=self.messages.copy(),
            target_url=self.target_url
        )
        
        # 🔥 广播漏洞到前端
        for vuln in vulnerabilities:
            vuln_key = f"{vuln['type']}_{vuln.get('url', '')}_{vuln.get('description', '')[:50]}"
            if vuln_key not in self.vulns_found:
                self.vulns_found.add(vuln_key)
                self.output.vulnerability_found(vuln)
                self.output.log("success", f"🔓 发现漏洞: {vuln['type']} - {vuln['severity']}")
        
        # 保存到实例
        self.vulnerabilities = vulnerabilities
        
        # 生成摘要
        summary = {
            'target': self.target_url,
            'mode': self.mode,
            'total_rounds': total_rounds,
            'successful_rounds': successful_rounds,
            'flags_found': len(self.flags_found),
            'vulnerabilities_found': len(vulnerabilities),
            'status': 'completed' if self.flags_found or vulnerabilities else 'no_findings'
        }
        
        # 统计信息
        statistics = {
            'total_rounds': total_rounds,
            'successful_rounds': successful_rounds,
            'failed_rounds': total_rounds - successful_rounds,
            'success_rate': successful_rounds / total_rounds if total_rounds > 0 else 0,
            'tool_usage': self._collect_tool_usage(),
            'total_flags': len(self.flags_found),
            'total_vulns': len(vulnerabilities),
            'vuln_by_severity': self._count_vulns_by_severity(vulnerabilities)
        }
        
        # 时间线（简化版）
        timeline = [
            {
                'round': r.get('round', i+1),
                'tool_calls': r.get('tool_calls', 0),
                'status': r.get('status', 'unknown')
            }
            for i, r in enumerate(execution_results)
        ]
        
        # 建议
        recommendations = self._generate_recommendations(vulnerabilities)
        
        # 🔥 完整报告结构（与前端一致）
        report = {
            'task_id': self.task_id,
            'target_url': self.target_url,
            'mode': self.mode,
            'summary': summary,
            'statistics': statistics,
            'vulnerabilities': vulnerabilities,
            'flags_found': self.flags_found,
            'timeline': timeline,
            'attack_path': attack_path,  # 🔥 攻击路径
            'recommendations': recommendations,
            'generated_at': datetime.now().isoformat(),
            'status': 'completed'
        }
        
        self.output.log("success", f"✅ 报告生成完成: {len(vulnerabilities)}个漏洞, {len(self.flags_found)}个FLAG")
        
        return report
    
    async def _save_report_to_db(self, report: Dict[str, Any]):
        """🔥 保存报告到数据库"""
        try:
            from app.db.database import AsyncSessionLocal
            from app.models.task import Task
            from sqlalchemy import select
            from datetime import datetime
            
            async with AsyncSessionLocal() as session:
                result = await session.execute(
                    select(Task).where(Task.id == self.task_id)
                )
                task = result.scalar_one_or_none()
                
                if task:
                    # 🔥 更新Task
                    task.report = report
                    task.flags_found = self.flags_found
                    task.vulnerabilities = self.vulnerabilities
                    task.completed_at = datetime.utcnow()
                    
                    await session.commit()
                    self.output.log("success", "✅ 报告已保存到数据库")
                else:
                    self.output.log("warning", f"⚠️  未找到任务: {self.task_id}")
        
        except Exception as e:
            self.output.log("error", f"❌ 保存报告失败: {e}")
    
    def _count_vulns_by_severity(self, vulns: List[Dict]) -> Dict[str, int]:
        """按严重程度统计漏洞"""
        counts = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0, 'info': 0}
        for v in vulns:
            severity = v.get('severity', 'info').lower()
            if severity in counts:
                counts[severity] += 1
        return counts
    
    def _generate_recommendations(self, vulns: List[Dict]) -> List[str]:
        """生成修复建议"""
        recommendations = []
        
        if not vulns:
            recommendations.append("未发现明显漏洞，建议进行更深入的测试")
        else:
            # 根据漏洞类型生成建议
            vuln_types = set(v.get('type', 'unknown') for v in vulns)
            
            for vtype in vuln_types:
                if 'sql' in vtype.lower():
                    recommendations.append("修复SQL注入：使用参数化查询，验证输入")
                elif 'xss' in vtype.lower():
                    recommendations.append("修复XSS：输出编码，使用CSP头")
                elif 'rce' in vtype.lower():
                    recommendations.append("修复RCE：禁止命令执行，验证输入")
        
        return recommendations
    
    async def _check_pause_state(self):
        """🔥 检查暂停状态，如果暂停则等待恢复"""
        try:
            from app.db.database import AsyncSessionLocal
            from app.models.task import Task, TaskStatus
            from sqlalchemy import select
            import asyncio
            
            async with AsyncSessionLocal() as session:
                result = await session.execute(
                    select(Task).where(Task.id == self.task_id)
                )
                task = result.scalar_one_or_none()
                
                if task and task.status == TaskStatus.PAUSED:
                    self.output.log("warning", "⏸️  任务已暂停，等待恢复...")
                    
                    # 轮询等待恢复
                    while True:
                        await asyncio.sleep(2)  # 每2秒检查一次
                        
                        # 重新查询状态
                        result = await session.execute(
                            select(Task).where(Task.id == self.task_id)
                        )
                        task = result.scalar_one_or_none()
                        
                        if task.status == TaskStatus.RUNNING:
                            self.output.log("success", "▶️  任务已恢复")
                            break
                        elif task.status == TaskStatus.STOPPED:
                            self.output.log("warning", "⏹️  任务已停止")
                            self.stop_event.set()
                            break
        
        except Exception as e:
            self.output.log("error", f"❌ 检查暂停状态失败: {e}")
    
    async def _check_human_intervention(self):
        """🔥 检查人工干预指令并注入"""
        try:
            from app.db.database import AsyncSessionLocal
            from app.models.task import Message
            from sqlalchemy import select
            
            async with AsyncSessionLocal() as session:
                # 查询未处理的intervention消息
                result = await session.execute(
                    select(Message)
                    .where(Message.task_id == self.task_id)
                    .where(Message.type == 'intervention')
                    .order_by(Message.created_at.desc())
                    .limit(10)
                )
                interventions = result.scalars().all()
                
                for intervention in interventions:
                    # 检查是否已处理
                    metadata = intervention.msg_metadata or {}
                    if metadata.get('processed'):
                        continue
                    
                    # 注入指令
                    instruction = intervention.content
                    priority = metadata.get('priority', 'high')
                    
                    self.output.log("info", f"👥 检测到人工干预：{instruction}")
                    
                    # 注入到Worker上下文
                    priority_prefix = {
                        'critical': '🔴 [紧急]',
                        'high': '🟠 [高优先级]',
                        'medium': '🟡 [中优先级]',
                        'low': '🟢 [低优先级]'
                    }.get(priority, '')
                    
                    self.messages.append({
                        'role': 'system',
                        'content': f"{priority_prefix} **人工干预**：{instruction}"
                    })
                    
                    # 🔥 广播到前端（卡片显示）
                    self.output.intervention(instruction, priority)
                    
                    # 标记为已处理
                    metadata['processed'] = True
                    metadata['processed_at'] = datetime.now().isoformat()
                    intervention.msg_metadata = metadata
                    await session.commit()
                    
                    self.output.log("success", f"✅ 人工指令已注入")
        
        except Exception as e:
            self.output.log("error", f"❌ 检查人工干预失败: {e}")
    
    async def _load_history_from_db(self):
        """
        🔥🔥🔥 从数据库加载历史对话（用于恢复任务）
        
        从 messages 表加载所有历史消息，按时间顺序排列
        """
        try:
            from app.db.database import AsyncSessionLocal
            from app.models.task import Message
            from sqlalchemy import select
            
            async with AsyncSessionLocal() as session:
                # 🔥 查询所有历史消息（按时间排序）
                result = await session.execute(
                    select(Message)
                    .where(Message.task_id == self.task_id)
                    .where(Message.type.in_(['llm_thinking', 'tool_execution']))  # 🔥 只加载对诚内容
                    .order_by(Message.created_at.asc())
                )
                messages = result.scalars().all()
                
                self.output.log("info", f"📋 从数据库加载到 {len(messages)} 条原始消息")
                
                # 🔥 转换为LLM对话格式
                for msg in messages:
                    msg_metadata = msg.msg_metadata or {}
                    
                    if msg.type == 'llm_thinking':
                        # LLM思考消息
                        role = msg_metadata.get('role', 'assistant')
                        self.messages.append({
                            'role': role,
                            'content': msg.content
                        })
                    
                    elif msg.type == 'tool_execution':
                        # 工具执行消息
                        tool_name = msg_metadata.get('tool_name')
                        tool_result = msg_metadata.get('result')
                        
                        if tool_name and tool_result:
                            # 添加工具结果消息
                            self.messages.append({
                                'role': 'system',
                                'content': f"🛠️ **工具执行结果** ({tool_name}):\n{tool_result}"
                            })
                
                self.output.log("success", f"✅ 历史对话加载完成，共 {len(self.messages)} 条消息")
                
        except Exception as e:
            self.output.log("error", f"⚠️  加载历史对话失败: {e}")
            import traceback
            traceback.print_exc()
            # 🔥 失败也要继续，但从空对话开始
            self.messages = []
    
    async def _save_plan_to_db(self, plan_data: dict):
        """💾 保存计划到数据库（直接覆盖task.task_plan字段）"""
        try:
            from app.db.database import AsyncSessionLocal
            from app.models.task import Task
            from sqlalchemy import select
            
            async with AsyncSessionLocal() as session:
                result = await session.execute(
                    select(Task).where(Task.id == self.task_id)
                )
                task = result.scalar_one_or_none()
                
                if task:
                    # 🔥🔥🔥 直接覆盖，不管之前有没有
                    task.task_plan = plan_data
                    await session.commit()
                    self.output.log("success", f"✅ 计划已保存到数据库: {len(plan_data.get('tasks', []))} 个任务")
                else:
                    self.output.log("warning", f"⚠️  未找到任务ID {self.task_id}，跳过保存")
        except Exception as e:
            self.output.log("error", f"⚠️  保存计划到数据库失败: {e}")
