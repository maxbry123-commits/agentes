from __future__ import annotations

import importlib.util
import json
from pathlib import Path

BASE_PATH = Path(__file__).with_name("yaiwes_integrate_second_five.py")
spec = importlib.util.spec_from_file_location("yaiwes_integrate_second_five_base", BASE_PATH)
if spec is None or spec.loader is None:
    raise SystemExit("FAIL_CLOSED cannot load base integration script")
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)

Y = Path.cwd() / "Agente Yaiwes principal"

MANIFESTS = [
    (Y / "definition-registry/domain-specific-contracts/baml/ficha.baml.v2.json", "transversal", "T"),
    (Y / "execution-orchestration/state-machine-executor/burr/ficha.burr.v2.json", "pipeline", "E"),
    (Y / "mesh-routing-collaboration/caddy-gateway/ficha.caddy.v2.json", "transversal", "T"),
]

SOURCE_ROOTS = [
    base.SRC / "Argo-Workflows",
    base.SRC / "Azure-Durable-Functions",
    base.SRC / "BAML",
    base.SRC / "Burr",
    base.SRC / "Caddy",
]


def normalize_generated_fichas() -> None:
    for path, categoria, etapa in MANIFESTS:
        if not path.is_file():
            raise SystemExit(f"FAIL_CLOSED missing generated ficha: {path}")
        doc = json.loads(path.read_text(encoding="utf-8"))
        # Ficha Contract v2 canonical values. Do not weaken the validator.
        doc["contrato"]["rol"] = "transform"
        doc["seguridad"]["sandbox"] = "container"
        doc["categoria"] = categoria
        doc["etapa"] = etapa
        doc["repite_en"] = ["EXEC_STATE"]
        doc["salud"]["metodo"] = "exec"
        path.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def defer_rm(path: Path) -> None:
    """Keep recovered sources until every runtime and bus gate has passed."""
    return None


def verified_rm(path: Path) -> None:
    """Deduplicate only after runtime + UniversalPluginBus verification."""
    if path.exists():
        base.run("git", "rm", "-r", "-f", str(path))


def move_caddy_runtime_dependency() -> None:
    """Move the internal notify package required directly by caddy.go."""
    source = base.SRC / "Caddy/notify"
    destination = Y / "mesh-routing-collaboration/caddy-gateway/notify"
    if source.exists() and not destination.exists():
        base.mv(source, destination)


def prepare() -> None:
    # StrategyDelta: MOVE the missing Caddy internal runtime dependency while
    # keeping all source-root deduplication deferred until runtime + bus PASS.
    move_caddy_runtime_dependency()
    base.rm = defer_rm
    base.prepare()
    normalize_generated_fichas()
    base.run("git", "add", str(Y), str(base.SRC))


def persist() -> None:
    # Deduplicate recovered origins only after the complete verification gate.
    for source_root in SOURCE_ROOTS:
        verified_rm(source_root)
    base.persist()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("prepare", "persist"))
    args = parser.parse_args()
    if args.command == "prepare":
        prepare()
    else:
        persist()
