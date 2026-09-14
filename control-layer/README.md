# Control Layer (Wordflow) — capa universal 100%

Capa de control determinista · multiagente por **capability** · inmutable por tarea.  
Token/repo/backup viven en la **carpeta del proyecto** (`config/`), no en el core.

## Estado
**Cerrada** la capa universal (ver `WORDFLOW_100.md` + `docs/LISTA_TAREAS_WORDFLOW_CONTROL.md`).

Pendiente **fuera** de esta capa: HF · binario real · memoria avanzada.

## Árbol clave
```
control-layer/
├── loops/              # Engine · Supervisor · Adapter · factory
├── templates/uoos/     # D1–D10 plantillas
├── templates/pipeline/ # guía (no runtime)
├── templates/despliegue/
├── despliegue/         # organizador→…→verificar
├── schemas/            # D1 D2 D3 D4 D6 D8
├── skills/             # validate_schemas
├── bootstrap_project.py
└── WORDFLOW_100.md
```

## Uso mínimo
```python
from bootstrap_project import bootstrap
ctrl = bootstrap("/PROJECT")  # valida + carga nodes + engine + supervisor
```

## Conectar agente
1. `nodes/<id>.yaml` con `capabilities` + `adapter.id`
2. `build_adapter_from_project` / `bootstrap` registra solo
3. Loop pide **capability**, no conoce el agente

Branch: `workflow/A1-nucleo`
