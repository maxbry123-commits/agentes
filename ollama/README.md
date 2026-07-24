# gemma4-vps-api.py

Wrapper OpenAI-compatible para Ollama.

- Archivo: `gemma4-vps-api.py`
- Puerto: `8002`
- Comando para correrlo: `python3 gemma4-vps-api.py`
- Qué hace: expone el modelo local de Ollama `gemma3:1b` bajo el nombre
  público `gemma-4-vps`, vía endpoints OpenAI-compatible
  `/v1/chat/completions` y `/v1/models` (más `/health`). Internamente
  llama a `http://127.0.0.1:11434/api/generate` (Ollama) y traduce la
  respuesta al formato `chat.completion` de OpenAI.
- `test_gemma.sh` en esta misma carpeta prueba el modelo vía LiteLLM
  (`:4500/v1/chat/completions`, modelo `gemma-4-vps`), no llama a este
  wrapper directamente.
