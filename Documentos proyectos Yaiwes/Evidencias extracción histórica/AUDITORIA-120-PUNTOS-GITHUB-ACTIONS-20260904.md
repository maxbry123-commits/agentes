# Auditoría forense de 120 puntos — GitHub Actions / Core kernel Yaiwes

Fecha: 2026-09-04
Repositorio: `maxbry123-commits/agentes`
Alcance: cierre de extracción en `Core kernel Yaiwes/Componentes recuperados A` y `Core kernel Yaiwes/Componentes recuperados B`, control de GAPS, Git LFS, publicación a `main`, runs antiguos y consistencia del skill.

## Hallazgo principal

Los GAPS repetitivos no provienen de 133 componentes que estén fallando una y otra vez. El sistema mezclaba tres clases diferentes de estado:

1. GAPS históricos de un baseline antiguo que seguían apareciendo en reportes aunque componentes posteriores ya hubieran sido reparados.
2. Reparaciones locales correctas que fallaban únicamente al publicar el commit.
3. Un run fantasma/estancado de control (`forensic-gates` #190, id `32214991157`) que permanece `queued` desde 2026-08-19 aunque su workflow ya no existe en `main`.

La causa técnica dominante de los últimos fallos es la publicación: varios shards escribían a la misma rama `main`, hacían `fetch + rebase + push`, y algunos commits terminaban referenciando punteros LFS desconocidos. Además, el reparador evacuaba punteros LFS reales a una carpeta de evidencia y esa carpeta se incluía en `git add`, por lo que la propia evidencia podía reintroducir un puntero LFS al commit. Repetir exactamente el mismo push ocho veces no podía resolver un rechazo GH008 determinista.

## 120 puntos auditados

### A. Ciclo de vida y antigüedad de Actions
1. PASS — se enumeraron runs `in_progress` actuales.
2. PASS — se enumeraron runs `queued` actuales.
3. PASS — se compararon `created_at`, `updated_at` y estado.
4. PASS — ningún job GitHub-hosted actual supera 6 h.
5. PASS — ningún workflow de cierre actual supera 24 h.
6. FINDING — existe run `32214991157` queued desde 2026-08-19 (>2 semanas).
7. FINDING — el workflow asociado `forensic-gates.yml` ya no existe en `main`.
8. FINDING — cancel normal del run antiguo devuelve HTTP 409.
9. FINDING — force-cancel del run antiguo también devuelve HTTP 409.
10. FINDING — DELETE del run antiguo con `GITHUB_TOKEN` devuelve HTTP 403; se clasifica `STALE_RUN_CONTROL_GAP`, no GAP de componentes.

### B. Triggers, dispatch y recursión
11. PASS — se revisaron triggers `push`, `workflow_dispatch` y `repository_dispatch`.
12. PASS — se confirmó que push hecho con `GITHUB_TOKEN` no dispara normalmente otro workflow de push.
13. FINDING — cadenas anteriores dependían demasiado de redispatch para continuar.
14. FINDING — Guardian/Watchdog/retry/LFS podían representar más de una autoridad de reparación.
15. PASS — se creó `canonical-quiesce` para apagar writers duplicados.
16. PASS — se evita reactivar workflows viejos para el mismo GAP.
17. PASS — `repository_dispatch` queda reservado para continuaciones explícitas.
18. PASS — el cierre nuevo no depende de que un commit automático vuelva a dispararse a sí mismo.
19. PASS — los triggers de organización ya no son parte de la extracción.
20. RECOMMENDATION — mantener una sola autoridad de dispatch por destino.

### C. Concurrencia y escritores
21. FINDING — cuatro shards podían publicar simultáneamente a la misma rama `main`.
22. FINDING — rutas disjuntas no eliminan la carrera de actualización del mismo ref Git.
23. EVIDENCE — shard 1 recibió `fetch first` porque otro commit avanzó `main`.
24. EVIDENCE — shard 3 tuvo el mismo patrón de carrera/publicación.
25. FINDING — `rebase` después de cada carrera hizo el flujo menos determinista.
26. PASS — shard 0 sí publicó correctamente.
27. PASS — shard 2 sí publicó correctamente.
28. REQUIRED — serializar publicación a `main` aunque la computación pueda ser paralela.
29. REQUIRED — `max-parallel: 1` o publisher único para los commits finales.
30. REQUIRED — si `HEAD` cambia, reconstruir desde `main` fresco; no rebasar ciegamente un payload de reparación.

### D. Checkout e historia Git
31. FINDING — `fetch-depth: 0` descargaba toda la historia, ramas y tags.
32. FINDING — el repositorio tiene un índice enorme; el checkout mostró ~1.18 millones de entradas.
33. PASS — sparse checkout reduce materialización del working tree.
34. FINDING — sparse checkout no elimina el costo de mantener un índice Git muy grande.
35. REQUIRED — usar shallow checkout (`fetch-depth: 1`) para reparaciones que no necesitan historia.
36. REQUIRED — mantener `filter: blob:none`.
37. REQUIRED — mantener `lfs: false`.
38. RECOMMENDATION — usar versión actual de `actions/checkout` en workflows nuevos.
39. FINDING — `checkout@v4` genera advertencia de Node 20 forzado a Node 24 en runners actuales.
40. PASS — no se necesitan tags ni historia completa para reconstruir componentes desde ZIP ya versionados.

### E. Git LFS: fuente, filtros, índice e historia
41. PASS — la política del proyecto prohíbe Git LFS.
42. PASS — los punteros se detectan por `version https://git-lfs.github.com/spec/v1`.
43. FINDING — GH008 significa que el push referencia OIDs LFS que GitHub no conoce.
44. FINDING — un working tree sin punteros no prueba que el índice esté limpio.
45. EVIDENCE — `.gitattributes` + `filter=lfs` puede transformar archivos durante `git add` mediante el clean filter.
46. PASS — el workflow neutralizaba `clean/smudge/process` localmente.
47. GAP — no existía inspección del contenido REAL de cada blob staged después de `git add`.
48. CRITICAL — `evacuate_pointer_files()` movía punteros LFS crudos a `Evidencias extracción histórica/LFS pointer evidence/...`.
49. CRITICAL — la carpeta completa de evidencias se añadía al commit, pudiendo reintroducir esos mismos punteros.
50. REQUIRED — conservar solo metadatos JSON del puntero (ruta, oid, tamaño, hash), nunca el pointer file crudo.

### F. GH008 e historia
51. EVIDENCE — shard 1 terminó extracción local con `failures=[]` y `REPAIR_PASS`.
52. EVIDENCE — shard 1 falló después en push con al menos 14 OIDs LFS desconocidos.
53. EVIDENCE — shard 3 terminó extracción local con `failures=[]` y `REPAIR_PASS`.
54. EVIDENCE — shard 3 falló después en push con al menos 6 OIDs LFS desconocidos.
55. FINDING — por tanto esos resultados no son `COMPONENT_GAP`; son `PUBLISH_GH008`.
56. FINDING — la comunidad git-lfs documenta GH008 causado por punteros existentes en historia aunque `git lfs ls-files` en HEAD no muestre archivos.
57. FINDING — `git lfs migrate export --everything` reescribe historia y exige force-push; está fuera de alcance porque la política prohíbe force y no es necesario para este cierre.
58. REQUIRED — no incorporar historia reescrita/rebased si basta crear un commit fresco sobre el HEAD remoto actual.
59. REQUIRED — si aparece GH008 idéntico, detener el retry del mismo commit inmediatamente.
60. REQUIRED — clasificar la causa antes de producir otro commit.

### G. Tamaños de blobs y datasets
61. PASS — GitHub bloquea blobs >100 MiB en Git normal.
62. FINDING — GitHub advierte por archivos grandes aunque sean menores del límite duro.
63. EVIDENCE — PRM800K produjo partes de 90 MiB y 75 MiB.
64. EVIDENCE — esas partes provocaron GH001 warnings, no el rechazo principal.
65. FIX — tamaño de parte normal-Git reducido de 90 MiB a 45 MiB.
66. PASS — 45 MiB queda por debajo de la recomendación operativa de 50 MiB observada por GitHub en los logs y muy por debajo de 100 MiB.
67. PASS — el manifiesto conserva SHA256 del archivo fuente completo.
68. PASS — el manifiesto conserva SHA256 de cada parte.
69. PASS — la reconstrucción valida concatenación, bytes y SHA.
70. PASS — Math-Shepherd y PRM800K pueden representarse en Git normal sin LFS mediante partes verificadas.

### H. ZIP, integridad y extracción
71. PASS — cada ZIP ejecuta prueba CRC.
72. PASS — se bloquean rutas absolutas.
73. PASS — se bloquea `..`/Zip Slip.
74. PASS — se bloquean symlinks/dispositivos especiales mediante validación de modo.
75. PASS — se detectan rutas duplicadas dentro del ZIP.
76. PASS — se detectan colisiones cruzadas entre partes ZIP.
77. PASS — extracción ocurre en staging temporal.
78. PASS — se calcula hash determinista del árbol final.
79. PASS — se valida conteo de archivos/bytes.
80. PASS — ZIP fuente se conserva como evidencia; no se confunde ZIP válido con componente instalado.

### I. Destinos y colisiones
81. PASS — destino real A es `Core kernel Yaiwes/Componentes recuperados A`.
82. PASS — destino real B es `Core kernel Yaiwes/Componentes recuperados B`.
83. FINDING — reportes históricos conservan alias antiguos `Agente core kernel Yaiwes principal` y `core kernel Yaiwes principal`.
84. FINDING — esos alias históricos hacían parecer que había dos Core adicionales.
85. PASS — el script nuevo traduce alias históricos a A/B sin recrear raíces antiguas.
86. PASS — una colisión conserva backup antes de reemplazar con fuente comprobada.
87. PASS — se registran hashes de árboles resultantes.
88. PASS — no se elimina código/componente como deduplicación ciega.
89. REQUIRED — auditor final debe inspeccionar A/B reales, no los alias históricos.
90. REQUIRED — no contar un alias histórico como GAP de estructura.

### J. Evidencia, baseline y Watchdog
91. FINDING — baseline `repair-33836197018.json` contiene 133 gaps históricos.
92. FINDING — seguir mostrando `baseline_remaining=133` no significa que sigan faltando 133 componentes hoy.
93. PASS — `done_keys()` descuenta evidencia canonical posterior.
94. RISK — `done_keys()` confía demasiado en reportes `canonical-*.json` sin recomputar siempre el árbol completo.
95. REQUIRED — verificación final debe hacer read-back fresco de los árboles A/B.
96. REQUIRED — `missing_evidence` y `missing_target_trees` deben ser cero.
97. REQUIRED — `active_jobs` debe ser cero al certificar.
98. REQUIRED — fallos de publicación deben separarse de fallos de contenido.
99. REQUIRED — stale run de control debe reportarse aparte de `remaining_component_gaps`.
100. REQUIRED — no emitir `VERIFIED_CLOSED` por un JSON viejo ni por el resultado local de un runner.

### K. REST API, refs y retries
101. PASS — Git refs con `force=false` garantizan no sobrescribir trabajo remoto.
102. PASS — Git Trees API sigue siendo el método primario para organización interna masiva.
103. PASS — mutaciones Contents API deben ser seriales.
104. FINDING — GitHub recomienda evitar requests concurrentes para no golpear secondary rate limits.
105. FINDING — GitHub recomienda shallow clones para reducir costo de lecturas Git en repos grandes.
106. FINDING — push rate recomendado es bajo; cuatro publishers + retries elevaban innecesariamente la tasa.
107. CRITICAL — ocho retries del mismo GH008 eran deterministas y solo generaban carga.
108. REQUIRED — retry solo para timeout, red o non-fast-forward antes de construir el commit.
109. REQUIRED — GH008, collision, pointer y >100 MiB son fail-fast hasta corregir causa.
110. REQUIRED — cada nuevo intento debe partir de estado remoto fresco y producir evidencia nueva.

### L. Consistencia del skill/procedimiento
111. FINDING — skill v3.6 permitía shards disjuntos paralelos con rebase a la misma rama; la práctica mostró que esa regla era demasiado permisiva.
112. REQUIRED — cambiar a `parallel compute, serial publish` para una misma rama.
113. REQUIRED — prohibir rebase como mecanismo de retry de un commit de payload NO-LFS ya construido.
114. REQUIRED — añadir gate de blobs staged después de `git add`.
115. REQUIRED — prohibir guardar raw pointer files como evidencia versionada.
116. REQUIRED — bajar partes normales a <50 MiB cuando sea práctico.
117. REQUIRED — preferir checkout shallow; historia completa solo si una prueba la requiere.
118. REQUIRED — incluir barrido de runs >24 h y clasificación especial para runs fantasma del control plane.
119. REQUIRED — separar `CONTENT_PASS` de `PUBLISH_PASS` y `READ_BACK_PASS`.
120. CLOSURE GATE — solo `CONTENT_PASS + PUBLISH_PASS + READ_BACK_PASS + active_jobs=0 + remaining_component_gaps=0` permite `VERIFIED_CLOSED`.

## Fuentes oficiales consultadas

- https://docs.github.com/en/actions/reference/limits
- https://docs.github.com/en/repositories/creating-and-managing-repositories/repository-limits
- https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/control-workflow-concurrency
- https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/trigger-a-workflow
- https://docs.github.com/en/rest/actions/workflow-runs
- https://docs.github.com/en/rest/using-the-rest-api/best-practices-for-using-the-rest-api
- https://docs.github.com/en/rest/git/refs
- https://docs.github.com/en/rest/git/trees
- https://docs.github.com/en/repositories/working-with-files/managing-large-files/about-git-large-file-storage
- https://docs.github.com/en/repositories/working-with-files/managing-large-files/about-large-files-on-github
- https://github.com/actions/checkout

## Comunidad técnica consultada

- https://github.com/git-lfs/git-lfs/issues/4148
- https://github.com/git-lfs/git-lfs/issues/4190
- https://github.com/git-lfs/git-lfs/issues/4821
- https://github.com/git-lfs/git-lfs/issues/3708
- https://github.com/git-lfs/git-lfs/discussions/6026
- https://github.com/actions/checkout/issues/663
- https://github.com/actions/checkout/issues/800
- https://github.com/actions/checkout/issues/1550
- https://github.com/actions/checkout/issues/2249
- https://github.com/actions/checkout/issues/2441
- https://github.com/actions/checkout/issues/2556
- https://stackoverflow.com/questions/52612880/lfs-upload-missing-object-but-the-file-is-there
- https://stackoverflow.com/questions/70785041/how-to-skip-lfs-pre-receive-hook-or-drop-the-lfs-object-all-together

## Solución consolidada

1. Apagar writers viejos/duplicados.
2. No tratar el run fantasma de 2026-08-19 como GAP de componentes.
3. Reducir dataset chunks a 45 MiB.
4. Serializar cualquier publisher de `main`.
5. Usar checkout shallow.
6. No hacer rebase de commits de reparación; reconstruir desde HEAD fresco si cambia la rama.
7. Nunca versionar pointer files LFS crudos, ni siquiera como evidencia; conservar únicamente sus metadatos.
8. Verificar el índice staged y bloquear cualquier pointer antes de commit.
9. Publicar una sola vez por estado; GH008 no se reintenta sin modificar la causa.
10. Ejecutar auditor fresh read-back sobre A/B y cerrar únicamente con cero gaps reales.
