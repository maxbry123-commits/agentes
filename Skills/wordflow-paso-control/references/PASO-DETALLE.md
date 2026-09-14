# PASO DETALLE — Actions + Registry

## PASO 4 workflow contrato

```
on: workflow_dispatch
permissions:
  contents: read
jobs:
  copy:
    steps:
      - uses: actions/checkout@v4
        with:
          path: source
          fetch-depth: 1
      - uses: actions/checkout@v4
        with:
          repository: OWNER/TARGET_REPO
          token: ${{ secrets.TARGET_REPO_TOKEN }}
          path: target
          fetch-depth: 1
      - run: |
          set -euo pipefail
          QUEUE=(file1 file2)
          for FILE in "${QUEUE[@]}"; do
            test -f "source/$FILE"
            cp "source/$FILE" "target/$MAPPED"
          done
          cd target
          git add .
          git diff --cached --quiet || git commit -m "Batch copy files from source repository"
          git push
```

Cola all-root alternativa

```
find source -maxdepth 1 -type f -printf '%f\n' | sort > queue/files.txt
```

Map destino organizado

```
raiz     README pyproject
src/     app code
config/  config
scripts/ tools
tests/   tests
```

## PASO 8 registry

```
SKILL
  -> Repository Router
     -> Repo Registry
        SOURCE_01  maxbry123-commits/agentes                         read
        SOURCE_02  maxbry123-commits/TAREA-1                         read
        SOURCE_03  maxbry123-commits/Agentes-motores-Wordflow-YAIWES read
        WORK_01    maxbry123-commits/agentes Wordflow Code           process
        DEST_A     maxbry123-commits/<repo>                          write  Maxbry_123_tokens
        DEST_B     abc1tienda-web/<repo>                             write  EXTERNAL_GH_B_TOKEN
        DEST_C     HOLD/<repo>                                       write  EXTERNAL_GH_C_TOKEN
     -> GitHub API / Git
        token env only
     -> leer -> procesar -> validar -> escribir
```

CABLE A Wordflow Code arquitectura (no editar runner).
CABLE B apply_push deploy.
