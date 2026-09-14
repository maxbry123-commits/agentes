# 🔐 H-Pentest 2.0 - AI驱动的智能渗透测试平台

**🥷 全异步架构 | 三层智能决策 | 50+攻击知识库 | Docker容器化 | 实时可视化**

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10+-green.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-teal.svg)](https://fastapi.tiangolo.com/)
[![Vue](https://img.shields.io/badge/Vue-3.4+-4FC08D.svg)](https://vuejs.org/)
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](https://www.docker.com/)
[![OpenAI](https://img.shields.io/badge/LLM-OpenAI%2FKimi%2FQwen-orange.svg)](https://platform.openai.com/)

🏆 **2025腾讯云黑客松 - 智能渗透挑战赛 TOP20**
[![TCH](https://github.com/hexian2001/tuchuang1/blob/main/40402b984f640d234bc202cccee57ca8.png?raw=true)](https://zc.tencent.com/competition/competitionHackathon?code=cha004)

---

## 📖 项目简介

H-Pentest 是一个基于大语言模型(LLM)驱动的**全自动化渗透测试平台**，采用**多Agent协作架构**，集成了52+攻击知识库、Docker沙箱环境和实时可视化界面，为安全研究人员提供企业级的渗透测试自动化解决方案。

### 🚀 核心架构

#### 多Agent协作系统

```
┌─────────────────────────────────────────────────────────────┐
│  🧑‍⚖️ Meta Supervisor (元监督层)                              │
│  • 每3轮生成元层洞察                                         │
│  • 自主决策是否停止测试                                       │
│  • 模式感知：CTF vs RealWorld                               │
│  • 分析Agent表现                                             │
│                                 │                           │
│                                 ▼ 监督指导                   │
│                                 │                           │
│  🧠 Strategic Supervisor (战略规划层)                        │
│  • 生成初始测试计划                                           │
│  • 每轮动态调整策略                                           │
│  • 基于执行结果修改方案                                       │
│                                 │                           │
│                                 ▼ 任务分配                   │
│                                 │                           │
│  👷 Worker Agent (执行层)                                     │
│  • ReAct循环：推理→行动→观察→反思                            │
│  • GLM-4.6模型，快速执行                                     │
│  • 工具调用：execute_python, nuclei, dirscan等             │
│                                 │                           │
│  💡 Payload Master (载荷生成层)                               │
│  • 每3轮提供测试指导                                         │
│  • 识别漏洞类型并建议载荷                                     │
│  • 进化思路说明                                               │
│                                 │                           │
│                                 ▼ 分析报告                   │
│                                 │                           │
│  📊 Report Supervisor (报告生成层)                            │
│  • 分析对话历史                                               │
│  • 提取漏洞信息                                               │
│  • 生成攻击路径                                               │
└─────────────────────────────────────────────────────────────┘
```

---

## 🌟 核心特性

### 1. 🤖 多Agent智能协作

- **🧑‍⚖️ Meta Supervisor (元监督层)**
  - 每3轮生成元层洞察和决策
  - 自主决策测试停止时机
  - 模式感知：CTF激进 vs RealWorld深度
  - 分析Agent表现并给出建议

- **🧠 Strategic Supervisor (战略规划层)**
  - 生成初始测试计划
  - 每轮动态调整测试策略
  - 基于执行结果优化方案

- **👷 Worker Agent (执行层)**
  - GLM-4.6模型，快速响应
  - ReAct执行框架
  - 集成工具调用和结果分析

- **💡 Payload Master (载荷大师)**
  - 每3轮提供专业测试指导
  - 识别漏洞类型并生成载荷
  - 攻击思路进化说明

- **📊 Report Supervisor (报告生成层)**
  - 分析完整对话历史
  - 自动提取漏洞信息
  - 重建攻击路径并生成报告

### 2. 📚 52+ 攻击知识库

基于**105个真实案例**提取的攻击知识库，包含：

- **IDOR攻击** (5个文档)
  - URL参数枚举、POST修改、Cookie篡改
  - JWT令牌攻击、间接对象引用

- **注入攻击** (15个文档)
  - SQL注入、布尔盲注、时间延迟注入
  - 命令注入、过滤绕过技术
  - SSTI模板注入、沙箱逃逸
  - NoSQL注入、OGNL注入

- **XSS攻击** (5个文档)
  - 反射型、存储型、DOM型XSS
  - JSFuck编码绕过、过滤绕过技术

- **文件相关** (8个文档)
  - 文件上传漏洞、LFI/RFI
  - 路径遍历、日志注入RCE

- **权限相关** (10个文档)
  - JWT令牌攻击、OAuth绕过
  - 权限提升、业务逻辑漏洞

- **其他漏洞** (20+文档)
  - SSRF、XXE、反序列化
  - 竞态条件、密码学攻击
  - API安全、GraphQL注入

### 3. 🔧 集成工具

| 工具名称 | 类型 | 功能描述 |
|---------|------|----------|
| **execute_python** | Python沙箱 | Docker容器隔离执行，512MB内存，预装渗透库 |
| **nuclei_scan** | 漏洞扫描 | 11,000+CVE模板，支持严重度过滤 |
| **dirscan** | 目录扫描 | 快速发现隐藏路径和目录 |
| **query_knowledge** | 知识库查询 | RAG检索52+攻击知识文档 |
| **kali_execute** | Kali工具 | 执行预装的渗透测试工具 |

### 4. 🎨 实时可视化界面

- **Dashboard** - 任务统计、实时监控面板
- **Monitor** - 多Agent消息流实时展示
- **Report** - 自动生成的漏洞报告
- **TaskList** - 智能任务列表管理
- **Settings** - 动态配置管理

### 5. 💾 智能上下文管理

- **LangChain集成** - 支持120K Token上下文
- **智能压缩** - 自动压缩历史对话
- **对话恢复** - 支持历史对话完整恢复
- **Token优化** - 大幅降低API成本

### 6. 🎯 双模式支持

#### 🚩 CTF模式
- 激进攻击策略，快速寻找FLAG
- 自动提交功能
- 支持自定义目标

#### 🛡️ RealWorld模式
- 稳健测试策略
- 全面漏洞评估
- 专业报告生成

### 5. 💻 现代化技术栈

- **后端**: FastAPI + Python 3.10+，全异步架构
- **前端**: Vue 3 + TypeScript + Element Plus
- **数据库**: SQLite + aiosqlite
- **容器**: Docker + Docker Compose
- **AI**: OpenAI API兼容模型
- **RAG**: 支持Embedding和Rerank模型

---

## 🚀 快速开始

### 前置要求

- Python 3.10+
- Node.js 18+
- Docker 20.10+ & Docker Compose
- OpenAI API Key 或兼容的LLM API

### 🐳 方式一：Docker Compose部署

```bash
# 1. 克隆项目
git clone https://github.com/hexian2001/H-pentest.git
cd H-pentest

# 2. 配置API Key
# 编辑 config.json 文件，填入你的API Keys
# - openai.api_key: LLM API Key (如智谱AI)
# - dashscope.api_key: 阿里云Embedding Key

# 3. 启动服务
docker-compose up -d

# 访问地址
# 前端: http://localhost:5173
# 后端: http://localhost:8000
# API文档: http://localhost:8000/docs
```

### 👻 方式二：本地开发

#### 后端启动

```bash
# 1. 安装Python依赖
cd backend
pip install -r requirements.txt

# 2. 配置API Keys
# 编辑 ../config.json 文件，配置API Keys
# - openai.api_key: LLM API Key (如智谱AI)
# - dashscope.api_key: 阿里云Embedding Key

# 3. 初始化数据库
python init_db.py

# 4. 启动后端服务
python -m app.main
```

#### 前端启动

```bash
# 1. 安装Node.js依赖
cd frontend
npm install

# 2. 启动开发服务器
npm run dev
```

---

## 📊 系统架构

### 技术架构

```
Frontend (Vue 3 + TypeScript)
├── Element Plus UI组件库
├── Pinia状态管理
├── Vue Router路由
├── Axios HTTP客户端
├── ECharts数据可视化
├── XTerm.js终端模拟
└── Vite构建工具

Backend (FastAPI)
├── Python 3.10+
├── 异步架构设计
├── WebSocket实时通信
├── SQLite + aiosqlite
├── CORS支持
└── 自动化API文档

AI Agent Engine
├── 三层决策架构
├── OpenAI API集成
├── RAG知识库检索
├── 上下文管理
├── Python沙箱执行
└── 智能工具调用

Infrastructure
├── Docker容器化
├── Docker Compose
├── Kali Linux工具集
└── 日志与监控
```

### 工作流程

```
渗透测试流程
┌─────────────────┐
│ 1. 创建任务      │
├─────────────────┤
│ 2. Meta监督      │ - 检测无效循环
│                 | - 智能干预
├─────────────────┤
│ 3. Strategic规划 │ - 任务分解
│                 | - 优先级管理
├─────────────────┤
│ 4. Worker执行    │ - ReAct循环
│                 | - 工具调用
├─────────────────┤
│ 5. 结果分析      │
└─────────────────┘
```

---

## 🎮 使用指南

### Web界面
![](https://github.com/hexian2001/tuchuang1/blob/main/dashborad1.png?raw=true)
![](https://github.com/hexian2001/tuchuang1/blob/main/monitor1.png?raw=true)
![](https://github.com/hexian2001/tuchuang1/blob/main/monitor2.png?raw=true)
![](https://github.com/hexian2001/tuchuang1/blob/main/report1.png?raw=true)
![](https://github.com/hexian2001/tuchuang1/blob/main/report2.png?raw=true)
![](https://github.com/hexian2001/tuchuang1/blob/main/report3.png?raw=true)

访问 **http://localhost:5173** 进入主界面：

1. **Dashboard** - 查看任务概览和系统状态
2. **TaskList** - 管理渗透测试任务列表
3. **Monitor** - 实时监控测试进度
   - WebSocket实时日志
   - AI思考过程展示
   - 工具执行状态
4. **Report** - 查看和导出测试报告
5. **Settings** - 配置系统和参数

### API接口

主要API端点：

#### 任务管理
- `POST /api/v1/tasks/` - 创建新任务
- `GET /api/v1/tasks/` - 获取任务列表
- `GET /api/v1/tasks/{task_id}` - 获取任务详情
- `POST /api/v1/tasks/{task_id}/intervention` - 人工干预
- `POST /api/v1/tasks/{task_id}/stop` - 停止任务
- `DELETE /api/v1/tasks/{task_id}` - 删除任务

#### 实时通信
- `WebSocket /api/v1/ws/{task_id}` - 实时消息推送
- `GET /api/v1/tasks/{task_id}/messages` - 获取消息历史
- `GET /api/v1/tasks/{task_id}/messages/latest` - 最新消息

#### 对话和上下文
- `GET /api/v1/tasks/{task_id}/conversations` - 获取对话历史
- `GET /api/v1/context/info` - 上下文信息

#### 配置管理
- `GET /api/v1/config/all` - 获取所有配置
- `POST /api/v1/config/agent` - 更新Agent配置
- `POST /api/v1/config/api` - 更新API配置
- `POST /api/v1/config/tools/{tool_name}` - 更新工具配置

详细API文档访问：http://localhost:8000/docs

---

## 🏗️ 项目结构

```
H-pentest/
├── backend/                 # FastAPI后端
│   ├── app/                # 应用核心
│   │   ├── api/           # REST API路由
│   │   │   ├── tasks.py   # 任务管理
│   │   │   ├── websocket_api.py # WebSocket
│   │   │   ├── messages.py # 消息处理
│   │   │   ├── conversations.py # 对话管理
│   │   │   ├── context.py # 上下文管理
│   │   │   └── config.py  # 配置管理
│   │   ├── core/          # 核心配置
│   │   ├── db/            # 数据库模型
│   │   ├── models/        # 数据模型
│   │   ├── schemas/       # API模式
│   │   └── services/      # 业务服务
│   │   └── main.py        # FastAPI入口
│   ├── agent/             # 🔥 AI Agent核心
│   │   ├── core/          # Agent引擎
│   │   │   ├── agent.py   # 主Agent
│   │   │   ├── llm.py     # LLM客户端
│   │   │   └── context_manager.py # 上下文管理
│   │   ├── supervisors/   # 监督层
│   │   │   ├── meta.py    # 元监督
│   │   │   ├── strategic.py # 战略监督
│   │   │   ├── payload_master.py # 载荷管理
│   │   │   └── report_supervisor.py # 报告监督
│   │   ├── planning/      # 规划层
│   │   │   └── dynamic_planner.py # 动态规划
│   │   ├── tools/         # 工具集成
│   │   │   ├── base.py    # 工具基类
│   │   │   ├── execute_python.py # Python沙箱
│   │   │   ├── knowledge.py # 知识库查询
│   │   │   ├── dirscan.py # 目录扫描
│   │   │   └── nuclei.py  # 漏洞扫描
│   │   ├── preprocessing/ # 预处理
│   │   └── runner.py      # 执行器
│   ├── requirements.txt   # Python依赖
│   └── init_db.py        # 数据库初始化
│
├── frontend/               # Vue 3前端
│   ├── src/
│   │   ├── components/    # Vue组件
│   │   ├── views/         # 页面视图
│   │   │   ├── Dashboard.vue
│   │   │   ├── Monitor.vue
│   │   │   ├── Report.vue
│   │   │   ├── Settings.vue
│   │   │   ├── TaskList.vue
│   │   │   └── TestContext.vue
│   │   ├── services/      # API服务
│   │   ├── stores/        # Pinia状态管理
│   │   ├── router/        # 路由配置
│   │   └── styles/        # 样式文件
│   ├── package.json       # Node.js依赖
│   ├── vite.config.ts     # Vite配置
│   └── Dockerfile         # 前端镜像
│
├── knowledge/              # 📚 知识库
│   └── know/              # 50+攻击知识文档
│       ├── 00-INDEX.md    # 知识库索引
│       ├── SQL注入-*.md   # SQL注入相关
│       ├── XSS-*.md       # XSS攻击
│       ├── SSTI-*.md      # 模板注入
│       ├── IDOR-*.md      # 权限漏洞
│       ├── LFI-*.md       # 文件包含
│       ├── 命令注入-*.md  # 命令注入
│       └── ...            # 更多漏洞类型
│
├── docker/                 # Docker配置
│   └── Dockerfile.kali    # Kali容器定义
│
├── .env.example           # 环境变量示例
├── docker-compose.yml     # 容器编排
├── build_embedding_cache.py # 构建向量缓存
└── CONFIG.md             # 配置说明
```

---

## 🔧 配置说明

### 主配置文件 (config.json)

```json
{
  "app": {
    "name": "H-Pentest 2.0",
    "version": "2.0.0",
    "debug": false
  },
  "openai": {
    "api_key": "your-api-key-here",
    "base_url": "https://open.bigmodel.cn/api/coding/paas/v4",
    "model": "GLM-4.6",
    "temperature": 0.7,
    "max_tokens": 8192
  },
  "dashscope": {
    "api_key": "your-dashscope-key-here",
    "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1"
  },
  "embedding": {
    "model": "text-embedding-v3",
    "api_key": "your-embedding-key-here"
  },
  "rerank": {
    "model": "gte-rerank",
    "api_key": "your-rerank-key-here"
  },
  "rag": {
    "enabled": true,
    "top_k": 5,
    "rerank_enabled": true,
    "score_threshold": 0.3
  },
  "process": {
    "max_concurrent_tasks": 3,
    "task_timeout": 3600
  }
}
```

### 关键配置项

- **OpenAI配置**: 智谱AI GLM-4.6模型设置
- **多LLM配置**: Worker/Meta/Strategic不同参数
- **DashScope**: 阿里云Embedding和Rerank服务
- **RAG配置**: 知识库检索(top_k=5, score_threshold=0.3)
- **进程配置**: 最大并发3任务，超时3600秒
- **WebSocket**: 心跳30秒，消息队列1000

### Docker配置

#### docker-compose.yml 服务说明
- **backend**: FastAPI后端服务 (端口8000)
  - 卷挂载: 后端代码、知识库、缓存、日志、Docker socket
- **frontend**: Vue 3前端服务 (端口5173)
  - 热重载: 开发时代码实时更新
- **kali-sandbox**: Kali Linux工具容器
  - 预装工具: nmap, sqlmap, nikto, gobuster, masscan, hydra等
  - 持久化工作目录: /pentest

---

## 🛡️ 安全特性

### Docker隔离环境

- **Python沙箱容器**
  - 每次代码执行独立容器
  - 非 root 用户 (UID:1000)
  - 512MB 内存限制
  - 执行完成后自动销毁

- **Kali Linux工具容器**
  - 预装渗透测试工具集
  - Root权限执行环境
  - 持久化会话管理
  - Bridge网络隔离

### 执行安全

```python
# AI生成的Python代码在隔离容器中执行
code = """
import requests
response = requests.get('http://target.com')
# 即使包含恶意代码，也在容器中隔离执行
"""
```

---

## 🎨 界面展示

### 功能页面

#### Dashboard - 仪表盘
- 任务统计: 总数、运行中、已完成、失败、漏洞数、FLAG数
- 漏洞分布可视化图表
- 运行中任务实时监控
- 创建新任务快速入口

#### Monitor - 实时监控
- 多Agent消息流实时展示
  - LLM思考和响应
  - 工具执行结果
  - Meta监督洞察
  - Payload大师指导
- 可折叠的工具结果
- 人工干预操作面板

#### TaskList - 任务列表
- 智能过滤: 默认显示运行中+暂停+最近3个完成/失败
- 任务状态图标
- 快速操作: 暂停、恢复、删除、查看报告

#### Report - 报告页面
- 自动提取的漏洞信息
- 攻击路径重建
- 导出功能

#### Settings - 配置管理
- Agent参数配置
- API配置管理
- 工具开关设置

---

## 📊 性能特点

- **全异步FastAPI架构** - 支持高并发任务执行
- **多LLM实例协作** - Worker/Meta/Strategic/Payload/Report分工
- **WebSocket实时通信** - 流式展示所有Agent思考过程
- **智能上下文管理** - LangChain压缩，支持120K Token
- **智能知识检索** - RAG检索52+攻击知识文档
- **多Agent决策机制** - 避免无效循环，确保测试效果

---

## 🤝 开发指南

### 本地开发

```bash
# 1. 配置API Keys
cp config.json.example config.json
# 编辑 config.json，配置智谱AI和阿里云API Keys

# 2. 后端开发
cd backend
pip install -r requirements.txt
# 初始化数据库
python init_db.py
# 启动后端服务
python -m app.main

# 3. 前端开发
cd frontend
npm install
# 启动开发服务器（热重载）
npm run dev

# 4. 构建知识库向量缓存
cd ..
python build_embedding_cache.py
```

### 添加新工具

1. 在 `backend/agent/tools/` 创建新工具类
2. 继承 `BaseTool` 基类
3. 实现 `execute` 方法
4. 定义工具参数

### 扩展知识库

1. 在 `knowledge/know/` 添加Markdown文档
2. 包含实际攻击Payload
3. 更新 `00-INDEX.md` 索引

---

## ❓ 常见问题

**Q: 如何配置API Keys？**
A: 编辑 `config.json` 文件：
- openai.api_key: 填入智谱AI或其他LLM的API Key
- dashscope.api_key: 填入阿里云DashScope API Key
- embedding.api_key: 用于向量化的API Key

**Q: 支持哪些LLM模型？**
A: 支持OpenAI API兼容的模型，默认配置为智谱AI GLM-4.6

**Q: 知识库如何构建？**
A: 运行 `python build_embedding_cache.py` 构建向量缓存

**Q: Docker是必需的吗？**
A: 是的，Python代码执行需要Docker沙箱环境

**Q: 如何启用RAG功能？**
A: 在config.json中设置 rag.enabled 为 true，并配置相应的API Key

---

## 🛡️ 免责声明

本工具仅用于**合法授权的安全测试**。使用者需：

1. 获得目标系统的**书面授权**
2. 在**隔离环境**中进行测试
3. 遵守当地**法律法规**
4. 对使用后果承担责任

---

## 📄 许可证

MIT License

---

## 🙏 致谢

- 腾讯云黑客松 - 提供竞赛平台
- OpenAI - 提供强大的LLM能力
- FastAPI & Vue 3 - 现代化Web框架
- 所有贡献者的支持

---

**⭐ 觉得有用请给个Star！⭐**

Made with ❤️ by HRP Team

继续创建以下文件：
1. Message Consumer（消息消费者）
2. Agent Runner（子进程入口）
3. 简化版Agent核心
4. LLM Client（异步）
5. FastAPI Main
6. API路由
7. 前端框架

## 快速开始

```bash
# 1. 安装依赖
cd /home/H-pentest/H-pentest/backend
pip install -r requirements.txt

# 2. 配置环境变量
cp .env.example .env
# 编辑.env文件，设置OPENAI_API_KEY等

# 3. 初始化数据库
python -m alembic init alembic
python -m alembic revision --autogenerate -m "init"
python -m alembic upgrade head

# 4. 启动后端
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 5. 启动前端（另一个终端）
cd ../frontend
npm install
npm run dev
```

## 架构特点

- 🚀 完全异步（asyncio + FastAPI）
- 🔄 进程隔离（multiprocessing）
- 📡 实时通信（WebSocket + Queue）
- 💾 双重持久化（WebSocket + Database）
- 🎯 统一输出（所有输出通过Queue）
