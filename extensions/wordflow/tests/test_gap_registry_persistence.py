from pathlib import Path

from extensions.wordflow.standards.gap_registry import Gap, GapRegistry


def test_gap_registry_persists_across_instances(tmp_path: Path):
    store = tmp_path / "gaps.json"
    first = GapRegistry(str(store))
    first.add(
        Gap(
            gap_id="G-PERSIST-001",
            task_id="T04",
            mission_id="m1",
            rule_id="PERSISTENCE",
            severity="blocking",
            description="persistence check",
        )
    )
    first.transition("G-PERSIST-001", "FIXED", evidence="fix", revision="r1")
    second = GapRegistry(str(store))
    gaps = {item["gap_id"]: item for item in second.to_list()}
    assert gaps["G-PERSIST-001"]["status"] == "FIXED"
    assert gaps["G-PERSIST-001"]["fixed_revision"] == "r1"
