"""YAIWES Hatchet STEP3 adapter: real embedded DAG execution through the canonical plugin bus."""
from __future__ import annotations

import asyncio
import json
import sys
import threading
import time
from pathlib import Path
from typing import Any

from pydantic import BaseModel

PLUGIN_ID = "yaiwes.orchestration.hatchet"
ROLE = "durable_task_orchestration"
SDK_RELATIVE = "Agente Yaiwes principal/execution-orchestration/state-machine-executor/hatchet/sdks/python"


class MicroInput(BaseModel):
    value: int


def descriptor() -> dict[str, str]:
    return {
        "plugin_id": PLUGIN_ID,
        "role": ROLE,
        "sdk_path": SDK_RELATIVE,
        "microtest": "embedded_two_task_dag",
    }


def run_microtest(repo_root: str | Path) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    sdk = root / SDK_RELATIVE
    if not (sdk / "hatchet_sdk").is_dir():
        raise RuntimeError(f"HATCHET_SDK_MISSING:{sdk}")
    if str(sdk) not in sys.path:
        sys.path.insert(0, str(sdk))

    from hatchet_sdk import Hatchet

    hatchet = Hatchet.from_embedded()
    workflow = hatchet.workflow(
        name="YAIWESHatchetN22Micro",
        input_validator=MicroInput,
    )

    @workflow.task(name="double")
    def double(input: MicroInput, ctx) -> dict[str, int]:
        return {"value": input.value * 2}

    @workflow.task(name="plus_one", parents=[double])
    def plus_one(input: MicroInput, ctx) -> dict[str, int]:
        parent = ctx.task_output(double)
        return {"value": parent["value"] + 1}

    worker = hatchet.worker("yaiwes-n22-micro-worker", workflows=[workflow])
    thread = threading.Thread(target=worker.start, daemon=True)
    thread.start()

    try:
        deadline = time.time() + 30
        while time.time() < deadline:
            if getattr(worker.status, "name", "") == "HEALTHY":
                break
            time.sleep(0.25)
        else:
            raise RuntimeError(f"HATCHET_WORKER_NOT_HEALTHY:{worker.status}")

        result = workflow.run(MicroInput(value=20))
        expected = {"double": {"value": 40}, "plus_one": {"value": 41}}
        if result.get("double") != expected["double"]:
            raise RuntimeError(f"HATCHET_DOUBLE_BAD:{result}")
        if result.get("plus_one") != expected["plus_one"]:
            raise RuntimeError(f"HATCHET_DAG_BAD:{result}")
        return {
            "status": "PASS",
            "capability": "embedded_two_task_dag",
            "result": result,
        }
    finally:
        loop = worker.loop
        if loop is not None and loop.is_running():
            fut = asyncio.run_coroutine_threadsafe(worker.exit_gracefully(), loop)
            try:
                fut.result(timeout=20)
            except Exception:
                pass
        hatchet.stop_embedded()


def main() -> int:
    if len(sys.argv) != 2:
        raise SystemExit("usage: hatchet_adapter.py <repo_root>")
    result = run_microtest(sys.argv[1])
    print("YAIWES_HATCHET_RESULT=" + json.dumps(result, separators=(",", ":")), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
