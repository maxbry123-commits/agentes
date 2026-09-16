# Retrieval Evaluation

`RetrievalEvaluationAgent` measures literature retrieval quality.

It is opt-in in P14:

```powershell
D:\Develop_Tools\Anaconda3\envs\video_llava\python.exe -m app.main run --topic topics\intent_led_virat.json --data-dir data --max-papers 4 --enable-retrieval-evaluation
```

## Outputs

- `state.values["retrieval_evaluation"]`
- `state.values["retrieval_evaluation_status"]`
- `state.values["retrieval_quality_score"]`
- `artifacts/retrieval_evaluations/*.json`

## Deterministic Checks

- candidate paper count
- selected paper count
- source mix
- topic keyword coverage
- selected-paper keyword coverage
- reference seed inclusion
- duplicate title rate
- low relevance reference seed count

## Optional LLM Judge

The judge is disabled by default. It only runs when both flags are present:

```powershell
--enable-llm --enable-retrieval-judge
```

Use a small top K and budget:

```powershell
--retrieval-judge-top-k 3 --llm-call-budget 2 --llm-token-budget 12000
```

Unit tests mock the judge and do not call real APIs.
