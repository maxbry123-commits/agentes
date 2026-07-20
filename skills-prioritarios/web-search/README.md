# web-search

## Qué hace
Búsqueda web con fallback de proveedores:
1. **Primary**: Serper API (si `SERPER_API_KEY` está).
2. **Fallback 1**: DuckDuckGo HTML scraping.
3. **Fallback 2**: Bing HTML scraping.

Devuelve top-10 resultados con `title`, `url`, `snippet`.

## Cuándo se usa
- En el nodo `DISCOVERY` del pipeline DSL DAG SHERIFF.
- Cuando una skill necesita contexto actualizado (no está en knowledge registry).

## Schema
```yaml
id: web-search
version: 0.1.0
entry: ./run.py
required_tools: [http, parse]
tags: [research, search]
source: core
```

## Uso
```bash
openclaw skill run web-search --input '{"q":"daytona io api documentation","n":5}'
```

## Estado
- Spec completa, scripts en este dir.
- Pendiente: implementar fallback de DuckDuckGo (hoy solo stub de Serper).
