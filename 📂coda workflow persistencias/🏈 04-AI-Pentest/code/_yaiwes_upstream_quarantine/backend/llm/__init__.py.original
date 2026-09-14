"""
大语言模型客户端基类
提供统一的接口用于与各种LLM交互
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import json
import os
import requests
from dotenv import load_dotenv

load_dotenv()


class ModelProvider(Enum):
    """支持的模型提供商"""
    DEEPSEEK = "deepseek"
    GLM = "glm"
    QWEN = "qwen"
    OPENAI = "openai"


@dataclass
class LLMResponse:
    """LLM响应数据结构"""
    content: str
    model: str
    usage: Dict[str, int]
    raw_response: Optional[Dict] = None


@dataclass
class Message:
    """聊天消息结构"""
    role: str  # system, user, assistant
    content: str

    def to_dict(self) -> Dict:
        return {"role": self.role, "content": self.content}


class BaseLLMClient(ABC):
    """LLM客户端基类"""

    def __init__(
        self,
        api_key: str,
        base_url: str,
        model: str,
        timeout: int = 120,
        temperature: float = 0.7,
        max_tokens: int = 4096
    ):
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self.timeout = timeout
        self.temperature = temperature
        self.max_tokens = max_tokens

    @abstractmethod
    def chat(
        self,
        messages: List[Message],
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> LLMResponse:
        """发送聊天请求"""
        pass

    @abstractmethod
    def chat_with_json(self, messages: List[Message], schema: Dict) -> Dict:
        """发送请求并要求返回JSON格式"""
        pass

    def _build_headers(self) -> Dict[str, str]:
        """构建请求头"""
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }


class DeepSeekClient(BaseLLMClient):
    """DeepSeek模型客户端"""

    def __init__(self, api_key: str = None, model: str = "deepseek-chat", **kwargs):
        api_key = api_key or os.getenv("DEEPSEEK_API_KEY", "")
        base_url = kwargs.pop("base_url", "") or "https://api.deepseek.com/v1"
        timeout = kwargs.pop("timeout", 120)
        temperature = kwargs.pop("temperature", 0.7)
        max_tokens = kwargs.pop("max_tokens", 4096)
        super().__init__(api_key, base_url, model, timeout, temperature, max_tokens)

    def chat(
        self,
        messages: List[Message],
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> LLMResponse:
        """发送聊天请求到DeepSeek"""
        url = f"{self.base_url}/chat/completions"

        # 构建消息列表
        chat_messages = []
        if system_prompt:
            chat_messages.append(Message("system", system_prompt).to_dict())
        chat_messages.extend([msg.to_dict() for msg in messages])

        payload = {
            "model": self.model,
            "messages": chat_messages,
            "temperature": kwargs.get("temperature", self.temperature),
            "max_tokens": kwargs.get("max_tokens", self.max_tokens)
        }

        try:
            response = requests.post(
                url,
                headers=self._build_headers(),
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            data = response.json()

            return LLMResponse(
                content=data["choices"][0]["message"]["content"],
                model=self.model,
                usage=data.get("usage", {}),
                raw_response=data
            )
        except requests.exceptions.RequestException as e:
            raise Exception(f"DeepSeek API调用失败: {str(e)}")

    def chat_with_json(self, messages: List[Message], schema: Dict) -> Dict:
        """发送请求并要求返回JSON格式"""
        # 添加JSON格式要求
        schema_str = json.dumps(schema, ensure_ascii=False)
        prompt = f"你必须返回有效的JSON格式，不要包含任何其他内容。\n\n要求的JSON结构:\n{schema_str}\n\n用户问题: {messages[-1].content}"

        messages = [Message(m.role, m.content) for m in messages]
        messages[-1] = Message("user", prompt)

        response = self.chat(messages)
        try:
            return json.loads(response.content)
        except json.JSONDecodeError:
            # 尝试提取JSON部分
            content = response.content
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            return json.loads(content)


class GLMClient(BaseLLMClient):
    """智谱AI GLM模型客户端"""

    def __init__(self, api_key: str = None, model: str = "glm-4", **kwargs):
        api_key = api_key or os.getenv("GLM_API_KEY", "")
        base_url = kwargs.pop("base_url", "") or "https://open.bigmodel.cn/api/paas/v4"
        timeout = kwargs.pop("timeout", 120)
        temperature = kwargs.pop("temperature", 0.7)
        max_tokens = kwargs.pop("max_tokens", 4096)
        super().__init__(api_key, base_url, model, timeout, temperature, max_tokens)

    def chat(
        self,
        messages: List[Message],
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> LLMResponse:
        """发送聊天请求到GLM"""
        url = f"{self.base_url}/chat/completions"

        chat_messages = []
        if system_prompt:
            chat_messages.append({"role": "system", "content": system_prompt})
        chat_messages.extend([msg.to_dict() for msg in messages])

        payload = {
            "model": self.model,
            "messages": chat_messages,
            "temperature": kwargs.get("temperature", self.temperature),
            "max_tokens": kwargs.get("max_tokens", self.max_tokens)
        }

        try:
            response = requests.post(
                url,
                headers=self._build_headers(),
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            data = response.json()

            return LLMResponse(
                content=data["choices"][0]["message"]["content"],
                model=self.model,
                usage=data.get("usage", {}),
                raw_response=data
            )
        except requests.exceptions.RequestException as e:
            raise Exception(f"GLM API调用失败: {str(e)}")

    def chat_with_json(self, messages: List[Message], schema: Dict) -> Dict:
        """发送请求并要求返回JSON格式"""
        schema_str = json.dumps(schema, ensure_ascii=False)
        prompt = f"你必须返回有效的JSON格式，不要包含任何其他内容。\n\n要求的JSON结构:\n{schema_str}\n\n用户问题: {messages[-1].content}"

        messages = [Message(m.role, m.content) for m in messages]
        messages[-1] = Message("user", prompt)

        response = self.chat(messages)
        try:
            return json.loads(response.content)
        except json.JSONDecodeError:
            content = response.content
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            return json.loads(content)


class QwenClient(BaseLLMClient):
    """阿里云Qwen模型客户端"""

    def __init__(self, api_key: str = None, model: str = "qwen-turbo", **kwargs):
        api_key = api_key or os.getenv("QWEN_API_KEY", "")
        base_url = kwargs.pop("base_url", "") or "https://dashscope.aliyuncs.com/api/v1"
        timeout = kwargs.pop("timeout", 120)
        temperature = kwargs.pop("temperature", 0.7)
        max_tokens = kwargs.pop("max_tokens", 4096)
        super().__init__(api_key, base_url, model, timeout, temperature, max_tokens)

    def chat(
        self,
        messages: List[Message],
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> LLMResponse:
        """发送聊天请求到Qwen"""
        url = f"{self.base_url}/aigc/text-generation/generation"

        chat_messages = []
        if system_prompt:
            chat_messages.append({"role": "system", "content": system_prompt})
        chat_messages.extend([msg.to_dict() for msg in messages])

        payload = {
            "model": self.model,
            "input": {"messages": chat_messages},
            "parameters": {
                "temperature": kwargs.get("temperature", self.temperature),
                "max_tokens": kwargs.get("max_tokens", self.max_tokens),
                "result_format": "message"
            }
        }

        try:
            response = requests.post(
                url,
                headers=self._build_headers(),
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            data = response.json()

            return LLMResponse(
                content=data["output"]["choices"][0]["message"]["content"],
                model=self.model,
                usage=data.get("usage", {}),
                raw_response=data
            )
        except requests.exceptions.RequestException as e:
            raise Exception(f"Qwen API调用失败: {str(e)}")

    def chat_with_json(self, messages: List[Message], schema: Dict) -> Dict:
        """发送请求并要求返回JSON格式"""
        schema_str = json.dumps(schema, ensure_ascii=False)
        prompt = f"你必须返回有效的JSON格式，不要包含任何其他内容。\n\n要求的JSON结构:\n{schema_str}\n\n用户问题: {messages[-1].content}"

        messages = [Message(m.role, m.content) for m in messages]
        messages[-1] = Message("user", prompt)

        response = self.chat(messages)
        try:
            return json.loads(response.content)
        except json.JSONDecodeError:
            content = response.content
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            return json.loads(content)


class OpenAIClient(BaseLLMClient):
    """OpenAI兼容接口客户端"""

    def __init__(self, api_key: str = None, model: str = "gpt-3.5-turbo", **kwargs):
        api_key = api_key or os.getenv("OPENAI_API_KEY", "")
        base_url = kwargs.pop("base_url", "") or "https://api.openai.com/v1"
        timeout = kwargs.pop("timeout", 120)
        temperature = kwargs.pop("temperature", 0.7)
        max_tokens = kwargs.pop("max_tokens", 4096)
        super().__init__(api_key, base_url, model, timeout, temperature, max_tokens)

    def chat(
        self,
        messages: List[Message],
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> LLMResponse:
        """发送聊天请求到OpenAI兼容接口"""
        url = f"{self.base_url}/chat/completions"

        chat_messages = []
        if system_prompt:
            chat_messages.append(Message("system", system_prompt).to_dict())
        chat_messages.extend([msg.to_dict() for msg in messages])

        payload = {
            "model": self.model,
            "messages": chat_messages,
            "temperature": kwargs.get("temperature", self.temperature),
            "max_tokens": kwargs.get("max_tokens", self.max_tokens)
        }

        try:
            response = requests.post(
                url,
                headers=self._build_headers(),
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            data = response.json()

            return LLMResponse(
                content=data["choices"][0]["message"]["content"],
                model=self.model,
                usage=data.get("usage", {}),
                raw_response=data
            )
        except requests.exceptions.RequestException as e:
            raise Exception(f"OpenAI API调用失败: {str(e)}")

    def chat_with_json(self, messages: List[Message], schema: Dict) -> Dict:
        """发送请求并要求返回JSON格式"""
        schema_str = json.dumps(schema, ensure_ascii=False)
        prompt = f"你必须返回有效的JSON格式，不要包含任何其他内容。\n\n要求的JSON结构:\n{schema_str}\n\n用户问题: {messages[-1].content}"

        messages = [Message(m.role, m.content) for m in messages]
        messages[-1] = Message("user", prompt)

        response = self.chat(messages)
        try:
            return json.loads(response.content)
        except json.JSONDecodeError:
            content = response.content
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            return json.loads(content)


class LLMFactory:
    """LLM客户端工厂"""

    _clients = {
        "deepseek": DeepSeekClient,
        "glm": GLMClient,
        "qwen": QwenClient,
        "openai": OpenAIClient
    }

    @classmethod
    def create(
        cls,
        provider: str,
        api_key: str = None,
        model: str = None,
        **kwargs
    ) -> BaseLLMClient:
        """创建LLM客户端实例"""
        provider = provider.lower()

        if provider not in cls._clients:
            raise ValueError(f"不支持的模型提供商: {provider}，支持的提供商: {list(cls._clients.keys())}")

        client_class = cls._clients[provider]

        # 设置默认模型
        default_models = {
            "deepseek": "deepseek-chat",
            "glm": "glm-4",
            "qwen": "qwen-turbo",
            "openai": "gpt-3.5-turbo"
        }
        model = model or default_models.get(provider, "gpt-3.5-turbo")

        return client_class(api_key=api_key, model=model, **kwargs)

    @classmethod
    def register_client(cls, name: str, client_class: type):
        """注册新的LLM客户端"""
        cls._clients[name] = client_class
