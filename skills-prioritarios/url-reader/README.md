# url-reader

## Qué hace
Lee una URL y devuelve el contenido en **markdown limpio** (sin ads, sin nav, sin scripts).
Usa `trafilatura` para extraer el texto principal y lo convierte a markdown.

## Cuándo se usa
- Después de `web-search`: para abrir el top-N resultados y resumirlos.
- En `READ` de knowledge registry: ingesta de docs externas.
- Cuando un agente necesita "leer" una página para responder.

## Schema
```yaml
id: url-reader
version: 0.1.0
entry: ./run.py
required_tools: [http, parse]
tags: [research, reader, parse]
source: core
```

## Uso
```bash
openclaw skill run url-reader --input '{"url":"https://github.com/openclaw/openclaw","max_chars":20000}'
```

## Estado
- Spec completa, scripts en este dir.
- Pendiente: implementar extracción con `trafilatura` (hoy stub que devuelve raw HTML cap a N chars).
