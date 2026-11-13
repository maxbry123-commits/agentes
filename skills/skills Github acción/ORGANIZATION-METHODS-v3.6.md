# Research Download Chain — Organization Methods v3.6

Esta extensión forma parte del skill `research-download-chain` y define la selección determinista de método para MOVE/COPY/DELETE y la convivencia con GitHub Actions.

## Rol obligatorio de cada mecanismo

1. **GitHub Actions** — exclusivamente adquisición externa, descarga, extracción, entrega del payload adquirido y read-back asociado a esa adquisición. No usar Actions para organizar carpetas internas, índices, limpieza documental o simples movimientos ya presentes en el repositorio.
2. **Git Trees API** — método primario para MOVE/COPY/DELETE masivo dentro del mismo repositorio. Reutiliza blob/tree SHA para conservar bytes; una operación MOVE añade el destino con el mismo SHA y retira el origen en el mismo árbol.
3. **Contents API** — solo ediciones textuales pequeñas y seriales. No ejecutar create/update/delete del mismo conjunto de rutas en paralelo.
4. **Rama staging + Pull Request + merge** — método primario cuando `main` tiene escritores concurrentes o branch protection. La rama fija un snapshot; el PR permite que GitHub integre el cambio con el HEAD actual sin force-push.
5. **Update-ref CAS** — usar directamente únicamente cuando el HEAD leído sigue siendo el mismo justo antes de actualizar la referencia. Siempre `force:false`; si el HEAD cambió, reconstruir desde el nuevo árbol.
6. **Commit/merge Git nativo** — válido dentro de un runner de adquisición/extracción; antes de push usar `git fetch origin <branch> && git rebase --autostash origin/<branch>` y como máximo tres retries transitorios.
7. **workflow_dispatch/repository_dispatch** — solo orquestación de trabajos que realmente requieren runner de descarga/extracción. No usar dispatch para sustituir Git Trees en organización interna.
8. **PR de revisión** — obligatorio cuando las reglas de rama impiden una actualización directa o cuando una mutación masiva requiere aislamiento de conflictos.
9. **Copia por SHA** — cuando el origen ya existe en Git y se debe conservar, COPY por Git Trees con el mismo SHA; no volver a descargar ni reescribir.
10. **Movimiento por SHA** — cuando el origen ya existe y está autorizado retirarlo, MOVE atómico por Git Trees; nunca borrar primero y copiar después.

## Matriz de selección

| Necesidad | Método |
|---|---|
| Descargar código externo | GitHub Actions |
| Extraer ZIP/partes y entregar árbol | GitHub Actions |
| Mover muchos archivos ya existentes | Git Trees API |
| Copiar muchos archivos ya existentes | Git Trees API |
| Eliminar documentación autorizada en lote | Git Trees API |
| Editar un Markdown pequeño | Contents API serial |
| `main` cambia durante la preparación | Rama staging + PR merge |
| HEAD estable y commit fast-forward | Git Trees + update-ref `force:false` |
| Rama protegida | Rama + PR |
| Acción activa escribe un destino | Proteger destino; organizar lo demás y finalizarlo tras el cierre |

## Gates de seguridad

- Nunca borrar código o componentes. MOVE debe demostrar que el SHA del destino coincide con el SHA del origen antes de retirar el origen.
- Nunca mutar un destino de una Action activa. Identificar `queued|in_progress` y las rutas que escribe antes de crear el tree.
- Una colisión de ruta con SHA distinto es `COLLISION_BLOCKED`; no sobrescribir.
- Incertidumbre de clasificación es `GAP_REVIEW`; no borrar.
- Para documentación duplicada, eliminar solo con identidad de blob/hash demostrada y copia canónica preservada.
- `Componentes open source Yaiwes/` puede quedar reservado/vacío; un directorio vacío de Git se representa con el empty-tree si se requiere que exista como entrada.
- Read-back obligatorio del branch/tree/paths después de cada merge o actualización de ref.

## Concurrencia sin non-fast-forward

Si un Guardian/runner modifica `main` mientras se organiza:

`SNAPSHOT_MAIN → STAGING_BRANCH → TREE/COMMIT → PR → RECHECK_MERGEABLE → MERGE(expected_head_sha) → READ_BACK_MAIN`.

Esto evita force-push y conserva ambos historiales. Si el PR deja de ser mergeable, actualizar/recrear la rama contra el HEAD actual; nunca forzar `main`.

## LOOP de organización

`AUDIT → CLASSIFY → PROTECT_ACTIVE_DESTINATIONS → SELECT_METHOD → EXECUTE → READ_BACK → GAP_ANALYSIS → REPAIR → REPEAT`.

Cierre solamente con:

```yaml
gaps: 0
failures: 0
active_jobs: 0
collisions: 0
sha_preservation: PASS
workflow_scope: PASS
read_back: PASS
verdict: VERIFIED_CLOSED
```
