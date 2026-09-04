# Datagen tools

Small entrypoints for creating, transforming, inspecting, and publishing datasets. Run Python tools from the repository root; use `--help` for their complete CLI. Prefer the cluster launch skills and `hpc.launch` for managed datagen jobs.

## Generate data

| Tool | Use it for | Main inputs and outputs |
|---|---|---|
| `async_datagen.py` | High-concurrency, non-agentic generation against an OpenAI-compatible vLLM endpoint. | Reads a Hugging Face prompt dataset; writes resumable JSONL/Parquet checkpoints and can push completions to a Hugging Face dataset repo. |
| `curator_datagen.py` | Non-agentic generation through Bespoke Curator's hosted-vLLM backend. | Reads a Hugging Face prompt dataset; supports resume, sharding, checkpoints, and optional Hub upload. |
| `submit_curator_sharded.sh` | Submit a sharded standard-datagen Slurm chain with restart dependencies. | Wraps `data/sbatches/run_curator_datagen_sharded.sbatch`; pass model, input dataset, and output repo after `--`. |
| `gsm8k_terminal_bench_traces.py` | Generate Harbor traces for the GSM8K Terminal Bench task dataset. | Ensures the task dataset is local, then runs the shared `BaseDataGenerator` workflow. |

## Prepare task datasets

| Tool | Use it for | Main inputs and outputs |
|---|---|---|
| `extract_tasks_from_parquet.py` | Materialize Harbor-compatible task directories from a task parquet snapshot or Hugging Face task repo. | Produces canonical task folders for trace generation; handles both `task_binary` parquet and raw task directories. |
| `find_task_binary_datasets.py` | Inventory datasets in the configured Hugging Face organization that expose a `task_binary` field. | Writes a Markdown inventory beside the script. |
| `collect_task_binaries.py` | Bundle selected task-binary dataset repos without changing their contents. | Reads repo IDs from Markdown and uploads each source repo under its own subdirectory in a target Hub dataset repo. |

## Transform or combine datasets

| Tool | Use it for | Main inputs and outputs |
|---|---|---|
| `prep_for_thinking.py` | Normalize assistant reasoning blocks for Qwen3/LLaMA-Factory SFT. | Import `reformat_assistant_content` or preprocess a Hub/local dataset; preserves content while standardizing `<think>` structure. |
| `join_hf_repos.py` | Concatenate an explicit ordered list of compatible Hugging Face dataset repos. | Loads matching splits, cleans empty structs when available, and pushes the combined dataset to a target repo. |
| `concatenate_training_datasets.py` | Build one provenance-labelled corpus from datasets referenced by model records in Supabase. | Streams source datasets through temporary parquet shards and pushes a combined Hub dataset. |

## Inspect and validate

| Tool | Use it for | Main inputs and outputs |
|---|---|---|
| `count_conversation_tokens.py` | Measure aggregate dataset tokens using an explicit representation. | Defaults to legacy compact-JSON `serialized` `conversations`; `conversation_text` and `chat_template` are separate opt-in measurements. Reads one Hub split and does not modify it. |
| `print_trace_contents.py` | Quickly inspect the latest Harbor trace messages and optional ShareGPT projection. | Reads a local trace/job directory via Harbor; prints one representative trace. |
| `reasoning_content_smoke.py` | Check whether a LiteLLM-supported model returns reasoning content in the Harbor-style request path. | Sends diagnostic requests to a configured model endpoint; requires the provider credential. |
| `gemini_hello_world.py` | Smoke-test Gemini prompt templating and thinking-level configuration. | Uses `google-genai` and configured Google credentials; prints model and response diagnostics. |

## Credentials and side effects

- Hub reads may need `HF_TOKEN`; scripts that create or push datasets require it.
- `concatenate_training_datasets.py` also requires `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY`.
- Generation tools write checkpoints and may upload output when an output repo is configured. Use a disposable output location for smoke tests.
