import os
from typing import Optional
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()

class SSHConfig(BaseModel):
    hostname: str = Field(..., description="Kali box hostname or IP")
    port: int = Field(22, description="SSH Port")
    username: str = Field(..., description="SSH Username")
    password: Optional[str] = Field(None, description="SSH Password")
    key_filename: Optional[str] = Field(None, description="Path to SSH private key")

class LLMConfig(BaseModel):
    base_url: str = Field("http://localhost:11434/v1", description="Local LLM API Base URL")
    api_key: str = Field("lm-studio", description="API Key (dummy for local)")
    model_name: str = Field("local-model", description="Model name to request")

class MemoryConfig(BaseModel):
    persist_dir: str = Field("memory_db", description="Path to ChromaDB persistence directory")
    collection_name: str = Field("pentest_knowledge", description="Name of the vector collection")
    embedding_model: str = Field("all-MiniLM-L6-v2", description="Embedding model name (if local)")

class AgentConfig(BaseModel):
    ssh: SSHConfig
    llm: LLMConfig
    memory: MemoryConfig = Field(default_factory=lambda: MemoryConfig())

def load_config() -> AgentConfig:
    ssh_config = SSHConfig(
        hostname=os.getenv("KALI_HOST", "127.0.0.1"),
        port=int(os.getenv("KALI_PORT", 2222)),
        username=os.getenv("KALI_USER", "kali"),
        password=os.getenv("KALI_PASS", "kali"),
        key_filename=os.getenv("KALI_KEY_PATH")
    )
    
    llm_config = LLMConfig(
        base_url=os.getenv("LLM_BASE_URL", "http://localhost:11434/v1"),
        api_key=os.getenv("LLM_API_KEY", "lm-studio"),
        model_name=os.getenv("LLM_MODEL", "local-model")
    )
    
    return AgentConfig(ssh=ssh_config, llm=llm_config)
