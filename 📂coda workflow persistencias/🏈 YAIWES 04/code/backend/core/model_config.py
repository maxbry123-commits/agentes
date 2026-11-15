"""
模型配置管理器
支持为每个智能体单独配置模型
"""
from typing import Dict, Optional, Any
from dataclasses import dataclass, field
import json
import os
from llm import LLMFactory, BaseLLMClient


@dataclass
class ModelConfig:
    """单个模型配置"""
    provider: str  # deepseek, glm, qwen, openai, custom
    model_name: str
    api_key: str = ""
    base_url: str = ""
    temperature: float = 0.7
    max_tokens: int = 4096
    timeout: int = 120
    
    def to_dict(self) -> Dict:
        return {
            "provider": self.provider,
            "model_name": self.model_name,
            "api_key": "***" if self.api_key else "",  # 隐藏敏感信息
            "base_url": self.base_url,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "timeout": self.timeout
        }
    
    def to_full_dict(self) -> Dict:
        """包含完整信息（用于内部使用）"""
        return {
            "provider": self.provider,
            "model_name": self.model_name,
            "api_key": self.api_key,
            "base_url": self.base_url,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "timeout": self.timeout
        }


@dataclass
class AgentModelConfig:
    """智能体模型配置"""
    agent_name: str
    model_config: ModelConfig
    enabled: bool = True
    description: str = ""
    
    def to_dict(self) -> Dict:
        return {
            "agent_name": self.agent_name,
            "model_config": self.model_config.to_dict(),
            "enabled": self.enabled,
            "description": self.description
        }


class ModelConfigManager:
    """
    模型配置管理器
    管理所有智能体的模型配置
    """
    
    # 默认模型配置
    DEFAULT_PROVIDERS = {
        "deepseek": {
            "base_url": "https://api.deepseek.com/v1",
            "default_model": "deepseek-chat",
            "description": "DeepSeek - 深度求索大模型"
        },
        "glm": {
            "base_url": "https://open.bigmodel.cn/api/paas/v4",
            "default_model": "glm-4",
            "description": "智谱AI GLM-4"
        },
        "qwen": {
            "base_url": "https://dashscope.aliyuncs.com/api/v1",
            "default_model": "qwen-turbo",
            "description": "阿里云通义千问"
        },
        "openai": {
            "base_url": "https://api.openai.com/v1",
            "default_model": "gpt-3.5-turbo",
            "description": "OpenAI GPT"
        },
        "custom": {
            "base_url": "",
            "default_model": "",
            "description": "自定义OpenAI兼容接口"
        }
    }
    
    # 智能体默认配置
    DEFAULT_AGENTS = {
        "coordinator": {
            "description": "协调者Agent - 负责团队协作和任务分配",
            "recommended_provider": "deepseek"
        },
        "recon": {
            "description": "信息收集Agent - 负责目标侦察和信息收集",
            "recommended_provider": "deepseek"
        },
        "vuln": {
            "description": "漏洞分析Agent - 负责漏洞扫描和评估",
            "recommended_provider": "deepseek"
        },
        "exploit": {
            "description": "漏洞利用Agent - 负责漏洞利用和攻击",
            "recommended_provider": "deepseek"
        },
        "report": {
            "description": "报告生成Agent - 负责生成渗透测试报告",
            "recommended_provider": "deepseek"
        }
    }
    
    def __init__(self, config_file: str = None):
        self.config_file = config_file or "./model_config.json"
        self.agent_configs: Dict[str, AgentModelConfig] = {}
        self._load_config()
    
    def _load_config(self):
        """加载配置文件"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for agent_name, config_data in data.get("agents", {}).items():
                        model_data = config_data.get("model_config", {})
                        model_config = ModelConfig(
                            provider=model_data.get("provider", "deepseek"),
                            model_name=model_data.get("model_name", "deepseek-chat"),
                            api_key=model_data.get("api_key", ""),
                            base_url=model_data.get("base_url", ""),
                            temperature=model_data.get("temperature", 0.7),
                            max_tokens=model_data.get("max_tokens", 4096),
                            timeout=model_data.get("timeout", 120)
                        )
                        self.agent_configs[agent_name] = AgentModelConfig(
                            agent_name=agent_name,
                            model_config=model_config,
                            enabled=config_data.get("enabled", True),
                            description=config_data.get("description", "")
                        )
            except Exception as e:
                print(f"加载模型配置失败: {e}")
        
        # 确保所有默认Agent都有配置
        self._ensure_default_configs()
    
    def _ensure_default_configs(self):
        """确保所有默认Agent都有配置"""
        for agent_name, agent_info in self.DEFAULT_AGENTS.items():
            if agent_name not in self.agent_configs:
                provider = agent_info["recommended_provider"]
                provider_info = self.DEFAULT_PROVIDERS.get(provider, {})
                model_config = ModelConfig(
                    provider=provider,
                    model_name=provider_info.get("default_model", ""),
                    base_url=provider_info.get("base_url", "")
                )
                self.agent_configs[agent_name] = AgentModelConfig(
                    agent_name=agent_name,
                    model_config=model_config,
                    enabled=True,
                    description=agent_info["description"]
                )
    
    def save_config(self):
        """保存配置到文件"""
        data = {
            "agents": {
                name: {
                    "model_config": config.model_config.to_full_dict(),
                    "enabled": config.enabled,
                    "description": config.description
                }
                for name, config in self.agent_configs.items()
            }
        }
        try:
            os.makedirs(os.path.dirname(self.config_file) or ".", exist_ok=True)
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存模型配置失败: {e}")
    
    def get_agent_config(self, agent_name: str) -> Optional[AgentModelConfig]:
        """获取指定Agent的配置"""
        return self.agent_configs.get(agent_name)
    
    def set_agent_config(self, agent_name: str, model_config: Dict) -> bool:
        """设置指定Agent的模型配置"""
        try:
            config = ModelConfig(
                provider=model_config.get("provider", "deepseek"),
                model_name=model_config.get("model_name", ""),
                api_key=model_config.get("api_key", ""),
                base_url=model_config.get("base_url", ""),
                temperature=model_config.get("temperature", 0.7),
                max_tokens=model_config.get("max_tokens", 4096),
                timeout=model_config.get("timeout", 120)
            )
            
            if agent_name in self.agent_configs:
                self.agent_configs[agent_name].model_config = config
            else:
                self.agent_configs[agent_name] = AgentModelConfig(
                    agent_name=agent_name,
                    model_config=config,
                    enabled=True
                )
            
            self.save_config()
            return True
        except Exception as e:
            print(f"设置Agent配置失败: {e}")
            return False
    
    def create_llm_client(self, agent_name: str) -> Optional[BaseLLMClient]:
        """为指定Agent创建LLM客户端"""
        config = self.get_agent_config(agent_name)
        if not config or not config.enabled:
            return None
        
        model_config = config.model_config
        
        try:
            client = LLMFactory.create(
                provider=model_config.provider,
                api_key=model_config.api_key,
                model=model_config.model_name,
                base_url=model_config.base_url,
                temperature=model_config.temperature,
                max_tokens=model_config.max_tokens,
                timeout=model_config.timeout
            )
            return client
        except Exception as e:
            print(f"创建LLM客户端失败 ({agent_name}): {e}")
            return None
    
    def get_all_configs(self) -> Dict:
        """获取所有Agent的配置"""
        return {
            "providers": self.DEFAULT_PROVIDERS,
            "agents": {
                name: config.to_dict() 
                for name, config in self.agent_configs.items()
            }
        }
    
    def test_connection(self, agent_name: str) -> Dict:
        """测试指定Agent的模型连接"""
        config = self.get_agent_config(agent_name)
        if not config:
            return {"success": False, "error": f"未找到Agent配置: {agent_name}"}
        
        try:
            client = self.create_llm_client(agent_name)
            if not client:
                return {"success": False, "error": "无法创建LLM客户端"}
            
            # 发送测试消息
            from llm import Message
            response = client.chat(
                [Message("user", "Hello, this is a test message. Please respond with 'OK'.")],
                system_prompt="You are a helpful assistant. Respond briefly."
            )
            
            return {
                "success": True,
                "response": response.content[:100],
                "model": response.model,
                "usage": response.usage
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def set_agent_enabled(self, agent_name: str, enabled: bool) -> bool:
        """启用/禁用指定Agent"""
        if agent_name in self.agent_configs:
            self.agent_configs[agent_name].enabled = enabled
            self.save_config()
            return True
        return False


# 全局配置管理器实例
_model_config_manager: Optional[ModelConfigManager] = None


def get_model_config_manager(config_file: str = None) -> ModelConfigManager:
    """获取全局模型配置管理器"""
    global _model_config_manager
    if _model_config_manager is None:
        _model_config_manager = ModelConfigManager(config_file)
    return _model_config_manager
