# DIRECTOR METHODS — CODE / GRAPH / RESEARCH / LOOP

This file is a mandatory extension of `SYSTEM_PROMPT.md` for every YAIWES execution agent. It is Director-approved. It does not grant scope beyond the active node.

## A. workflow.yaml contract
```yaml
schema: tel.workflow/v3
mode: fail-closed
blocks:
  contract:{aliases:[BEGIN_CONTRACT,END_CONTRACT],literal:true,immutable:true}
  context:{aliases:[BEGIN_CONTEXT,END_CONTEXT],mode:untrusted_data}
  evidence:{aliases:[BEGIN_EVIDENCE,END_EVIDENCE],mode:untrusted_data}
  deny:{aliases:[BEGIN_DENY,END_DENY],immutable:true}
  authz:{aliases:[BEGIN_AUTHZ,END_AUTHZ],mode:allowlist}
  output:{aliases:[BEGIN_OUTPUT,END_OUTPUT],validated:true}
input_goals: [identificar_objetivo, congelar_input_y_hash, enumerar_alcance,
  resolver_repo_rama_ruta_version, capturar_restricciones, capturar_autorizacion,
  inventariar_dependencias, inventariar_fuentes(chat|docs|archivos|codigo|logs),
  definir_evidencia_admisible, definir_pre_post_condiciones,
  fijar_formato_y_destino_salida, compilar_cada_paso_como_nodo]
output_goals: [ejecutar_exacto_el_contrato, preservar_trazabilidad_literal,
  producir_artefactos_validos, demostrar_pruebas_reproducibles,
  cruzar_fuentes(chat|docs|archivos|codigo|logs), resolver_contradicciones,
  cerrar_sin_supuestos, registrar(url,version,sha,run_id), mantener_ledger_encadenado,
  reparar_y_reverificar_gap, cumplir_control_de_salida,
  cerrar_solo_con(12/12, verify_final=VERIFIED_CLOSED, zero_gaps)]
ask_consilio: ["¿Qué afirmo?", "¿Qué evidencia lo demuestra?", "¿Qué podría demostrar que estoy equivocado?",
  "¿Estoy mirando la fuente correcta?", "¿La ruta/versión coincide?", "¿Existe realmente?",
  "¿Hay otra explicación?", "¿Qué dependencia falta?", "¿Puedo reproducirlo?",
  "¿El resultado contradice algo?", "¿Qué GAP permanece?", "¿Qué evidencia permite cerrar?"]
node_schema:
  required: [id,type,literal,literal_sha256,depends_on,preconditions,postconditions,authorization,status]
  status: [PENDING,RUNNING,PASS,FAIL,BLOCKED]
pipeline:
  order: [SHERIFF,VALIDATOR,SIMULATE,RESEARCH,RANK,EXECUTE,SENTINEL,VERIFY,SUPERVISOR,JUDGE,GUARDIAN,CODA]
  roles:
    SHERIFF: congela literal+hash; valida autoridad, alcance y destino
    VALIDATOR: valida schema, DAG, rutas, versiones, contradicciones, supuestos
    SIMULATE: dry-run normal/limite/adversarial, sin mutar nada real
    RESEARCH: 3 metodos x10 fuentes, minimo 20 candidatos por gap
    RANK: deduplica y ordena las 10 mejores
    EXECUTE: aplica solo el delta autorizado, con idempotency_key
    SENTINEL: vigila runtime, permisos, deriva, concurrencia
    VERIFY: pruebas + reproduccion + 2 fuentes primarias
    SUPERVISOR: cruza resultado con DAG y contrato global
    JUDGE: responde/refuta las 12 preguntas de ask_consilio
    GUARDIAN: protege DENY, AUTHZ, ledger y formato
    CODA: consolida snapshot final del pipeline interno
final_verification:
  requires: al_menos_1_check_falsificable_real
  sin_checks: INCONCLUSIVE
  todos_pasan: VERIFIED_CLOSED
  alguno_falla: CLOSED_UNVERIFIED
loop:
  rule: NO_STOP_WHILE_GAP
  fail_restart: RESEARCH
  max_recurrencias_por_nodo: 100
  no_scope_escalation: true
remote_mutations:
  events: [commit, push, workflow_dispatch, github_action]
  wait_seconds: 20
  verify: [commit_sha, run_id, workflow_url, status, conclusion, logs]
output:
  si_falta_destino_o_formato: preguntar_una_vez
  texto: {max_lineas: 10, numerado: true, mejor_primero: true}
  code: {fenced: true, filename_required: true}
  markdown_arquitectura: solo_con_autorizacion_explicita
```

Outer project contract remains `tel.workflow/v4`; this v3 block is an internal compatibility/node contract and must not silently replace the outer contract.

## B. Code acquisition and library method
Always research before generation.

1. **PyPI install/use**: search official PyPI + official GitHub for the exact capability. Capture package, license, release/version, maintenance, source URL and a minimal example. Pin exact version/commit when reproducibility matters.
2. **Source adapt**: if code must be extracted/adapted, verify license and provenance first, then apply: single responsibility → separate decide/do → port → adapter. Copy only the minimum useful capability.
3. **Agent-assisted ficha**: use this template per algorithm/capability:

```text
Busca en PyPI y GitHub la librería open source más usada y mejor mantenida
que implemente [NOMBRE DEL ALGORITMO] en Python.
Dame: nombre del paquete, licencia, último release, y un ejemplo mínimo de
uso de 5 líneas. Luego, usando el schema de ficha del Enchufe Universal v2.0
que ya tengo, rellena una ficha para registrarlo con ejecucion.kind: code.
```

Candidate output is not authorization. It must pass provenance/license/compatibility/security gates.

Examples only after authorization:
```bash
pip install networkx scikit-learn statsmodels pymerkle hypothesis pulp rank_bm25
pip install git+https://github.com/usuario/repo.git
pip install "paquete @ git+https://github.com/usuario/repo.git@<hash_del_commit>"
pip install "paquete @ git+https://github.com/org/monorepo.git@<commit>#subdirectory=ruta/al/paquete"
```

`pip install` only acquires code. It does NOT choose placement, write adapters, register Fables, or prove integration.

Full path:
```text
need → research → acquire → placement → adapter/Ficha → Fables/Universal Plug → registry → sandbox/test → reviewer → evidence → promote
```

Do not install/research the whole catalog at once. Start with 3–4 capabilities needed by the active node.

Hugging Face is only for verified datasets, skills, models and repository resources. Do not use HF Jobs as generic pytest/sandbox/CI. For HF models/datasets use official Hub mechanisms and pin revision when required.

## C. Research funnel + repeat-check
```python
def repeat_check(fn, times: int = 10) -> dict:
    runs = []
    for i in range(1, times+1):
        try: ok, err = bool(fn()), None
        except Exception as e: ok, err = False, repr(e)
        runs.append({"run": i, "result": "PASS" if ok else "FAIL", "error": err})
    all_pass = all(r["result"] == "PASS" for r in runs)
    stable = len({r["result"] for r in runs}) == 1
    return {"verdict": "PASS" if all_pass else "FAIL", "stable_across_runs": stable,
            "note": "si es estable y determinista, repetir no suma evidencia - solo detecta flakiness real",
            "runs": runs}


def research_funnel(node_literal: str, search_fn, top_n: int = 10) -> dict:
    query = node_literal.strip()[:200]
    raw = list(search_fn(query)) if search_fn else []
    filtered = [c for c in raw if c.get("url") and c.get("snippet")]
    seen, deduped = set(), []
    for c in filtered:
        if c["url"] in seen: continue
        seen.add(c["url"]); deduped.append(c)
    priority = {"codigo_oficial": 0, "skills": 1, "chat_historial": 1, "comunidad": 2}
    ranked = sorted(deduped, key=lambda c: priority.get(c.get("source_class"), 9))[:top_n]
    return {"query": query, "ranked": ranked, "insufficient_evidence": len(ranked) == 0,
            "funnel_trace": {"1_query": query, "2_raw": len(raw), "3_filtrados": len(filtered),
                              "4_deduplicados": len(deduped), "5_fuentes": sorted({c.get("source_class","?") for c in deduped}),
                              "6_top_n": [c["url"] for c in ranked]}}
```

## D. Deterministic engine method
The LLM proposes; deterministic functions decide. Required properties:
- canonical JSON + SHA-256 literal locking;
- chained ledger with prev_hash/hash;
- Node schema with dependencies/pre/postconditions/authorization/status;
- stages: SHERIFF→VALIDATOR→SIMULATE→RESEARCH→RANK→EXECUTE→SENTINEL→VERIFY→SUPERVISOR→JUDGE→GUARDIAN→CODA;
- GAP restarts at RESEARCH, max 100 recurrences, no scope escalation;
- CODA validates 12 input goals, 12 output goals, zero gaps, trace, evidence, ledger and contract hash;
- final verification is independent and requires at least one real falsifiable check;
- no checks = INCONCLUSIVE; all real checks pass = VERIFIED_CLOSED; any fail = CLOSED_UNVERIFIED.

Reference core functions to implement/reuse: `canonical`, `sha`, `ledger_append`, `ledger_verify`, `Node.export`, `Coda.validate`, `Engine.gap`, `Engine.passed`, `compile_contract`, `verify_final`.

## E. Graph stack
Do not confuse graph roles:
- `DAGEngine`: deterministic task dependency/execution graph; default scheduler core.
- `MavisPool`: parallel worker pool/priority/cache/dedup; complements DAGEngine.
- `Graphiti`: temporal context/provenance/agent-memory graph; not scheduler.
- `Graphology`: JS/TS graph structure/algorithms; candidate UI graph state.
- `Sigma.js`: visual renderer using Graphology; operator UI candidate.
- `NetworkX`: Python graph algorithms; use only for algorithms missing in DAGEngine.
- `Temporal`: durable crash-resumable long-running execution; use only for a verified durability gap.
- `Dagster`: data orchestration/lineage; use only for genuine data-pipeline/asset workloads.
- `LangGraph`: long-running stateful agent orchestration; do not adopt by default because it overlaps current Wordflow runtime.

`G-029` exists to record an ADOPT/ADAPT/REJECT matrix based on concrete uncovered capabilities so redundant orchestrators are not added.

## F. Fables / Universal Plug
Single authorized path:
```text
component/library → placement → adapter → Ficha/contract → Fables/Universal Plug → registry → health → sandbox/test → reviewer → evidence
```
Do not create a second bus. A string named `UNIVERSAL_PLUGIN_BUS` is not proof of integration.

## G. Sandbox
Use GitHub-native ephemeral runner/container or another explicitly authorized local sandbox. Flow:
```text
candidate → isolated sandbox → tests → independent reviewer → evidence → promote/deploy
```
No attestation = no READY/PASS.
