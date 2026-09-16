# Research Agent Lab 项目交接说明

更新时间：2026-06-17

## 1. 文档目的

本文件用于把 `research_agent_lab` 交付给其他开发者继续开发。

它记录项目目标、当前进度、已验证命令、关键约束、API 使用方式、后续任务。

后续每轮有较大开发进展时，应同步更新本文件。

本文件优先描述事实，不写泛泛的设想。

如果本文件与代码不一致，以代码和最新测试结果为准，但需要及时修正文档。

## 2. 项目定位

项目名：Research Agent Lab。

路径：`D:\Codes\VS\research_agent_lab`。

目标：构建一个本地优先、可切换课题的科研多智能体开发平台。

当前服务的主要课题：基于 LED/VIRAT 的意图或语言条件行人轨迹预测。

当前真实课题代码副本：`D:\Codes\VS\Intent-LED-mul-agent`。

本项目不是单次脚本，而是科研 workflow 框架。

核心路线来自 `code_plan.md`。

推荐路线是 Agent Laboratory 二次开发，加自建 Topic Pack、方法卡、证据链、记忆和实验计划。

当前阶段处于 V1 本地可用原型。

当前重点不是完全自动科研，而是可追溯、可控、可人工审查的科研辅助。

Codex 在本项目中只作为开发执行者。

内部 multi-agent 任务不得路由到当前 Codex 会话。

内部智能任务应使用本地规则或配置好的 DeepSeek API。

## 3. 当前目录结构

`app/`：CLI 入口。

`agents/`：各科研 agent。

`core/`：workflow、state、artifact store、agent base。

`memory/`：SQLite 记忆实现。

`schemas/`：结构化 artifact schema。

`tools/`：工具层，如 PDF parser、LLM client、model router、codebase analyzer。

`topics/`：Topic Pack 配置。

`workflows/`：workflow factory 和定义。

`tests/`：单元测试和 smoke test。

`docs/`：运行、模型、交接和安全说明。

`data/`：运行产物和备份，默认不应提交。

`external/AgentLaboratory/`：clone 的 Agent Laboratory。

## 4. 重要外部路径

Agent Laboratory 路径：`D:\Codes\VS\research_agent_lab\external\AgentLaboratory`。

可修改课题副本：`D:\Codes\VS\Intent-LED-mul-agent`。

本地论文库 EPC：`C:\Users\duyul\Desktop\work\Essay\轨迹预测\EPC`。

本地论文库 SPK：`C:\Users\duyul\Desktop\work\Essay\轨迹预测\SPK`。

本地论文目录只读使用，不应自动改动或删除。

`Intent-LED-mul-agent` 是用户复制出的副本，可以高权限探索。

即使可以改，也应先备份关键文件。

## 5. Python 环境

统一使用 `video_llava` 环境。

解释器路径：`D:\Develop_Tools\Anaconda3\envs\video_llava\python.exe`。

不要默认使用系统 `python`。

已在该环境安装 `pypdf`，用于本地 PDF 解析。

Windows shell 偶发不稳定。

PowerShell 有时会返回 `-1073741502`。

遇到 shell 异常时，优先用显式解释器执行 Python 命令。

`cmd /c dir`、`cmd /c type` 通常可用。

## 6. API 和密钥

DeepSeek API key 放在项目根目录 `.env`。

`.env` 应被 `.gitignore` 忽略。

`.env.example` 只能放占位符。

不要把真实 key 写入文档、测试或日志。

`check-config` 输出只允许显示 mask。

当前 key mask 形如 `sk-7ce...16ff`。

DeepSeek endpoint 默认：`https://api.deepseek.com/chat/completions`。

可用环境变量覆盖：`DEEPSEEK_BASE_URL`。

当前模型分层：简单任务用 `deepseek-v4-flash`。

当前模型分层：困难任务用 `deepseek-v4-pro`。

默认 workflow 不调用付费 API。

只有显式加 `--enable-llm` 才允许支持的 agent 调用 API。

默认 API 预算：`--llm-call-budget 3`。

默认 token 预算：`--llm-token-budget 20000`。

预算为 0 时应生成跳过记录，不应真实调用 API。

## 7. 当前 Topic Pack

主 Topic Pack：`topics/intent_led_virat.json`。

Topic 名：`intent_conditioned_led_virat`。

主要领域：`pedestrian_trajectory_prediction`。

当前目标：在复制的 LED/VIRAT 代码上探索 intention/language conditioning。

基线：LED VIRAT baseline。

数据：来自 `../MID-main/processed_data_virat` 的 VIRAT processed pkl。

指标：ADE、FDE、miss_rate、multimodal_diversity。

代码仓库路径：`D:/Codes/VS/Intent-LED-mul-agent`。

允许自动编辑：`models/*`。

允许自动编辑：`trainer/*`。

允许自动编辑：`data/dataloader_virat.py`。

允许自动编辑：`cfg/virat/*`。

允许自动编辑：`utils/*`。

允许自动编辑：`main_led_nba.py`。

允许自动编辑：`visualize_virat_prediction.py`。

允许自动编辑：`work.md`。

受保护路径包括 results、原始数据、MID-main、缓存等。

## 8. 已实现 agent

`ResearchManagerAgent`：生成研究 brief。

`LocalPaperLibraryAgent`：扫描本地论文库。

`LiteratureSearchAgent`：生成或检索论文 seed。

`PaperTriageAgent`：基于关键词选择论文。

`LocalPaperParserAgent`：解析本地 PDF。

`PaperReaderAgent`：生成 evidence 记录。

`EvidenceCheckerAgent`：检查 evidence 可用性。

`MethodCardExtractorAgent`：生成结构化方法卡。

`SynthesisAgent`：生成综合报告。

`CodebaseAnalyzerAgent`：分析课题代码库。

`OpportunityAgent`：生成研究机会。

`ExperimentPlannerAgent`：生成实验计划。

`DeveloperAgent`：生成受控开发任务。

`ReviewerAgent`：复查证据、计划和风险。

## 9. 已实现工具

`tools/env_loader.py`：加载 `.env` 并 mask secret。

`tools/model_router.py`：按 topic metadata 路由模型。

`tools/llm_client.py`：OpenAI-compatible chat client。

`tools/llm_budget.py`：共享 LLM 调用预算和 token 计数。

`tools/local_paper_library.py`：扫描本地论文。

`tools/local_pdf_parser.py`：用 pypdf/PyPDF2 解析 PDF。

`tools/paper_chunk_selector.py`：选择与方法、实验、指标相关的 chunks。

`tools/codebase_analyzer.py`：分析目标代码库结构。

`tools/agent_laboratory_adapter.py`：生成 Agent Laboratory config。

`tools/arxiv_tool.py`：arXiv 工具接口。

`tools/git_tool.py`：Git 工具接口。

`tools/test_runner.py`：测试工具接口。

## 10. 结构化产物

`Paper`：论文元数据。

`ParsedPaper`：解析后的论文文本和 chunk。

`PaperChunk`：论文文本块。

`Evidence`：可追溯证据。

`MethodCard`：方法卡。

`ResearchOpportunity`：研究机会。

`ExperimentPlan`：实验计划。

`CodeTask`：开发任务。

`ReviewResult`：复查结果。

运行产物存放在 `data/runs/<run_id>/`。

结构化 JSON artifact 存放在 `artifacts/<kind>/`。

综合报告存放在 `artifacts/reports/`。

LLM 调用记录存放在 `artifacts/llm_calls/`。

LLM 调用记录不得保存 API key。

LLM 调用记录不保存完整 prompt，只保存摘要、长度、usage、状态和预览。

## 11. 当前 LLM 接入状态

`method_card_extractor` 已接入 `deepseek-v4-pro`。

`synthesis` 本轮已接入 `deepseek-v4-flash` 路径。

`experiment_planner` 本轮已接入 `deepseek-v4-pro` 路径。

`reviewer_agent` 仍主要是规则检查。

`paper_triage` 路由已配置 flash，但尚未实现真实 LLM 调用。

`result_parser` 路由已配置 flash，但尚未实现独立 agent。

所有 LLM 路径都必须受 `--enable-llm` 控制。

所有 LLM 路径都必须受预算控制。

所有 LLM 失败都应回退到规则产物。

任何 LLM 输出进入 workflow 前都必须转换成 schema。

不得让自由文本直接驱动代码修改。

## 12. 已验证运行记录

本地论文扫描已验证：共 47 篇。

PDF 解析已验证：可解析本地 PDF 并生成 chunks。

DeepSeek key 可见性已验证：`check-config` 可 mask 输出。

真实 `deepseek-v4-pro` method-card 小跑已成功。

成功 run：`data/runs/run_75105eb7669d`。

该 run 结果：`method_card_llm_success_count=1`。

该 run 结果：`review_status=pass`。

该 run 一篇论文约使用 4715 total tokens。

预算跳过 run 已验证。

预算跳过 run：`data/runs/run_9eb80578170f`。

预算跳过结果：`skipped_call_budget`。

预算跳过结果：真实 API 调用数 0。

## 13. Intent-LED-mul-agent 已做内容

已在复制项目中实现 motion-intent condition 实验。

改动文件包括 `models/model_led_initializer.py`。

改动文件包括 `trainer/train_led_trajectory_augment_input.py`。

新增配置 `cfg/virat/led_virat_intent_debug.yml`。

新增配置 `cfg/virat/led_virat_intent.yml`。

更新了目标项目 `work.md`。

关键备份在 `data/backups/intent_led_motion_condition_base`。

motion-intent 特征为 `[dx, dy, vx, vy]`。

该特征注入 LEDInitializer 的 mean、variance、scale ego embeddings。

debug train smoke run 已通过。

debug eval smoke run 已通过。

debug checkpoint 曾生成在 `results/led_virat_intent_debug/motion_condition/models/model_0002.p`。

当前 `research_agent_lab` 后续开发不应默认继续改外部项目。

只有用户明确要求执行代码改动时，才修改 `Intent-LED-mul-agent`。

## 14. 常用命令

检查配置：

`D:\Develop_Tools\Anaconda3\envs\video_llava\python.exe -m app.main check-config --topic topics\intent_led_virat.json`

离线 run：

`D:\Develop_Tools\Anaconda3\envs\video_llava\python.exe -m app.main run --topic topics\intent_led_virat.json --data-dir data --max-papers 8`

一篇论文 LLM smoke run：

`D:\Develop_Tools\Anaconda3\envs\video_llava\python.exe -m app.main run --topic topics\intent_led_virat.json --data-dir data --max-papers 1 --enable-llm --llm-call-budget 1`

预算跳过验证：

`D:\Develop_Tools\Anaconda3\envs\video_llava\python.exe -m app.main run --topic topics\intent_led_virat.json --data-dir data --max-papers 1 --enable-llm --llm-call-budget 0`

运行全部测试：

`D:\Develop_Tools\Anaconda3\envs\video_llava\python.exe -m unittest discover -s tests`

生成 Agent Laboratory config：

`D:\Develop_Tools\Anaconda3\envs\video_llava\python.exe -m app.main agentlab-config --topic topics/intent_led_virat.json --output agentlab_configs/intent_led_virat_agentlab.yaml`

## 15. 当前测试状态

本轮新增了 chunk selector、synthesis LLM、experiment planner LLM 相关代码。

本轮新增测试包括 `test_paper_chunk_selector.py`。

本轮新增测试包括 `test_synthesis_and_planner_llm.py`。

编译检查已通过。

局部 LLM 相关测试已通过。

完整测试已通过。

验证命令：`D:\Develop_Tools\Anaconda3\envs\video_llava\python.exe -m unittest discover -s tests`。

当前结果：18 个测试 OK。

测试不访问真实 DeepSeek API。

后续真实 API run 仍需单独小批量验证。

## 16. 当前开发注意点

项目当前不是 Git 仓库。

不要依赖 `git status` 管理变更。

重要文件修改前先备份到 `data/backups/<task_name>/`。

不要删除用户未要求删除的运行结果。

清理测试输出时只清理明确生成的 `data/runs`、`memory.sqlite3`、`__pycache__` 等。

不要删除 `.env`。

不要删除 `external/AgentLaboratory`。

不要删除 `data/backups`。

不要删除本地论文库。

不要在文档或日志中写真实 API key。

真实 API run 前优先用 `--max-papers 1`。

真实 API run 前优先设置 `--llm-call-budget`。

真实 API run 后检查 `artifacts/llm_calls/`。

DeepSeek pro 可能把大量 token 用于 reasoning。

method-card 一篇论文曾消耗约 4.7k tokens。

扩大 batch 前必须评估成本。

## 17. 代码设计原则

默认离线可运行。

LLM 只是增强路径，不是基础路径。

LLM 输出必须 schema 化。

agent 之间传递结构化 artifact，不传自由聊天文本。

证据不足的结论必须标记为待验证。

实验计划必须 smoke-first。

开发 agent 默认只产出任务，不自动大范围改代码。

修改外部项目前先明确改动范围。

每个 agent 的失败都应可回退。

每次 run 都应可从 `state.json` 和 artifact 复盘。

## 18. 后续优先级

第一优先级：完成本轮 synthesis/planner LLM 接入测试。

第二优先级：增强 reviewer 对 LLM 产物的 schema 和证据检查。

第三优先级：实现 paper triage 的 flash LLM 路径。

第四优先级：实现更可靠的 section-aware PDF parsing。

第五优先级：加入轻量 hybrid retrieval。

第六优先级：加入文献 memory 和 method card 检索。

第七优先级：把 experiment plan 转成可审查 patch plan。

第八优先级：在用户确认后继续外部项目实验开发。

## 19. 暂不建议做的事

暂不建议直接重写成 LangGraph。

暂不建议直接引入大型向量数据库作为强依赖。

暂不建议一次性接入 Agent Laboratory 全流程运行。

暂不建议让 multi-agent 自动修改真实研究代码。

暂不建议无预算地跑多篇论文 LLM 总结。

暂不建议把论文库复制到项目目录。

暂不建议把 `.env` 或 key 写入任何交付文件。

## 20. 交接检查清单

确认 `.env` 存在且未提交。

确认 `.env.example` 没有真实 key。

确认 `check-config` 可以看到本地论文和模型路由。

确认离线 workflow 可运行。

确认预算为 0 时不调用 API。

确认真实 API smoke run 只跑一篇论文。

确认 `data/backups` 保留关键备份。

确认文档命令使用 `video_llava` 解释器。

确认新增测试不访问网络。

确认 final 文档说明测试结果。
