# WORDFLOW PROGRAMMING — MASTER FULL 100%

**Idioma:** español (términos de code en inglés como en el repo)  
**Repo:** maxbry123-commits/agentes  
**Incluye:** sistema completo + listas **1–500** y **E001–E500** texto completo  

---

# BLOQUE 1 — SISTEMA (código y enforcement)

## 1.1 Qué es
Control plane fail-closed + path C-19 `run_code_path`. No es IDE. No auto-escribe git. LLM no declara PASS.

## 1.2 Paths
- Hot path: `extensions/wordflow/engine/code_path_runner.py`
- Enforcer: `extensions/wordflow/standards/forensic_core.py`
- Gaps: `extensions/wordflow/standards/gap_registry.py`
- Catálogo runtime: `extensions/wordflow/standards/programming_points_catalog.py`
- Sheriff: `checklist_sheriff.py` · Applicability · ContextManifest · EvidenceVerifier · copy_first · symbol_index · wiring_graph · test_runner · verdict_authority · closure_engine · executor_gates
- Data: `component_catalog.json`, `connect_catalog.json`
- Policy: PIPELINE/*, AGENTS.md, `.cursor/rules/wordflow-programming.mdc`, CI forensic-gates

## 1.3 Paso a paso
1 ContextManifest + validator  
2 context_verified + handoff_verified solo con prueba  
3 ApplicabilityEngine → required  
4 AgentChecklistClaim + EvidenceVerifier + ChecklistSheriff  
5 COPY-FIRST scan  
6 run_code_path  
7 quality_bar → goal_lock → cognitive_loop → evidence engine  
8 CORE-01..14 measures (default False)  
9 connectivity chain  
10 4 passes ordenadas  
11 counters todos 0  
12 evidence_complete + final_clean_reaudit + quality_dag_ok  
13 PASS o FAIL/BLOCK  
14 si FAIL: GapRegistry FIX→RE-AUDIT hasta new_gaps_after_fix=0 → CLOSED solo desde VERIFIED  

## 1.4 API run_code_path
context_verified=False, handoff_verified=False por defecto → BLOCK si no True.  
core_measures, connectivity, counters, evidence_complete, final_clean_reaudit_passed, quality_dag_ok.  
Sin bypass REQUIRED. llm_control=DENY.

## 1.5 CORE-01..14
REQUIREMENT, SCOPE/DIFF, IMPLEMENTATION, ARCHITECTURE, DEPENDENCY, CONTRACT, REAL WIRING, BEHAVIOR/EDGE, TEST EFFECTIVENESS, REGRESSION/IMPACT, ERROR PATH, CODE QUALITY, REPOSITORY TRUTH, EVIDENCE/VERDICT.

## 1.6 4 passes
STRUCTURE → CONNECTIVITY → BEHAVIOR → FORENSIC_CLOSURE (fail corta éxito de las siguientes).

## 1.7 Connectivity
DECLARED→REGISTERED→RESOLVED→INVOKED→EXECUTED→OUTPUT_CONSUMED→BEHAVIOR_VERIFIED

## 1.8 Counters (=0)
gaps, blocking_gaps, broken_connections, unexplained_orphans, unreachable_required_paths, unresolved_dependencies, unverified_paths, unverified_requirements, unverified_claims, pending_fixes, new_gaps_after_fix, unexpected_changes

## 1.9 Rules
CLAIM≠EVIDENCE≠VERIFICATION≠PASS · required_without_handler=FAIL · required_skip=FAIL · skip≠pass · OPEN→CLOSED forbidden · no_dev_bypass_required · NO VERIFIED CONTEXT → NO PROGRAMMING/AUDIT

## 1.10 Catálogo runtime (no 500 gates)
Ver `programming_points_catalog.py`: C-CTX/PLN/CPY/APL/VRF/WRD/GAP + K-* conditional + A-* advisory + R-* reference. CATALOG_VERSION=2.0.0

## 1.11 PASS máquina
context∧handoff∧CORE14∧4passes∧counters0∧evidence∧final_reaudit∧quality_dag∧¬claim_as_pass

---

# BLOQUE 2 — LISTA COMPLETA 1–200

## A. Workspace & context (1–25)
1. Index semántico tipo codebase chat con ranking de relevancia  
2. @file / @folder scope explícito por turno  
3. @codebase query con límites de tokens  
4. @docs / @web grounding opcional con citas  
5. @git diff como contexto de tarea  
6. @commit messages como contexto  
7. Rules por glob con prioridad  
8. Rules not-applied telemetry  
9. Project memory corta vs larga  
10. Sticky intent across turns  
11. Auto-attach open tabs  
12. Auto-attach active selection  
13. Ignore patterns (.cursorignore) enforced  
14. Binary/large file exclusion  
15. Secrets redaction in context  
16. Context budget meter  
17. Context pin/unpin files  
18. Multi-root workspace index  
19. Monorepo package boundary awareness  
20. Language server symbols in context  
21. Type error context from diagnostics  
22. Linter diagnostics as input  
23. Test failure logs as input  
24. Terminal last command output as input  
25. Debug breakpoint context  

## B. Planning (26–45)
26. Plan mode obligatorio antes de multi-file  
27. Plan artifact reviewed by human  
28. Plan step checkboxes  
29. Plan → task graph  
30. Estimate blast radius in plan  
31. Plan risk score  
32. Plan requires test strategy  
33. Plan requires rollback strategy  
34. Plan links to ADR  
35. Plan frozen hash  
36. Re-plan on requirement change  
37. Parallel vs serial step marking  
38. Human approval gate mid-plan  
39. Max steps per plan  
40. Plan diff against previous plan  
41. Definition of done in plan  
42. Non-goals section enforced  
43. Acceptance criteria machine-checked  
44. Dependency order of edits  
45. Dry-run plan without writes  

## C. Edit application (46–75)
46. Inline diff view per hunk  
47. Accept/reject hunk  
48. Accept file / reject file  
49. Multi-file transaction apply  
50. Atomic apply rollback  
51. Apply only staged AI hunks  
52. No apply without plan id  
53. Path allowlist for writes  
54. Path denylist (secrets, vendor)  
55. Max files per apply  
56. Max LOC delta per apply  
57. Max churn percent per file  
58. Protect main/master branch  
59. Require feature branch  
60. Block edit on dirty unrelated files  
61. Format-on-apply  
62. Organize imports on apply  
63. Code action auto-fix  
64. Rename symbol refactor (LSP)  
65. Extract method refactor  
66. Move file + update imports  
67. Safe delete with reference check  
68. Generate stub + TODO gate  
69. Snippet expansion controlled  
70. Template file from skeleton  
71. Partial apply with residual markers  
72. Conflict detect with local edits  
73. 3-way merge AI vs user vs base  
74. Undo AI apply stack  
75. Redo AI apply stack  

## D. Verification (76–100)
76. Run nearest test on save  
77. Run affected tests only (test impact)  
78. Coverage delta gate  
79. Typecheck gate  
80. Lint gate  
81. Format check gate  
82. Import cycle gate on apply  
83. Dead code gate  
84. Complexity delta gate  
85. Mutation test sample  
86. Snapshot test update policy  
87. Visual regression (UI)  
88. Contract test consumers  
89. Property-based tests hook  
90. Fuzz smoke optional  
91. Benchmark regression  
92. Memory leak smoke  
93. Race detector optional  
94. Integration test env spinup  
95. Ephemeral DB fixture  
96. HTTP mock server fixture  
97. Golden file review  
98. Flake quarantine  
99. Test timeout policy  
100. Fail-fast vs full suite policy  

## E. Git / PR (101–125)
101. Auto branch name from task  
102. Conventional commits  
103. Commit split by concern  
104. PR template fill  
105. PR description from diff  
106. PR linked to issue/task  
107. Required reviewers CODEOWNERS  
108. Label risk high/medium/low  
109. CI status required green  
110. Merge queue  
111. Squash policy  
112. Signed commits  
113. Commit GPG/SSH verify  
114. Protected paths CODEOWNERS  
115. Draft PR first  
116. Stacked PRs  
117. Cherry-pick assistant  
118. Rebase assistant  
119. Conflict resolution assistant gated  
120. Changelog fragment  
121. Version bump suggestion  
122. Release notes draft  
123. Tag creation policy  
124. Revert PR one-click policy  
125. Post-merge verify job  

## F. Agent authority & safety (126–150)
126. Tool permission prompts  
127. Network allowlist  
128. Shell command allowlist  
129. No sudo policy  
130. Sandbox FS for agent  
131. Read-only mode  
132. Ask mode vs Agent mode  
133. Yolo/auto-apply off by default  
134. Confirmation on destructive ops  
135. Rate limit tool calls  
136. Max agent turns  
137. Max tool failures then stop  
138. Prompt injection filters  
139. Untrusted instruction quarantine  
140. Model pin per project  
141. Temperature policy  
142. System prompt checksum  
143. Tool result size limit  
144. Exfiltrate path block  
145. PII redaction  
146. Audit log of tool calls  
147. Replay tool session  
148. Agent session export  
149. Multi-agent isolation  
150. Supervisor agent veto  

## G. Architecture & design (151–170)
151. Arch unit test (fitness functions)  
152. Layer rule tests  
153. Package dependency matrix  
154. No-new-cyclic-deps gate  
155. Port/adapter presence test  
156. Domain purity test  
157. ADR required for layer breach  
158. RFC template  
159. Design doc review gate  
160. API first OpenAPI  
161. Schema-first protobuf/JSON Schema  
162. Backward compat checker  
163. Feature flag scaffolding  
164. Strangler pattern checklist  
165. Data migration dry-run  
166. Expand/contract migration  
167. Shadow traffic hook  
168. Canary config stub  
169. SLO impact note  
170. Threat model checkbox  

## H. DX / Cursor product loops (171–200)
171. Composer multi-file oriented UI state  
172. Chat-to-apply continuity  
173. Checkpoint code timeline  
174. Restore checkpoint  
175. Image/mock UI to code  
176. Terminal agent mode  
177. Background agent jobs  
178. Bugbot-style review comments  
179. Inline AI chat on selection  
180. Docstring/gen tests from symbol  
181. Explain code panel  
182. Fix from diagnostics one-click  
183. Generate PR from chat  
184. Notion/Linear task sync  
185. MCP tool registry  
186. MCP allowlist  
187. Custom modes (review/refactor/test)  
188. Memories user-level vs project  
189. Privacy mode (no train/retain)  
190. Usage/cost dashboard per session  
191. Fast vs slow model routing  
192. Tab autocomplete accept metrics  
193. Next-edit suggestion  
194. Peek definition assisted  
195. Symbol search AI ranked  
196. Shared team rules sync  
197. Rules lint (invalid frontmatter)  
198. Extension conflict detection  
199. Workspace trust model  
200. Update channel / rule version pin  

---

# BLOQUE 3 — LISTA COMPLETA 201–500

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

## N. Python/JS stack (361–390)
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

## O. Collaboration (391–420)
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

## P. Agent evaluation (421–450)
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

## Q. Platform (451–480)
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

## R. Governance (481–500)
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

**Conteo bloque 2+3:** 500 puntos (1–500).

---

# BLOQUE 4 — LISTA COMPLETA E001–E500 (PODADA ROI)

## E001–E050 Context
E001 @file scope obligatorio en multi-file  
E002 @folder scope  
E003 @git diff como contexto de tarea  
E004 Diagnostics LSP en contexto  
E005 Test failure log en contexto  
E006 Stack trace → source map  
E007 Call-graph ±N callers/callees  
E008 Test-twin auto-attach  
E009 Config-twin auto-attach  
E010 Schema/OpenAPI twin  
E011 .cursorignore enforced  
E012 Secrets redaction in context  
E013 Context budget meter  
E014 Pin/unpin files  
E015 Multi-root index  
E016 Package boundary awareness  
E017 Recent CI failure → files  
E018 CODEOWNERS of touched files  
E019 Linked issue/task body  
E020 ADR retrieval by keyword  
E021 Design doc section retrieval  
E022 Glossary / domain terms  
E023 Error code catalog  
E024 Env var catalog  
E025 Feature flag list  
E026 Deprecation schedule  
E027 Generated code regions protect  
E028 vendor/ third_party protect  
E029 Negative examples library  
E030 Symbol-level chunks  
E031 Type hierarchy context  
E032 Import graph neighborhood  
E033 Diff hunks only (not whole files)  
E034 Open editors auto-weight  
E035 Active selection priority  
E036 Terminal last exit code + snippet  
E037 Pre-commit failure snippet  
E038 Type error burst summary  
E039 Lint burst summary  
E040 Lockfile context when deps change  
E041 Migration history when schema change  
E042 Permission matrix when auth change  
E043 Public API surface snapshot  
E044 Internal API leakage hints  
E045 Clone detection hints  
E046 Dead export hints  
E047 TODO/FIXME near edit  
E048 Suppressions near edit  
E049 Related PR conversations  
E050 Branch name intent parse  

## E051–E100 Plan
E051 Plan mode before multi-file  
E052 Human-readable plan artifact  
E053 Plan frozen hash  
E054 Non-goals section  
E055 Acceptance criteria list  
E056 Blast radius estimate  
E057 Risk score  
E058 Test strategy in plan  
E059 Rollback strategy in plan  
E060 Order of edits  
E061 Dry-run without writes  
E062 Max steps per plan  
E063 Re-plan on requirement change  
E064 Parallel vs serial steps  
E065 Mid-plan approval gate  
E066 File cluster before edit  
E067 Fan-out on interface change  
E068 Fan-out on schema change  
E069 Rename cascade plan  
E070 Co-edit docs+code rule  
E071 Co-edit tests+code rule  
E072 Co-edit i18n+code rule  
E073 Co-edit flag+code rule  
E074 Lockfile regenerate step  
E075 Codegen order (proto/openapi)  
E076 Migration before ORM use  
E077 Contract before mock update  
E078 Version bump plan  
E079 Changelog fragment plan  
E080 ADR link if layer breach  
E081 No-touch-core checklist  
E082 Allowlist paths in plan  
E083 Denylist paths in plan  
E084 Max files in plan  
E085 Max LOC delta in plan  
E086 Definition of done machine-checkable  
E087 Explicit GENERATE vs ADAPT choice  
E088 Explicit COPY sources list  
E089 Evidence expected list  
E090 Post-conditions list  
E091 Invariants list  
E092 Error-path plan  
E093 Observability plan (logs/metrics)  
E094 Security notes if trust boundary  
E095 Data model notes if persistence  
E096 Concurrency notes if shared state  
E097 Idempotency notes if side effects  
E098 Performance notes if hot path  
E099 Compat notes if public API  
E100 Exit criteria for stop/replan  

## E101–E150 Apply
E101 Path allowlist writes  
E102 Path denylist writes  
E103 Max files per apply  
E104 Max LOC delta per apply  
E105 Max churn % per file  
E106 Require feature branch  
E107 Block apply on protected branch  
E108 Atomic multi-file apply  
E109 Rollback apply  
E110 Undo stack AI applies  
E111 Hunk accept/reject  
E112 File accept/reject  
E113 Format-on-apply  
E114 Lint-fix-on-apply optional  
E115 Organize imports on apply  
E116 Conflict detect vs local edits  
E117 3-way merge base/user/AI  
E118 Protect generated regions  
E119 No write secrets files  
E120 No write .env  
E121 Paired test touch rule  
E122 Paired snapshot policy  
E123 Rename via LSP  
E124 Move file + imports  
E125 Safe delete refcheck  
E126 Partial apply markers  
E127 No silent drop of user edits  
E128 Apply only under plan id  
E129 Reject apply if plan hash mismatch  
E130 Stage vs apply separation  
E131 Worktree isolation optional  
E132 Dirty tree policy  
E133 Generated lockfile policy  
E134 Binary file write deny  
E135 Large file write deny  
E136 Symlink write policy  
E137 Line-ending policy  
E138 License header preserve  
E139 Copyright preserve  
E140 Encoding utf-8 enforce  
E141 No reformat unrelated hunks  
E142 Minimize diff policy  
E143 Single concern per apply  
E144 Split applies by concern  
E145 Require description per apply  
E146 Link task id per apply  
E147 Record SOURCE→DEST on copy  
E148 Record import rewrites  
E149 Post-apply file list evidence  
E150 Post-apply hash list  

## E151–E200 Verify
E151 Typecheck gate  
E152 Lint gate  
E153 Format check gate  
E154 Unit tests affected  
E155 Integration tests opt-in  
E156 Coverage delta gate  
E157 Import cycle gate  
E158 Dead code gate  
E159 Complexity delta gate  
E160 Secret scan gate  
E161 Dep audit gate on new deps  
E162 License gate on new deps  
E163 Lockfile drift gate  
E164 Schema compat gate  
E165 OpenAPI diff gate  
E166 Contract consumer tests  
E167 Snapshot review policy  
E168 Flake quarantine  
E169 Test timeout policy  
E170 Fail-fast policy  
E171 Smoke post-apply  
E172 Build gate  
E173 Package import smoke  
E174 Entrypoint smoke  
E175 Migration dry-run  
E176 Idempotency tests if side effects  
E177 Concurrency tests if shared state  
E178 Authz matrix if auth  
E179 Input validation tests  
E180 Error path tests  
E181 Characterization tests legacy  
E182 Differential test old vs new  
E183 Golden file policy  
E184 Benchmark on hot path opt-in  
E185 Bundle size if frontend  
E186 a11y smoke if UI  
E187 i18n missing keys if UI  
E188 CSP/headers if web  
E189 Dockerfile lint if docker  
E190 Compose validate if compose  
E191 Terraform validate opt-in  
E192 K8s manifest validate opt-in  
E193 SBOM on release only  
E194 CVE scan on release only  
E195 CI required green  
E196 Local pre-push hooks  
E197 Pre-commit hooks  
E198 Gate skip ≠ pass  
E199 Required gate missing = fail  
E200 Evidence packet after gates  

## E201–E250 Agent authority
E201 Ask mode default  
E202 Agent mode explicit  
E203 Auto-apply off default  
E204 Tool allowlist  
E205 Shell allowlist  
E206 Network allowlist  
E207 No sudo  
E208 Read-only mode  
E209 Max tool calls  
E210 Max turns  
E211 Max failures then stop  
E212 Confirm destructive ops  
E213 Prompt injection filters  
E214 Untrusted doc quarantine  
E215 Model pin  
E216 Temperature policy  
E217 System prompt checksum  
E218 Tool result size limit  
E219 Path exfil block  
E220 PII redaction  
E221 Audit log tool calls  
E222 Session export  
E223 Replay session  
E224 Supervisor veto  
E225 Multi-agent isolation  
E226 MCP allowlist  
E227 MCP security review  
E228 Plugin allowlist  
E229 Rate limit  
E230 Cost budget per task  
E231 Token budget per task  
E232 Fast/slow model routing  
E233 Secondary review model opt-in  
E234 Hallucinated path detect  
E235 Hallucinated symbol detect  
E236 Invented import detect  
E237 Invented config key detect  
E238 Copy-paste drift detect  
E239 Style deviation score  
E240 Naming consistency check  
E241 Prompt version registry  
E242 Rules version pin  
E243 Policy snapshot per task  
E244 Change_id required  
E245 Mission_id required  
E246 Task_id required  
E247 Human gate on high risk  
E248 Risk from secrets/auth/data  
E249 Deny prod credentials in agent  
E250 Sandbox FS for agent applies  

## E251–E300 Git/PR
E251 Conventional commits  
E252 Commit split by concern  
E253 PR template  
E254 PR body from diff  
E255 Link task in PR  
E256 CODEOWNERS reviewers  
E257 Risk labels  
E258 Draft PR first opt-in  
E259 CI green required  
E260 Signed commits opt-in  
E261 Protected paths  
E262 Changelog fragment  
E263 Version bump suggestion  
E264 Revert policy  
E265 Post-merge smoke  
E266 Branch naming from task  
E267 No commit secrets  
E268 No force push main  
E269 Merge queue opt-in  
E270 Squash policy explicit  
E271 Conflict resolution gated  
E272 Stacked PR support opt-in  
E273 Release notes draft opt-in  
E274 Tag policy  
E275 PR size soft limit  
E276 PR file count soft limit  
E277 Require tests in PR when code  
E278 Require docs in PR when API  
E279 Screenshot if UI  
E280 A11y note if UI  
E281 Migration note if schema  
E282 Feature flag note if progressive  
E283 Rollback note if prod  
E284 Owner mention  
E285 Review SLA opt-in  
E286 Automark stale PR  
E287 Block merge on TODO critical  
E288 Block merge on failed gates  
E289 Require approval N  
E290 Dismiss stale approvals on new push  
E291 CODEOWNERS for standards/  
E292 CODEOWNERS for kernel/  
E293 Binary in PR deny  
E294 Large blob deny  
E295 Submodule policy  
E296 Vendored code policy  
E297 Generated code mark  
E298 PR checklist machine-verified subset  
E299 Link forensic report if code task  
E300 Link plan hash in PR  

## E301–E350 Architecture fitness
E301 Layer rule tests  
E302 No new cyclic deps  
E303 Package dependency matrix  
E304 Domain purity test  
E305 Ports/adapters presence  
E306 Forbidden imports test  
E307 Public API delta report  
E308 Semver suggest on public break  
E309 ADR on layer breach  
E310 Fitness: no touch core  
E311 Module LOC budget soft  
E312 Fan-out budget soft  
E313 Fan-in budget soft  
E314 Stable dependency principle check  
E315 Acyclic dependency principle check  
E316 Boundary test for engine vs standards  
E317 Boundary test kernel vs engine  
E318 Catalog entry required for new component  
E319 Connect catalog edge required when wired  
E320 Orphan component report  
E321 Unreachable path report  
E322 Dead export report  
E323 Duplicate module report  
E324 Naming law for packages  
E325 Event/DTO versioning  
E326 Schema expand/contract  
E327 Feature flag for new path  
E328 Deprecation window  
E329 Remove flag deadline  
E330 Architecture test in CI  
E331 Import linter config  
E332 Dependency cruiser/equivalent  
E333 Code city metrics opt-in  
E334 Hotspot files report  
E335 Churn vs complexity report  
E336 Knowledge concentration report  
E337 Bus factor soft signal  
E338 Owned modules map  
E339 Experimental folder policy  
E340 Deprecated folder policy  
E341 Examples/ treated as tests  
E342 Scripts/ policy  
E343 Tools/ policy  
E344 Generated/ policy  
E345 Third_party/ policy  
E346 Docs must reference paths real  
E347 PIPELINE links must resolve  
E348 No doc-only architecture claims without path  
E349 Arch diagram auto from catalogs  
E350 Arch drift bot comment on PR  

## E351–E400 Quality signals
E351 Cognitive complexity budget  
E352 Nesting depth max  
E353 Param count max  
E354 File cohesion  
E355 Feature envy detect  
E356 God class score  
E357 Magic number budget  
E358 Any-type budget  
E359 type:ignore budget  
E360 lint-disable budget  
E361 TODO budget  
E362 Commented-out code detect  
E363 Debug print detect  
E364 Hardcoded URL detect  
E365 SQL concat detect  
E366 Command injection detect  
E367 Insecure deserialization detect  
E368 Path traversal detect  
E369 SSRF detect opt-in  
E370 XSS sink detect opt-in  
E371 Pickle/eval detect  
E372 Assert as control flow detect  
E373 Bare except detect  
E374 Mutable default arg detect  
E375 Resource leak detect  
E376 File handle close detect  
E377 Timeout missing detect  
E378 Retry without jitter detect  
E379 Busy wait detect  
E380 N+1 query detect opt-in  
E381 Unbounded list load detect  
E382 Missing pagination detect  
E383 Naive datetime detect  
E384 Timezone bug patterns  
E385 Float money detect  
E386 UUID/string id confusion  
E387 Enum stringify drift  
E388 Dict key typo risk  
E389 Optional not handled  
E390 Race on shared dict detect  
E391 Lock ordering notes  
E392 Async cancel safety  
E393 Task group hygiene  
E394 Context manager required  
E395 Idempotent handler patterns  
E396 Exactly-once claims banned without proof  
E397 At-least-once dual process notes  
E398 Poison message handling  
E399 Backpressure handling  
E400 Graceful shutdown hooks  

## E401–E450 Stack
E401 ruff format  
E402 ruff lint  
E403 mypy/pyright subset  
E404 pytest markers taxonomy  
E405 coverage fail_under  
E406 pre-commit  
E407 pip-audit/npm audit on dep change  
E408 lockfile committed  
E409 src layout  
E410 pydantic/zod at boundaries  
E411 httpx timeout defaults  
E412 SQLAlchemy session scope  
E413 alembic lint  
E414 FastAPI deps rules  
E415 React hooks deps  
E416 server/client component boundary  
E417 env schema validated  
E418 no process.env scattered  
E419 structured logging  
E420 request id propagation  
E421 OpenTelemetry hooks opt-in  
E422 health endpoint  
E423 readiness endpoint  
E424 metrics endpoint  
E425 graceful timeout config  
E426 docker non-root user  
E427 .dockerignore present  
E428 multi-stage build  
E429 pin base images  
E430 no latest tags in prod  
E431 CI cache deps  
E432 CI matrix py versions opt-in  
E433 CI artifact upload evidence  
E434 determinism seed in tests  
E435 freezegun/clock inject  
E436 respx/httpx mock policy  
E437 factory_boy/fixtures policy  
E438 hypothesis opt-in  
E439 snapshot library policy  
E440 typescript strict opt-in  
E441 eslint  
E442 prettier  
E443 no-floating-promises  
E444 exhaustiveness checks  
E445 import type discipline  
E446 side-effects free modules  
E447 barrel files policy  
E448 circular via barrels detect  
E449 tree-shaking friendly exports  
E450 bundle analyzer on budget exceed  

## E451–E500 Wordflow ROI
E451 context_verified default False until handoff proof  
E452 handoff_verified default False  
E453 git diff based scope measure  
E454 unexpected_changes from git status  
E455 post_verify cannot set core True without measure  
E456 mission-specific edge injection API  
E457 GapRegistry runtime persist  
E458 gap OPEN→FIXED→VERIFIED→CLOSED enforced  
E459 forbid OPEN→CLOSED in code  
E460 FourPassController real independent passes  
E461 code_path applies COPY when plan says ADAPT auto-option  
E462 wire adapt_imports in pipeline  
E463 symbol index disk cache  
E464 multi-repo roots from reception manifest  
E465 reception docs auto index for context  
E466 PolicySnapshot auto at run start  
E467 PlanArtifact auto at multi-file  
E468 PR SHA in EvidencePacket  
E469 run ledger mission_id/task_id/change_id  
E470 catalog snapshot hash in evidence  
E471 verdict baseline compare previous commit  
E472 arch fitness tests in CI  
E473 forbidden import tests in CI  
E474 cycle tests in CI  
E475 code_path_runner caller inventory doc generated  
E476 cognitive_loop classified DETERMINISTIC|LLM in evidence  
E477 quality_bar rules documented + tested  
E478 goal_lock rules documented + tested  
E479 consumer of run_code_path return dict verified  
E480 fail if enforce_post_verify False in prod profile  
E481 prod profile vs dev profile gates  
E482 write allowlist extensions/wordflow/** default  
E483 deny write PIPELINE via agent without doc task flag  
E484 paired test for new engine module  
E485 component_catalog entry gate for new engine file  
E486 connect_catalog edge gate when claiming wired  
E487 orphan report in CI  
E488 unreachable required path report  
E489 SOURCE→DEST required if ADAPT  
E490 regenerate claim blocked if hash match existing  
E491 human gate if risk auth/secrets  
E492 prompt injection scan on raw_input  
E493 untrusted reception markdown sandbox  
E494 model pin in instance config  
E495 cost/token fields in run result  
E496 stage timings in run result  
E497 structured log sink optional  
E498 forensic report artifact path in return  
E499 AGENTS.md test: links resolve  
E500 .cursor/rules test: frontmatter valid  

**Conteo E:** 500 (E001–E500).

---

# BLOQUE 5 — CÓMO SE RELACIONAN LAS LISTAS CON EL RUNTIME

```
1–500 + E001–E500  = DATASET / guía / gaps potenciales
        ↓
ApplicabilityEngine + programming_points_catalog (subset)
        ↓
ChecklistSheriff (required + evidence)
        ↓
forensic_core CORE-01..14 + 4-pass + counters
        ↓
run_code_path verdict
```

No se programan 500/1000 gates. Sí se exige que el agente use el catálogo de forma determinista y el enforcer no acepte claim como PASS.

---

**FIN MASTER FULL.**  
Sistema + **500 puntos 1–500** + **500 extras E001–E500** en un archivo.
