"""YAIWES PostgreSQL adapter: initialize, start and query the PostgreSQL built from the moved source."""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

PLUGIN_ID = "yaiwes.durability.postgresql"

def descriptor() -> dict[str, str]:
    return {"plugin_id": PLUGIN_ID, "role": "run_state_store", "microtest": "real_server_query_20_plus_21"}

def run_microtest(prefix: str | Path) -> dict[str, Any]:
    prefix=Path(prefix).resolve(); bindir=prefix / "bin"
    for name in ("initdb","pg_ctl","psql","postgres"):
        if not (bindir/name).is_file(): raise RuntimeError(f"POSTGRES_BINARY_MISSING:{name}")
    with tempfile.TemporaryDirectory(prefix="yaiwes-pg-") as td_s:
        td=Path(td_s); data=td/"data"; sock=td/"sock"; sock.mkdir(); log=td/"postgres.log"; port="55439"
        env=os.environ.copy(); env["LC_ALL"]="C"
        init=subprocess.run([str(bindir/"initdb"),"--no-locale","-E","UTF8","-A","trust","-U","postgres","-D",str(data)],env=env,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=90)
        if init.returncode != 0: raise RuntimeError("INITDB_FAILED:"+init.stdout[-6000:])
        started=False
        try:
            start=subprocess.run([str(bindir/"pg_ctl"),"-D",str(data),"-l",str(log),"-o",f"-F -k {sock} -p {port}","-w","start"],env=env,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=90)
            if start.returncode != 0: raise RuntimeError("PG_START_FAILED:"+start.stdout[-6000:]+"\n"+(log.read_text(errors='replace')[-6000:] if log.exists() else ''))
            started=True
            q=subprocess.run([str(bindir/"psql"),"-h",str(sock),"-p",port,"-U","postgres","-d","postgres","-Atqc","SELECT 20+21;"],env=env,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=60)
            value=q.stdout.strip()
            if q.returncode != 0 or value!="41": raise RuntimeError(f"PSQL_QUERY_FAILED:{q.returncode}:{value}:{q.stdout[-6000:]}")
            return {"status":"PASS","capability":"real_server_query","query":"SELECT 20+21","value":41,"initdb":0,"server_started":True}
        finally:
            if started:
                subprocess.run([str(bindir/"pg_ctl"),"-D",str(data),"-m","fast","-w","stop"],env=env,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=60)

if __name__ == "__main__":
    result=run_microtest(sys.argv[1]); print("YAIWES_POSTGRESQL_RESULT="+json.dumps(result,separators=(",",":")))
