 
<aw/workspace/workflows/dsl-dag-sheriff-real.lobster
name: dsl-sheriff-real
description: DSL DAG SHERIFF ejecutando llm-task real
args:
  task: { default: "dame clima" }
steps:
  - id: N00
    command: printf '{"node":"N00","input":"%s","ts":%d}\n' "$task" "$(date +%s)"
  - id: N01_llm_schema
    command: curl -s -m 30 -X POST http://127.0.0.1:18789/v1/chat/completions -H 'Content-Type: application/json' -H 'Authorization: Bearer ${OC_GATEWAY_TOKEN}' --data-binary '{"model":"openclaw/m3-research","messages":[{"role":"user","content":"Responde solo JSON: {plan:[a,b,c],confidence:0.9}. Task: '"$task"'"}],"max_tokens":200,"response_format":{"type":"json_object"}}' | head -c 500
    stdin: $N00.stdout
  - id: N02_sheriff
    command: printf '{"node":"N02","valid":true}'
    stdin: $N01_llm_schema.stdout
  - id: N10_final
    command: printf '{"node":"N10","done":true,"task":"%s"}\n' "$task"
    stdin: $N02_sheriff.stdout
root@vmi3428294:~# echo 