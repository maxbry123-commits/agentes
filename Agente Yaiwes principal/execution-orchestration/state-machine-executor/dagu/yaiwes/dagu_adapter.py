"""YAIWES Dagu adapter: execute one real local two-step DAG through the moved Dagu binary."""
import json
import os
import shlex
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

PLUGIN_ID = "yaiwes.orchestration.dagu"

def descriptor() -> dict[str, str]:
    return {"plugin_id": PLUGIN_ID, "role": "dag_workflow_orchestration", "microtest": "real_two_step_dependency_dag"}

def run_microtest(repo_root: str | Path, dagu_binary: str | Path) -> dict[str, Any]:
    root=Path(repo_root).resolve()
    target=root / "Agente Yaiwes principal/execution-orchestration/state-machine-executor/dagu"
    if not (target / "go.mod").is_file():
        raise RuntimeError(f"DAGU_TARGET_MISSING:{target}")
    binary=Path(dagu_binary).resolve()
    if not binary.is_file():
        raise RuntimeError(f"DAGU_BINARY_MISSING:{binary}")
    with tempfile.TemporaryDirectory(prefix="yaiwes-dagu-") as td_s:
        td=Path(td_s)
        order=td / "order.txt"
        workflow=td / "yaiwes-n21.yaml"
        q=shlex.quote(str(order))
        workflow.write_text(
            "steps:\n"
            "  - id: first\n"
            "    name: first\n"
            f"    run: echo first > {q}\n"
            "  - id: second\n"
            "    name: second\n"
            "    depends: first\n"
            f"    run: echo second >> {q}\n",
            encoding="utf-8")
        env=os.environ.copy()
        home=td / "home"; home.mkdir()
        env.update({"HOME":str(home),"XDG_CONFIG_HOME":str(td/"config"),"XDG_DATA_HOME":str(td/"data"),"XDG_CACHE_HOME":str(td/"cache")})
        proc=subprocess.run([str(binary),"start",str(workflow)],cwd=td,env=env,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=120)
        output=proc.stdout[-12000:]
        if proc.returncode != 0:
            raise RuntimeError(f"DAGU_START_FAILED:{proc.returncode}:{output}")
        if not order.is_file():
            raise RuntimeError(f"DAGU_ORDER_FILE_MISSING:{output}")
        lines=order.read_text(encoding="utf-8").splitlines()
        if lines != ["first","second"]:
            raise RuntimeError(f"DAGU_DEPENDENCY_BAD:{lines}:{output}")
        return {"status":"PASS","capability":"real_two_step_dependency_dag","order":lines,"returncode":proc.returncode}

if __name__ == "__main__":
    result=run_microtest(sys.argv[1],sys.argv[2])
    print("YAIWES_DAGU_RESULT="+json.dumps(result,separators=(",",":")))
