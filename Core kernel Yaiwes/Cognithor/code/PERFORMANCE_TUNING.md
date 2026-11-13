# Performance Tuning Guide

> Optimize Cognithor for your hardware and use case.

## Table of Contents

- [Hardware Profiles](#hardware-profiles)
- [LLM Backend Selection](#llm-backend-selection)
- [Memory Optimization](#memory-optimization)
- [Token Budget Management](#token-budget-management)
- [PGE Loop Tuning](#pge-loop-tuning)
- [Web Search Performance](#web-search-performance)
- [Monitoring](#monitoring)

---

## Hardware Profiles

Cognithor uses the PGE-Trinity architecture: **Planner** (reasoning), **Executor** (tool calling), and **Embedding** (semantic search). Each model requires dedicated VRAM.

| VRAM | Planner | Executor | Embedding | Expected Speed |
|------|---------|----------|-----------|----------------|
| 6 GB | qwen3:8b | qwen3:8b | nomic-embed-text | ~5s/response |
| 12 GB | qwen3:14b | qwen3:8b | nomic-embed-text | ~4s/response |
| 24 GB | qwen3:32b | qwen3:8b | qwen3-embedding:0.6b | ~3s/response |
| 48 GB+ | qwen3:32b | qwen3-coder:30b | qwen3-embedding:0.6b | ~2s/response |

### Model Configuration

Edit `~/.jarvis/config.yaml`:

```yaml
models:
  planner:
    name: qwen3:32b
    context_window: 32768
    vram_gb: 20.0
  executor:
    name: qwen3:8b
    context_window: 32768
    vram_gb: 6.0
  coder:
    name: qwen3-coder:30b
    context_window: 32768
    vram_gb: 20.0
  coder_fast:
    name: qwen2.5-coder:7b
    context_window: 32768
    vram_gb: 5.0
  embedding:
    name: qwen3-embedding:0.6b
    context_window: 8192
    vram_gb: 0.5
    embedding_dimensions: 1024
```

### Ollama Keep-Alive

Models stay in VRAM for `keep_alive` duration after last use. Reduce to free memory sooner:

```yaml
ollama:
  base_url: http://localhost:11434
  timeout_seconds: 120
  keep_alive: "5m"    # Default: 30m
```

---

## LLM Backend Selection

Cognithor supports multiple LLM backends. Choose based on your priorities:

| Backend | Strengths | Weaknesses | Cost |
|---------|-----------|------------|------|
| **Ollama** (local) | Privacy, no API costs, offline capable | Requires GPU, slower on small GPUs | Hardware only |
| **OpenAI** | Fastest inference, strong tool calling (gpt-5.x) | Privacy concerns, pay-per-token | $0.01-0.06/1K tokens |
| **Anthropic** | Best reasoning (Claude), strong safety | Pay-per-token, rate limits | $0.01-0.08/1K tokens |

### Mixing Backends

You can use different backends for Planner and Executor:

```yaml
models:
  planner:
    name: claude-sonnet-4-20250514    # Best reasoning
    backend: anthropic
  executor:
    name: qwen3:8b            # Fast, local tool calling
    backend: ollama
```

---

## Memory Optimization

### Embedding Cache

The embedding cache reduces duplicate computations for repeated queries. Stored in `~/.jarvis/cache/`:

```yaml
memory:
  embedding_cache_enabled: true
  embedding_cache_max_size: 10000   # Max cached embeddings
```

### Chunk Size

Controls how text is split before embedding:

- **Larger chunks** (512-1024 tokens): fewer lookups, broader context per result
- **Smaller chunks** (128-256 tokens): more precise retrieval, higher lookup count

```yaml
memory:
  chunk_size: 512
  chunk_overlap: 64
```

### Episodic Memory Compaction

The `EpisodicCompressor` periodically summarizes old episodic memories to keep the index lean:

```yaml
memory:
  compressor_enabled: true
  compressor_age_days: 30     # Summarize entries older than 30 days
```

### FAISS Index

The vector index (FAISS HNSW) uses approximately 1 GB per 500K entries. Monitor index size:

```bash
ls -lh ~/.jarvis/memory/
```

Reduce `top_k` if searches are slow:

```yaml
memory:
  retrieval_top_k: 10         # Default: 20
```

---

## Token Budget Management

### Context Pipeline

The context pipeline assembles input for the Planner. Control total input size:

```yaml
context_pipeline:
  max_context_tokens: 16384   # Max tokens sent to Planner
  memory_budget: 4096         # Tokens reserved for memory context
  vault_budget: 2048          # Tokens reserved for vault content
```

### Planner Output

Limit Planner output to reduce generation time:

```yaml
planner:
  max_tokens: 4096            # Max response length
  response_token_budget: 2048 # For formulate_response()
```

### Session History

Limit how much conversation history is retained per session:

```yaml
session:
  max_history_messages: 50    # Older messages are summarized
  max_history_tokens: 8192
```

---

## PGE Loop Tuning

The Planner-Gatekeeper-Executor loop iterates until the task is complete or a limit is hit.

### Iteration Limits

```yaml
planner:
  max_iterations: 25          # Default: 25, reduce for faster (but less thorough) responses
  max_tool_calls_per_step: 5  # Parallel tool calls per iteration
```

Reducing `max_iterations` to 15 can halve response time for simple queries at the cost of complex multi-step tasks.

### Gatekeeper Performance

The Gatekeeper classifies tool risk synchronously. Unknown tools default to ORANGE (requires audit). Register frequently-used custom tools in `_classify_risk()` green/yellow sets to skip the audit overhead.

### Executor Timeout

```yaml
executor:
  default_timeout_seconds: 30   # Per tool call
  # Media tools have higher limits: 120-180s
```

---

## Web Search Performance

### Backend Priority

Cognithor uses a multi-backend search fallback chain: SearXNG -> Brave -> Google CSE -> DuckDuckGo.

For best performance, run a local SearXNG instance:

```yaml
web:
  searxng_url: "http://localhost:8888"   # Fastest option
  search_rate_limit_seconds: 2           # DuckDuckGo rate limit
```

### Search Cache

Results are cached in `~/.jarvis/cache/web_search/` to avoid redundant lookups:

```yaml
web:
  cache_enabled: true
  cache_ttl_seconds: 3600     # 1 hour
```

### search_and_read vs web_search

For factual queries, prefer `search_and_read` (fetches full pages using trafilatura) over `web_search` (returns only snippets). This produces better results but takes longer.

---

## Monitoring

### Dashboard

Access the monitoring dashboard at:

```
GET /api/v1/monitoring/dashboard
```

This returns a JSON snapshot of system health: active sessions, tool call rates, memory usage, error rates.

### Swagger / OpenAPI

Interactive API documentation is available at:

```
http://localhost:8741/api/docs     # Swagger UI
http://localhost:8741/api/redoc    # ReDoc
```

### Key Metrics to Watch

| Metric | Healthy Range | Action if Outside |
|--------|---------------|-------------------|
| Response time | < 5s median | Reduce model size or max_iterations |
| PGE iterations/request | 1-10 | Check Planner prompt quality |
| Tool error rate | < 5% | Review Gatekeeper blocks, tool params |
| Memory index size | < 500K entries | Run compaction |
| Ollama VRAM usage | < 90% | Use smaller models or increase keep_alive |
| WebSocket reconnects | < 1/hour | Check network stability |

### Structured Logging

Cognithor uses structured logging. Increase log level for performance debugging:

```bash
python -m jarvis --log-level DEBUG
```

Or set via environment variable:

```bash
export JARVIS_LOG_LEVEL=DEBUG
```
