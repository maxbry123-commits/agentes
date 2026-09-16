# Model and Literature Configuration

## Local Paper Library

`topics/intent_led_virat.json` now points to the local paper folders:

- `C:/Users/duyul/Desktop/work/Essay/轨迹预测/EPC`
- `C:/Users/duyul/Desktop/work/Essay/轨迹预测/SPK`

The workflow scans these folders recursively for `*.pdf`, `*.md`, and `*.txt`.
Local papers are used before arXiv or offline seed records.

Current V1 behavior:

- Indexes local file metadata.
- Uses filenames as paper titles.
- Ranks papers by topic keyword overlap.
- Parses selected local PDFs with `pypdf` when it is installed in the active
  Python environment.

Unified runtime:

```powershell
D:\Develop_Tools\Anaconda3\envs\video_llava\python.exe
```

`pypdf` is installed in this environment for local PDF parsing.

## Model Routing

The default workflow is still offline/rule-based. It does not call Codex or a
paid model by default.

Configured DeepSeek routes use one DeepSeek API key with two model tiers:

- Simple/batch tasks use `deepseek-v4-flash`.
- Hard/reasoning-heavy tasks use `deepseek-v4-pro`.

Current split:

- `paper_triage`: `deepseek-v4-flash`
- `synthesis`: `deepseek-v4-flash`
- `result_parser`: `deepseek-v4-flash`
- `method_card_extractor`: `deepseek-v4-pro`
- `experiment_planner`: `deepseek-v4-pro`
- `reviewer_agent`: `deepseek-v4-pro`

These routes read the API key from the environment variable:

```powershell
$env:DEEPSEEK_API_KEY = "your_key_here"
```

The CLI also loads a project-root `.env` file automatically. Do not put real API
keys in tracked files. `.env` is ignored by git; use `.env.example` only as a
template.

Check whether the key and local paper library are visible:

```powershell
D:\Develop_Tools\Anaconda3\envs\video_llava\python.exe -m app.main check-config --topic topics\intent_led_virat.json
```

Run the workflow without paid model calls:

```powershell
D:\Develop_Tools\Anaconda3\envs\video_llava\python.exe -m app.main run --topic topics\intent_led_virat.json --data-dir data --max-papers 8
```

Allow supported agents to use their configured model route:

```powershell
D:\Develop_Tools\Anaconda3\envs\video_llava\python.exe -m app.main run --topic topics\intent_led_virat.json --data-dir data --max-papers 3 --enable-llm
```

The CLI uses conservative default limits when model calls are enabled:

- `--llm-call-budget 3`
- `--llm-token-budget 20000`

For a one-paper smoke run, use:

```powershell
D:\Develop_Tools\Anaconda3\envs\video_llava\python.exe -m app.main run --topic topics\intent_led_virat.json --data-dir data --max-papers 1 --enable-llm --llm-call-budget 1
```

Current LLM-enabled implementation:

- `method_card_extractor` can call `deepseek-v4-pro` through the
  DeepSeek-compatible client.
- It only attempts a call when `--enable-llm` is present and the selected paper
  has parsed local text.
- If the route is disabled, the key is missing, the network fails, or the model
  returns invalid JSON, the agent falls back to rule-based method cards.
- Non-secret call records are saved under
  `data/runs/<run_id>/artifacts/llm_calls/`; API keys and full prompts are not
  saved.
- A verified one-paper method-card run used roughly 4.7k total tokens on
  `deepseek-v4-pro`, so review `llm_calls` before increasing batch size.

## Cost Policy

The intended policy is:

- Current Codex is only the development operator for this repository.
- Do not route internal multi-agent tasks to the current Codex session.
- Use local/rule-based logic for scanning, codebase analysis, logs, and simple
  workflow routing.
- Use DeepSeek only for tasks that need language reasoning over paper text or
  experiment design.
- Use `deepseek-v4-flash` for simple/batch tasks and `deepseek-v4-pro` for hard
  reasoning tasks.
