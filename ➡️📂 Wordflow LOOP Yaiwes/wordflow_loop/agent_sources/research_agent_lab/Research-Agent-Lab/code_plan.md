**建议采用“Agent Laboratory 二次开发 + 模块化重构 + 吸收 AI Scientist-v2 / PaperQA2 / LangGraph / LangMem / GraphRAG 等项目优点”的路线。**

不要一开始完全重写，也不要直接把 AI Scientist-v2 当主底座。你的目标是自用、学习多智能体、辅助毕设开发，所以最合理的是：

```text
第一阶段：Fork Agent Laboratory，先获得可用科研 workflow。
第二阶段：把文献检索、论文阅读、方法卡、记忆、实验规划模块重构成可复用组件。
第三阶段：吸收 AI Scientist-v2 的实验树搜索与自动 debug 思路。
第四阶段：逐步迁移到 LangGraph 风格的状态机架构。
第五阶段：形成可针对不同课题切换的科研多智能体平台。
```

Agent Laboratory 本身已经包含 Literature Review、Experimentation、Report Writing 三个阶段，并集成 arXiv、Hugging Face、Python、LaTeX 等工具，适合作为启动底座。([agentlaboratory.github.io][1]) AI Scientist-v2 更适合参考其 idea generation、agentic tree search、实验执行、结果分析和论文生成流程，而不是直接作为主框架。([GitHub][2])

---

# 1. 总体设计目标

你要做的不是“单课题脚本”，而是一个可切换课题的科研多智能体系统。

核心目标：

```text
输入：
任意课题方向 + 课题约束 + 已有代码 / 数据 / 文献

输出：
1. 相关文献检索结果
2. 论文结构化方法卡
3. 跨论文技术路线总结
4. 可迁移到当前课题的研究点
5. 实验方案与消融设计
6. 代码开发计划
7. 自动或半自动代码修改
8. 实验结果验收报告
```

可复用性的关键不在 agent 名字，而在这四层：

```text
1. Topic Pack：课题配置包
2. Standard Schemas：标准中间产物
3. Tool Registry：工具插件层
4. Workflow Graph：可替换工作流
```

换课题时，不改核心系统，只换 `Topic Pack` 和少量 schema。

---

# 2. 推荐总体架构

```text
Research Multi-Agent System
│
├── 1. Orchestration Layer
│   ├── Workflow Graph
│   ├── Agent Router
│   ├── State Manager
│   ├── Human-in-the-loop
│   └── Run Logger
│
├── 2. Agent Layer
│   ├── Research Manager Agent
│   ├── Literature Search Agent
│   ├── Paper Triage Agent
│   ├── Deep Reading Agent
│   ├── Evidence Checker Agent
│   ├── Method Card Agent
│   ├── Synthesis Agent
│   ├── Research Opportunity Agent
│   ├── Experiment Planner Agent
│   ├── Developer Agent
│   ├── Test Agent
│   └── Reviewer Agent
│
├── 3. Knowledge Layer
│   ├── Literature RAG
│   ├── Project Memory
│   ├── Experiment Memory
│   ├── Codebase Memory
│   ├── Method Card Store
│   └── Citation / Evidence Store
│
├── 4. Tool Layer
│   ├── arXiv API
│   ├── Semantic Scholar API
│   ├── Zotero / Local PDF
│   ├── PDF Parser
│   ├── Vector DB
│   ├── Graph DB
│   ├── Code Executor
│   ├── Git Tool
│   ├── Test Runner
│   └── Report Generator
│
└── 5. Artifact Layer
    ├── papers/
    ├── parsed_papers/
    ├── method_cards/
    ├── synthesis_reports/
    ├── experiment_plans/
    ├── code_patches/
    ├── test_logs/
    └── final_reports/
```

主流程建议后期使用 LangGraph，因为它支持有状态 agent、持久执行、失败恢复和 human-in-the-loop，适合长期科研任务。([GitHub][3]) 但短期不需要立刻重写 Agent Laboratory，可以先在它外面加一层 adapter。

---

# 3. 核心路线：基于 Agent Laboratory，但不要被它锁死

## 3.1 第一阶段：Fork Agent Laboratory

先保留它已有的三阶段科研流程：

```text
Literature Review
→ Experimentation
→ Report Writing
```

这一步的目标不是“改得很优雅”，而是先让它能服务你的真实课题：

```text
课题：
基于扩散模型的多模态行人轨迹预测

输入：
Leapfrog / MID / VIART 数据 / 行人自然语言描述 / 视频特征 / 轨迹历史

输出：
相关论文 + 方法总结 + 可实验方案
```

Agent Laboratory 论文和项目都强调它允许人类在各阶段提供反馈，这对你自用很重要，因为科研 agent 不能完全自动放权。([arXiv][4])

---

## 3.2 第二阶段：抽象出你自己的核心接口

不要长期把所有逻辑写死在 Agent Laboratory 源码里。你应该抽象出统一接口：

```python
class ResearchWorkflow:
    def run(topic_pack): ...

class Agent:
    def run(state, tools, memory): ...

class Tool:
    def call(input): ...

class MemoryStore:
    def write(memory_item): ...
    def retrieve(query, scope): ...

class ArtifactStore:
    def save(artifact): ...
    def load(artifact_id): ...
```

你的目标是让 Agent Laboratory 变成一个可替换后端：

```text
Agent Laboratory Adapter
AI Scientist-v2 Adapter
LangGraph Workflow Adapter
Custom Workflow Adapter
```

这样后续你可以平滑迁移，不会被某个开源项目绑死。

---

# 4. Topic Pack：实现高复用的关键

这是整个系统最重要的设计。

你需要为每个课题创建一个 `Topic Pack`。它描述当前课题的目标、术语、检索策略、抽取 schema、实验指标、代码仓库结构。

## 4.1 Topic Pack 示例：你的毕设课题

```yaml
topic_name: language_conditioned_pedestrian_trajectory_prediction

domain:
  primary_area: pedestrian_trajectory_prediction
  secondary_areas:
    - diffusion_models
    - multimodal_fusion
    - pedestrian_intention_recognition
    - video_language_understanding

research_goal:
  short: 在 Leapfrog / MID 等扩散轨迹预测方法基础上，引入行人自然语言描述、视频特征和历史轨迹信息，提高行人轨迹预测效果。
  long: >
    构建一个多模态条件扩散轨迹预测模型，将行人自然语言描述、
    视频语义信息、历史轨迹和时序交互信息作为条件输入，预测未来轨迹。

current_status:
  baseline_methods:
    - Leapfrog
    - MID
  existing_models:
    - Qwen3.5-2B LoRA intention recognition
  known_results:
    - 输出格式遵循率 100%
    - 行人意图识别准确率约 70%
  priority:
    - 暂不优先提升意图识别准确率
    - 优先探索语言特征如何输入扩散轨迹预测模型

search_seeds:
  keywords:
    - diffusion trajectory prediction
    - pedestrian trajectory forecasting diffusion
    - language conditioned trajectory prediction
    - multimodal pedestrian trajectory prediction
    - pedestrian intention trajectory forecasting
    - feature fusion trajectory prediction
    - cross attention diffusion model trajectory
    - MID motion indeterminacy diffusion
    - Leapfrog pedestrian trajectory prediction

paper_schema:
  required_fields:
    - task
    - input_modalities
    - output
    - model_architecture
    - temporal_modeling
    - fusion_strategy
    - diffusion_strategy
    - datasets
    - metrics
    - limitations
    - reusable_ideas
    - implementation_difficulty

experiment_metrics:
  - ADE
  - FDE
  - miss_rate
  - collision_rate
  - multimodal_diversity

codebase:
  repo_path: /path/to/project
  protected_files:
    - data/raw/*
  allowed_auto_edit:
    - models/*
    - configs/*
    - train.py
    - datasets/*
```

换课题时，只换这个配置。

例如换成“VIN OCR 识别”，Topic Pack 就变成：

```yaml
topic_name: vin_ocr_mobile_pipeline
domain:
  primary_area: scene_text_recognition
  secondary_areas:
    - OCR
    - vehicle_identification_number
    - mobile_deployment
    - PaddleOCR
    - ONNX
    - steel_stamp_recognition
metrics:
  - exact_match_accuracy
  - character_accuracy
  - latency
  - model_size
  - steel_stamp_accuracy
```

这样同一套 agent 可以服务不同方向。

---

# 5. 标准中间产物设计

多智能体系统最容易失败的地方是：所有 agent 都输出自然语言，后续无法复用。

你应该强制每一步输出结构化 artifact。

---

## 5.1 Paper 对象

```json
{
  "paper_id": "string",
  "title": "string",
  "authors": ["string"],
  "year": 2025,
  "venue": "string",
  "url": "string",
  "pdf_path": "string",
  "abstract": "string",
  "keywords": ["string"],
  "citation_count": 0,
  "source": "arxiv / semantic_scholar / zotero / local",
  "relevance_score": 0.0,
  "triage_reason": "string"
}
```

文献元数据来源建议优先接 arXiv、Semantic Scholar 和 Zotero。本地科研工具里，arXiv API 适合程序化访问开放论文，Semantic Scholar API 适合查论文、作者、引用和 venues，Zotero API 适合接入你自己的文献库。([arXiv信息][5])

---

## 5.2 Evidence 对象

```json
{
  "evidence_id": "string",
  "paper_id": "string",
  "section": "Method",
  "page": 5,
  "chunk_id": "string",
  "quote": "string",
  "claim_supported": "string",
  "support_level": "strong / weak / inferred / unsupported"
}
```

这个非常重要。你的系统必须做到：

```text
没有证据，不允许生成强结论。
```

PaperQA / PaperQA2 的核心价值就是面向科学文献做带引用的 RAG 问答，强调从 full-text paper 中检索相关 passages 并生成有来源的回答。([GitHub][6]) PaperQA2 相关论文也专门强调科学文献 agent 的事实性、检索、总结和矛盾检测能力。([arXiv][7])

---

## 5.3 Method Card 对象

```json
{
  "method_card_id": "string",
  "paper_id": "string",
  "task": "string",
  "problem_setting": "string",
  "input_modalities": ["trajectory", "scene", "language", "video"],
  "output": "future trajectory",
  "model_architecture": {
    "encoder": "string",
    "decoder": "string",
    "diffusion_module": "string",
    "fusion_module": "string"
  },
  "temporal_modeling": "string",
  "fusion_strategy": {
    "type": "early / middle / late / cross-attention / gated",
    "description": "string"
  },
  "training_objective": "string",
  "datasets": ["string"],
  "metrics": ["ADE", "FDE"],
  "main_results": "string",
  "limitations": ["string"],
  "reusable_ideas_for_current_topic": ["string"],
  "implementation_difficulty": "low / medium / high",
  "risk": ["string"],
  "evidence_ids": ["string"]
}
```

方法卡是系统的核心产物。它把“读论文”变成“可用于研发的知识结构”。

---

## 5.4 Research Opportunity 对象

```json
{
  "opportunity_id": "string",
  "title": "string",
  "hypothesis": "string",
  "based_on_papers": ["paper_id"],
  "technical_strategy": "string",
  "expected_benefit": "string",
  "novelty_level": "low / medium / high",
  "implementation_difficulty": "low / medium / high",
  "data_requirement": "string",
  "risk": ["string"],
  "recommended_priority": 1
}
```

例如你的课题中可以生成：

```json
{
  "title": "Language-conditioned diffusion denoiser for pedestrian trajectory prediction",
  "hypothesis": "将行人自然语言描述作为扩散去噪网络的条件输入，可以改善多意图场景下的轨迹预测。",
  "technical_strategy": "使用 text encoder 提取语言特征，通过 cross-attention 注入 denoising network。",
  "expected_benefit": "改善目标不确定或意图不明确场景下的 FDE。",
  "implementation_difficulty": "medium"
}
```

---

## 5.5 Experiment Plan 对象

```json
{
  "experiment_id": "string",
  "name": "string",
  "hypothesis": "string",
  "baseline": "string",
  "modification": "string",
  "files_to_change": ["string"],
  "dataset": "string",
  "training_config": {
    "epochs": 50,
    "batch_size": 64,
    "learning_rate": 0.0001
  },
  "metrics": ["ADE", "FDE"],
  "ablation_studies": [
    "without language",
    "concat fusion",
    "cross-attention fusion",
    "gated fusion"
  ],
  "acceptance_criteria": {
    "must_run": true,
    "metric_improvement": "FDE improves over baseline",
    "no_data_leakage": true
  },
  "rollback_plan": "string"
}
```

这个对象可以直接交给 Developer Agent。

---

# 6. 记忆系统设计

你提到“记忆系统”，这是关键。科研多智能体的记忆不应该只是聊天历史，而应该分层。

我建议设计成六类 memory。

---

## 6.1 Working Memory：当前任务短期状态

保存当前 workflow 的状态：

```json
{
  "current_topic": "",
  "current_stage": "paper_reading",
  "selected_papers": [],
  "current_questions": [],
  "open_decisions": [],
  "temporary_notes": []
}
```

生命周期：一次任务内有效。

实现方式：

```text
LangGraph State / Python dict / SQLite run_state
```

LangGraph 适合这种长流程状态管理，因为它支持持久执行、恢复和 human-in-the-loop。([GitHub][3])

---

## 6.2 Project Memory：课题长期记忆

保存某个课题的长期背景：

```json
{
  "topic_id": "pedestrian_diffusion",
  "research_goal": "",
  "baseline": "",
  "dataset": "",
  "current_progress": "",
  "known_constraints": [],
  "important_decisions": [],
  "failed_attempts": [],
  "preferred_methods": []
}
```

例如：

```text
当前课题暂不优先提升行人意图识别准确率，优先研究语言描述如何条件化扩散轨迹预测模型。
```

生命周期：跨 session 长期有效。

实现方式：

```text
SQLite/PostgreSQL + vector index
```

---

## 6.3 Literature Memory：文献记忆

保存论文、chunk、方法卡、证据链：

```text
Paper
→ Section
→ Chunk
→ Claim
→ Evidence
→ Method Card
→ Related Opportunity
```

这类记忆不要混入普通聊天记忆。它应该是一个专业文献知识库。

实现方式：

```text
Qdrant / Milvus / Chroma + SQLite metadata
```

Qdrant 是开源向量相似度搜索引擎和向量数据库，适合存 embedding 和 payload 过滤。([GitHub][8]) Milvus 更偏大规模向量数据库，适合后期文献库很大时考虑。([GitHub][9])

---

## 6.4 Episodic Memory：实验过程记忆

保存每次实验发生了什么：

```json
{
  "experiment_id": "",
  "date": "",
  "hypothesis": "",
  "code_version": "",
  "config": "",
  "result": "",
  "logs": "",
  "failure_reason": "",
  "next_action": ""
}
```

用处：

```text
避免重复做失败实验
复盘哪些策略有效
让 agent 能根据历史结果调整下一步计划
```

---

## 6.5 Procedural Memory：流程记忆

保存“如何做某类任务”的经验：

```json
{
  "procedure_name": "read_trajectory_prediction_paper",
  "steps": [
    "extract task setting",
    "identify input modalities",
    "identify temporal modeling",
    "identify fusion strategy",
    "identify loss and metrics",
    "extract reusable ideas"
  ],
  "preferred_prompt": "",
  "known_failure_modes": []
}
```

这类记忆可以参考 LangMem。LangMem 提供从交互中抽取重要信息、优化 agent 行为和维护长期记忆的工具，并且能和 LangGraph 的存储层集成。([GitHub][10])

---

## 6.6 Artifact Memory：产物记忆

保存系统生成的文件：

```text
method_cards/*.json
reports/*.md
experiment_plans/*.yaml
patches/*.diff
test_logs/*.txt
review_reports/*.md
```

这类内容不要只存在对话里，要落盘，可回溯。

---

## 6.7 记忆系统参考项目

| 项目                 | 适合参考什么                                    | 是否建议直接用                |
| ------------------ | ----------------------------------------- | ---------------------- |
| **LangMem**        | LangGraph 生态下的长期记忆、行为优化、记忆抽取              | 后期如果迁移 LangGraph，建议优先用 |
| **Mem0**           | 通用长期记忆层、跨 session 个性化、低延迟记忆检索             | 可作为 memory backend 参考  |
| **Letta / MemGPT** | stateful agent、agent 自管理记忆、长期运行 agent     | 适合参考，不建议初期重度集成         |
| **Zep / Graphiti** | temporal knowledge graph memory，多跳与时间关系记忆 | 后期做复杂实验因果关系可参考         |

Mem0 的项目定位是“Universal memory layer for AI Agents”，其论文提出动态抽取、合并、检索显著记忆，并报告相比全上下文方法显著降低延迟和 token 成本。([GitHub][11]) Letta 定位为构建 stateful agents 的平台，强调 agent 能跨对话维护记忆和上下文。([GitHub][12]) Zep/Graphiti 方向则更适合需要时间关系和多跳关系的长期记忆。([arXiv][13])

我的建议：

```text
V1：自己实现轻量 memory，SQLite + Qdrant 即可。
V2：如果采用 LangGraph，接 LangMem。
V3：如果需要更复杂长期关系，参考 Zep/Graphiti 做 temporal KG。
不要一开始就上很重的记忆平台。
```

---

# 7. 检索系统设计

科研多智能体的能力上限，很大程度取决于检索系统。普通向量 RAG 不够，你至少需要 hybrid retrieval。

---

## 7.1 文献来源层

建议支持四种来源：

```text
1. arXiv：开放论文检索
2. Semantic Scholar：论文元数据、引用、相关论文
3. Zotero：你的个人文献库
4. Local PDF Folder：本地 PDF 文件夹
```

arXiv API 适合程序化访问 arXiv e-prints。([arXiv信息][5]) Semantic Scholar Academic Graph API 支持查 paper、author、citation、venue 等学术图谱数据。([Semantic Scholar][14]) Zotero Web API 支持访问在线 Zotero library，也可通过桌面客户端本地 API 访问本地库。([Zotero][15])

---

## 7.2 PDF 解析层

建议双方案：

```text
普通论文 PDF：Docling
学术结构精细解析：GROBID
```

Docling 支持 PDF、DOCX、PPTX、HTML、图片等多种格式，并支持 PDF 页面布局、阅读顺序、表格结构、公式、代码等解析。([Docling Project][16]) GROBID 专注于把科研 PDF 解析成结构化 XML/TEI，适合标题、作者、摘要、正文、参考文献等学术结构抽取。([GitHub][17])

我的建议：

```text
V1：Docling 优先，简单稳定。
V2：GROBID 补充，用于参考文献、章节、citation extraction。
V3：如果遇到扫描版 PDF，再接 OCR。
```

---

## 7.3 Chunk 策略

不要按固定 1000 token 切块。科研论文要按结构切：

```text
Title
Abstract
Introduction
Related Work
Method
Experiments
Ablation
Limitations
Conclusion
References
```

每个 chunk 保存：

```json
{
  "paper_id": "",
  "section": "Method",
  "subsection": "",
  "page_start": 4,
  "page_end": 5,
  "text": "",
  "figures": [],
  "tables": [],
  "citations": [],
  "embedding": []
}
```

方法、实验、结果部分的权重应该高于 introduction。

---

## 7.4 检索策略

推荐五路检索融合：

```text
1. Dense Vector Retrieval
语义检索，找相似内容。

2. Sparse / BM25 Retrieval
关键词检索，保证术语、模型名、数据集名不丢。

3. Metadata Filtering
按年份、领域、venue、任务、数据集过滤。

4. Citation Graph Expansion
从 seed paper 扩展 references 和 citations。

5. Method Card Retrieval
不是检索原文，而是检索已抽取的方法卡。
```

实际实现：

```text
query
→ query rewrite
→ vector retrieval
→ BM25 retrieval
→ citation expansion
→ metadata filter
→ reranker
→ evidence pack
→ answer / extraction
```

RAGFlow 可以作为深文档理解型 RAG 的参考，它强调从复杂格式非结构化数据中做深文档理解和带引用问答。([GitHub][18]) Haystack 也适合参考模块化 RAG pipeline，它支持检索、路由、记忆、生成和 agent workflow 的显式控制。([GitHub][19]) LlamaIndex 则适合参考文档基础设施、索引和 agentic 应用构建。([GitHub][20])

---

## 7.5 GraphRAG 是否需要？

建议后期加，不建议 V1 就上。

原因：

```text
普通 RAG 适合回答局部问题：
“这篇论文如何融合语言特征？”

GraphRAG 适合回答全局关系问题：
“这些论文中，扩散轨迹预测、语言条件、cross-attention、goal prediction 之间有什么技术演进关系？”
```

Microsoft GraphRAG 是从非结构化文本抽取知识图谱、构建社区层级和摘要，再基于这些结构做 RAG。([GitHub][21]) LightRAG 采用图结构和向量 embedding 的双层检索，以兼顾低层实体关系和高层主题信息。([GitHub][22])

你的系统可以先做轻量版科研知识图谱：

```text
Paper
Method
Dataset
Metric
Model
Module
Task
Claim
Experiment
CodeModule
```

关系：

```text
paper proposes method
method uses dataset
method optimizes metric
method contains module
claim supported_by evidence
opportunity derived_from method
experiment tests opportunity
```

这对跨课题复用非常有价值。

---

# 8. Agent 设计细化

## 8.1 Research Manager Agent

职责：

```text
理解课题需求
读取 Topic Pack
拆分研究问题
选择 workflow
决定是否检索、精读、生成实验计划或进入开发
```

输入：

```text
topic_pack
user_request
project_memory
```

输出：

```json
{
  "research_questions": [],
  "workflow_plan": [],
  "required_tools": [],
  "expected_artifacts": []
}
```

---

## 8.2 Literature Search Agent

职责：

```text
生成检索式
调用 arXiv / Semantic Scholar / Zotero
扩展引用网络
去重
初筛
```

需要有 query rewrite：

```text
原始问题：
“自然语言输入扩散模型预测行人轨迹”

扩展检索：
- language conditioned trajectory prediction
- text guided trajectory forecasting
- multimodal pedestrian trajectory prediction
- conditional diffusion trajectory forecasting
- goal conditioned diffusion trajectory prediction
```

输出：

```text
candidate_papers.json
```

---

## 8.3 Paper Triage Agent

职责：

```text
判断论文是否值得精读
```

评分维度：

```text
topic relevance
method novelty
reuse value
implementation feasibility
citation / venue importance
recency
```

输出：

```json
{
  "paper_id": "",
  "decision": "read / skim / discard",
  "reason": "",
  "score": 4.2
}
```

---

## 8.4 Deep Reading Agent

职责：

```text
按 section 阅读论文
抽取方法、实验、数据、指标、局限
```

它不应该直接写长摘要，而是回答固定问题：

```text
1. 这篇论文解决什么任务？
2. 输入是什么？
3. 输出是什么？
4. 模型结构是什么？
5. 时序信息如何建模？
6. 多模态信息如何融合？
7. 是否使用扩散模型？
8. loss 是什么？
9. baseline 是什么？
10. 数据集和指标是什么？
11. 有什么局限？
12. 对当前课题有什么可迁移点？
```

---

## 8.5 Evidence Checker Agent

职责：

```text
检查 Deep Reading Agent 的每条结论是否有原文证据。
```

规则：

```text
强结论：必须有 evidence span
推测：必须标记 inferred
无证据：标记 unsupported，不允许进入最终报告
```

这是防止科研幻觉的关键。

---

## 8.6 Method Card Agent

职责：

```text
把论文转成标准方法卡
```

它的输出是后续 Synthesis Agent 和 Experiment Planner Agent 的输入。

---

## 8.7 Synthesis Agent

职责：

```text
跨论文归纳技术路线
```

它应该输出：

```text
1. 方法分类
2. 技术演进
3. 常用数据集
4. 常用指标
5. 融合策略对比
6. 扩散模型使用方式对比
7. 当前课题可借鉴点
8. 潜在研究空白
```

这里可以参考 STORM 的知识整理流程。STORM 是 Stanford OVAL 的知识整理系统，目标是围绕 topic 做搜索并生成带引用的长报告。([GitHub][23]) 也可以参考 OpenScholar 这类面向科学文献的 RAG 系统，它强调先检索相关论文，再生成 grounded response。([GitHub][24])

---

## 8.8 Research Opportunity Agent

职责：

```text
从文献总结中生成可研究方向
```

要求：

```text
每个 idea 必须绑定：
- 来源论文
- 支持证据
- 技术路径
- 可实现性
- 风险
- 实验验证方式
```

不要让它凭空创新。它应该基于方法卡生成。

---

## 8.9 Experiment Planner Agent

职责：

```text
把 research opportunity 转成实验计划
```

例如：

```text
实验 1：Baseline Leapfrog
实验 2：Leapfrog + text embedding concat
实验 3：Leapfrog + gated fusion
实验 4：Leapfrog + cross-attention condition
实验 5：Leapfrog + text dropout
实验 6：Leapfrog + language-guided goal prediction
```

每个实验必须输出：

```text
改什么
为什么改
怎么训练
怎么评估
怎么消融
失败如何判断
失败后怎么回退
```

---

## 8.10 Developer Agent

职责：

```text
根据实验计划修改代码
```

但必须受控：

```text
1. 先读项目结构
2. 生成修改计划
3. 标明修改文件
4. 生成 patch
5. 运行测试
6. 输出 diff
7. 不自动提交
8. 不自动大规模训练
```

开发 agent 可以参考 OpenHands 和 SWE-agent。OpenHands 是面向 AI 软件开发 agent 的平台，支持 agent 写代码、使用命令行和浏览器，并强调沙箱环境与评估基准。([arXiv][25]) OpenHands SDK 也强调可扩展 agent、沙箱执行、生命周期控制和多模型路由。([arXiv][26]) SWE-agent 则强调 agent-computer interface 对代码导航、编辑和测试执行的重要性。([Swe Agent][27])

---

## 8.11 Reviewer Agent

职责：

```text
检查代码、实验、结论是否可靠
```

它应该检查：

```text
代码是否改错范围
实验是否真的运行
指标是否有效
是否有数据泄露
是否过度解释实验结果
是否应该继续该方向
```

---

# 9. AI Scientist-v2 的思想如何吸收

AI Scientist-v2 的关键价值是：

```text
1. 自动生成研究想法
2. 实验树搜索
3. 自动 debug
4. 结果分析
5. 论文生成
```

它的 main pipeline 包含 agentic tree search、实验执行、结果分析和 paper draft 生成。([GitHub][2])

你可以吸收它的“轻量实验树搜索”：

```text
root: current baseline

branch A: text concat
branch B: gated fusion
branch C: cross-attention
branch D: language-guided goal prediction

每个 branch：
1. 生成实验计划
2. 修改代码
3. 小样本跑通
4. 记录指标
5. 判断继续 / 剪枝
```

不要一开始做完全自动科研，而是做：

```text
Human-guided Experiment Tree Search
```

也就是：

```text
agent 提出分支
你选择保留哪些
agent 帮你执行
agent 记录结果
agent 根据结果推荐下一步
```

这样更稳。

---

# 10. 开源项目参考与取舍

## 10.1 主框架

| 项目               | 用法                             | 建议                                        |
| ---------------- | ------------------------------ | ----------------------------------------- |
| Agent Laboratory | 初始底座                           | **先 fork**                                |
| AI Scientist-v2  | 实验树搜索、idea generation、自动 debug | **参考，不直接做主框架**                            |
| LangGraph        | 最终工作流编排                        | **中长期迁移**                                 |
| CrewAI           | role-based agent 设计            | 可参考，不建议主用                                 |
| AutoGen          | 多 agent 原型                     | 谨慎；其 GitHub 已提示维护模式，但新文档仍强调事件驱动多 agent 框架 |

CrewAI 的强项是角色式协作和 Flows/Crews 抽象。([GitHub][28]) AutoGen 当前 GitHub 页面提示 maintenance mode，但其文档仍将其描述为事件驱动多智能体框架。([GitHub][29]) 因此我更建议主线选 Agent Laboratory + LangGraph，而不是 CrewAI/AutoGen。

---

## 10.2 文献阅读与 RAG

| 项目                  | 用法                   | 建议              |
| ------------------- | -------------------- | --------------- |
| PaperQA2            | 科学论文 QA、引用、证据链       | 强烈参考            |
| OpenScholar         | 科学文献检索增强回答           | 参考              |
| STORM               | 主题调研和综述生成            | 参考              |
| RAGFlow             | 深文档理解型 RAG           | 可参考或局部集成        |
| LlamaIndex          | 文档索引、RAG、agentic app | 可作为工具库          |
| Haystack            | 模块化 RAG pipeline     | 可参考 pipeline 设计 |
| GraphRAG / LightRAG | 跨论文关系和全局综合           | 后期加入            |

---

## 10.3 记忆系统

| 项目             | 用法                                  | 建议   |
| -------------- | ----------------------------------- | ---- |
| LangMem        | LangGraph 生态长期记忆                    | 后期优先 |
| Mem0           | 通用 agent memory layer               | 可参考  |
| Letta          | stateful agent / memory-first agent | 可参考  |
| Zep / Graphiti | temporal KG memory                  | 后期参考 |

---

## 10.4 代码开发 agent

| 项目              | 用法                   | 建议        |
| --------------- | -------------------- | --------- |
| OpenHands       | 代码 agent、沙箱、命令行、文件编辑 | 后期可接      |
| SWE-agent       | 代码修复、repo 导航、测试执行    | 参考 ACI 设计 |
| AI Scientist-v2 | 实验代码生成和 debug        | 参考流程      |

---

## 10.5 评估与可观测性

| 项目        | 用法                      | 建议              |
| --------- | ----------------------- | --------------- |
| Ragas     | RAG 评估                  | 用于检索与回答质量评估     |
| DeepEval  | LLM 应用单元测试              | 用于 agent 输出测试   |
| Phoenix   | tracing、观测、调试           | 用于记录 agent 运行过程 |
| Promptfoo | prompt 回归测试、red teaming | 用于 prompt 版本管理  |

RAGAS 是面向 RAG pipeline 的自动评估框架，覆盖检索上下文、回答忠实度等维度。([arXiv][30]) DeepEval 类似 “Pytest for LLM apps”，支持 answer relevancy、hallucination、task completion 等指标。([GitHub][31]) Phoenix 是开源 AI observability 平台，支持 LLM 应用 tracing、evaluation 和 troubleshooting。([GitHub][32]) Promptfoo 适合做 prompt 评估、回归测试和 red teaming。([GitHub][33])

---

# 11. 推荐技术栈

## V1：最小可用版

```text
Base:
- Agent Laboratory fork

Backend:
- Python
- FastAPI 可选

Storage:
- SQLite
- Local filesystem

Vector DB:
- Qdrant 或 Chroma

PDF:
- Docling
- GROBID 可选

RAG:
- 自建 hybrid RAG
- 参考 PaperQA2

Memory:
- 自建轻量 memory
- SQLite + Qdrant

Code execution:
- 本地 shell
- Docker sandbox 可选

UI:
- Streamlit
```

这个版本的目标是能用，不追求架构完美。

---

## V2：稳定可复用版

```text
Orchestration:
- LangGraph

Backend:
- FastAPI

Storage:
- PostgreSQL
- Qdrant

PDF:
- Docling + GROBID

RAG:
- hybrid retrieval
- reranker
- evidence checker
- method card store

Memory:
- LangMem 或自建 memory
- project memory
- experiment memory
- literature memory

Code:
- Docker sandbox
- Git diff
- pytest runner

Observability:
- Phoenix
- run logs
```

---

## V3：高级版

```text
GraphRAG:
- paper-method-dataset-metric graph
- citation graph
- experiment graph

Experiment Search:
- AI Scientist-v2 style tree search
- branch pruning
- automatic debug budget

Development Agent:
- OpenHands SDK / SWE-agent style ACI

Evaluation:
- Ragas
- DeepEval
- Promptfoo
- custom benchmarks
```

---

# 12. 推荐开发路线

## 阶段 1：先跑 Agent Laboratory

目标：

```text
跑通原项目
用你的真实课题测试
记录它在哪些地方有用，哪些地方不行
```

测试任务：

```text
请调研基于扩散模型的行人轨迹预测，重点关注 Leapfrog、MID、多模态融合、自然语言条件输入，并提出可执行实验计划。
```

验收：

```text
1. 是否能找对论文
2. 是否能区分扩散轨迹预测、行人意图、多模态融合
3. 是否能提出具体实验
4. 是否有明显胡编
5. 是否能生成代码开发方向
```

---

## 阶段 2：加 Topic Pack

目标：

```text
让系统能针对不同课题切换
```

实现：

```text
topics/
  pedestrian_diffusion.yaml
  vin_ocr.yaml
  generic_ml_research.yaml
```

每个 topic pack 包含：

```text
研究目标
关键词
排除词
相关数据集
常用指标
论文抽取模板
实验模板
代码仓库信息
```

---

## 阶段 3：重构文献系统

目标：

```text
从“文献总结”升级为“证据约束方法卡”
```

功能：

```text
1. arXiv / Semantic Scholar 检索
2. PDF 导入
3. Docling/GROBID 解析
4. chunk
5. embedding
6. hybrid retrieval
7. method card extraction
8. evidence check
```

这是整个系统最值得投入的部分。

---

## 阶段 4：加入记忆系统

目标：

```text
让系统记住不同课题的长期状态
```

实现：

```text
memory/
  global_memory
  project_memory
  literature_memory
  experiment_memory
  procedural_memory
```

第一版不复杂：

```text
SQLite 表结构 + Qdrant 向量索引
```

---

## 阶段 5：实验规划 agent

目标：

```text
把文献结论转成实验计划
```

输出：

```text
实验名称
假设
baseline
模型修改
数据修改
训练配置
指标
消融
验收标准
风险
```

---

## 阶段 6：代码开发 agent

目标：

```text
小范围自动改代码
```

严格限制：

```text
1. 每次只处理一个实验计划
2. 必须先输出修改计划
3. 必须限制可修改文件
4. 必须生成 diff
5. 必须运行测试
6. 必须输出验收报告
7. 失败最多 debug 两轮
```

---

## 阶段 7：实验树搜索

目标：

```text
参考 AI Scientist-v2，探索多个实验分支
```

但不要完全自动：

```text
agent 提出树
你选择分支
agent 执行
agent 记录
agent 分析
你决定下一步
```

---

# 13. 目录结构建议

```text
research_agent_lab/
│
├── app/
│   ├── main.py
│   ├── api/
│   └── ui/
│
├── core/
│   ├── workflow.py
│   ├── state.py
│   ├── agent_base.py
│   ├── tool_base.py
│   ├── memory_base.py
│   └── artifact_store.py
│
├── agents/
│   ├── research_manager.py
│   ├── literature_searcher.py
│   ├── paper_triage.py
│   ├── paper_reader.py
│   ├── evidence_checker.py
│   ├── method_card_extractor.py
│   ├── synthesis_agent.py
│   ├── opportunity_agent.py
│   ├── experiment_planner.py
│   ├── developer_agent.py
│   └── reviewer_agent.py
│
├── tools/
│   ├── arxiv_tool.py
│   ├── semantic_scholar_tool.py
│   ├── zotero_tool.py
│   ├── pdf_parser_docling.py
│   ├── pdf_parser_grobid.py
│   ├── vector_search.py
│   ├── graph_search.py
│   ├── git_tool.py
│   ├── code_executor.py
│   └── test_runner.py
│
├── memory/
│   ├── project_memory.py
│   ├── literature_memory.py
│   ├── experiment_memory.py
│   ├── procedural_memory.py
│   └── memory_policy.py
│
├── schemas/
│   ├── topic_pack.py
│   ├── paper.py
│   ├── evidence.py
│   ├── method_card.py
│   ├── opportunity.py
│   ├── experiment_plan.py
│   ├── code_task.py
│   └── review_result.py
│
├── workflows/
│   ├── literature_review.yaml
│   ├── method_synthesis.yaml
│   ├── experiment_planning.yaml
│   ├── code_development.yaml
│   └── full_research_loop.yaml
│
├── topics/
│   ├── pedestrian_diffusion.yaml
│   ├── vin_ocr.yaml
│   └── generic_ml.yaml
│
├── data/
│   ├── papers/
│   ├── parsed/
│   ├── vector_db/
│   ├── method_cards/
│   ├── reports/
│   ├── experiments/
│   └── patches/
│
└── evals/
    ├── rag_eval.yaml
    ├── method_card_eval.yaml
    ├── experiment_plan_eval.yaml
    └── coding_agent_eval.yaml
```

---

# 14. 系统评估指标

你自用也要评估，否则会越改越乱。

## 14.1 文献检索评估

```text
Recall@K：
给定 seed papers，检索前 K 篇是否能召回。

Relevance Precision：
Top K 中真正相关论文比例。

Coverage：
是否覆盖 baseline、最新方法、相关综述、关键数据集。
```

---

## 14.2 论文阅读评估

```text
Method Card Completeness：
方法卡字段完整率。

Evidence Support Rate：
结论中有证据支持的比例。

Unsupported Claim Rate：
无证据强结论比例。

Citation Accuracy：
引用是否真的支持该结论。
```

---

## 14.3 研发计划评估

```text
Executability：
实验计划能否真正执行。

Specificity：
是否明确到文件、模块、参数、指标。

Ablation Quality：
是否包含合理消融。

Risk Awareness：
是否说明失败风险和回退方案。
```

---

## 14.4 代码 agent 评估

```text
Patch Validity：
diff 是否能应用。

Test Pass Rate：
测试是否通过。

Scope Control：
是否只修改允许文件。

Regression：
是否破坏原功能。

Human Review Cost：
你需要花多久检查它的输出。
```

---

# 15. 你最终应该做成什么样

我建议最终系统交互方式是这样的：

```text
你：
新建课题：基于扩散模型的多模态行人轨迹预测。

系统：
已创建 Topic Pack。
请确认 baseline、数据集、目标指标。

你：
baseline 是 Leapfrog 和 MID，指标用 ADE/FDE，重点研究语言条件输入。

系统：
生成检索计划：
1. diffusion trajectory prediction
2. language conditioned trajectory forecasting
3. multimodal pedestrian trajectory prediction
4. cross-attention fusion trajectory prediction

系统：
检索到 80 篇论文，筛选出 15 篇精读，生成方法卡。

系统：
综合结论：
最适合当前课题的三个方向是：
A. text embedding concat baseline
B. cross-attention language-conditioned denoiser
C. language-guided goal prediction + diffusion refinement

系统：
是否生成实验计划？

你：
生成 B 方案。

系统：
输出实验计划、代码修改范围、训练配置、消融实验和验收标准。
```

这才是对你毕设开发真正有用的科研 agent。

---

# 16. 最终推荐方案

你可以按下面这个技术路线执行：

```text
主路线：
Agent Laboratory 二开启动
→ 自建 Topic Pack
→ 自建 Method Card / Evidence / Experiment Plan schema
→ 自建轻量 memory
→ 自建 hybrid literature RAG
→ 参考 PaperQA2 做证据约束
→ 参考 AI Scientist-v2 做实验树搜索
→ 后期迁移 LangGraph
→ 后期接 OpenHands / SWE-agent 做代码开发
```

一句话概括：

> **先用 Agent Laboratory 起步，尽快得到可用科研助手；核心能力自己重构成“Topic Pack + 方法卡 + 证据检索 + 分层记忆 + 实验计划 + 受控开发”的平台化结构；AI Scientist-v2 只吸收实验树搜索和自动 debug 思路；LangGraph、PaperQA2、LangMem、GraphRAG、OpenHands 分别作为编排、文献证据、长期记忆、关系检索和代码开发模块的参考。**

[1]: https://agentlaboratory.github.io/?utm_source=chatgpt.com "Agent Laboratory"
[2]: https://github.com/sakanaai/ai-scientist-v2?utm_source=chatgpt.com "The AI Scientist-v2: Workshop-Level Automated Scientific ..."
[3]: https://github.com/langchain-ai/langgraph?utm_source=chatgpt.com "langchain-ai/langgraph: Build resilient agents."
[4]: https://arxiv.org/abs/2501.04227?utm_source=chatgpt.com "Agent Laboratory: Using LLM Agents as Research Assistants"
[5]: https://info.arxiv.org/help/api/user-manual.html?utm_source=chatgpt.com "arXiv API User's Manual"
[6]: https://github.com/future-house/paper-qa?utm_source=chatgpt.com "Future-House/paper-qa: High accuracy RAG for answering ..."
[7]: https://arxiv.org/abs/2409.13740?utm_source=chatgpt.com "Language agents achieve superhuman synthesis of scientific knowledge"
[8]: https://github.com/qdrant/qdrant?utm_source=chatgpt.com "GitHub - qdrant/qdrant: Qdrant - High-performance ..."
[9]: https://github.com/milvus-io/milvus?utm_source=chatgpt.com "Milvus is a high-performance, cloud-native vector database ..."
[10]: https://github.com/langchain-ai/langmem?utm_source=chatgpt.com "langchain-ai/langmem"
[11]: https://github.com/mem0ai/mem0?utm_source=chatgpt.com "mem0ai/mem0: Universal memory layer for AI Agents"
[12]: https://github.com/letta-ai/letta?utm_source=chatgpt.com "Letta (formerly MemGPT)"
[13]: https://arxiv.org/abs/2501.13956?utm_source=chatgpt.com "Zep: A Temporal Knowledge Graph Architecture for Agent Memory"
[14]: https://www.semanticscholar.org/product/api?utm_source=chatgpt.com "Semantic Scholar Academic Graph API"
[15]: https://www.zotero.org/support/dev/web_api/v3/basics?utm_source=chatgpt.com "Zotero Web API Documentation"
[16]: https://docling-project.github.io/docling/?utm_source=chatgpt.com "Index - Docling"
[17]: https://github.com/grobidOrg/grobid?utm_source=chatgpt.com "grobidOrg/grobid: A machine learning software ..."
[18]: https://github.com/infiniflow/ragflow?utm_source=chatgpt.com "RAGFlow is a leading open-source Retrieval-Augmented ..."
[19]: https://github.com/deepset-ai/haystack?utm_source=chatgpt.com "deepset-ai/haystack: Open-source AI orchestration ..."
[20]: https://github.com/run-llama/llama_index?utm_source=chatgpt.com "run-llama/llama_index: LlamaIndex is the leading ..."
[21]: https://github.com/microsoft/graphrag?utm_source=chatgpt.com "microsoft/graphrag: A modular graph-based Retrieval- ..."
[22]: https://github.com/hkuds/lightrag?utm_source=chatgpt.com "LightRAG: Simple and Fast Retrieval-Augmented Generation"
[23]: https://github.com/stanford-oval/storm?utm_source=chatgpt.com "stanford-oval/storm: An LLM-powered knowledge curation ..."
[24]: https://github.com/akariasai/openscholar?utm_source=chatgpt.com "AkariAsai/OpenScholar: This repository ..."
[25]: https://arxiv.org/abs/2407.16741?utm_source=chatgpt.com "OpenHands: An Open Platform for AI Software Developers as Generalist Agents"
[26]: https://arxiv.org/abs/2511.03690?utm_source=chatgpt.com "The OpenHands Software Agent SDK: A Composable and Extensible Foundation for Production Agents"
[27]: https://swe-agent.com/latest/?utm_source=chatgpt.com "Getting Started - SWE-agent documentation"
[28]: https://github.com/crewaiinc/crewai?utm_source=chatgpt.com "crewAIInc/crewAI: Framework for orchestrating role-playing ..."
[29]: https://github.com/microsoft/autogen?utm_source=chatgpt.com "microsoft/autogen: A programming framework for agentic AI"
[30]: https://arxiv.org/abs/2309.15217?utm_source=chatgpt.com "RAGAS: Automated Evaluation of Retrieval Augmented Generation"
[31]: https://github.com/confident-ai/deepeval?utm_source=chatgpt.com "confident-ai/deepeval: The LLM Evaluation Framework"
[32]: https://github.com/arize-ai/phoenix?utm_source=chatgpt.com "Arize-ai/phoenix: AI Observability & Evaluation"
[33]: https://github.com/promptfoo/promptfoo?utm_source=chatgpt.com "Promptfoo: LLM evals & red teaming"
