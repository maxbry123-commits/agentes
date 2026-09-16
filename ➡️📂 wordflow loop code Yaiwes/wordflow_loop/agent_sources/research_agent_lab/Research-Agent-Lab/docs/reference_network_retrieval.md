# Reference Network Retrieval

P13 connects `ReferenceExtractorAgent` output to later literature search runs.

## Data Flow

```text
LocalPaperParserAgent
→ ReferenceExtractorAgent
→ LiteratureMemoryPersistenceAgent
→ LiteratureMemoryStore.lit_references
→ LiteratureSearchAgent with --enable-reference-expansion
```

Reference expansion is cross-run by design. A run first extracts references from parsed papers. A later run can reuse persisted references as additional search seeds.

## CLI

Offline reference seed run:

```powershell
D:\Develop_Tools\Anaconda3\envs\video_llava\python.exe -m app.main run --topic topics\intent_led_virat.json --data-dir data --max-papers 4 --enable-reference-expansion --max-reference-seeds 4
```

Online arXiv expansion run:

```powershell
D:\Develop_Tools\Anaconda3\envs\video_llava\python.exe -m app.main run --topic topics\intent_led_virat.json --data-dir data --online --enable-reference-expansion --max-reference-seeds 4
```

## Safety

- Reference expansion is disabled by default.
- Online arXiv calls require `--online`.
- DeepSeek calls still require `--enable-llm`.
- Reference seeds are deterministic and written to `state.values["reference_search_seeds"]`.
