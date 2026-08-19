# FORENSE PASADA 02 — CONNECTIVITY

**Cadena máquina (forensic_core):**  
`DECLARED → REGISTERED → RESOLVED → INVOKED → EXECUTED → OUTPUT_CONSUMED → BEHAVIOR_VERIFIED`

Un archivo presente (pasada 1) no es eslabón cerrado.

---

## 1. Enlaces WIRED (import o llamada en code)

| Desde | Hacia | Evidencia |
|-------|-------|-----------|
| `wordflow_kernel.reception.convert` | `wordflow.reception.convert` | `_impl()` fail-closed |
| `handle_message` | `reception.ingest` / `locate` | actions convert/ingest/reception |
| `KernelExtMotor.dispatch` | `wordflow_kernel.reception` | ingest + locate (commit ed96d7d) |
| `code_path_runner` | `standards.forensic_core` + sheriff + QualityDAG + GapRegistry + ClosureEngine | imports reales |
| `code_path_runner` | `goal_lock`, `cognitive_loop`, `evidence_packet`, `input_quality_bar` | imports |
| `loop_bridge` | input_compiler, goals_compiler, goal_lock, echo, classifier, push_ping | imports |
| `maxbry_loop.GatewayModel` | `wordflow_kernel.gateway.intelligence` | `make_request` + `complete` |
| `bootstrap_fake` | `bootstrap_multi` + intento `lock_goals` + FakeGitDataPort | try/except |
| `plan_push` | reject force | T32 |
| `protected` | HOLD | T33 |
| `accounts.require` | `token_ref` | T38/T39 |

## 2. Enlaces STUB / Fake (firma sí, ejecución no real)

| Enlace | Qué hace |
|--------|----------|
| `IntelligenceGateway.complete` | `GATEWAY_STUB` |
| `engines/openclaw_stub` / `hermes_stub` | reason fake |
| `bootstrap_fake._code_path_dry` | **no llama** `run_code_path` |
| `loop_bridge.bridge_run_fake` | etapas intake/dry/loop_fake/publish_fake |
| `repo_truth.FakeRepoTruth` | verdad simulada |
| `router_slot/pipeline` | discover/map/select/load stubs |
| HF `resources/*` | PLAN_ONLY |
| Kimi/Minimax slot | `fusion: false` |

## 3. Enlaces GAP (doc/inbox lo pide, code no invoca)

| Declarado | Real |
|-----------|------|
| inbox: ubicar code en fase + PLUGIN | `convert` solo normaliza texto |
| `ingest.next` → `input_compiler`, `context_pack` | string en dict; **sin llamada** |
| `connect_catalog` viejo: loop → `run_code_path` | PARTIAL; loop no orquesta C-19 |
| `CONN.path_gateway` runner → gateway | runner **no** importa IntelligenceGateway |
| `WordflowKernel.audit_to_plan` | RuntimeError si no inject |
| `component_catalog` acquire_os path | directorio no en tree extensions |

## 4. Cadena reception (la que pediste cableada)

```
archivo en wordflow/reception/
        |
        v
convert.py (producto)  — WIRED impl
        ^
        | import fail-closed
        |
kernel/reception/convert.py  — WIRED LINK
        ^
        |
handle_message / KernelExtMotor  — WIRED dispatch
        |
        v
ingest() adjunta locate() + next[]  — EXECUTED hasta aquí
        |
        x  INPUT_COMPILER NO INVOKED
        x  FASE / PLUGIN NO EXECUTED
        x  OUTPUT_CONSUMED NO
```

**Verdict cadena reception:** se corta en RESOLVED/INVOKED del LINK. No llega a OUTPUT_CONSUMED de fase.

## 5. Cadena programming C-19

```
caller
  → run_code_path                    WIRED
    → require_context                WIRED (default False → BLOCK)
    → quality_bar / goal_lock        WIRED
    → cognitive_loop                 WIRED
    → evidence + QualityDAG          WIRED
    → VerdictAuthority.decide        WIRED
    → ClosureEngine                  WIRED
```

Callers de producción del runner: tests + smoke.  
`bootstrap_fake` **no** entra a esta cadena (dry).

## 6. Cadena LLM

```
maxbry_loop.GatewayModel.generate
  → gateway.complete                 WIRED
    → MockIntelligenceGateway        EXECUTED stub
    → RouterHTTPGateway              archivo existe; runtime depende ROUTER_URL
OpenAI/Anthropic desde loop          DENY por diseño
```

## 7. Duplicados (REGISTERED dos veces)

| Concepto | A | B | ¿Un consumidor único? |
|----------|---|---|------------------------|
| Reception | wordflow/reception | kernel/reception | LINK sí; motor ahora usa kernel |
| Goal bridge | maxbry_loop | kernel/bridge | NO |
| Stage hooks | maxbry_loop | kernel/stages | NO |
| Forense | audit_forensic | kernel + wordflow standards | NO |
| Publisher | engine/github_publisher | extensions/github_publisher | NO |
| Knowledge | extensions/knowledge | kernel/knowledge_index | NO |

## 8. Veredicto pasada 2

| Eslabón | Reception | C-19 | LLM | Deploy |
|---------|-----------|------|-----|--------|
| DECLARED | SÍ | SÍ | SÍ | SÍ |
| REGISTERED | SÍ | SÍ | SÍ | SÍ |
| RESOLVED | SÍ LINK | SÍ | SÍ | SÍ |
| INVOKED | SÍ handle/motor | solo callers C-19 | stub | Fake/HOLD |
| EXECUTED | convert only | sí si context | stub text | no publish |
| OUTPUT_CONSUMED | NO | caller | NO | NO |
| BEHAVIOR_VERIFIED | NO | tests parcial | mock tests | tests Fake |

**CONNECTIVITY sistema = FAIL** (varios eslabones WIRED; cadena completa no).  
CORE-07 REAL WIRING no se puede marcar True a nivel repo.
