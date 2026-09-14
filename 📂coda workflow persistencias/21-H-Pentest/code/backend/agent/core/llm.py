"""
LLM Client - 完全异步的LLM调用（带重试机制）
"""
import asyncio
from typing import List, Dict, Any, Optional
from openai import AsyncOpenAI
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)
import os


class LLMClient:
    """异步LLM客户端"""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: str = None,  # 🔥 禁止硬编码，不提供默认值
        temperature: float = 0.7,
        max_tokens: int = 8000,
        output_callback: Optional[callable] = None,  # 流式输出回调
        stop_event: Optional[Any] = None  # 🔥🔥🔥 添加停止事件
    ):
        # 🔥🔥🔥 只从config.json加载，不读取环境变量
        if not api_key or not base_url or not model:
            try:
                from app.core.config import settings
                self.api_key = api_key or settings.OPENAI_API_KEY
                self.base_url = base_url or settings.OPENAI_BASE_URL
                self.model = model or settings.OPENAI_MODEL
            except Exception as e:
                raise ValueError(f"⚠️  加载配置失败: {e}. 请检查 config.json")
        else:
            self.api_key = api_key
            self.base_url = base_url
            self.model = model
        
        # 验证必要参数
        if not self.api_key:
            raise ValueError("⚠️  未配置 API Key！请在 config.json 中设置 openai.api_key")
        if not self.base_url:
            raise ValueError("⚠️  未配置 Base URL！请在 config.json 中设置 openai.base_url")
        if not self.model:
            raise ValueError("⚠️  未配置模型！请在 config.json 中设置 openai.model")
        
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.output_callback = output_callback
        self.stop_event = stop_event  # 🔥🔥🔥 保存停止事件  # 用于实时广播
        
        # 🔥 只在第一个实例时打印（减少日志）
        # print(f"✅ LLM客户端初始化: model={self.model}, base_url={self.base_url}")
        
        # 创建异步客户端
        self.client = AsyncOpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
            timeout=120.0
        )
    
    async def chat(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict]] = None,
        stream: bool = True,
        **kwargs
    ) -> Dict[str, Any]:
        """
        异步调用LLM
        
        Args:
            messages: 消息列表
            tools: 工具列表
            stream: 是否流式输出
            **kwargs: 其他参数
        
        Returns:
            LLM响应
        """
        params = {
            'model': kwargs.get('model', self.model),
            'messages': messages,
            'temperature': kwargs.get('temperature', self.temperature),
            'max_tokens': kwargs.get('max_tokens', self.max_tokens),
            'stream': stream
        }
        
        # 🔥🔥🔥 支持response_format参数（强制JSON输出）
        if 'response_format' in kwargs:
            params['response_format'] = kwargs['response_format']
        
        if tools:
            params['tools'] = tools
            # 🔥🔥🔥 必须设置tool_choice，否则GLM会使用XML格式而不是OpenAI格式
            params['tool_choice'] = 'auto'  # 'auto' | 'required' | 'none'
        
        if stream:
            return await self._handle_stream(params)
        else:
            return await self._handle_non_stream(params)
    
    @retry(
        stop=stop_after_attempt(3),  # 最多重试3次
        wait=wait_exponential(multiplier=1, min=2, max=10),  # 指数退避
        retry=retry_if_exception_type((Exception,)),
        reraise=True
    )
    async def _handle_stream(self, params: dict) -> Dict[str, Any]:
        """处理流式响应（实时广播）"""
        content_chunks = []
        tool_calls = []
        
        # 🔥🔥🔥 检查停止事件
        if self.stop_event and self.stop_event.is_set():
            raise asyncio.CancelledError("任务已取消")
        
        # 🔥 用于过滤 <think> 标签
        in_think_tag = False
        
        try:
            stream = await self.client.chat.completions.create(**params)
            
            async for chunk in stream:
                # 🔥🔥🔥 每个chunk都检查停止事件
                if self.stop_event and self.stop_event.is_set():
                    raise asyncio.CancelledError("任务已取消")
                
                if not chunk.choices:
                    continue
                
                delta = chunk.choices[0].delta
                
                # 内容
                if delta.content:
                    content_chunks.append(delta.content)
                    
                    # 🔥🔥🔥 过滤 <think> 标签内的内容，不打印出来
                    chunk_text = delta.content
                    
                    # 检查是否进入或离开 <think> 标签
                    if '<think>' in chunk_text:
                        in_think_tag = True
                    if '</think>' in chunk_text:
                        in_think_tag = False
                        chunk_text = ''  # 不打印 </think> 标签
                    
                    # 只有在不在 <think> 标签内时才打印
                    if not in_think_tag and chunk_text and '<think>' not in chunk_text:
                        print(chunk_text, end='', flush=True)
                    
                    # 实时广播到前端
                    if self.output_callback:
                        await self.output_callback(delta.content)
                
                # 工具调用
                if delta.tool_calls:
                    for tc in delta.tool_calls:
                        if tc.index >= len(tool_calls):
                            tool_calls.append({
                                'id': tc.id,
                                'type': 'function',
                                'function': {
                                    'name': tc.function.name or '',
                                    'arguments': ''
                                }
                            })
                        
                        if tc.function.arguments:
                            tool_calls[tc.index]['function']['arguments'] += tc.function.arguments
            
            # 🔥 换行，让输出更整齐
            if content_chunks:
                print()  # 流式输出结杞后换行
            
            return {
                'content': ''.join(content_chunks),
                'tool_calls': tool_calls if tool_calls else None
            }
        
        except asyncio.CancelledError:
            raise
        except Exception as e:
            raise
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((Exception,)),
        reraise=True
    )
    async def _handle_non_stream(self, params: dict) -> Dict[str, Any]:
        """处理非流式响应"""
        try:
            response = await self.client.chat.completions.create(**params)
            message = response.choices[0].message
            
            content = message.content or ''
            
            return {
                'content': content,
                'tool_calls': message.tool_calls
            }
        
        except Exception as e:
            raise
