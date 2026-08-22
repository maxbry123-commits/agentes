# GUÍA COMPLETA — Cableo Cuenta A ↔ B ↔ C (remoto, 0% LLM)

**Repo:** `maxbry123-commits/agentes`  
**Rama:** `main`  
**Enlace:** https://github.com/maxbry123-commits/agentes/blob/main/GUIA_CUENTAS_REMOTE.md  

**Regla de oro:** el agente solo entrega `dest` + `account_id` + `token_ref` + datos. El código es fail-closed. Nunca PAT en chat/YAML.

---

## 0. Mapa de las 3 cuentas

| Nombre | Owner GitHub | Rol | Secret en Cuenta A |
|--------|--------------|-----|--------------------|
| **Cuenta A** | `maxbry123-commits` | Origen. Código Wordflow + **todos los secrets** | (login nativo del runner) |
| **Cuenta B** | `abc1tienda-web` | Destino software/memoria (ej. `Wordflow-1`) | `EXTERNAL_GH_B_TOKEN` |
| **Cuenta C** | *(username que indiques)* | Segundo destino / espejo | `EXTERNAL_GH_C_TOKEN` |

**Alias normalizados en código**

| Alias | Owner real |
|-------|------------|
| `abc1`, `abc1tienda`, `abc1tienda-web`, `cuenta_b`, `cuenta-b` | `abc1tienda-web` |
| `cuenta_c`, `cuenta-c`, `github_c`, `c` | owner de Cuenta C (config en yaml) |

**Repo del cableo (este):** https://github.com/maxbry123-commits/agentes  

**NO es este repo:** https://github.com/maxbry123-commits/Agentes-motores-Wordflow-YAIWES  

---

## 1. Dónde están los tokens / secrets

**Único lugar donde se guardan los PAT:**

→ **Cuenta A** → repo `agentes` → Settings → Secrets and variables → Actions  

**Enlace directo:**  
https://github.com/maxbry123-commits/agentes/settings/secrets/actions

| Nombre del secret | Qué es | Scope del PAT |
|-------------------|--------|---------------|
| `EXTERNAL_GH_B_TOKEN` | PAT de **Cuenta B** | `repo` |
| `GITHUB_B_TOKEN` | Alias opcional del mismo (o distinto) PAT B | `repo` |
| `EXTERNAL_GH_C_TOKEN` | PAT de **Cuenta C** | `repo` |
| `GITHUB_C_TOKEN` | Alias opcional del PAT C | `repo` |
| `HF_TOKEN` | Token HuggingFace (si se usa hf_b) | write |

**Cómo crear el PAT (logueado en B o en C):**  
https://github.com/settings/personal-access-tokens/new  

**Nunca** pegues `ghp_...` en el repo, en el chat ni en YAML. Solo referencias `env:NOMBRE`.

### Comprobar secrets

Actions → workflow `check-external-token-secret` → Run workflow  

O en CI:

```bash
python3 -c "import os; t=os.environ.get('EXTERNAL_GH_B_TOKEN',''); print('B', 'OK' if t else 'FAIL', len(t))"
python3 -c "import os; t=os.environ.get('EXTERNAL_GH_C_TOKEN',''); print('C', 'OK' if t else 'FAIL', len(t))"
```

---

## 2. Cómo se hace el cableo (A ↔ B ↔ C)

### Archivos

1. `GUIA_CUENTAS_REMOTE.md` ← esta guía  
2. `extensions/wordflow/connectors/external_accounts.yaml` ← account_id + credential_ref + owner  
3. `extensions/github_deploy/remote_ops.py` ← CRUD remoto  
4. `extensions/github_deploy/apply_push.py` ← apply → commit → push  
5. `extensions/github_deploy/credential_env.py` ← resuelve `env:` / `secret://`  
6. Workflows: `check-external-token-secret.yml`, `create-cuenta-b-repo.yml`, `validate-external-github.yml`

### account_id → secret

| account_id | token_ref | owner |
|------------|-----------|-------|
| `github_b` | `env:EXTERNAL_GH_B_TOKEN` | `abc1tienda-web` |
| `github_c` | `env:EXTERNAL_GH_C_TOKEN` | *(tu username C)* |
| `hf_b` | `env:HF_TOKEN` | — |

### Activar Cuenta C (checklist)

1. Crear cuenta GitHub C (si no existe): https://github.com/signup  
2. Crear PAT en C: https://github.com/settings/personal-access-tokens/new (scope `repo`)  
3. En Cuenta A añadir secret:  
   https://github.com/maxbry123-commits/agentes/settings/secrets/actions  
   Nombre: `EXTERNAL_GH_C_TOKEN` → valor = PAT de C  
4. Sustituir `REPLACE_CUENTA_C_OWNER` en `external_accounts.yaml` por el username real de C  
5. Run workflow `check-external-token-secret` → debe salir OK B y OK C  

### Comunicación entre las 3

```
Cuenta A (agentes + secrets)
    │  token B ──► API GitHub como B  → crear/leer/editar/borrar repos en abc1tienda-web
    │  token C ──► API GitHub como C  → crear/leer/editar/borrar repos en owner-C
    └─ (mismo código remote_ops / apply_and_push; solo cambia account_id + token_ref + owner)
```

No hace falta login en B ni en C. Todo sale desde A con el secret correspondiente.

---

## 3. Capacidades (B y C iguales)

| Operación | Función / remote_op | token_ref típico |
|-----------|---------------------|------------------|
| Identificar owner | aliases B/C | — |
| Crear repo | `create_repo` / `remote_op("create_repo")` | B o C |
| Leer archivo | `get_file` / `remote_op("read")` | B o C |
| Head SHA | `get_head` / `remote_op("head")` | B o C |
| Listar árbol | `list_tree` / `remote_op("tree")` | B o C |
| Listar repos del token | `list_repos` / `remote_op("repos")` | B o C |
| Escribir / editar | `write_files` / `remote_op("edit")` | B o C |
| Borrar | `delete_paths` / `remote_op("delete")` | B o C |
| Verificar | `verify_file` / `verify_head` | B o C |

Flag: `GITHUB_DEPLOY_REAL=1` = writes reales; sin flag = `DRY_RUN`.

---

## 4. Contrato del agente (payload)

### Hacia B

```json
{
  "account_id": "github_b",
  "token_ref": "env:EXTERNAL_GH_B_TOKEN",
  "dest": {
    "provider": "github",
    "owner": "abc1tienda-web",
    "repo": "Wordflow-1",
    "branch": "main"
  },
  "files": [{"path": "pkg/hello.py", "content": "print('hola')\n"}],
  "commit_message": "wordflow apply"
}
```

### Hacia C

```json
{
  "account_id": "github_c",
  "token_ref": "env:EXTERNAL_GH_C_TOKEN",
  "dest": {
    "provider": "github",
    "owner": "REPLACE_CUENTA_C_OWNER",
    "repo": "frontend",
    "branch": "main"
  },
  "files": [{"path": "src/App.tsx", "content": "..."}],
  "commit_message": "wordflow apply C"
}
```

### API Python

```python
from extensions.github_deploy.remote_ops import remote_op

# B
remote_op("edit", owner="abc1", repo="Wordflow-1",
          files=[{"path": "a.py", "content": "x=1\n"}],
          token=token_b, dry_run=False)

# C
remote_op("edit", owner="REPLACE_CUENTA_C_OWNER", repo="frontend",
          files=[{"path": "a.py", "content": "x=1\n"}],
          token=token_c, dry_run=False)

remote_op("create_repo", name="frontend", token_ref="env:EXTERNAL_GH_C_TOKEN")
remote_op("read", owner="...", repo="frontend", path="README.md", token=token_c)
remote_op("delete", owner="...", repo="frontend", paths=["old.js"], token=token_c)
```

---

## 5. Transferir un repo de Cuenta A → B o A → C

### Opción 1 — Transferencia nativa GitHub (cambia el dueño)

1. Entra al repo en **Cuenta A** (ej. `maxbry123-commits/frontend`)  
2. **Settings** → General → abajo del todo → **Transfer ownership**  
3. Escribe el owner destino:
   - B: `abc1tienda-web`
   - C: *(username de Cuenta C)*  
4. Confirma. El repo pasa a `abc1tienda-web/frontend` (o C).  
5. Historial, issues y URL de dueño cambian. El original en A deja de existir bajo ese path.

Requisitos: permisos admin en origen; la cuenta destino debe poder aceptar (o ser org con permiso).

### Opción 2 — Espejo con Wordflow (copia contenido, no transfiere)

Desde A, sin login en B/C:

```python
# 1) Crear repo vacío en destino
remote_op("create_repo", name="frontend",
          token_ref="env:EXTERNAL_GH_B_TOKEN",  # o EXTERNAL_GH_C_TOKEN
          private=True, dry_run=False)

# 2) Subir archivos
remote_op("edit", owner="abc1tienda-web", repo="frontend",
          files=[{"path": "src/App.tsx", "content": open("src/App.tsx").read()}, ...],
          token=token_b, dry_run=False)

# 3) Verificar
remote_op("verify_file", owner="abc1tienda-web", repo="frontend",
          path="src/App.tsx", token=token_b, expect_content="...")
```

El repo original en A **sigue existiendo**. Tienes dos copias.

### Opción 3 — Fork

En la UI de GitHub del repo A, **Fork** hacia la cuenta B o C. Copia ligada al upstream; luego se puede desligar.

### ¿Cuál elegir?

| Objetivo | Método |
|----------|--------|
| Mover de verdad (un solo dueño) | Transfer (opción 1) |
| Copia en B/C y dejar original en A | Espejo remote_ops (opción 2) |
| Copia rápida ligada | Fork (opción 3) |

---

## 6. Comandos de prueba

```bash
# Unit tests remote_ops (offline, FakeHTTP)
PYTHONPATH=. python -m pytest extensions/github_deploy/tests/test_remote_ops.py -v

# Unit tests apply_push
PYTHONPATH=. python -m pytest extensions/github_deploy/tests/test_apply_push.py -v

# Comprobar secrets en Actions
# → workflow check-external-token-secret → Run workflow
```

Prueba real (solo con secret + `GITHUB_DEPLOY_REAL=1`, en CI o máquina controlada):

```bash
export EXTERNAL_GH_B_TOKEN=***   # no commitear
export EXTERNAL_GH_C_TOKEN=***   # no commitear
export GITHUB_DEPLOY_REAL=1
PYTHONPATH=. python - <<'PY'
from extensions.github_deploy.remote_ops import list_repos
import os
print(list_repos(token=os.environ["EXTERNAL_GH_B_TOKEN"]))
PY
```

---

## 7. Reglas fail-closed

| Situación | Resultado |
|-----------|-----------|
| PAT crudo (`ghp_`) | `RAW_TOKEN_FORBIDDEN` |
| Token env no set | `TOKEN_REF_UNRESOLVED` |
| Path protegido | `PROTECTED_PATH` / HOLD |
| force=true | `FORCE_PUSH_DENIED` |
| expected_head mismatch | `HEAD_CONFLICT` |
| Sin `GITHUB_DEPLOY_REAL=1` | `DRY_RUN` |
| Owner C = `REPLACE_CUENTA_C_OWNER` | No usar en REAL hasta sustituir |

`llm_control: DENY` siempre en este path.

---

## 8. Resumen

- **Secrets:** solo en https://github.com/maxbry123-commits/agentes/settings/secrets/actions  
- **B activo:** `EXTERNAL_GH_B_TOKEN` + owner `abc1tienda-web`  
- **C cableado en config:** falta secret `EXTERNAL_GH_C_TOKEN` + username real en yaml  
- **Misma API** (`remote_ops` / `apply_and_push`) sirve para B y C  
- **Transfer A→B/C:** Settings → Transfer ownership, o espejo con `create_repo` + `write_files`

**Enlace guía:** https://github.com/maxbry123-commits/agentes/blob/main/GUIA_CUENTAS_REMOTE.md
