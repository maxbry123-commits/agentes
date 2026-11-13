# Database Reference

Cognithor uses SQLite (WAL mode) for all local storage. Optional PostgreSQL is available for production deployments.

---

## Database Files

| Database | Location | Purpose |
|----------|----------|---------|
| `memory.db` | `~/.cognithor/index/` | Main memory index (chunks, embeddings, knowledge graph) |
| `sessions.db` | `~/.cognithor/memory/sessions/` | Session state and chat history |
| `memory_episodic.db` | `~/.cognithor/index/` | Episodic memory (daily logs, summaries) |
| `memory_traces.db` | `~/.cognithor/index/` | GEPA execution traces |
| `memory_proposals.db` | `~/.cognithor/index/` | GEPA optimization proposals |
| `memory_runs.db` | `~/.cognithor/index/` | Forensic run recordings |
| `memory_governance.db` | `~/.cognithor/index/` | Self-improvement governance proposals |
| `memory_prompt_evolution.db` | `~/.cognithor/index/` | Prompt A/B testing data |
| `memory_weights.db` | `~/.cognithor/index/` | Hybrid search weight optimization |
| `memory_costs.db` | `~/.cognithor/index/` | LLM cost tracking |
| `marketplace.db` | `~/.cognithor/` | Skill Marketplace listings, reviews, reputation |
| `tool_registry.db` | `~/.cognithor/` | Persistent tool registry |
| `consent.db` | `~/.cognithor/` | User consent records (data portal) |
| `reminders.db` | `~/.cognithor/` | Scheduled reminders |
| `message_queue.db` | `~/.cognithor/memory/` | Durable message queue |
| `working_memory.db` | `~/.cognithor/identity/` | Identity working memory (Cognitio engine) |
| `session_analysis.db` | `~/.cognithor/learning/` | Session failure clusters, feedback, metrics |
| `knowledge_qa.db` | `~/.cognithor/memory/` | Knowledge QA pairs |
| `knowledge_lineage.db` | `~/.cognithor/memory/` | Knowledge provenance/lineage tracking |

---

## Schema Overview

### memory.db (Main Memory Index)

```sql
-- Document chunks for semantic search
chunks (
    id            TEXT PRIMARY KEY,
    source        TEXT,
    content       TEXT,
    token_count   INTEGER,
    metadata_json TEXT,
    created_at    TEXT
)

-- Embedding vectors (FAISS index stored separately)
embeddings (
    chunk_id       TEXT PRIMARY KEY,
    embedding_blob BLOB,
    model          TEXT,
    dimensions     INTEGER
)

-- Knowledge graph entities
entities (
    id         TEXT PRIMARY KEY,
    name       TEXT,
    type       TEXT,
    properties TEXT,
    created_at TEXT
)

-- Knowledge graph relations
relations (
    id         TEXT PRIMARY KEY,
    source_id  TEXT,
    target_id  TEXT,
    type       TEXT,
    properties TEXT,
    created_at TEXT
)
```

### sessions.db (Session Store)

```sql
-- Active and historical sessions
sessions (
    session_id   TEXT PRIMARY KEY,
    agent        TEXT,
    channel      TEXT,
    user_id      TEXT,
    created_at   TEXT,
    last_active  TEXT,
    metadata     TEXT
)

-- Chat message history
chat_history (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id   TEXT,
    role         TEXT,
    content      TEXT,
    timestamp    TEXT,
    metadata     TEXT
)

-- Channel-to-session mappings
channel_mappings (
    channel_type TEXT,
    channel_id   TEXT,
    session_id   TEXT,
    PRIMARY KEY (channel_type, channel_id)
)

-- User preferences (auto-learned)
user_preferences (
    user_id    TEXT,
    key        TEXT,
    value      TEXT,
    updated_at TEXT,
    PRIMARY KEY (user_id, key)
)
```

### memory_episodic.db (Episodic Memory)

```sql
-- Daily interaction episodes
episodes (
    id         TEXT PRIMARY KEY,
    date       TEXT,
    session_id TEXT,
    role       TEXT,
    content    TEXT,
    timestamp  TEXT,
    metadata   TEXT
)

-- Daily episode summaries
episode_summaries (
    date       TEXT PRIMARY KEY,
    summary    TEXT,
    created_at TEXT
)
```

### memory_traces.db (GEPA Execution Traces)

```sql
-- Top-level execution traces
execution_traces (
    trace_id          TEXT PRIMARY KEY,
    session_id        TEXT,
    goal              TEXT,
    success_score     REAL,
    model_used        TEXT,
    total_duration_ms INTEGER,
    created_at        TEXT
)

-- Individual steps within a trace
trace_steps (
    step_id        TEXT PRIMARY KEY,
    trace_id       TEXT,
    parent_id      TEXT,
    seq            INTEGER,
    tool_name      TEXT,
    input_summary  TEXT,
    output_summary TEXT,
    status         TEXT,
    error_detail   TEXT,
    duration_ms    INTEGER,
    ts             TEXT
)
```

### memory_proposals.db (GEPA Optimization)

```sql
optimization_proposals (
    id           TEXT PRIMARY KEY,
    trace_ids    TEXT,
    proposal     TEXT,
    status       TEXT,
    score_before REAL,
    score_after  REAL,
    created_at   TEXT,
    applied_at   TEXT
)
```

### memory_runs.db (Forensic Run Recorder)

```sql
-- Complete agent runs for debugging
runs (
    run_id     TEXT PRIMARY KEY,
    session_id TEXT,
    goal       TEXT,
    status     TEXT,
    started_at TEXT,
    ended_at   TEXT,
    metadata   TEXT
)

-- Individual steps in a run
run_steps (
    step_id    TEXT PRIMARY KEY,
    run_id     TEXT,
    seq        INTEGER,
    tool_name  TEXT,
    input      TEXT,
    output     TEXT,
    status     TEXT,
    duration   REAL
)

-- Policy state snapshots per run
run_policy_snapshots (
    id         INTEGER PRIMARY KEY,
    run_id     TEXT,
    policy     TEXT,
    snapshot   TEXT
)
```

### memory_governance.db (Self-Improvement Governance)

```sql
proposals (
    id          TEXT PRIMARY KEY,
    domain      TEXT,
    description TEXT,
    status      TEXT,
    created_at  TEXT,
    decided_at  TEXT,
    metadata    TEXT
)
```

### memory_prompt_evolution.db (A/B Testing)

```sql
prompt_versions (
    id         TEXT PRIMARY KEY,
    name       TEXT,
    content    TEXT,
    score      REAL,
    created_at TEXT
)

prompt_sessions (
    id         TEXT PRIMARY KEY,
    version_id TEXT,
    session_id TEXT,
    score      REAL,
    created_at TEXT
)

ab_tests (
    id           TEXT PRIMARY KEY,
    control_id   TEXT,
    variant_id   TEXT,
    status       TEXT,
    started_at   TEXT,
    completed_at TEXT
)
```

### memory_weights.db (Search Weight Optimization)

```sql
search_outcomes (
    id        TEXT PRIMARY KEY,
    query     TEXT,
    results   TEXT,
    feedback  TEXT,
    weights   TEXT,
    timestamp TEXT
)

weight_state (
    id        INTEGER PRIMARY KEY,
    weights   TEXT,
    score     REAL,
    timestamp TEXT
)
```

### memory_costs.db (Cost Tracking)

```sql
llm_costs (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp       TEXT,
    model           TEXT,
    provider        TEXT,
    input_tokens    INTEGER,
    output_tokens   INTEGER,
    cost_usd        REAL,
    session_id      TEXT,
    tool_name       TEXT
)
```

### marketplace.db (Skill Marketplace)

```sql
listings (
    id           TEXT PRIMARY KEY,
    name         TEXT,
    description  TEXT,
    author       TEXT,
    version      TEXT,
    category     TEXT,
    tags         TEXT,
    source       TEXT,
    content      TEXT,
    metadata     TEXT,
    created_at   TEXT,
    updated_at   TEXT
)

reviews (
    id         TEXT PRIMARY KEY,
    listing_id TEXT,
    user_id    TEXT,
    rating     INTEGER,
    comment    TEXT,
    created_at TEXT
)

reputation (
    author_id TEXT PRIMARY KEY,
    score     REAL,
    reviews   INTEGER
)

reputation_log (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    author_id TEXT,
    action    TEXT,
    delta     REAL,
    timestamp TEXT
)

install_history (
    id         TEXT PRIMARY KEY,
    listing_id TEXT,
    user_id    TEXT,
    action     TEXT,
    timestamp  TEXT
)

publishers (
    publisher_id   TEXT PRIMARY KEY,
    display_name   TEXT,
    trust_level    TEXT,
    public_key     TEXT,
    created_at     TEXT
)

recalls_remote (
    recall_id   TEXT PRIMARY KEY,
    skill_id    TEXT,
    reason      TEXT,
    severity    TEXT,
    recalled_at TEXT
)
```

### tool_registry.db (Persistent Tool Registry)

```sql
tools (
    name        TEXT PRIMARY KEY,
    module      TEXT,
    description TEXT,
    schema      TEXT,
    metadata    TEXT,
    registered  TEXT
)
```

### session_analysis.db (Learning)

```sql
failure_clusters (
    id         TEXT PRIMARY KEY,
    pattern    TEXT,
    count      INTEGER,
    last_seen  TEXT,
    resolution TEXT
)

cluster_occurrences (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    cluster_id TEXT,
    session_id TEXT,
    timestamp  TEXT
)

user_feedback (
    id         TEXT PRIMARY KEY,
    session_id TEXT,
    rating     INTEGER,
    comment    TEXT,
    timestamp  TEXT
)

improvement_actions (
    id          TEXT PRIMARY KEY,
    type        TEXT,
    description TEXT,
    status      TEXT,
    created_at  TEXT,
    applied_at  TEXT
)

session_metrics (
    id           TEXT PRIMARY KEY,
    session_id   TEXT,
    duration_ms  INTEGER,
    tool_calls   INTEGER,
    success      BOOLEAN,
    timestamp    TEXT
)
```

### consent.db (User Data Portal)

```sql
consents (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id    TEXT,
    scope      TEXT,
    granted    BOOLEAN,
    timestamp  TEXT
)
```

### reminders.db (Notifications)

```sql
reminders (
    id         TEXT PRIMARY KEY,
    user_id    TEXT,
    message    TEXT,
    due_at     TEXT,
    channel    TEXT,
    status     TEXT,
    created_at TEXT
)
```

### message_queue.db (Durable Queue)

```sql
message_queue (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    channel     TEXT,
    user_id     TEXT,
    content     TEXT,
    priority    INTEGER,
    status      TEXT,
    retries     INTEGER DEFAULT 0,
    created_at  TEXT,
    processed_at TEXT
)
```

### working_memory.db (Identity / Cognitio)

```sql
interactions (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    role       TEXT,
    content    TEXT,
    timestamp  TEXT,
    session_id TEXT,
    metadata   TEXT
)

pending_memories (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    content    TEXT,
    source     TEXT,
    priority   REAL,
    created_at TEXT
)
```

### Profiler Databases

Located at `~/.cognithor/index/`:

```sql
-- Tool call profiling
tool_calls (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    tool_name   TEXT,
    duration_ms REAL,
    success     BOOLEAN,
    timestamp   TEXT
)

-- Task-level profiling
task_records (
    id          TEXT PRIMARY KEY,
    session_id  TEXT,
    duration_ms REAL,
    tool_count  INTEGER,
    success     BOOLEAN,
    timestamp   TEXT
)
```

### Causal Learning

```sql
-- Causal action sequences
causal_sequences (
    id          TEXT PRIMARY KEY,
    trigger     TEXT,
    actions     TEXT,
    outcome     TEXT,
    confidence  REAL,
    count       INTEGER,
    created_at  TEXT
)
```

### Knowledge QA

```sql
qa_pairs (
    id         TEXT PRIMARY KEY,
    question   TEXT,
    answer     TEXT,
    source     TEXT,
    confidence REAL,
    created_at TEXT
)
```

### Knowledge Lineage

```sql
lineage (
    id          TEXT PRIMARY KEY,
    chunk_id    TEXT,
    source_type TEXT,
    source_ref  TEXT,
    created_at  TEXT,
    metadata    TEXT
)
```

### Task Telemetry

```sql
task_telemetry (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id   TEXT,
    task_type    TEXT,
    duration_ms  REAL,
    tool_count   INTEGER,
    token_count  INTEGER,
    success      BOOLEAN,
    error        TEXT,
    timestamp    TEXT
)
```

---

## Backup

```bash
# Backup all databases (Linux/macOS)
cp -r ~/.cognithor/index/ ~/backup/cognithor-index/
cp -r ~/.cognithor/memory/ ~/backup/cognithor-memory/
cp ~/.cognithor/marketplace.db ~/backup/
cp ~/.cognithor/tool_registry.db ~/backup/
cp ~/.cognithor/consent.db ~/backup/
cp ~/.cognithor/reminders.db ~/backup/

# Backup all databases (Windows PowerShell)
Copy-Item -Recurse "$HOME\.cognithor\index" "$HOME\backup\cognithor-index"
Copy-Item -Recurse "$HOME\.cognithor\memory" "$HOME\backup\cognithor-memory"
Copy-Item "$HOME\.cognithor\marketplace.db" "$HOME\backup\"
```

---

## SQLite Encryption

Optional SQLCipher encryption can be enabled for all SQLite databases:

```yaml
database:
  encryption_enabled: true
  encryption_backend: keyring   # Uses OS credential store
```

Install the encryption extra: `pip install cognithor[encryption]`

The encryption key is stored in the OS keyring (Windows Credential Manager, macOS Keychain, Linux Secret Service). See `src/cognithor/db/encryption.py` for details.

---

## PostgreSQL Migration

For production deployments, configure PostgreSQL in `config.yaml`:

```yaml
database:
  backend: postgresql
  pg_host: localhost
  pg_port: 5432
  pg_dbname: cognithor
  pg_user: cognithor
  pg_password: your-secure-password
  pg_pool_min: 2
  pg_pool_max: 10
```

The PostgreSQL schema is defined in `src/cognithor/db/pg_schema.sql` and includes equivalent tables for chunks, embeddings, entities, relations, sessions, and chat_history.

---

## WAL Mode

All SQLite databases use WAL (Write-Ahead Logging) mode for better concurrent read performance. The `sqlite_max_retries` and `sqlite_retry_base_delay` config options control retry behavior on lock contention.
