# Sistema de trabajo — ACR / Reciclaje de código / Trigger / Cuenta B

## Alcance

Este documento consolida las capacidades que deben formar parte del método de trabajo y del Wordflow determinista. Se basa en las piezas ya presentes en el repositorio: AgentRegistry, adquisición de agentes, COPY-FIRST/REUSE-FIRST, workflow de creación de repositorios de Cuenta B y las reglas del método de trabajo.

## 1. ACR — resolución y registro de capacidades

El repositorio ya contiene un `AgentRegistry` basado en capacidades (`control-layer/agents/registry.py`). El registro mantiene manifests de agente y permite resolver agentes saludables por capacidad y grupo.

### Contrato operativo

```text
REQUEST CAPABILITY
      ↓
AGENT REGISTRY
      ↓
FILTER healthy=true
      ↓
MATCH capability
      ↓
OPTIONAL group
      ↓
SORT priority + cost_weight
      ↓
CANDIDATE AGENT
```

El sistema no debe asumir que un nombre de agente implica una capacidad. La capacidad debe estar declarada en el manifest.

### Gate

```text
capability missing → BLOCK
agent unhealthy → EXCLUDE
no candidate → BLOCK
```

## 2. Reciclaje de código

El método `PIPELINE/60_REUSE_FIRST.md` establece el principio:

```text
BUSCAR → LOCALIZAR → LEER/COMPARAR → EVALUAR → REUSE/COPY/ADAPT → TRANSFERIR → VERIFICAR → TEST
```

Orden de búsqueda:

1. repositorio actual
2. repositorios del proyecto
3. Wordflows relacionados
4. repositorios autorizados de la organización
5. repositorios externos autorizados

Cada candidato debe conservar:

```text
CANDIDATE_ID
SOURCE_REPOSITORY
SOURCE_PATH
SOURCE_COMMIT
SOURCE_VERSION
LICENSE
COMPATIBILITY
DEPENDENCIES
TEST_STATUS
REUSE_STATUS
```

Reglas:

- implementación existente compatible → REUSE/COPY-FIRST
- implementación existente parcialmente compatible → ADAPT_EXISTING
- no existe implementación → GENERATE_LAST
- si existe código reutilizable, REWRITE no debe sustituirlo arbitrariamente
- el origen se copia/recicla con provenance y hashes cuando aplique

## 3. Trigger — disparador

El trigger debe activar una misión determinista sin convertirse en una segunda autoridad.

```text
EVENT
  ↓
TRIGGER
  ↓
IDEMPOTENCY CHECK
  ↓
COMMAND CENTER
  ↓
ROUTER
  ↓
ORCHESTRATOR
  ↓
DAG
```

Un mismo `idempotency_key` no debe producir ejecuciones duplicadas.

Los triggers pueden iniciar adquisición, procesamiento, pruebas, publicación o creación de repositorios, pero todas las mutaciones deben pasar por la autoridad correspondiente.

## 4. Crear nuevos repositorios en Cuenta B

El repositorio ya contiene `.github/workflows/create-cuenta-b-repo.yml`. Ese workflow usa el secreto `EXTERNAL_GH_B_TOKEN`, recibe `owner`, `repo_name` y `private`, llama a la API de GitHub para crear el repositorio y acepta `201` como creación y `422` como posible existencia previa, seguida de verificación de acceso.

### Flujo determinista

```text
TRIGGER_CREATE_REPO
      ↓
VALIDATE OWNER / NAME / POLICY
      ↓
RESOLVE ACCOUNT B
      ↓
RESOLVE EXTERNAL_GH_B_TOKEN
      ↓
CREATE REPOSITORY
      ↓
IF 201 → CREATED
IF 422 → VERIFY EXISTING
ELSE → BLOCK
      ↓
READ-BACK
      ↓
EVIDENCE
      ↓
SHERIFF
      ↓
VERDICT
```

### Regla de seguridad

El token nunca debe aparecer en payloads, logs, código o documentación. Solo debe circular mediante el mecanismo de secretos y la capacidad/credential boundary del runtime.

## 5. Trigger Create + Wordflow

La capacidad debe quedar cableada como una operación del Wordflow:

```text
USER / SYSTEM EVENT
      ↓
TRIGGER.CREATE_REPOSITORY
      ↓
COMMAND CENTER
      ↓
ACCOUNT RESOLVER
      ↓
CREDENTIAL BROKER
      ↓
CREATE-REPO PROVIDER
      ↓
REMOTE READ-BACK
      ↓
EVIDENCE
      ↓
SHERIFF
      ↓
VERDICT AUTHORITY
```

El agente puede solicitar la operación, pero no debe saltar directamente a una ruta lateral de `curl`/`git push` fuera de la autoridad de deployment/provisioning.

## 6. Integración con el método de trabajo

La cadena base continúa siendo:

```text
CONTEXT/HANDOFF
→ COPY-FIRST SCAN
→ IMPLEMENT(COPY|ADAPT|GENERATE)
→ WIRE
→ FORENSIC VERIFY
→ VERDICT AUTHORITY
→ CLOSED | FIX LOOP
```

Y la publicación persistente continúa siendo:

```text
TASK_INTAKE
→ SANDBOX_BUILD
→ LOCAL_VERIFY
→ GITHUB_PUBLISH
→ REMOTE_VERIFY
→ FORENSIC_AUDIT
→ DONE
```

Este documento añade ACR/capability resolution, REUSE-FIRST, Trigger y Cuenta B sin sustituir las reglas anteriores.

## 7. Acceptance tests

- Resolver agente por capacidad y no por nombre.
- Rechazar manifest sin capacidades.
- Reutilizar implementación existente antes de generar.
- Preservar source commit/provenance durante reciclaje.
- Trigger duplicado con misma idempotency key → no duplicar ejecución.
- Cuenta B sin credencial → BLOCK.
- Cuenta B con credencial inválida → BLOCK.
- Create repo `201` → verificar remoto.
- Create repo `422` → comprobar si realmente existe y es accesible.
- Cualquier otro HTTP → BLOCK.
- Token nunca visible en evidencia/logs/payloads.
- PASS únicamente desde VerdictAuthority.
