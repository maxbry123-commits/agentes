# EXTRACT + X-RAY

Workflows:
- assets/extract-downloaded-zips.yml
- assets/download-extract-xray.yml
- .github/workflows/extract-downloaded-zips.yml
- .github/workflows/download-extract-xray.yml

Dest:
Download code/archivos/{slug}_NNNN.zip -> Download code/archivos/{slug}/

Prohibido auditar cada parte.
Cadena S1-S12. Compare source_commit del MANIFEST no main.
unzip extrae. Python hashea.
Download usa packer lock.
