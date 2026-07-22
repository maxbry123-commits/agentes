#!/bin/bash
curl -s -m 50 -X POST http://127.0.0.1:4500/v1/chat/completions \
  -H "Authorization: Bearer sk-litellm-maxbry-2026" \
  -H "Content-Type: application/json" \
  -d '{"model":"gemma-4-vps","messages":[{"role":"user","content":"di ok"}],"max_tokens":20}'
