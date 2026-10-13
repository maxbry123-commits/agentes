# Integración UOOS en el Wordflow
# SOURCE: schema project_docs · templates/uoos · install · despliegue · leyes · RT · G30 · L11

## Flujo nativo (no modifica el núcleo por tarea)

1. **Detectar proyecto**  
   Leer carpeta del trabajo en turno con `schemas/project_docs.yaml`.

2. **Validar B1–B8 + config/**  
   Si falta required → REJECT.

3. **Entregar receta al agente**  
   `templates/uoos/RECETA_AGENTE.md` + plantillas B1–B8.

4. **Ejecutar**  
   DAG (B4) + loops (B5) + RT states + G30 + Tribunal (B6) + leyes L01–L15.

5. **Install (si hay source)**  
   `install/source_resolver` + `policy.yaml` (no-from-scratch).

6. **Despliegue (si aplica)**  
   Leer `config/token_ref` · `repo_destino` · `backup_destino` del **proyecto**.  
   `despliegue/organizador` → verificar → `evidence.json`.

7. **Cierre**  
   L11 evidencia · RT-90 · sin secretos en árbol.

## Inmutable
La Capa de Control no se edita por tarea.  
Token, repo y backup viven solo en la carpeta del proyecto.
