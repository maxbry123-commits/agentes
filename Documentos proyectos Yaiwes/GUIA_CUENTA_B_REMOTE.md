# GUÍA COMPLETA — Trabajar a distancia en Cuenta B (sin login en B)

> **Nota:** Esta guía es **solo Cuenta B**.  
> Para cableo A ↔ B ↔ C, secrets de las 3 cuentas y transferir repos A→B/C, ver:  
> **[GUIA_CUENTAS_REMOTE.md](https://github.com/maxbry123-commits/agentes/blob/main/GUIA_CUENTAS_REMOTE.md)**

**Repo de esta guía:** `maxbry123-commits/agentes`  
**Rama:** `main`  
**Enlace canónico:** https://github.com/maxbry123-commits/agentes/blob/main/GUIA_CUENTA_B_REMOTE.md  

**Audiencia:** cualquier AI / agente / humano que deba operar Cuenta B desde Cuenta A.  
**Regla de oro:** 0% LLM decide el path de deploy. Solo entrega `dest` + `account_id` + `token_ref` + datos. El código es fail-closed.

---

## 0. Mapa de cuentas (no confundir)

| Nombre | Owner GitHub | Rol |
|--------|----------------|-----|
| **Cuenta A** | `maxbry123-commits` | Origen. Aquí vive el código Wordflow y el **secret** |
| **Cuenta B** | `abc1tienda-web` | Destino. Repos de software/memoria (ej. `Wordflow-1`) |
| **Alias de B** | `abc1`, `abc1tienda`, `cuenta_b`, `cuenta-b` | El código los normaliza a `abc1tienda-web` |

**Repo del cableo (este):**  
https://github.com/maxbry123-commits/agentes  

**NO es este repo:**  
https://github.com/maxbry123-commits/Agentes-motores-Wordflow-YAIWES  
(ese es el Router/centro de control; no tiene el cableo A→B)

---

## 1. Secret (una sola vez)

En **Cuenta A** → repo `agentes` → Settings → Secrets and variables → Actions:

| Secret | Valor |
|--------|--------|
| `EXTERNAL_GH_B_TOKEN` | PAT de **Cuenta B** con scope `repo` (crear repos + leer/escribir) |

Opcional alias de runtime: `GITHUB_B_TOKEN` (mismo valor o distinto).

**Nunca** pegues `ghp_...` en YAML, chat, ni payload. Solo referencias `env:NOMBRE`.

Comprobar secret: Actions → workflow `check-external-token-secret` → Run workflow.

---

## 2. Archivos del sistema (leer en este orden)

1. `GUIA_CUENTA_B_REMOTE.md` ← este archivo  
2. `PIPELINE/08_DESPLIEGUE_APPLY_PUSH.md`  
3. `extensions/github_deploy/remote_ops.py` ← **CRUD remoto completo**  
4. `extensions/github_deploy/apply_push.py` ← apply → commit → push  
5. `extensions/github_deploy/credential_env.py`  
6. `extensions/github_deploy/git_data_port.py`  
7. `extensions/wordflow/accounts/resolver.py`  
8. `extensions/wordflow/connectors/external_accounts.yaml`  
9. `extensions/wordflow_kernel/reception/git_apply.py`  
10. Workflows: `create-cuenta-b-repo.yml`, `check-external-token-secret.yml`, `validate-external-github.yml`

---

## 3. Capacidades

| Operación | Función Python | Trigger CI |
|-----------|----------------|------------|
| Identificar B (`abc1` → owner) | `identify_cuenta_b` / `remote_op("identify")` | — |
| Crear repo en B | `create_repo` | `create-cuenta-b-repo.yml` |
| Leer archivo | `get_file` / `remote_op("read")` | — |
| Leer head SHA | `get_head` | — |
| Listar árbol | `list_tree` | — |
| Listar repos del token B | `list_repos` | — |
| Escribir / editar archivos | `write_files` / `apply_and_push` | — |
| Borrar archivos | `delete_paths` | — |
| Verificar contenido | `verify_file` | — |
| Verificar head | `verify_head` | — |

Flags: `GITHUB_DEPLOY_REAL=1` = writes reales; sin flag = `DRY_RUN`.

---

## 4. Contrato del agente

### Payload apply_push

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

Owner también puede ser `abc1` (se normaliza).

### API Python unificada

```python
from extensions.github_deploy.remote_ops import remote_op, identify_cuenta_b

identify_cuenta_b("abc1")  # → abc1tienda-web

remote_op("create_repo", name="Wordflow-2", token_ref="env:EXTERNAL_GH_B_TOKEN", credentials=creds)
remote_op("read", owner="abc1", repo="Wordflow-1", path="README.md", token=token)
remote_op("tree", owner="abc1", repo="Wordflow-1", token=token)
remote_op("edit", owner="abc1", repo="Wordflow-1", files=[{"path": "pkg/a.py", "content": "x=1\n"}], token=token, dry_run=False)
remote_op("delete", owner="abc1", repo="Wordflow-1", paths=["pkg/old.py"], token=token)
remote_op("verify_file", owner="abc1", repo="Wordflow-1", path="pkg/a.py", token=token, expect_content="x=1\n")
```

---

## 5. Paso a paso

### Crear repo en B
Actions → `create-cuenta-b-repo.yml` → Run workflow  
Inputs: `owner=abc1tienda-web`, `repo_name=Wordflow-2`, `private=true`  
HTTP 201 = creado; 422 = ya existe.

### Validar acceso
Actions → `validate-external-github` → owner/repo/branch de B.

### Escribir + verificar

```python
from extensions.github_deploy.remote_ops import get_head, write_files, verify_file, verify_head
h = get_head(owner="abc1", repo="Wordflow-1", token=token)
old = h.detail["head_sha"]
w = write_files(owner="abc1", repo="Wordflow-1",
    files=[{"path": "docs/nota.md", "content": "# hola\n"}],
    token=token, expected_head=old, dry_run=False)
verify_head(owner="abc1", repo="Wordflow-1", token=token, expect_not_sha=old)
verify_file(owner="abc1", repo="Wordflow-1", path="docs/nota.md", token=token, expect_content="# hola\n")
```

### Borrar

```python
from extensions.github_deploy.remote_ops import delete_paths, verify_file
delete_paths(owner="abc1", repo="Wordflow-1", paths=["docs/nota.md"], token=token, dry_run=False)
verify_file(owner="abc1", repo="Wordflow-1", path="docs/nota.md", token=token, expect_missing=True)
```

### Listar árbol / repos

```python
from extensions.github_deploy.remote_ops import list_tree, list_repos
list_tree(owner="abc1", repo="Wordflow-1", token=token)
list_repos(token=token)
```

---

## 6. Espejo completo (read → edit → write → verify)

```
Cuenta A
  get_head(B) → sha0
  get_file(B, path) → contenido
  editar en memoria
  write_files(..., expected_head=sha0)
  get_head(B) → sha1 ≠ sha0
  verify_file(...)
```

Sin clonar B. Sin login en B.

---

## 7. Reglas fail-closed

| Situación | Resultado |
|-----------|-----------|
| PAT crudo (`ghp_`) | `RAW_TOKEN_FORBIDDEN` |
| Token env no set | `TOKEN_REF_UNRESOLVED` |
| Path protegido | `PROTECTED_PATH` / HOLD |
| force=true | `FORCE_PUSH_DENIED` |
| expected_head mismatch | `HEAD_CONFLICT` |
| Sin GITHUB_DEPLOY_REAL=1 | `DRY_RUN` |

`llm_control: DENY` siempre.

---

## 8. Tests

```bash
PYTHONPATH=. python -m pytest extensions/github_deploy/tests/test_apply_push.py -v
PYTHONPATH=. python -m pytest extensions/github_deploy/tests/test_remote_ops.py -v
```

Familias (≥10 cada una): identify, read, write/delete, create_repo, verify.  
Implementación: `extensions/github_deploy/tests/test_remote_ops.py`.

---

## 9. Qué NO hacer

- No buscar el cableo en `Agentes-motores-Wordflow-YAIWES`.
- No poner PAT en chat/repo.
- No force-push.
- No declarar PASS sin commit_sha + read-back.

---

## 10. Resumen

**Desde `maxbry123-commits/agentes`, con secret `EXTERNAL_GH_B_TOKEN`, usas `remote_ops` / `apply_and_push` para crear, leer, editar, borrar y verificar cualquier repo de `abc1tienda-web` sin iniciar sesión en Cuenta B.**

**Enlace:** https://github.com/maxbry123-commits/agentes/blob/main/GUIA_CUENTA_B_REMOTE.md
