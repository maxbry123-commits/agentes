# reasoning/ — Zona LLM aislada
# SOURCE: SALIDA_6 §17 · APORTES_1_CAPA_CONTROL

Comunicación SOLO por archivos JSON:
- determinista escribe `reasoning_request.json`
- reasoning emite `reasoning_verdict.json`

REGLAS:
- determinista/ NUNCA hace import de reasoning/
- reasoning/ NUNCA ejecuta comandos ni escribe fuera de esta carpeta
- Si se borra reasoning/ entero → el sistema sigue en modo estricto
  (todo gate con IA se resuelve como REJECT por defecto)
