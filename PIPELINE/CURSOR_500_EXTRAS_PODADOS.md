# 500 extras Cursor — podados (alto valor)

**Base ya cubierta en Wordflow (no repetir):** COPY-FIRST, VerdictAuthority, llm DENY, smoke CI, WiringGraph básico, forensic contract, AGENTS/.cursor rules mínimos.

**Poda aplicada:** fuera de lista — compliance teatro, chaos genérico, multi-region, meeting/mob notes, legal hold, GPU offload, experiment design social, etc. Solo puntos que mejoran **editar code con agente + verificar + no romper**.  

**Extras = 500** (E001–E500).  
**Lista original 1–200:** `CURSOR_200_PUNTOS_AUSENTES_WORDFLOW.md` (algunos solapan; esta lista es la canónica de prioridad).

---

## E001–E050 Context útil
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

## E051–E100 Plan / blast radius
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

## E101–E150 Apply / edit safety
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

## E151–E200 Verify gates
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

## E251–E300 Git/PR hygiene
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

## E351–E400 Quality signals finos
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

## E401–E450 Stack gates (Python/JS realistas)
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

## E451–E500 Wordflow-specific upgrades (alto ROI)
E451 context_verified default **False** until handoff proof  
E452 handoff_verified default **False**  
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

---

**Conteo:** 500 extras (E001–E500) podados a valor de programación con agente.  
**No incluidos a propósito:** chaos genérico, multi-region, compliance teatro, legal hold, mob/meeting theater, GPU, marketing DX puro sin gate.
