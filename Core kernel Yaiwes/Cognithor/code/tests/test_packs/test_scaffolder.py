from __future__ import annotations

import json
from typing import TYPE_CHECKING

from cognithor.packs.scaffolder import scaffold_pack

if TYPE_CHECKING:
    from pathlib import Path


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
        eula_text = (result / "eula.md").read_text(encoding="utf-8")
        actual_hash = hashlib.sha256(eula_text.encode("utf-8")).hexdigest()
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
        assert "MyLeadSource" in pack_py

    def test_display_name_is_title_case(self, tmp_path: Path) -> None:
        result = scaffold_pack(
            output_dir=tmp_path,
            name="my-cool-pack",
            namespace="dev",
            description="Test",
        )
        manifest = json.loads((result / "pack_manifest.json").read_text())
        assert manifest["display_name"] == "My Cool Pack"
