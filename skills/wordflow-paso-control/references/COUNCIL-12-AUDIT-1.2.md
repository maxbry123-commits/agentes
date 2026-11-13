# Council 12 — audit skill 1.1 vs pedido Director

## 12 in

1. Meter GitHub Action Wordflow DENTRO del skill.
2. Explicar que hace Download code.
3. Explicar que hace Desplegar.
4. Explicar que hace Refactoria.
5. Meter sistema extract zip (guia 404).
6. DSL DAG schema.
7. YAML como regla anclada no texto libre.
8. Cablear copias Metodo/Download/Desplegar/Refactoria/Wordflow.
9. Readme de revision.
10. Decir si la guia puede omitir pasos.
11. Cerrar gaps reales.
12. Confirmar que falta vs HOLD externo.

## Hallazgo

- 1.1 era texto libre. Ambiguo. SI podia omitir pasos.
- Action no estaba en assets/.
- Roles de carpetas ausentes.
- docs/METODO_ZIP_COPY_DETERMINISTA.md 404.
- Sin DAG YAML.

## 12 out

1. assets/research-download-chain-final.yml blob lock.
2. assets/batch-copy-root-files.yml.
3. references/RULES.yaml ancla.
4. SKILL.md 1.2.0 YAML-first.
5. Roles Download/Desplegar/Refactoria.
6. Extract zip en RULES.
7. omit_steps false.
8. Copias cableadas.
9. references/README-SKILL.md.
10. Guia NO puede omitir nodos.
11. HOLD owner C + secret UI.
12. Guia zip repo 404 — ancla interna sustituye.

## Verdict

GO 1.2.0. NO pipeline PASS. HOLD C + Maxbry_123_tokens value.
