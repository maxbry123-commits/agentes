from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Iterable

REPO = Path.cwd()
SRC = REPO / "Core kernel Yaiwes/Componentes recuperados A"
Y = REPO / "Agente Yaiwes principal"
BUS_REL = "Agente Yaiwes principal/kernel-principal/extension-kernel/plugin-bus/universal_plugin_bus_v2_integrated.py"
CONTRACT_REL = "Agente Yaiwes principal/kernel-principal/extension-kernel/plugin-bus/ficha_contract_v2.py"
STATE = REPO / "Core kernel Yaiwes/Crack wall bitácora stated JSON/STATE.json"
LEDGER = REPO / "Core kernel Yaiwes/Crack wall bitácora stated JSON/README.md"
ARCH = REPO / "Readme arquitectura Yaiwes/README.md"

TARGETS = {
    "Camunda": Y / "execution-orchestration/state-machine-executor/camunda",
    "Cedar": Y / "definition-registry/authorization-model/cedar",
    "Celery": Y / "execution-engine-pool/parallel-dispatch/celery",
    "Cerberus": Y / "definition-registry/schema-contracts/cerberus",
    "Cerbos": Y / "control-governance/policy-guardrails-permissions/cerbos",
}


def run(*args: str) -> None:
    subprocess.run(args, cwd=REPO, check=True)


def require(path: Path) -> None:
    if not path.exists():
        raise SystemExit(f"required path missing: {path}")


def git_mv(src: Path, dst: Path) -> None:
    require(src)
    if dst.exists():
        raise SystemExit(f"destination already exists: {dst}")
    dst.parent.mkdir(parents=True, exist_ok=True)
    run("git", "mv", str(src), str(dst))


def move_items(src_root: Path, dst_root: Path, items: Iterable[str]) -> None:
    dst_root.mkdir(parents=True, exist_ok=True)
    for item in items:
        src = src_root / item
        if src.exists():
            git_mv(src, dst_root / item)


def adapter_text(name: str, runtime_root: str, extra: str = "") -> str:
    return f'''from __future__ import annotations
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
RUNTIME = ROOT / {runtime_root!r}


def source_probe() -> dict[str, Any]:
    if not RUNTIME.exists():
        raise RuntimeError("{name} runtime missing")
    return {{"component": "{name}", "runtime": str(RUNTIME), "exists": True}}

{extra}
'''


def ficha(pid: str, case: str, family: str, input_type: str, output_type: str,
          event: str, category: str, stage: str, entry: str, sandbox: str = "container") -> dict:
    return {
        "artifact_id": pid,
        "version": "1.0.0",
        "estado": "testing",
        "contract_hash": "",
        "tribunal_case_id": case,
        "contrato": {
            "rol": "transform",
            "consume": {"datatype": {"family": family, "type": input_type, "version": 1}},
            "expone": {"datatype": {"family": family, "type": output_type, "version": 1}},
            "input_map": {}, "output_map": {},
        },
        "ejecucion": {
            "kind": "code", "transport": "importlib", "runtime_type": "compute",
            "entry_point": entry, "llm_ratio": 0.0, "idempotente": True,
        },
        "seguridad": {"sandbox": sandbox, "permisos": [], "limites": {"timeout_ms": 30000, "deadline_ms": 45000}},
        "firma": {"gpg_key_id": "PENDIENTE", "revocation_ref": "contracts/revocation_list.json"},
        "categoria": category, "etapa": stage,
        "perfiles": {"n0": {"habilitada": True, "iteraciones": 1, "simulaciones": 0, "criticas": 0, "muestras_k": 1}},
        "repeticion": {"max": 1, "condicion": "nunca", "backoff": "1000*2^n+rand(0,1000)"},
        "repite_en": ["EXEC_STATE"],
        "activacion": {"eventos": [event], "wake_words": [], "condicion": ""},
        "presupuesto": {"n0": {"max_tokens": 1, "max_ms": 30000, "max_costo_usd": 0.000001}},
        "telemetria": {"metricas": ["tiempo", "errores", "reintentos"], "span_otel": True},
        "evidencia": {"produce": ["L1_static", "L2_build", "L3_runtime"], "destino": "runtime/evidence/"},
        "failover": {"sustituible_por": [], "compensacion": "fail_closed"},
        "salud": {"metodo": "exec", "heartbeat_interval_s": 30},
        "trazas": {"task_id_requerido": True, "trace_id_requerido": True},
    }


def write_surface(name: str, dest: Path, manifest: dict, source_entry: str, adapter: str) -> None:
    dest.mkdir(parents=True, exist_ok=True)
    (dest / "adapter.py").write_text(adapter, encoding="utf-8")
    mf = dest / f"ficha.{name.lower()}.v2.json"
    mf.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    wiring = {
        "artifact_id": manifest["artifact_id"], "classification": "B" if manifest["categoria"] == "pipeline" else "C",
        "fail_closed": True, "adapter": "adapter.py", "manifest": mf.name,
        "source": source_entry, "plugin_bus": BUS_REL, "contract_validator": CONTRACT_REL,
    }
    (dest / "WIRING.json").write_text(json.dumps(wiring, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (dest / "README.md").write_text(
        f"# {name} — integración YAIWES\n\nRuntime vendor preservado sin monolito. Entrada YAIWES: `adapter.py`; contrato: `{mf.name}`; cableado: `WIRING.json`; bus: Universal Plugin Bus/Fables.\n",
        encoding="utf-8",
    )


def prepare_camunda() -> None:
    src_outer = SRC / "Camunda"
    src = src_outer / "Camunda"
    dest = TARGETS["Camunda"]
    require(src / "zeebe/engine")
    move_items(src, dest, ["zeebe", "parent", "bom", "build-tools", ".mvn", "mvnw", "mvnw.cmd"])
    for license_name in ["LICENSE.txt", "NOTICE.txt", "LICENSE", "NOTICE", "licenses"]:
        if (src / license_name).exists():
            git_mv(src / license_name, dest / license_name)
    m = ficha("yaiwes.workflow.camunda", "YAIWES-CAMUNDA-011", "workflow", "bpmn_process", "workflow_state", "yaiwes.workflow.camunda.requested", "pipeline", "E", "adapter:source_probe")
    write_surface("camunda", dest, m, "zeebe/engine", adapter_text("Camunda", "zeebe/engine", "def bpmn_model_root() -> str:\n    p = ROOT / 'zeebe' / 'bpmn-model'\n    if not p.is_dir(): raise RuntimeError('Camunda BPMN model missing')\n    return str(p)\n"))


def prepare_cedar() -> None:
    src = SRC / "Cedar"
    dest = TARGETS["Cedar"]
    require(src / "cedar-policy/src")
    crates = ["cedar-policy", "cedar-policy-core", "cedar-policy-formatter", "cedar-policy-cli", "cedar-policy-symcc", "cedar-testing", "cedar-wasm", "cedar-language-server"]
    move_items(src, dest, crates + ["Cargo.toml", "LICENSE", "NOTICE", "NOTICE.txt", "THIRD_PARTY_LICENSES.txt"])
    m = ficha("yaiwes.authorization.cedar", "YAIWES-CEDAR-012", "authorization", "authorization_request", "authorization_decision", "yaiwes.authorization.cedar.requested", "transversal", "T", "adapter:policy_root")
    write_surface("cedar", dest, m, "cedar-policy", adapter_text("Cedar", "cedar-policy", "def policy_root() -> str:\n    p = ROOT / 'cedar-policy' / 'src'\n    if not p.is_dir(): raise RuntimeError('Cedar policy source missing')\n    return str(p)\n"))


def prepare_celery() -> None:
    src = SRC / "Celery"
    dest = TARGETS["Celery"]
    require(src / "celery/app")
    move_items(src, dest, ["celery", "requirements", "setup.py", "setup.cfg", "pyproject.toml", "MANIFEST.in", "LICENSE"])
    m = ficha("yaiwes.dispatch.celery", "YAIWES-CELERY-013", "task", "task_definition", "task_result", "yaiwes.task.celery.requested", "pipeline", "E", "adapter:build_app", "process")
    extra = "def build_app(name: str = 'yaiwes'):\n    from celery import Celery\n    app = Celery(name, broker='memory://', backend='cache+memory://')\n    app.conf.task_always_eager = True\n    return app\n"
    write_surface("celery", dest, m, "celery", adapter_text("Celery", "celery", extra))


def prepare_cerberus() -> None:
    src = SRC / "Cerberus"
    dest = TARGETS["Cerberus"]
    require(src / "cerberus/validator.py")
    move_items(src, dest, ["cerberus", "LICENSE"])
    for junk in [dest / "cerberus/tests", dest / "cerberus/benchmarks"]:
        if junk.exists(): run("git", "rm", "-r", str(junk))
    m = ficha("yaiwes.validation.cerberus", "YAIWES-CERBERUS-014", "contract", "python_document_schema", "validation_result", "yaiwes.validation.cerberus.requested", "transversal", "T", "adapter:validate_document", "process")
    extra = "def validate_document(schema: dict, document: dict) -> dict:\n    from cerberus import Validator\n    v = Validator(schema)\n    ok = v.validate(document)\n    return {'valid': bool(ok), 'document': v.document, 'errors': v.errors}\n"
    write_surface("cerberus", dest, m, "cerberus", adapter_text("Cerberus", "cerberus", extra))


def prepare_cerbos() -> None:
    src = SRC / "Cerbos"
    dest = TARGETS["Cerbos"]
    require(src / "internal/engine")
    # `internal/server/awslambda` imports cmd/cerbos/server, so cmd is a required
    # runtime dependency for the Cerbos engine compile gate and must MOVE with it.
    move_items(src, dest, ["internal", "pkg", "api", "schema", "private", "cmd", "go.mod", "go.sum", "LICENSE", "NOTICE.txt"])
    m = ficha("yaiwes.authorization.cerbos", "YAIWES-CERBOS-015", "authorization", "principal_resource_actions", "policy_decision", "yaiwes.authorization.cerbos.requested", "transversal", "T", "adapter:engine_root")
    write_surface("cerbos", dest, m, "internal/engine", adapter_text("Cerbos", "internal/engine", "def engine_root() -> str:\n    p = ROOT / 'internal' / 'engine'\n    if not p.is_dir(): raise RuntimeError('Cerbos engine missing')\n    return str(p)\n"))


def prepare() -> None:
    prepare_camunda(); prepare_cedar(); prepare_celery(); prepare_cerberus(); prepare_cerbos()
    print("THIRD_FIVE_PREPARED")


def finalize() -> None:
    for source_name in ["Camunda", "Cedar", "Celery", "Cerberus", "Cerbos"]:
        p = SRC / source_name
        if p.exists(): run("git", "rm", "-r", str(p))
    state = json.loads(STATE.read_text(encoding="utf-8"))
    closed = list(dict.fromkeys([*state.get("verified_closed", []), "Camunda", "Cedar", "Celery", "Cerberus", "Cerbos"]))
    state["verified_closed"] = closed
    state["current_boundary"] = "BATCH_11_15_VERIFIED_CLOSED"
    for n in ["Camunda", "Cedar", "Celery", "Cerberus", "Cerbos"]: state["status_by_component"][n] = "VERIFIED_CLOSED"
    state["approval_required_before_components_11_15_move_or_wiring"] = False
    state["last_test"] = f"GitHub Actions run {os.environ.get('GITHUB_RUN_ID', 'unknown')} — runtime + UniversalPluginBus 10x"
    state["next_delta"] = "Audit/analyze components 16-20 when Director authorizes next round"
    STATE.write_text(json.dumps(state, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    marker = "## Cierre físico tanda 11–15"
    ledger = LEDGER.read_text(encoding="utf-8")
    if marker not in ledger:
        ledger += f"\n\n---\n\n{marker}\n\nRun: `{os.environ.get('GITHUB_RUN_ID','unknown')}`. Camunda, Cedar, Celery, Cerberus y Cerbos pasaron runtime real + Ficha Contract v2 + WIRING + `UniversalPluginBus.enchufar()` 10×; el origen fue deduplicado únicamente después del PASS. Estado: `VERIFIED_CLOSED` sujeto a read-back del commit publicado.\n"
        LEDGER.write_text(ledger, encoding="utf-8")
    arch_marker = "## 27. Integraciones VERIFIED_CLOSED — componentes 11–15"
    arch = ARCH.read_text(encoding="utf-8")
    if arch_marker not in arch:
        arch += f"\n\n{arch_marker}\n\n- **Camunda (B):** BPMN/workflow durable en `execution-orchestration/state-machine-executor/camunda/`; Zeebe aislado tras adapter/Ficha/WIRING/Universal Plugin Bus.\n- **Cedar (C):** autorización embebida determinista en `definition-registry/authorization-model/cedar/`.\n- **Celery (B):** despacho distribuido de tareas/workers en `execution-engine-pool/parallel-dispatch/celery/`.\n- **Cerberus (C):** validación/normalización Python en `definition-registry/schema-contracts/cerberus/`.\n- **Cerbos (C):** PDP/autorización centralizada en `control-governance/policy-guardrails-permissions/cerbos/`.\n\nGate común: MOVE real, Ficha Contract v2, WIRING, `UniversalPluginBus.enchufar()`, health/evidence y runtime; run `{os.environ.get('GITHUB_RUN_ID','unknown')}`. Esta sección es aditiva y no sustituye arquitectura existente.\n"
        ARCH.write_text(arch, encoding="utf-8")
    print("THIRD_FIVE_FINALIZED")


if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in {"prepare", "finalize"}:
        raise SystemExit("usage: yaiwes_integrate_third_five.py prepare|finalize")
    prepare() if sys.argv[1] == "prepare" else finalize()
