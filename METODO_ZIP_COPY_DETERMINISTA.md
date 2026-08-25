# METODO_ZIP_COPY_DETERMINISTA

**Método de trabajo obligatorio** para Grok / GPT / cualquier AI al copiar desde ZIP a repos GitHub **sin reescribir** el contenido, con verificación cruzada y raíz organizada.

**Repos canónica:** `maxbry123-commits/agentes`  
**Aplicable a:** frontend · agentes · Orquestador-Maxbry · osquestador-auditor · router-universal-router-inteligente · Maxbry · motor agente · YAIWES (Agentes-motores-Wordflow-YAIWES)

Relacionado:
- [GUIA_CUENTAS_REMOTE.md](./GUIA_CUENTAS_REMOTE.md) — cableado A/B/C
- [GUIA_CUENTA_B_REMOTE.md](./GUIA_CUENTA_B_REMOTE.md) — espejo remoto B
- [GUIA-DESPLIEGUE-ZIP-UNIVERSAL.md](./GUIA-DESPLIEGUE-ZIP-UNIVERSAL.md) — despliegue ZIP universal (si existe)

---

## 0. Principio fijo (fail-closed)

```text
ZIP bytes  →  extract (sin modificar)  →  blob/content exacto  →  commit  →  verify SHA/content
```

- **Nunca** regenerar, formatear ni “mejorar” el texto.
- Si el hash del archivo en destino ≠ hash del ZIP → **FAIL** (no marcar PASS).
- Token solo por ref (`env:` / `secret://`). Nunca PAT en claro.
- Sin force-push. Usar `expected_head` cuando exista.

---

## 1. Diez maneras de copiar sin reescribir el archivo

| # | Método | Cuándo usarlo | Comando / código clave |
|---|--------|---------------|------------------------|
| 1 | Local unzip + git | Máquina con git y acceso | `unzip src.zip -d tmp/` → `cp` → `git add` → `commit` → `push` |
| 2 | GitHub Actions (unzip + commit) | ZIP en el repo o artifact | Workflow: `unzip` + `git add .` + `git commit` + `git push` |
| 3 | Contents API (PUT) | 1 archivo ≤ 1 MB | `PUT /repos/{o}/{r}/contents/{path}` con `content` = base64 de los bytes del ZIP |
| 4 | **Git Data API (blob → tree → commit → ref)** | Varios archivos / cualquier tamaño | `POST /git/blobs` → `POST /git/trees` → `POST /git/commits` → `PATCH /git/refs/heads/main` |
| 5 | zip-deployer / equivalente | Despliegue completo de ZIP | Lee ZIP → filtra `__MACOSX` → blobs en batch → tree → commit |
| 6 | PyGithub / ghapi / Octokit | Script Python/JS | `repo.create_git_blob(content, "base64")` + tree + commit |
| 7 | gh CLI | Terminal autenticada | `gh api .../git/blobs -f content=... -f encoding=base64` |
| 8 | curl + base64 | Entorno mínimo | Extraer bytes → `base64 -w0` → PUT Contents o blob |
| 9 | Clone vacío + unzip + push | Repo destino vacío o limpio | `git clone` → `unzip -o` → `git add -A` → `push` |
| 10 | Marketplace Action “Unzip and update” | Solo CI | Action que hace unzip + commit automático |

**Recomendado para AI (Wordflow / remote_ops):** Método **4** (Git Data API) o `write_files` / `remote_op("write")`.

---

## 2. Flujo determinista (schema)

```text
INPUT:
  zip_path          : string
  dest_owner        : string
  dest_repo         : string
  dest_branch       : "main"
  dest_base_path    : string | ""     # ej. "apps/frontend/"
  token_ref         : "secret://EXTERNAL_GH_B_TOKEN" | similar
  expected_head     : string | null
  dry_run           : bool = true

STEPS (orden fijo):
  1. EXTRACT
     - Abrir ZIP
     - Filtrar: __MACOSX/, .DS_Store, Thumbs.db
     - Por entrada: path_relativo + bytes exactos + sha256(bytes)

  2. MANIFEST
     - Lista: [{path, size, sha256, content_b64}]
     - Guardar manifest.json (evidence append-only)

  3. RESOLVE TOKEN
     - resolve_token(token_ref) → token o FAIL (TOKEN_REF_UNRESOLVED)

  4. GET HEAD
     - GET /repos/{o}/{r}/git/ref/heads/{branch} → head_sha

  5. WRITE
     - ≤1 archivo y ≤1 MB  → Contents API (opcional)
     - resto               → Git Data API:
         a. POST blobs
         b. POST tree (base_tree = tree del head)
         c. POST commit (parents=[head_sha])
         d. PATCH ref (sin force)

  6. VERIFY (obligatorio)
     - get_file / verify_file por cada path del manifest
     - sha256 destino == sha256 ZIP
     - Si mismatch → FAIL

  7. EVIDENCE
     - evidence.json: {zip_sha256, commit_sha, files_ok, files_fail, timestamp}
```

---

## 3. Código / comandos

### A. Extract + manifest (Python)

```python
import zipfile, hashlib, json, base64
from pathlib import PurePosixPath

def extract_manifest(zip_path: str) -> list[dict]:
    out = []
    with zipfile.ZipFile(zip_path, "r") as z:
        for info in z.infolist():
            if info.is_dir():
                continue
            name = PurePosixPath(info.filename).as_posix()
            if name.startswith("__MACOSX/") or name.endswith((".DS_Store", "Thumbs.db")):
                continue
            data = z.read(info)
            out.append({
                "path": name,
                "size": len(data),
                "sha256": hashlib.sha256(data).hexdigest(),
                "content_b64": base64.b64encode(data).decode("ascii"),
            })
    return out
```

### B. Git Data API (lógica)

```bash
# Blob
curl -s -X POST -H "Authorization: Bearer $TOKEN" \
  -H "Accept: application/vnd.github+json" \
  https://api.github.com/repos/OWNER/REPO/git/blobs \
  -d "{\"content\":\"$CONTENT_B64\",\"encoding\":\"base64\"}"

# Tree → Commit → PATCH ref/heads/main (sin force)
```

### C. Wordflow / remote_ops

```python
files = [{"path": f"{dest_base_path}{m['path']}", "content": base64.b64decode(m["content_b64"])}
         for m in manifest]

remote_op("write",
          owner=dest_owner, repo=dest_repo, branch="main",
          files=files, token=token, expected_head=expected_head, dry_run=False)

for m in manifest:
    remote_op("verify_file", owner=..., repo=..., path=...,
              token=token, expect_content=base64.b64decode(m["content_b64"]))
```

### D. Verificación cruzada ZIP ↔ repo

```python
def cross_verify(zip_manifest, owner, repo, token, base_path=""):
    fails = []
    for m in zip_manifest:
        dest_path = f"{base_path}{m['path']}".lstrip("/")
        r = remote_op("get_file", owner=owner, repo=repo, path=dest_path, token=token)
        if r.get("status") != "ok":
            fails.append({"path": dest_path, "error": "missing"})
            continue
        raw = r["content"] if isinstance(r["content"], bytes) else r["content"].encode()
        got_sha = hashlib.sha256(raw).hexdigest()
        if got_sha != m["sha256"]:
            fails.append({"path": dest_path, "error": "sha256_mismatch",
                          "expected": m["sha256"], "got": got_sha})
    return {"ok": len(fails) == 0, "fails": fails}
```

Local rápido:

```bash
python -c "
import zipfile, hashlib
z=zipfile.ZipFile('src.zip')
for i in z.infolist():
  if not i.is_dir():
    print(hashlib.sha256(z.read(i)).hexdigest(), i.filename)
"
```

---

## 4. Cablear y editar sin romper bloques de código

1. Trabajar siempre con **bytes** del ZIP (no texto re-codificado).
2. Editar archivo existente: `get_file` → sha + content → modificar mínimo → write con sha/base_tree.
3. Nunca pretty-print, fix whitespace ni regenerar con LLM el archivo completo.
4. Tras cualquier write → `verify_file` con content/sha esperado.
5. Paths protegidos (`.github/workflows`, secrets, etc.) → **HOLD**.

---

## 5. Organización de la raíz de `main` (varios software en paralelo)

```text
/
├── apps/                    # software desplegables
│   ├── frontend/
│   ├── backend/
│   └── worker/
├── packages/                # librerías compartidas
│   ├── ui/
│   ├── utils/
│   └── config/
├── tools/
├── docs/
├── .github/workflows/
├── CODEOWNERS
├── README.md
└── (opcional) turbo.json / nx.json / pnpm-workspace.yaml
```

Reglas:
- Cada app/package independiente → ZIP completo puede ir a `apps/xxx/` o `packages/yyy/`.
- `CODEOWNERS` por carpeta.
- Parallel = PRs que tocan solo su subárbol.
- Proyectos totalmente independientes → repos separados + cableado A/B/C.

---

## 6. Checklist de validación (antes de PASS)

```text
[ ] Manifest generado desde el ZIP (path + sha256)
[ ] Token resuelto por ref (no raw PAT)
[ ] expected_head usado o documentado
[ ] Commit sin force
[ ] Todos los paths del manifest existen en destino
[ ] sha256(content_destino) == sha256(content_zip) por archivo
[ ] evidence.json con commit_sha + OK/FAIL
[ ] Paths protegidos no tocados
[ ] dry_run=false solo tras dry_run=true exitoso
```

Si **cualquier** ítem falla → reportar GAP y no continuar.

---

## 7. Resumen de una línea

**Extrae bytes del ZIP → crea blobs → un solo commit con tree → actualiza ref → verifica sha256 de cada archivo contra el manifest del ZIP. Si no coincide, FAIL.**

---

## 8. Repos donde aplica este método

| Repo | Owner |
|------|--------|
| agentes | maxbry123-commits |
| frontend | maxbry123-commits |
| Orquestador-Maxbry- | maxbry123-commits |
| osquestador-auditor | maxbry123-commits |
| router-universal-router-inteligente- | maxbry123-commits |
| Maxbry-AGI | maxbry123-commits |
| Agentes-motores-Wordflow-YAIWES | maxbry123-commits |

Copia canónica de este archivo en cada repo raíz como `METODO_ZIP_COPY_DETERMINISTA.md` (o enlace a agentes).
