<div align="center">

# PRISM

### Pareto-Efficient Retrieval over Intent-Aware Structured Memory for Long-Horizon Agents

[![Project Page](https://img.shields.io/badge/🌐_Project_Page-PRISM-1f5fa8.svg?style=flat&labelColor=555)](https://jingyip-cat.github.io/PRISM/)
[![arXiv](https://img.shields.io/badge/arXiv-2605.12260-b31b1b.svg?style=flat&labelColor=555)](https://arxiv.org/abs/2605.12260)
[![Python](https://img.shields.io/badge/python-3.10+-3776A9.svg?style=flat&labelColor=555&logo=python&logoColor=white)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-2EA44F.svg?style=flat&labelColor=555)](LICENSE)
[![Benchmark: LoCoMo](https://img.shields.io/badge/benchmark-LoCoMo-14B8A6.svg?style=flat&labelColor=555)](https://github.com/snap-research/locomo)

**A training-free, retrieval-side memory framework that hits high answer accuracy at an order-of-magnitude smaller context budget.**

🌐 [**Project Page**](https://jingyip-cat.github.io/PRISM/) &nbsp;|&nbsp; 📄 [**Paper**](https://arxiv.org/abs/2605.12260)

[Overview](#-overview) • [Results](#-results) • [Install](#-installation) • [Quick Start](#-quick-start) • [How It Works](#-how-it-works) • [Reproducing the Paper](#-reproducing-the-paper) • [Citation](#-citation)

</div>

---

> **Note on naming.** The Python package is named `mmem` for historical reasons. It implements the **PRISM** framework described in the paper above; `mmem` and PRISM refer to the same system throughout this repository.

## 🌟 Overview

Long-horizon language agents accumulate conversation history far faster than any fixed context window can hold, which makes memory management critical to **both** answer accuracy **and** serving cost. The quality of a memory system is governed by two coupled quantities: the **accuracy** of the answers it supports, and the **context cost** — the number of tokens packed into the answer model's prompt for every query.

Prior systems advance these along separate axes: ingestion-heavy systems reach high accuracy but retrieve large candidate pools; long-context backbones pay a heavy token cost for moderate accuracy; graph-based memory adds relational structure but sits at moderate accuracy and cost. The **high-accuracy / low-cost corner of the frontier is left largely empty.**

**PRISM** occupies that corner. It is a *training-free, retrieval-side* framework that operates over an already-constructed graph memory and treats long-horizon memory as a joint **retrieval-and-compression** problem. It needs no fine-tuning and no modification to the upstream ingestion pipeline — it plugs into any backend that exposes its node/edge schema.

PRISM composes **four orthogonal inference-time modules**:

| | Module | Role |
|---|---|---|
| **N1** | **Hierarchical Bundle Search** | Scores candidate episodes by the *minimum-cost typed path* over relation templates, recovering evidence that flat similarity misses. |
| **N2** | **Query-Sensitive Edge Costing** | Re-weights traversal cost by detected query intent — temporal/causal edges become cheaper when the query needs them. |
| **N3** | **Evidence Compression** | A single content-only LLM call re-ranks and compresses the candidate bundle into a compact answer-side context. |
| **N4** | **Adaptive Intent Routing** | Routes most queries through zero-LLM tiers (keyword → prototype → LLM fallback), concentrating LLM cost on hard cases. |

## 📈 Results

All same-protocol rows use `gpt-4o-mini` as both answer and judge model (temperature 0.0), and share the same answer prompt, judge prompt, tokenizer, and token-counting procedure. Evaluation is on **LoCoMo** categories 1–4 (1,540 QA pairs). Metrics: **Judge** = LLM-judge accuracy; **Per-1K Eff.** = judge points per 1K retrieved context tokens; **Ctx** = average context tokens per query.

### Main results on LoCoMo

| Method | Multi-Hop | Temporal | Open-Dom. | Single-Hop | **Overall** | Per-1K Eff. | Ctx tokens/query |
|---|---|---|---|---|---|---|---|
| Full Context | 0.468 | 0.562 | 0.486 | 0.630 | 0.481 | 0.018 | 26,031 |
| MAGMA | 0.528 | 0.650 | 0.517 | 0.776 | 0.688 | 0.204 | 3,370 |
| Mem0 | 0.512 | 0.555 | 0.729 | 0.671 | 0.669 | 0.379 | 1,764 |
| Mem0ᵍ | 0.472 | 0.581 | 0.757 | 0.657 | 0.684 | 0.189 | 3,616 |
| **PRISM (ours)** | **0.787** | **0.788** | **0.813** | **0.863** | **0.831** | **0.411** | 2,023 |

*Best same-protocol result per column in bold.*

PRISM achieves the highest overall judge score (**0.831**) — beating Mem0ᵍ by +14.2 pp, MAGMA by +14.0 pp, and Full Context by +35.2 pp — while delivering the best accuracy-per-token (**0.411** vs. 0.379 for the next-best). It is the sole same-protocol method on the accuracy–efficiency frontier.

#### Different-protocol references (stronger answer LLM / managed commercial pipeline)

| Method | Overall | Per-1K Eff. | Ctx tokens/query |
|---|---|---|---|
| M-Flow | 0.818 | 0.316 | 2,588 |
| PRISM (gpt-5.5) | 0.891 | 0.440 | 2,023 |
| Mem0 platform | 0.916 | 0.131 | ~7,000 |

Swapping only the answer model from `gpt-4o-mini` to `gpt-5.5` — holding the retrieval pipeline and ingest checkpoint fixed — lifts PRISM from 0.831 to **0.891** at the same 2,023-token budget.

### Context-efficiency frontier

Compared with Full Context, PRISM achieves a **13× context reduction** (~26K → ~2K tokens) with a **+35 pp judge gain** (0.481 → 0.831). The two improvements are aligned rather than traded off.

### Ablation study

Each row changes **one** flag relative to PRISM; all variants reuse the same ingest checkpoint.

| Configuration | Judge | ER@5 | Ctx Tokens |
|---|---|---|---|
| **PRISM** | 0.831 | 0.694 | 2,023 |
| − N1 (relation paths) | 0.831 | 0.694 | 2,024 |
| − N2 (cost adjustment) | 0.831 | 0.694 | 2,020 |
| − N3 (LLM re-rank) | 0.825 | **0.627** | **4,108** |
| + N4 (hybrid intent) | 0.833 | 0.694 | 2,023 |

**N3 (Evidence Compression)** is the dominant lever: removing it drops ER@5 by 6.8 pp and roughly doubles answer-side context (2,023 → 4,108 tokens). **N1/N2** are null on LoCoMo because the benchmark is mostly anchor-discoverable (73.4% of questions cite a single evidence entry, only ~3% need a two-hop bridge); they are designed for lexically-mismatched multi-hop settings such as MuSiQue or bridge-style HotpotQA. **N4** removes 42.3% of classifier-side LLM calls at no measurable accuracy cost.

> See the [paper](https://arxiv.org/abs/2605.12260) for full per-category numbers, paired-bootstrap confidence intervals, McNemar mid-*p* values, and the N4 routing breakdown.

## 📦 Installation

**Requirements:** Python 3.10+, an OpenAI-compatible API key. PRISM is **CPU-only** — no GPU is required (FAISS `IndexFlatIP` retrieval + graph traversal).

```bash
# Clone
git clone https://github.com/<your-username>/PRISM.git
cd PRISM

# (recommended) create a virtual environment
python -m venv .venv
# Windows:  .venv\Scripts\activate
# macOS/Linux:  source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure your API key
cp .env.example .env
# then edit .env and set OPENAI_API_KEY
```

The sentence encoder (`all-MiniLM-L6-v2`, 384-dim) is downloaded automatically from HuggingFace on first run.

## 🚀 Quick Start

### Smoke test (no API key needed)

A fully offline smoke test exercises the ingest → checkpoint → reload → search pipeline using a deterministic rule-based stub:

```bash
python scripts/smoke_test_alice.py
```

### Run on LoCoMo

The evaluation entry point is a module (`scripts.eval.run_locomo`). The LoCoMo dataset is **downloaded automatically** on first run.

> ⚠️ **`PYTHONHASHSEED=0` is required.** The runner refuses to start otherwise — this guarantees bit-reproducible retrieval. Set it in the same command:

```bash
# Sanity check on a single conversation (PowerShell)
$env:PYTHONHASHSEED=0; python -m scripts.eval.run_locomo --mode sanity --conv-id 0

# Full benchmark, all 10 conversations (bash/zsh)
PYTHONHASHSEED=0 python -m scripts.eval.run_locomo --mode full
```

By default `--ablation A1` runs the **full PRISM system**. A summary report and per-conversation JSON results are written under `scripts/eval/results/<ablation>/`.

## 🧠 How It Works

PRISM retrieves over a **multi-relational memory graph** `G = (V, E, τ)` built once at write time.

**Four node layers** (a hierarchy of granularity): `Entity` → `FacetPoint` → `Facet` → `Episode`, where an Episode is the original conversation chunk and the unit returned to the answer model.

**Two edge families:** hierarchical `belongs_to` containment edges, plus five typed cross-cutting relations — `semantic`, `temporal`, `causal`, `evolution`, and `involves_entity`.

At query time the four modules compose into a fixed sequence:

```
h(q)  ← N4  Adaptive Intent Routing       (keyword → prototype → LLM fallback)
c_edge ← N2  Query-Sensitive Edge Cost     (re-weight typed edges by intent)
B     ← N1  Hierarchical Bundle Search     (min-cost typed-path candidate bundle, top-K)
B*    ← N3  Evidence Compression           (single LLM call, content-only → top-M)
```

The pipeline issues **at most two LLM calls per query** in the worst case (N4 fallback + N3 selection), and only **one** on queries handled by N4's cheap tiers. Everything else is deterministic vector arithmetic and graph traversal.

### Repository layout

```
mmem/                       # PRISM core library (the "mmem" package)
├── core/                   # graph, nodes, typed edges
│   ├── graph.py
│   ├── nodes.py
│   └── edges.py
├── ingestion/              # write-time graph construction
│   ├── extractor.py        # schema-guided LLM extraction
│   ├── graph_builder.py    # node/edge construction + merging
│   ├── consolidation.py    # asynchronous causal consolidation
│   ├── pipeline.py         # end-to-end ingest + checkpointing
│   └── prompts.py
├── retrieval/              # query-time modules (N1–N4)
│   ├── anchor_discovery.py # N1 phase 1: multi-layer FAISS anchors
│   ├── subgraph_extractor.py
│   ├── path_scorer.py      # N1: min-cost typed-path scoring
│   ├── intent_classifier.py / intent_resources.py  # N4
│   ├── query_preprocessor.py / query_decomposer.py
│   ├── reranker.py         # N3: evidence compression
│   ├── output_assembler.py
│   └── search.py           # bundle_search orchestration
├── indexing/vector_store.py
├── utils/                  # embedding, llm client
└── config.py               # all hyper-parameters (MMemConfig)

scripts/
├── eval/                   # LoCoMo evaluation harness
│   ├── run_locomo.py       # main entry point (python -m scripts.eval.run_locomo)
│   ├── run_locomo_full_context.py / run_locomo_naive_rag.py  # baselines
│   ├── locomo_loader.py / locomo_chunker.py
│   ├── metrics.py / prompts.py / report.py
│   └── gated_diagnostics.py
└── smoke_test_alice.py     # offline end-to-end smoke test

tests/                      # unit + integration tests (pytest)
```

## 🔬 Reproducing the Paper

All experiments reuse a single ingest checkpoint per conversation, so ablations differ **only** in retrieval-side configuration. The runner exposes ablations via `--ablation`, and `--checkpoint-ablation` lets retrieval-only variants reuse the full-system ingest graph (no re-ingestion).

| Paper cell | Command (prefix each with `PYTHONHASHSEED=0`) |
|---|---|
| **PRISM (full)** — Table 1 | `python -m scripts.eval.run_locomo --mode full --ablation A1` |
| **− N1** (no relation paths) | `python -m scripts.eval.run_locomo --mode full --ablation A2_clean --checkpoint-ablation A1` |
| **− N2** (no cost adjustment) | `python -m scripts.eval.run_locomo --mode full --ablation A10_no_cost_adj --checkpoint-ablation A1` |
| **− N3** (no LLM re-rank) | `python -m scripts.eval.run_locomo --mode full --ablation A1_no_rerank --checkpoint-ablation A1` |
| **+ N4** (hybrid intent routing) | `python -m scripts.eval.run_locomo --mode full --ablation R5-1 --checkpoint-ablation A1` |
| **Full Context** baseline | `python -m scripts.eval.run_locomo_full_context --mode full` |
| **Naive RAG** baseline | `python -m scripts.eval.run_locomo_naive_rag --mode full` |

Hyper-parameters are fixed across all rows and documented in `mmem/config.py` (and mirrored in `config.example.py`). They match Table 5 of the paper: FAISS top-k = 30, bundle size K = 10, rerank size M = 5, edge-cost discounts α ∈ {0.5, 0.7, 1.0}, random seed 42.

### Running tests

```bash
pip install pytest
pytest
```

## 📝 Citation

If you use PRISM in your research, please cite:

```bibtex
@article{peng2026prism,
  title   = {PRISM: Pareto-Efficient Retrieval over Intent-Aware Structured Memory for Long-Horizon Agents},
  author  = {Peng, Jingyi and Wan, Zhongwei and Liu, Weiting and Sun, Qiuzhuang},
  journal = {arXiv preprint arXiv:2605.12260},
  year    = {2026},
  url     = {https://arxiv.org/abs/2605.12260}
}
```

## 🙏 Acknowledgments

- **Benchmark:** [LoCoMo](https://github.com/snap-research/locomo) — long-conversation memory evaluation.
- **Embedding model:** [all-MiniLM-L6-v2](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2) (Apache-2.0).
- **Vector index:** [FAISS](https://github.com/facebookresearch/faiss) (MIT).

The answer-then-judge evaluation protocol follows the public Mem0 memory-benchmarks LoCoMo evaluation, adapted with project-specific prompts.

## 📄 License

Released under the [MIT License](LICENSE).
