# CABLEADO DEL EQUIPO DE AGENTES - listo para arrancar (2026-09-21)

Este archivo es el cableado: quien ejecuta, quien revisa, con que modelo, y de
donde salen las claves. Sin sobre ingenieria. Todo lo de aqui usa componentes que
YA estan montados y verificados (ver INVENTARIO-FORENSE-agent_sources.md).

## 1. El equipo: 5 agentes (6 con el consenso)

1. CLAUDE CODE - ejecutor. agent_sources/claude_code (REAL). Handoff: handoffs/HANDOFF-claude_code.md
2. CODEX - auditor y refactor. agent_sources/codex (REAL). Handoff: handoffs/HANDOFF-codex.md
   Nota real: el slot de trabajo de instalacion simple esta swapeado a AIDER porque
   codex-rs exige compilar un monorepo Rust. Codex sigue como AUDITOR (no compila nada).
3. OPENCODE - ejecutor. agent_sources/opencode (REAL). Handoff: handoffs/HANDOFF-opencode.md
4. OPENHANDS - auditor y revisor. agent_sources/openhands (REAL). Handoff: handoffs/HANDOFF-openhands.md
5. META CODE - son DOS componentes, no uno:
   5a. MUSE CODE - programador y orquestador: lee repo, mantiene sesion, modifica
       codigo, ejecuta el ciclo de desarrollo.
       agent_sources/meta_muse_code_sdk (SDK real) + agent_sources/meta_agent_cookbook
       (seccion 04_muse_code, 10 recipes). Handoff: handoffs/HANDOFF-muse_code.md
   5b. MUSE GLIMMER - cerebro de decisiones: plan, tool, result, self-correct, next.
       agent_sources/muse_glimmer/code/agentic-fundamentals/ (agent_loop.py,
       response_parser.py, run_agent.py). Handoff: handoffs/HANDOFF-muse_glimmer.md
6. ASK CONSUL - no es un agente: es el paso de consenso antes de cada salida.

## 2. Reparto por objetivo (orden del Director, 1 a 1)

OBJETIVO 1:
- Claude Code ejecuta
- Codex revisa, audita, refactoriza o repara

OBJETIVO 2, OBJETIVO 3 y OBJETIVO 4 (el mismo patron en los tres):
- Opencode ejecuta
- Openhands audita y revisa
- Meta Code (Muse Code + Muse Glimmer) revisa de nuevo, refactoriza y repara

## 3. Ask Consul - consenso antes de cada salida

Antes de ejecutar cualquier tarea:
1. Se plantea el goal de entrada y el goal de salida.
2. Los modelos del router analizan la arquitectura ANTES de ejecutar.
3. El resultado NO es de un agente: se decide por consenso.
4. Queda anotado en la bitacora para evitar desviacion.

Quien llama a los modelos: el ROUTER, no Claude directamente.

## 4. Claves: banco secreto, nunca en el repo

Regla dura del Director, sin excepciones:
1. Las claves NO van a GitHub Secrets, NO van al chat, NO van a archivos.
2. Los agentes y el router usan el credential_ref (nombre), nunca el valor.
3. El broker resuelve por dentro. El agente recibe la respuesta, nunca la clave.
4. Si alguien pega una clave en el chat: no se usa, no se guarda, no se copia.

credential_ref disponibles para el equipo NVIDIA (4 claves, una por grupo):
1. nvidia/digi-maxbry
2. nvidia/movistar-briseida
3. nvidia/wow-maxbry
4. nvidia/wow-brisa

Fuera del kit: nvidia/digi-briseida (inestable, lo excluyo el equipo del router).

Codigo del banco (repo router-universal-router-inteligente-):
1. Chat Mvp/secret_bank/vault.py, session.py, broker.py
2. Claude notas/KIT-EQUIPO-NVIDIA/nvidia_team_client.py (NvidiaPool con respaldo
   automatico: si una clave tarda o falla, usa la siguiente)
3. Claude notas/BANCO-SECRETO-README.md

ESTO CIERRA EL BLOQUEO QUE TENIA ESTE REPO: ya no hace falta sellar ni subir
ninguna clave NVIDIA a GitHub Actions Secrets. Se usa el banco por nombre.

## 5. Modelos del router - catalogo REAL verificado, no el teorico

Evidencia del equipo del router, runner real de GitHub, 2026-09-20:

1. nvidia/nemotron-3-super-120b-a12b - FUNCIONA. Principal, para trabajo en volumen.
   Respondio en 1-2 s con las claves 3, 4 y 5.
2. deepseek-ai/deepseek-v4-flash-0731 - funciona con 1 peticion. Maximo 1-2 en
   paralelo, se agota el tiempo con 10. Solo tareas menores.
3. MiniMax M3 - por el router de Hugging Face. Para codigo.
4. moonshotai/kimi-k3 - se agota el tiempo con carga en NVIDIA. Mejor por Hugging Face.
5. z-ai/glm-5.3-flash - se agota el tiempo con carga en NVIDIA.
6. moonshotai/kimi-k2.6 - NO existe en NVIDIA (404).
7. minimaxai/minimax-m2.7 - retirado por NVIDIA (410).

CORRECCION IMPORTANTE al plan original: la cascada pensada (Kimi K3, GLM 5,
DeepSeek v4 y Nemotron rotando por igual) NO aguanta en la realidad. Solo Nemotron
soporta volumen. La cascada real queda:
1. Nemotron primero, siempre, para todo el trabajo pesado.
2. DeepSeek v4 flash solo para tareas menores y como maximo 1-2 en paralelo.
3. MiniMax M3 (via Hugging Face) para codigo.
4. Kimi y GLM via Hugging Face, no via NVIDIA.
Si NVIDIA falla: avisar al Director. No se cambia de proveedor sin su OK.

## 6. Grupos y desbloqueo

1. Son 4 grupos, uno por objetivo. Cada grupo usa un credential_ref distinto de los
   4 de arriba.
2. Si un objetivo necesita ser desbloqueado y no puede ejecutarse: se marca con
   bandera, se sigue con la siguiente tarea, y al final se vuelve en bucle a revisar
   si ya esta listo. Nunca se para el ciclo.

## 7. Reglas heredadas (no se renegocian)

Del contrato ya existente Claude notas/PLAN-DSL-DAG-00-CONTRATO.yaml:
R01 nada de codigo desde cero (podar, editar, refactorizar, cablear lo descargado)
R02 maximo 500 LOC por bloque
R03 nunca borrar archivos
R04 no PASS sin evidencia real (CODE + TEST + EVIDENCE sha256 + READ-BACK)
R05 sparse-checkout obligatorio en Actions (el repo pesa 16.4GB)
R06 anotar cada paso antes de avanzar
R08 nunca escalar sin agotar el gap ladder; agotado, bandera y siguiente nodo

## 8. Estado de arranque

Montado y verificado: 13/13 slots de agent_sources, 20 carpetas de codigo real,
12 submodules reales, handoff por agente de los 5 del loop.
Pendiente unico antes de correr: la prueba real, que la da el Director.
