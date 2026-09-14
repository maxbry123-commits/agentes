from __future__ import annotations

import json
from typing import TYPE_CHECKING

from cognithor.packs.cli import main

if TYPE_CHECKING:
    from pathlib import Path


class TestPackCreate:
    def test_create_non_interactive(self, tmp_path: Path) -> None:
        output = tmp_path / "output"
        exit_code = main(
            [
                "create",
                "--name",
                "test-pack",
                "--namespace",
                "dev",
                "--description",
                "A test pack",
                "--output",
                str(output),
            ]
        )
        assert exit_code == 0
        pack_dir = output / "dev" / "test-pack"
        assert (pack_dir / "pack_manifest.json").exists()
        assert (pack_dir / "pack.py").exists()

    def test_create_with_leads(self, tmp_path: Path) -> None:
        output = tmp_path / "output"
        exit_code = main(
            [
                "create",
                "--name",
                "lead-pack",
                "--namespace",
                "dev",
                "--description",
                "Lead pack",
                "--with-leads",
                "--output",
                str(output),
            ]
        )
        assert exit_code == 0
        pack_dir = output / "dev" / "lead-pack"
        assert (pack_dir / "src" / "my_source.py").exists()

    def test_create_proprietary(self, tmp_path: Path) -> None:
        output = tmp_path / "output"
        exit_code = main(
            [
                "create",
                "--name",
                "paid-pack",
                "--namespace",
                "dev",
                "--description",
                "Paid",
                "--license",
                "proprietary",
                "--output",
                str(output),
            ]
        )
        assert exit_code == 0
        manifest = json.loads((output / "dev" / "paid-pack" / "pack_manifest.json").read_text())
        assert manifest["license"] == "proprietary"
