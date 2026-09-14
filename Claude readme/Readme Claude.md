# README CLAUDE — MEMORIA PERSISTENTE DEL ORQUESTADOR
**Última actualización: 2026-09-13 20:19 hora de Colombia (America/Bogota)**
**Este archivo NUNCA se resume. Se actualiza añadiendo, nunca borrando historia relevante.**

---

## 1. QUÉ ES ESTO

Soy Claude, actuando como orquestador central del ecosistema Maxbry/NCT. No escribo código de producción — escribo instrucciones, audito evidencia, y mantengo este archivo y sus hermanos (`Readme Claude instrucciones.md`, `Claude bitácora stated JSON Craxy wall.md`, `Handoff`) como mi memoria de trabajo persistente entre sesiones de chat.

Sol GPT queda retirado del rol de orquestador (rendimiento insuficiente, no planifica bien, requiere explicación repetida). Yo centralizo la planificación desde ahora.

---

## 2. EL ECOSISTEMA COMPLETO (7 proyectos, verificado 2026-09-13)

| # | Proyecto | Repo GitHub | Estado de confirmación |
|---|---|---|---|
| 1 | Agente Yaiwes | `agentes` | Confirmado |
| 2 | Osquestador Maxbry | `Orquestador-Maxbry-` | Alta confianza, no confirmado explícitamente |
| 3 | Router Inteligente Universal | `router-universal-router-inteligente-` | Confirmado (prioridad activa) |
| 4 | UI Yaiwes (multi-ventana + mini-VM) | `nct-hub` (hipótesis) | Sin confirmar — pendiente |
| 5 | Fábrica de UI | `frontend` | Confirmado (prioridad activa) — ya contiene su propia carpeta `UI YAIWES/` con Crazy Wall y Handoff propios en V5/V8 |
| 6 | Osquestador auditor + memoria (diseño Fables) | `osquestador-auditor` | Contiene 2 procesos: memoria del agente, e "Input Shark" 🦈 (prepara contexto antes de la llamada al LLM, evita fricción/bucles) — ubicación del segundo proceso aún no cerrada por decisión de Fables, se revisará más adelante |
| 7 | NCT (Neuronas Code Turbo) | `nct-core` | Confirmado |

**Repos activos AHORA (prioridad del Director):** `agentes`, `frontend`, `router-universal-router-inteligente-`.
**Repos a ignorar por ahora:** `TAREA-1` (contiene arquitectura de Hugging Face — se revisa cuando lleguemos al Router Universal), `TAREA-2`, `MEMORIA`, `Maxbry-AGI`, `Cerebro`, `Grupo-Trabajo-1/2`, `comand-Center`, `BIBLIOTECA`, `informaci-n-auditor-`, `nct-hub` (hasta confirmar), `BITACORA-MAXBRY` (propósito sin confirmar — ¿bitácora central del ecosistema?).

---

## 3. MÉTODO DE TRABAJO (constitución operativa)

1. **Un paso por salida.** No se avanza al siguiente paso hasta cerrar el actual (o dejarlo con evidencia de GAP documentado).
2. **Micro-mundos aislados por proyecto.** Cada repo tiene su propio: Readme arquitectura, Crazy Wall/bitácora/stated JSON, Handoff, componentes open source a integrar, motor de descarga/extracción/copia. Ninguna IA mezcla proyectos.
3. **Contrato de nodo: máximo 3 pasos.** `VERIFY_RESEARCH → EXECUTE_DELTA → TEST_REPORT`. Formato general: `READ FRESH → IDENTIFY FREE/GAP_RESOLVABLE → CLAIM → VERIFY_RESEARCH → EXECUTE_DELTA → TEST_REPORT → VERIFIED_CLOSED|GAP → READ FRESH → NEXT NODE`.
4. **Reglas duras de cualquier ejecutor (Sol GPT, Haiku, Sonnet, etc.):**
   - Nunca reclamar un nodo `CLAIMED|EXECUTING` de otro ejecutor.
   - Solo reclamar `FREE|GAP_RESOLVABLE`.
   - Antes del claim: releer main y registrar `fresh_main_sha + chat_id + node_id + write_scope + claimed_at`.
   - Prioridad de resolución: `REUSE_EXISTING > PATCH > ADAPT > GENERATE > NEW_DOWNLOAD`.
   - No declarar PASS sin evidencia real (`path/blob/SHA + test + log + readback`).
   - `SOURCE_PRESENT != IMPLEMENTED != WIRED != RUNTIME_TEST_PASS != VERIFIED_CLOSED`.
   - Si el nodo se bloquea: registrar GAP con evidencia y tomar otro nodo FREE independiente — nunca detenerse.
   - Ante un GAP: investigar mínimo 20 formas de resolverlo (GitHub, Hugging Face, comunidad de desarrolladores) antes de escalar — nunca asumir que ya se sabe la respuesta.
   - Solo escribe en: Crazy Wall/bitácora/stated JSON, Handoff, los archivos que ejecuta, y el Readme de arquitectura del proyecto. Nunca inventa archivos nuevos fuera de ese alcance sin aprobación.
5. **Escalera de escalamiento cuando un ejecutor no resuelve:**
   `Sol GPT → Claude Haiku → Claude Sonnet → Claude Opus → GPT/Astra (históricamente sin resultados) → Fables 5.1`.
6. **Cómo se relaciona el Director conmigo:** yo redacto la instrucción/nodo, el Director la aprueba, y la pega en el chat ejecutor correspondiente (Sol GPT, Haiku, Sonnet) junto con el enlace al Crazy Wall + Handoff de ese proyecto específico. El Director puede correr enjambres de 10-20 chats Sol en paralelo con un chat supervisor propio revisando el Crazy Wall; cuando terminan o encuentran GAPs, yo reviso y genero la siguiente instrucción/escalamiento.
7. **Regla de oro de honestidad:** nunca resumir en los documentos de trabajo — todo debe quedar tan detallado que funcione como parche de recuperación completo si la sesión se corta.
8. **Fuente de verdad de componentes:** antes de generar código nuevo, siempre `COPY-FIRST` — revisar si ya existe en el repo (frecuentemente sí, con nombres distintos) antes de escribir nada.

---

## 4. PRIORIDAD ACTUAL (según el Director, 2026-09-13)

1. Cerrar la ficha técnica, componentes e integración del Agente Yaiwes (`agentes`) — EN CURSO.
2. Continuar con el Wordflow Loop code de Yaiwes.
3. Activar el Router Inteligente Universal para poner en marcha los wordflow loops.
4. Tener operativos varios wordflow loops automatizados tipo SDK de agentes de trabajo.

**Próxima acción pendiente de ejecutar:** Paso 1 — auditoría forense X-Ray del repo `agentes`, enfocada en cerrar lo que ya veníamos construyendo (ficha, componentes, integración) antes de pasar al Wordflow Loop.
