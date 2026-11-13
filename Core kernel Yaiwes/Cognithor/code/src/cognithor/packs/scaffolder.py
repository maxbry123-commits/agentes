"""Pack scaffolder — generates a new pack directory from templates."""

from __future__ import annotations

import hashlib
import json
from typing import TYPE_CHECKING

if TYPE_CHECKING:
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
        publisher={"id": "test", "display_name": "Test"},
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

    eula_text = _EULA_PROPRIETARY if license_type == "proprietary" else _EULA_APACHE
    (pack_dir / "eula.md").write_text(eula_text, encoding="utf-8")
    eula_hash = hashlib.sha256(eula_text.encode("utf-8")).hexdigest()

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

    if with_leads:
        pack_py = _PACK_PY_LEADS.format(pack_id=name)
    else:
        pack_py = _PACK_PY_TOOLS.format(pack_id=name)
    (pack_dir / "pack.py").write_text(pack_py, encoding="utf-8")

    src_dir = pack_dir / "src"
    src_dir.mkdir(exist_ok=True)
    (src_dir / "__init__.py").write_text("", encoding="utf-8")

    if with_leads:
        source_stub = _LEAD_SOURCE_STUB.format(source_id=name, display_name=display_name)
        (src_dir / "my_source.py").write_text(source_stub, encoding="utf-8")

    tests_dir = pack_dir / "tests"
    tests_dir.mkdir(exist_ok=True)
    (tests_dir / "test_pack.py").write_text(_TEST_PACK, encoding="utf-8")

    catalog_dir = pack_dir / "catalog"
    catalog_dir.mkdir(exist_ok=True)
    catalog_mdx = _CATALOG_MDX.format(display_name=display_name, description=description)
    (catalog_dir / "catalog.mdx").write_text(catalog_mdx, encoding="utf-8")

    return pack_dir
