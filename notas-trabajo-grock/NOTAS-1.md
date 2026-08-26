# NOTAS-1 — Auditoría chat 5 pasadas + INPUT BLOCKS literales

**Extensión de:** [NOTAS.md](./NOTAS.md)  
**Regla:** no reescribe NOTAS.md. Este archivo es el parche de auditoría.  
**Repo:** maxbry123-commits/agentes · **rama:** main  
**Fecha ancla:** 2026-08-26

Enlace de auditoría de este archivo:
https://github.com/maxbry123-commits/agentes/blob/main/notas-trabajo-grock/NOTAS-1.md

Base:
https://github.com/maxbry123-commits/agentes/blob/main/notas-trabajo-grock/NOTAS.md

Plan vivo (no tocar):
https://github.com/maxbry123-commits/agentes/blob/main/PIPELINE/PLAN_YAIWES_AGENTE_WORDFLOW.md

---

# PASADA 1 — ESTRUCTURA (qué se pidió, en orden)

1. Ubicar el Wordflow de LA TAREA del enlace  
   `PIPELINE/PLAN_YAIWES_AGENTE_WORDFLOW.md`  
   No mezclar repos. No inventar raíces. Mostrar README de arquitectura de cada Wordflow.
2. El enlace de trabajo es la raíz de referencia. Había desorden en `main` (imagen: PIPELINE, Refactoria, TASK-GAPS, agente-yaiwes, code-programming-engine, control-layer, despliegue, extensions, wordflow, agents, …).
3. Quedan **solo 6 raíces** en `main` (más este block de notas Grok, autorizado después).
4. Tres salidas: S1 Grok · S2 plan para GPT · S3 Grok plantilla-molde.
5. Después de esas salidas: 2 simulaciones + 3 ask-council sobre el molde, sin dañarlo.
6. Fase 2 se ANOTA ahora y se EJECUTA solo cuando S1+S2+S3+simulaciones/council estén cerrados.
7. Fase 3, 4, 5 = mismo método que Fase 2.
8. `notas-trabajo-grock` = state/crazy wall de Grok. Input aprobado nuevo = archivo nuevo. 100% PASS → borrar ESE archivo de notas.

---

# PASADA 2 — CONECTIVIDAD (cómo se cablea)

```text
Plan X-N
    → Desplegar/Desplegar N/          docs + code que el Director sube
    → Refactoria/refactoria-plan-x-N/ versiones VIEJAS a modificar
    → raíz destino canónica           Yaiwes wordflow  o  Wordflow Code
    → PIPELINE/                       plan vivo de ESA misión + molde universal
    → Método de trabajo               reglas; parche si falta, no rewrite
```

- `Desplegar 1` es SOLO ejemplo del primer lote. Cada plan nuevo tiene su `Desplegar N`.
- `Refactoria` no es edición in-place. Se copia el archivo viejo ahí, se escribe el nuevo aparte, verificación cruzada ×3, luego se integra. El viejo se borra solo con autorización + 3 verificaciones.
- README de cada Wordflow = ancla (enlace exacto + qué es la raíz + mapa de `main`).
- Parches README:

```text
Yaiwes wordflow/Readme/
Yaiwes wordflow/Readme/Readme1/
Yaiwes wordflow/Readme/Readme2/
```

Igual en Wordflow Code y en método de trabajo.

- Microkernel / Plugin Architecture = patrón de industria (no invento).
  - extension point / plugin contract ≈ lo que se llamó abi-mount
  - Plugin Registry ≈ lo que se llamó capability-registry
  - ciclo de vida del núcleo ≈ lo que se llamó mount-guard
  - `wordflow/abi.py` (`ExtensionABI`) = implementación concreta del extension point EN ESTE REPO
- `extension-kernel` es UN NODO EJEMPLO dentro de Yaiwes. **Prohibido** meter todo lo nuevo ahí.
- Hot path operativo hoy (no apagar): `extensions/wordflow/engine/code_path_runner.py` hasta que el rename a `Wordflow Code` quede anclado en README.

---

# PASADA 3 — COMPORTAMIENTO (qué se hace / qué no)

HACER:
- Leer INPUT BLOCK literal en cada turno.
- Copiar, no reescribir bases.
- Crear archivo nuevo = parche + enlace al anterior.
- Si algo ya no sirve → borrar el parche, no “reparar” el base.
- PASS solo con evidencia en GitHub (read-back).
- Gaps OPEN explícitos. No fake PASS.
- De Grupo-Trabajo-1: COPIAR guías/método que NO estén ya en agentes. No reescribir esas guias.

NO HACER:
- Inventar nombres de raíces.
- Crear archivos fuera de raíz autorizada / sin autorización.
- Reescribir `PLAN_YAIWES_AGENTE_WORDFLOW.md`.
- Tratar `PLAN_100_ESTRUCTURA_DEFINITIVA.md` como el plan de trabajo (es mapa de árbol YAIWES, otro archivo).
- Hardcodear `Desplegar 1` en la plantilla.
- Tirar todo a `extension-kernel/`.
- Mezclar PIPELINE-HUGGINGFACE (contenido HF) dentro de agentes.
- Ejecutar Fase 2 antes de cerrar S1 S2 S3 + 2 simulaciones + 3 council.
- Declarar limpieza hecha sin X-Ray + notice.
- Editar hot path sin paridad de tests.

---

# PASADA 4 — COMPLETITUD (todo el input del chat, bloque a bloque)

## IB-00 — Plan de la tarea (enlace original Director)

Path: `PIPELINE/PLAN_YAIWES_AGENTE_WORDFLOW.md`  
Commit que el Director pegó (histórico): `b7c9b89fa0f655943dc40ecab4af505f8bf857de`  
HEAD main al auditar: archivo sigue vivo con el mismo nombre.

Ese archivo ES el plan de trabajo de la misión YAIWES. No se toca.
Contiene: sistema Refactoria source/new + 3 verificaciones, fuentes canónicas, reglas, S1–S12, gaps G1–G7, hot path `code_path_runner.py`.

## IB-01 — Pedido inicial
Ubicar Wordflow de ESA tarea en `main`. Cómo se llama. Revisar README del Wordflow con estructura raíz.

## IB-02 — Corrección de mezcla
No mezclar `wordflow/` ABI + `extensions/wordflow/` + `agente-yaiwes/`.  
El enlace del plan es la referencia de trabajo. Revisar README. Debe existir estructura raíz que coincida con el trabajo. La imagen muestra desorden no autorizado.

## IB-03 — Seis raíces únicas de main (texto Director)

1. Desplegar — UNA raíz. No dos nombres.  
   `Desplegar 1` = primer lote subido para trabajar.  
   `Desplegar/Desplegar 1/`, `Desplegar 2/`, `Desplegar 3/` — cada uno es fuente de verdad de UN plan.  
   Ejemplo dado por el Director: la tarea del plan S2 se vincula a los archivos de Desplegar 1.
2. PIPELINE — lo único vivo al inicio es el plan que pasó. El resto de PIPELINE = basura a depurar (S2). S3 añade el MOLDE (archivo nuevo), no sustituye el plan.
3. Método de trabajo — no se toca el base.
4. Refactoria — copia versión anterior / archivo a modificar. No se edita el original in-place. Se usa de referencia para escribir el nuevo. Verificación cruzada. Auditado → se borra el viejo (con regla de 3 verificaciones + autorización).
5. Wordflow YAIWES (nombre autorizado en main: **Yaiwes wordflow**).
6. Wordflow Code.

Objetivo: organizar el repo. Preparar plan para que lo haga GPT. Limpiar basura que no sea code de esas raíces. Primero entender; no ejecutar hasta orden.

Prompt GPT de gaps (adjunto Director, recorte): por cada gap `despliegue/refactoria/<gap>/source/` + `new/`. No fake PASS. Hot path intacto. G1/G3 CLOSED con artifacts canónicos o BLOCKER. G2 schemas solo stages reales. G4–G7 CLOSED solo con evidencia; si no, OPEN. Sin source G5/G6/G7 → BLOCKER, no inventar body.

## IB-04 — Mostrar raíces, no solo enlaces
Mostrar raíz Yaiwes y raíz Wordflow Code. Luego explicar. Buscar README de referencia de CADA Wordflow donde sale la arquitectura que debe tener esa raíz y MOSTRARLA en el chat. No inventar nombres.

Hallazgo de repo (hecho, no es input; se registra para no perderlo):
- Arquitectura Yaiwes: `agente-yaiwes/PLAN_100_ESTRUCTURA_DEFINITIVA.md` + `STRUCTURE.md` + `README.md`  
  PLAN_100 ≠ plan de trabajo. Es mapa de árbol.
- Arquitectura Wordflow Code: `PIPELINE/ARQUITECTURA_03_WORDFLOW.md` + árbol real `extensions/wordflow/`.

## IB-05 — Método README / no rewrite (texto Director)
Cambiar nombres de las 2 raíces. En el README de cada Wordflow: enlace + nota exacta para que Grok/GPT/agentes no se pierdan. El README debe explicar qué hay y qué significa cada raíz de `main`. Prohibido crear archivos nuevos sin autorización ni fuera de la raíz de trabajo. Si no se manda eliminar, el archivo nuevo es PARCHE. Ejemplo: `Yaiwes wordflow/Readme/Readme1/Readme2/`. Cada README parche se conecta con enlace y raíz. Mismo método en método de trabajo: la AI al reescribir borra información y entra en bucle commit/push; la solución es parche nuevo o borrar lo inútil. Aplicar a todo archivo nuevo.

Cablear sin tocar el archivo base: sí. El ejemplo de code es registro de capacidades (una línea genérica una vez; kernels nuevos = fila al registro). Ese formato es obligatorio en planes, método, README, docs y code.

## IB-06 — Microkernel (adjunto Director, frase canónica)

Nombre de industria: Microkernel Architecture = Plugin Architecture.

Frase para README (citable):

> El sistema sigue el patrón de Microkernel Architecture (también conocido como Plugin Architecture): un núcleo mínimo (`kernel-principal`) que expone puntos de extensión y un registro de plugins, permitiendo añadir capacidades nuevas sin modificar el núcleo. `wordflow/abi.py` (`ExtensionABI`) es la implementación concreta de ese punto de extensión en este repositorio.

Tabla Director:
| Nombre interno usado | Nombre industria |
| abi-mount | Extension point / plugin contract |
| capability-registry | Plugin Registry |
| mount-guard | ciclo de vida del núcleo (no patrón aparte tan formal) |
| ExtensionABI / attach_to_wordflow_extension | extension point concreto |

## IB-07 — Tres salidas (texto Director)

Salida 1 — Grok: 2 README; luego cambiar y crear en main lo dicho; auditoría forense X-Ray para depurar basura; definir qué es lo único que queda; mostrar notice.

Salida 2 — Crear el plan de depuración para GPT. Grok no ejecuta esa limpieza.

Salida 3 — Grok lo hace, no GPT. En PIPELINE debe existir:
1. Tomar el plan que pasó, copiarlo EXACTO, convertirlo en plantilla: ELIMINAR las tareas de dentro, dejarlo como MODELO universal para replicar en todos los planes.
2. Mejoras del molde:
   - Schema en cada nodo.
   - Lugar de checkpoint donde Grok y GPT escriben cada tarea cerrada al 100%.
   - 3.1 Enrutar el plan con el enlace de la raíz Desplegar (patrón N, no Desplegar 1 fijo).
   - 3.2 Instrucción de extensión/parche en todos los archivos para no volver a tocar el base. El adjunto Microkernel va en README + método + plantilla. `extension-kernel` = EJEMPLO, no destino universal.
   - 3.3 Revisar el repo agentes, comparar con este plan, ver qué más incluir. Revisar Grupo-Trabajo-1 métodos y TODAS las guías; COPIAR (no reescribir) lo que no esté ya en el método de agentes.
   - 3.4 La plantilla debe tener todas las guías enlazadas y cómo se copia un archivo, cómo se saca un ZIP, cómo se hace el trabajo. Bien estructurada.
   - Referencia de estructura: https://github.com/maxbry123-commits/Grupo-Trabajo-1/blob/main/PIPELINE-HUGGINGFACE.md  
     (referencia de PIPELINE vivo / registro. NO copiar contenido HF a agentes.)
4. Buscar qué más se puede mejorar del PLAN/MOLDE. El plan que pasó es el enlace YAIWES.

Corrección explícita posterior (no alucinar S3):
- No es “copia del plan + el mismo plan mejorado al lado con las tareas YAIWES”.
- Es: original intacto + archivo NUEVO molde SIN las tareas de esa misión.

Cableado en el molde (ejemplo Director):
Plan X número 2 → Desplegar 2 → archivo viejo a crear/modificar → `Refactoria/refactoria-plan-x-2/`.

## IB-08 — Post-salidas + Fase 2 anotada (texto Director)

Después de terminar S1 S2 S3:
- 2 simulaciones
- 3 ask-council distintos
Objetivo: qué se puede mejorar del plan-modelo-plantilla SIN dañarlo.

Anotar para el FINAL (luego de salidas pendientes) la Fase 2.

Qué es Fase 2:
Paso 1. El Director sube a Desplegar un lote de documentos y archivos de code.
Paso 2. Auditoría forense X-Ray verificación cruzada de los documentos y el código fuente. Se audita 4 u 8 veces según lo que se consiga. Lo que se consigue se va haciendo checkpoint dentro de lo que será el nuevo plan de trabajo. Goals de 12 pasos. Qué buscamos:
- Qué está en los documentos/archivos subidos a Desplegar y qué no está en el código fuente del Wordflow.
- Qué está incompleto y qué se puede mejorar.
- Dónde se ubica y por qué (justificación).
- Qué existe, qué rompe, qué bloquea, qué falta.
- Cómo se soluciona.
- Y así varios 12 goals más.
Paso 3. Grok usa el prompt de Grok de chat 1 SOLO para mandar a diseñar el code que falta, y lo entrega al Director para mandarlo a diseñar con los estándares de ese prompt, colocando el sistema plugins de extensión.
Paso 4. El Director sube los archivos con el code nuevo. Se revisan y debaten los cambios para aprobar.
Paso 5. Grok revisa que esté todo y crea el nuevo plan usando los code que están en la nueva extensión de Desplegar. Si hay archivos que requieren modificarse, Grok crea la extensión de Refactoria y conecta y cablea todo el trabajo: Refactoria, Desplegar, Plan, trazabilidad de archivos a modificar, guías, métodos de trabajo, arquitectura raíz donde va cada archivo. Queda cableado para que GPT trabaje sin salirse de la ruta.

Luego Fase 3, 4 y 5 + el mismo método.

## IB-09 — notas-trabajo-grock (texto Director)
Crear en main `notas trabajo grock`. Usarlo como block de notas. Cada input nuevo aprobado se anota cableado con plugins/extensión desde el primero. Nunca reescribir el archivo: solo crear uno nuevo. Si la tarea se terminó 100%, borrar el archivo. Equivale a state JSON y crazy wall.

## IB-10 — Este turno
Auditar el chat 5 pasadas. Anotar TODO input block leer literal en ese archivo. Dar el enlace para auditar a Grok. Completo y detallado. No hacer repetir las instrucciones.

---

# PASADA 5 — CIERRE / ESTADO / SIGUIENTE

## Lo único autorizado a vivir en main (tras S1)

1. Desplegar/
2. PIPELINE/  (plan vivo + molde S3)
3. Método de trabajo
4. Refactoria/
5. Yaiwes wordflow/
6. Wordflow Code/
7. notas-trabajo-grock/  (solo estado Grok; no es Wordflow)

Todo lo demás hoy en main (agents, control-layer, TASK-GAPS, docs, groups, memory, scripts, tools, wordflow ABI suelto, extensions extras no ancladas, PIPELINE histórico, etc.) = candidato a basura en S2. `.github/workflows/` es excepción física de GitHub Actions (el README Yaiwes ya lo separa: workflows ejecutables solo ahí). No se inventa borrar Actions en S1.

## Hecho ya
- [x] Entendimiento de 6 raíces + 3 salidas + Fase 2 anotada
- [x] NOTAS.md base
- [x] NOTAS-1.md esta auditoría

## NO hecho (pendiente, en orden)
- [ ] Salida 1
- [ ] Salida 2 (plan GPT)
- [ ] Salida 3 (molde)
- [ ] 2 simulaciones del molde
- [ ] 3 ask-council del molde
- [ ] Fase 2 ejecución

## Criterio para no perder el hilo
INPUT BLOCK de este archivo + NOTAS.md + plan vivo en PIPELINE + GitHub = verdad.  
No memorizar el proyecto. No reescribir bases.

## Siguiente acción válida
Esperar orden explícita: **ejecuta Salida 1**.
