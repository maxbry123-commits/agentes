# H-Pentest 2.0 配置说明

## 📋 配置读取流程

```
.env文件 → config.py (Settings类) → Agent使用
```

## 🔧 当前配置

### 你已经配置好的智谱AI

在 `.env` 文件中：

```bash
# OpenAI API配置
OPENAI_API_KEY=8a7f3a7e25a74ed3827610cca3ce4ec1.SIjLY7tBiulAvJ38
OPENAI_BASE_URL=https://open.bigmodel.cn/api/coding/paas/v4

# LLM模型配置
OPENAI_MODEL=glm-4-plus          # 智谱AI主模型（用于Worker/Meta/Strategic）
OPENAI_MODEL_MINI=glm-4-flash    # 智谱AI轻量模型（用于上下文压缩）
OPENAI_TEMPERATURE=0.7
OPENAI_MAX_TOKENS=8000
```

## 📖 配置项说明

### backend/app/core/config.py

```python
class Settings(BaseSettings):
    # 主配置
    OPENAI_API_KEY: str              # API密钥
    OPENAI_BASE_URL: str             # API地址
    OPENAI_MODEL: str = "gpt-4o"     # 主模型
    OPENAI_MODEL_MINI: str = "gpt-4o-mini"  # 轻量模型
    
    # 各Agent模型（默认使用主模型）
    WORKER_MODEL: Optional[str] = None       # 执行层Agent
    META_MODEL: Optional[str] = None         # 监督层Agent
    STRATEGIC_MODEL: Optional[str] = None    # 战略层Agent
    CONTEXT_MODEL: Optional[str] = None      # 上下文压缩（使用轻量模型）
```

### Agent如何使用配置

```python
from app.core.config import settings

# Worker Agent
self.llm = LLMClient(
    model=settings.WORKER_MODEL,        # 自动从config.py读取
    temperature=settings.WORKER_TEMPERATURE,
    max_tokens=settings.WORKER_MAX_TOKENS
)

# Context Manager
self.llm = ChatOpenAI(
    model=settings.CONTEXT_MODEL,       # 使用轻量模型
    temperature=0.3
)
```

## ✅ 已修复的问题

### 1. Dockerfile路径错误 ✅

**修复前（错误）：**
```dockerfile
COPY requirements.txt .
```

**修复后（正确）：**
```dockerfile
COPY backend/requirements.txt .
```

### 2. 配置统一管理 ✅

- ✅ .env文件添加模型配置
- ✅ config.py统一读取
- ✅ Agent从settings读取，不再硬编码
- ✅ 支持智谱AI、OpenAI、DeepSeek等多种提供商

## 🚀 快速启动

```bash
# 1. 配置已完成（你已经运行过了）
./deploy.sh

# 2. 访问服务
# 前端: http://localhost:5173
# 后端: http://localhost:8000
```

## 🔍 验证配置

```bash
# 进入后端目录
cd backend

# 验证配置读取
python -c "from app.core.config import settings; print(f'Base URL: {settings.OPENAI_BASE_URL}'); print(f'Model: {settings.WORKER_MODEL}')"
```

## 📦 配置优先级

1. **环境变量** (.env文件)
2. **默认值** (config.py中的默认值)
3. **自动设置** (__init__方法中的逻辑)

## 🎯 多模型支持

你可以为不同的Agent使用不同的模型：

```bash
# .env文件
WORKER_MODEL=glm-4-plus         # 执行层用强模型
META_MODEL=glm-4-plus           # 监督层用强模型
STRATEGIC_MODEL=glm-4-plus      # 战略层用强模型
CONTEXT_MODEL=glm-4-flash       # 压缩用轻量模型（省钱）
```

## ⚠️ 注意事项

1. **必须配置**：OPENAI_API_KEY 和 OPENAI_BASE_URL
2. **模型名称**：必须与API提供商支持的模型名称一致
3. **智谱AI模型**：glm-4-plus、glm-4-flash、glm-4、glm-3-turbo等
4. **Docker构建**：首次构建需要下载900MB的PyTorch，需要耐心等待

## 🐛 故障排查

### 配置不生效？

```bash
# 检查.env文件
cat .env

# 检查配置加载
cd backend
python -c "from app.core.config import settings; print(vars(settings))"
```

### Docker构建失败？

```bash
# 查看详细日志
docker-compose build --no-cache backend

# 清理重建
docker-compose down -v
docker-compose build
docker-compose up -d
```
