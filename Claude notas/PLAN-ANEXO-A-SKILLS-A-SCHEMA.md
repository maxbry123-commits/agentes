# ANEXO A - LOS 24 SKILLS DE FRONTEND CONVERTIDOS A SCHEMA
Anexo del PLAN-MAESTRO-4-OBJETIVOS.md. Version 1, 2026-09-19.

REGLA DEL DIRECTOR (aprobada, no negociable):
"cada skills lo transformas en un shema ya no sera mas skills"

NINGUNO se instala como SKILL.md. TODOS se convierten en contrato DSL DAG schema.
Un skill que queda como .md es un skill de adorno. Eso esta prohibido.

CONTEO AUDITADO DEL ARCHIVO DEL DIRECTOR:
39 repos GitHub unicos en total
  20 repos -> frontend (producen 24 skills + 7 software)
  18 repos -> Jev/RSI, destino repo router-universal-router-inteligente-
  1 repo  -> maxbry123-commits/agentes (el propio)

---

## FORMATO OBLIGATORIO DE CADA SCHEMA

Destino: `skills_schema/<nombre>.dag.yaml`
Plantilla base a REUTILIZAR (no inventar formato):
  `Core kernel Yaiwes/control-layer/schemas/output_contract.yaml`
  `Seals team YAIWES/dag_schema.yaml`

Campos obligatorios:
  schema_id
  objective
  acceptance[]        <- criterios VERIFICABLES, no prosa
  tools[]             <- herramientas registradas en el ToolRegistry
  evidence[]          <- path + sha256 + screenshot cuando aplique
  work_surface        <- FRONTEND | BACKEND | MIXED
  oracle              <- el test determinista que decide PASS
  gap_policy          <- que hacer cuando falla

---

## CLASIFICACION POR FUNCION (cada skill cae en un sitio distinto del DAG)

CLASE 1 - ESTETICA -> se convierten en ACCEPTANCE CRITERIA verificables
CLASE 2 - AUDITORIA -> se convierten en CHECKS EJECUTABLES del oracle
CLASE 3 - PIPELINE -> se convierten en NODOS del DAG
CLASE 4 - MOTION -> pipeline aparte con CLI registrado como tool
CLASE 5 - ROUTER -> schema de enrutado que invoca a los demas

---

## LOS 24 SKILLS, UNO A UNO

### CLASE 1 - ESTETICA (acceptance criteria)

1. Taste Skill
   https://github.com/Leonxlnx/taste-skill  |  https://www.tasteskill.dev/
   Aporta: referencias de diseno para evitar interfaces genericas.
   -> `skills_schema/taste.dag.yaml`
   acceptance[]: la UI generada no coincide con patron generico; usa referencia declarada.

2. Impeccable
   https://github.com/pbakaus/impeccable
   Aporta: tipografia, espaciado, layout, acabado visual.
   YA ESTA FISICAMENTE en el repo (Wordflow loop code Yaiwes/skills/)
   -> `skills_schema/impeccable.dag.yaml`
   acceptance[]: escala tipografica coherente, espaciado en rejilla, sin overflow.

3. UI/UX Pro Max
   https://github.com/nextlevelbuilder/ui-ux-pro-max-skill
   Aporta: 79 estilos, 192 paletas, 74 combinaciones tipograficas, UX, GSAP, charts, 22 stacks.
   -> `skills_schema/ui-ux-pro-max.dag.yaml`
   acceptance[]: paleta y tipografia elegidas del catalogo declarado, no improvisadas.

4. Emil Kowalski - Design Engineering Skills
   https://github.com/emilkowalski/skills
   Aporta: motion UI, easing, transiciones, microinteracciones.
   -> `skills_schema/motion-design-engineering.dag.yaml`
   acceptance[]: curvas de easing declaradas; sin transiciones por defecto del navegador.

5. Anthropic Frontend Design Skill
   https://github.com/anthropics/skills/tree/main/skills/frontend-design
   Aporta: interfaces distintivas de nivel produccion.
   YA ESTA FISICAMENTE en el repo.
   -> `skills_schema/frontend-design.dag.yaml`

6. AgentsORG DESIGN (/design)
   https://github.com/AgentsORG/DESIGN/tree/main/skills/design
   Aporta: sistemas visuales, tokens, componentes, identidad, evitar design drift.
   -> `skills_schema/design-system.dag.yaml`
   acceptance[]: todo color/espaciado sale de token declarado; cero valores magicos.

### CLASE 2 - AUDITORIA (checks ejecutables del oracle)

7. Vercel Web Design Guidelines
   https://github.com/vercel-labs/agent-skills/tree/main/skills/web-design-guidelines
   Aporta: mas de 100 reglas de UX, accesibilidad, formularios, motion, tipografia, performance.
   -> `skills_schema/web-design-guidelines.dag.yaml`
   ESTE ES EL MAS IMPORTANTE DE LA CLASE 2: sus 100+ reglas se vuelven
   assertions ejecutables del oracle, no un prompt.

8. Vercel React Best Practices
   https://github.com/vercel-labs/agent-skills/tree/main/skills/react-best-practices
   Aporta: rendimiento React/Next, waterfalls, bundles, renders, hooks, arquitectura.
   -> `skills_schema/react-best-practices.dag.yaml`
   acceptance[]: sin waterfalls detectados; bundle bajo umbral declarado.

9. Frontend Design Codex
   https://github.com/dachent/skills/blob/main/frontend-design-codex/SKILL.md
   Aporta: obliga a revisar la interfaz RENDERIZADA, screenshots, responsive,
   accesibilidad y browser QA - no solo el source.
   -> `skills_schema/frontend-design-codex.dag.yaml`
   Este schema es el que ENFORZA el gate BROWSER PASS + VISUAL PASS.

10. Awesome Design (VoltAgent)
    https://github.com/VoltAgent/awesome-design-md/
    Aporta: indice de referencias de diseno.
    -> `skills_schema/awesome-design-index.dag.yaml` (biblioteca RAG, no nodo ejecutable)

### CLASE 3 - PIPELINE (nodos del DAG)

11. Design-to-Code
    https://github.com/JPeetz/agent-skills/blob/main/design-to-code/SKILL.md
    Aporta: Figma/Sketch/XD/screenshot -> tokens -> componentes -> responsive ->
    WCAG -> React/Vue/Svelte + visual regression.
    -> `skills_schema/design-to-code.dag.yaml`
    Es un DAG completo por si solo: 6 nodos encadenados.

12. Image to Code
    https://github.com/Leonxlnx/taste-skill/blob/main/skills/image-to-code-skill/SKILL.md
    Aporta: imagen -> codigo.
    -> `skills_schema/image-to-code.dag.yaml`
    Nodo de entrada del pipeline anterior.

13. 21st MCP (magic-mcp)
    https://github.com/21st-dev/magic-mcp
    Aporta: generacion de componentes UI via MCP.
    -> `skills_schema/21st-magic.dag.yaml`
    Se registra como TOOL en el ToolRegistry, su schema define el contrato de llamada.

14. Skill Creator / Skills Design
    https://github.com/anthropics/skills
    Aporta: como se construye un skill.
    YA ESTA FISICAMENTE en el repo.
    -> `skills_schema/skill-creator.dag.yaml`
    META-SCHEMA: este es el que genera los demas schemas. Se procesa PRIMERO.

15. one-skill-to-rule-them-all
    https://github.com/rebelytics/one-skill-to-rule-them-all
    Aporta: patron de skill unico que enruta a los demas.
    -> `skills_schema/skill-router.dag.yaml`  (ver CLASE 5)

### CLASE 4 - MOTION / HYPERFRAMES (8 schemas)

Framework: https://github.com/heygen-com/hyperframes
Estructura: HyperFrames (framework) -> /hyperframes (router) -> skills especializados
-> CLI/renderizador -> MP4

16. hyperframes (skill router)
    -> `skills_schema/hyperframes-router.dag.yaml`
17. hyperframes-core - estructura y contrato de composicion
    -> `skills_schema/hyperframes-core.dag.yaml`
18. hyperframes-animation - animaciones, motion, GSAP, Three.js
    -> `skills_schema/hyperframes-animation.dag.yaml`
19. hyperframes-keyframes - keyframes y animacion determinista
    -> `skills_schema/hyperframes-keyframes.dag.yaml`
    NOTA: "animacion determinista" encaja con la filosofia 90% determinista.
20. hyperframes-creative - diseno, concepto, tipografia, planificacion visual
    -> `skills_schema/hyperframes-creative.dag.yaml`
21. hyperframes-audio - audio y automatizacion
    -> `skills_schema/hyperframes-audio.dag.yaml`
22. hyperframes-cli - init, preview, lint, render, publish, diagnostico
    -> `skills_schema/hyperframes-cli.dag.yaml`
    Se registra como TOOL (es un CLI real, contrato de automatizacion).
23. hyperframes-registry - registro de bloques/componentes reutilizables
    -> `skills_schema/hyperframes-registry.dag.yaml`
    Alimenta la biblioteca RAG (REUSE antes de GENERATE).

24. Web Design Studio / cinematic-scroll
    https://github.com/MustBeSimo/web-design-studio
    Aporta: sitios cinematograficos con scroll, GSAP, Three.js, 3D interactivo. MIT.
    -> `skills_schema/cinematic-scroll.dag.yaml`

### CLASE 5 - ROUTER
El schema `skill-router.dag.yaml` (del #15) es el punto de entrada:
  TAREA UI -> ROUTER -> selecciona que schemas aplican -> los encadena en un DAG
  -> ejecuta -> oracle -> evidencia

---

## LOS 7 SOFTWARE (NO son skills - son herramientas del entorno)

Estos NO se convierten a schema. Se registran como TOOLS o se ubican en la Fabrica UI.

1. Playwright MCP
   https://github.com/microsoft/playwright
   ES EL NAVEGADOR REAL del gate BROWSER PASS. Se registra como tool.
   Reutiliza el capability/adapter que Wordflow YA TIENE - no crear otro.

2. Caret        https://github.com/precious112/caret-desktop
   Canvas visual + IA + React real + Git + sync diseno->app + MCP. Open source.
3. Onlook       https://github.com/onlook-dev/onlook
   Editor visual tipo Figma sobre Next.js/Tailwind, codigo en vivo, checkpoints.
4. Plasmic      https://github.com/plasmicapp/plasmic
   Builder visual React con componentes propios.
5. Webstudio    https://github.com/webstudio-is/webstudio
   Builder visual open source, control CSS, CMS/headless, self-hosting.
   -> Los 4 anteriores van a FABRICA UI, NO dentro del loop automatico.
      Son para el humano, no para el agente.

6. HyperFrames CLI/renderizador -> produce el MP4 final.
7. ZCode        https://zcode.z.ai/  +  https://github.com/dan646/zcode-plugin-cc
   Plugin de integracion ZCode <-> Claude Code. Evaluar, no urgente.

---

## COMBINACION RECOMENDADA POR EL DIRECTOR (cadena completa)

Taste/Impeccable/Emil
  -> UI-UX Pro Max
  -> Design-to-Code
  -> Caret/Onlook
  -> Playwright MCP
  -> Vercel QA

Asi se pasa de "instrucciones de diseno" a
diseno + construccion + edicion visual + pruebas reales + correccion automatica.

---

## ORDEN DE CONVERSION

1. skill-creator (meta-schema, genera los demas)
2. skill-router (punto de entrada)
3. Clase 2 auditoria (define los oracles - sin oracle no hay PASS)
4. Clase 1 estetica (define los acceptance)
5. Clase 3 pipeline (nodos)
6. Clase 4 motion (pipeline aparte)

PASS por schema: valida contra el validador DAG existente + 1 test.
PARCHE: schemas independientes; si uno falla los demas siguen.
