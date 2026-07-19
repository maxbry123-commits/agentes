#!/bin/bash
set +e
cd /opt/nct/repos
python3 - <<'PYEOF'
import os, json, subprocess, datetime
repos = ["agentes","frontend","Command-Center","Cerebro","Fichas","Auditoria","Orquestador",
         "Grupo-Trabajo-1","Grupo-Trabajo-2","Grupo-Trabajo-3","Maxbry-AGI",
         "openclaw-install","claude-code-config","mimo-code-config","nct-router","nct-mcp-gateway"]
out = []
for r in repos:
    p = f"/opt/nct/repos/{r}"
    item = {"nombre": r, "ruta": p, "branch": None, "ultimo_commit": None, "remote": None, "estado": "no_existe"}
    if os.path.isdir(f"{p}/.git"):
        try:
            item["branch"] = subprocess.check_output(["git","-C",p,"rev-parse","--abbrev-ref","HEAD"], text=True).strip()
            item["ultimo_commit"] = subprocess.check_output(["git","-C",p,"log","-1","--format=%H|%cI|%s"], text=True).strip()
            item["remote"] = subprocess.check_output(["git","-C",p,"remote","get-url","origin"], text=True).strip()
            item["estado"] = "ok"
        except Exception as x: item["estado"] = f"error: {x}"
    out.append(item)
with open("/opt/nct/repos/repos_inventory.json","w") as f:
    json.dump({"generado": datetime.datetime.utcnow().isoformat()+"Z",
               "cuenta": "maxbry123-commits",
               "total": len(out),
               "ok": sum(1 for i in out if i["estado"]=="ok"),
               "repos": out}, f, indent=2)
print("OK", len(out))
PYEOF
