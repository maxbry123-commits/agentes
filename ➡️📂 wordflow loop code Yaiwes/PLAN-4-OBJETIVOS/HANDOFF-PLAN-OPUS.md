# HANDOFF PLAN OPUS

Plan opus = Claude notas/PLAN-MAESTRO-4-OBJETIVOS.md (4 objetivos) + PLAN-ANEXO-C-2-PUNTOS-ADICIONALES.md.
Este handoff manda sobre CABLEADO-EQUIPO-AGENTES.md y HANDOFF-SONNET-ARRANQUE-AGENTES.md donde se contradigan.
Los swaps a aider/smolagents quedan ANULADOS: el equipo es el que dio el Director.

## Archivos del plan opus (todo en Claude notas/PLAN-OPUS/)

1. CRAZY-WALL-BITACORA-PLAN-OPUS.json - donde los agentes anotan resultados. Claude revisa.
2. agentes/README-AGENTE-nombre.md - memoria de cada agente (5 archivos).
3. HANDOFF-PLAN-OPUS.md - este archivo.
4. PROMPT-DSL-DAG-PLAN-OPUS.yaml - el DAG que cablea todo.

## Paso 0 - loop de trabajo (orden textual del Director)

Los 5 agentes:
1. Claude Code
2. Codex
3. Open Code
4. Open Hands
5. Meta Code (Muse Code + Muse Glimmer)
6. Decisiones por consenso (Ask Consul)

Antes de CADA salida: Ask Consul.
1. Se escribe goal de entrada y goal de salida.
2. Los modelos analizan la arquitectura ANTES de ejecutar, con la misma api; el mini router los cambia de modelo en cascada: Kimi K3, Nemotron, GLM 5, DeepSeek v4, y uno adicional (MiniMax M3 por Hugging Face).
3. Se decide por consenso como hacer la tarea.
4. Todo queda anotado en la bitacora para evitar desviacion.

Reparto:
- Objetivo 1: Claude Code ejecuta. Codex revisa, audita, refactoriza o repara.
- Objetivo 2: Open Code ejecuta. Open Hands audita y revisa. Meta Code revisa de nuevo, refactoriza y repara.
- Objetivo 3: igual que el 2.
- Objetivo 4: igual que el 2.

## Grupos y claves

El router dicta la norma: clave y modelo. 4 claves, una por grupo, un grupo por objetivo:
1. Grupo Objetivo 1 - nvidia/digi-maxbry
2. Grupo Objetivo 2 - nvidia/movistar-briseida
3. Grupo Objetivo 3 - nvidia/wow-maxbry
4. Grupo Objetivo 4 - nvidia/wow-brisa
Se piden por nombre (credential_ref). Nadie ve ni escribe la clave.

Objetivo bloqueado: BANDERA, se anota en la bitacora, se sigue con la siguiente tarea, y al final se vuelve en bucle a revisar si ya se puede ejecutar.

## Paso 1 - X-Ray forense de Core kernel Yaiwes

Recorrer toda la raiz de Core kernel Yaiwes, componente por componente. Salida: Claude notas/PLAN-OPUS/XRAY-CORE-KERNEL-YAIWES.md. Plantilla: Claude notas/VERBATIM-01-node-executor-xray-v2.md.

## Paso 2 - auditoria Wordflow al cierre de cada objetivo

Al cerrar cada objetivo: revisar el Wordflow y auditar con la plantilla del metodo de Meta que describio Sol GPT. Un archivo por cierre:
1. AUDITORIA-WORDFLOW-OBJETIVO-1.md a -4.md
2. AUDITORIA-CIERRE-SEALS-TEAM-YAIWES.md
3. AUDITORIA-CIERRE-ORQUESTADOR-COMANDANTE.md
Todos en Claude notas/PLAN-OPUS/.

## Como se instalan los agentes (a verificar en el primer run, anotar resultado)

1. Claude Code: npm i -g @anthropic-ai/claude-code
2. Codex: npm i -g @openai/codex (binario ya compilado, no hace falta Rust)
3. Open Code: npm i -g opencode-ai
4. Open Hands: pip install openhands-ai
5. Meta Code: agent_sources/meta_muse_code_sdk + agent_sources/muse_glimmer/code/agentic-fundamentals
Si una instalacion falla: BANDERA en la bitacora y seguir.

## Bloqueos abiertos (BANDERA)

1. Banco NVIDIA: banco-nvidia-equipo.b64 no esta en ningun repo; la contrasena la da el Director. Sin eso ningun grupo llama a NVIDIA.
2. Evidencia del router: bajo carga solo Nemotron aguanta; Kimi K3 y GLM 5 se agotan en NVIDIA. El router decide la cascada.

## Reglas

R01 nada desde cero, R02 max 500 LOC, R03 nunca borrar, R04 no PASS sin evidencia real, R05 sparse-checkout en Actions, R06 anotar antes de avanzar, R08 gap ladder y bandera.

## Como se ejecuta (loop + coda + bucle determinista)

1. Workflow: .github/workflows/plan-opus-loop.yml, nombre "Plan Opus - loop de agentes". Se lanza a mano en Actions, eligiendo grupo (G1..G4 o all) y nodos por vuelta.
2. Runner: Claude notas/PLAN-OPUS/runner/plan_opus_loop.py. Usa la cola durable de Fables (coda workflow persistencias, SQLiteDurableStore) guardada en estado/plan_opus_queue.db.
3. Cada vuelta: aplica ordenes del centro de control, siembra la cola desde el DAG y toma por grupo el siguiente nodo con dependencias en PASS. En ese nodo hace Ask Consul (cascada y consenso), ejecuta, audita, repara si hay GAP, re-audita, guarda evidencia sha256 y anota en la bitacora y en la memoria del agente. Segunda pasada = bucle de banderas.
4. PASS solo si: ejecutor rc 0 + auditor "VEREDICTO: OK" + archivo de salida real, o cambio real dentro de las rutas del grupo. Si no, GAP y vuelve a la cola (max 20 intentos, R08).
5. Salvaguardas: los agentes corren con sus protecciones puestas (sin saltarse permisos ni sandbox). La clave del grupo solo llega al proceso del agente, nunca a logs (se reemplaza por ***). El banco no llega al agente. Cada vuelta termina en un PR; el Director decide el merge. La cola solo cuenta como PASS lo que ya se fusiono en main.
6. Claves en Actions: secrets RIU_TEAM_BANK_B64 (banco cifrado) + RIU_TEAM_BANK_PASSPHRASE. Sin ellos cada nodo queda BANDERA B-001. Alternativa sin GitHub: correr el runner en otra maquina con RIU_TEAM_BANK_FILE + RIU_TEAM_BANK_PASSPHRASE.

## Centro de control (Sonnet / Sol / Director)

Archivo: Claude notas/PLAN-OPUS/CENTRO-DE-CONTROL.yaml. El revisor actua como mini orquestador:
1. Revisa la bitacora, evidencia/<nodo>-<fecha>/ y el PR de la vuelta.
2. Escribe ordenes PENDIENTE: REACTIVAR, INSTRUCCION, PAUSAR, NUEVO_NODO, REVISION.
3. Relanza el workflow. El runner aplica las ordenes, las marca APLICADA y las anota en la bitacora.
El centro de control da instrucciones; no escribe codigo. Los agentes ejecutan el plan.
