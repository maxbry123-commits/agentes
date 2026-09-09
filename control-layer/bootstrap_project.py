"""Bootstrap proyecto → Adapter + LoopEngine + Supervisor · capa universal
SOURCE: W12 · sin binario obligatorio (stub/generic ok)
"""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from loops.engine import LoopEngine
from loops.phase_handlers import make_default_handlers
from loops.runtime_factory import build_adapter_from_project
from loops.supervisor import LoopSupervisor, SupervisorConfig
from loops.contracts.types import LoopContext
from skills.validate_schemas import validate_project_dir


@dataclass
class ProjectControl:
    root: Path
    adapter: Any
    engine: LoopEngine
    supervisor: LoopSupervisor
    validation: dict[str, Any]


def bootstrap(project_root: str | Path, *, persist_dir: str | None = None) -> ProjectControl:
    root = Path(project_root).resolve()
    validation = validate_project_dir(root)
    adapter = build_adapter_from_project(root, stub_ok=True)
    engine = LoopEngine(phase_handlers=make_default_handlers(adapter))
    pdir = persist_dir or str(root / "loop_data")
    sup = LoopSupervisor(engine=engine, config=SupervisorConfig(persist_dir=pdir))
    return ProjectControl(root=root, adapter=adapter, engine=engine, supervisor=sup, validation=validation)


def run_once_demo(ctrl: ProjectControl, *, capability: str = "code_generation") -> Any:
    """Una iteración demo (stub ok)."""
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc).isoformat()
    ctx = LoopContext(
        run_id="R-demo",
        loop_id="L-demo",
        project_id=ctrl.root.name,
        agent_id="demo",
        task_id="T-demo",
        goal_id="G-demo",
        created_at=now,
        updated_at=now,
        inputs={"capability": capability},
        strategy="sequential",
    )
    ctrl.supervisor.create(ctx)
    return ctrl.supervisor.run_once(
        "R-demo",
        goal_complete=True,
        phase_context={"capability": capability, "strategy": "sequential"},
    )


if __name__ == "__main__":
    import json
    import sys
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
    ctrl = bootstrap(root)
    print(json.dumps({"validation": ctrl.validation, "root": str(ctrl.root)}, indent=2))
