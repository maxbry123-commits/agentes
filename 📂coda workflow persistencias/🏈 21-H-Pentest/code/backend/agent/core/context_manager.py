"""
Context Manager - 基于LangChain的上下文管理和压缩
"""
from typing import List, Dict, Any
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema import HumanMessage, AIMessage, SystemMessage
import tiktoken
import re


class ContextManager:
    """上下文管理器 - 智能压缩和优先级管理"""
    
    def __init__(self, model: str = None, max_tokens: int = 8000):  # 🔥 禁止硬编码
        # 🔥🔥🔥 只从config.json加载，不读取环境变量
        if not model:
            try:
                from app.core.config import settings
                model = settings.CONTEXT_MODEL or settings.OPENAI_MODEL_MINI
            except Exception as e:
                raise ValueError(f"⚠️  未配置压缩模型！请检查 config.json: {e}")
        
        self.model = model
        self.max_tokens = max_tokens
        
        # 🔥 初始化 tokenizer（容错处理，避免网络请求）
        try:
            # 🔥🔥🔥 使用本地缓存的tokenizer，避免网络下载
            import os
            os.environ['TIKTOKEN_CACHE_DIR'] = '/tmp/tiktoken_cache'
            
            self.encoding = tiktoken.get_encoding("cl100k_base")
            # print('✅ Tokenizer 初始化成功: cl100k_base')  # 🔥 减少日志输出
        except Exception as e:
            # 🔥 网络失败时静默回退，不打印警告（避免干扰）
            # print(f'⚠️ Tokenizer 初始化失败: {e}，使用简单估算')
            self.encoding = None
        
        # LangChain LLM用于总结
        # 🔥🔥🔥 从 config.json 获取API配置
        try:
            from app.core.config import settings
            api_key = settings.OPENAI_API_KEY
            base_url = settings.OPENAI_BASE_URL
            
            if not api_key or not base_url:
                raise ValueError("⚠️  config.json 中缺少 api_key 或 base_url")
            
            # 🔥 静默初始化，不打印日志（由Agent统一打印）
            # print(f"✅ ContextManager初始化: model={model}, base_url={base_url}")
            
        except Exception as e:
            raise ValueError(f"⚠️  加载配置失败: {e}")
        
        self.summarizer = ChatOpenAI(
            model=model,
            temperature=0.3,
            max_tokens=500,
            api_key=api_key,
            base_url=base_url
        )
    
    def count_tokens(self, text: str) -> int:
        """计算token数量（智能估算）"""
        if not self.encoding:
            # 简单估算：1 token ≈ 4 characters (英文) 或 1.5 characters (中文)
            chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
            other_chars = len(text) - chinese_chars
            return int(chinese_chars / 1.5 + other_chars / 4)
        
        try:
            return len(self.encoding.encode(text))
        except Exception:
            # 备用方案
            return len(text) // 4
    
    def count_messages_tokens(self, messages: List[Dict[str, str]]) -> int:
        """计算消息列表的总token数"""
        total = 0
        for msg in messages:
            # role和content的token
            total += self.count_tokens(msg.get('role', ''))
            total += self.count_tokens(msg.get('content', ''))
            # 消息格式开销
            total += 4
        return total
    
    async def compress_messages(
        self, 
        messages: List[Dict[str, str]],
        target_tokens: int = None
    ) -> List[Dict[str, str]]:
        """
        压缩消息历史
        
        策略：
        1. 保留system消息
        2. 保留最近N条消息
        3. 中间部分通过LLM总结压缩
        """
        if target_tokens is None:
            target_tokens = self.max_tokens
        
        current_tokens = self.count_messages_tokens(messages)
        
        # 如果不需要压缩
        if current_tokens <= target_tokens:
            return messages
        
        print(f"🗜️  开始压缩: {current_tokens} -> {target_tokens} tokens")
        
        # 分离不同类型消息
        system_msgs = [m for m in messages if m.get('role') == 'system']
        other_msgs = [m for m in messages if m.get('role') != 'system']
        
        if len(other_msgs) <= 4:
            return messages  # 太少不压缩
        
        # 保留最新的4条
        recent_msgs = other_msgs[-4:]
        middle_msgs = other_msgs[:-4]
        
        # 压缩中间部分
        compressed = await self._compress_middle(middle_msgs)
        
        result = system_msgs + compressed + recent_msgs
        
        new_tokens = self.count_messages_tokens(result)
        print(f"✅ 压缩完成: {len(messages)} -> {len(result)} 条消息, {new_tokens} tokens")
        
        return result
    
    async def _compress_middle(self, messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """压缩中间消息"""
        if not messages:
            return []
        
        # 构建要总结的文本
        text_to_summarize = "\n\n".join([
            f"[{msg['role']}]: {msg['content'][:500]}"  # 限制每条长度
            for msg in messages
        ])
        
        # 使用LangChain总结
        summary_prompt = ChatPromptTemplate.from_messages([
            ("system", """你是一个专业的渗透测试助手。请总结以下对话历史，保留关键信息：
- 已执行的工具和命令
- 发现的漏洞和重要结果
- 下一步计划

要求：简洁、关键信息不丢失、中文输出。"""),
            ("human", "请总结以下对话:\n\n{text}")
        ])
        
        try:
            chain = summary_prompt | self.summarizer
            response = await chain.ainvoke({"text": text_to_summarize})
            
            summary = response.content if hasattr(response, 'content') else str(response)
            
            return [{
                'role': 'assistant',
                'content': f"[历史总结 - {len(messages)}条消息]\n{summary}"
            }]
        
        except Exception as e:
            print(f"⚠️  总结失败: {e}, 使用简单截断")
            # 降级方案：简单截断
            return [{
                'role': 'assistant',
                'content': f"[历史消息 - 已压缩{len(messages)}条]"
            }]
    
    def prioritize_messages(
        self, 
        messages: List[Dict[str, str]], 
        priorities: Dict[str, float]
    ) -> List[Dict[str, str]]:
        """
        基于优先级排序消息
        
        priorities: {message_id: priority_score}
        高优先级：漏洞发现、FLAG、工具成功执行
        低优先级：重复信息、失败尝试
        """
        # 为每条消息计算优先级分数
        scored = []
        for i, msg in enumerate(messages):
            content = msg.get('content', '').lower()
            
            # 基础分数
            score = 0.5
            
            # 系统消息最高优先级
            if msg.get('role') == 'system':
                score = 1.0
            
            # 最近的消息高优先级
            recency_bonus = (i / len(messages)) * 0.3
            score += recency_bonus
            
            # 内容重要性
            if any(kw in content for kw in ['flag', 'vuln', '漏洞', '成功']):
                score += 0.3
            
            if any(kw in content for kw in ['失败', 'error', '错误']):
                score -= 0.2
            
            scored.append((score, msg))
        
        # 按分数排序
        scored.sort(key=lambda x: x[0], reverse=True)
        
        return [msg for score, msg in scored]
    
    async def smart_compress(
        self, 
        messages: List[Dict[str, str]],
        keep_recent: int = 5,
        target_ratio: float = 0.6
    ) -> List[Dict[str, str]]:
        """
        智能压缩：结合优先级和LLM总结
        
        Args:
            messages: 消息列表
            keep_recent: 保留最近N条
            target_ratio: 目标压缩比（保留60%的tokens）
        """
        current_tokens = self.count_messages_tokens(messages)
        target_tokens = int(current_tokens * target_ratio)
        
        # 先按优先级排序
        prioritized = self.prioritize_messages(messages, {})
        
        # 保留system + 高优先级 + 最近
        system_msgs = [m for m in prioritized if m.get('role') == 'system']
        recent_msgs = messages[-keep_recent:]
        
        # 中间部分压缩
        remaining = [m for m in messages if m not in system_msgs and m not in recent_msgs]
        
        if remaining:
            compressed = await self._compress_middle(remaining)
            result = system_msgs + compressed + recent_msgs
        else:
            result = system_msgs + recent_msgs
        
        return result
