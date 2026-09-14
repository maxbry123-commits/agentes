"""
协调者Agent
负责团队协作、任务分配和进度监控
像黑客团队领导一样高效协调各个专家Agent
"""
from typing import Dict, List, Optional, Any
import json
from datetime import datetime
from .base import BaseAgent, AgentResult, Task, AgentStatus


class CoordinatorAgent(BaseAgent):
    """
    协调者Agent - 黑客团队领导
    
    职责：
    1. 分析渗透测试目标，制定攻击策略
    2. 协调各个专业Agent的工作
    3. 监控任务进度，处理异常情况
    4. 整合各Agent的结果，做出决策
    5. 优化攻击路径，提高效率
    """
    
    AGENT_TYPE = "coordinator"
    
    SYSTEM_PROMPT = """你是一个经验丰富的渗透测试团队负责人（Red Team Lead），负责协调和指挥整个渗透测试行动。

## 你的角色定位
你就像一个黑客团队的领导者，拥有以下特质：
- 战略思维：能够从全局角度规划攻击路线
- 技术精通：了解各种攻击技术和防御机制
- 团队协作：善于分配任务和协调资源
- 快速决策：能够在信息不完整时做出正确判断
- 风险管理：评估攻击风险，确保安全可控

## 你管理的团队
1. **ReconAgent（侦察专家）**：负责信息收集，发现目标资产和潜在入口
2. **VulnAgent（漏洞分析师）**：负责漏洞扫描和评估，识别可利用的弱点
3. **ExploitAgent（攻击专家）**：负责漏洞利用，获取系统访问权限
4. **ReportAgent（报告专家）**：负责记录和报告，生成专业的测试报告

## 工作流程
1. **目标分析**：分析目标类型、可能的防御措施、潜在攻击面
2. **策略制定**：根据目标特点选择最优攻击路径
3. **任务分配**：合理分配任务给各个专业Agent
4. **进度监控**：实时监控各Agent的执行状态
5. **结果整合**：整合各Agent的发现，做出下一步决策
6. **风险控制**：评估操作风险，必要时调整策略

## 决策原则
- 优先选择成功率高、风险低的攻击路径
- 根据实时发现的信息动态调整策略
- 遇到障碍时快速切换备选方案
- 保持攻击的隐蔽性，避免触发告警
- 详细记录所有操作和发现

## 输出格式
请始终使用结构化的JSON格式输出你的决策和指令：

```json
{
  "situation_analysis": "当前情况分析",
  "attack_strategy": "攻击策略",
  "task_assignments": [
    {
      "agent": "recon|vuln|exploit|report",
      "task": "具体任务描述",
      "priority": "high|medium|low",
      "dependencies": ["依赖的任务ID"],
      "expected_output": "预期输出"
    }
  ],
  "risk_assessment": {
    "level": "low|medium|high",
    "factors": ["风险因素"],
    "mitigations": ["缓解措施"]
  },
  "next_steps": ["下一步行动"],
  "notes": "备注信息"
}
```

记住：你是一个专业、高效、有战略眼光的团队领导者！"""

    def __init__(self, llm_client, team_agents: Dict = None, **kwargs):
        super().__init__(llm_client, **kwargs)
        self.team_agents = team_agents or {}  # 团队成员Agent
        self.task_queue: List[Dict] = []  # 任务队列
        self.execution_plan: Dict = {}  # 执行计划
        self.progress: Dict = {}  # 进度跟踪
        self.findings: List[Dict] = []  # 发现收集
        
    def register_agent(self, agent_name: str, agent: BaseAgent):
        """注册团队成员Agent"""
        self.team_agents[agent_name] = agent
        self.add_log(f"注册团队成员: {agent_name}")
    
    def execute(self, task: Task) -> AgentResult:
        """执行协调任务"""
        target = task.input_data.get("target")
        mode = task.input_data.get("mode", "auto")  # auto, semi, manual
        
        if not target:
            return AgentResult(success=False, error="未指定目标")
        
        self.add_log(f"开始协调渗透测试: {target}")
        
        # 1. 分析目标并制定策略
        strategy = self._analyze_and_plan(target, task.input_data)
        self.execution_plan = strategy
        self.add_log(f"攻击策略: {strategy.get('strategy_name', '综合攻击')}")
        
        # 2. 执行攻击计划
        results = self._execute_plan(target, strategy, mode)
        
        # 3. 整合结果并做出最终评估
        final_assessment = self._assess_results(results)
        
        return AgentResult(
            success=True,
            data={
                "target": target,
                "strategy": strategy,
                "execution_results": results,
                "final_assessment": final_assessment,
                "findings": self.findings
            },
            logs=self.execution_logs
        )
    
    def _analyze_and_plan(self, target: str, input_data: Dict) -> Dict:
        """分析目标并制定攻击计划"""
        prompt = f"""请分析以下渗透测试目标，并制定详细的攻击计划。

目标: {target}
额外信息: {json.dumps(input_data.get("extra_info", {}), ensure_ascii=False)}

请返回JSON格式的攻击计划：
{{
    "strategy_name": "策略名称",
    "target_type": "web|network|cloud|hybrid",
    "estimated_time": "预计时间",
    "phases": [
        {{
            "name": "阶段名称",
            "agent": "recon|vuln|exploit",
            "tasks": ["具体任务"],
            "parallel": true/false,
            "dependencies": ["依赖的阶段"]
        }}
    ],
    "priority_targets": ["优先攻击目标"],
    "backup_plans": ["备选方案"],
    "risk_level": "low|medium|high"
}}"""

        try:
            result = self.analyze_with_llm(
                prompt,
                require_json=True,
                json_schema={
                    "strategy_name": {"type": "string"},
                    "target_type": {"type": "string"},
                    "estimated_time": {"type": "string"},
                    "phases": {"type": "array", "items": {"type": "object"}},
                    "priority_targets": {"type": "array", "items": {"type": "string"}},
                    "backup_plans": {"type": "array", "items": {"type": "string"}},
                    "risk_level": {"type": "string"}
                }
            )
            return result
        except Exception as e:
            self.add_log(f"策略制定失败，使用默认策略: {e}", "WARNING")
            return self._default_strategy(target)
    
    def _default_strategy(self, target: str) -> Dict:
        """默认攻击策略"""
        return {
            "strategy_name": "标准渗透测试流程",
            "target_type": "unknown",
            "estimated_time": "2-4小时",
            "phases": [
                {
                    "name": "信息收集",
                    "agent": "recon",
                    "tasks": ["端口扫描", "服务识别", "Web指纹"],
                    "parallel": True,
                    "dependencies": []
                },
                {
                    "name": "漏洞分析",
                    "agent": "vuln",
                    "tasks": ["漏洞扫描", "CVE匹配", "风险评估"],
                    "parallel": False,
                    "dependencies": ["信息收集"]
                },
                {
                    "name": "漏洞利用",
                    "agent": "exploit",
                    "tasks": ["漏洞利用尝试", "权限获取"],
                    "parallel": False,
                    "dependencies": ["漏洞分析"]
                },
                {
                    "name": "报告生成",
                    "agent": "report",
                    "tasks": ["生成测试报告"],
                    "parallel": False,
                    "dependencies": ["漏洞利用"]
                }
            ],
            "priority_targets": ["Web服务", "SSH服务", "数据库服务"],
            "backup_plans": ["暴力破解", "社工攻击"],
            "risk_level": "medium"
        }
    
    def _execute_plan(self, target: str, strategy: Dict, mode: str) -> Dict:
        """执行攻击计划"""
        results = {}
        phases = strategy.get("phases", [])
        
        for phase in phases:
            phase_name = phase.get("name")
            agent_name = phase.get("agent")
            tasks = phase.get("tasks", [])
            
            self.add_log(f"执行阶段: {phase_name}")
            self.progress[phase_name] = {"status": "running", "started_at": datetime.now().isoformat()}
            
            # 获取对应的Agent
            agent = self.team_agents.get(agent_name)
            if not agent:
                self.add_log(f"Agent {agent_name} 未注册，跳过阶段", "WARNING")
                continue
            
            # 创建并执行任务
            phase_results = []
            for task_desc in tasks:
                task = Task(
                    id=f"{agent_name}_{task_desc}_{int(datetime.now().timestamp())}",
                    name=task_desc,
                    description=f"{phase_name}: {task_desc}",
                    input_data={
                        "target": target,
                        "phase": phase_name,
                        "previous_results": results
                    }
                )
                
                try:
                    result = agent.run_task(task)
                    phase_results.append({
                        "task": task_desc,
                        "success": result.success,
                        "data": result.data,
                        "logs": result.logs[:10]  # 限制日志长度
                    })
                    
                    # 收集发现
                    if result.success and result.data:
                        self._collect_findings(phase_name, result.data)
                        
                except Exception as e:
                    self.add_log(f"任务执行失败 {task_desc}: {e}", "ERROR")
                    phase_results.append({
                        "task": task_desc,
                        "success": False,
                        "error": str(e)
                    })
            
            results[phase_name] = phase_results
            self.progress[phase_name]["status"] = "completed"
            self.progress[phase_name]["completed_at"] = datetime.now().isoformat()
            
            # 分析结果并决定是否继续
            if not self._should_continue(results, phase):
                self.add_log(f"根据阶段结果，决定终止后续阶段", "WARNING")
                break
        
        return results
    
    def _collect_findings(self, phase: str, data: Dict):
        """收集发现"""
        finding = {
            "phase": phase,
            "timestamp": datetime.now().isoformat(),
            "data": data
        }
        self.findings.append(finding)
    
    def _should_continue(self, results: Dict, current_phase: Dict) -> bool:
        """判断是否应该继续执行"""
        # 检查是否有严重错误
        phase_name = current_phase.get("name")
        phase_results = results.get(phase_name, [])
        
        # 如果所有任务都失败，考虑停止
        if all(not r.get("success", False) for r in phase_results):
            # 但如果是信息收集阶段失败，可能目标不可达，应该停止
            if phase_name == "信息收集":
                return False
        
        return True
    
    def _assess_results(self, results: Dict) -> Dict:
        """评估最终结果"""
        prompt = f"""请评估以下渗透测试结果，并提供最终评估报告。

测试结果:
{json.dumps(results, ensure_ascii=False, indent=2)}

发现列表:
{json.dumps(self.findings, ensure_ascii=False, indent=2)}

请返回JSON格式的评估报告：
{{
    "overall_status": "success|partial|failed",
    "vulnerabilities_found": 数量,
    "high_risk_vulnerabilities": 数量,
    "access_obtained": "none|user|root|system",
    "key_findings": ["关键发现"],
    "recommendations": ["安全建议"],
    "risk_level": "critical|high|medium|low",
    "summary": "总结描述"
}}"""

        try:
            return self.analyze_with_llm(
                prompt,
                require_json=True,
                json_schema={
                    "overall_status": {"type": "string"},
                    "vulnerabilities_found": {"type": "number"},
                    "high_risk_vulnerabilities": {"type": "number"},
                    "access_obtained": {"type": "string"},
                    "key_findings": {"type": "array", "items": {"type": "string"}},
                    "recommendations": {"type": "array", "items": {"type": "string"}},
                    "risk_level": {"type": "string"},
                    "summary": {"type": "string"}
                }
            )
        except Exception as e:
            self.add_log(f"结果评估失败: {e}", "WARNING")
            return {
                "overall_status": "partial",
                "summary": "测试完成，但结果评估失败",
                "error": str(e)
            }
    
    def get_progress(self) -> Dict:
        """获取当前进度"""
        return {
            "execution_plan": self.execution_plan,
            "progress": self.progress,
            "findings_count": len(self.findings),
            "current_phase": self._get_current_phase()
        }
    
    def _get_current_phase(self) -> str:
        """获取当前执行阶段"""
        for phase_name, status in self.progress.items():
            if status.get("status") == "running":
                return phase_name
        return "completed"
    
    def delegate_task(self, agent_name: str, task: Task) -> AgentResult:
        """委派任务给指定Agent"""
        agent = self.team_agents.get(agent_name)
        if not agent:
            return AgentResult(success=False, error=f"Agent {agent_name} 未注册")
        
        self.add_log(f"委派任务给 {agent_name}: {task.name}")
        return agent.run_task(task)
    
    def broadcast_update(self, message: str, level: str = "INFO"):
        """广播更新消息"""
        self.add_log(f"[广播] {message}", level)
        # 可以扩展为实际的通知机制

    def plan_phase_round(self, target: str, phase: str, context: Dict = None) -> Dict:
        """为当前阶段生成一轮协作计划"""
        context = context or {}
        prompt = f"""请为当前渗透测试阶段制定一轮多智能体协作计划。

目标: {target}
阶段: {phase}
上下文:
{json.dumps(context, ensure_ascii=False, indent=2)}

请返回 JSON：
{{
  "goal": "本轮目标",
  "focus_points": ["本轮关注点"],
  "assignments": [
    {{
      "agent": "recon|vuln|exploit|report",
      "instruction": "发送给该Agent的任务指令",
      "expected_output": "预期产出"
    }}
  ]
}}"""
        try:
            return self.analyze_with_llm(
                prompt,
                require_json=True,
                json_schema={
                    "goal": {"type": "string"},
                    "focus_points": {"type": "array", "items": {"type": "string"}},
                    "assignments": {"type": "array", "items": {"type": "object"}}
                }
            )
        except Exception as e:
            self.add_log(f"阶段协作计划生成失败，使用默认计划: {e}", "WARNING")
            return self._default_round_plan(phase)

    def review_phase_round(
        self,
        target: str,
        phase: str,
        context: Dict = None,
        phase_result: Dict = None
    ) -> Dict:
        """评估本轮结果并判断是否继续下一轮"""
        context = context or {}
        phase_result = phase_result or {}
        prompt = f"""请评估当前阶段的一轮协作结果，判断是否需要继续追问或补充证据。

目标: {target}
阶段: {phase}
上下文:
{json.dumps(context, ensure_ascii=False, indent=2)}

阶段结果:
{json.dumps(phase_result, ensure_ascii=False, indent=2)}

请返回 JSON：
{{
  "should_continue": true,
  "summary": "本轮总结",
  "follow_up_question": "如果继续，下一轮核心问题",
  "next_recipient": "recon|vuln|exploit|report",
  "completion_message": "如果结束，该阶段的结论"
}}"""
        try:
            return self.analyze_with_llm(
                prompt,
                require_json=True,
                json_schema={
                    "should_continue": {"type": "boolean"},
                    "summary": {"type": "string"},
                    "follow_up_question": {"type": "string"},
                    "next_recipient": {"type": "string"},
                    "completion_message": {"type": "string"}
                }
            )
        except Exception as e:
            self.add_log(f"阶段结果评估失败，使用默认评估: {e}", "WARNING")
            return {
                "should_continue": False,
                "summary": f"{phase} 阶段已完成初步协作",
                "follow_up_question": "",
                "next_recipient": "",
                "completion_message": f"{phase} 阶段暂无进一步追问"
            }

    def _default_round_plan(self, phase: str) -> Dict:
        """默认轮次计划"""
        defaults = {
            "recon": {
                "goal": "收集目标基础情报并确认攻击面",
                "focus_points": ["开放端口", "服务识别", "基础指纹"],
                "assignments": [
                    {
                        "agent": "recon",
                        "instruction": "收集端口、服务、OS 与 Web 指纹信息，并整理成结构化情报",
                        "expected_output": "攻击面和基础资产画像"
                    }
                ]
            },
            "vuln": {
                "goal": "基于侦察结果提出并验证关键漏洞假设",
                "focus_points": ["高风险服务", "Web入口", "已知版本风险"],
                "assignments": [
                    {
                        "agent": "vuln",
                        "instruction": "结合侦察结果分析最值得优先验证的漏洞",
                        "expected_output": "漏洞假设和风险评估"
                    }
                ]
            },
            "exploit": {
                "goal": "评估已识别漏洞的利用路径",
                "focus_points": ["可利用性", "影响范围", "利用前提"],
                "assignments": [
                    {
                        "agent": "exploit",
                        "instruction": "评估漏洞利用链并给出验证建议",
                        "expected_output": "利用结论和影响分析"
                    }
                ]
            },
            "report": {
                "goal": "整合阶段结果并生成最终报告",
                "focus_points": ["证据链", "风险评级", "修复建议"],
                "assignments": [
                    {
                        "agent": "report",
                        "instruction": "汇总所有阶段产出，整理成面向用户的报告",
                        "expected_output": "结构化测试报告"
                    }
                ]
            }
        }
        return defaults.get(phase, {
            "goal": f"{phase} 阶段协作",
            "focus_points": [],
            "assignments": []
        })
    
    def get_capabilities(self) -> List[str]:
        """获取能力列表"""
        return [
            "团队协调",
            "任务分配",
            "策略制定",
            "进度监控",
            "结果整合",
            "风险评估",
            "决策支持"
        ]
