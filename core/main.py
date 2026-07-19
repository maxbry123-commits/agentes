"""
main.py — CLI del Orquestador Universal v1.0.

Uso:
  python main.py --template template.json
  python main.py --demo
"""
import argparse
import json
import os
import sys

from orchestrator.orchestrator import run_orchestrator


DEMO_TEMPLATE = {
    "objetivo": "construir API REST de tareas en FastAPI con tests",
    "planificar": [
        "L1 Goal Lock + Plan",
        "L2 Consensus plan",
        "L3 Asignar sandboxes",
        "L4 Claude Code EJECUTA",
        "L5 Mimo Code VERIFICA (pytest)",
        "L6 Mimo Code REPARA si L5 falla",
        "L7 Mimo Code VALIDA (ruff/black/mypy)",
        "L8 Loop repair max 2",
        "L9 Sentinel + OpenManus",
        "L10 Juez 3 simulaciones",
    ],
    "organizar": {
        "L1": "Orquestador",
        "L2": "3 sandboxes paralelos (consensus)",
        "L3": "Router",
        "L4": "Sandbox Claude",
        "L5-L8": "Sandbox Mimo",
        "L9": "Sentinel",
        "L10": "Juez",
    },
    "tareas": [
        "escribir models.py",
        "escribir routes/tasks.py",
        "escribir tests/test_tasks.py",
        "ejecutar pytest",
        "ejecutar ruff/black/mypy",
        "persistir baseline",
    ],
    "metas": [
        "pytest pasa 100%",
        "ruff 0 errores",
        "mypy 0 errores",
        "coverage >= 80%",
    ],
    "proposito": "habilitar API base para el módulo de tareas del proyecto",
    "refutaciones": [
        "R1: Claude puede proponer código que rompe imports",
        "R2: Mimo puede entrar en loop infinito reparando",
        "R3: tests pueden pasar pero la app crashea en runtime",
        "R4: baseline puede no existir en primera ejecución",
        "R5: sandbox puede colgarse sin respuesta",
    ],
    "consensus": "fast",
}


def main():
    parser = argparse.ArgumentParser(description="Orquestador Universal v1.0")
    parser.add_argument("--template", type=str, help="Path al JSON con la plantilla")
    parser.add_argument("--demo", action="store_true", help="Ejecutar demo con plantilla hardcoded")
    parser.add_argument("--work-dir", type=str, default="/tmp/orch_work",
                        help="Directorio de trabajo para sandboxes")
    parser.add_argument("--consensus", type=str, default="fast",
                        choices=["single", "fast", "full"],
                        help="Modo de consenso: single (sin consensus), fast (2 modelos), full (3 modelos)")
    args = parser.parse_args()

    if args.demo:
        template = DEMO_TEMPLATE
    elif args.template:
        with open(args.template) as f:
            template = json.load(f)
    else:
        parser.print_help()
        sys.exit(1)

    print(f"[orchestrator] Iniciando con plantilla: {template.get('objetivo', '<sin objetivo>')[:80]}")
    print(f"[orchestrator] Modo consensus: {args.consensus}")
    print(f"[orchestrator] Work dir: {args.work_dir}")
    print("=" * 70)

    result = run_orchestrator(template, work_dir=args.work_dir,
                              consensus_mode=args.consensus or template.get("consensus", "fast"))

    print("=" * 70)
    print(f"[orchestrator] Status: {result['status']}")
    print(f"[orchestrator] Goal hash: {result['goal_hash']}")
    print(f"[orchestrator] Completed nodes: {len(result['completed_nodes'])}/{len(result['order'])}")
    print(f"[orchestrator] Completed: {result['completed_nodes']}")
    if result["errors"]:
        print(f"[orchestrator] Errors ({len(result['errors'])}):")
        for e in result["errors"][:10]:
            print(f"  - {e}")
    if "metrics" in result and result["metrics"]:
        m = result["metrics"]
        print(f"[orchestrator] Metrics: events={m.get('total_events', 0)} "
              f"loops={len(m.get('loops', []))} "
              f"deadlocks={len(m.get('deadlocks', []))}")
    return 0 if result["status"] == "done" else 1


if __name__ == "__main__":
    sys.exit(main())
