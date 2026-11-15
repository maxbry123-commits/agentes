---
sidebar_position: 9
title: Configuration
---

# Configuration

Most runs need no config file at all — the launcher (`pentestswarm run`) and
`scan` flags cover everything. A `config.yaml` is there for when you want to
**pin a provider and model**, **override individual agents**, or check the file
into a repo for reproducible runs.

## Getting a starter config

```bash
pentestswarm init
```

`init` writes a starter `config.yaml` you can edit. Two companion commands help
you keep an environment healthy:

- **`pentestswarm doctor`** — health check: verifies Go, Docker, installed recon
  tools, and provider configuration, and tells you exactly what to fix.
- **`pentestswarm install-tools`** — fetches the recon / exploit toolchain
  (subfinder, httpx, nuclei, naabu, katana, dnsx, gau, nmap, …) so the swarm has
  real tools to operate.

## `config.yaml`

### `orchestrator`

The orchestrator block is the swarm's default LLM configuration — every agent
inherits from it unless a per-agent override says otherwise.

```yaml
orchestrator:
  provider: "together"        # together | claude | openai | gemini | orcarouter | ollama | lmstudio
  model: ""                   # explicit model id; leave empty to use the provider default
  api_key: ""                 # or set PENTESTSWARM_ORCHESTRATOR_API_KEY
  endpoint: ""                # base URL — auto-configured for most providers
  context_window: 128000      # tokens
```

| Field | Meaning |
|-------|---------|
| `provider` | Which LLM provider to use. See [Providers](./providers.md). |
| `model` | Explicit model id. Leave empty to take the provider's default (and, for `together`, its automatic per-task routing). |
| `api_key` | The key. Can also come from the `PENTESTSWARM_ORCHESTRATOR_API_KEY` env var or the launcher's key field. |
| `endpoint` | Base URL. Auto-configured for most providers; set it for a custom OpenAI-compatible endpoint. |
| `context_window` | Context size in tokens. |

### Per-agent overrides (`agents`)

The swarm has four agent roles — **recon**, **classifier**, **exploit**, and
**report**. You can override any of them individually with its own `model`,
`provider`, and `api_key`:

```yaml
agents:
  recon:
    model: "meta-llama/Llama-3.3-70B-Instruct-Turbo"
  classifier:
    model: "Qwen/Qwen2.5-72B-Instruct-Turbo"
  exploit:
    provider: "claude"        # run just the exploit agent on a different provider
    api_key: ""
  report:
    model: "meta-llama/Llama-3.3-70B-Instruct-Turbo"
```

:::note Explicit model always wins
An explicit per-agent `model` **always beats** the automatic routing that the
`together` provider does. If you set a model here, that's the model that agent
uses — the auto-routing only applies to agents you leave unset. See
[Providers → Together AI](./providers.md#together-ai).
:::

## Setting the key via environment

For any cloud provider you can skip `api_key` in the file and export the key
instead:

```bash
export PENTESTSWARM_ORCHESTRATOR_API_KEY=your-key-here
```

The launcher's key field, the `orchestrator.api_key` config value, and this env
var are three interchangeable ways to supply the same key. Local providers
(**Ollama**, **LM Studio**) need no key at all.

## Precedence, in short

1. **Per-agent `model`/`provider`** in `agents.*` — most specific, wins for that
   agent.
2. **`orchestrator`** block — the default every un-overridden agent inherits.
3. **`PENTESTSWARM_ORCHESTRATOR_API_KEY`** / launcher key field — supplies the
   key when the config doesn't.
