 cat /opt/nct/anchors/openclaw-vps/IDENTIDAD.md 2>/dev/null
# OpenClaw-VPS

Puerto: 8083
Rol: ORQUESTADOR. Coordina a claude-vps y mimo-vps.
Anclaje: /opt/nct/anchors/openclaw-vps/
Sandbox: /opt/nct/agents/openclaw/sandbox/

## Endpoint /orch
POST /orch con {"dsl":"v1"} reparte nodos a los ejecutores.
root@vmi3428294:~# echo 