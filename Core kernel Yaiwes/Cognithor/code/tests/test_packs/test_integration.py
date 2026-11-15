"""End-to-end integration test for the pack system.

Exercises: CLI install → on-disk layout → PackLoader discovery → PackLoader load → register() runs.
"""

from __future__ import annotations

import hashlib
import json
import zipfile
from typing import TYPE_CHECKING

from cognithor.packs.cli import main as pack_main
from cognithor.packs.interface import PackContext
from cognithor.packs.loader import PackLoader

if TYPE_CHECKING:
    from pathlib import Path

    import pytest


def _build_pack_zip(tmp_path: Path, pack_id: str = "e2e") -> Path:
    eula = "EULA e2e"
    eula_hash = hashlib.sha256(eula.encode("utf-8")).hexdigest()
    manifest = {
        "schema_version": 1,
        "namespace": "cognithor-official",
        "pack_id": pack_id,
        "version": "1.0.0",
        "display_name": "E2E",
        "description": "integration test",
        "license": "apache-2.0",
        "min_cognithor_version": ">=0.1.0",
        "eula_sha256": eula_hash,
        "publisher": {"id": "cognithor-official", "display_name": "Cognithor"},
    }
    body = (
        "from cognithor.packs.interface import AgentPack, PackContext\n\n"
        "class Pack(AgentPack):\n"
        "    def register(self, ctx: PackContext) -> None:\n"
        "        ctx.gateway = 'touched'\n"
    )
    zip_path = tmp_path / f"{pack_id}.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("pack_manifest.json", json.dumps(manifest))
        zf.writestr("eula.md", eula)
        zf.writestr("pack.py", body)
    return zip_path


def test_install_and_load_end_to_end(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    packs_root = tmp_path / "packs"
    zip_path = _build_pack_zip(tmp_path)

    monkeypatch.setenv("COGNITHOR_PACKS_DIR", str(packs_root))
    monkeypatch.setattr("builtins.input", lambda _prompt="": "y")

    rc = pack_main(["install", str(zip_path)])
    assert rc == 0

    loader = PackLoader(packs_dir=packs_root, cognithor_version="0.92.0")
    ctx = PackContext()
    loader.load_all(ctx)

    pack = loader.get("cognithor-official/e2e")
    assert pack is not None
    assert pack.manifest.version == "1.0.0"
    assert ctx.gateway == "touched"  # register() ran and set the sentinel
