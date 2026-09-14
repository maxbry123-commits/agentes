# 🐋 OpenWhale - 渗透测试智能体

基于 OpenAI 兼容 SDK 构建的渗透测试 AI 智能体，用于参加腾讯云黑客松智能渗透挑战赛。

## 功能特性

- 🤖 **多智能体分工**：支持"侦察-检测-利用"流程，基于主从模式协作
- 🔌 **MCP 协议接入**：通过标准 MCP 协议直接接入比赛平台
- 📊 **实时 Web 监控**：极简 Web 前端，实时展示智能体运行过程
- 📝 **完整日志追踪**：使用 loguru + rich，每次运行保存全量日志
- 🔒 **环境变量配置**：API Key 等敏感信息通过环境变量注入，避免硬编码

## 快速开始

### 1. 安装依赖

```bash
# 使用 uv 安装依赖（推荐）
pip install uv
uv sync
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env，填写以下必填项：
# AGENT_TOKEN=<YOUR_AGENT_TOKEN>
# SERVER_HOST=<SERVER_HOST>
# AGENT_BACKEND=openai_compat
# 切换 Claude Code SDK：AGENT_BACKEND=claude_code
# 切换 DeepAgents：AGENT_BACKEND=deepagents
# TOKENHUB_API_KEY=<YOUR_LLM_API_KEY>
# CLAUDE_MODEL=<可选，默认沿用 MODEL_ID>
# CLAUDE_PERMISSION_MODE=bypassPermissions
# CLAUDE_ALLOWED_TOOLS=Bash,mcp__challenge__list_challenges
```

### 3. 运行智能体

```bash
uv run openwhale


# 仅启动 Web 界面
uv run openwhale-web
```

运行后：
- 智能体将自动连接 MCP 服务器，按比赛流程执行赛题并输出执行报告
- Web 界面在 `http://localhost:8080` 实时展示运行过程

### 4. 离线持续运行（延时遥控）

当你希望离线持续跑题：脚本启动后先等待 60 秒，然后反复调用智能体，直到全部赛题完成才退出。

```bash
uv run python scripts/delayed_autopilot.py
```

可通过 `.env` 调整行为：
- `AUTOPILOT_START_DELAY_SECONDS`：首轮启动前延时（默认 60）
- `AUTOPILOT_CYCLE_INTERVAL_SECONDS`：轮次间隔（默认 5）
- `AUTOPILOT_MAX_CYCLES`：最大轮次，`0` 为不限
- `AUTOPILOT_AGENT_COMMAND`：每轮实际执行命令（默认 `uv run openwhale`）

## 项目结构

```
OpenWhale/
├── src/openwhale/
│   ├── main.py           # 主入口（启动器）
│   ├── agent.py          # 兼容导出（保留旧导入路径）
│   ├── agents/
│   │   ├── base.py       # 智能体基类与统一执行框架
│   │   ├── factory.py    # 智能体工厂
│   │   ├── openai_agent.py # OpenAI 兼容实现
│   │   ├── deepagents_agent.py # DeepAgents 实现
│   │   ├── claude_code_agent.py # Claude Code SDK 实现
│   │   └── prompts.py    # 共享提示词
│   ├── web/
│   │   ├── app.py        # Web 前端（FastAPI + SSE）
│   │   └── templates/
│   │       └── index.html
│   └── util/
│       ├── __init__.py
│       ├── mcp_client.py     # MCP 协议客户端
│       └── logging_config.py # 日志配置（loguru + rich）
├── logs/                 # 运行时自动创建的日志目录
├── .env.example          # 环境变量模板
├── pyproject.toml        # 项目依赖配置（uv）
└── README.md
```

## 环境变量说明

| 变量名 | 必填 | 默认值 | 说明 |
|--------|------|--------|------|
| `AGENT_TOKEN` | ✅ | - | 竞赛平台 Agent Token（MCP 鉴权） |
| `SERVER_HOST` | ✅ | - | 竞赛平台 Server Host（自动拼接 `/mcp`） |
| `TOKENHUB_API_KEY` | ✅ | - | OpenAI 兼容模型 API Key |
| `MCP_SERVER_URL` | ❌ | 自动拼接 | 可手动覆盖 MCP 地址 |
| `AGENT_BACKEND` | ❌ | `openai_compat` | 智能体基座实现选择（含 `deepagents`） |
| `MODEL_BASE_URL` | ❌ | `https://tokenhub.tencentmaas.com/v1` | OpenAI 兼容模型网关地址 |
| `MODEL_NAME` | ❌ | `MiniMax-M2.7` | 模型展示名称 |
| `MODEL_ID` | ❌ | `ep-jsc7o0kw` | 实际调用的模型 ID |
| `DEEPAGENTS_RECURSION_LIMIT` | ❌ | `64` | DeepAgents 图递归上限 |
| `DEEPAGENTS_TIMEOUT_SECONDS` | ❌ | `300` | DeepAgents 单次运行超时（秒） |
| `DEEPAGENTS_REPEAT_CALL_LIMIT` | ❌ | `4` | 相同工具+参数允许重复调用次数 |
| `DEEPAGENTS_BASH_TIMEOUT_SECONDS` | ❌ | `120` | Bash 工具命令超时（秒） |
| `DEEPAGENTS_BASH_MAX_OUTPUT_CHARS` | ❌ | `8000` | Bash 工具输出截断长度 |
| `DEEPAGENTS_TRACE_ENABLED` | ❌ | `false` | 是否输出 trace 阶段日志 |
| `DEEPAGENTS_TRACE_VERBOSE` | ❌ | `false` | 是否输出更细的原始事件流 |
| `CLAUDE_MODEL` | ❌ | `MODEL_ID` | Claude Code SDK 使用的模型（默认沿用 MiniMax 模型 ID） |
| `CLAUDE_CLI_PATH` | ❌ | - | Claude Code CLI 可执行文件路径 |
| `CLAUDE_API_KEY` | ❌ | `MODEL_API_KEY` | Claude SDK 专用 API Key（可覆盖） |
| `CLAUDE_BASE_URL` | ❌ | `MODEL_BASE_URL` | Claude SDK 专用网关地址（可覆盖） |
| `CHALLENGE_MCP_SERVER_NAME` | ❌ | `challenge` | 主赛题 MCP 服务名，用于默认工具命名 |
| `CLAUDE_TOOLS_PRESET` | ❌ | `claude_code` | Claude Code 工具集预设 |
| `CLAUDE_PERMISSION_MODE` | ❌ | `bypassPermissions` | Claude SDK 工具权限模式 |
| `CLAUDE_ALLOWED_TOOLS` | ❌ | 自动生成 | 允许自动执行的工具（逗号分隔） |
| `CLAUDE_DISALLOWED_TOOLS` | ❌ | - | 禁用工具（逗号分隔） |
| `EXTRA_MCP_SERVERS_JSON` | ❌ | - | 额外 MCP Server JSON 配置（对象） |
| `EXTRA_MCP_SERVERS_FILE` | ❌ | - | 额外 MCP Server 配置文件路径 |
| `LOG_LEVEL` | ❌ | `INFO` | 日志级别 |
| `WEB_ENABLED` | ❌ | `true` | 是否启动 Web 界面 |
| `WEB_HOST` | ❌ | `0.0.0.0` | Web 服务监听地址 |
| `WEB_PORT` | ❌ | `8080` | Web 服务端口 |

## 技术栈

- **运行时**：Python 3.12+ / [uv](https://github.com/astral-sh/uv)
- **AI 基座**：[OpenAI Python SDK](https://github.com/openai/openai-python)
- **Deep Agent 编排**：[deepagents](https://github.com/langchain-ai/deepagents) + [LangChain](https://github.com/langchain-ai/langchain)
- **MCP 协议**：[Model Context Protocol Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- **日志**：[loguru](https://github.com/Delgan/loguru) + [rich](https://github.com/Textualize/rich)
- **Web**：[FastAPI](https://fastapi.tiangolo.com/) + Server-Sent Events

### Claude Code 扩展示例

可通过额外 MCP 接入 RAG 或渗透扫描器（与主挑战 MCP 并行）：

```json
{
	"rag": {
		"type": "http",
		"url": "http://127.0.0.1:9001/mcp"
	},
	"scanner": {
		"type": "stdio",
		"command": "python",
		"args": ["-m", "my_scanner_mcp"]
	}
}
```

将上面 JSON 写入文件后设置：

```bash
EXTRA_MCP_SERVERS_FILE=/path/to/mcp_servers.json
```

### 关于 MiniMax 与 Claude Code SDK

- `claude-agent-sdk`/Claude Code CLI 会校验模型名，常见 OpenAI 风格模型标识（如 `ep-...`、`MiniMax-...`）通常会被拒绝。
- 如果目标是稳定调用 MiniMax（OpenAI 兼容接口），建议使用 `AGENT_BACKEND=openai_compat`。
- 若必须使用 `AGENT_BACKEND=claude_code`，请提供 Anthropic 兼容网关，并设置可识别的 Claude 模型名。
