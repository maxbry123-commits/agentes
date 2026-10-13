# AUDIT_INDEX — trazabilidad documentos del proyecto
# SOURCE: ESPECIFICACION_PIPELINE_NCT · índice maestro obligatorio

```yaml
schema_version: "1.0"
kind: AUDIT_INDEX
project_id: ""
generated_at: ""

entries:
  - path: ""                       # ruta exacta
    contenido: ""                  # 1 frase qué trae por dentro
    verificado: false              # SI solo si leído literal
    usado_en_fases: []             # ej: ["05.02", "08.01"]
    origen: bandeja                # bandeja | chat | repo | generado
```

## Uso Wordflow
- Generar/actualizar antes de escribir cualquier FASE.
- Afirmación en PIPELINE sin fila verificada = inválida.
- Apoya programación: el agente sabe qué archivos existen de verdad.
