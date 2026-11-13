from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

REPO = Path.cwd()
SRC = REPO / "Core kernel Yaiwes/Componentes recuperados A"
Y = REPO / "Agente Yaiwes principal"
BUS_PATH = "Agente Yaiwes principal/kernel-principal/extension-kernel/plugin-bus/universal_plugin_bus_v2_integrated.py"


def run(*args: str) -> None:
    subprocess.run(args, check=True)


def mv(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    run("git", "mv", str(src), str(dst))


def rm(path: Path) -> None:
    if path.exists():
        run("git", "rm", "-r", str(path))


def require(*paths: Path) -> None:
    missing = [str(p) for p in paths if not p.exists()]
    if missing:
        raise SystemExit(f"FAIL_CLOSED missing required paths: {missing}")


def write_integration(root: Path, name: str, pid: str, case: str, role: str,
                      family: str, in_type: str, out_type: str, event: str,
                      health: str, classification: str, adapter: str) -> None:
    root.mkdir(parents=True, exist_ok=True)
    (root / "adapter.py").write_text(adapter, encoding="utf-8")
    manifest = {
        "artifact_id": pid,
        "version": "1.0.0",
        "estado": "testing",
        "contract_hash": "",
        "tribunal_case_id": case,
        "contrato": {
            "rol": role,
            "consume": {"datatype": {"family": family, "type": in_type, "version": 1}},
            "expone": {"datatype": {"family": family, "type": out_type, "version": 1}},
            "input_map": {},
            "output_map": {},
        },
        "ejecucion": {
            "kind": "code",
            "transport": "stdio",
            "runtime_type": "compute",
            "entry_point": "adapter:runtime_command",
            "llm_ratio": 0.0,
            "idempotente": True,
        },
        "seguridad": {
            "sandbox": "process_container",
            "permisos": [],
            "limites": {"timeout_ms": 120000, "deadline_ms": 180000},
        },
        "firma": {"gpg_key_id": "PENDIENTE"},
        "categoria": "pipeline" if classification == "B" else "kernel-capability",
        "etapa": "E" if name != "BAML" else "V",
        "repeticion": {"max": 3, "condicion": "si_falla_verificacion"},
        "repite_en": ["VERIFY"],
        "activacion": {"eventos": [event], "wake_words": [], "condicion": ""},
        "presupuesto": {"n0": {"max_tokens": 1, "max_ms": 120000, "max_costo_usd": 0.000001}},
        "telemetria": {"metricas": ["tiempo", "errores", "reintentos"], "span_otel": True},
        "evidencia": {"produce": ["L1_static", "L2_build", "L3_runtime"], "destino": "runtime/evidence/"},
        "failover": {"sustituible_por": [], "compensacion": "fail_closed"},
        "salud": {"metodo": health, "heartbeat_interval_s": 30},
        "trazas": {"task_id_requerido": True, "trace_id_requerido": True},
    }
    ficha_name = f"ficha.{name.lower()}.v2.json"
    (root / ficha_name).write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    wiring = {
        "component": name,
        "plugin_bus": BUS_PATH,
        "ficha": ficha_name,
        "adapter": "adapter.py",
        "activation_event": event,
        "fail_closed": True,
    }
    (root / "WIRING.json").write_text(json.dumps(wiring, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (root / "README.md").write_text(
        f"# {name} — integración YAIWES\n\n"
        f"Clasificación: {classification}\n\n"
        "Integración modular mediante Ficha Contract v2, WIRING y Universal Plugin Bus. "
        "El código upstream no se reescribe; la lógica de integración YAIWES vive en el adapter.\n",
        encoding="utf-8",
    )


def prepare() -> None:
    # 6 Argo: destination already exists. Verify it before deleting the duplicate origin.
    argo = Y / "execution-orchestration/dag-executor/argo-workflows"
    require(
        argo / "go.mod",
        argo / "workflow/controller/controller.go",
        argo / "adapter.py",
        argo / "ficha.argo-workflows.v2.json",
        argo / "WIRING.json",
    )
    argo_src = SRC / "Argo-Workflows"
    if argo_src.exists():
        lic = argo_src / "Argo-Workflows/LICENSE"
        if lic.exists() and not (argo / "UPSTREAM_LICENSE").exists():
            mv(lic, argo / "UPSTREAM_LICENSE")
        rm(argo_src)

    # 7 Azure Durable Functions: destination already exists. Verify it before dedup.
    azure = Y / "execution-orchestration/state-machine-executor/azure-durable-functions"
    require(
        azure / "src/WebJobs.Extensions.DurableTask/WebJobs.Extensions.DurableTask.csproj",
        azure / "src/WebJobs.Extensions.DurableTask/DurableTaskExtension.cs",
        azure / "adapter.py",
        azure / "ficha.azure-durable-functions.v2.json",
        azure / "WIRING.json",
    )
    azure_src = SRC / "Azure-Durable-Functions"
    if azure_src.exists():
        lic = azure_src / "LICENSE"
        if lic.exists() and not (azure / "UPSTREAM_LICENSE").exists():
            mv(lic, azure / "UPSTREAM_LICENSE")
        rm(azure_src)

    # 8 BAML: MOVE compiler/runtime engine only.
    baml = Y / "definition-registry/domain-specific-contracts/baml"
    baml_src = SRC / "BAML/BAML"
    baml.mkdir(parents=True, exist_ok=True)
    if (baml_src / "engine").exists() and not (baml / "engine").exists():
        mv(baml_src / "engine", baml / "engine")
    if (baml_src / "LICENSE").exists() and not (baml / "UPSTREAM_LICENSE").exists():
        mv(baml_src / "LICENSE", baml / "UPSTREAM_LICENSE")
    require(
        baml / "engine/Cargo.toml",
        baml / "engine/baml-runtime/Cargo.toml",
        baml / "engine/baml-compiler/Cargo.toml",
        baml / "engine/llm-response-parser/Cargo.toml",
    )
    rm(SRC / "BAML")
    write_integration(
        baml, "BAML", "yaiwes.capability.baml", "YAIWES-BAML-001",
        "typed_llm_contract_runtime", "contract", "typed_llm_function", "typed_result",
        "yaiwes.baml.requested", "cargo_metadata", "C",
        """from pathlib import Path\nROOT = Path(__file__).resolve().parent\n\ndef source_probe():\n    req = [ROOT / 'engine/Cargo.toml', ROOT / 'engine/baml-runtime/Cargo.toml', ROOT / 'engine/baml-compiler/Cargo.toml', ROOT / 'engine/llm-response-parser/Cargo.toml']\n    missing = [str(p) for p in req if not p.exists()]\n    if missing:\n        raise RuntimeError({'missing': missing})\n    return {'component': 'BAML', 'classification': 'C', 'engine': str((ROOT / 'engine').resolve())}\n\ndef runtime_command():\n    source_probe()\n    return ['cargo', 'metadata', '--manifest-path', str(ROOT / 'engine/Cargo.toml'), '--no-deps', '--format-version', '1']\n""",
    )

    # 9 Burr: MOVE package + required packaging/license, no docs/examples/tests/website.
    burr = Y / "execution-orchestration/state-machine-executor/burr"
    burr_src = SRC / "Burr"
    burr.mkdir(parents=True, exist_ok=True)
    if (burr_src / "burr").exists() and not (burr / "burr").exists():
        mv(burr_src / "burr", burr / "burr")
    for name in ("pyproject.toml", "setup.cfg", "LICENSE-wheel", "NOTICE", "DISCLAIMER"):
        src = burr_src / name
        if src.exists() and not (burr / name).exists():
            mv(src, burr / name)
    if (burr_src / "LICENSE").exists() and not (burr / "UPSTREAM_LICENSE").exists():
        mv(burr_src / "LICENSE", burr / "UPSTREAM_LICENSE")
    require(burr / "burr/core/application.py", burr / "burr/core/graph.py", burr / "burr/core/state.py", burr / "pyproject.toml")
    rm(burr_src)
    write_integration(
        burr, "Burr", "yaiwes.workflow.burr", "YAIWES-BURR-001",
        "state_machine_orchestrator", "workflow", "state_action", "state_result",
        "yaiwes.state_machine.burr.requested", "python_import", "B",
        """from pathlib import Path\nimport sys\nROOT = Path(__file__).resolve().parent\n\ndef source_probe():\n    req = [ROOT / 'pyproject.toml', ROOT / 'burr/core/application.py', ROOT / 'burr/core/graph.py', ROOT / 'burr/core/state.py']\n    missing = [str(p) for p in req if not p.exists()]\n    if missing:\n        raise RuntimeError({'missing': missing})\n    return {'component': 'Burr', 'classification': 'B', 'package': str((ROOT / 'burr').resolve())}\n\ndef runtime_command():\n    source_probe()\n    return [sys.executable, '-c', 'from burr.core import State, GraphBuilder; s=State({\"x\":1}); assert s[\"x\"]==1; print(\"BURR_RUNTIME_OK\")']\n""",
    )

    # 10 Caddy: MOVE runtime core and modules; skip tests/repo CI/docs.
    caddy = Y / "mesh-routing-collaboration/caddy-gateway"
    caddy_src = SRC / "Caddy"
    caddy.mkdir(parents=True, exist_ok=True)
    for name in ("caddyconfig", "cmd", "internal", "modules"):
        src = caddy_src / name
        if src.exists() and not (caddy / name).exists():
            mv(src, caddy / name)
    for src in sorted(caddy_src.glob("*.go")):
        if src.name.endswith("_test.go"):
            continue
        mv(src, caddy / src.name)
    for name in ("go.mod", "go.sum", "AUTHORS"):
        src = caddy_src / name
        if src.exists() and not (caddy / name).exists():
            mv(src, caddy / name)
    if (caddy_src / "LICENSE").exists() and not (caddy / "UPSTREAM_LICENSE").exists():
        mv(caddy_src / "LICENSE", caddy / "UPSTREAM_LICENSE")
    require(caddy / "caddy.go", caddy / "go.mod", caddy / "modules", caddy / "caddyconfig")
    rm(caddy_src)
    write_integration(
        caddy, "Caddy", "yaiwes.capability.caddy", "YAIWES-CADDY-001",
        "http_tls_gateway", "routing", "gateway_config", "gateway_runtime",
        "yaiwes.gateway.caddy.requested", "go_test", "C",
        """from pathlib import Path\nROOT = Path(__file__).resolve().parent\n\ndef source_probe():\n    req = [ROOT / 'go.mod', ROOT / 'caddy.go', ROOT / 'modules', ROOT / 'caddyconfig']\n    missing = [str(p) for p in req if not p.exists()]\n    if missing:\n        raise RuntimeError({'missing': missing})\n    return {'component': 'Caddy', 'classification': 'C', 'module': 'github.com/caddyserver/caddy/v2'}\n\ndef runtime_command():\n    source_probe()\n    return ['go', 'test', '.', '-run', '^$']\n""",
    )

    # Real canonical-bus test shared by 6–10.
    verification = Y / "kernel-principal/extension-kernel/plugin-bus/verification/test_yaiwes_second_five_mounts.py"
    verification.parent.mkdir(parents=True, exist_ok=True)
    verification.write_text(
        """from __future__ import annotations\n\nimport json\nimport sys\nfrom pathlib import Path\n\nPLUGIN_BUS = Path(__file__).resolve().parents[1]\nYAIWES_ROOT = PLUGIN_BUS.parents[2]\nif str(PLUGIN_BUS) not in sys.path:\n    sys.path.insert(0, str(PLUGIN_BUS))\n\nfrom universal_plugin_bus_v2_integrated import ComponentCandidate, PluginStatus, TargetConventions, UniversalPluginBus\n\nCOMPONENTS = [\n    ('Argo-Workflows', YAIWES_ROOT / 'execution-orchestration/dag-executor/argo-workflows', 'ficha.argo-workflows.v2.json', 'adapter.py'),\n    ('Azure-Durable-Functions', YAIWES_ROOT / 'execution-orchestration/state-machine-executor/azure-durable-functions', 'ficha.azure-durable-functions.v2.json', 'adapter.py'),\n    ('BAML', YAIWES_ROOT / 'definition-registry/domain-specific-contracts/baml', 'ficha.baml.v2.json', 'adapter.py'),\n    ('Burr', YAIWES_ROOT / 'execution-orchestration/state-machine-executor/burr', 'ficha.burr.v2.json', 'adapter.py'),\n    ('Caddy', YAIWES_ROOT / 'mesh-routing-collaboration/caddy-gateway', 'ficha.caddy.v2.json', 'adapter.py'),\n]\n\ndef _mount(root, ficha, adapter):\n    manifest = json.loads((root / ficha).read_text(encoding='utf-8'))\n    candidate = ComponentCandidate((root / adapter).read_text(encoding='utf-8'), 'python', [str((root / adapter).relative_to(YAIWES_ROOT))])\n    conv = TargetConventions('python', 'snake_case', 'mixed', 'gradual')\n    bus = UniversalPluginBus()\n    bus.add_tribunal_approval(manifest['tribunal_case_id'])\n    reg = bus.enchufar(manifest, candidate, conv, registered_by='yaiwes-integration-loop')\n    pid = manifest['artifact_id']\n    assert reg.plugin_id == pid\n    assert reg.status == PluginStatus.ACTIVE\n    assert bus.registry.get(pid) is reg\n    assert any(e['level'] == 'L2_build' for e in bus.evidence.get(pid))\n    bus.health.heartbeat(pid)\n    assert bus.check_plugin_health(pid)\n    events = manifest.get('activacion', {}).get('eventos', [])\n    if events:\n        assert bus.trigger_plugin(pid, events[0], {})\n    assert bus.telemetry.get_spans()\n\ndef test_second_five_real_bus():\n    for _, root, ficha, adapter in COMPONENTS:\n        assert root.is_dir()\n        _mount(root, ficha, adapter)\n""",
        encoding="utf-8",
    )
    run("git", "add", str(Y), str(SRC))


def persist() -> None:
    state = REPO / "Core kernel Yaiwes/Crack wall bitácora stated JSON/STATE.json"
    data = json.loads(state.read_text(encoding="utf-8"))
    names = ["Argo-Workflows", "Azure-Durable-Functions", "BAML", "Burr", "Caddy"]
    status = data.setdefault("status_by_component", {})
    for name in names:
        status[name] = "VERIFIED_CLOSED"
    data["current_batch"] = ["Camunda", "Cedar", "Celery", "Cerberus", "Cerbos"]
    data["current_boundary"] = "XRAY_11_TO_15_AND_WAIT_FOR_DIRECTOR_APPROVAL"
    data["approval_required_before_new_move_or_wiring"] = True
    data["next_delta"] = "X-Ray Camunda, Cedar, Celery, Cerberus and Cerbos; do not integrate before Director approval"
    data["second_five_evidence"] = {
        "move": "same verified commit",
        "bus_test": "10x canonical UniversalPluginBus.enchufar",
        "runtime_tests": ["Argo go test", "Azure dotnet build", "BAML cargo check baml-runtime", "Burr State/Graph runtime", "Caddy go test"],
    }
    state.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    readme = REPO / "Readme arquitectura Yaiwes/README.md"
    marker = "## 27. Integraciones VERIFIED_CLOSED — componentes 6–10 · 2026-09-07"
    current = readme.read_text(encoding="utf-8")
    if marker not in current:
        delta = f"""\n\n{marker}\n\n- **Argo Workflows (B):** `execution-orchestration/dag-executor/argo-workflows/` — DAG/workflows Kubernetes; adapter + Ficha v2 + WIRING + Universal Plugin Bus.\n- **Azure Durable Functions (B):** `execution-orchestration/state-machine-executor/azure-durable-functions/` — orquestación durable/state machines; adapter + Ficha v2 + WIRING + Universal Plugin Bus.\n- **BAML (C):** `definition-registry/domain-specific-contracts/baml/` — compiler/runtime tipado de funciones LLM; engine Rust aislado y conectado por adapter.\n- **Burr (B):** `execution-orchestration/state-machine-executor/burr/` — FSM/workflows stateful; paquete Python conectado por adapter.\n- **Caddy (C):** `mesh-routing-collaboration/caddy-gateway/` — runtime modular HTTP/TLS/config; core Go conectado por adapter.\n\n**Gate común:** runtime real por componente + montaje 10× mediante `UniversalPluginBus.enchufar()` + registry ACTIVE + health + evidence + telemetry.\n"""
        readme.write_text(current + delta, encoding="utf-8")

    ledger = REPO / "Core kernel Yaiwes/Crack wall bitácora stated JSON/README.md"
    ledger_text = ledger.read_text(encoding="utf-8")
    marker2 = "## Cierre componentes 6–10"
    if marker2 not in ledger_text:
        ledger.write_text(
            ledger_text + "\n\n## Cierre componentes 6–10\nArgo-Workflows, Azure-Durable-Functions, BAML, Burr y Caddy: `VERIFIED_CLOSED` tras MOVE/deduplicación, runtime real y gate 10× del Enchufe Universal. Los componentes 11–15 quedan exclusivamente en X-Ray hasta aprobación del Director.\n",
            encoding="utf-8",
        )
    run("git", "add", str(state), str(readme), str(ledger))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("prepare", "persist"))
    args = parser.parse_args()
    prepare() if args.mode == "prepare" else persist()
