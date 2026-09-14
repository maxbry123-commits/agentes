# AI-Pentest: 基于大模型的自动化渗透测试系统

<div align="center">

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Vue](https://img.shields.io/badge/Vue-3.4+-green.svg)
![TDesign](https://img.shields.io/badge/TDesign-1.13+-purple.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

**利用大语言模型的智能渗透测试自动化系统**

[功能特性](#功能特性) • [快速开始](#快速开始) • [系统架构](#系统架构) • [前端界面](#前端界面)

</div>

---

## 项目简介

AI-Pentest 是一个基于大语言模型（LLM）的自动化安全测试平台，通过AI Agent实现渗透测试流程的智能化和自动化。

### 核心特点

- 🤖 **LLM驱动决策** - 利用大模型的理解与推理能力进行智能决策
- 🔄 **Agent协作架构** - 多Agent协作完成渗透测试全流程
- 🛠️ **工具集成丰富** - 集成Nmap、Nikto、Hydra等主流安全工具
- 📊 **可视化Dashboard** - 暗色系现代化前端界面
- 📝 **多格式报告** - 支持JSON/HTML/Markdown报告输出

## 项目结构

```
AI_Pentest/
├── backend/                    # 后端服务
│   ├── agents/                # Agent模块
│   │   ├── base.py           # Agent基类
│   │   ├── recon_agent.py    # 信息收集Agent
│   │   ├── vuln_agent.py     # 漏洞分析Agent
│   │   ├── exploit_agent.py  # 漏洞利用Agent
│   │   └── report_agent.py   # 报告生成Agent
│   ├── llm/                   # 大模型接口
│   │   ├── base.py           # LLM基类
│   │   └── __init__.py       # 多模型客户端
│   ├── tools/                 # 安全工具集成
│   │   ├── network_scanner.py
│   │   ├── web_scanner.py
│   │   ├── vulnerability_scanner.py
│   │   ├── brute_force.py
│   │   └── tool_manager.py
│   ├── core/                  # 核心模块
│   │   ├── orchestrator.py   # 流程编排
│   │   ├── decision_engine.py# 决策引擎
│   │   └── report_generator.py
│   ├── utils/                 # 工具函数
│   ├── config.yaml           # 配置文件
│   └── main.py               # 后端入口
│
├── frontend/                   # 前端服务
│   └── ai-pentest-frontend/
│       ├── src/
│       │   ├── views/        # 页面视图
│       │   │   ├── Dashboard.vue
│       │   │   ├── Targets.vue
│       │   │   ├── Scan.vue
│       │   │   ├── Vulnerabilities.vue
│       │   │   ├── Reports.vue
│       │   │   ├── Tools.vue
│       │   │   └── Settings.vue
│       │   ├── components/   # 组件
│       │   ├── App.vue
│       │   └── main.ts
│       └── package.json
│
└── README.md
```

## 快速开始

### 后端部署

```bash
# 进入后端目录
cd backend

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r ../requirements.txt

# 配置API密钥
cp .env.example .env
# 编辑 .env 填入LLM API密钥

# 启动服务
python main.py --target 192.168.1.1 --mode auto
```

### 前端部署

```bash
# 进入前端目录
cd frontend/ai-pentest-frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev

# 构建生产版本
npm run build
```

## 前端界面

### Dashboard 控制台

暗色系设计的Dashboard，提供：

- 📈 **统计卡片** - 活跃目标、扫描任务、漏洞数量、报告数量
- 📊 **活动趋势图** - 可视化测试活动数据
- 🔄 **实时任务监控** - 扫描任务进度和状态
- 🤖 **Agent状态面板** - 各Agent运行状态
- 📝 **活动日志** - 实时操作记录

### 功能模块

| 模块 | 功能 |
|------|------|
| 控制台 | 系统概览、实时监控、数据可视化 |
| 目标管理 | 添加/管理测试目标、查看目标详情 |
| 扫描任务 | 创建扫描任务、查看进度、历史记录 |
| 漏洞管理 | 漏洞列表、严重程度分类、修复状态 |
| 测试报告 | 报告列表、多格式下载、风险评级 |
| 工具集成 | 安全工具管理、安装状态、使用统计 |
| 系统设置 | LLM配置、系统参数、安全设置 |

## Agent协作架构

```
┌─────────────────────────────────────────────────────────────┐
│                    Orchestrator (编排器)                      │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐    │
│  │ Recon    │  │ Vuln     │  │ Exploit  │  │ Report   │    │
│  │ Agent    │→│ Agent    │→│ Agent    │→│ Agent    │    │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘    │
├─────────────────────────────────────────────────────────────┤
│                    Decision Engine (决策引擎)                 │
├─────────────────────────────────────────────────────────────┤
│                    Tool Manager (工具管理器)                  │
│  Nmap | Nikto | Dirb | Hydra | SearchSploit | ...          │
└─────────────────────────────────────────────────────────────┘
```

## 支持的LLM

| 提供商 | 模型 | 特点 |
|--------|------|------|
| DeepSeek | deepseek-chat | 推荐默认 |
| 智谱AI | GLM-4 | 中文优化 |
| 阿里云 | Qwen-Turbo | 快速响应 |
| OpenAI | GPT系列 | 国际通用 |

## 安全说明

⚠️ **重要提醒**

- 本系统仅供合法授权的安全测试使用
- 在未授权目标上使用可能违反法律法规
- 请确保在受控环境中进行测试
- 生成的报告可能包含敏感信息，请妥善保管

## 技术栈

### 后端
- Python 3.8+
- Requests, PyYAML
- python-nmap, paramiko

### 前端
- Vue 3.4+
- TypeScript 5.0+
- TDesign Vue Next
- ECharts
- TailwindCSS

## 许可证

本项目采用 MIT 许可证

---

<div align="center">

**Made with ❤️ for Security Research**

</div>
