# ➡️📂 readme wordflow loop Yaiwes

## REGLA DE REGISTRO VIGENTE

- Este README es la bitácora canónica del trabajo del **Wordflow LOOP Yaiwes**.
- **No se escribe, modifica, integra ni programa nada en GitHub hasta que el Director diga `APROBADO`, `INTÉGRALO` o autorice explícitamente esa acción.**
- Cuando exista autorización, primero se registra el INPUT BLOCK del Director **literal 1:1**, sin resumir ni reinterpretar.
- Después se registra la salida/decisión correspondiente.
- Cada segmento aprobado se convierte solo en su propia capa/módulo; arquitectura no monolítica.
- Todo es determinista por defecto. LLM solo puede entrar en decisiones o razonamiento que no puedan resolverse determinísticamente.
- Cada capa con razonamiento llevará un **skill pequeño específico de esa capa**.
- Todo archivo de código que se cree posteriormente deberá llevar contrato/ficha y conexión mediante plugin/Enchufe Universal.
- Raíz de trabajo: `➡️📂 Wordflow LOOP Yaiwes/`.

---

## INPUT BLOCK 010 — DIRECTOR — LITERAL

Ok necesito que hagas 2 tareas 

Tarea 1. 
Acruliza el code del wordflow Github acción 

Con este skills ya que se tubo que hacer mejoras por algunos problemas repetidos de el code que se usaba para el Github acción 

https://github.com/maxbry123-commits/agentes/tree/c789e5fe635e220230ffc759d86dc3bbb8e261d4/skills/skills%20Github%20acci%C3%B3n

Tarea 2
Reciclas el mismo code del wordflow para no reescribir solo copiar con code Github y lo mandas al archivo destino 

Dime qué entiendes de las 2 tareas 

---

## INPUT BLOCK 011 — DIRECTOR — LITERAL

Inicia y usas el sistema de trabajo de flujo que te di

---

## EJECUCIÓN BLOQUE 010–011

- Se leyó el skill canónico en el commit `c789e5fe635e220230ffc759d86dc3bbb8e261d4`.
- Regla fuente confirmada: `DO_NOT_REWRITE_CODE`; política `COPY_THEN_SURGICAL_EDIT`.
- Se tomaron los locks exactos del mecanismo Descargar+Extraer:
  - `gha-download-extract.yml` → `4e64ca02c2bc970dc4cd246a2a43ec2fdb7b4e62`
  - `FORENSIC-PASS-research-download-chain-final.yml` → `9ffd682ec9491741a8f49e4a7f8bb385aa62c2ee`
  - `FORENSIC-PASS-research_download_chain.py` → `b629f9a7844a4752ff7c28b844b83e7f1d99ccb1`
  - `research_download_chain.py` → `1504bbc7ec780a351beb105df884180c9ae2c666`
  - `ADVERTENCIA-CODE.json` → `f62bee5aa59d25721be6e075778ab670b5525b7a`
- El archivo `gha-download-extract.yml` del destino ya coincidía exactamente con el lock fuente.
- Los cuatro artefactos restantes se copiaron al destino mediante referencias de blob GitHub, sin reescribir contenido.
- Destino: `➡️📂 Wordflow LOOP Yaiwes/📂 Capa workflow GitHub Action/`.
- Commit de sincronización preparado: `159810dc09d77bd5ab24bca06ea261ac293aada5`.

## MÉTODO LOOP APLICADO

0. 12 goals de entrada/salida: verificar fuente exacta, commit, destino, locks, no reescritura, integridad y read-back.
1. Analizar tarea.
2. Priorizar actualización segura y copia exacta.
3. Planificar por locks SHA.
4. Ejecutar una tarea a la vez.
5. Verificar/refutar cada copia contra SHA fuente.
6. Pasar a la siguiente tarea solo tras PASS.
7. Verificar objetivos completos; si falla, LOOP con investigación de alternativas.
8. Salida solo con checklist PASS/GAP real.

---

## INPUT BLOCK 012 — DIRECTOR — LITERAL

Te voy a pasar partes del flujo de las capas que vamos a diseñar 

En varias partes vas hacer un flujo de diagrama en cascada 

Cada capa del flujo debe tener 

Ejemplo 

➡️➡️📂 Capa de tarea 
goals 12/12 → 1 analiza → 2 prioridades → 3 planifica → 4 cola 1×1 → 5 verifica/refuta + 20 soluciones si falla → 6 siguiente → 7 verificación global/LOOP → 8 checklist + salida.


2 vas a buscar en 3 lugares code y información para reciclar code analizas que necesitas para el wordflow LOOP y lo copias no puedes reescribrir solo copiar en capas y cablear usando los plugins 

1. En el repo ➡️ agentes ➡️📂core kernel Yaiwes 

2.  En el repo ➡️ nct core 🔌📂 wordflow code 
Hay varios archivos revisa donde hay información de code que necesitas 

3. En el repo ➡️ agentes motores Wordflow YAIWES ➡️ en todas las carpetas raíces hay cientos en agente revisas hasta encontrar lo que necesitas ➡️ 

puedes usar dagu o cualquier osquestador pero hagasno esto minimalista un 
Un micro kernel de flujo con un LOOP y bucle persistente bien estructurado solo para las tareas que vamos hacer 

Dime si entendiste está instruccion y anotas en ➡️ 📂 readme wordflow loop Yaiwes 

---

## INTERPRETACIÓN OPERATIVA DEL BLOQUE 012 — PENDIENTE DE PROGRAMACIÓN

1. El Wordflow LOOP se diseña por **capas separadas** y varias capas usarán **flujo en cascada**.
2. Cada capa aplicará el patrón: `12/12 goals → analiza → prioridades → planifica → cola 1×1 → verifica/refuta → 20 alternativas si falla → siguiente → verificación global/LOOP → checklist/salida`.
3. Para cada capa se debe buscar primero código reutilizable en tres fuentes: `agentes/Core kernel Yaiwes`, `NCT core/wordflow code` y `Agentes-motores-Wordflow-YAIWES`.
4. Regla de implementación: **no reescribir código existente**; copiar el mecanismo necesario, ubicarlo en su capa y cablearlo mediante plugin/Enchufe Universal.
5. Se permite Dagu u otro orquestador solo si encaja; objetivo: **microkernel de flujo pequeño, modular, persistente y no monolítico**, limitado a las tareas del Wordflow LOOP.
6. Este bloque queda registrado; todavía no se programan nuevas capas hasta recibir el siguiente segmento o autorización específica del Director.
