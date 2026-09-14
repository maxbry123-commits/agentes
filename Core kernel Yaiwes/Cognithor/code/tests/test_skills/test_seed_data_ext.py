"""Extended tests for skills/seed_data.py -- missing lines coverage.

Targets:
  - _parse_procedure_to_listing with various categories
  - Icon selection based on category
  - seed_marketplace with nonexistent dir
  - seed_marketplace with parse errors
  - Trigger keywords as string
  - Priority-based is_featured
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock

from cognithor.skills.seed_data import (
    _CATEGORY_MAP,
    _parse_procedure_to_listing,
    seed_marketplace,
)

if TYPE_CHECKING:
    from pathlib import Path


class TestParseToListing:
    def test_basic_procedure(self, tmp_path: Path) -> None:
        md = tmp_path / "test.md"
        md.write_text(
            "---\nname: Test Skill\ncategory: development\npriority: 3\n"
            "trigger_keywords: [test, dev]\n---\n\nA test skill description.\n",
            encoding="utf-8",
        )
        listing = _parse_procedure_to_listing(md)
        assert listing is not None
        assert listing["name"] == "Test Skill"
        assert listing["category"] == "entwicklung"
        assert listing["tags"] == ["test", "dev"]
        assert listing["is_featured"] is False  # priority < 5
        assert listing["icon"] == "\U0001f4bb"  # entwicklung icon

    def test_featured_high_priority(self, tmp_path: Path) -> None:
        md = tmp_path / "featured.md"
        md.write_text(
            "---\nname: Featured Skill\npriority: 7\ncategory: productivity\n---\n\nDescription.\n",
            encoding="utf-8",
        )
        listing = _parse_procedure_to_listing(md)
        assert listing is not None
        assert listing["is_featured"] is True
        assert listing["featured_reason"] == "Built-in Prozedur"

    def test_category_mapping(self, tmp_path: Path) -> None:
        for raw, mapped in _CATEGORY_MAP.items():
            md = tmp_path / f"{raw}.md"
            md.write_text(f"---\nname: {raw}\ncategory: {raw}\n---\nBody.", encoding="utf-8")
            listing = _parse_procedure_to_listing(md)
            assert listing is not None
            assert listing["category"] == mapped

    def test_unknown_category_passthrough(self, tmp_path: Path) -> None:
        md = tmp_path / "custom.md"
        md.write_text("---\nname: Custom\ncategory: custom_cat\n---\nBody.", encoding="utf-8")
        listing = _parse_procedure_to_listing(md)
        assert listing["category"] == "custom_cat"

    def test_trigger_keywords_as_string(self, tmp_path: Path) -> None:
        md = tmp_path / "triggers.md"
        md.write_text(
            "---\nname: Triggers\ntrigger_keywords: hello, world\n---\nBody.",
            encoding="utf-8",
        )
        listing = _parse_procedure_to_listing(md)
        assert listing["tags"] == ["hello", "world"]

    def test_no_frontmatter(self, tmp_path: Path) -> None:
        md = tmp_path / "plain.md"
        md.write_text("# Just a heading\n\nSome text here.", encoding="utf-8")
        listing = _parse_procedure_to_listing(md)
        assert listing is not None
        assert listing["name"] == "plain"

    def test_invalid_yaml_frontmatter(self, tmp_path: Path) -> None:
        md = tmp_path / "bad.md"
        md.write_text("---\n: [invalid yaml\n---\nBody.", encoding="utf-8")
        listing = _parse_procedure_to_listing(md)
        assert listing is None

    def test_empty_name(self, tmp_path: Path) -> None:
        md = tmp_path / "empty_name.md"
        md.write_text("---\nname: \n---\nBody.", encoding="utf-8")
        listing = _parse_procedure_to_listing(md)
        assert listing is None

    def test_description_from_body(self, tmp_path: Path) -> None:
        md = tmp_path / "desc.md"
        md.write_text(
            "---\nname: Desc Test\n---\n# Heading\n\nFirst line of body.\n",
            encoding="utf-8",
        )
        listing = _parse_procedure_to_listing(md)
        assert listing["description"] == "First line of body."

    def test_description_fallback_to_name(self, tmp_path: Path) -> None:
        md = tmp_path / "no_desc.md"
        md.write_text("---\nname: No Desc\n---\n# Only Heading\n", encoding="utf-8")
        listing = _parse_procedure_to_listing(md)
        assert listing["description"] == "No Desc"

    def test_icons_for_categories(self, tmp_path: Path) -> None:
        # Test a few icon assignments
        for cat, icon in [
            ("produktivitaet", "\u26a1"),
            ("daten", "\U0001f4ca"),
            ("sonstiges", "\U0001f4e6"),
        ]:
            md = tmp_path / f"icon_{cat}.md"
            md.write_text(f"---\nname: Icon {cat}\ncategory: {cat}\n---\nBody.", encoding="utf-8")
            listing = _parse_procedure_to_listing(md)
            assert listing["icon"] == icon


class TestSeedMarketplace:
    def test_nonexistent_dir(self, tmp_path: Path) -> None:
        store = MagicMock()
        count = seed_marketplace(store, tmp_path / "nonexistent")
        assert count == 0

    def test_seed_with_files(self, tmp_path: Path) -> None:
        proc_dir = tmp_path / "procedures"
        proc_dir.mkdir()
        for i in range(3):
            (proc_dir / f"skill{i}.md").write_text(
                f"---\nname: Skill {i}\ncategory: general\n---\nBody {i}.",
                encoding="utf-8",
            )

        store = MagicMock()
        count = seed_marketplace(store, proc_dir)
        assert count == 3
        assert store.save_listing.call_count == 3

    def test_seed_with_error_file(self, tmp_path: Path) -> None:
        proc_dir = tmp_path / "procedures"
        proc_dir.mkdir()
        (proc_dir / "good.md").write_text(
            "---\nname: Good\n---\nBody.",
            encoding="utf-8",
        )
        (proc_dir / "bad.md").write_text(
            "---\n: [invalid\n---\nBody.",
            encoding="utf-8",
        )

        store = MagicMock()
        count = seed_marketplace(store, proc_dir)
        # Only good.md should be saved
        assert count == 1
