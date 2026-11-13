#!/usr/bin/env python3
from __future__ import annotations

import json
import shutil
import textwrap
from pathlib import Path

ROOT = Path("📂coda workflow persistencias")
FIELD = ROOT / "🏈 cancha deportiva de fútbol"
TEAM = "Swarm agent team Navy seals YAIWES"
VERSION = "YAIWES-PERSISTENCE-v2.0"

COMPONENTS = [
    "01-DeepAudit", "02-CyberStrikeAI", "03-LuaN1aoAgent", "04-AI-Pentest",
    "05-AI-Infra-Guard", "06-PentAGI", "07-Strix", "08-Redcell", "09-Shel",
    "10-Pentest-Swarm-AI", "11-LLM-CTF-Solver", "12-PentestGPT",
    "13-Auto-Pentest-LLM", "14-Dark-Moon", "15-Pentdem",
    "16-Autonomous-Pentest-Agent", "17-AI-Red-Team-Agent", "18-Agent-Smith",
    "19-TPT-Agent", "20-OpenWhale", "21-H-Pentest", "22-PHANTOM",
    "23-HackSynth", "24-Security-AI-Agent",
]

ADAPTER = textwrap.dedent('''\
from __future__ import annotations
import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, List

ALLOWED_STATUS = {"PENDING", "CLAIMED", "RUNNING", "CHECKPOINTED", "VERIFIED", "FAILED", "RELEASED"}

@dataclass
class TaskState:
    task_id: str
    status: str = "PENDING"
    attempts: int = 0
    checkpoint: Dict[str, Any] | None = None
    evidence: List[Dict[str, Any]] | None = None

    def __post_init__(self) -> None:
        if self.checkpoint is None:
            self.checkpoint = {}
        if self.evidence is None:
            self.evidence = []

class YaiwesPersistenceAdapter:
    """Safe persistence link. Never executes vendor/source code."""
    def __init__(self, state_path: str | Path) -> None:
        self.state_path = Path(state_path)

    def load(self, task_id: str) -> TaskState:
        if not self.state_path.exists():
            return TaskState(task_id=task_id)
        data = json.loads(self.state_path.read_text(encoding="utf-8"))
        if data.get("task_id") != task_id:
            return TaskState(task_id=task_id)
        return TaskState(**data)

    def save(self, state: TaskState) -> None:
        if state.status not in ALLOWED_STATUS:
            raise ValueError(f"invalid status: {state.status}")
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.state_path.with_suffix(self.state_path.suffix + ".tmp")
        tmp.write_text(json.dumps(asdict(state), ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(self.state_path)

    def claim(self, task_id: str) -> TaskState:
        state = self.load(task_id)
        if state.status not in {"PENDING", "FAILED", "RELEASED"}:
            raise RuntimeError(f"task not claimable: {state.status}")
        state.status = "CLAIMED"
        state.attempts += 1
        self.save(state)
        return state

    def checkpoint_task(self, task_id: str, payload: Dict[str, Any]) -> TaskState:
        state = self.load(task_id)
        if state.status not in {"CLAIMED", "RUNNING", "CHECKPOINTED"}:
            raise RuntimeError(f"task not checkpointable: {state.status}")
        state.status = "CHECKPOINTED"
        state.checkpoint = dict(payload)
        self.save(state)
        return state

    def verify(self, task_id: str, evidence: Dict[str, Any]) -> TaskState:
        state = self.load(task_id)
        state.status = "VERIFIED"
        state.evidence.append(dict(evidence))
        self.save(state)
        return state

    def release(self, task_id: str) -> TaskState:
        state = self.load(task_id)
        state.status = "RELEASED"
        self.save(state)
        return state
''')

TEST = textwrap.dedent('''\
from pathlib import Path
import tempfile
import unittest
from yaiwes_persistence_adapter import YaiwesPersistenceAdapter

class PersistenceAdapterTests(unittest.TestCase):
    def test_roundtrip(self):
        with tempfile.TemporaryDirectory() as td:
            state_path = Path(td) / "state.json"
            adapter = YaiwesPersistenceAdapter(state_path)
            state = adapter.claim("T-1")
            self.assertEqual(state.status, "CLAIMED")
            state = adapter.checkpoint_task("T-1", {"step": 2})
            self.assertEqual(state.checkpoint["step"], 2)
            state = adapter.verify("T-1", {"pass": True})
            self.assertEqual(state.status, "VERIFIED")
            state = adapter.release("T-1")
            self.assertEqual(state.status, "RELEASED")

if __name__ == "__main__":
    unittest.main()
''')

SAFE_BUS = textwrap.dedent('''\
from __future__ import annotations
import ast
from dataclasses import dataclass
from pathlib import Path
from typing import List

@dataclass(frozen=True)
class StaticSymbol:
    name: str
    kind: str

def extract_python_symbols(source: str) -> List[StaticSymbol]:
    tree = ast.parse(source)
    symbols: List[StaticSymbol] = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            symbols.append(StaticSymbol(node.name, "function"))
        elif isinstance(node, ast.ClassDef):
            symbols.append(StaticSymbol(node.name, "class"))
    return symbols

def inspect_file(path: str | Path) -> List[StaticSymbol]:
    return extract_python_symbols(Path(path).read_text(encoding="utf-8"))

def compatible(expone: dict, consume: dict) -> bool:
    return bool(expone) and expone.get("datatype") == consume.get("datatype")
''')


def source_repo_from_manifest(path: Path) -> str:
    if not path.exists():
        return "unknown"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return "unknown"
    source = data.get("source")
    if isinstance(source, dict):
        source = source.get("repo") or source.get("repository")
    return str(data.get("source_repo") or source or "unknown")


def build_readme(component_name: str, upstream_name: str, source_repo: str) -> str:
    return f"""# {component_name} — YAIWES Persistence Architecture v2.0

## {TEAM}

**Nueva versión:** `{VERSION}`  
**Componente base:** `{upstream_name}`  
**Fuente upstream:** `{source_repo}`  
**Rol nuevo:** eslabón seguro de persistencia de tareas dentro de CODA YAIWES.

### Arquitectura nueva

`INPUT → NORMALIZE → CLAIM → CHECKPOINT → SAFE_TASK → VERIFY → EVIDENCE → RELEASE/NEXT`

El código upstream se conserva dentro de `code/` para trazabilidad. El enlace YAIWES nuevo no ejecuta automáticamente código externo: usa `code/coda_persistence/yaiwes_persistence_adapter.py` para estado, checkpoints, reintentos controlados, evidencia y liberación de tareas.

### Contrato universal / Fables

El cableado adopta el sistema suministrado por el usuario: ficha universal con identidad/versionado, `consume/expone`, ejecución, sandbox, límites, evidencia, salud, failover y trazas. El autoensamblaje solo se permite entre entradas/salidas compatibles y validadas.

### Frontera de ejecución

- Descubrimiento estático; no `exec`/`eval` del código upstream.
- Sin shell ni red desde el adapter de persistencia.
- Sin credenciales ni acciones irreversibles desde este eslabón.
- Código upstream preservado como referencia/análisis.
- El runtime nuevo ejecutable es exclusivamente el adapter de persistencia verificado.

### Estado del eslabón

`PENDING → CLAIMED → CHECKPOINTED → VERIFIED → RELEASED`

### Documentación y evidencia

`📂coda workflow persistencias/🏈 cancha deportiva de fútbol/{component_name}/`
"""


def main() -> None:
    if not ROOT.exists():
        raise SystemExit(f"MISSING_ROOT:{ROOT}")
    FIELD.mkdir(parents=True, exist_ok=True)

    registry = []
    for upstream in COMPONENTS:
        old_path = ROOT / upstream
        new_name = f"🏈 {upstream}"
        new_path = ROOT / new_name

        if old_path.exists() and not new_path.exists():
            old_path.rename(new_path)
        if not new_path.exists():
            raise SystemExit(f"MISSING_COMPONENT:{upstream}")

        code_dir = new_path / "code"
        if not code_dir.exists():
            raise SystemExit(f"MISSING_CODE_DIR:{new_name}")

        link_dir = code_dir / "coda_persistence"
        link_dir.mkdir(parents=True, exist_ok=True)
        (link_dir / "yaiwes_persistence_adapter.py").write_text(ADAPTER, encoding="utf-8")
        (link_dir / "test_yaiwes_persistence_adapter.py").write_text(TEST, encoding="utf-8")

        docs_dir = FIELD / new_name
        docs_dir.mkdir(parents=True, exist_ok=True)

        for filename in (
            "DOWNLOAD_EXTRACT_MANIFEST.json",
            "PERSISTENCE-ARCHITECTURE-MAP.md",
            "PERSISTENCE-LINK-MANIFEST.json",
        ):
            src = new_path / filename
            if src.exists():
                dst = docs_dir / filename
                if dst.exists():
                    dst.unlink()
                shutil.move(str(src), str(dst))

        manifest_path = docs_dir / "DOWNLOAD_EXTRACT_MANIFEST.json"
        source_repo = source_repo_from_manifest(manifest_path)
        (docs_dir / "README.md").write_text(
            build_readme(new_name, upstream, source_repo), encoding="utf-8"
        )

        link_manifest = {
            "schema": "yaiwes.coda.persistence-link/v2",
            "component": new_name,
            "upstream_component": upstream,
            "version": VERSION,
            "team": TEAM,
            "adapter": str(link_dir / "yaiwes_persistence_adapter.py"),
            "test": str(link_dir / "test_yaiwes_persistence_adapter.py"),
            "mode": "TASK_PERSISTENCE_ONLY",
            "offensive_execution": False,
            "network_default": "deny",
            "source_execution_during_discovery": False,
        }
        (docs_dir / "PERSISTENCE-LINK-MANIFEST-V2.json").write_text(
            json.dumps(link_manifest, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        registry.append(link_manifest)

    # Project-generated non-code files are centralized here. Vendor/source files under code/ stay untouched.
    project_docs = FIELD / "00-PROJECT"
    project_docs.mkdir(parents=True, exist_ok=True)
    for path in list(ROOT.iterdir()):
        if not path.is_file():
            continue
        if path.suffix.lower() not in {".md", ".json", ".txt", ".yaml", ".yml"}:
            continue
        dst = project_docs / path.name
        if dst.exists():
            dst.unlink()
        shutil.move(str(path), str(dst))

    (FIELD / "YAIWES-SWARM-NAVY-SEALS-REGISTRY.json").write_text(
        json.dumps(
            {"schema": "yaiwes.swarm.registry/v2", "count": len(registry), "components": registry},
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    fables = ROOT / "Fables enchufe universal"
    fables.mkdir(parents=True, exist_ok=True)
    (fables / "yaiwes_fables_static_safe_bus.py").write_text(SAFE_BUS, encoding="utf-8")
    (fables / "README-YAIWES-V2.md").write_text(
        "# Fables/Kimi Universal Plug — YAIWES safe integration v2\n\n"
        f"## {TEAM}\n\n"
        "Base conceptual: ficha universal + plugin bus suministrados por el usuario. "
        "Para componentes externos no confiables, la inspección dinámica se sustituye "
        "por AST estático. El cableado operativo conecta únicamente adapters de persistencia YAIWES verificados.\n",
        encoding="utf-8",
    )

    print(f"TRANSFORMED_COMPONENTS={len(registry)}")


if __name__ == "__main__":
    main()
