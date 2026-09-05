import tempfile
from pathlib import Path
from loops.supervisor import LoopSupervisor, SupervisorConfig
from loops.contracts.types import LoopContext
from loops.engine import LoopEngine
from loops.policy.engine import PolicyEngine


def test_persist_and_metrics_default():
    with tempfile.TemporaryDirectory() as td:
        eng = LoopEngine(policy=PolicyEngine([
            {"id": "c", "when": {"phase_outcome": "validation_passed", "goal_complete": True},
             "action": "CLOSE", "reason": "ok"}
        ]))
        sup = LoopSupervisor(engine=eng, config=SupervisorConfig(persist_dir=td))
        ctx = LoopContext(
            run_id="R-c", loop_id="L", project_id="P", agent_id="A",
            task_id="T", goal_id="G", created_at="t", updated_at="t",
        )
        sup.create(ctx)
        r = sup.run_once("R-c", goal_complete=True)
        assert r.closed
        assert (Path(td) / "supervisor.jsonl").exists()
        assert (Path(td) / "registry.jsonl").exists()
        snap = sup.metrics_snapshot()
        assert snap["runs_total"] >= 1
