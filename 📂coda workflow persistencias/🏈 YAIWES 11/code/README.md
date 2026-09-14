# LLM-CTF-Solver

> 基于 [BUUCTF_Agent](https://github.com/MuWinds/BUUCTF_Agent) 二次开发 | Apache 2.0 协议
> [gehewu](https://github.com/gehewu) / LLM-CTF-Solver

基于大语言模型的双模式安全自动化 Agent，支持 **CTF 自动解题** 与 **授权渗透测试**，提供 CLI / TUI / Web UI 三种交互入口。系统以 ReAct 范式为核心，配合三层解析回退、六维僵局检测、三层记忆与关键事实防丢、三级缓存、RAG 知识库与攻击面结构化管理，保障长任务鲁棒性与成本可控。

---

## 目录

- [核心架构](#核心架构)
- [快速开始](#快速开始)
- [使用指南](#使用指南)
- [工具系统](#工具系统)
- [核心特性](#核心特性)
- [Web API](#web-api)
- [配置参考](#配置参考)
- [项目结构](#项目结构)
- [Docker 部署](#docker-部署)
- [安全机制](#安全机制)
- [测试](#测试)
- [故障排查](#故障排查)
- [License](#license)

---

## 核心架构

```
┌──────────────────────────────────────────────────────────┐
│  入口层                                                   │
│  main.py ........... CLI 解题 / 渗透                       │
│  tui_main.py ....... TUI 终端界面 (Textual)                │
│  backend/ .......... Web UI (FastAPI + Vue 3 + WebSocket) │
│  cli.py ............ 知识库管理                            │
│  log_viewer.py ..... 日志回溯                              │
│  benchmark_run.py .. 基准测试                              │
└──────────────────────┬───────────────────────────────────┘
                       │
┌──────────────────────▼───────────────────────────────────┐
│  Workflow — 编排层                                        │
│  CTF / 渗透双流程 · 自动学习 · 质量门控 · 报告生成         │
│  try/finally 保护（中断仍生成 writeup / 报告）             │
└──────────────────────┬───────────────────────────────────┘
                       │
┌──────────────────────▼───────────────────────────────────┐
│  SolveAgent — 推理引擎                                    │
│  原生 tool_calls + 2 层回退 · 阶段感知 (recon→exploit)    │
│  6 维僵局检测 · LLM/成本双熔断 · 工具模式过滤              │
│  断点续跑（恢复重跑 step-0 + MCP 重激活）                  │
└──┬──────────┬──────────┬──────────┬──────────────────────┘
   │          │          │          │
   ▼          ▼          ▼          ▼
Analyzer   Memory    ToolUtils   KnowledgeBase
快速分析    三层记忆   模式过滤     ChromaDB
LLM 兜底   关键事实   动态发现     混合检索
            防丢      远程探测     自动学习
```

---

## 快速开始

### 环境要求

| 依赖 | 版本 | 用途 |
|------|------|------|
| Python | 3.10+ | 运行 Agent |
| LLM API | OpenAI 兼容格式 | 推理引擎（需支持 tool_calls） |
| Redis | 6+ | Web UI 消息队列（仅 Web 模式需要） |
| Node.js | 20+ | Web UI 前端构建（仅 Web 模式需要） |
| Kali Linux | — | SSH 远程执行环境（可选） |

### 安装

```bash
git clone https://github.com/gehewu/LLM-CTF-Solver.git
cd LLM-CTF-Solver
pip install -r requirements.txt
```

### 配置

1. 复制示例配置并填入真实值：

```bash
cp config.example.json config.json
```

2. 编辑 `config.json`，将 `sk-xxxx` 替换为你的 API Key，修改 SSH 连接信息：

```json
{
    "llm": {
        "solve_agent": {
            "model": "openai/deepseek-v4-pro",
            "api_key": "sk-xxxx",
            "api_base": "https://api.deepseek.com"
        }
    },
    "tool_config": {
        "ssh_shell": {
            "host": "192.168.56.101",
            "port": 22,
            "username": "kali",
            "password": "kali"
        }
    }
}
```

> `llm` 段的 4 个入口（solve_agent / analyzer / pre_processor / embedding）为必填项，每个入口需包含 `model`、`api_key`、`api_base` 三个字段。
>
> `config.example.json` 是项目配置模板，可安全上传；`config.json` 含真实 API Key，已加入 `.gitignore` 防止泄露。

**环境变量覆盖**（优先级高于 config.json）：

```bash
# 通用覆盖：所有 LLM 入口使用同一 Key
export LLM_API_KEY=sk-xxxx

# 逐个入口覆盖
export LLM_API_KEY_SOLVE_AGENT=sk-xxx
export LLM_API_KEY_ANALYZER=sk-xxx
```

验证连接：`python test_llm.py`

### 三种运行模式

#### CLI 模式

```bash
# CTF 解题
echo "你的CTF题目描述" > question.txt
python main.py --mode ctf

# 渗透测试
cat > scope.txt << 'EOF'
测试目标: 192.168.1.100, app.example.com
授权时间: 2026-01-01 至 2026-01-07
EOF
python main.py --mode pentest

# 常用参数
python main.py --mode ctf --auto          # 强制自动模式
python main.py --mode ctf --manual        # 强制手动模式（每步审批）
python main.py --mode ctf --resume        # 断点续跑
python main.py --mode ctf --export-writeup # 解题后导出 Writeup
python main.py --interactive              # 交互式选择模式和审批方式
```

#### TUI 终端模式

```bash
python tui_main.py
```

快捷键：`n` 新建 / `Enter` 恢复 / `Space` 暂停 / `Ctrl+S` 存档 / `?` 帮助 / `↑↓` 浏览步骤

#### Web UI 模式

```bash
# 1. 启动 Redis
docker compose up -d redis

# 2. 启动后端
python -m backend.server
# → http://localhost:8002
# → API 文档: http://localhost:8002/docs

# 3. 启动前端
cd frontend
npm install
npm run dev
# → http://localhost:5173
```

**页面导航**：

| 路径 | 功能 |
|------|------|
| `/` | 首页 — 任务列表 |
| `/session/new` | 新建任务 — 选择模式 → 输入题目 → 开始执行 |
| `/session/:taskId` | 执行面板 — 左侧时间线 + 右侧步骤详情 + HIL 审批弹窗 |
| `/kb` | 知识库管理 — 浏览/搜索/添加/维护 |
| `/status` | 连接测试 — LLM 测试 / Kali 环境探测 / MCP 状态 |

---

## 使用指南

### CTF 解题流程

1. 准备题目文件 `question.txt`，附件放入 `attachments/` 目录
2. 启动 Agent：`python main.py --mode ctf` 或通过 Web UI 提交
3. Agent 自动执行：题型分类 → 信息收集 → 漏洞利用 → Flag 提取
4. 发现 Flag 后自动确认（自动模式）或弹出确认对话框（手动模式）
5. 解题成功后自动学习，知识存入 ChromaDB 知识库
6. `--export-writeup` 时生成 Markdown / JSON 双格式 Writeup；Ctrl+C 中断仍会生成（标注"中断未取得 flag"）

### 渗透测试流程

1. 准备授权范围文档 `scope.txt`
2. 启动 Agent：`python main.py --mode pentest` 或通过 Web UI 提交
3. Agent 自动执行：攻击面枚举 → 漏洞发现 → 漏洞验证 → 凭据收集 → 横向移动
4. 报告自动生成到 `reports/` 目录（含 PoC、CVSS 向量、修复建议、攻击链路）
5. Ctrl+C 中断或达到步数上限时，报告仍然生成（try/finally 保护）

### 断点续跑

```bash
python main.py --mode ctf --resume
```

Agent 每隔 `checkpoint_interval` 步自动存档到 `checkpoints/`，以题目内容 MD5 为键，保留最近 3 个同键存档。恢复时会自动重跑步骤零上下文（从知识库匹配同类经验）与按题型激活的 MCP 工具，避免恢复后"未找到工具"或缺少经验参考。

### 日志回溯

```bash
python log_viewer.py list            # 列出所有会话
python log_viewer.py last            # 查看最近会话
python log_viewer.py show 1 --steps 3-8  # 查看指定会话的步骤范围
```

### 知识库管理

```bash
python cli.py kb stats               # 统计
python cli.py kb search "SQL注入"     # 搜索
python cli.py kb list                # 列表
python cli.py kb add                 # 交互添加
python cli.py kb export backup.json  # 导出
python cli.py kb import backup.json  # 导入
python cli.py kb reset -f            # 清空重建
```

### 基准测试

```bash
python benchmark_run.py                          # 运行全部用例
python benchmark_run.py --filter web             # 按分类过滤
python benchmark_run.py --parallel --workers 3   # 并行执行
python benchmark_run.py --timeout 300            # 单用例超时（秒）
python benchmark_run.py --report results.json    # 输出 JSON 报告
python benchmark_run.py --list                   # 列出可用用例
```

---

## 工具系统

Agent 内置 20+ 专业安全工具，覆盖 CTF 和渗透测试的主要场景。所有工具继承 `BaseTool` 抽象基类，通过反射自动发现注册。

### 模式过滤

每个工具通过类属性 `modes` 声明适用模式，`ToolUtils.load_tools()` 加载时按当前模式过滤，避免无关工具干扰 LLM 决策：

- `modes = None` — 全模式共享（基础工具：shell / python / network / jwt / file_analyzer / mcp 等）
- `modes = {"ctf"}` — CTF 专属（9 个：crypto_attacks / crypto_tools / codec / stego_tools / forensics_tools / reverse_tools / binary_analysis / android_tools / challenge_classifier）
- `modes = {"pentest"}` — 渗透专属（3 个：web_tools / exploit_templates / powershell_tools）

### 内置工具一览

| 工具 | 文件 | 模式 | 功能 |
|------|------|------|------|
| Shell 命令执行 | `ssh_shell.py` | 共享 | 在远程 Kali 执行命令，自动上传附件 |
| Python 代码执行 | `python.py` | 共享 | 本地（AST 沙箱）/ 远程 SSH 执行 |
| 网络工具 | `network.py` | 共享 | HTTP 请求 / DNS 解析 / 端口扫描 / 目录爆破 |
| Web 渗透 | `web_tools.py` | 渗透 | 技术栈识别 / SQLi / XSS / SSTI / LFI / 命令注入 / 文件上传 / 认证测试 / 全量扫描 |
| 密码学分析 | `crypto_tools.py` | CTF | 编码识别（30+） / 频率分析 / XOR 破解 / 古典密码 / 哈希识别（22 种） / 模式检测 |
| 密码学攻击 | `crypto_attacks.py` | CTF | RSA 攻击（Wiener/Fermat/共模/Hastad）/ CBC 翻转 / Vigenere / 仿射 / 模运算 |
| 编码/解码 | `codec.py` | CTF | base64/32/hex/url/unicode/rot13/caesar/morse/binary/xor 等；自动检测格式 |
| JWT 分析 | `jwt_tools.py` | 共享 | 解码 / 伪造 / 弱密钥爆破 / 漏洞扫描（none 算法/kid/jku/过期） |
| 文件分析 | `file_analyzer.py` | 共享 | Magic Byte 识别（60+ 签名）/ 字符串提取 / PE/ELF 分析 / 归档列表 / 正则搜索 |
| 逆向工程 | `reverse_tools.py` | CTF | 格式识别 / 反汇编 / 字符串分类 / 反分析检测 / 补丁建议 |
| 二进制/PWN | `binary_analysis.py` | CTF | checksec / 架构识别 / pwntools 辅助 / ROP gadget / one_gadget |
| 隐写分析 | `stego_tools.py` | CTF | LSB 提取 / 元数据 / 频域分析 / 附加数据检测 |
| 取证分析 | `forensics_tools.py` | CTF | PCAP 摘要 / HTTP 对象提取 / 文件雕刻（12 种签名）/ Hex 搜索 |
| 漏洞利用模板 | `exploit_templates.py` | 渗透 | 7 种利用模板（SQLi/SSTI/LFI/XSS/SSRF/CMDi/XXE） |
| Android 逆向 | `android_tools.py` | CTF | 反编译 / Manifest 分析 / 资源提取 |
| Windows 渗透 | `powershell_tools.py` | 渗透 | 25+ 预定义 PS 命令模板（侦查/凭据/持久化/域环境） |
| 题型分类 | `challenge_classifier.py` | CTF | 三维度分类（附件后缀 60+ / 描述关键词 80+ / 连接信息） |
| Flag 检测 | `flag_detector.py` | 共享 | 5 层检测（正则预扫 → 快速分析 → LLM 分析 → Pro 模型 → 用户确认） |
| MCP 适配器 | `mcp_adapter.py` | 共享 | MCP 协议（stdio/HTTP SSE），懒加载 + 超时自动重连 |

### MCP 外部工具集成

通过 `config.json` 的 `mcp_server` 段配置外部工具服务：

```json
"mcp_server": {
    "burp": {
        "type": "stdio",
        "command": "java",
        "args": ["-jar", "mcp-proxy.jar", "--sse-url", "http://127.0.0.1:9876"],
        "lazy": true,
        "catalog_desc": "Burp Suite — Web 渗透专用",
        "aliases": ["burpsuite", "burp_suite"],
        "auto_activate_for": ["web"]
    }
}
```

| 字段 | 说明 |
|------|------|
| `type` | 通信方式：`stdio` 或 `http`（SSE） |
| `lazy` | `true` = 按需加载（推荐）；`false` = 启动时连接 |
| `catalog_desc` | 注入 Prompt 的工具目录描述 |
| `aliases` | LLM 提及这些别名时触发懒加载 |
| `auto_activate_for` | CTF 题型分类命中时自动激活 |

> **断点续跑兼容**：MCP 子进程无法跨进程恢复，续跑时 Agent 会自动重新激活按题型匹配的 MCP 工具。

### 远程工具动态发现

当 LLM 提及本地未注册的 CLI 工具时，Agent 会自动通过 SSH 探测远程 Kali 环境是否安装了该工具，内置 80+ 常见安全工具映射。

---

## 核心特性

### ReAct 推理循环

每步执行 Think → Tool Call → Analyze 的循环，支持三层 tool_calls 解析回退：

```
原生 tool_calls（LLM function calling）
    → 成功：直接获得结构化 tool_calls
    → 无原生调用：堆栈法 JSON 提取（处理数组/嵌套参数）
    → JSON 失败：XML 解析 + general_next 回退模板
```

三层回退保障 LLM 输出格式不稳定时仍能提取工具调用，避免单次格式错误导致整步失败。

### 阶段感知

Agent 根据解题进度自动切换阶段：

- **recon** — 信息收集与攻击面枚举（CTF 最少 3 步，渗透最少 4 步）
- **exploit** — 漏洞利用与 Flag 提取
- **report** — 报告生成（仅渗透测试模式）

阶段切换条件结合僵局计数与覆盖率（关键事实数 / 工具多样性 / 近期进展），避免单步无进展就过早切换。每阶段对应不同 Prompt 模板键（`think_recon` / `think_exploit` / `think_report`），缺失时回退 `think_next`。

### 6 维僵局检测

| 维度 | 类型 | 判定条件 |
|------|------|----------|
| D1 | LLM + 规则 | LLM 标记 progress=none，需规则二次确认 |
| D2 | 规则 | 连续 4 步中 ≥3 次调用相同工具 |
| D3 | 规则 | 输出完全相同或 SequenceMatcher 相似度 >0.85 |
| D4 | 规则 | 意图关键词重复 ≥3 次 |
| D5 | 混合 | 步数 ≥15 无进度 |
| D6 | 规则 | 最近 5 步工具错误率 ≥60% |

僵局计数累计达 `max_stuck_steps`（默认 5）触发 3 级策略切换提示；连续无进展（`progress_level=none` 且输出无显著变化）达 5 次强制终止。LLM 调用连续 3 次失败或成本达上限均触发熔断，自动存档退出。

### 三层记忆系统

采用三层记忆结构解决 LLM 上下文窗口有限与长任务历史增长的矛盾：

- **详细历史（history）**：`List[Dict]`，最近详细步骤（think/tool_args/output/analysis），通过规范化 key 去重写入
- **日志叙事（journal_entries）**：`List[str]`，每步由 flash 模型生成 150-350 字叙事摘要，原样不压缩
- **整合叙事（consolidated_narrative）**：`str`，早期日志经 LLM 整合后的连贯技术叙事，原则"宁可长，不可丢"

`get_summary` 将三层记忆组装为 Prompt 上下文（整合叙事 + 最近 5 条日志 + 外部事实 + 最近 6 步详情），稳定在 4000-5000 字。

### 关键事实防丢机制

LLM 整合叙事可能遗漏凭据/flag 等关键信息。系统在整合后执行后置校验 `_ensure_protected_facts`：用 11 个正则模式扫描源文本，提取 flag、密码、Bearer Token、JWT、数据库连接串、AWS Key、私钥头、shadow 行、SHA256、MD5 等关键事实，缺失则强制以"关键事实（防丢）"块追加到叙事末尾。此机制作为 LLM 整合的硬兜底。

### 叙事长度控制

- 成功路径：`_NARRATIVE_MAX_CHARS=10000` 软上限，超长触发 `_compress_narrative` 二次 LLM 压缩（目标 6000 字，保留凭据/payload/IP/端口/失败原因）
- 失败降级路径：`_FALLBACK_NARRATIVE_MAX_CHARS=6000` 硬上限，仅保留日志标题行骨架 + 关键事实

避免叙事无界增长导致 Prompt 超上下文。

### 失败尝试追踪

`failed_attempts: Dict[str, int]` 记录失败工具调用次数。`add_step` 检测 `progress_level in ("none","minor")` 且输出含 error/failed/失败/exception 等关键字时登记失败；`_execute_single_tool` 异常路径主动调用 `add_failed_attempt`。key 经 `_normalize_tool_args_key` 规范化（list 元素排序 + dict sort_keys），消除参数顺序差异导致的去重失败。`get_summary` 在详情中显示"历史失败次数"，避免 LLM 重复踩坑。

### 三级缓存

| 缓存层 | 机制 | 说明 |
|--------|------|------|
| L1 精确 | 归一化 MD5 | 步骤编号/时间戳归一化后精确匹配 |
| L2 语义 | 语义指纹 + cosine | 双阈值：≥0.92 直接命中 / ≥0.78 需关键词校验（重叠度 ≥0.3）；`threshold>=1.0` 时跳过 L2（JSON 模式防误命中） |
| 工具结果 | 参数 MD5 + TTL | MCP 工具跳过缓存；工具执行错误不缓存（`is_error` 标记） |
| RAG 查询 | MD5 + 300s TTL | 同方向免重复检索 |
| 会话隔离 | reset_session_cache | 新任务清空，防跨会话污染 |

补充规则：纯 tool_calls 响应（空 content）序列化为 JSON 后再缓存；TokenTracker 在每任务步 0 重置，防跨任务成本累积。

### RAG 知识库

基于 ChromaDB 的混合检索：

- **向量检索**（权重 70%）+ **BM25 关键词检索**（权重 30%）
- LLM 重排序（0-10 分评分）
- 内置种子数据：6 大分类（web / crypto / pwn / reverse / stego / forensics）
- 自动学习：质量门控（步数 ≥2 + 工具 ≥1 + flag 格式校验）→ LLM 生成结构化摘要 → 按题型分类存入

### 技能库

45 个结构化安全技能（`skills/` 目录），每个包含 YAML frontmatter + Markdown 方法论：

- **注入类**：SQLi / XSS / SSTI / XXE / CMDi / XSLT / CRLF / EL / CSV
- **认证授权**：Auth Bypass / IDOR / CSRF / OAuth-OIDC / JWT / API Auth
- **服务端**：SSRF / LFI / 反序列化 / HTTP 走私 / 竞态条件 / 原型链污染
- **客户端**：点击劫持 / WebSocket / Web Cache / CORS / Open Redirect
- **方法论**：Recon / Hack / API 安全 / 业务逻辑 / 类型混淆 / JNDI / SAML / GraphQL

技能通过 `skill_loader.py` 动态注入 Prompt 上下文，按题型自动匹配。

### 环境自适应

三层探测回退机制：

```
完整探测 (45s) → 30+ 工具 + 15 Python 模块 + 网络 + OS
    → 失败: 最小探测 (10s) → uname + python3 + OS release
    → 失败: 降级运行
```

### 攻击面管理与渗透增强

**结构化管理**：`AttackSurface` 统一管理 Target / Service / Finding / Credential，支持序列化往返与 **schema 版本契约**（`to_dict` 写入 `schema_version`，`from_dict` 校验版本 + 未知字段容错 + `_migrate_schema` 迁移钩子），保障 checkpoint 跨版本兼容。

**漏洞优先级注入**：`get_priority_findings(top_n=3)` 按 `severity_weight × confidence_weight` 评分降序选取未确认的 Top-3 漏洞注入 Prompt，引导 LLM 优先验证高危漏洞。

| severity | 权重 | confidence | 权重 |
|----------|------|------------|------|
| critical | 4.0 | confirmed | 0.3 |
| high | 3.0 | likely | 1.0 |
| medium | 2.0 | possible | 0.7 |
| low | 1.0 | | |
| info | 0.5 | | |

> confirmed 权重低因其已验证无需再注入。

**凭据复用建议**：`get_credential_reuse_suggestions()` 仅对上次建议之后的新增凭据生成复用建议（避免重复注入），按凭据类型匹配已知服务端口（SSH 凭据→22 / 数据库凭据→3306,5432 / Web 凭据→HTTP），生成具体复用动作。

**其他渗透增强**：

- **漏洞验证闭环**：likely → 自动验证 → confirmed/放弃（最多 2 次）
- **凭据自动跟踪**：8 种正则模式检测密码/Token/Secret/私钥/JWT/数据库/哈希/凭据，去重后注入 Prompt 支持横向移动
- **报告生成**：per-finding PoC + 代码计算 CVSS + LLM 生成执行摘要/攻击链
- **IDOR 三要素校验**：traversable_id + cross_user_chain + no_ownership_check

### 成本控制

- `max_solve_cost_usd` 配置项，达到上限自动熔断
- `TokenTracker` 内置 20+ 模型定价表，实时追踪用量和成本，每任务步 0 重置
- 语义缓存减少重复 LLM 调用

---

## Web API

### REST 端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/health` | GET | 健康检查（含 Redis 状态） |
| `/api/task/submit` | POST | 提交任务 `{problem, mode, auto_mode}` → 返回 `task_id` |
| `/api/task/` | GET | 列出所有任务 |
| `/api/task/{task_id}/messages` | GET | 获取消息历史 |
| `/api/task/{task_id}/status` | GET | 获取任务运行状态 |
| `/api/status/env` | GET | Kali 环境探测（缓存） |
| `/api/status/env/refresh` | POST | 刷新环境探测 |
| `/api/status/llm` | POST | LLM 连接测试（60s 缓存） |
| `/api/status/mcp` | GET | MCP 服务状态 |
| `/api/kb/stats` | GET | 知识库统计 |
| `/api/kb/list` | GET | 知识库列表 |
| `/api/kb/search` | POST | 知识库搜索 `{query, n_results}` |
| `/api/kb/add` | POST | 添加知识条目 `{content, tags}` |
| `/api/kb/delete` | POST | 删除条目 `{ids}` |
| `/api/kb/reset` | POST | 清空重建知识库 |

### WebSocket

端点：`/ws/task/{task_id}`

实时消息推送 + Human-in-the-Loop 决策回传。所有 `solve_step` 与 `approval` 消息在 Redis 发布后同步落盘，确保刷新页面或断线重连后历史可回放。

**消息类型**：

| msg_type | 说明 | 关键字段 |
|----------|------|----------|
| `system` | 系统消息 | type: info / warning / success / error |
| `solve_step` | 每步快照 | step_num, phase, think, tool_calls, output, analysis, flag_found |
| `approval` | HIL 确认请求 | checkpoint_id, prompt, options, timeout |
| `task_status` | 任务状态变更 | status: running / paused / completed / failed |

**HIL 审批**：手动模式下，每步工具执行前弹出 `ApprovalDialog`，用户可选择批准 / 修改 / 终止 / 反馈方向，决策经 WebSocket 回传 worker 线程继续执行。

**cURL 测试**：

```bash
# 提交任务
curl -X POST http://localhost:8002/api/task/submit \
  -H "Content-Type: application/json" \
  -d '{"problem": "你的CTF题目", "mode": "ctf", "auto_mode": true}'

# 查看消息
curl http://localhost:8002/api/task/{task_id}/messages

# WebSocket 连接
wscat -c ws://localhost:8002/ws/task/{task_id}
```

---

## 配置参考

### config.json 完整结构

```json
{
    "llm": {
        "solve_agent":   { "model": "...", "api_key": "...", "api_base": "..." },
        "analyzer":      { "model": "...", "api_key": "...", "api_base": "..." },
        "pre_processor": { "model": "...", "api_key": "...", "api_base": "..." },
        "embedding":     { "model": "...", "api_key": "...", "api_base": "..." }
    },
    "tool_config": {
        "ssh_shell": { "host": "...", "port": 22, "username": "...", "password": "..." }
    },
    "mcp_server": { ... },
    "max_solve_steps": 100,
    "max_solve_cost_usd": 5.0,
    "max_stuck_steps": 5,
    "checkpoint_interval": 5,
    "tool_cache_ttl": 300,
    "output_summary_threshold": 2048,
    "output_summary_max_chars": 800,
    "knowledge_entry_max_chars": 2000
}
```

### 运行参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `max_solve_steps` | 100 | 最大执行步数 |
| `max_solve_cost_usd` | 5.0 | 成本熔断上限（美元，0 = 不限制） |
| `max_stuck_steps` | 5 | 连续僵局次数上限 |
| `checkpoint_interval` | 5 | 自动存档间隔（步） |
| `tool_cache_ttl` | 300 | 工具结果缓存 TTL（秒） |
| `output_summary_threshold` | 2048 | 触发 LLM 输出摘要的长度阈值 |
| `output_summary_max_chars` | 800 | 摘要最大字符数 |
| `knowledge_entry_max_chars` | 2000 | 知识条目结构化摘要最大字数 |

### CLI 参数

| 参数 | 说明 |
|------|------|
| `--mode ctf/pentest` | 运行模式（不指定则交互选择） |
| `--auto` | 强制自动模式 |
| `--manual` | 强制手动模式（每步审批） |
| `--resume` | 断点续跑 |
| `--export-writeup` | 解题后导出 Writeup |
| `--interactive` | 交互式选择模式和审批方式 |

---

## 项目结构

```
LLM-CTF-Solver/
├── main.py                          # CLI 入口
├── tui_main.py                      # TUI 入口
├── cli.py                           # 知识库管理 CLI
├── log_viewer.py                    # 日志回溯工具
├── benchmark_run.py                 # 基准测试入口
├── test_llm.py                      # 连接测试脚本
├── config.py                        # 配置管理（单例 + 环境变量覆盖）
├── config.example.json              # 配置模板（可安全上传）
├── config.json                      # 主配置文件（含 API Key，已 gitignore）
├── requirements.txt                 # Python 依赖
├── Dockerfile                       # Docker 镜像
├── docker-compose.yml               # Redis + Agent 编排
│
├── agent/                           # 核心 Agent 引擎
│   ├── workflow.py                  # 编排层：CTF/渗透双流程 + 自学习 + 报告
│   ├── solve_agent.py               # 推理引擎：ReAct 循环 + 僵局检测 + 阶段感知 + 断点续跑
│   ├── memory.py                    # 三层记忆 + 关键事实防丢 + 叙事长度控制 + 失败追踪
│   ├── analyzer.py                  # LLM 步骤分析
│   ├── attack_surface.py            # 攻击面管理 + schema 版本 + 漏洞优先级 + 凭据复用
│   ├── checkpoint.py                # 断点存档（MD5 键 + 保留最近 3 个）
│   └── user_interface.py            # UI 抽象基类 + CLI 实现
│
├── ctf_tool/                        # 20+ 内置安全工具（按 modes 过滤）
│   ├── base_tool.py                 # 工具抽象基类（modes 类属性）
│   ├── ssh_shell.py                 # Shell 命令执行（共享）
│   ├── python.py                    # Python 代码执行（AST 沙箱，共享）
│   ├── network.py                   # 网络工具集（共享）
│   ├── web_tools.py                 # Web 渗透测试（渗透）
│   ├── crypto_tools.py              # 密码学分析（CTF）
│   ├── crypto_attacks.py            # 密码学攻击（CTF）
│   ├── codec.py                     # 编码/解码（CTF）
│   ├── jwt_tools.py                 # JWT 分析（共享）
│   ├── file_analyzer.py             # 文件分析（共享）
│   ├── reverse_tools.py             # 逆向工程（CTF）
│   ├── binary_analysis.py           # 二进制/PWN（CTF）
│   ├── stego_tools.py               # 隐写分析（CTF）
│   ├── forensics_tools.py           # 取证分析（CTF）
│   ├── exploit_templates.py         # 漏洞利用模板（渗透）
│   ├── android_tools.py             # Android 逆向（CTF）
│   ├── powershell_tools.py          # Windows 渗透（渗透）
│   ├── challenge_classifier.py      # 题型分类器（CTF）
│   ├── flag_detector.py             # 5 层 Flag 检测（共享）
│   ├── mcp_adapter.py               # MCP 协议适配器（共享）
│   └── ssh_client.py                # 共享 SSH 客户端
│
├── utils/                           # 工具函数
│   ├── llm_request.py               # LLM 请求封装（重试 + 缓存 + Token 追踪）
│   ├── tools.py                     # 工具加载/推荐/解析/执行（模式过滤）
│   ├── security.py                  # 命令安全黑名单（30+ 规则 + 编码绕过检测）
│   ├── semantic_cache.py            # 语义缓存（L1 MD5 + L2 双阈值 + threshold 参数）
│   ├── token_tracker.py             # Token 用量追踪（20+ 模型定价，每任务重置）
│   ├── tool_cache.py                # 工具结果缓存（TTL + 防重放 + 错误跳过）
│   ├── env_probe.py                 # 环境探测（三层回退）
│   ├── dynamic_resolver.py          # 远程工具动态发现（80+ 映射）
│   ├── output_parser.py             # 规则式输出解析
│   ├── text.py                      # JSON 修复 + 文本优化
│   ├── skill_loader.py              # 技能加载器
│   └── skill_seeder.py              # 技能知识库种子
│
├── rag/                             # RAG 知识库
│   ├── rag_service.py               # ChromaDB 混合检索（向量 70% + BM25 30%）
│   ├── knowledge_base.py            # 知识库管理
│   ├── memory_base.py               # 记忆系统
│   ├── seed_knowledge.py            # 种子数据加载
│   └── seed_data/                   # 种子知识（6 大分类 JSON）
│
├── prompts/                         # Prompt 模板
│   └── v1/
│       ├── prompt.yaml              # CTF 解题 Prompt
│       └── pentest_prompt.yaml      # 渗透测试 Prompt
│
├── skills/                          # 45 个安全技能
│   ├── sqli-sql-injection/SKILL.md
│   ├── xss-cross-site-scripting/SKILL.md
│   └── ...                          # 每个技能含 YAML frontmatter + Markdown
│
├── backend/                         # Web UI 后端 (FastAPI)
│   ├── server.py                    # 应用入口（CORS + 生命周期）
│   └── app/
│       ├── routers/
│       │   ├── task_router.py       # 任务提交/状态/消息（消息落盘）
│       │   ├── ws_router.py         # WebSocket 实时推送 + HIL
│       │   ├── status_router.py     # 环境/LLM/MCP 状态
│       │   └── kb_router.py         # 知识库 CRUD
│       ├── schemas/                 # 消息/请求/枚举模型（SolveStep/Approval/TaskStatus）
│       ├── services/
│       │   ├── redis_manager.py     # Redis Pub/Sub + 文件日志（save_message_to_file_sync）
│       │   ├── ws_manager.py        # WebSocket 连接管理
│       │   └── state_store.py       # Redis HIL 状态持久化
│       ├── adapters/
│       │   └── web_ui_interface.py  # WebUI 适配器（SolveAgent ↔ Redis）
│       └── utils/task_id.py         # Task ID 生成（YYYYMMDD-HHMMSS-uuid8）
│
├── frontend/                        # Web UI 前端 (Vue 3 + Vite)
│   └── src/
│       ├── pages/                   # 页面组件
│       │   ├── index.vue            # 首页（任务列表）
│       │   ├── session/new.vue      # 新建任务
│       │   ├── session/[id].vue     # 执行面板（含 HIL 审批集成）
│       │   ├── kb/index.vue         # 知识库管理
│       │   └── status/index.vue     # 连接测试
│       ├── components/              # 业务组件 + shadcn-vue UI 组件
│       │   ├── ApprovalDialog.vue   # HIL 审批弹窗
│       │   ├── SolveTimeline.vue    # 步骤时间线（可交互）
│       │   ├── StepCard.vue         # 步骤详情卡片
│       │   ├── FlagBanner.vue       # Flag 横幅
│       │   ├── PhaseIndicator.vue   # 阶段指示器
│       │   └── TokenUsageBar.vue    # Token 用量条
│       ├── stores/task.ts           # Pinia Store
│       ├── utils/                   # WebSocket / Axios / 类型定义
│       └── router/index.ts          # Vue Router 配置
│
├── tui/                             # Textual TUI
│   ├── app.py                       # TUI 应用入口
│   ├── ui_interface.py              # Textual UI 适配器
│   ├── screens/                     # 会话列表/解题/知识库/新建会话
│   ├── widgets/                     # 步骤列表/详情/输出/阶段/攻击面
│   ├── modals/                      # 确认/选择/输入/帮助/知识库添加
│   └── styles/theme.tcss            # 主题样式
│
├── benchmark/                       # 基准测试
│   ├── case.py                      # 测试用例定义（YAML 加载）
│   ├── runner.py                    # 测试运行器（支持并行）
│   └── cases/                       # 测试用例目录
│
├── tests/                           # 测试（96 passed, 1 skipped）
│   ├── test_attack_surface.py       # 攻击面 + schema 版本 + 优先级评分
│   ├── test_flag_detector.py        # Flag 检测
│   ├── test_integration.py          # 集成测试（mock LLM）
│   ├── test_output_parser.py        # 输出解析器
│   ├── test_security.py             # 安全黑名单
│   └── test_tool_cache.py           # 工具缓存
│
├── checkpoints/                     # 断点存档（运行时生成）
├── logs/                            # 日志（运行时生成，30 天自动清理）
├── reports/                         # 渗透测试报告（运行时生成）
├── writeups/                        # CTF Writeup（运行时生成）
└── attachments/                     # 题目附件目录
```

---

## Docker 部署

```bash
# 构建镜像
docker build -t ctf-agent .

# CTF 解题
docker run -it --rm \
  -v ./config.json:/app/config.json:ro \
  -v ./question.txt:/app/question.txt:ro \
  -v ./attachments:/app/attachments:ro \
  ctf-agent --mode ctf

# 使用 docker compose
docker compose up -d redis
docker compose run --rm ctf-agent --mode ctf

# Web UI 后端
docker compose run --rm -p 8002:8002 ctf-agent python -m backend.server
```

**环境变量**（docker-compose.yml 中配置）：

| 变量 | 说明 |
|------|------|
| `LLM_API_KEY` | 覆盖所有 LLM 入口的 API Key |
| `LLM_API_KEY_SOLVE_AGENT` | 仅覆盖 solve_agent 的 Key |
| `LLM_API_KEY_ANALYZER` | 仅覆盖 analyzer 的 Key |
| `AGENT_PYTHON_SANDBOX` | Python 沙箱模式：`subprocess`（默认）/ `docker` |

---

## 安全机制

| 机制 | 说明 |
|------|------|
| 命令黑名单 | 30+ 规则，覆盖 rm -rf / fork bomb / shutdown 等高危命令 |
| 编码绕过检测 | 自动解码 base64 / hex / $'\x' 后重新检查 |
| Python 沙箱 | AST 层拦截 exec / eval / compile / getattr + 写文件操作 |
| LLM 熔断 | 连续 3 次 LLM 调用失败 → 自动存档退出 |
| 成本熔断 | `max_solve_cost_usd` 达到上限 → 自动终止；TokenTracker 每任务重置 |
| MCP 线程安全 | 锁串行化 event loop 访问，防止并发冲突 |
| Schema 版本契约 | AttackSurface checkpoint 含 `schema_version`，未知版本拒绝恢复，未知字段容错 |
| 关键事实防丢 | 11 正则模式后置校验整合叙事，确保凭据/flag 不丢失 |
| 配置安全 | 复制 `config.example.json` → `config.json`，含敏感信息的 `config.json` 已加入 `.gitignore` |

> **已知局限**：Python AST 沙箱可被属性链绕过，命令黑名单无法枚举所有变体，Web 后端无认证。本系统适合作为学习研究原型，生产部署需优先修复认证、沙箱、并发隔离三项。

---

## 测试

```bash
# 运行全部测试
pytest

# 运行指定测试
pytest tests/test_integration.py -v     # 集成测试（mock LLM）
pytest tests/test_security.py -v        # 安全黑名单测试
pytest tests/test_flag_detector.py -v   # Flag 检测测试
pytest tests/test_attack_surface.py -v  # 攻击面 + schema 版本测试

# Web UI 端到端测试（需 Redis + Server 运行）
cd backend && python test_e2e.py
```

当前测试结果：**96 passed, 1 skipped**（skip 为依赖网络的 LLM 连接测试）。

---

## 故障排查

| 症状 | 可能原因 | 排查方式 |
|------|---------|---------|
| 环境探测失败 | SSH 未连接 / VM 未启动 | `python test_llm.py` |
| Embedding 400 错误 | Prompt 超过嵌入模型上限 | 检查语义缓存指纹是否生效 |
| MCP 工具超时 | SSE session 空闲断开 | 查看日志中是否有重连标记 |
| MCP 工具 "already running" | 多线程并发访问 event loop | 确认 `_exec_lock` 已初始化 |
| 续跑后"未找到工具" | MCP 子进程未重激活 | 已修复：续跑自动调 `_auto_activate_mcp()` |
| 续跑后无经验参考 | step-0 上下文未加载 | 已修复：续跑自动调 `_load_step_zero_context()` |
| WebSocket 连接后无消息 | Redis 未启动 / 端口占用 | `curl localhost:8002/api/health` |
| 刷新页面后历史丢失 | 消息未落盘 | 已修复：step/approval 消息 `save_message_to_file_sync` |
| Ctrl+C 后无 writeup | CTF 分支条件错误 | 已修复：`export_writeup=True` 即生成（标注中断） |
| Flag 检测不工作 | 正则未覆盖该格式 | 查看 flag_detector.py 的 `_FLAG_PATTERNS` |
| 记忆整合丢失凭据 | LLM 整合遗漏 | 已修复：`_ensure_protected_facts` 后置校验 |
| 叙事无限增长 | LLM 压缩失败 | 已修复：`_FALLBACK_NARRATIVE_MAX_CHARS=6000` 硬上限 |

---

## License

[Apache License 2.0](LICENSE)
