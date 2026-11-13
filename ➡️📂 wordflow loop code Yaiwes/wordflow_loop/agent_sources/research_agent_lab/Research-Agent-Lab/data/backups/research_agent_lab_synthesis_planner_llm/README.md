# Research Agent Lab

Research Agent Lab is a local-first scaffold for a reusable scientific
multi-agent system. It follows the direction in `code_plan.md`: topic packs,
structured artifacts, layered memory, workflow orchestration, and controlled
developer-agent behavior.

The first implementation slice is intentionally dependency-light. It can run an
offline smoke workflow without LLM keys, vector databases, or external search
services. Online integrations such as Agent Laboratory, arXiv, Semantic Scholar,
Docling, Qdrant, LangGraph, and PaperQA2 are represented by stable interfaces and
can be attached incrementally.

## What Works Now

- Load a topic pack from JSON.
- Run a full offline research loop:
  - research manager
  - literature search seed generator
  - paper triage
  - evidence extraction
  - method-card extraction
  - synthesis
  - research-opportunity generation
  - experiment planning
  - developer task planning
  - reviewer checks
- Persist run state, memory events, JSON artifacts, and Markdown reports under
  `data/runs/<run_id>/`.
- Keep code-development actions scoped and human-reviewed by default.
- Generate Agent Laboratory YAML configs from topic packs without launching the
  external long-running workflow.
- Configure the copied `Intent-LED-mul-agent` project with explicit allowed and
  protected paths.
- Scan the configured local paper library before falling back to online or
  offline seed papers.
- Record model-routing policy so expensive model calls can be limited to
  selected agents.
- Treat Codex as the development operator only; internal multi-agent tasks are
  routed to local rules or configured model APIs.
- Optionally use DeepSeek for method-card extraction when `--enable-llm` is
  passed; the default run remains offline.

## Quick Start

```powershell
python -m app.main run --topic topics/pedestrian_diffusion.json
```

On this Windows workstation, use the unified project interpreter explicitly:

```powershell
D:\Develop_Tools\Anaconda3\envs\video_llava\python.exe -m app.main run --topic topics/intent_led_virat.json --data-dir data --max-papers 8
```

Allow configured model routes for the agents that support them:

```powershell
D:\Develop_Tools\Anaconda3\envs\video_llava\python.exe -m app.main run --topic topics/intent_led_virat.json --data-dir data --max-papers 3 --enable-llm
```

For the current implementation, `--enable-llm` is wired into
`method_card_extractor`. It uses the topic's configured `deepseek-v4-pro` route
only when parsed paper text is available, and writes non-secret call records
under `data/runs/<run_id>/artifacts/llm_calls/`.

The CLI also applies conservative run-level API limits by default:
`--llm-call-budget 3` and `--llm-token-budget 20000`. Raise these explicitly
only after reviewing a small run.

Run tests:

```powershell
D:\Develop_Tools\Anaconda3\envs\video_llava\python.exe -m unittest discover -s tests
```

Generate an Agent Laboratory config for the copied LED/VIRAT project:

```powershell
D:\Develop_Tools\Anaconda3\envs\video_llava\python.exe -m app.main agentlab-config --topic topics/intent_led_virat.json --output agentlab_configs/intent_led_virat_agentlab.yaml
```

The generated command is printed but not executed automatically. Edit the API key
placeholder before running Agent Laboratory.

Local literature and model routing are configured in
`topics/intent_led_virat.json`; details are in
`docs/model_and_literature_config.md`.

## Project Layout

```text
app/                 CLI entry points
agents/              Specialized research agents
core/                Workflow, state, artifact store, agent/tool base classes
memory/              SQLite-backed memory and memory policy helpers
schemas/             Standard structured artifacts
tools/               Tool adapters such as arXiv, git, code execution
topics/              Topic packs
workflows/           Workflow factories and definitions
tests/               Smoke and contract tests
data/                Runtime artifacts, ignored by git
```

## Next Development Steps

1. Wire DeepSeek into synthesis, experiment planning, and review agents behind
   the same `--enable-llm` and budget gates.
2. Add richer paper chunk selection before each LLM call.
3. Add real arXiv and Semantic Scholar retrieval as fallback sources.
4. Add backup-and-apply support for protected codebase edits.
5. Add vector search and hybrid retrieval.
