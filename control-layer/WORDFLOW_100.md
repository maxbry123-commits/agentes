# Wordflow capa de control universal — 100%

Branch: `workflow/A1-nucleo`

## Alcance cerrado
Contratos · loops engine completo · plantillas D1–D10 · discovery nodes ·
adapter/router · runtime_factory (generic/stub sin exigir bin) ·
despliegue scripts · schema validators · bootstrap_project.

## Fuera de alcance (pendiente acordado)
- HF
- Binario temporal/openclaw real
- Memoria avanzada Wordflow
- PIPELINE 00–20 poblado por proyecto
- P1-CONVERTIDOR / OUSS Drive

## Entrada
```python
from bootstrap_project import bootstrap, run_once_demo
ctrl = bootstrap("/path/PROJECT")
# ctrl.validation · ctrl.engine · ctrl.supervisor
```

## Validar proyecto
```bash
python -m skills.validate_schemas /path/PROJECT
```

Estado: **CAPA UNIVERSAL CERRADA** — listo para más documentos.
