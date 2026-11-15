CONTRATO - SKILL DESIGN DE ANTHROPIC COMO COMPUERTA DURA PARA FRONTEND
2026-09-17

## OBJETIVO
El skill oficial de Anthropic sobre como disenar/crear Skills (conocido
como skill-creator) se descarga y se convierte en requisito obligatorio
antes de que cualquier agente del Fleet trabaje en frontend.

## CONTRATO (fail-closed, igual que los demas gates)

frontend_skill_gate:
  requiere: skill_design_anthropic_cargado == true
  fuente_skill: skill-creator (Anthropic, oficial)
  destino_descarga: Skills agente/skill-design-anthropic/
  verificacion:
    - archivo SKILL.md presente
    - frontmatter YAML valido
    - accesible por el agente que va a trabajar en frontend
  si_no_esta_cargado: BLOCKED, el agente NO AVANZA con la tarea de
    frontend, sin excepcion.
  se_verifica_en: cada activacion del mini-workflow frontend
    (SCHEMA-frontend-browser-verified.md), ANTES de EDITA_COMPONENTE.

## RELACION CON EL RESTO DE LA ARQUITECTURA
Este gate se suma a los ya existentes en el mini-workflow frontend
(CODE_PASS + BROWSER_PASS + VISUAL_PASS) - ahora hay un gate previo:
SKILL_PASS -> CODE_PASS -> BROWSER_PASS -> VISUAL_PASS. Los 4 son
obligatorios, ninguno opcional.

## PROMPT PARA SOL - descargar el skill
SOL GPT - DESCARGAR SKILL DESIGN ANTHROPIC - AGENTE YAIWES
repo: maxbry123-commits/agentes | branch: main | modo: FAIL_CLOSED_STRICT_3_STEPS

OBJETIVO: buscar y descargar el skill oficial de Anthropic sobre diseno
de Skills (skill-creator). Verificar que es la fuente oficial de
Anthropic antes de descargar - no una copia de terceros sin confirmar.
DESTINO: Skills agente/skill-design-anthropic/
Si no encuentras con certeza la fuente oficial: marca
NOT_FOUND_VERIFY_WITH_DIRECTOR, no descargues una alternativa sin avisar.
REPORTA EN: Claude notas/EVIDENCIA-DESCARGA-4-COMPONENTES.md (mismo
archivo del prompt anterior de descarga, anadir aqui, no crear otro).
INICIA AHORA.
