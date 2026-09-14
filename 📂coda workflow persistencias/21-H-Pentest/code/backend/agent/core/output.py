"""
Output Manager - 统一管理所有输出到Queue
"""
from multiprocessing import Queue
from typing import Any, Dict


class OutputManager:
    """输出管理器 - 所有输出通过Queue发送到主进程"""
    
    def __init__(self, task_id: str, message_queue: Queue):
        self.task_id = task_id
        self.queue = message_queue
    
    def _send(self, msg_type: str, data: Dict[str, Any]):
        """发送消息到队列"""
        try:
            self.queue.put({
                'type': msg_type,
                'data': data,
                'task_id': self.task_id
            }, block=False)
        except Exception as e:
            print(f"⚠️  发送消息失败: {e}")
    
    def log(self, level: str, content: str):
        """发送日志"""
        self._send('log', {
            'level': level,
            'content': content
        })
    
    def progress(self, current: int, total: int, status: str, message: str = ''):
        """发送进度"""
        self._send('progress', {
            'current': current,
            'total': total,
            'status': status,
            'message': message
        })
    
    def llm_thinking(self, content: str, round_num: int):
        """发送LLM思考内容"""
        self._send('llm_thinking', {
            'content': content,
            'round': round_num
        })
    
    def llm_stream(self, chunk: str):
        """发送LLM流式输出块（实时）"""
        self._send('llm_stream', {
            'chunk': chunk
        })
    
    def tool_execution(self, tool_name: str, args: dict, result: str, round_num: int):
        """发送工具执行"""
        self._send('tool_execution', {
            'tool_name': tool_name,
            'args': args,
            'result': result,
            'round': round_num
        })
    
    def vulnerability(self, vuln: dict):
        """发送漏洞（已弃用，使用vulnerability_found）"""
        self.vulnerability_found(vuln)
    
    def vulnerability_found(self, vuln: dict):
        """🔥 发送漏洞发现消息（前端期望的格式）"""
        self._send('vulnerability', {
            'vulnerability': vuln  # 🔥 前端期望在vulnerability字段中
        })
    
    def flag(self, flag_value: str):
        """发送FLAG"""
        self._send('flag', {
            'flag': flag_value
        })
    
    def plan(self, plan_data: dict):
        """发送计划"""
        self._send('plan', plan_data)
    
    def strategic(self, analysis: dict, round_num: int):
        """发送战略分析"""
        self._send('strategic_analysis', {  # 🔥 修复类型名称
            **analysis,
            'round': round_num
        })
    
    def meta_insights(self, insights: list, round_num: int):
        """🔥 发送Meta监督洞察（卡片显示）"""
        # 🔥🔥🔥 前端期望的完整格式
        self._send('meta_supervision', {
            'insights': insights,
            'round': round_num,
            'intervention_needed': False,  # 🔥 默认不需要干预
            'reason': None,                # 🔥 分析原因（可选）
            'guidance_message': '\n'.join(insights),  # 🔥 指导消息
            'intervention_type': None      # 🔥 干预类型（可选）
        })
    
    def payload_injection(self, payload: str, context: str, round_num: int):
        """🔥 发送Payload注入信息（卡片显示）"""
        self._send('payload', {
            'payload': payload,
            'context': context,
            'round': round_num,
            'type': 'payload_injection'
        })
    
    def payload_guidance(self, vuln_type: str, payloads: list, tested_payloads: list, suggested_payloads: list, evolution_note: str, round_num: int):
        """🔥🔥🔥 发送Payload大师指导（卡片显示）"""
        self._send('payload_guidance', {
            'vuln_type': vuln_type,
            'payloads': payloads,
            'tested_payloads': tested_payloads,
            'suggested_payloads': suggested_payloads,
            'evolution_note': evolution_note,
            'round': round_num
        })
    
    def intervention(self, instruction: str, priority: str):
        """🔥 发送人工干预指令（卡片显示）"""
        self._send('intervention', {
            'instruction': instruction,
            'priority': priority,
            'type': 'human_intervention'
        })
    
    def conversation_message(self, role: str, content: str, tool_calls: list = None, tool_call_id: str = None, tool_name: str = None, round_num: int = 0):
        """🔥🔥🔥 发送对话消息（user/assistant/tool）到前端显示"""
        data = {
            'role': role,
            'content': content or '',
            'round': round_num
        }
        
        # assistant的工具调用
        if role == 'assistant' and tool_calls:
            data['tool_calls'] = tool_calls
            data['has_tool_calls'] = True
        
        # tool的响应
        if role == 'tool':
            data['tool_call_id'] = tool_call_id
            data['tool_name'] = tool_name
        
        self._send('conversation_message', data)
