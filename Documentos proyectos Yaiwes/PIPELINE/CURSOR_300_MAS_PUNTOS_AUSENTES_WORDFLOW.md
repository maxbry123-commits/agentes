# +300 puntos Cursor / agent-IDE AUSENTES en Wordflow (201–500)

**Complemento de:** `PIPELINE/CURSOR_200_PUNTOS_AUSENTES_WORDFLOW.md` (1–200)  
**Total acumulado si se unen:** 500 puntos de gap potencial  
**Criterio:** prácticas Cursor-class / agent coding / IDE+CI que no equivalen a enforcement en nuestro `run_code_path` + standards.

---

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

## N. Python/JS stack specifics often in Cursor repos (361–390)
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

## P. Agent evaluation & quality of AI output (421–450)
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

---

**Conteo:** 300 puntos (201–500).  
**Unión con lista 1–200:** 500 gaps potenciales estilo Cursor vs Wordflow programming actual.
