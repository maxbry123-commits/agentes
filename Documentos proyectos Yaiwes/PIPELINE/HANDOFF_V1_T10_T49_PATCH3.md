# HANDOFF PATCH3 — cierre gap bloqueante T10 + veredicto final
**NO editar:** HANDOFF · PATCH · PATCH2  
**Fecha:** 2026-08-18  
**Anclas:** HANDOFF → PATCH → PATCH2 → **PATCH3**

---

## Gap bloqueante encontrado (re-audit final)

### B1 — T10 validación de ficha vs JSON real
El handoff decía validar `id` o `name`.  
El archivo real en GH **no trae** `id` ni `name`.

**Path real:** `extensions/wordflow_kernel/ficha.v2.json`  
**Claves reales (extraídas del repo):**
- `artifact_id` (identificador principal) = `wordflow.kernel.extension`
- `abi_version` = `2.0`
- `extension_type`, `kernel_min`, `mount_mode`, `load_priority`
- `llm_control` = `DENY`
- `provides` (lista)
- `contracts` (dict)
- `security` (dict; `fail_closed: true`)
- `entry_points` (dict)

**Código existente** `ficha_loader.py` ya tiene:
- `CapabilityRegistry` (register/get/list)
- `load_ficha(path) -> dict`
- `load_and_register(path, registry) -> str` usando `id` o `name` o `path.stem`

### Qué programar en T10 (corrección obligatoria)
**ADAPT** `extensions/wordflow_kernel/ficha_loader.py` (no crear archivo paralelo):

1. `validate_ficha(data: dict) -> list[str]`:
   - Error si no es dict
   - Error si falta identificador: aceptar **`artifact_id` OR `id` OR `name`**
   - Error si falta versión: aceptar **`abi_version` OR `version`**
   - Opcional: si existe `llm_control` y T12 exige DENY, no fallar aquí salvo regla explícita (T12)
2. `load_and_register`:
   - `cap_id = data.get("artifact_id") or data.get("id") or data.get("name") or path.stem`
3. `register_capability` puede ser alias de `registry.register`
4. Smoke `__main__`:
   - load del `ficha.v2.json` junto al módulo
   - validate → lista vacía
   - register → print cap_id

**Criterio DONE T10 actualizado:** smoke con ficha real del repo PASS (artifact_id reconocido).

---

## Re-audit 4 pasadas (post B1)

| Pasada | Resultado |
|--------|-----------|
| 1 · 40 tareas listadas | PASS |
| 2 · HANDOFF+PATCH+PATCH2+PATCH3 | PASS |
| 3 · Sim T10 con JSON real | PASS si se aplica B1 |
| 4 · ¿Queda gap **bloqueante**? | **NO** |

### No bloqueantes (operativos, ya documentados)
- Inventariar árbol antes de GENERATE (PATCH1 G-H1)
- Path A vs B → elegir existente (PATCH2 R2)
- Actualizar TAREAS_ACTUAL (PATCH2 R3)
- Leer SPEC_HTML en GH para T41 (archivo existe)
- Fuera de V1 (Kimi fusion, etc.) — no son tareas V1

---

## Veredicto final
**No quedan gaps bloqueantes ni información faltante crítica para programar V1 T10→T49**, siempre que la otra instancia lea:

1. https://github.com/maxbry123-commits/agentes/blob/main/PIPELINE/HANDOFF_V1_T10_T49.md  
2. https://github.com/maxbry123-commits/agentes/blob/main/PIPELINE/HANDOFF_V1_T10_T49_PATCH.md  
3. https://github.com/maxbry123-commits/agentes/blob/main/PIPELINE/HANDOFF_V1_T10_T49_PATCH2.md  
4. https://github.com/maxbry123-commits/agentes/blob/main/PIPELINE/HANDOFF_V1_T10_T49_PATCH3.md  

**Primera tarea: T10** con validación `artifact_id` / `abi_version`.

Si en ejecución aparece un gap nuevo de producto → `PATCH4` aditivo; no editar estos cuatro archivos sin orden del Director.

**Estado:** READY_FOR_T10
