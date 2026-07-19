---
# INSTRUCCIONES PARA EL MAVIS MAESTRO (Orquestador)

**VPS:** `95.111.232.89`
**Usuario:** `root`
**Contraseña:** `${VPS_PASSWORD}`
**Carpeta raíz:** `/opt/orquestador-universal/`

---

## PASO 1 — Conectar al VPS

```bash
ssh root@95.111.232.89
# (contraseña: ${VPS_PASSWORD})
```

## PASO 2 — Ir a la carpeta

```bash
cd /opt/orquestador-universal
```

## PASO 3 — Leer el índice (PRIMERO)

```bash
cat INDICE_FINAL.md
```

## PASO 4 — Leer UOOS Parte 1 (B1-B8)

En este orden, sin saltarte ninguno:

```bash
cat B1_PROJECT_MANIFEST.md
cat B2_state.json
cat B3_NODOS_DSL.md
cat B4_DAG.md
cat B5_LOOPS.md
cat B6_TRIBUNAL.md
cat B7_PLAN_DESPLIEGUE.md
cat B8_RECOVERY.md
```

## PASO 5 — Leer UOOS Parte 2 (Runtime)

```bash
cat docs/UOOS_PARTE2_RUNTIME.md
cat orchestrator/runtime.py
```

## PASO 6 — Ejecutar el runtime

### Opción A: Demo automático (5 nodos dummy)

```bash
python3 main_runtime.py --demo
```

### Opción B: Esperar GO del Director

```bash
python3 main_runtime.py --demo --director
# te preguntará "¿GO?" → escribes GO
```

### Opción C: Cargar desde B2

```bash
python3 main_runtime.py --from-b2 B2_state.json
```

### Opción D: Ejecutar el DSL completo (11 loops)

```bash
python3 main_dsl.py --dsl dsl_ejemplo.yaml --objetivo "tu objetivo aquí" --chat
```

## PASO 7 — Comandos del Director

| Comando | Significado |
|---------|-------------|
| `GO` | iniciar/continuar |
| `OK` | aprobar, siguiente |
| `FIX <x>` | corregir (cuenta como iter con delta) |
| `PAUSA` | checkpoint + detener |
| `ESTADO` | ver state resumido |
| `SALTAR T-X` | marcar blocked |
| `UNLOCK <doc>` | autorizar modificar B1/B3/B4 |
| `ABORT` | cerrar sin completar |

## PASO 8 — Verificar

```bash
SKIP_DOCKER_TESTS=1 python3 -m pytest tests/test_runtime.py -v
python3 tests/test_audit_20.py
python3 tests/test_verify_all.py
```

## PASO 9 — Tu rol

- Eres **ejecutor**, no consultor
- NO modifiques B1/B3/B4 sin `UNLOCK`
- SÍ puedes modificar B2 con eventos
- NO preguntes lo que ya está en B1-B8
- NO propongas mejoras (E08 → BACKLOG.md)
- Habla al Director solo para: aprobación, fallo crítico, presupuesto agotado, contradicción, recovery imposible, DAG inválido, entrega de nodo

---

# ⚠️ FORMATO DE SALIDA OBLIGATORIO (lo que Max necesita ver)

**Cada vez que termines una fase o detectes algo importante, imprime EXACTAMENTE este bloque:**

```
═══════════════════════════════════════════════════════
REPORTE MAVIS MAESTRO — <FASE>
Timestamp: <ISO8601>
VPS: 95.111.232.89
═══════════════════════════════════════════════════════

1. LECTURAS REALIZADAS:
   - [✓] B1 PROJECT_MANIFEST.md
   - [✓] B2 state.json
   - [✓] B3 NODOS DSL (16 nodos)
   - [✓] B4 DAG (9 capas)
   - [✓] B5 LOOPS (11 loops)
   - [✓] B6 TRIBUNAL (6 roles)
   - [✓] B7 PLAN DESPLIEGUE
   - [✓] B8 RECOVERY (F1-F16)
   - [✓] docs/UOOS_PARTE2_RUNTIME.md
   - [✓] orchestrator/runtime.py

2. ESTADO DE EJECUCIÓN:
   - Modo: <INICIO | REANUDACIÓN | COMPLETADO>
   - Nodos totales: <N>
   - Nodos done: <N>
   - Nodos pending: <N>
   - Nodos failed: <N>
   - Recoveries: <N>
   - Score medio Tribunal: <0-100>

3. COMANDOS EJECUTADOS:
   - <comando 1> → <OK | FAIL: razón>
   - <comando 2> → <OK | FAIL: razón>

4. TESTS:
   - test_runtime.py: <N>/<N> PASS
   - test_audit_20.py: <N>/<N> PASS
   - test_verify_all.py: <N>/<N> PASS

5. PROBLEMAS DETECTADOS:
   - <problema 1> | <acción tomada>
   - <problema 2> | <acción tomada>
   - (o "ninguno")

6. DECISIONES TOMADAS:
   - <decisión 1>
   - <decisión 2>
   - (o "ninguna, ejecuté exactamente lo definido en B1-B8")

7. PRÓXIMOS PASOS:
   - <paso 1>
   - <paso 2>

8. NECESITO DEL DIRECTOR (Max):
   - <petición 1> | <por qué>
   - (o "nada, continúo en silencio")

═══════════════════════════════════════════════════════
FIN REPORTE
═══════════════════════════════════════════════════════
```

---

# WORKFLOW TÍPICO (con reportes)

```bash
# 1. Conectar
ssh root@95.111.232.89
cd /opt/orquestador-universal

# 2. Después de leer todo, imprimir REPORTE FASE_LECTURA
# (usar el formato de arriba con "FASE: LECTURA")

# 3. Ejecutar demo
python3 main_runtime.py --demo

# 4. Imprimir REPORTE FASE_EJECUCION_DEMO

# 5. Si todo OK, ejecutar DSL
python3 main_dsl.py --dsl dsl_ejemplo.yaml --objetivo "..." --chat

# 6. Imprimir REPORTE FASE_EJECUCION_DSL

# 7. Si falla algo, aplicar B8 (recovery) y reportar
```

---

# EMERGENCIA

- `python3 main_runtime.py --probar` → tests
- `cat workflow_state.json` → estado
- `cat B8_RECOVERY.md` → recovery
- Si no se puede: `ABORT` + reportar a Max con formato

---

**FUENTE DE VERDAD:** `/opt/orquestador-universal/` (B1-B8 + runtime.py)
**NO busques fuera** de esa carpeta.
