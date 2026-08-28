# README SKILL wordflow-paso-control 1.2.0 — revision Director

Skill YAML-first. Ancla `references/RULES.yaml`. Actions en `assets/`.

## Arbol

```
wordflow-paso-control/
  SKILL.md
  assets/
    research-download-chain-final.yml
    batch-copy-root-files.yml
  references/
    RULES.yaml
    INPUT-BLOCK.md
    SOURCE-MAP.md
    PASO-DETALLE.md
    COUNCIL-12.md
    COUNCIL-12-AUDIT-1.2.md
    README-SKILL.md
    AUDIT-SKILL-CREATOR.md
  scripts/check-tarjeta.sh
```

## Que hace cada raiz

- Download code = zips + bandeja N + extract
- Desplegar = lote nuevo plan N + estado + deploy tail
- Refactoria = source/ intocable + new/ + cruzado x3

## Extract

`RULES.yaml extract_zip`. unzip -t / unzip -q / cp -a / sha256. Guia docs/ 404.

## DAG

No omitir. Edges en RULES.yaml.

## Cables

skills/ + Metodo de trabajo/ + Download code/ + Desplegar/ + Refactoria/ + Wordflow Code/Readme/Readme1/CABLE-PASO-CONTROL.md

## HOLD

owner C. Valor secret Maxbry_123_tokens (UI). Guia zip 404 en repo.

## Enlaces

- https://github.com/maxbry123-commits/agentes/blob/main/skills/wordflow-paso-control/SKILL.md
- https://github.com/maxbry123-commits/agentes/blob/main/skills/wordflow-paso-control/references/RULES.yaml
- https://github.com/maxbry123-commits/agentes/blob/main/skills/wordflow-paso-control/references/README-SKILL.md
- https://github.com/maxbry123-commits/agentes/blob/main/skills/wordflow-paso-control/assets/research-download-chain-final.yml
- https://github.com/maxbry123-commits/agentes/settings/secrets/actions
