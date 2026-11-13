# Método de trabajo

Cualquier instancia debe leer y seguir:

1. [PIPELINE/00_METODO_TRABAJO_Y_ARQUITECTURA.md](PIPELINE/00_METODO_TRABAJO_Y_ARQUITECTURA.md) — si existe en este repo
2. [PIPELINE/56_METODO_COPY_MOVE_REUSE_INDEX.md](PIPELINE/56_METODO_COPY_MOVE_REUSE_INDEX.md)
3. [PIPELINE/59_PATCH_GIT_01.md](PIPELINE/59_PATCH_GIT_01.md)
4. [PIPELINE/58_CROSS_REPOSITORY_TRANSFER.md](PIPELINE/58_CROSS_REPOSITORY_TRANSFER.md)
5. [PIPELINE/57_MARKDOWN_TO_CODE_EXTRACTION.md](PIPELINE/57_MARKDOWN_TO_CODE_EXTRACTION.md)
6. [PIPELINE/60_REUSE_FIRST.md](PIPELINE/60_REUSE_FIRST.md)

COPY-FIRST. Origen intacto. EXTRACT_LITERAL desde Markdown. LLM ≠ PASS. GitHub = verdad.

## Procedimiento ZIP → nueva raíz

1. Auditar destino y localizar el ZIP por nombre, ruta, SHA y tamaño.
2. Descargar el ZIP como binario; no interpretarlo como UTF-8.
3. Extraer todos los archivos y directorios a un área temporal.
4. Auditar el contenido extraído y detectar una posible carpeta envolvente.
5. Crear una sola raíz nueva con el nombre solicitado.
6. Colocar TODO el contenido extraído dentro de esa raíz, quitando solo la carpeta envolvente si existe.
7. No cambiar nombres, rutas internas ni contenido.
8. Comparar inventario ZIP ↔ raíz: archivos, directorios, tamaños y SHA/contenido cuando sea posible.
9. Crear tree/commit conservando el resto del repositorio y actualizar la rama destino.
10. Verificar directamente en GitHub que la nueva raíz contiene todo lo esperado.

## Reglas ZIP

- ZIP original intacto salvo instrucción expresa.
- No clasificar, mover, borrar ni reescribir otros documentos durante esta tarea.
- GitHub es la fuente de verdad.
- TERMINADA solo después de la verificación cruzada.

Flujo: `localizar ZIP → descargar binario → extraer → inventariar → crear raíz → desplegar → comparar → commit → push → verificar`.