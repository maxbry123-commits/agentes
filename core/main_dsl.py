"""
main_dsl.py — CLI para ejecutar el DSL YAML.

Uso:
  python main_dsl.py --dsl dsl_ejemplo.yaml
  python main_dsl.py --dsl dsl_ejemplo.yaml --objetivo "construir API REST"
  python main_dsl.py --dsl dsl_ejemplo.yaml --chat
"""
import argparse
import json
import sys
import time


def chat_callback(msg: str):
    """Callback simple: imprime a stdout."""
    ts = time.strftime("%H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)


def main():
    parser = argparse.ArgumentParser(description="DSL Runtime para Orquestador Universal")
    parser.add_argument("--dsl", required=True, help="Ruta al archivo DSL YAML")
    parser.add_argument("--objetivo", type=str, help="Objetivo del workflow")
    parser.add_argument("--metas", type=str, help="Metas separadas por coma")
    parser.add_argument("--chat", action="store_true", help="Activa chat en vivo")
    parser.add_argument("--json", action="store_true", help="Output en JSON")
    args = parser.parse_args()

    user_input = {}
    if args.objetivo:
        user_input["objetivo"] = args.objetivo
    if args.metas:
        user_input["metas"] = [m.strip() for m in args.metas.split(",")]

    # importar después de los args
    from orchestrator.dsl import run_dsl

    cb = chat_callback if args.chat else None
    print(f"[main_dsl] Cargando DSL: {args.dsl}", file=sys.stderr)
    result = run_dsl(args.dsl, user_input=user_input, chat_callback=cb)

    if args.json:
        print(json.dumps(result, indent=2, default=str))
    else:
        print("\n" + "=" * 70)
        print(f"STATUS: {result.get('status')}")
        if result.get('status') == 'done':
            print(f"Loops completados: {len(result.get('completed_loops', []))}/{len(result.get('results', {}))}")
            for lid, lr in result.get('results', {}).items():
                st = lr.get('status', 'unknown')
                attempts = lr.get('attempts', 0)
                print(f"  {lid:30s} {st:12s} attempts={attempts}")
        elif result.get('status') == 'escalated':
            print(f"Loop que escaló: {result.get('loop_id')}")
        elif result.get('errors'):
            print("Errores de validación:")
            for e in result['errors']:
                print(f"  - {e}")
    return 0 if result.get('status') == 'done' else 1


if __name__ == "__main__":
    sys.exit(main())
