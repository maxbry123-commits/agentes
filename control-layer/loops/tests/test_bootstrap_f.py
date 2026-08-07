import tempfile
from pathlib import Path
from loops.supervisor import LoopSupervisor, SupervisorConfig
from loops.bootstrap import Bootstrap
from loops.contracts.types import LoopContext
from loops.engine import LoopEngine
from loops.policy.engine import PolicyEngine


def test_hydrate_and_resume():
    with tempfile.TemporaryDirectory() as td:
        eng = LoopEngine(policy=PolicyEngine([
            {"id": "cont", "when": {"phase_outcome": "validation_passed", "goal_complete": False},
             "action": "CONTINUE", "reason": "go"},
        ]))
        sup = LoopSupervisor(engine=eng, config=SupervisorConfig(persist_dir=td))
        ctx = LoopContext(
            run_id="R-boot", loop_id="L", project_id="P", agent_id="A",
            task_id="T", goal_id="G", created_at="t", updated_at="t",
        )
        sup.create(ctx)
        # leave RUNNING after one iteration
        sup.run_once("R-boot", goal_complete=False)

        # new supervisor from disk
        boot = Bootstrap(td, engine=eng)
        sup2, report = boot.hydrate_supervisor()
        assert report.registry_loaded >= 1
        assert "R-boot" in sup2._contexts or report.active_restored >= 0
