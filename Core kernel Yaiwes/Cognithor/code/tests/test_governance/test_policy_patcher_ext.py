"""Extended tests for PolicyPatcher -- missing lines coverage."""

from __future__ import annotations

from typing import TYPE_CHECKING

import yaml

from cognithor.governance.policy_patcher import PolicyPatcher
from cognithor.models import PolicyChange

if TYPE_CHECKING:
    from pathlib import Path


class TestMergeChange:
    def test_merge_adds_changes_list(self) -> None:
        data: dict = {}
        result = PolicyPatcher._merge_change(data, {"action": "add_rule"})
        assert "changes" in result
        assert len(result["changes"]) == 1

    def test_merge_preserves_existing_changes(self) -> None:
        data: dict = {"changes": [{"action": "old"}]}
        result = PolicyPatcher._merge_change(data, {"action": "new"})
        assert len(result["changes"]) == 2

    def test_merge_promotes_action(self) -> None:
        data: dict = {}
        result = PolicyPatcher._merge_change(data, {"action": "restrict"})
        assert result["last_action"] == "restrict"

    def test_merge_no_action_key(self) -> None:
        data: dict = {}
        result = PolicyPatcher._merge_change(data, {"tool": "exec"})
        assert "last_action" not in result


class TestRollbackEdgeCases:
    def test_rollback_empty_stack(self, tmp_path: Path) -> None:
        patcher = PolicyPatcher(str(tmp_path / "policies"))
        assert patcher.rollback_last() is False

    def test_rollback_missing_backup_file(self, tmp_path: Path) -> None:
        pol_dir = tmp_path / "policies"
        pol_dir.mkdir()
        patcher = PolicyPatcher(str(pol_dir))
        # Push a fake backup path that doesn't exist
        patcher._backup_stack.append(str(pol_dir / "nonexistent.yaml.bak"))
        assert patcher.rollback_last() is False

    def test_rollback_new_category_deletes_file(self, tmp_path: Path) -> None:
        """Rolling back a new category should delete the file since it didn't exist before."""
        pol_dir = tmp_path / "policies"
        pol_dir.mkdir()
        patcher = PolicyPatcher(str(pol_dir))

        change = PolicyChange(
            proposal_id=1,
            category="newcat",
            title="New rule",
            change={"action": "add_rule"},
        )
        patcher.apply_change(change)
        assert (pol_dir / "newcat.yaml").exists()

        # Rollback should restore "no file" state
        result = patcher.rollback_last()
        assert result is True
        assert not (pol_dir / "newcat.yaml").exists()

    def test_rollback_with_timestamp_parsing(self, tmp_path: Path) -> None:
        """Test the timestamp-based filename parsing in rollback."""
        pol_dir = tmp_path / "policies"
        pol_dir.mkdir()

        # Create a policy file
        policy_file = pol_dir / "security.yaml"
        policy_file.write_text(yaml.dump({"rules": []}), encoding="utf-8")

        patcher = PolicyPatcher(str(pol_dir))
        change = PolicyChange(
            proposal_id=2,
            category="security",
            title="Add rule",
            change={"action": "add_rule"},
        )
        patcher.apply_change(change)

        # Now rollback
        assert patcher.rollback_last() is True
        # File should be restored to original content
        content = yaml.safe_load(policy_file.read_text(encoding="utf-8"))
        assert content == {"rules": []}


class TestApplyChangeEdgeCases:
    def test_apply_change_empty_dict(self, tmp_path: Path) -> None:
        pol_dir = tmp_path / "policies"
        pol_dir.mkdir()
        patcher = PolicyPatcher(str(pol_dir))

        change = PolicyChange(
            proposal_id=1,
            category="test",
            title="Empty change",
            change={},
        )
        result = patcher.apply_change(change)
        assert result is True

    def test_list_backups_nonexistent_dir(self, tmp_path: Path) -> None:
        patcher = PolicyPatcher(str(tmp_path / "nonexistent" / "dir"))
        assert patcher.list_backups() == []
