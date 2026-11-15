import json
import os
import threading
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def get_project_root() -> str:
    """返回项目根目录的绝对路径。"""
    return os.path.dirname(os.path.abspath(__file__))


class Config:
    """应用配置管理 — 单例模式，支持环境变量覆盖 API Key 和延迟写入。

    环境变量（按优先级从高到低）:
        LLM_API_KEY_<NAME> : 覆盖指定 LLM 入口的 api_key（如 LLM_API_KEY_ANALYZER）
        LLM_API_KEY        : 覆盖所有 LLM 入口的 api_key
        SILICONFLOW_API_KEY: 同 LLM_API_KEY（兼容旧称）
    """

    _instance: Optional['Config'] = None
    _lock: threading.Lock = threading.Lock()

    def __new__(cls, config_path: str = "./config.json"):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
            return cls._instance

    def __init__(self, config_path: str = "./config.json"):
        with self._lock:
            if hasattr(self, '_initialized'):
                return
            self.config_path = config_path
            self._config: dict = {}
            self._dirty: bool = False
            self._initialized = True
        self._load_env_file()
        self._load_from_disk()
        self._override_api_keys_from_env()

    # ---- 静态初始化辅助 -----------------------------------------------

    @staticmethod
    def _load_env_file():
        """尝试加载 .env 文件（如果安装了 python-dotenv）"""
        try:
            from dotenv import load_dotenv
            load_dotenv()
        except ImportError:
            pass

    def _load_from_disk(self):
        """读取 config.json 并验证结构"""
        if not os.path.exists(self.config_path):
            raise ValueError(f"配置文件 {self.config_path} 不存在")
        with open(self.config_path, "r", encoding="utf-8") as f:
            try:
                raw = json.load(f)
            except json.JSONDecodeError:
                raise ValueError(f"配置文件 {self.config_path} 不是有效的JSON格式")
        self._validate_structure(raw)
        self._config = raw

    @staticmethod
    def _validate_structure(raw: dict):
        """验证配置文件必要字段是否存在，及早报错。"""
        if "llm" not in raw:
            raise ValueError("配置缺少 'llm' 段")
        required_llm_keys = ("analyzer", "solve_agent", "pre_processor", "embedding")
        missing = [k for k in required_llm_keys if k not in raw.get("llm", {})]
        if missing:
            raise ValueError(f"配置 'llm' 段缺少以下入口: {', '.join(missing)}")
        for name, agent_cfg in raw["llm"].items():
            for field in ("model", "api_key", "api_base"):
                if field not in agent_cfg:
                    raise ValueError(f"llm.{name} 缺少 '{field}' 字段")

    def _override_api_keys_from_env(self):
        """用环境变量覆盖 API Key（不修改磁盘文件）"""
        llm_configs = self._config.get("llm", {})

        # 通用覆盖
        default_key = os.getenv("LLM_API_KEY") or os.getenv("SILICONFLOW_API_KEY")
        if default_key:
            for agent_config in llm_configs.values():
                if "api_key" in agent_config:
                    agent_config["api_key"] = default_key

        # 逐个入口覆盖
        for name, agent_config in llm_configs.items():
            env_key = os.getenv(f"LLM_API_KEY_{name.upper()}")
            if env_key and "api_key" in agent_config:
                agent_config["api_key"] = env_key

    # ---- 公开接口 ----------------------------------------------------

    @classmethod
    def load_config(cls, config_path: str = "./config.json") -> dict:
        """兼容旧接口 —— 返回完整配置字典。"""
        return cls(config_path).get_all()

    @classmethod
    def get_tool_config(cls, tool_name: str, config_path: str = "./config.json") -> dict:
        """获取指定工具的独立配置段。"""
        return cls(config_path).get_all().get("tool_config", {}).get(tool_name, {})

    def get_all(self) -> dict:
        with self._lock:
            return dict(self._config)  # 返回浅拷贝，避免外部修改影响内部状态

    def get(self, key: str, default=None):
        with self._lock:
            return self._config.get(key, default)

    def set(self, key: str, value):
        """设置配置项（标记脏数据，需调用 flush() 持久化）。"""
        with self._lock:
            self._config[key] = value
            self._dirty = True

    def flush(self):
        """将脏配置写入磁盘。"""
        with self._lock:
            if self._dirty:
                with open(self.config_path, "w", encoding="utf-8") as f:
                    json.dump(self._config, f, indent=4, ensure_ascii=False)
                self._dirty = False

    @classmethod
    def reset_instance(cls):
        """重置单例（仅测试用）。"""
        with cls._lock:
            cls._instance = None





"""
config.json   

"output_summary_threshold": 2048,   // 超过此长度的输出触发 LLM 摘要
"output_summary_max_chars": 800,    // 摘要最大字符数
"knowledge_entry_max_chars": 2000,  // 结构化知识条目最大字数

"""