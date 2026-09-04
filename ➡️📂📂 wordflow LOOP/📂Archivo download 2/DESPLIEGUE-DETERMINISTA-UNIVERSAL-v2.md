```json
{
  "documento": "DESPLIEGUE_DETERMINISTA_UNIVERSAL",
  "version": "2.0",
  "que_mejora_de_v1": "el patron de Sonnet (organizador+desplegador+detector+push, 0% LLM) es correcto y probado (5 repos, 140 archivos, 0 perdidos, 11/11 tests) — v2.0 lo generaliza para CUALQUIER proyecto, cierra 5 debilidades detectadas y añade verificacion post-push",
  "principio": "el agente NUNCA decide como desplegar. Reglas fijas -> script. La orden al agente siempre es: 'ejecuta estos comandos exactos y reporta. No analices, no propongas, no decidas.'"
}
```

# DESPLIEGUE DETERMINISTA UNIVERSAL v2.0
### Documento reusable para cualquier despliegue a GitHub — 0% LLM

---

## 1. ANÁLISIS DEL MÉTODO DE SONNET (v1.0) — SÍ LO ENTIENDO

El patrón tiene 4 pasos encadenados, cada uno un script sin decisiones:

```
[carpeta caótica ~140 archivos]
   │
   ▼ PASO 1 · organizador.py — REGLAS fijas (prefijo/extensión → repo),
   │           primera que calza gana. mismo input = mismo output
   ▼ PASO 2 · desplegador.py — crea carpeta por repo, copia, git init+add
   │           +commit, README autogenerado. IDEMPOTENTE (2 corridas = igual)
   ▼ PASO 3 · detector_version.py — hash de hoy vs anterior:
   │           nuevo=minor · editado=patch · borrado=major. versiona SOLO
   ▼ PASO 4 · subir_a_github.sh — gh repo create + push, 1 comando
```

**Fortalezas confirmadas**: 0% LLM en decisiones, idempotencia real, semver automático por hash, orden al agente de 3 líneas, probado con git real.

**5 debilidades detectadas (auditoría del código)**:
1. **REGLAS hardcodeadas** en el .py — cambiar el mapa de repos exige editar código (viola su propio principio "config fuera del código", connections.yaml).
2. **Sin verificación post-push** — el script termina en push pero nadie confirma que lo remoto == lo local (el Witness del sistema exige evidencia; aquí falta).
3. **Sin dry-run** — no hay modo "muéstrame el plan sin tocar nada" para que el Director apruebe antes.
4. **Archivo sin regla → destino silencioso** (cae al repo por defecto) — un archivo mal clasificado se descubre tarde.
5. **Secrets sin escaneo** — nada impide subir un `.env` o una API key por accidente a un repo.

---

## 2. REDISEÑO v2.0 — UNIVERSAL (6 pasos, cierra las 5 debilidades)

```
[cualquier carpeta de proyecto]
   │
   ▼ PASO 0 · deploy_config.yaml  ← LO NUEVO: las reglas viven AQUÍ, no en código
   │   repos: {nombre: [patrones]} · default_repo · visibilidad · rama
   │   protected_patterns: [".env","*key*","*.pem","secrets*"]  ← bloqueo
   │
   ▼ PASO 1 · organizar --dry-run  ← LO NUEVO: PLAN sin tocar nada
   │   salida: plan.json {repo: archivos[], SIN_REGLA: [...], BLOQUEADOS: [...]}
   │   REGLA DURA: SIN_REGLA no vacío → EXIT 1 (nada silencioso)
   │              BLOQUEADOS no vacío → EXIT 2 (posible secret)
   │   → el Director aprueba el plan.json (o el pipeline con 18 checks lo hace)
   │
   ▼ PASO 2 · organizar + desplegar (igual que v1: copiar+git, idempotente)
   │
   ▼ PASO 3 · detector_version (igual que v1: semver por hash)
   │   + LO NUEVO: escribe CHANGELOG.md automático por repo
   │     (qué archivos causaron el minor/patch/major — trazabilidad)
   │
   ▼ PASO 4 · subir (gh repo create + push, igual que v1)
   │
   ▼ PASO 5 · verificar  ← LO NUEVO: evidencia post-push (patrón Witness)
   │   por repo: git ls-remote hash == hash local · conteo de archivos
   │   remoto == plan.json · tag semver existe
   │   salida: evidence.json {repo: {ok, hash, archivos, tag}}
   │   un solo ok:false → reporte EXACTO de qué repo y qué difiere
   └─► FIN: evidence.json = la prueba. Sin evidence, no está desplegado.
```

## 3. LA ORDEN UNIVERSAL AL AGENTE (copiar/pegar, sirve para cualquier proyecto)

```
Estás bajo despliegue determinista v2.0. NO analices, NO opines, NO propongas.
Solo ejecuta en orden y reporta la salida de cada uno. Si un comando falla,
detente y pega el error completo:

1. python3 despliegue/organizador.py --dry-run .          # plan
   [ESPERA mi OK sobre plan.json]
2. python3 despliegue/desplegador.py . ./repos_listos     # copiar+git
3. python3 despliegue/detector_version.py ./repos_listos  # semver+changelog
4. bash despliegue/subir_a_github.sh MI_USUARIO           # push
5. python3 despliegue/verificar.py ./repos_listos         # evidencia
6. pega evidence.json y detente.
```

## 4. QUÉ HAY QUE CONSTRUIR PARA v2.0 (delta mínimo sobre lo ya probado)

| Pieza | Estado | LOC est. |
|---|---|---|
| organizador/desplegador/detector/push | ✅ ya existen y probados | 0 (reusar) |
| deploy_config.yaml + loader (saca REGLAS del código) | nuevo | ~60 |
| --dry-run + EXIT por SIN_REGLA/BLOQUEADOS | nuevo | ~50 |
| escaneo protected_patterns | nuevo | ~30 |
| CHANGELOG.md automático | nuevo | ~40 |
| verificar.py (evidencia post-push) | nuevo | ~80 |
| **Total nuevo** | | **~260 LOC** |

**v2.0 = el patrón de Sonnet intacto + config externa + freno de seguridad + prueba de que lo subido es lo planeado.** Sirve tal cual para el orquestador NCT, para UOOS, o para cualquier proyecto futuro: solo cambia el deploy_config.yaml.
