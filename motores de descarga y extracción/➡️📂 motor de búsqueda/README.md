# ➡️📂 Motor de búsqueda

Motor de búsqueda web multi-proveedor para Router Inteligente Universal.

## Objetivo

Ejecutar búsqueda fuera del chat, de forma **local y anónima**, y escribir el resultado en archivos para que Claude/Sol/agentes lean solo el resultado final.

Flujo:

TRIGGER local -> 5 proveedores -> deduplicación/ranking determinista -> result.json + summary.md

No usa Actions de CI. No usa LLM por defecto. No publica en repositorios remotos.

## Proveedores

1. ddgs — metasearch sin API key; combina varios motores disponibles.
2. brave — BRAVE_SEARCH_API_KEY.
3. tavily — TAVILY_API_KEY.
4. serper — SERPER_API_KEY.
5. firecrawl — FIRECRAWL_API_KEY.

El scraper HTML directo de DuckDuckGo se conserva solo como fallback interno opcional; no es el proveedor principal porque puede recibir challenge/CAPTCHA.

Los proveedores sin secreto quedan GAP; el motor continúa con los disponibles.

## Archivos

- websearch_engine.py — ejecuta, agrega, deduplica, puntúa y escribe resultados.
- trigger_websearch.py — trigger local on-demand; invoca al engine y devuelve el veredicto.
- test_websearch_engine.py — tests deterministas sin red.
- source_registry.json — fuentes habilitadas del research prepass.
- research_prepass.py — búsqueda determinista de evidencia directa y contextual.
- context_packet.schema.json — esquema del context packet.
- test_research_prepass.py — tests deterministas sin red.
- RESEARCH-PREPASS-TRAZABILIDAD.md — documento histórico (no refleja el flujo vigente).

## Salida

Por defecto:

./websearch-results/<RUN_ID>/result.json
./websearch-results/<RUN_ID>/summary.md

El run id se toma de `RUN_ID` si existe; si no, se genera con marca temporal y hash de la consulta.

La persistencia es **solo local**: `result.json` y `summary.md` se escriben y se verifican por read-back. No hay publicación remota.

summary.md es la vista compacta que debe leer el agente para reducir contexto/tokens.

## Uso local

python websearch_engine.py "consulta"

## Trigger local

python trigger_websearch.py "consulta"

Opcional:

python trigger_websearch.py "consulta" --providers ddgs,brave,tavily,serper,firecrawl --limit 8

Variables: `QUERY`, `PROVIDERS`, `MAX_RESULTS_PER_PROVIDER`, `WEBSEARCH_OUTPUT_ROOT`, `RUN_ID`.

## Secretos

El motor no lee, imprime ni reenvía credenciales de repositorios. Las claves de los proveedores de búsqueda se leen del entorno del proceso que ejecuta el motor y solo se usan para esa llamada.

## PASS

VERIFIED_CLOSED exige:
1. consulta válida;
2. al menos un resultado;
3. result.json escrito;
4. summary.md escrito;
5. read-back de result.json coherente.

Si un proveedor falla, queda registrado como GAP sin ocultarse.


## Research Prepass nativo

Objetivo:

INPUT_BLOCK verbatim
-> research_prepass.py
-> 10 fuentes web preestablecidas
-> API REST pública de GitHub
-> dedupe/ranking/budget
-> context_packet.json + context.md
-> agente/LLM

Archivos:

- source_registry.json
- research_prepass.py
- context_packet.schema.json
- test_research_prepass.py
- RESEARCH-PREPASS-TRAZABILIDAD.md

Fuentes web preestablecidas:

1. Stack Overflow
2. DEV Community
3. Reddit
4. Python Docs
5. MDN
6. docs.rs
7. Node.js Docs
8. Docker Docs
9. Vercel Docs
10. npm

Fuentes directas de alta autoridad:

- API REST de búsqueda de GitHub (pública y anónima)

Reglas:

- no LLM durante la investigación;
- input literal preservado en input_verbatim.txt;
- context.md NO reemplaza el input original;
- consultas derivadas por reglas deterministas;
- resultados deduplicados y rankeados;
- context budget antes de entregarlo al modelo;
- cache por hash para evitar búsquedas repetidas;
- NO_NEW_EVIDENCE si no aparece evidencia nueva;
- cada fuente conserva provenance y estado PASS/NO_RESULTS/GAP.

Uso local:

INPUT_BLOCK_FILE=input.md python research_prepass.py

Con plan de ejecución:

INPUT_BLOCK_FILE=input.md EXECUTION_PLAN_FILE=plan.md python research_prepass.py

Estado actual:

CODE_PRESENT / RUNTIME_NETWORK_TEST_PENDING.

Trazabilidad exacta:

RESEARCH-PREPASS-TRAZABILIDAD.md
