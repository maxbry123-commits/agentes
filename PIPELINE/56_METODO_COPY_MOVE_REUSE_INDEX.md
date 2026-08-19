# Método — COPY / MOVE / REUSE / EXTRACT

Fuente: input del operador 2026-08-19. Los archivos 57–60 son el texto original. No reescritos.

Leer en este orden:

1. `PIPELINE/59_PATCH_GIT_01.md`
2. `PIPELINE/58_CROSS_REPOSITORY_TRANSFER.md`
3. `PIPELINE/57_MARKDOWN_TO_CODE_EXTRACTION.md`
4. `PIPELINE/60_REUSE_FIRST.md`

Reglas cortas:

- REUSE → COPY_FIRST → MOVE_FIRST → ADAPT_EXISTING → GENERATE_LAST
- Entre repos: COPY_FIRST. Origen intacto. No `git mv` A→B.
- MOVE semántico = COPY → VERIFY → AUTHORIZE DELETE → DELETE origen.
- Si el código está en un `.md`: EXTRACT_LITERAL. No reimplementar.
- El `.md` no se borra. Es provenance.
- SOURCE_HASH = DESTINATION_HASH o COPY_INTEGRITY FAIL.
- Secretos: no copiar.

Hashes de los protocolos (origen local de esta publicación):

- 57: ecd9e8b21ed3ade18a9e8f3b2bdca1cfabecec7de4dd14dec20488c892974a82
- 58: 77eab1ea666849ca1f9f01b23f9128e7626bfbbe2ed157bfac0f56f389c9419f
- 59: 628727306165a74106f6f7532a089574ef4220d2c33b5d7be60244e0f387b5d0
- 60: 6087f799cec98bbf9619c6f069f61d2c660e6ebb52921677af413e1d80ca3879
