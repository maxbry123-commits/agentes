"""
main_runtime.py — CLI del UOOS Parte 2 v3.0 Executor Runtime.

Uso:
  python main_runtime.py --demo              (3 nodos dummy)
  python main_runtime.py --from-b2 B2_state.json
  python main_runtime.py --probar            (corre test_runtime.py)
"""
import argparse
import json
import sys
import time

from orchestrator.runtime import (
    RuntimeExecutor, RuntimeState, Node, NodeStatus,
    UOOS_VERSION, build_state_from_b3
)


def make_demo_state(n: int = 5) -> RuntimeState:
    """Estado demo: N nodos en cadena."""
    state = RuntimeState(proyecto="demo", modo="A")
    for i in range(1, n + 1):
        nid = f"T-{i:03d}"
        node = Node(
            id=nid,
            goal=f"objetivo verificable del nodo {i}",
            contrato_input={},
            contrato_output={"criterio_exito": "status==ok"},
            criterio_exito="status==ok",
            dependencies=[f"T-{i-1:03d}"] if i > 1 else [],
            risk="bajo",
            priority=1,
            skills_requeridas=["python"],
            timeout_seg=10,
        )
        state.nodos[nid] = node
    return state


def demo(n: int = 5, director: bool = False):
    """Demo: BOOT → ejecutar N nodos → CIERRE."""
    state = make_demo_state(n)
    ex = RuntimeExecutor(state)

    # BOOT
    print("=" * 60)
    print(f"UOOS Parte 2 v{UOOS_VERSION} — DEMO")
    print("=" * 60)
    boot = ex.boot()
    print(f"BOOT: {boot['status']} | modo={boot['modo']}")
    print(f"ORDEN: {boot['orden']}")
    print(f"PRÓXIMO: {boot['proximo']}")
    print()

    if not director:
        print("(auto-ejecutando, sin pedir GO)")
    else:
        go = input("¿GO? ")
        if go.strip().upper() != "GO":
            print("Abortado por Director")
            return 1

    # ejecutar nodos
    while True:
        nodo = ex.rt_10_select()
        if nodo is None:
            break
        result = ex.execute_node(nodo, {})
        status = "✓" if result["status"] == "done" else "✗"
        print(f"  {status} {nodo.id} ({nodo.goal[:40]}) → {result['status']}")

    # CIERRE
    print()
    cierre = ex.rt_90_cierre()
    print(f"CIERRE: {cierre['status']}")
    if cierre["status"] == "completed":
        print(f"  Nodos completados: {cierre['nodos']}")
        print(f"  Recoveries: {sum(n.recoveries for n in state.nodos.values())}")
    return 0 if cierre["status"] == "completed" else 1


def from_b2(b2_path: str):
    """Carga state desde B2_state.json y continúa."""
    if not os.path.exists(b2_path):
        print(f"ERROR: {b2_path} no existe")
        return 1
    with open(b2_path) as f:
        b2 = json.load(f)
    # reconstruir nodos desde state.json
    state = RuntimeState(
        proyecto=b2.get("proyecto", "imported"),
        uoos_version=b2.get("uoos_version", UOOS_VERSION),
        modo=b2.get("modo", "A"),
    )
    for nid, nd in b2.get("nodos", {}).items():
        node = Node(
            id=nid,
            goal=nd.get("goal", ""),
            contrato_input={},
            contrato_output={"criterio_exito": nd.get("criterio_exito", "status==ok")},
            criterio_exito=nd.get("criterio_exito", "status==ok"),
            dependencies=nd.get("dependencies", []),
            risk=nd.get("risk", "bajo"),
            priority=nd.get("priority", 3),
            skills_requeridas=nd.get("skills_requeridas", []),
            timeout_seg=nd.get("timeout_seg", 300),
            estado=nd.get("estado", "pending"),
        )
        node.intentos = nd.get("intentos", 0)
        node.recoveries = nd.get("recoveries", 0)
        state.nodos[nid] = node
    ex = RuntimeExecutor(state)
    return demo_with_state(ex, state)


def demo_with_state(ex: RuntimeExecutor, state: RuntimeState) -> int:
    boot = ex.boot()
    print(f"BOOT: {boot['status']} | modo={boot['modo']} | próximo={boot['proximo']}")
    while True:
        nodo = ex.rt_10_select()
        if nodo is None:
            break
        result = ex.execute_node(nodo, {})
        status = "✓" if result["status"] == "done" else "✗"
        print(f"  {status} {nodo.id} → {result['status']}")
    cierre = ex.rt_90_cierre()
    return 0 if cierre["status"] == "completed" else 1


def probar():
    """Corre los tests del runtime."""
    import subprocess
    result = subprocess.run(
        [sys.executable, "tests/test_runtime.py"],
        capture_output=True, text=True
    )
    print(result.stdout)
    if result.returncode != 0:
        print(result.stderr)
    return result.returncode


def main():
    parser = argparse.ArgumentParser(description="UOOS Parte 2 Runtime")
    parser.add_argument("--demo", action="store_true", help="Demo con 5 nodos dummy")
    parser.add_argument("--demo-n", type=int, default=5, help="Cantidad de nodos demo")
    parser.add_argument("--director", action="store_true", help="Pedir GO al Director")
    parser.add_argument("--from-b2", type=str, help="Importar desde B2_state.json")
    parser.add_argument("--probar", action="store_true", help="Correr tests del runtime")
    args = parser.parse_args()

    if args.demo:
        return demo(args.demo_n, args.director)
    if args.from_b2:
        return from_b2(args.from_b2)
    if args.probar:
        return probar()
    parser.print_help()
    return 1


if __name__ == "__main__":
    import os
    sys.exit(main())
