# Pack SDK & Developer Documentation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Enable external developers to build Cognithor packs with a developer guide, CLI scaffolding, and typed SDK package.

**Architecture:** Three independent deliverables: (1) MDX docs pages on cognithor.ai with a new "packs" DocSection, (2) a `cognithor pack create` CLI command backed by a scaffolder module, (3) a minimal `cognithor-sdk` PyPI package re-exporting pack interfaces.

**Tech Stack:** MDX / next-intl (docs), Python / argparse (CLI), Python / Pydantic / hatchling (SDK)

---

## File Map

| File | Action | Responsibility |
|------|--------|---------------|
| `cognithor-site/lib/content/schemas.ts` | Modify | Add `'packs'` to DocSection enum |
| `cognithor-site/content/docs/packs/getting-started.mdx` | Create | Quickstart guide |
| `cognithor-site/content/docs/packs/pack-structure.mdx` | Create | Manifest + lifecycle reference |
| `cognithor-site/content/docs/packs/tools-and-sources.mdx` | Create | MCP tools + LeadSource guide |
| `cognithor-site/content/docs/packs/testing-and-publishing.mdx` | Create | Testing + publishing workflow |
| `src/cognithor/packs/scaffolder.py` | Create | Template generation logic |
| `src/cognithor/packs/cli.py` | Modify | Add `create` subcommand |
| `tests/test_packs/test_scaffolder.py` | Create | Scaffolder unit tests |
| `sdk/pyproject.toml` | Create | SDK package metadata |
| `sdk/src/cognithor_sdk/__init__.py` | Create | Public re-exports |
| `sdk/src/cognithor_sdk/interface.py` | Create | Pack interface copies |
| `sdk/src/cognithor_sdk/leads.py` | Create | Lead interface copies |
| `sdk/src/cognithor_sdk/py.typed` | Create | PEP 561 marker |

---

### Task 1: Add "packs" DocSection to cognithor-site

**Files:**
- Modify: `D:\Jarvis\cognithor-site\lib\content\schemas.ts:131`

- [ ] **Step 1: Update DocSection enum**

In `D:\Jarvis\cognithor-site\lib\content\schemas.ts`, change line 131 from:

```typescript
export const DocSection = z.enum(['getting-started', 'architecture', 'guides', 'reference']);
```

To:

```typescript
export const DocSection = z.enum(['getting-started', 'architecture', 'guides', 'packs', 'reference']);
```

- [ ] **Step 2: Verify build**

Run:
```bash
cd "D:/Jarvis/cognithor-site"
npx tsc --noEmit
```
Expected: No errors.

- [ ] **Step 3: Commit**

```bash
cd "D:/Jarvis/cognithor-site"
git add lib/content/schemas.ts
git commit -m "feat(docs): add 'packs' to DocSection enum"
```

---

### Task 2: Getting Started docs page

**Files:**
- Create: `D:\Jarvis\cognithor-site\content\docs\packs\getting-started.mdx`

- [ ] **Step 1: Create the directory and file**

```bash
mkdir -p "D:/Jarvis/cognithor-site/content/docs/packs"
```

Write `D:\Jarvis\cognithor-site\content\docs\packs\getting-started.mdx`:

```mdx
---
slug: packs/getting-started
title: Building Your First Pack
description: Create a Cognithor agent pack from scratch in under five minutes. Install the SDK, scaffold a project, register a tool, and test it locally.
section: packs
order: 0
---

A **pack** is an agent extension — a self-contained module that adds new MCP tools, lead sources, or REST endpoints to Cognithor. Packs are installed as directories with a manifest, an entry point, and a EULA. They can be free (Apache 2.0) or paid (proprietary, sold via the marketplace).

## Prerequisites

- Python 3.12+
- Cognithor installed and running (`cognithor --version`)
- The SDK for type hints: `pip install cognithor-sdk`

## Scaffold a new pack

```bash
cognithor pack create --name my-weather --namespace my-namespace
```

This creates a ready-to-run pack at `~/.cognithor/packs/my-namespace/my-weather/` with a hello-world tool already wired.

## Project layout

```
my-namespace/my-weather/
  pack_manifest.json    # metadata, version, EULA hash
  pack.py               # entry point — register() wires your tools
  eula.md               # license text (SHA-256 pinned in manifest)
  src/                   # your implementation code
  tests/                 # unit tests
  catalog/               # marketing content for the marketplace
```

## Your first tool

Open `pack.py` — the scaffolder already created a hello-world tool:

```python
from cognithor.packs.interface import AgentPack, PackContext


class Pack(AgentPack):
    def register(self, context: PackContext) -> None:
        if context.mcp_client is None:
            return

        async def hello(name: str = "World") -> str:
            return f"Hello, {name}!"

        context.mcp_client.register_builtin_handler(
            "my_weather_hello",
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

## Install and test locally

```bash
cognithor pack install ~/.cognithor/packs/my-namespace/my-weather/
cognithor
```

Then ask the agent: _"Use the my_weather_hello tool to greet Alice."_ — you should see the tool execute in the PGE loop.

## Next steps

- [Pack Structure](/docs/packs/pack-structure) — manifest reference, lifecycle, EULA
- [Tools & Sources](/docs/packs/tools-and-sources) — register MCP tools and lead sources
- [Testing & Publishing](/docs/packs/testing-and-publishing) — unit tests, debugging, marketplace
```

- [ ] **Step 2: Verify content validation**

```bash
cd "D:/Jarvis/cognithor-site"
pnpm validate-content
```
Expected: No errors for the new file.

- [ ] **Step 3: Commit**

```bash
cd "D:/Jarvis/cognithor-site"
git add content/docs/packs/getting-started.mdx
git commit -m "docs(packs): add Getting Started guide"
```

---

### Task 3: Pack Structure docs page

**Files:**
- Create: `D:\Jarvis\cognithor-site\content\docs\packs\pack-structure.mdx`

- [ ] **Step 1: Write pack-structure.mdx**

Write `D:\Jarvis\cognithor-site\content\docs\packs\pack-structure.mdx`:

```mdx
---
slug: packs/pack-structure
title: Pack Structure Reference
description: Complete reference for Cognithor pack layout, pack_manifest.json fields, pack.py lifecycle, EULA requirements, and version constraints.
section: packs
order: 1
---

## Directory layout

Every installed pack lives at `~/.cognithor/packs/<namespace>/<pack_id>/`:

```
<namespace>/<pack_id>/
  pack_manifest.json      # required — validated by the loader
  pack.py                 # required — entry point (or custom via entrypoint field)
  eula.md                 # required — SHA-256 pinned in manifest
  .eula_accepted          # auto-created when user accepts EULA
  src/                    # your implementation code
  tests/                  # unit tests
  catalog/
    catalog.mdx           # marketplace listing content
```

## pack_manifest.json

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `schema_version` | `int` | yes | Always `1` |
| `namespace` | `string` | yes | Publisher namespace, lowercase, 1-64 chars (`a-z0-9-`) |
| `pack_id` | `string` | yes | Pack identifier, same format as namespace |
| `version` | `string` | yes | Semver: `X.Y.Z` (e.g. `1.0.0`) |
| `display_name` | `string` | yes | Human-friendly name |
| `description` | `string` | yes | One-paragraph description |
| `license` | `string` | yes | `"apache-2.0"` or `"proprietary"` |
| `min_cognithor_version` | `string` | yes | Version constraint (e.g. `">=0.92.0"`) |
| `max_cognithor_version` | `string` | no | Upper bound (e.g. `"<=2.0.0"`) |
| `entrypoint` | `string` | no | Default: `"pack.py"` |
| `eula_sha256` | `string` | yes | SHA-256 hex digest of `eula.md` |
| `publisher` | `object` | yes | `{ id, display_name, website?, contact_email? }` |
| `revenue_share` | `object` | no | Default: `{ creator: 70, platform: 30 }` |
| `lead_sources` | `string[]` | no | Declared source IDs (informational) |
| `tools` | `string[]` | no | Declared tool names (informational) |
| `checkout_url` | `string` | no | Lemon Squeezy / Stripe checkout link |
| `pricing` | `object` | conditional | Required when `license` is `"proprietary"` |

### Pricing tiers

```json
"pricing": {
  "indie": {
    "list_price": 129,
    "launch_price": 75,
    "post_launch_price": 89,
    "launch_cap": 50,
    "currency": "EUR"
  }
}
```

## pack.py lifecycle

Your `pack.py` must export a class named `Pack` (case-sensitive) extending `AgentPack`:

```python
from cognithor.packs.interface import AgentPack, PackContext

class Pack(AgentPack):
    def register(self, context: PackContext) -> None:
        # Called once at startup. Wire tools, sources, routes here.
        pass

    def unregister(self, context: PackContext) -> None:
        # Optional cleanup on shutdown.
        pass
```

### PackContext

The `context` parameter gives you access to Cognithor internals:

| Attribute | Type | Usage |
|-----------|------|-------|
| `context.mcp_client` | `JarvisMCPClient` | Register MCP tools |
| `context.leads` | `LeadService` | Register lead sources |
| `context.config` | `JarvisConfig` | Read configuration |
| `context.gateway` | `Gateway` | Advanced: register REST routes |

All attributes may be `None` — always check before use.

## EULA

Every pack must include an `eula.md` file. The SHA-256 hash of this file must match the `eula_sha256` field in the manifest. Users accept the EULA on first install.

Compute the hash:
```bash
python -c "import hashlib, pathlib; print(hashlib.sha256(pathlib.Path('eula.md').read_bytes()).hexdigest())"
```

## Version constraints

The `min_cognithor_version` field supports operators: `>=`, `>`, `<=`, `<`, `==`.

Example: `">=0.92.0"` means your pack requires Cognithor 0.92.0 or newer.
```

- [ ] **Step 2: Verify**

```bash
cd "D:/Jarvis/cognithor-site"
pnpm validate-content
```

- [ ] **Step 3: Commit**

```bash
cd "D:/Jarvis/cognithor-site"
git add content/docs/packs/pack-structure.mdx
git commit -m "docs(packs): add Pack Structure reference"
```

---

### Task 4: Tools & Sources docs page

**Files:**
- Create: `D:\Jarvis\cognithor-site\content\docs\packs\tools-and-sources.mdx`

- [ ] **Step 1: Write tools-and-sources.mdx**

Write `D:\Jarvis\cognithor-site\content\docs\packs\tools-and-sources.mdx`:

```mdx
---
slug: packs/tools-and-sources
title: Registering Tools and Lead Sources
description: How to register MCP tools with input schemas and risk levels, and implement LeadSource subclasses for the multi-channel lead hunting system.
section: packs
order: 2
---

## MCP tools

Register tools in your `pack.py` via `context.mcp_client.register_builtin_handler()`:

```python
def register(self, context: PackContext) -> None:
    if context.mcp_client is None:
        return

    async def weather_forecast(city: str, days: int = 3) -> str:
        import json
        # Your implementation here
        return json.dumps({"city": city, "forecast": "sunny", "days": days})

    context.mcp_client.register_builtin_handler(
        "weather_forecast",
        weather_forecast,
        description="Get weather forecast for a city",
        input_schema={
            "type": "object",
            "properties": {
                "city": {"type": "string", "description": "City name"},
                "days": {"type": "integer", "description": "Forecast days (1-7)", "default": 3},
            },
            "required": ["city"],
        },
        risk_level="green",
    )
```

### Handler requirements

- Must be `async def`
- Return a JSON-serializable string
- Parameters must match the `input_schema` properties
- Handle errors gracefully — return error info as JSON, don't crash

### Risk levels

The Gatekeeper classifies every tool call. Set `risk_level` to control the default:

| Level | Behavior | Use for |
|-------|----------|---------|
| `"green"` | Auto-execute | Read-only, no side effects |
| `"yellow"` | Execute + inform user | Local writes, safe mutations |
| `"orange"` | User must approve | Network calls, deletions, external APIs |
| `"red"` | Blocked by default | Destructive, irreversible |

If you omit `risk_level`, unknown tools default to **orange** (user approval required).

## Lead sources

Implement a `LeadSource` subclass to add a new channel to the lead hunting system.

### Required class variables

```python
from cognithor.leads.source import LeadSource
from cognithor.leads.models import Lead

class MySource(LeadSource):
    source_id = "my-platform"
    display_name = "My Platform"
    icon = "forum"           # Material icon name
    color = "#FF6B35"        # Hex color for UI
    capabilities = frozenset({"scan"})
```

### Required method: scan()

```python
    async def scan(
        self,
        *,
        config: dict,
        product: str,
        product_description: str,
        min_score: int,
    ) -> list[Lead]:
        # Fetch posts from your platform
        posts = await self._fetch_posts(config)

        # Score each post with the local LLM
        leads = []
        for post in posts:
            score = await self._score(post, product, product_description)
            if score >= min_score:
                leads.append(Lead(
                    post_id=f"my-platform-{post['id']}",
                    source_id=self.source_id,
                    title=post["title"],
                    url=post["url"],
                    intent_score=score,
                    body=post.get("body", ""),
                    author=post.get("author", ""),
                ))
        return leads
```

### Optional methods

Add capabilities to enable these:

| Capability | Method | Signature |
|------------|--------|-----------|
| `"draft_reply"` | `draft_reply(lead, *, tone)` | Returns reply text |
| `"refine_reply"` | `refine_reply(lead, draft)` | Returns refined text |
| `"auto_post"` | `post_reply(lead, text)` | Posts to platform |

### Registration

```python
def register(self, context: PackContext) -> None:
    if context.leads:
        self._source = MySource()
        context.leads.register_source(self._source)

def unregister(self, context: PackContext) -> None:
    if context.leads and self._source:
        context.leads.unregister_source(self._source.source_id)
```
```

- [ ] **Step 2: Verify and commit**

```bash
cd "D:/Jarvis/cognithor-site"
pnpm validate-content
git add content/docs/packs/tools-and-sources.mdx
git commit -m "docs(packs): add Tools and Sources guide"
```

---

### Task 5: Testing & Publishing docs page

**Files:**
- Create: `D:\Jarvis\cognithor-site\content\docs\packs\testing-and-publishing.mdx`

- [ ] **Step 1: Write testing-and-publishing.mdx**

Write `D:\Jarvis\cognithor-site\content\docs\packs\testing-and-publishing.mdx`:

```mdx
---
slug: packs/testing-and-publishing
title: Testing and Publishing Packs
description: How to test Cognithor packs locally, write unit tests with mocked contexts, debug loading issues, and prepare for marketplace submission.
section: packs
order: 3
---

## Local testing

Install your pack directly from its directory:

```bash
cognithor pack install ./my-pack/
```

Then start Cognithor and test your tools:

```bash
cognithor --log-level debug
```

The `--log-level debug` flag shows pack loading, tool registration, and any errors.

## Unit tests

Write tests that mock the `PackContext` to verify your pack registers correctly:

```python
from unittest.mock import MagicMock
from pack import Pack
from cognithor.packs.interface import PackManifest, PackContext


def test_register_creates_tools():
    manifest = PackManifest(
        namespace="test", pack_id="test", version="0.1.0",
        display_name="Test", description="Test pack",
        eula_sha256="0" * 64,
        license="apache-2.0", min_cognithor_version=">=0.92.0",
        publisher={"id": "test", "display_name": "Test"},
    )
    mcp = MagicMock()
    ctx = PackContext(mcp_client=mcp)

    pack = Pack(manifest)
    pack.register(ctx)

    mcp.register_builtin_handler.assert_called_once()
    call_args = mcp.register_builtin_handler.call_args
    assert call_args[0][0] == "my_tool_name"  # first positional arg is tool name
```

Run tests from your pack directory:

```bash
cd my-pack/
python -m pytest tests/ -v
```

## Debugging

| Symptom | Likely cause | Fix |
|---------|-------------|-----|
| Pack not loaded | EULA not accepted | `cognithor pack accept-eula namespace/pack-id` |
| Pack not loaded | Version mismatch | Check `min_cognithor_version` in manifest |
| Tool not found | `register()` not wiring tool | Add `register_builtin_handler()` call |
| Import error | `sys.path` missing `src/` | Add `sys.path.insert(0, str(Path(__file__).parent / "src"))` in `pack.py` |

## Pre-publish checklist

Before submitting your pack:

- [ ] `pack_manifest.json` is valid (run `cognithor pack install ./` to check)
- [ ] `eula_sha256` matches `eula.md` (re-compute after any edit)
- [ ] Version bumped from previous release
- [ ] `tools` and `lead_sources` arrays list all registered names
- [ ] Unit tests pass
- [ ] `catalog/catalog.mdx` written with description, screenshots, use cases

## Marketplace submission (Q4 2026)

The Cognithor creator marketplace launches in Q4 2026. To submit:

1. Push your pack to the `cognithor-packs` repository
2. CI validates manifest, EULA hash, and runs tests
3. Review team checks `catalog/catalog.mdx` content
4. Pack goes live on cognithor.ai/packs

Revenue split: 70% creator / 30% platform (configurable in `revenue_share`).
```

- [ ] **Step 2: Verify and commit**

```bash
cd "D:/Jarvis/cognithor-site"
pnpm validate-content
git add content/docs/packs/testing-and-publishing.mdx
git commit -m "docs(packs): add Testing and Publishing guide"
```

---

### Task 6: Pack Scaffolder module

**Files:**
- Create: `D:\Jarvis\jarvis complete v20\src\cognithor\packs\scaffolder.py`
- Test: `D:\Jarvis\jarvis complete v20\tests\test_packs\test_scaffolder.py`

- [ ] **Step 1: Write the test**

Create `D:\Jarvis\jarvis complete v20\tests\test_packs\test_scaffolder.py`:

```python
from __future__ import annotations

import json
from pathlib import Path

import pytest

from cognithor.packs.scaffolder import scaffold_pack


class TestScaffoldPack:
    def test_creates_all_files(self, tmp_path: Path) -> None:
        result = scaffold_pack(
            output_dir=tmp_path,
            name="my-weather",
            namespace="acme",
            description="Weather tools",
            with_leads=False,
            license_type="apache-2.0",
        )
        assert result.exists()
        assert (result / "pack_manifest.json").exists()
        assert (result / "pack.py").exists()
        assert (result / "eula.md").exists()
        assert (result / "src" / "__init__.py").exists()
        assert (result / "tests" / "test_pack.py").exists()
        assert (result / "catalog" / "catalog.mdx").exists()

    def test_manifest_is_valid_json(self, tmp_path: Path) -> None:
        result = scaffold_pack(
            output_dir=tmp_path,
            name="test-pack",
            namespace="dev",
            description="Test",
        )
        manifest = json.loads((result / "pack_manifest.json").read_text())
        assert manifest["namespace"] == "dev"
        assert manifest["pack_id"] == "test-pack"
        assert manifest["version"] == "0.1.0"
        assert manifest["license"] == "apache-2.0"

    def test_eula_hash_matches_manifest(self, tmp_path: Path) -> None:
        import hashlib

        result = scaffold_pack(
            output_dir=tmp_path,
            name="hash-test",
            namespace="dev",
            description="Hash test",
        )
        eula_bytes = (result / "eula.md").read_bytes()
        actual_hash = hashlib.sha256(eula_bytes).hexdigest()
        manifest = json.loads((result / "pack_manifest.json").read_text())
        assert manifest["eula_sha256"] == actual_hash

    def test_with_leads_creates_source_stub(self, tmp_path: Path) -> None:
        result = scaffold_pack(
            output_dir=tmp_path,
            name="lead-pack",
            namespace="dev",
            description="Lead test",
            with_leads=True,
        )
        assert (result / "src" / "my_source.py").exists()
        pack_py = (result / "pack.py").read_text()
        assert "LeadSource" in pack_py or "MyLeadSource" in pack_py

    def test_display_name_is_title_case(self, tmp_path: Path) -> None:
        result = scaffold_pack(
            output_dir=tmp_path,
            name="my-cool-pack",
            namespace="dev",
            description="Test",
        )
        manifest = json.loads((result / "pack_manifest.json").read_text())
        assert manifest["display_name"] == "My Cool Pack"
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd "D:/Jarvis/jarvis complete v20"
python -m pytest tests/test_packs/test_scaffolder.py -v
```
Expected: `ModuleNotFoundError: No module named 'cognithor.packs.scaffolder'`

- [ ] **Step 3: Write scaffolder.py**

Create `D:\Jarvis\jarvis complete v20\src\cognithor\packs\scaffolder.py`:

```python
"""Pack scaffolder — generates a new pack directory from templates."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

_EULA_APACHE = """\
# End User License Agreement

This agent pack is licensed under the Apache License, Version 2.0.
You may obtain a copy of the License at:
https://www.apache.org/licenses/LICENSE-2.0

By installing this pack you agree to the terms of the Apache 2.0 license.
"""

_EULA_PROPRIETARY = """\
# End User License Agreement

This agent pack is proprietary software. By installing it you agree to
the following terms:

1. You receive a personal, non-transferable license to use this pack.
2. You may not redistribute, sublicense, or reverse-engineer this pack.
3. The author provides no warranty. Use at your own risk.
4. Refund policy: 14 days from purchase date.
"""

_PACK_PY_TOOLS = """\
from cognithor.packs.interface import AgentPack, PackContext


class Pack(AgentPack):
    def register(self, context: PackContext) -> None:
        if context.mcp_client is None:
            return

        async def hello(name: str = "World") -> str:
            return f"Hello, {{name}}!"

        context.mcp_client.register_builtin_handler(
            "{pack_id}_hello",
            hello,
            description="Say hello",
            input_schema={{
                "type": "object",
                "properties": {{
                    "name": {{"type": "string", "description": "Who to greet"}},
                }},
            }},
        )

    def unregister(self, context: PackContext) -> None:
        pass
"""

_PACK_PY_LEADS = """\
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from cognithor.packs.interface import AgentPack, PackContext
from my_source import MyLeadSource


class Pack(AgentPack):
    _source: MyLeadSource | None = None

    def register(self, context: PackContext) -> None:
        if context.leads:
            self._source = MyLeadSource()
            context.leads.register_source(self._source)

    def unregister(self, context: PackContext) -> None:
        if context.leads and self._source:
            context.leads.unregister_source(self._source.source_id)
"""

_LEAD_SOURCE_STUB = """\
from __future__ import annotations

from typing import Any, ClassVar

from cognithor.leads.models import Lead
from cognithor.leads.source import LeadSource


class MyLeadSource(LeadSource):
    source_id: ClassVar[str] = "{source_id}"
    display_name: ClassVar[str] = "{display_name}"
    icon: ClassVar[str] = "search"
    color: ClassVar[str] = "#6366F1"
    capabilities: ClassVar[frozenset[str]] = frozenset({{"scan"}})

    async def scan(
        self,
        *,
        config: dict[str, Any],
        product: str,
        product_description: str,
        min_score: int,
    ) -> list[Lead]:
        # TODO: implement your scanning logic
        return []
"""

_TEST_PACK = """\
from unittest.mock import MagicMock

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from pack import Pack
from cognithor.packs.interface import PackManifest, PackContext


def test_register_does_not_crash():
    manifest = PackManifest(
        namespace="test", pack_id="test", version="0.1.0",
        display_name="Test", description="Test pack",
        eula_sha256="0" * 64,
        license="apache-2.0", min_cognithor_version=">=0.92.0",
        publisher={{"id": "test", "display_name": "Test"}},
    )
    pack = Pack(manifest)
    ctx = PackContext(mcp_client=MagicMock())
    pack.register(ctx)
"""

_CATALOG_MDX = """\
---
title: {display_name}
description: {description}
---

# {display_name}

{description}

## Features

- Feature 1
- Feature 2

## Installation

```bash
cognithor pack install <path-or-url>
```
"""


def scaffold_pack(
    *,
    output_dir: Path,
    name: str,
    namespace: str,
    description: str,
    with_leads: bool = False,
    license_type: str = "apache-2.0",
) -> Path:
    """Generate a new pack directory with all required files.

    Returns the path to the created pack directory.
    """
    display_name = name.replace("-", " ").title()
    pack_dir = output_dir / namespace / name
    pack_dir.mkdir(parents=True, exist_ok=True)

    # eula.md
    eula_text = _EULA_PROPRIETARY if license_type == "proprietary" else _EULA_APACHE
    (pack_dir / "eula.md").write_text(eula_text, encoding="utf-8")
    eula_hash = hashlib.sha256(eula_text.encode("utf-8")).hexdigest()

    # pack_manifest.json
    manifest = {
        "schema_version": 1,
        "namespace": namespace,
        "pack_id": name,
        "version": "0.1.0",
        "display_name": display_name,
        "description": description,
        "license": license_type,
        "min_cognithor_version": ">=0.92.0",
        "entrypoint": "pack.py",
        "eula_sha256": eula_hash,
        "publisher": {
            "id": namespace,
            "display_name": namespace.replace("-", " ").title(),
        },
        "lead_sources": [],
        "tools": [],
    }
    (pack_dir / "pack_manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    # pack.py
    if with_leads:
        pack_py = _PACK_PY_LEADS.format(pack_id=name)
    else:
        pack_py = _PACK_PY_TOOLS.format(pack_id=name)
    (pack_dir / "pack.py").write_text(pack_py, encoding="utf-8")

    # src/
    src_dir = pack_dir / "src"
    src_dir.mkdir(exist_ok=True)
    (src_dir / "__init__.py").write_text("", encoding="utf-8")

    if with_leads:
        source_stub = _LEAD_SOURCE_STUB.format(
            source_id=name,
            display_name=display_name,
        )
        (src_dir / "my_source.py").write_text(source_stub, encoding="utf-8")

    # tests/
    tests_dir = pack_dir / "tests"
    tests_dir.mkdir(exist_ok=True)
    (tests_dir / "test_pack.py").write_text(_TEST_PACK, encoding="utf-8")

    # catalog/
    catalog_dir = pack_dir / "catalog"
    catalog_dir.mkdir(exist_ok=True)
    catalog_mdx = _CATALOG_MDX.format(
        display_name=display_name,
        description=description,
    )
    (catalog_dir / "catalog.mdx").write_text(catalog_mdx, encoding="utf-8")

    return pack_dir
```

- [ ] **Step 4: Run tests**

```bash
cd "D:/Jarvis/jarvis complete v20"
python -m pytest tests/test_packs/test_scaffolder.py -v
```
Expected: 5 passed.

- [ ] **Step 5: Commit**

```bash
cd "D:/Jarvis/jarvis complete v20"
git add src/cognithor/packs/scaffolder.py tests/test_packs/test_scaffolder.py
git commit -m "feat(packs): add scaffolder module with template generation"
```

---

### Task 7: Wire `cognithor pack create` CLI command

**Files:**
- Modify: `D:\Jarvis\jarvis complete v20\src\cognithor\packs\cli.py`
- Test: `D:\Jarvis\jarvis complete v20\tests\test_packs\test_cli_create.py`

- [ ] **Step 1: Write the test**

Create `D:\Jarvis\jarvis complete v20\tests\test_packs\test_cli_create.py`:

```python
from __future__ import annotations

import json
from pathlib import Path

import pytest

from cognithor.packs.cli import main


class TestPackCreate:
    def test_create_non_interactive(self, tmp_path: Path) -> None:
        output = tmp_path / "output"
        exit_code = main([
            "create",
            "--name", "test-pack",
            "--namespace", "dev",
            "--description", "A test pack",
            "--output", str(output),
        ])
        assert exit_code == 0
        pack_dir = output / "dev" / "test-pack"
        assert (pack_dir / "pack_manifest.json").exists()
        assert (pack_dir / "pack.py").exists()

    def test_create_with_leads(self, tmp_path: Path) -> None:
        output = tmp_path / "output"
        exit_code = main([
            "create",
            "--name", "lead-pack",
            "--namespace", "dev",
            "--description", "Lead pack",
            "--with-leads",
            "--output", str(output),
        ])
        assert exit_code == 0
        pack_dir = output / "dev" / "lead-pack"
        assert (pack_dir / "src" / "my_source.py").exists()

    def test_create_proprietary(self, tmp_path: Path) -> None:
        output = tmp_path / "output"
        exit_code = main([
            "create",
            "--name", "paid-pack",
            "--namespace", "dev",
            "--description", "Paid",
            "--license", "proprietary",
            "--output", str(output),
        ])
        assert exit_code == 0
        manifest = json.loads(
            (output / "dev" / "paid-pack" / "pack_manifest.json").read_text()
        )
        assert manifest["license"] == "proprietary"
```

- [ ] **Step 2: Run test to verify it fails**

```bash
python -m pytest tests/test_packs/test_cli_create.py -v
```
Expected: FAIL (no `create` subcommand).

- [ ] **Step 3: Add create subcommand to cli.py**

Add the handler function before `build_parser()` in `D:\Jarvis\jarvis complete v20\src\cognithor\packs\cli.py`:

```python
def _cmd_create(args: argparse.Namespace) -> int:
    from cognithor.packs.scaffolder import scaffold_pack

    output = Path(args.output) if args.output else _resolve_packs_root()
    try:
        pack_dir = scaffold_pack(
            output_dir=output,
            name=args.name,
            namespace=args.namespace,
            description=args.description or f"{args.name} pack for Cognithor",
            with_leads=args.with_leads,
            license_type=args.license,
        )
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print(f"\n[OK] Created pack at {pack_dir}/\n")
    print("  pack_manifest.json    [OK]")
    print("  pack.py               [OK]")
    print("  eula.md               [OK]")
    print("  src/__init__.py       [OK]")
    print("  tests/test_pack.py    [OK]")
    print("  catalog/catalog.mdx   [OK]")
    print(f"\nNext steps:")
    print(f"  1. Edit src/ to add your tools")
    print(f"  2. Wire them in pack.py register()")
    print(f"  3. Test: cognithor pack install {pack_dir}")
    return 0
```

Add the subparser inside `build_parser()`, after the `accept-eula` block:

```python
    # create
    p_create = sub.add_parser("create", help="Scaffold a new pack from template.")
    p_create.add_argument("--name", required=True, help="Pack identifier (lowercase, e.g. my-pack)")
    p_create.add_argument("--namespace", default="cognithor-community", help="Publisher namespace")
    p_create.add_argument("--description", default="", help="Pack description")
    p_create.add_argument("--with-leads", action="store_true", help="Include LeadSource stub")
    p_create.add_argument("--license", default="apache-2.0", choices=["apache-2.0", "proprietary"], help="License type")
    p_create.add_argument("--output", default="", help="Output directory (default: packs root)")
    p_create.set_defaults(func=_cmd_create)
```

- [ ] **Step 4: Run tests**

```bash
python -m pytest tests/test_packs/test_cli_create.py tests/test_packs/test_scaffolder.py -v
```
Expected: 8 passed.

- [ ] **Step 5: Format and commit**

```bash
cd "D:/Jarvis/jarvis complete v20"
ruff format src/cognithor/packs/cli.py tests/test_packs/test_cli_create.py
git add src/cognithor/packs/cli.py tests/test_packs/test_cli_create.py
git commit -m "feat(packs): add 'cognithor pack create' scaffolding command"
```

---

### Task 8: cognithor-sdk PyPI package

**Files:**
- Create: `D:\Jarvis\jarvis complete v20\sdk\pyproject.toml`
- Create: `D:\Jarvis\jarvis complete v20\sdk\src\cognithor_sdk\__init__.py`
- Create: `D:\Jarvis\jarvis complete v20\sdk\src\cognithor_sdk\interface.py`
- Create: `D:\Jarvis\jarvis complete v20\sdk\src\cognithor_sdk\leads.py`
- Create: `D:\Jarvis\jarvis complete v20\sdk\src\cognithor_sdk\py.typed`

- [ ] **Step 1: Create directory structure**

```bash
mkdir -p "D:/Jarvis/jarvis complete v20/sdk/src/cognithor_sdk"
```

- [ ] **Step 2: Create pyproject.toml**

Write `D:\Jarvis\jarvis complete v20\sdk\pyproject.toml`:

```toml
[project]
name = "cognithor-sdk"
version = "0.92.1"
description = "Type stubs and interfaces for building Cognithor agent packs"
readme = "README.md"
requires-python = ">=3.12"
license = "Apache-2.0"
authors = [{ name = "Alexander Soellner" }]
dependencies = ["pydantic>=2.0,<3"]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/cognithor_sdk"]
```

- [ ] **Step 3: Create interface.py**

Copy the interface classes from `src/cognithor/packs/interface.py` into `D:\Jarvis\jarvis complete v20\sdk\src\cognithor_sdk\interface.py`:

```python
"""Pack interfaces — the stable contract between packs and Cognithor Core.

This module is a standalone copy of cognithor.packs.interface.
Packs developed against cognithor-sdk are fully compatible with cognithor
at runtime via structural (duck) typing.
"""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

_SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+(?:[-+][0-9A-Za-z\.-]+)?$")
_NS_PACK_RE = re.compile(r"^[a-z][a-z0-9-]{0,63}$")
_SHA256_RE = re.compile(r"^[a-f0-9]{64}$")


class Publisher(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    display_name: str
    website: str | None = None
    contact_email: str | None = None
    payout_provider: str | None = None


class RevenueShare(BaseModel):
    model_config = ConfigDict(extra="forbid")
    creator: int = Field(default=70, ge=0, le=100)
    platform: int = Field(default=30, ge=0, le=100)

    @model_validator(mode="after")
    def _sum_to_100(self) -> RevenueShare:
        if self.creator + self.platform != 100:
            raise ValueError("creator + platform must sum to 100")
        return self


class PricingTier(BaseModel):
    model_config = ConfigDict(extra="forbid")
    list_price: int = Field(ge=0)
    launch_price: int = Field(ge=0)
    post_launch_price: int = Field(ge=0)
    launch_cap: int = Field(ge=1)
    currency: str = "USD"


class PackManifest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schema_version: int = 1
    namespace: str
    pack_id: str
    version: str
    display_name: str
    description: str
    license: str
    min_cognithor_version: str
    max_cognithor_version: str | None = None
    entrypoint: str = "pack.py"
    eula_sha256: str
    publisher: Publisher
    revenue_share: RevenueShare = Field(default_factory=RevenueShare)
    lead_sources: list[str] = Field(default_factory=list)
    tools: list[str] = Field(default_factory=list)
    checkout_url: str | None = None
    commercial_checkout_url: str | None = None
    pricing: dict[str, PricingTier] = Field(default_factory=dict)

    @field_validator("namespace")
    @classmethod
    def _validate_namespace(cls, v: str) -> str:
        if "/" in v or not _NS_PACK_RE.match(v):
            raise ValueError(f"namespace must match {_NS_PACK_RE.pattern!r}")
        return v

    @field_validator("pack_id")
    @classmethod
    def _validate_pack_id(cls, v: str) -> str:
        if "/" in v or not _NS_PACK_RE.match(v):
            raise ValueError(f"pack_id must match {_NS_PACK_RE.pattern!r}")
        return v

    @field_validator("version")
    @classmethod
    def _validate_version(cls, v: str) -> str:
        if not _SEMVER_RE.match(v):
            raise ValueError(f"version must be semver X.Y.Z, got {v!r}")
        return v

    @field_validator("eula_sha256")
    @classmethod
    def _validate_eula_hash(cls, v: str) -> str:
        if not _SHA256_RE.match(v):
            raise ValueError("eula_sha256 must be 64 lowercase hex chars")
        return v

    @property
    def qualified_id(self) -> str:
        return f"{self.namespace}/{self.pack_id}"


class PackContext(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    gateway: Any = None
    config: Any = None
    mcp_client: Any = None
    leads: Any = None


class AgentPack(ABC):
    def __init__(self, manifest: PackManifest) -> None:
        self.manifest = manifest

    @abstractmethod
    def register(self, context: PackContext) -> None: ...

    def unregister(self, context: PackContext) -> None:
        pass
```

- [ ] **Step 4: Create leads.py**

Write `D:\Jarvis\jarvis complete v20\sdk\src\cognithor_sdk\leads.py`:

```python
"""Lead source interfaces — standalone copy of cognithor.leads."""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, ClassVar


class LeadStatus(str, Enum):
    NEW = "new"
    REVIEWED = "reviewed"
    REPLIED = "replied"
    ARCHIVED = "archived"


@dataclass
class Lead:
    post_id: str
    source_id: str
    title: str
    url: str
    intent_score: int
    body: str = ""
    author: str = ""
    created_utc: float = 0.0
    score_reason: str = ""
    reply_draft: str = ""
    status: LeadStatus = LeadStatus.NEW
    scan_id: str = ""
    received_at: float = field(default_factory=time.time)
    subreddit: str = ""
    upvotes: int = 0
    num_comments: int = 0


class LeadSource(ABC):
    source_id: ClassVar[str]
    display_name: ClassVar[str]
    icon: ClassVar[str]
    color: ClassVar[str]
    capabilities: ClassVar[frozenset[str]]

    @abstractmethod
    async def scan(
        self,
        *,
        config: dict[str, Any],
        product: str,
        product_description: str,
        min_score: int,
    ) -> list[Lead]: ...

    async def draft_reply(self, lead: Lead, *, tone: str) -> str:
        raise NotImplementedError

    async def refine_reply(self, lead: Lead, draft: str) -> str:
        raise NotImplementedError

    async def post_reply(self, lead: Lead, text: str) -> None:
        raise NotImplementedError
```

- [ ] **Step 5: Create __init__.py**

Write `D:\Jarvis\jarvis complete v20\sdk\src\cognithor_sdk\__init__.py`:

```python
"""Cognithor SDK — type stubs and interfaces for building agent packs.

Usage:
    pip install cognithor-sdk

    from cognithor_sdk import AgentPack, PackContext, PackManifest
    from cognithor_sdk import LeadSource, Lead, LeadStatus
"""

from cognithor_sdk.interface import (
    AgentPack,
    PackContext,
    PackManifest,
    PricingTier,
    Publisher,
    RevenueShare,
)
from cognithor_sdk.leads import Lead, LeadSource, LeadStatus

__all__ = [
    "AgentPack",
    "Lead",
    "LeadSource",
    "LeadStatus",
    "PackContext",
    "PackManifest",
    "PricingTier",
    "Publisher",
    "RevenueShare",
]
```

- [ ] **Step 6: Create py.typed marker**

```bash
touch "D:/Jarvis/jarvis complete v20/sdk/src/cognithor_sdk/py.typed"
```

- [ ] **Step 7: Verify the SDK builds**

```bash
cd "D:/Jarvis/jarvis complete v20/sdk"
pip install -e . 2>&1
python -c "from cognithor_sdk import AgentPack, PackManifest, LeadSource, Lead; print('SDK imports OK')"
```
Expected: `SDK imports OK`

- [ ] **Step 8: Commit**

```bash
cd "D:/Jarvis/jarvis complete v20"
git add sdk/
git commit -m "feat(sdk): add cognithor-sdk package with typed pack interfaces"
```

---

### Task 9: Final verification + push

- [ ] **Step 1: Run all pack tests**

```bash
cd "D:/Jarvis/jarvis complete v20"
python -m pytest tests/test_packs/ -v
```
Expected: all tests pass.

- [ ] **Step 2: Verify site builds**

```bash
cd "D:/Jarvis/cognithor-site"
pnpm validate-content
pnpm typecheck
```
Expected: no errors.

- [ ] **Step 3: Push both repos**

```bash
cd "D:/Jarvis/jarvis complete v20"
git push

cd "D:/Jarvis/cognithor-site"
git push
```

- [ ] **Step 4: Final commit message**

```bash
cd "D:/Jarvis/jarvis complete v20"
# If there are any remaining changes:
git add -A
git commit -m "feat(packs): Pack SDK Phase 1 complete — docs, CLI scaffolding, SDK package"
```
