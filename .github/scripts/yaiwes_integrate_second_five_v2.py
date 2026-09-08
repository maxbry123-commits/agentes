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


def prepare() -> None:
    base.prepare()
    normalize_generated_fichas()
    base.run("git", "add", str(Y), str(base.SRC))


def persist() -> None:
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
