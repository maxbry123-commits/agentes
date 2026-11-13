"""
核心配置 - 基于JSON配置文件
"""
import json
import os
from pathlib import Path
from typing import Optional, Dict, Any


class ConfigLoader:
    """配置加载器"""

    def __init__(self, config_path: str = None):
        if config_path is None:
            # 默认在项目根目录查找 config.json
            self.config_path = Path(__file__).parent.parent.parent.parent / "config.json"
        else:
            self.config_path = Path(config_path)

        self._config: Dict[str, Any] = {}
        self.load_config()

    def load_config(self):
        """加载JSON配置文件"""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    self._config = json.load(f)
                print(f"✅ 已加载配置文件: {self.config_path}")
            else:
                raise FileNotFoundError(f"配置文件不存在: {self.config_path}")
        except Exception as e:
            print(f"⚠️ 加载配置文件失败: {e}")
            self._config = {}

    def get(self, key_path: str, default=None):
        """获取配置值，支持点号分隔的路径"""
        keys = key_path.split('.')
        value = self._config

        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default


class Settings:
    """应用配置"""

    def __init__(self, config_path: str = None):
        self.loader = ConfigLoader(config_path)
        self._init_from_config()

    def _init_from_config(self):
        """从JSON配置初始化"""
        # 应用基础配置
        self.APP_NAME: str = self.loader.get('app.name', 'H-Pentest')
        self.APP_VERSION: str = self.loader.get('app.version', '2.0.0')
        self.DEBUG: bool = self.loader.get('app.debug', True)

        # 数据库配置
        self.DATABASE_URL: str = self.loader.get('database.url', 'sqlite+aiosqlite:////app/data/h-pentest.db')

        # LLM配置 - 🔥🔥🔥 移除所有硬编码默认值
        self.OPENAI_API_KEY: str = self.loader.get('openai.api_key', '')
        self.OPENAI_BASE_URL: str = self.loader.get('openai.base_url', '')
        self.OPENAI_MODEL: str = self.loader.get('openai.model')  # 🔥 必须配置
        self.OPENAI_MODEL_MINI: str = self.loader.get('openai.model_mini')  # 🔥 必须配置
        self.OPENAI_TEMPERATURE: float = self.loader.get('openai.temperature', 0.7)
        self.OPENAI_MAX_TOKENS: int = self.loader.get('openai.max_tokens', 8000)

        # Worker LLM（执行层）
        self.WORKER_MODEL: Optional[str] = self.loader.get('llm.worker.model')
        self.WORKER_TEMPERATURE: Optional[float] = self.loader.get('llm.worker.temperature')
        self.WORKER_MAX_TOKENS: Optional[int] = self.loader.get('llm.worker.max_tokens')

        # Meta LLM（监督层）
        self.META_MODEL: Optional[str] = self.loader.get('llm.meta.model')
        self.META_TEMPERATURE: Optional[float] = self.loader.get('llm.meta.temperature')
        self.META_MAX_TOKENS: Optional[int] = self.loader.get('llm.meta.max_tokens')

        # Strategic LLM（战略层）
        self.STRATEGIC_MODEL: Optional[str] = self.loader.get('llm.strategic.model')
        self.STRATEGIC_TEMPERATURE: Optional[float] = self.loader.get('llm.strategic.temperature')
        self.STRATEGIC_MAX_TOKENS: Optional[int] = self.loader.get('llm.strategic.max_tokens')

        # Context Manager（上下文压缩）
        self.CONTEXT_MODEL: Optional[str] = self.loader.get('llm.context.model')

        # 阿里云DashScope配置
        self.DASHSCOPE_API_KEY: Optional[str] = self.loader.get('dashscope.api_key')
        self.DASHSCOPE_BASE_URL: Optional[str] = self.loader.get('dashscope.base_url')

        # Embedding模型配置
        self.EMBEDDING_MODEL: str = self.loader.get('embedding.model', 'text-embedding-v3')
        self.EMBEDDING_API_KEY: Optional[str] = self.loader.get('embedding.api_key')
        self.EMBEDDING_BASE_URL: Optional[str] = self.loader.get('embedding.base_url')

        # Rerank模型配置
        self.RERANK_MODEL: str = self.loader.get('rerank.model', 'gte-rerank')
        self.RERANK_API_KEY: Optional[str] = self.loader.get('rerank.api_key')
        self.RERANK_BASE_URL: Optional[str] = self.loader.get('rerank.base_url')

        # 初始化默认值
        self._init_defaults()

    def _init_defaults(self):
        """初始化默认值"""
        # 如果未单独配置各层模型，使用主模型
        if not self.WORKER_MODEL:
            self.WORKER_MODEL = self.OPENAI_MODEL
        if not self.META_MODEL:
            self.META_MODEL = self.OPENAI_MODEL
        if not self.STRATEGIC_MODEL:
            self.STRATEGIC_MODEL = self.OPENAI_MODEL
        if not self.CONTEXT_MODEL:
            self.CONTEXT_MODEL = self.OPENAI_MODEL_MINI

        # 如果未配置各层参数，使用主参数
        if self.WORKER_TEMPERATURE is None:
            self.WORKER_TEMPERATURE = self.OPENAI_TEMPERATURE
        if self.WORKER_MAX_TOKENS is None:
            self.WORKER_MAX_TOKENS = self.OPENAI_MAX_TOKENS
        
        # 🔥🔥🔥 Meta层默认值
        if self.META_TEMPERATURE is None:
            self.META_TEMPERATURE = 0.3  # 更保守
        if self.META_MAX_TOKENS is None:
            self.META_MAX_TOKENS = 32000
        
        # 🔥🔥🔥 Strategic层默认值
        if self.STRATEGIC_TEMPERATURE is None:
            self.STRATEGIC_TEMPERATURE = 0.5  # 中等保守
        if self.STRATEGIC_MAX_TOKENS is None:
            self.STRATEGIC_MAX_TOKENS = 32000

        # 阿里云配置默认值
        if not self.EMBEDDING_API_KEY:
            self.EMBEDDING_API_KEY = self.DASHSCOPE_API_KEY
        if not self.EMBEDDING_BASE_URL:
            self.EMBEDDING_BASE_URL = self.DASHSCOPE_BASE_URL
        if not self.RERANK_API_KEY:
            self.RERANK_API_KEY = self.DASHSCOPE_API_KEY
        if not self.RERANK_BASE_URL:
            self.RERANK_BASE_URL = "https://dashscope.aliyuncs.com/api/v1/services/rerank/text-rerank/text-rerank"
        if not self.DASHSCOPE_BASE_URL:
            self.DASHSCOPE_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"

    # 进程配置
    @property
    def MAX_CONCURRENT_TASKS(self) -> int:
        return self.loader.get('process.max_concurrent_tasks', 3)

    @property
    def TASK_TIMEOUT(self) -> int:
        return self.loader.get('process.task_timeout', 3600)

    # WebSocket配置
    @property
    def WS_HEARTBEAT_INTERVAL(self) -> int:
        return self.loader.get('websocket.heartbeat_interval', 30)

    @property
    def WS_MESSAGE_QUEUE_SIZE(self) -> int:
        return self.loader.get('websocket.message_queue_size', 1000)

    # Kali配置
    @property
    def KALI_IMAGE(self) -> str:
        return self.loader.get('kali.image', 'kalilinux/kali-rolling')

    @property
    def KALI_TOOLS_PATH(self) -> str:
        return self.loader.get('kali.tools_path', '/usr/share/kali-tools')

    # 知识库配置
    @property
    def KNOWLEDGE_BASE_PATH(self) -> str:
        return self.loader.get('knowledge.base_path', './knowledge')

    @property
    def KNOWLEDGE_CACHE_DIR(self) -> str:
        return self.loader.get('knowledge.cache_dir', './cache')

    # RAG配置
    @property
    def RAG_ENABLED(self) -> bool:
        return self.loader.get('rag.enabled', True)

    @property
    def RAG_TOP_K(self) -> int:
        return self.loader.get('rag.top_k', 5)

    @property
    def RAG_RERANK_ENABLED(self) -> bool:
        return self.loader.get('rag.rerank_enabled', True)

    @property
    def RAG_SCORE_THRESHOLD(self) -> float:
        return self.loader.get('rag.score_threshold', 0.3)

    # Docker配置
    @property
    def DOCKER_SOCKET(self) -> str:
        return self.loader.get('docker.socket', 'unix:///var/run/docker.sock')

    # 工具路径配置
    @property
    def NUCLEI_TEMPLATES_PATH(self) -> str:
        return self.loader.get('tools.nuclei_templates_path', '/app/tools/nuclei-templates')

    @property
    def SQLMAP_PATH(self) -> str:
        return self.loader.get('tools.sqlmap_path', '/app/tools/sqlmap/sqlmap.py')

    @property
    def DIRSEARCH_PATH(self) -> str:
        return self.loader.get('tools.dirsearch_path', '/app/tools/dirsearch/dirsearch.py')


# 全局配置实例
settings = Settings()
