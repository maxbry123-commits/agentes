# METODO_ZIP_COPY_DETERMINISTA

Ancla skill wordflow-paso-v3.

## Sacar
1. Group by *_0001.zip
2. dest = Download code/archivos/{slug}/
3. unzip -tq cada parte
4. unzip -oq -d dest todas las partes ordenadas
5. flatten packer prefix {slug}/
6. Prohibido dest {slug}_0001/

## Copiar
cp -a src dest
no rewrite origen
sha256 src == sha256 dst

## X-Ray
source_commit del MANIFEST.jsonl no main
reensamblar .chunks via SPLIT_FILES.json antes de SHA
0 MISSING 0 EXTRA 0 CHANGED
