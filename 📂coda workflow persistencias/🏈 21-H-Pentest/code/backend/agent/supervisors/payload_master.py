"""
Payload Master - Payload变种测试管理器
"""
from typing import Dict, Any, List, Optional


class PayloadMaster:
    """Payload变种大师"""
    
    def __init__(self, output_manager, llm_client=None):
        """
        初始化Payload大师
        
        Args:
            output_manager: 输出管理器
            llm_client: LLM客户端（用于分析对话）
        """
        self.output = output_manager
        self.llm = llm_client
        self.payload_tests = []
    
    def record_payload_test(self, payload: str, result: str, success: bool = False, vuln_type: str = 'unknown'):
        """
        记录Payload测试结果
        
        Args:
            payload: 测试的payload
            result: 测试结果
            success: 是否成功
            vuln_type: 漏洞类型
        """
        import time
        self.payload_tests.append({
            'payload': payload,
            'result': result,
            'success': success,
            'vuln_type': vuln_type,
            'timestamp': time.time()
        })
        print(f"📝 记录Payload测试: {payload[:50]}... -> {'成功' if success else '失败'}")
    
    def get_tested_payloads(self, vuln_type: str = None) -> List[str]:
        """获取已测试的payloads"""
        if vuln_type:
            return [t['payload'] for t in self.payload_tests if t['vuln_type'] == vuln_type]
        return [t['payload'] for t in self.payload_tests]
    
    def should_provide_guidance(self, current_round: int) -> bool:
        """判断是否应该提供payload指导"""
        # 每3轮提供一次指导
        return current_round > 0 and current_round % 3 == 0
    
    async def generate_payload_guidance(self, conversation_history: list = None, round_num: int = 0) -> Dict[str, Any]:
        """
        生成Payload指导（🔥 使用LLM智能分析，生成真正有用的payload建议）
        
        Args:
            conversation_history: 完整对话历史
            round_num: 当前轮数
            
        Returns:
            指导信息
        """
        # 🔥🔥🔥 使用LLM智能分析对话，生成payload指导
        if self.llm and conversation_history:
            try:
                messages = conversation_history.copy()
                
                # 获取已测试的payload记录
                tested_summary = "\n".join([f"- {t['payload']} ({t['vuln_type']}): {'成功' if t['success'] else '失败'}" 
                                            for t in self.payload_tests[-10:]])  # 最近10条
                
                prompt = f"""作为Payload变种专家，分析Worker的测试进度，提供智能的payload建议。

已测试的payload记录：
{tested_summary if tested_summary else '暂无测试记录'}

请分析：
1. Worker当前正在测试什么漏洞类型？
2. 应该提供什么样的payload建议？
3. 如何进化/变种才能绕过防护？

以JSON格式输出：
{{
    "should_provide_guidance": true/false,
    "vuln_type": "sqli/xss/command_injection/file_upload/lfi等",
    "reason": "为什么提供这些建议",
    "payloads": ["具体的payload1", "具体的payload2", ...],
    "evolution_note": "进化思路说明（50字内）"
}}

**重要**：
1. 只输出JSON，不要额外说明
2. 如果Worker还没开始测试具体漏洞，should_provide_guidance=false
3. payloads要具体可用，不要模板占位符
4. evolution_note要有实际指导价值
"""
                messages.append({'role': 'user', 'content': prompt})
                
                response = await self.llm.chat(
                    messages=messages, 
                    temperature=0.7,  # TODO: 从配置读取
                    stream=True,  # 🔥 全流式输出
                    response_format={"type": "json_object"}  # 🔥 强制JSON输出
                )
                
                # 解析JSON
                import json
                content = response.get('content', '{}')
                
                # 🔥 输出LLM原始响应，方便调试
                self.output.log("debug", f"📦 Payload Master LLM原始响应: {content[:500]}...")
                
                # 🔥🔥🔥 清理非JSON内容（LLM可能输出思考过程或工具调用）
                # 1. 移除</think>之后的所有内容
                if '</think>' in content:
                    content = content.split('</think>')[0]
                # 2. 移除<think>标签
                if '<think>' in content:
                    content = content.replace('<think>', '')
                # 3. 移除```json代码块标记
                if '```json' in content:
                    content = content.split('```json')[1].split('```')[0].strip()
                elif '```' in content:
                    content = content.split('```')[1].split('```')[0].strip()
                
                # 🔥 去除首尾空白
                content = content.strip()
                
                # 🔥 尝试修复常见的JSON转义问题
                # 1. 替换单反斜杠为双反斜杠（除了合法的转义序列）
                # 2. 但保留 \n \r \t \" \\ 等合法转义
                import re
                # 先保护合法的转义序列
                content = content.replace('\\', '\\\\')  # \\ -> \\\\
                content = content.replace('\\\\n', '\\n')  # 恢复 \n
                content = content.replace('\\\\r', '\\r')  # 恢复 \r
                content = content.replace('\\\\t', '\\t')  # 恢复 \t
                content = content.replace('\\\\"', '\\"')  # 恢复 \"
                
                result = json.loads(content)
                
                # 如果不应该提供指导，返回空
                if not result.get('should_provide_guidance', False):
                    self.output.log("info", f"ℹ️  Payload Master: {result.get('reason', '当前无需提供指导')}")
                    return {'suggested_payloads': []}
                
                vuln_type = result.get('vuln_type', 'unknown')
                payloads = result.get('payloads', [])
                evolution_note = result.get('evolution_note', '基于对话分析生成的建议')
                
                self.output.log("success", f"🎯 检测到漏洞类型: {vuln_type}")
                
                # 获取已测试的payload
                tested_payloads = self.get_tested_payloads(vuln_type)
                
                # 过滤已测试的
                suggested_payloads = [p for p in payloads if p not in tested_payloads][:5]
                
                guidance = {
                    'vuln_type': vuln_type,
                    'tested_payloads': tested_payloads,
                    'suggested_payloads': suggested_payloads,
                    'evolution_note': evolution_note
                }
                
                # 广播到前端
                self.output.payload_guidance(
                    vuln_type=vuln_type,
                    payloads=payloads,
                    tested_payloads=tested_payloads,
                    suggested_payloads=suggested_payloads,
                    evolution_note=evolution_note,
                    round_num=round_num
                )
                
                return guidance
                
            except json.JSONDecodeError as je:
                self.output.log("error", f"⚠️  JSON解析失败: {je}")
                self.output.log("debug", f"📦 问题的JSON内容: {content}")
                return {'suggested_payloads': []}
            except Exception as e:
                self.output.log("warning", f"⚠️  LLM生成指导失败: {e}")
                import traceback
                traceback.print_exc()
                return {'suggested_payloads': []}
        else:
            # 没有LLM，返回空
            return {'suggested_payloads': []}
    
    def format_status(self) -> str:
        """格式化Payload大师状态"""
        if not self.payload_tests:
            return "暂无Payload测试记录"
        
        total = len(self.payload_tests)
        success = sum(1 for t in self.payload_tests if t['success'])
        
        return f"Payload测试统计: 总计{total}个, 成功{success}个, 成功率{success/total*100:.1f}%"
