"""
决策引擎
基于LLM的智能决策系统
"""
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import json

from llm import BaseLLMClient, Message


class DecisionType(Enum):
    """决策类型"""
    NEXT_STEP = "next_step"
    TOOL_SELECTION = "tool_selection"
    VULN_PRIORITIZATION = "vuln_prioritization"
    EXPLOIT_STRATEGY = "exploit_strategy"
    RISK_ASSESSMENT = "risk_assessment"


@dataclass
class Decision:
    """决策结果"""
    decision_type: DecisionType
    action: str
    reasoning: str
    confidence: float
    alternatives: List[str]
    metadata: Dict


class DecisionEngine:
    """
    决策引擎
    使用LLM进行智能决策
    """

    def __init__(self, llm_client: BaseLLMClient):
        self.llm_client = llm_client
        self.decision_history: List[Decision] = []

    def decide_next_step(
        self,
        current_phase: str,
        results: Dict,
        context: Dict = None
    ) -> Decision:
        """
        决定下一步行动

        Args:
            current_phase: 当前阶段
            results: 当前结果
            context: 上下文信息

        Returns:
            Decision
        """
        prompt = self._build_next_step_prompt(current_phase, results, context)

        try:
            response = self._get_llm_decision(prompt, DecisionType.NEXT_STEP)
            decision = Decision(
                decision_type=DecisionType.NEXT_STEP,
                action=response.get("action", "continue"),
                reasoning=response.get("reasoning", ""),
                confidence=response.get("confidence", 0.5),
                alternatives=response.get("alternatives", []),
                metadata=response
            )
        except Exception:
            decision = Decision(
                decision_type=DecisionType.NEXT_STEP,
                action="continue",
                reasoning="默认继续",
                confidence=0.5,
                alternatives=[],
                metadata={}
            )

        self.decision_history.append(decision)
        return decision

    def select_tools(
        self,
        target_type: str,
        services: List[str],
        objective: str
    ) -> Decision:
        """
        选择合适的工具

        Args:
            target_type: 目标类型
            services: 发现的服务
            objective: 目标

        Returns:
            Decision
        """
        prompt = f"""请根据以下信息选择最合适的安全工具。

目标类型: {target_type}
发现的服务: {', '.join(services)}
测试目标: {objective}

可用工具:
- nmap: 端口扫描、服务识别、OS检测
- nikto: Web漏洞扫描
- dirb: 目录枚举
- hydra: 暴力破解
- searchsploit: 漏洞利用搜索
- web_scanner: Web应用扫描

请返回JSON格式：
{{
    "selected_tools": ["工具列表"],
    "reasoning": "选择理由",
    "execution_order": ["执行顺序"],
    "confidence": 0.0-1.0
}}"""

        try:
            response = self._get_llm_decision(prompt, DecisionType.TOOL_SELECTION)
            decision = Decision(
                decision_type=DecisionType.TOOL_SELECTION,
                action=",".join(response.get("selected_tools", [])),
                reasoning=response.get("reasoning", ""),
                confidence=response.get("confidence", 0.5),
                alternatives=[],
                metadata={"execution_order": response.get("execution_order", [])}
            )
        except Exception:
            # 默认工具选择
            default_tools = self._default_tool_selection(target_type, services)
            decision = Decision(
                decision_type=DecisionType.TOOL_SELECTION,
                action=",".join(default_tools),
                reasoning="默认工具选择",
                confidence=0.5,
                alternatives=[],
                metadata={}
            )

        self.decision_history.append(decision)
        return decision

    def prioritize_vulnerabilities(
        self,
        vulnerabilities: List[Dict]
    ) -> Decision:
        """
        漏洞优先级排序

        Args:
            vulnerabilities: 漏洞列表

        Returns:
            Decision
        """
        if not vulnerabilities:
            return Decision(
                decision_type=DecisionType.VULN_PRIORITIZATION,
                action="no_vulnerabilities",
                reasoning="未发现漏洞",
                confidence=1.0,
                alternatives=[],
                metadata={}
            )

        vuln_summary = "\n".join([
            f"- {v.get('name', 'Unknown')} ({v.get('severity', 'unknown')}): {v.get('cve', 'N/A')}"
            for v in vulnerabilities[:15]
        ])

        prompt = f"""请对以下漏洞进行优先级排序。

漏洞列表:
{vuln_summary}

请考虑:
1. 漏洞严重性
2. 可利用性
3. 影响范围
4. 利用复杂度

返回JSON格式：
{{
    "priority_order": ["按优先级排序的漏洞名称"],
    "top_priority": "最高优先级漏洞",
    "reasoning": "排序理由",
    "confidence": 0.0-1.0,
    "exploit_recommendations": ["利用建议"]
}}"""

        try:
            response = self._get_llm_decision(prompt, DecisionType.VULN_PRIORITIZATION)
            decision = Decision(
                decision_type=DecisionType.VULN_PRIORITIZATION,
                action=response.get("top_priority", vulnerabilities[0].get("name", "")),
                reasoning=response.get("reasoning", ""),
                confidence=response.get("confidence", 0.5),
                alternatives=response.get("priority_order", [])[:5],
                metadata={"recommendations": response.get("exploit_recommendations", [])}
            )
        except Exception:
            # 按严重性默认排序
            severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
            sorted_vulns = sorted(
                vulnerabilities,
                key=lambda x: severity_order.get(x.get("severity", "low"), 3)
            )
            decision = Decision(
                decision_type=DecisionType.VULN_PRIORITIZATION,
                action=sorted_vulns[0].get("name", "") if sorted_vulns else "",
                reasoning="按严重性排序",
                confidence=0.6,
                alternatives=[v.get("name", "") for v in sorted_vulns[:5]],
                metadata={}
            )

        self.decision_history.append(decision)
        return decision

    def determine_exploit_strategy(
        self,
        target: str,
        vulnerabilities: List[Dict],
        recon_data: Dict
    ) -> Decision:
        """
        确定漏洞利用策略

        Args:
            target: 目标
            vulnerabilities: 漏洞列表
            recon_data: 侦察数据

        Returns:
            Decision
        """
        services = recon_data.get("services", {})
        service_list = [
            f"{info.get('name', 'unknown')}:{port}"
            for port, info in services.items()
        ]

        prompt = f"""请分析以下目标，确定最佳的漏洞利用策略。

目标: {target}

服务:
{chr(10).join(service_list)}

漏洞:
{json.dumps([v.get('name', '') for v in vulnerabilities[:10]], indent=2)}

请返回JSON格式：
{{
    "primary_strategy": "主要策略",
    "exploit_chain": ["利用链步骤"],
    "expected_outcome": "预期结果",
    "risk_level": "low/medium/high",
    "confidence": 0.0-1.0,
    "alternative_strategies": ["备选策略"],
    "prerequisites": ["前置条件"]
}}"""

        try:
            response = self._get_llm_decision(prompt, DecisionType.EXPLOIT_STRATEGY)
            decision = Decision(
                decision_type=DecisionType.EXPLOIT_STRATEGY,
                action=response.get("primary_strategy", ""),
                reasoning=response.get("expected_outcome", ""),
                confidence=response.get("confidence", 0.5),
                alternatives=response.get("alternative_strategies", []),
                metadata={
                    "exploit_chain": response.get("exploit_chain", []),
                    "risk_level": response.get("risk_level", "medium"),
                    "prerequisites": response.get("prerequisites", [])
                }
            )
        except Exception:
            decision = Decision(
                decision_type=DecisionType.EXPLOIT_STRATEGY,
                action="尝试已知漏洞利用",
                reasoning="默认策略",
                confidence=0.5,
                alternatives=["暴力破解"],
                metadata={}
            )

        self.decision_history.append(decision)
        return decision

    def assess_risk(
        self,
        vulnerabilities: List[Dict],
        exploits: List[Dict]
    ) -> Decision:
        """
        风险评估

        Args:
            vulnerabilities: 漏洞列表
            exploits: 成功利用列表

        Returns:
            Decision
        """
        severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        for vuln in vulnerabilities:
            severity = vuln.get("severity", "low").lower()
            if severity in severity_counts:
                severity_counts[severity] += 1

        prompt = f"""请评估以下安全风险。

漏洞统计:
- 严重: {severity_counts['critical']}
- 高危: {severity_counts['high']}
- 中危: {severity_counts['medium']}
- 低危: {severity_counts['low']}

成功利用: {len(exploits)} 个

请返回JSON格式：
{{
    "risk_level": "critical/high/medium/low",
    "risk_score": 0-100,
    "business_impact": "业务影响描述",
    "likelihood": "low/medium/high",
    "immediate_actions": ["立即行动"],
    "confidence": 0.0-1.0
}}"""

        try:
            response = self._get_llm_decision(prompt, DecisionType.RISK_ASSESSMENT)
            decision = Decision(
                decision_type=DecisionType.RISK_ASSESSMENT,
                action=response.get("risk_level", "medium"),
                reasoning=response.get("business_impact", ""),
                confidence=response.get("confidence", 0.5),
                alternatives=response.get("immediate_actions", []),
                metadata={
                    "risk_score": response.get("risk_score", 50),
                    "likelihood": response.get("likelihood", "medium")
                }
            )
        except Exception:
            # 计算简单风险评分
            score = (
                severity_counts["critical"] * 25 +
                severity_counts["high"] * 15 +
                severity_counts["medium"] * 5 +
                severity_counts["low"] * 1 +
                len(exploits) * 20
            )
            level = "critical" if score >= 50 else "high" if score >= 30 else "medium" if score >= 10 else "low"

            decision = Decision(
                decision_type=DecisionType.RISK_ASSESSMENT,
                action=level,
                reasoning=f"风险评分: {score}",
                confidence=0.6,
                alternatives=[],
                metadata={"risk_score": score}
            )

        self.decision_history.append(decision)
        return decision

    def _build_next_step_prompt(
        self,
        current_phase: str,
        results: Dict,
        context: Dict
    ) -> str:
        """构建下一步决策提示"""
        context_str = json.dumps(context, ensure_ascii=False, indent=2) if context else "无"

        return f"""请根据当前测试进度，决定下一步行动。

当前阶段: {current_phase}

当前结果摘要:
{json.dumps(results, ensure_ascii=False, indent=2)[:1000]}

上下文信息:
{context_str}

可选行动:
- continue: 继续当前阶段
- next_phase: 进入下一阶段
- retry: 重试当前操作
- skip: 跳过当前阶段
- stop: 停止测试

请返回JSON格式：
{{
    "action": "选择的行动",
    "reasoning": "决策理由",
    "confidence": 0.0-1.0,
    "alternatives": ["其他可选行动"],
    "additional_info": "补充信息"
}}"""

    def _get_llm_decision(
        self,
        prompt: str,
        decision_type: DecisionType
    ) -> Dict:
        """获取LLM决策"""
        messages = [Message("user", prompt)]

        system_prompt = f"""你是一个专业的渗透测试决策专家。
你需要根据提供的测试信息做出最佳决策。
请始终返回有效的JSON格式。"""

        response = self.llm_client.chat(
            messages,
            system_prompt=system_prompt
        )

        # 解析JSON响应
        content = response.content

        # 尝试提取JSON
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]

        return json.loads(content.strip())

    def _default_tool_selection(
        self,
        target_type: str,
        services: List[str]
    ) -> List[str]:
        """默认工具选择"""
        tools = ["nmap"]

        if "http" in target_type.lower() or any("http" in s.lower() for s in services):
            tools.extend(["nikto", "dirb"])

        if "ssh" in services:
            tools.append("hydra")

        if "smb" in services:
            tools.append("searchsploit")

        return tools

    def get_decision_history(self) -> List[Dict]:
        """获取决策历史"""
        return [
            {
                "type": d.decision_type.value,
                "action": d.action,
                "reasoning": d.reasoning,
                "confidence": d.confidence,
                "timestamp": d.metadata.get("timestamp", "")
            }
            for d in self.decision_history
        ]

    def clear_history(self):
        """清空决策历史"""
        self.decision_history.clear()
