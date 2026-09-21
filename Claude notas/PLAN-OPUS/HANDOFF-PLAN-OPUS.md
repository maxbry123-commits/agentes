# HANDOFF PLAN OPUS

Plan opus = Claude notas/PLAN-MAESTRO-4-OBJETIVOS.md (4 objetivos) + PLAN-ANEXO-C-2-PUNTOS-ADICIONALES.md.
Este handoff manda sobre CABLEADO-EQUIPO-AGENTES.md y HANDOFF-SONNET-ARRANQUE-AGENTES.md donde se contradigan.
Los swaps a aider/smolagents quedan ANULADOS: el equipo es el que dio el Director.

## Archivos del plan opus (todo en Claude notas/PLAN-OPUS/)

1. CRAZY-WALL-BITACORA-PLAN-OPUS.json - donde los agentes anotan resultados. Claude revisa.
2. agentes/README-AGENTE-<nombre>.md - memoria de cada agente (5 archivos).
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

Objetivo bloqueado: bandera 🚩, se anota en la bitacora, se sigue con la siguiente tarea, y al final se vuelve en bucle a revisar si ya se puede ejecutar.

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
Si una instalacion falla: 🚩 en la bitacora y seguir.

## Bloqueos abiertos (🚩)

1. Banco NVIDIA: banco-nvidia-equipo.b64 no esta en ningun repo; la contrasena la da el Director. Sin eso ningun grupo llama a NVIDIA.
2. Evidencia del router: bajo carga solo Nemotron aguanta; Kimi K3 y GLM 5 se agotan en NVIDIA. El router decide la cascada.

## Reglas

R01 nada desde cero, R02 max 500 LOC, R03 nunca borrar, R04 no PASS sin evidencia real, R05 sparse-checkout en Actions, R06 anotar antes de avanzar, R08 gap ladder y bandera.
