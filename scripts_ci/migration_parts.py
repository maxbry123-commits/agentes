#!/usr/bin/env python3
"""
Single source of truth for the agentes -> Yaiwes migration, split into parts.

Each part lists (source_path_in_agentes, destination_path_in_Yaiwes) pairs.
A part is sized so one GitHub Actions runner can handle it comfortably.

Usage:
    python3 migration_parts.py sparse <part>   # print sparse-checkout paths
    python3 migration_parts.py list            # list all part names
"""
from __future__ import annotations
import sys

# Emoji-bearing paths are written with \\u escapes on purpose (literal emoji in
# source has caused GitHub API write failures).
WORDFLOW_SRC = u"➡️\U0001f4c2 wordflow loop code Yaiwes"
MOTORES_SRC = u"➡️\U0001f4c2motores de descarga extracción copiado movimiento archivos agentes"
CODA_SRC = u"\U0001f4c2coda workflow persistencias"
BITACORA_SRC = u"\U0001f4c2 Bitácora stated JSON Craxy wall.json"

CORE = u"Core kernel Yaiwes"

CORE_A = [
    "A2A-Protocol", "AIOS", "APScheduler", "AgentGuard", "AgentScope",
    "Apache-Airflow", "Backend watchdog workflow adaptativo", "Bayesian-Agent",
    "CAMEL", "Celery", "Claude-Code", "Cognithor", "CognitiveKernel-Pro",
    "Componentes recuperados A", "Componentes recuperados B", "Continual-Harness",
    "Crack wall bitácora stated JSON", "DR-WELL", "Dagster", "Dask-Distributed",
    "Download code Yaiwes", "Download code", "ERC-8004-Contracts", "EVOLVE-MEM",
    "Fast-Downward",
]

CORE_B = [
    "GTPyhop", "Godel-Agent", "Graph-of-Agents-GoA", "Graphiti", "GrayMatter",
    "Gymnasium", "Hermes-Agent", "HiRAS", "ISEK", "Interlat", "Kimi-K2.5",
    "LangGraph", "LatentMAS", "Letta", "Life-Harness", "LiteLLM", "LlamaFirewall",
    "MemForge", "MemOS", "MemRL", "Mesa", "Meta-Agent-Cookbook-2026",
    "Meta-Muse-Code-SDK-2026", "Meta-Muse-Glimmer-Agent-2026", "Metodo de trabajo",
    "Método de trabajo", "NetworkX", "OpenAgentd", "OpenClaw", "OpenCognit",
    "OpenFang",
]

CORE_C = [
    "OpenGuardrails", "OpenSwarm", "Oxios", "PRISM", "PettingZoo", "Prefect",
    "Provability-Fabric", "Pyperplan", "Qualixar-OS", "Ray", "ReMe",
    "Readme de integración de componentes arquitectura Yaiwes", "RecursiveMAS",
    "Refactoria", "RouteLLM", "SCOPE", "SPIRAL", "SafeDB-MCP", "SafeHarbor",
    "TASK-GAPS", "Temporal", "TencentDB-Agent-Memory", "TensorZero",
    "TimesFM-Native-Capability", "Unified-Planning", "Visa-Trusted-Agent-Protocol",
    "WooAgent-OS", "ZERA", "agente-yaiwes",
]

CORE_D = [
    "agents", "anydoc", "code-programming-engine", "control-layer", "deepeval",
    "deer-flow", "detect-secrets", "detoxify", "extensions", "faiss", "gatekeeper",
    "gpt-researcher", "great-expectations", "groups", "ipyhop", "llm-guard",
    "mabwiser", "memory", "nats-server", "omarchy", "omniroute", "openevolve",
    "orca", "py-trees", "pybreaker", "readme índice componentes", "scripts",
    "semgrep", "simple-pid", "tools", "wordflow", "workflows archivados 2026-09-04",
]

# Loose files sitting directly inside Core kernel Yaiwes (copied once, in core-a).
CORE_LOOSE = [
    "loop_catalog.json",
    "CORE-KERNEL-COMPONENT-INVENTORY.json",
    "CORE-KERNEL-COMPONENT-INVENTORY.md",
    "Crack wall bitácora stated JSON.md",
    "Readme de integración de componentes arquitectura Yaiwes.md",
    "readme-memoria.md",
]


def _core_pairs(subdirs, include_loose=False):
    pairs = []
    if include_loose:
        for f in CORE_LOOSE:
            pairs.append((CORE + "/" + f, CORE + "/" + f))
    for d in subdirs:
        pairs.append((CORE + "/" + d, CORE + "/" + d))
    return pairs


PARTS = {
    "agente-principal": [
        (u"Agente Yaiwes principal", u"Agente Yaiwes principal"),
    ],
    "core-a": _core_pairs(CORE_A, include_loose=True),
    "core-b": _core_pairs(CORE_B),
    "core-c": _core_pairs(CORE_C),
    "core-d": _core_pairs(CORE_D),
    "wordflow": [
        (WORDFLOW_SRC, u"wordflow loop code Yaiwes"),
        (u"arquitectura wordflow loop code Yaiwes", u"arquitectura wordflow loop code Yaiwes"),
    ],
    "resto": [
        (u"Skills agente", u"Skills agente"),
        (u"Skills", u"Skills"),
        (u"Conecciones router inteligente universal", u"Conecciones router inteligente universal"),
        (u"Documentos proyectos Yaiwes", u"Documentos proyectos Yaiwes"),
        (MOTORES_SRC, u"motores de descarga extraccion copiado movimiento archivos agentes"),
        (u"Readme arquitectura Yaiwes", u"Readme arquitectura Yaiwes"),
        (CODA_SRC, u"coda workflow persistencias (pendiente de integrar)"),
        (u".cursor", u".cursor"),
        (u".gitmodules", u".gitmodules"),
        (u"AGENTS.md", u"AGENTS.md"),
        (BITACORA_SRC, u"Bitacora-stated-JSON-Craxy-wall.json"),
        (u"Readme-Handoff-core-integracion-y-wachdog.md", u"Readme-Handoff-core-integracion-y-wachdog.md"),
        (u"Readme-arquitectura-Yaiwes-general.md", u"Readme-arquitectura-Yaiwes-general.md"),
        (u"Readme-plan-wachdog-y-trabajo-en-paralelo.md", u"Readme-plan-wachdog-y-trabajo-en-paralelo.md"),
        (u"PARCHE-RECUPERACION-CORE-INTEGRACION-WATCHDOG.md", u"PARCHE-RECUPERACION-CORE-INTEGRACION-WATCHDOG.md"),
        (u"INDICE-COMPONENTES-OPEN-SOURCE-YAIWES.md", u"INDICE-COMPONENTES-OPEN-SOURCE-YAIWES.md"),
    ],
}

# Known stale duplicate to drop from staging after copying (path under staging).
DROP_AFTER_STAGE = {
    "wordflow": [
        u"wordflow loop code Yaiwes/➡️\U0001f4c2 README arquitectura Wordflow LOOP Yaiwes.md",
    ],
}


def sparse_paths(part):
    """Paths to fetch from agentes for this part, plus the motors (motor_3)."""
    paths = [p[0] for p in PARTS[part]]
    paths.append(MOTORES_SRC)
    paths.append(u"scripts_ci")
    return paths


def main():
    if len(sys.argv) < 2:
        print("usage: migration_parts.py [sparse <part> | list]")
        return 1
    cmd = sys.argv[1]
    if cmd == "list":
        for name in PARTS:
            print(name + "\t" + str(len(PARTS[name])) + " items")
        return 0
    if cmd == "sparse":
        part = sys.argv[2]
        if part not in PARTS:
            sys.stderr.write("unknown part: " + part + "\n")
            return 1
        for p in sparse_paths(part):
            # git sparse-checkout --stdin expects one pattern per line
            print("/" + p)
        return 0
    sys.stderr.write("unknown command: " + cmd + "\n")
    return 1


if __name__ == "__main__":
    sys.exit(main())
