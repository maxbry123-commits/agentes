# README SKILL wordflow-paso-control 1.3.0

Ancla `references/RULES.yaml`. Extract al lado del zip. Reconstruct por slug. X-Ray vs source_commit.

## Extract

```
Download code/archivos/{slug}_0001.zip
Download code/archivos/{slug}_0002.zip
        -> Download code/archivos/{slug}/
```

No auditar fragmentos. Cadena S1-S12. Un job `download-extract-xray.yml`.
Download sigue el packer lock. unzip extrae. Python hashea.

## Workflows

- .github/workflows/extract-downloaded-zips.yml
- .github/workflows/download-extract-xray.yml
- skills/wordflow-paso-control/assets/* mismos YAML

## HOLD

owner C. Secret Maxbry_123_tokens valor UI.
Archivos >8MiB el packer los parte en .chunks; X-Ray vs blob original puede FAIL en esos paths (esperado del lock, no reescribir packer).
