# INVESTIGACION 6 COMPONENTES - Comand Center backend (2026-09-19)

Busqueda real (WebSearch), no inventado. 5/6 confirmados con repo real,
1 GAP explicito.

## 1. Herder -> REAL. Nombre real: "Herdr"
Repo: github.com/ogulcancelik/herdr (mirror: herdrdev/herdr)
Que es: multiplexor de terminal para agentes de codigo IA ("tmux para
agentes"). NO es un orquestador de decisiones, es runtime/sesiones.
Mecanismo util para Comand Center: gestion de paneles/sesiones
concurrentes por agente, centro de notificaciones, todos por pane.
Extraer: patron de sesion-por-agente aislada (similar a isolation.py
que ya tenemos), NO su UI.

## 2. MatPoco Skills -> REAL. Nombre real: "mattpocock/skills"
Repo: github.com/mattpocock/skills
Que es: paquete de Skills (SKILL.md) para Claude Code, de Matt Pocock
("Skills for Real Engineers"). NO es un motor de descarga ni un agente,
es contenido/prompts de skill.
Mecanismo util: ninguno para Comand Center backend. Util solo como
biblioteca de skills a evaluar para integrar como .md, no como motor.

## 3. DeepSeek Harness -> REAL, oficial DeepSeek
Repo: github.com/deepseek-ai/deepseek-harness
Que es: harness open-source oficial de DeepSeek, "Everything is a
Plugin" - permite correr cualquier modelo (via provider config) como
agente de codigo.
Mecanismo util para Comand Center: patron de provider-plugin
(config declarativa de que modelo/API usar por tarea) - similar a lo
que ya hace router_modelos.py, sirve para validar/mejorar ese diseno.

## 4. Open Montage -> GAP. NO SE ENCONTRO REPO VERIFICABLE
Busqueda solo encontro un video de YouTube ("Open Montage: FREE
Open-Source Agentic Video System") sin link a repo real. Resultados
relacionados (Open-Sora, OmAgent, Mora, Code2Video) NO coinciden con
el nombre exacto. No se va a inventar una URL. Queda como GAP hasta
que el Director confirme el nombre exacto o el link.

## 5. Mander Diffling -> REAL (nombre real: "Munder Difflin",
referencia a The Office)
Repo: github.com/chaitanyagiri/munder-difflin
Que es: harness local multi-agente que corre "una oficina de agentes"
usando las suscripciones existentes de Claude Code/Codex del usuario.
Mecanismo util para Comand Center: patron de "oficina de agentes"
(varios agentes con roles fijos colaborando sobre las mismas
suscripciones) - relevante para como Seals Team reparte tareas.

## 6. Orca -> REAL (ya parcialmente investigado antes)
Repo: github.com/stablyai/orca
Que es: ADE (Agent Development Environment) para correr una flota de
agentes en paralelo, con las suscripciones propias del usuario.
Mecanismo ya extraido (ver CHECKPOINT-Ponytail-AgentSkills.md):
worktree git aislado por agente + rotacion/hot-swap de cuentas y API
keys con tracking de uso. Este es el mas directamente reusable para
Comand Center (coincide con isolation.py y router_modelos.py ya
existentes en seals_core).

## RESUMEN PARA COMAND CENTER
Componentes con mecanismo realmente extraible y compatible con lo que
YA existe en seals_core (isolation.py, router_modelos.py):
- Orca: aislamiento por worktree + rotacion de keys (mas fuerte)
- Munder Difflin: patron "oficina de agentes" con roles fijos
- DeepSeek Harness: patron provider-plugin declarativo
- Herdr: gestion de sesiones/paneles concurrentes (secundario)

MatPoco Skills: no es motor, es biblioteca de skills - fuera de scope
de "motor de descarga/extraccion".

Open Montage: GAP, sin repo, no se monta nada hasta confirmar.
