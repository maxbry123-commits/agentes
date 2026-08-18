# ARQUITECTURA REAL — Wordflow Programming (post verificación cruzada)

**Fecha:** 2026-08-18  
**Base:** listado GitHub `extensions/wordflow/engine/` + `standards/` + `code_path_runner.py` + `forensic_core.py`  
**MASTER único (listas 1–500 / E001–E500):** `PIPELINE/WORDFLOW_PROGRAMMING_MASTER_UNICO.md`

**RESTAURADO desde commit 8507c486 (ANEXO Y 201–500 línea a línea). NO borrar este cuerpo.**

---

## 1. Capas

```
┌─────────────────────────────────────────────────────────────┐
│ Callers: bootstrap / smoke / CI / agente / (otros UNKNOWN)  │
└──────────────────────────────┬──────────────────────────────┘
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ ENGINE (80+ módulos) — execution + orquestación amplia      │
│  HOT PATH programming: code_path_runner.run_code_path       │
│  + quality_bar, goal_lock, cognitive_loop, evidence_packet  │
│  + skill_native_compiler, programming_pipeline              │
│  + resto: main_loop, orchestrator*, policy, handoff, …      │
└──────────────────────────────┬──────────────────────────────┘
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ STANDARDS — control plane forense / checklist / copy-first  │
│  forensic_core (PASS máquina C-19)                          │
│  + gap_registry, checklist_sheriff, catalog, applicability  │
│  + context_manifest, evidence_verifier, copy_first, …       │
└──────────────────────────────┬──────────────────────────────┘
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ DATA: component_catalog.json, connect_catalog.json          │
│ POLICY: PIPELINE/*, AGENTS.md, .cursor/rules, CI            │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. Lo que EJECUTA hoy `run_code_path` (código real)

Orden real en `engine/code_path_runner.py`:

1. `ForensicProgrammingEnforcer.require_context` → BLOCK si falta  
2. `admit_or_reject` (quality_bar)  
3. `lock_goals`  
4. `run_cognitive_loop`  
5. `compile_skill_to_code` (si skill)  
6. `build_evidence_packet` + `verify_evidence_packet` (engine)  
7. Construir CORE-01..14 desde `core_measures` (default **False**)  
8. Connectivity + ClosureCounters desde args  
9. `ForensicProgrammingEnforcer.evaluate`  
10. Return `ok`, `verdict`, `forensic`, `llm_control=DENY`  

### NO ejecuta hoy dentro de `run_code_path` (snapshot histórico §2)

- ChecklistSheriff  
- ContextManifest validator (solo bools context/handoff)  
- COPY-FIRST scanner  
- ExecutorPreImplementGate / PostVerifyGate  
- ClosureEngine (módulo existe; no llamado aquí)  
- GapRegistry (módulo existe; no instanciado aquí)  
- QualityDAG.run (solo flag `quality_dag_ok`)  
- FC-01..13 como checks obligatorios en `evaluate`  

**AS-IS code 2026-08-18:** ver ANEXO X (sí cableados).

---

## 3. Inventario STANDARDS (presentes en repo)

| Archivo | Rol |
|---------|-----|
| forensic_core.py | Enforcer CORE14 + 4-pass + counters + evaluate |
| forensic_contract.py | Contrato dataclass complementario |
| forensic_report.py | Render reporte |
| verdict_authority.py | Verdict formal |
| gap_registry.py | Lifecycle gaps |
| closure_engine.py | Árbitro CLOSED |
| checklist_sheriff.py | Sheriff puntos catálogo |
| programming_points_catalog.py | CORE/CONDITIONAL/ADVISORY/REFERENCE |
| applicability_engine.py | Tags → required |
| context_manifest.py | Manifest + validator |
| evidence_verifier.py | claim ≠ evidence resoluble |
| evidence.py | EvidencePacket standards |
| executor_gates.py | Pre/post gates |
| copy_first.py | Scanner reuse |
| symbol_index.py | AST symbols |
| wiring_graph.py | Catalog graph |
| test_runner.py | Smoke |
| quality_dag.py | DAG calidad |
| rule_engine.py | Rules |
| sheriff.py | Sheriff legacy/otro |
| schema.py | Schemas |
| adapt_imports.py | Rewrite imports |
| plan_artifact.py | Plan artifact |
| policy_snapshot.py | Freeze policy |
| architecture_manifest.py | Arch manifest |
| dependency_graph.py | Dep graph |
| mission_edges.py | Mission edges |
| scope_measure.py | Scope measure |
| path_resolve.py | Path resolve |
| quality_handlers.py | DAG handlers |
| fc_auto_measure.py | FC auto |
| core_auto_measure.py | CORE auto |
| evidence_merge.py | Dual evidence |
| __init__.py | Package |

---

## 4. Inventario ENGINE

### 4.1 Hot path
code_path_runner · code_path_smoke · programming_pipeline · programming_kwargs · input_quality_bar · goal_lock · cognitive_loop · evidence_packet · skill_native_compiler · main_loop

### 4.2 Bridges
claim_validator · control_sheriff_bridge · sheriff_adapter · handoff · dna_handoff · policy_engine · state_authority · execution_facade · execution_manifest · evidence_bridge · evidence_graph · cursor_hooks · enchufe_gate · repair_gate · validator

### 4.3 Orquestación
main_loop · orchestrator* · bootstrap · entrypoint* · scheduler · task_* · council · expert_* · capability_* · loop_bridge · wave* · runtime_bus · parallel_* · supervisor · sentinel · watchdog · recovery · circuit_breaker · retry_policy · github_api · resource_* · mission · bitacora · checkpoint_store · …

---

## 5–7. Matriz histórica / G1–G7 / PASS máquina

Ver ANEXO X para AS-IS. PASS: context∧handoff∧CORE14∧4pass∧counters0∧evidence∧reaudit∧quality_dag∧¬claim.

## 8. Enlaces
- Este doc · MASTER · CURSOR_200 · CURSOR_300 · CURSOR_500_EXTRAS · code_path_runner · forensic_core

---

# ANEXO X — AS-IS code (append, no borra §2)

Secuencia REAL: PolicySnapshot → ContextManifest → require_context → PreGate(COPY-FIRST+Sheriff) → adapt → quality_bar → goal_lock → cognitive → evidence_merge → QualityDAG → core/fc auto → GapRegistry → VerdictAuthority → ClosureEngine → DENY

---

# ANEXO Y — LISTA CURSOR 201–500 COMPLETA (300 ítems) — NO BORRAR

## I. Context engineering avanzado (201–240)
201. Sliding window de archivos por recencia de edición  
202. TF-IDF / embedding hybrid retrieval  
203. Symbol-level chunking (no file-level only)  
204. Call-graph neighborhood context (±N callers/callees)  
205. Type hierarchy context (parents/impls)  
206. Test twin file auto-attach  
207. Config twin (yaml/toml) auto-attach  
208. OpenAPI/schema twin auto-attach  
209. Recent CI failure correlation to files  
210. Bug report → file localization model  
211. Stack trace → frame mapping to source  
212. Profiling hotspot → file context  
213. Dependency version constraint context  
214. LICENSE header context  
215. CODEOWNERS of touched files in prompt  
216. Branch intent from name parsing  
217. Linked issue body in context  
218. Prior PR discussion threads  
219. Design doc section retrieval  
220. ADR retrieval by keyword  
221. Negative examples (anti-patterns) library  
222. Project glossary / ubiquitous language  
223. Domain dictionary injection  
224. Error code catalog injection  
225. API error map injection  
226. Feature flag list injection  
227. Env var catalog injection  
228. Queue/topic catalog injection  
229. DB schema subset retrieval  
230. Migration history context  
231. Permission matrix context  
232. Tenant isolation rules context  
233. Locale/i18n catalog awareness  
234. Accessibility ruleset injection  
235. Performance budget table injection  
236. Security checklist injection  
237. Privacy data-class labels  
238. Cost center / ownership tags  
239. SLA tier of endpoint context  
240. Deprecation schedule context  

## J. Multi-file reasoning (241–270)
241. File cluster detection before edit  
242. Consistency pass across cluster  
243. Rename cascade planner  
244. Interface change fan-out estimator  
245. Protocol/schema bump fan-out  
246. Shared constant extraction planner  
247. Duplicate code clone merge planner  
248. Layer violation auto-detect before apply  
249. Circular import forecast  
250. Public API surface delta report  
251. Internal-only API leakage detect  
252. Cross-language boundary (FFI) awareness  
253. Generated code region protect  
254. vendor/ third_party protect  
255. Lockfile regenerate step  
256. Protobuf/codegen step order  
257. GraphQL schema + resolvers co-edit  
258. Infra as code + app co-edit policy  
259. Mobile+API contract co-edit  
260. Docs+code co-edit requirement  
261. i18n keys+code co-edit  
262. Feature flag+code co-edit  
263. Metrics+code co-edit  
264. Dashboard JSON + backend co-edit  
265. Helm/values + service co-edit  
266. Terraform + IAM co-edit caution  
267. Migration + ORM model order  
268. Seed data + schema order  
269. Contract + mock server co-edit  
270. Changelog + version + tag order  

## K. Testing strategy Cursor-style (271–300)
271. Characterize legacy with characterization tests  
272. Approval tests  
273. Sociable vs solitary unit test choice  
274. Hexagonal test doubles policy  
275. In-memory fake vs mock policy  
276. Time provider injection test  
277. Random seed control  
278. Clock freeze helper  
279. HTTP clock/timeout tests  
280. Retry/backoff tests  
281. Circuit breaker tests  
282. Idempotency key tests  
283. Exactly-once vs at-least-once tests  
284. Poison message tests  
285. Backpressure tests  
286. Pagination edge tests  
287. Authz matrix tests  
288. Multi-tenant isolation tests  
289. GDPR delete cascade tests  
290. Encryption at rest tests  
291. Key rotation tests  
292. Feature flag off/on matrix  
293. Canary percentage tests  
294. Schema evolution tests  
295. Wire compatibility tests  
296. Snapshot redaction tests  
297. Load smoke k6/locust hook  
298. Chaos kill-pod hook (opt-in)  
299. Synthetic probe post-deploy  
300. Test data factory library gate  

## L. Refactor patterns (301–330)
301. Parallel change (expand/migrate/contract)  
302. Branch by abstraction  
303. Strangler facade  
304. Anti-corruption layer scaffold  
305. Walk skeleton micro-service  
306. Lift-and-shift checklist  
307. Extract module vertical slice  
308. Move to hexagonal steps  
309. Introduce domain events steps  
310. CQRS split checklist  
311. Read model rebuild plan  
312. Outbox pattern scaffold  
313. Inbox pattern scaffold  
314. Saga orchestration scaffold  
315. Process manager scaffold  
316. Retry storm prevention  
317. Bulkhead isolation  
318. Graceful degradation stubs  
319. Fail-open vs fail-closed choice record  
320. Cache invalidation plan  
321. Pagination migration  
322. Sync→async migration  
323. Polling→webhook migration  
324. Monolith extract module boundaries  
325. Shared lib versioning plan  
326. API gateway route add checklist  
327. BFF layer rules  
328. DTO vs domain model separation  
329. Mapping layer tests  
330. Null-object / option type migration  

## M. Code quality gates finos (331–360)
331. Cognitive complexity budget per function  
332. Nesting depth max  
333. Parameter count max  
334. Return paths max  
335. File cohesion score  
336. Feature envy detect  
337. Data clumps detect  
338. Long parameter list refactor suggest  
339. Shotgun surgery detect  
340. Divergent change detect  
341. Primitive obsession detect  
342. Speculative generality detect  
343. Dead store detect  
344. Unused public symbol detect  
345. Todo/Fixme budget  
346. Suppressions budget  
347. eslint-disable budget  
348. type:ignore budget  
349. Any-type budget  
350. Magic number budget  
351. Stringly-typed API detect  
352. God class score  
353. Feature toggles leftover detect  
354. Commented-out code detect  
355. Debug print detect  
356. Hardcoded URLs detect  
357. Hardcoded credentials detect (extra)  
358. Insecure deserialization detect  
359. SQL string concat detect  
360. Command injection detect  

## N. Python/JS stack specifics (361–390)
361. pyproject.toml consistency  
362. ruff format gate  
363. ruff lint gate  
364. mypy strict subset  
365. pyright config  
366. pytest markers taxonomy  
367. coverage.py fail_under  
368. pre-commit hooks  
369. dependabot/renovate config  
370. pip-audit / npm audit gate  
371. lockfile committed policy  
372. src-layout enforcement  
373. namespace packages  
374. __all__ export policy  
375. TYPE_CHECKING patterns  
376. Protocol/TypedDict usage  
377. pydantic models for boundaries  
378. dataclasses vs pydantic policy  
379. async session lifecycle  
380. httpx timeout defaults  
381. SQLAlchemy session scope  
382. alembic lint  
383. FastAPI dependency rules  
384. Next.js app router rules  
385. React hooks exhaustive-deps  
386. server/client component boundary  
387. CSP headers checklist  
388. bundle size budget  
389. tree-shaking check  
390. env schema with zod/pydantic  

## O. Collaboration & knowledge (391–420)
391. Decision log auto-append  
392. Meeting note → tasks  
393. RFC comment resolution tracker  
394. Design QA checklist  
395. Security review checklist  
396. Privacy review checklist  
397. Ops readiness checklist  
398. On-call annotation in PR  
399. Runbook link required for prod path  
400. Dashboard link required  
401. Alert rule link required  
402. SLO link required  
403. Error budget impact note  
404. Customer impact classification  
405. Support playbook update  
406. Docs versioning (semver docs)  
407. Screenshot/gif for UI PR  
408. Accessibility review notes  
409. i18n review notes  
410. Analytics event taxonomy update  
411. Experiment design doc  
412. Kill switch documented  
413. Rollout schedule  
414. Comms plan internal  
415. Postmortem template link  
416. Incident timeline export  
417. Learning goals for juniors  
418. Pairing notes  
419. Mob session record  
420. Knowledge base article draft  

## P. Agent evaluation & AI output quality (421–450)
421. Golden prompt suite  
422. Regression prompts on rules change  
423. LLM-as-judge offline (opt-in)  
424. Human rating of applies  
425. Accept rate metrics  
426. Undo rate metrics  
427. Escape hatch rate  
428. Hallucinated path detect  
429. Hallucinated API detect  
430. Import invent detect  
431. Nonexistent config key detect  
432. Wrong package version suggest detect  
433. License-incompatible suggest detect  
434. Copy-paste drift detect  
435. Style guide deviation score  
436. Comment quality score  
437. Naming consistency score  
438. Example snippet accuracy tests  
439. Docstring accuracy tests  
440. Type stub accuracy  
441. Multi-model consensus on risky edits  
442. Secondary model review pass  
443. Static proof obligations list  
444. Formal spec fragment optional  
445. Symbolic execution hook optional  
446. Differential testing vs old impl  
447. Shadow compare outputs  
448. Canary agent on non-prod  
449. Agent A/B prompt variants  
450. Prompt versioning registry  

## Q. Platform / Cursor product adjacent (451–480)
451. Background agent queue UI  
452. Agent notification on finish  
453. Agent cancel token  
454. Agent pause/resume  
455. Worktree isolation per agent  
456. Devcontainer agent target  
457. Remote SSH agent target  
458. Codespace agent target  
459. GPU task offload policy  
460. Browser tool allowlist  
461. Browser screenshot evidence  
462. Playwright generation policy  
463. Storybook story generation  
464. MSW handler generation  
465. OpenAPI client generation  
466. SQL migration generation policy  
467. Terraform plan parse  
468. Kubernetes manifest validate  
469. Dockerfile lint (hadolint)  
470. Compose policy  
471. SBOM generate on release  
472. Image CVE scan gate  
473. Supply chain attestations  
474. OIDC deploy auth  
475. Environment promotion UI  
476. Secrets manager integration  
477. Vault/OIDC short-lived tokens  
478. Feature store hooks (ML)  
479. Notebook to module extract  
480. Data contract tests (ML/data)  

## R. Governance residual (481–500)
481. Policy-as-code (OPA) hooks  
482. License allowlist merge gate  
483. Export control tags  
484. Data residency tags  
485. Retention policy tags  
486. Model card for AI features  
487. Eval dataset versioning  
488. Red team prompt suite  
489. Jailbreak regression suite  
490. Agent permission review board  
491. Periodic access recertification  
492. Third-party MCP security review  
493. Plugin allowlist  
494. Extension marketplace policy  
495. Telemetry privacy labels  
496. User consent records  
497. Audit export for compliance  
498. Legal hold freeze  
499. Break-glass timebox + post-review  
500. Policy change changelog  

**Conteo ANEXO Y: 300 puntos (201–500). NO BORRAR.**
**1–200:** `PIPELINE/CURSOR_200_PUNTOS_AUSENTES_WORDFLOW.md`  
**E001–E500:** `PIPELINE/CURSOR_500_EXTRAS_PODADOS.md`

**Fin ANEXO Y. Archivo restaurado desde 8507c486 + nota AS-IS X.**

---

# === APPEND COPY desde PIPELINE/_COPY_BLOB_0cf4f6a1_ARQUITECTURA_REAL.md (commit 47d1a49) ===
# Fuente blob: 0cf4f6a18515134b675fd44b93e2bf8780e20b72 — solo pegado al final, sin borrar arriba

# ANEXO X — VERIFICACIÓN CRUZADA CODE vs §§1–8 (2026-08-18) — SOLO APPEND

**Regla:** no se borró el cuerpo histórico §§1–8 ni anexos A–H. Este anexo **corrige el AS-IS** donde el code actual supera el texto de §2/§5.

## X.1 Secuencia REAL actual de `run_code_path` (code main)

```
0. PolicySnapshot.freeze → policy en return
1. ContextManifest validate (si require_context_manifest)
2. VerdictAuthority.require_context → BLOCK
3. ExecutorPreImplementGate (si require_pre_gate | symbol+dest)
   → COPY-FIRST + ChecklistSheriff (si checklist)
4. apply_adapt + post_adapt ast.parse (si apply_adapt)
5. admit_or_reject (thresholds en wire_trace)
6. lock_goals
7. run_cognitive_loop + skill compile opt
8. evidence_packet + evidence_merge
9. QualityDAG.run + quality_handlers (FORMAT/STATIC/LINT/UNIT/ARCH smoke)
10. core_auto_measure + fc_auto_measure
11. GapRegistry (gaps de pre_gate/FC)
12. VerdictAuthority.decide(state) → forensic_core.evaluate
13. ClosureEngine.decide
14. return ok, verdict, policy, wire_trace.stage_ms, llm_control=DENY,
    c_status/s_status/t_status/u_status
```

## X.2 Matriz §5 ACTUALIZADA (code vs claim §5 viejo)

| Capacidad | §5 decía | Code main ahora |
|-----------|----------|-----------------|
| Context BLOCK | Sí | **Sí** |
| ContextManifest | No | **Sí** (opt require_context_manifest) |
| ChecklistSheriff | No | **Sí** (vía PreGate + checklist) |
| COPY-FIRST | No | **Sí** (PreGate + apply_adapt) |
| CORE-01..14 | Sí caller | **Sí** + core_auto_measure |
| 4 passes | Sí | **Sí** |
| Connectivity | Sí | **Sí** |
| Counters | Sí | **Sí** + gaps registry |
| FC-01..13 en evaluate | No | **Sí** si require_fc o fc_results; auto parcial FA-02 |
| GapRegistry | No | **Sí** instanciado en runner |
| ClosureEngine | No | **Sí** llamado en runner |
| QualityDAG execute | Solo flag | **Sí** run + handlers; TYPE/BUILD aún CI |
| VerdictAuthority | — | **Sí** decide() |
| PolicySnapshot | — | **Sí** |
| Unified pipeline | — | **Sí** run_unified |
| main_12 programming_path | — | **Sí** |
| full_pass attestation | — | **Sí** ci_attestation |
| llm DENY | Sí | **Sí** |

## X.3 Inventario STANDARDS faltante en §3 (append nombres)

| Archivo | Rol |
|---------|-----|
| path_resolve.py | Resolve paths WF/REPO |
| quality_handlers.py | DAG handlers + smoke UNIT/ARCH |
| fc_auto_measure.py | FC auto conservador |
| core_auto_measure.py | CORE auto conservador |
| evidence_merge.py | Dual evidence engine+standards |
| checklist_factory.py | dict → AgentChecklistClaim |

## X.4 Inventario ENGINE faltante en §4.1

| Archivo | Notas |
|---------|-------|
| programming_kwargs.py | full_pass attested / minimal_block |
| programming_pipeline.py | **run_unified** (no solo helpers) |
| main_loop.py | programming_path / programming_full_pass |

## X.5 Deuda G1–G7 estado post-code

| ID | Estado |
|----|--------|
| G1 | Mitigado por este anexo + inventarios |
| G2 | **Cerrado en code** (Sheriff/COPY-FIRST cableados) |
| G3 | **Parcial cerrado** (evaluate FC + auto; resto caller) |
| G4 | Sigue doc-light en módulos mission_edges/scope_measure |
| G5 | Bridges siguen adyacentes; C-19 ya no solo bools |
| G6 | **Cerrado** evidence_merge |
| G7 | **Parcial** core_auto_measure existe; no finge 14×True |

## X.6 Gaps residuales honestos (no reabrir wire)

- TYPE / INTEGRATION / BUILD QualityDAG → CI `quality_dag_ok`
- FC-02/03/05/07/11/13 → caller/CI
- §2 texto histórico “NO ejecuta…” queda como **snapshot antiguo**; verdad operativa = **§X.1–X.2**

## X.7 Veredicto cruzado

```
CODE  ahead of ARCH §§2/5  →  ARCH actualizado por ANEXO X (append-only)
Wire gaps GC/GR/C/S/T/U/FA → CLOSED en code
PASS máquina §7           → sin cambio de ley
```

**Fin ANEXO X — verificación cruzada 2026-08-18.**
**Fuente commit:** 0cf4f6a18515134b675fd44b93e2bf8780e20b72
**Copia intermedia:** PIPELINE/_COPY_BLOB_0cf4f6a1_ARQUITECTURA_REAL.md

# === FIN APPEND 0cf4 ===
# Pendiente COPY append (mismo método): faa6d95 A+B+C · 0f19cb2 H1–H5 E001–E500
