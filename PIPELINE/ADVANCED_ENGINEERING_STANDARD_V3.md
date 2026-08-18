# Advanced Engineering Standard V3 — Executable Core
**Fecha:** 2026-08-17  
**Responde a:** auditoría GPT (rules-as-labels → rules-as-controls)

## Qué se corrigió respecto a V2
| Hueco auditoría | Fix V3 |
|-----------------|--------|
| RULE-001 bands | <300 soft · 300–800 preferred · 801–1000 P2 · 1001–1500 P1 · >1500 P0 |
| RULE-003 cycles | DependencyGraph.find_cycles_module_level |
| RULE-004 forbidden imports | DependencyGraph.forbidden_hits + manifest |
| RULE-008 evidence | EvidencePacket + is_complete |
| RULE-010 arch machine | ArchitectureManifest + RuleEngine collectors |
| QualityDAG SKIP→PASS | required gate sin handler = FAIL |
| Linear list | GateNode + depends_on (DAG) |
| GAPS_100 imposible | solo gaps **blocking** (P0/P1); P2 debt permitido |
| RuleId labels only | RuleEngine + register(collector) |

## Núcleo ejecutable
```
extensions/wordflow/standards/
  schema.py
  rule_engine.py      # collectors ejecutables
  architecture_manifest.py
  dependency_graph.py
  evidence.py
  quality_dag.py      # GateNode DAG + fail-closed
  sheriff.py          # facade
```

## Aún pendiente (V3.1+)
AgentPolicy · secret scanner real · SBOM · impact analysis full · parallel gate workers · ADR store · contract compatibility matrix · SLO.

## Uso
```python
from extensions.wordflow.standards import RuleEngine, EvidencePacket, QualityDAG

engine = RuleEngine()
verdict = engine.evaluate(
    file_locs={"a.py": 420},
    scan_paths=list(Path("extensions/wordflow").rglob("*.py")),
    gaps_blocking=0,
    claim_mvp=False,
    used_ai_as_proof=False,
)
assert verdict.passed
```
