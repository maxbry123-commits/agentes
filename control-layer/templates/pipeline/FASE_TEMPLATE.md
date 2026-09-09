# FASE_TEMPLATE — guía de programación (NO runtime)
# SOURCE: ESPECIFICACION_PIPELINE_NCT_v2 · GUIA_MAESTRA_PIPELINE_NCT_v2
# Wordflow usa esto para generar/auditar docs de plan/pipeline/*.md
# No se ejecuta en LoopEngine.

```yaml
schema_version: "1.0"
kind: PIPELINE_FASE
# ID real del roadmap 00-20 (nunca inventar)
fase_id: "05.02"
nombre: ""
roadmap_fase: 5                    # 0..20
estado: pendiente                  # completo | en_progreso | pendiente
porcentaje: 0                      # 0-100

raiz_estructural:
  fuentes: []                      # rutas exactas verificadas
  verificado: false                # true solo si se LEYÓ el archivo
  conecta_anterior: ""             # ej: 05.01
  conecta_siguiente: ""            # ej: 05.03

proceso:
  debe: []                         # acciones obligatorias
  no_debe: []                      # prohibiciones explícitas

diagrama_horizontal: ""            # a → b → c

# Sello 10 roles (on|pend|off) — metadato de gobierno, no runtime
sello_gobierno:
  DSL: on
  DAG: on
  Schema: on
  Sheriff: on
  Sentinela: pend
  Juez: pend
  Supervisor: pend
  Validador: on
  Verificador: on
  Orquestador: on

explicacion:
  tecnica: ""                      # ingeniero/IA
  simple: ""                       # mismo contenido, sin jerga

fuentes_indice: []                 # filas del AUDIT_INDEX

mapeo_uoos:
  b1_manifest: false
  b2_state: false
  b3_nodos: false
  b4_dag: false
```

## Reglas Wordflow (diseño de plantilla)
1. Solo entra lo auditado (ruta en AUDIT_INDEX con verificado:true).
2. 3–100 tareas por fase en docs hijos; este template es la cabecera.
3. DEBE/NO DEBE sin ambigüedad.
4. Cadena anterior↔siguiente obligatoria.
5. Técnica y simple describen el MISMO comportamiento.
6. Dividir PIPELINE en muchos docs pequeños (`PIPELINE_00.md`, …).
7. Nunca runtime: no llama LoopEngine ni AgentAdapter.
