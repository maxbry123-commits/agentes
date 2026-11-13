# YAIWES gVisor adapter: execute a real runsc ptrace sandbox in CI.
import json
import subprocess
import sys
from pathlib import Path
from typing import Any
PLUGIN_ID = "yaiwes.isolation.gvisor"
def descriptor() -> dict[str, str]:
    return {"plugin_id": PLUGIN_ID, "role": "container_pod_isolation", "microtest": "runsc_do_privileged_ci_ptrace"}
def run_microtest(runsc_binary: str | Path) -> dict[str, Any]:
    binary=Path(runsc_binary).resolve()
    if not binary.is_file(): raise RuntimeError(f"RUNSC_BINARY_MISSING:{binary}")
    host_dir=str(binary.parent)
    cmd=[
        "docker","run","--rm","--privileged","--pid=host",
        "--security-opt","seccomp=unconfined","--security-opt","apparmor=unconfined",
        "-v",host_dir+":/gvisor:ro",
        "ubuntu:24.04",
        "/gvisor/runsc",
        "--root=/tmp/yaiwes-runsc-state",
        "--platform=ptrace",
        "--network=none",
        "--ignore-cgroups=true",
        "--directfs=false",
        "--host-settings=ignore",
        "--sidecar-usage-policy=LEGACY_DEPRECATED_SLOW_EMBEDDED_FALLBACK",
        "do","--quiet","/bin/sh","-c","printf 41",
    ]
    proc=subprocess.run(cmd,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=240)
    stdout=proc.stdout
    stderr=proc.stderr
    if proc.returncode != 0:
        raise RuntimeError(f"RUNSC_DO_FAILED:{proc.returncode}:stdout={stdout[-4000:]}:stderr={stderr[-8000:]}")
    value=stdout.strip()
    if value != "41":
        raise RuntimeError(f"RUNSC_SANDBOX_OUTPUT_BAD:{value!r}:stderr={stderr[-8000:]}")
    return {"status":"PASS","capability":"runsc_do_privileged_ci_ptrace","value":41,"returncode":proc.returncode,"network":"none","platform":"ptrace","rootless":False,"ci_outer_container_privileged":True}
if __name__ == "__main__":
    result=run_microtest(sys.argv[1]); print("YAIWES_GVISOR_RESULT="+json.dumps(result,separators=(",",":")))
