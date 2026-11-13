# TRAZABILIDAD - RESEARCH PREPASS NATIVO RIU

Scope: Router Inteligente Universal.
Estado: DESIGN + CODE PRESENT / RUNTIME NETWORK TEST PENDING.

## OBJETIVO

Convertir el INPUT_BLOCK verbatim + plan opcional en contexto técnico trazable
ANTES de que el LLM/agente ejecute la tarea.

Flujo:

INPUT_BLOCK verbatim
-> SHA256 + persistencia literal
-> QueryCompiler determinista
-> 10 fuentes web preestablecidas
-> GitHub API
-> Hugging Face Hub API
-> dedupe/ranking determinista
-> context budget
-> context_packet.json + context.md
-> agente/LLM

El motor de investigación NO usa LLM.

## FUENTES DE CODIGO INTERNAS

### R-001 Websearch engine existente

Archivo:
➡️📂motores de descarga extracción copiado movimiento archivos router-universal-router-inteligente-/➡️📂 motor de búsqueda/websearch_engine.py

Blob SHA:
dae4ea0cc6143c2031110872a5a77e2675439b7d

Mecanismos reutilizados:
- DDGS
- Brave/Tavily/Serper/Firecrawl opcionales
- URL canonicalization
- dedupe
- ranking
- output/read-back

No se crea un segundo buscador paralelo.

### R-002 Context Composer existente

Archivo:
Yaiwes Cognitive Control Plane/context_composer.py

Blob SHA:
4291158d2682a22a6cc0aca20be5bc549ab96dd7

Mecanismos de referencia:
- deduplicacion
- ranking por autoridad/relevancia
- presupuesto de contexto
- estimacion de tokens

El Research Prepass conserva el ownership del Context Composer:
no crea un segundo cognitive router.

## FUENTES OFICIALES EXTERNAS

GitHub REST API:
https://docs.github.com/en/rest/search/search

GitHub REST metadata / search endpoint discovery:
https://docs.github.com/en/rest/meta/meta

Hugging Face Hub API:
https://huggingface.co/docs/hub/api

Hugging Face Hub search:
https://huggingface.co/docs/huggingface_hub/guides/search

Uso aprobado:
- GitHub: repositorios publicos + code search cuando exista token autorizado.
- Hugging Face: models + datasets + Spaces.
- Respetar rate limits y clasificar fallo como GAP; nunca inventar resultado.

## R-003 SOURCE REGISTRY

Archivo:
source_registry.json

Blob SHA:
e62633c5c25c6eac1a081bfbc3871ad993ecc27c

Fuentes directas:
1. GitHub
2. Hugging Face

10 fuentes web preestablecidas:
1. stackoverflow.com
2. dev.to
3. reddit.com
4. docs.python.org
5. developer.mozilla.org
6. docs.rs
7. nodejs.org
8. docs.docker.com
9. vercel.com/docs
10. npmjs.com

Regla:
la lista vive en registry, no hardcodeada dentro del razonamiento del LLM.

## R-004 RESEARCH PREPASS

Archivo:
research_prepass.py

Blob SHA:
ea257a20ef1c7810ca0b4b0ff8e4b7caa86cf613

Schema runtime:
yaiwes.research.prepass.v1

Funciones clave:
- read_input()
- terms_from()
- build_query()
- load_registry()
- search_web_source()
- github_search()
- hf_search()
- rank_records()
- select_budget()
- run()

Input:
- INPUT_BLOCK o INPUT_BLOCK_FILE
- EXECUTION_PLAN opcional
- source_registry.json

Output:
- input_verbatim.txt
- plan_verbatim.txt opcional
- context_packet.json
- context.md

Invariante:
input_verbatim.txt debe ser byte-equivalent al input recibido.

QueryCompiler:
NO usa LLM.
Extrae deterministicamente identificadores, filenames, nombres de tecnologia,
tokens code-like, quoted text y terminos significativos.

## R-005 CONTEXT PACKET CONTRACT

Archivo:
context_packet.schema.json

Blob SHA:
5d0649f33da57dedfe34f7cf379c17528e3f394e

Campos criticos:
- input.sha256
- input.verbatim_preserved
- source_registry_sha256
- derived_query
- sources_requested
- source_status
- records
- budget_tokens
- estimated_context_tokens
- truncated
- llm_used=false
- verdict

Estados permitidos:
VERIFIED_CLOSED
NO_NEW_EVIDENCE

Un fallo por fuente:
GAP de esa fuente.
No se transforma en evidencia positiva.

## R-006 REGRESSION TESTS

Archivo:
test_research_prepass.py

Blob SHA:
2e97ad8aa0ecf395a0a28e038ce79a829c1ac378

Tests creados:
- deterministic query
- domain filter
- dedupe/ranking/budget
- input verbatim preservado
- llm_used=false
- outputs creados

Estado:
TEST CODE PRESENT.
RUNTIME TEST PENDING.

No declarar PASS runtime hasta ejecutar test real y al menos una busqueda de red.

## REGLAS DE CONTEXTO

1. INPUT_BLOCK original sigue siendo autoridad.
2. context.md es evidencia auxiliar, no reemplazo del input.
3. No meter todo el result set al modelo.
4. Aplicar budget y max_per_source.
5. Cache por hash evita investigar repetidamente el mismo input.
6. NO_NEW_EVIDENCE no se rellena con inferencia.
7. URL + source_id + provider + score quedan en provenance.
8. GitHub/HF direct sources tienen mayor autoridad que comunidad cuando el claim
   corresponde a codigo/modelos.
9. Community sources pueden aportar experiencia, no reemplazan documentacion oficial.
10. El agente debe diferenciar SOURCE_EVIDENCE de MODEL_INFERENCE.

## INTEGRACION NATIVA PROPUESTA

INPUT
-> ResearchPrepass
-> ContextPacket
-> ContextComposer
-> Router/Agent
-> PLAN
-> EXECUTE

No se conecta directamente al hot-path hasta:
- tests locales PASS
- network smoke PASS
- context schema validation PASS
- context budget PASS
- no-secret-leak PASS
- read-back PASS

## CONDICION DE CIERRE

RESEARCH_PREPASS_NATIVE_VERIFIED exige:

INPUT_VERBATIM_HASH_PASS
+ QUERY_DETERMINISM_PASS
+ SOURCE_REGISTRY_PASS
+ GITHUB_SEARCH_PASS_OR_TYPED_GAP
+ HF_SEARCH_PASS_OR_TYPED_GAP
+ 10_DOMAIN_SEARCH_PASS_OR_TYPED_GAPS
+ DEDUPE_PASS
+ BUDGET_PASS
+ CONTEXT_SCHEMA_PASS
+ NO_LLM_SEARCH_PASS
+ READBACK_PASS
+ ROUTER_INTEGRATION_TEST_PASS
