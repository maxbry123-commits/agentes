# Pack SDK & Developer Documentation — Design Spec

**Date:** 2026-04-18
**Status:** Approved
**Goal:** Enable external developers to build compatible Cognithor packs with clear documentation, a CLI scaffolding tool, and a typed SDK package.

## Scope: Phase 1

Phase 1 delivers the foundation for the Q4 2026 creator marketplace. Three deliverables:

1. **Developer Guide** — 4 MDX pages on cognithor.ai/docs/packs/
2. **`cognithor pack create`** — CLI scaffolding command
3. **`cognithor-sdk`** — Minimal PyPI stub package with typed interfaces

## Deliverable 1: Developer Guide

### Location

New MDX files under `cognithor-site/content/docs/packs/`:

```
content/docs/packs/
  getting-started.mdx       # section: "packs", order: 0
  pack-structure.mdx         # section: "packs", order: 1
  tools-and-sources.mdx      # section: "packs", order: 2
  testing-and-publishing.mdx # section: "packs", order: 3
```

### Schema Change

`cognithor-site/lib/content/schemas.ts` line 131: Add `'packs'` to the `DocSection` enum:

```typescript
export const DocSection = z.enum(['getting-started', 'architecture', 'guides', 'packs', 'reference']);
```

### Page Contents

#### getting-started.mdx
- What is a Pack (agent extension, tools + lead sources, marketplace-ready)
- Prerequisites: Python 3.12+, `pip install cognithor-sdk`
- Quickstart: `cognithor pack create --name my-pack --namespace my-namespace`
- "Hello World" pack: register one MCP tool, install locally, test it
- Full working code example (~30 lines)

#### pack-structure.mdx
- Directory layout diagram (pack_manifest.json, pack.py, eula.md, src/, tests/, catalog/)
- `pack_manifest.json` field reference (all fields with types, required/optional, examples)
  - schema_version, namespace, pack_id, version, display_name, description
  - license (apache-2.0 | proprietary), min/max_cognithor_version
  - entrypoint, eula_sha256, publisher, revenue_share
  - lead_sources, tools (informational arrays)
  - pricing (indie/commercial tiers)
- pack.py lifecycle: `__init__(manifest)` → `register(context)` → `unregister(context)`
- PackContext API: gateway, config, mcp_client, leads
- EULA requirements: file must exist, SHA-256 must match manifest, user accepts on install
- Version constraints: semver, min/max with operators (>=, <=, ==)

#### tools-and-sources.mdx
- Registering MCP tools via `context.mcp_client.register_builtin_handler()`
  - name, handler (async def), description, input_schema (JSON Schema), risk_level
  - Gatekeeper classification: where to put new tools (green/yellow/orange)
  - Full handler example with error handling
- Implementing a LeadSource
  - ABC: source_id, display_name, icon, color, capabilities
  - Required: `async scan(config, product, product_description, min_score) -> list[Lead]`
  - Optional: draft_reply, refine_reply, post_reply (check capabilities)
  - Lead model fields
  - Registration via `context.leads.register_source()`
- REST route registration (advanced, via `context.gateway._api`)

#### testing-and-publishing.mdx
- Local testing: `cognithor pack install ./my-pack/` → run cognithor → test tools
- Writing unit tests: mock PackContext, mock MCP client
- Debugging: `cognithor --log-level debug` to see pack loading
- Pre-publish checklist: manifest valid, EULA hash matches, version bumped
- Marketplace submission (Q4 2026 preview): push to cognithor-packs repo, CI validates, catalog.mdx required

## Deliverable 2: `cognithor pack create` CLI

### New Files

- `src/cognithor/packs/scaffolder.py` (~120 lines) — template generation logic
- Modify `src/cognithor/packs/cli.py` — add `create` subcommand

### CLI Interface

Interactive mode:
```
$ cognithor pack create
Pack name: my-weather-tools
Namespace [cognithor-community]: acme-corp
Description: Weather forecast tools for Cognithor
Include Lead Source? [y/N]: n
License (apache-2.0/proprietary) [apache-2.0]: apache-2.0

Creating pack at ~/.cognithor/packs/acme-corp/my-weather-tools/ ...

  pack_manifest.json    ✓
  pack.py               ✓
  eula.md               ✓
  src/__init__.py        ✓
  tests/test_pack.py     ✓
  catalog/catalog.mdx    ✓

Done! Next steps:
  1. Edit src/ to add your tools
  2. Wire them in pack.py register()
  3. Test: cognithor pack install ./
```

Non-interactive: `cognithor pack create --name my-pack --namespace acme --description "..." --with-leads --license proprietary --output ./my-pack`

### Scaffolder Output

Generated `pack_manifest.json`:
```json
{
  "schema_version": 1,
  "namespace": "<namespace>",
  "pack_id": "<name>",
  "version": "0.1.0",
  "display_name": "<Name Title Case>",
  "description": "<description>",
  "license": "<license>",
  "min_cognithor_version": ">=0.92.0",
  "entrypoint": "pack.py",
  "eula_sha256": "<computed from generated eula.md>",
  "publisher": {
    "id": "<namespace>",
    "display_name": "<Namespace Title Case>",
    "url": ""
  },
  "lead_sources": [],
  "tools": []
}
```

Generated `pack.py` (tools-only variant):
```python
from cognithor.packs.interface import AgentPack, PackContext


class Pack(AgentPack):
    def register(self, context: PackContext) -> None:
        if context.mcp_client is None:
            return

        async def hello(name: str = "World") -> str:
            return f"Hello, {name}!"

        context.mcp_client.register_builtin_handler(
            "<pack_id>_hello",
            hello,
            description="Say hello",
            input_schema={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Who to greet"},
                },
            },
        )

    def unregister(self, context: PackContext) -> None:
        pass
```

Generated `pack.py` (with-leads variant):
```python
from cognithor.packs.interface import AgentPack, PackContext
from src.my_source import MyLeadSource


class Pack(AgentPack):
    _source: MyLeadSource | None = None

    def register(self, context: PackContext) -> None:
        if context.leads:
            self._source = MyLeadSource()
            context.leads.register_source(self._source)

    def unregister(self, context: PackContext) -> None:
        if context.leads and self._source:
            context.leads.unregister_source(self._source.source_id)
```

Plus a generated `src/my_source.py` stub implementing `LeadSource` with `scan()` returning an empty list.

Generated `eula.md`: Standard Apache 2.0 or proprietary template text.

Generated `tests/test_pack.py`:
```python
from unittest.mock import MagicMock
from pack import Pack
from cognithor.packs.interface import PackManifest, PackContext


def test_register_does_not_crash():
    manifest = PackManifest(
        namespace="test", pack_id="test", version="0.1.0",
        display_name="Test", description="Test pack",
        eula_sha256="0" * 64,
    )
    pack = Pack(manifest)
    ctx = PackContext(mcp_client=MagicMock())
    pack.register(ctx)
```

## Deliverable 3: cognithor-sdk PyPI Package

### Location

New directory in the cognithor repo: `sdk/`

```
sdk/
  pyproject.toml
  src/cognithor_sdk/
    __init__.py           # re-exports everything
    interface.py          # AgentPack, PackManifest, PackContext, Publisher, PricingTier
    leads.py              # LeadSource, Lead, LeadStatus
    py.typed              # PEP 561 marker
```

### pyproject.toml

```toml
[project]
name = "cognithor-sdk"
version = "0.92.1"
description = "Type stubs and interfaces for building Cognithor agent packs"
requires-python = ">=3.12"
license = "Apache-2.0"
dependencies = ["pydantic>=2.0"]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/cognithor_sdk"]
```

### Interface Strategy

The SDK contains **copies** of the interface classes from cognithor core, not re-exports. This allows developers to `pip install cognithor-sdk` without installing the full cognithor package (which has ~50 dependencies). The classes are structurally identical — a Pack built against `cognithor-sdk` works with `cognithor` at runtime because Python uses duck typing.

The SDK exports:
- `AgentPack` — abstract base class with `register(context)` and `unregister(context)`
- `PackManifest` — Pydantic model with all manifest fields
- `PackContext` — facade with gateway, config, mcp_client, leads attributes
- `Publisher`, `RevenueShare`, `PricingTier` — manifest sub-models
- `LeadSource` — abstract base class with `scan()` and optional methods
- `Lead`, `LeadStatus` — lead data model

Version synced with cognithor main version. Publish to PyPI alongside cognithor releases.

## Changes Summary

| Repo | Files | Action |
|------|-------|--------|
| cognithor-site | `lib/content/schemas.ts` | Add `'packs'` to DocSection enum |
| cognithor-site | `content/docs/packs/*.mdx` (4 files) | Create developer guide pages |
| cognithor | `src/cognithor/packs/scaffolder.py` | Create: template generation |
| cognithor | `src/cognithor/packs/cli.py` | Modify: add `create` subcommand |
| cognithor | `sdk/` (new directory, 5 files) | Create: cognithor-sdk package |

## Out of Scope

- PyPI publishing automation (manual for Phase 1)
- Marketplace submission workflow (Q4 2026)
- Pack signing / publisher verification (exists in community skills, not yet for packs)
- GUI pack builder in Flutter
- Pack update/versioning CLI (already has `cognithor pack update` stub)
