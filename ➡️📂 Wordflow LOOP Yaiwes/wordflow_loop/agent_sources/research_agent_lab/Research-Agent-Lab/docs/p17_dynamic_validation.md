# P17 Dynamic Validation Runbook

This runbook validates that a run can be inspected after completion.

Use the `video_llava` interpreter:

`D:\Develop_Tools\Anaconda3\envs\video_llava\python.exe`

## 1. Full Unit Suite

```bash
D:\Develop_Tools\Anaconda3\envs\video_llava\python.exe -m unittest discover -s tests -p test*.py
```

Expected: all tests pass.

## 2. Offline Minimal Run

```bash
D:\Develop_Tools\Anaconda3\envs\video_llava\python.exe -m app.main run --topic topics\intent_led_virat.json --data-dir tmp\p17_validation\offline --max-papers 1
```

Then validate the printed run directory:

```bash
D:\Develop_Tools\Anaconda3\envs\video_llava\python.exe -m app.main validate-run --run-dir <printed_run_dir> --strict
```

Expected: validation does not block.

## 3. Retrieval Evaluation Run

```bash
D:\Develop_Tools\Anaconda3\envs\video_llava\python.exe -m app.main run --topic topics\intent_led_virat.json --data-dir tmp\p17_validation\retrieval --max-papers 2 --enable-retrieval-evaluation
```

Then:

```bash
D:\Develop_Tools\Anaconda3\envs\video_llava\python.exe -m app.main validate-run --run-dir <printed_run_dir> --strict
```

Expected: `retrieval_evaluations` exists and validation does not block.

## 4. LLM Budget-Zero Run

```bash
D:\Develop_Tools\Anaconda3\envs\video_llava\python.exe -m app.main run --topic topics\intent_led_virat.json --data-dir tmp\p17_validation\llm_budget_zero --max-papers 1 --enable-llm --llm-call-budget 0
```

Then:

```bash
D:\Develop_Tools\Anaconda3\envs\video_llava\python.exe -m app.main validate-run --run-dir <printed_run_dir> --strict
```

Expected: no real API call is required; validation does not require successful LLM output.

## 5. Experiment Smoke Run

```bash
D:\Develop_Tools\Anaconda3\envs\video_llava\python.exe -m app.main run --topic topics\intent_led_virat.json --data-dir tmp\p17_validation\experiment --max-papers 1 --enable-experiments
```

Then:

```bash
D:\Develop_Tools\Anaconda3\envs\video_llava\python.exe -m app.main validate-run --run-dir <printed_run_dir> --strict
```

Expected: `experiment_results` and `code_patches` are present and cross-linked.

## 6. Required Real API Smoke

Run with the user-confirmed tiny budget. This is required for P17 acceptance:

```bash
D:\Develop_Tools\Anaconda3\envs\video_llava\python.exe -m app.main run --topic topics\intent_led_virat.json --data-dir tmp\p17_validation\api --max-papers 1 --enable-llm --llm-call-budget 2 --llm-token-budget 12000
```

Then validate the printed run directory.

Expected: `llm_calls` records contain no secrets and link to debug records when debug records exist.
