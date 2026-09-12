from __future__ import annotations
import json,subprocess
from pathlib import Path
def run_microtest()->dict:
    root=Path(__file__).resolve().parents[1];p=subprocess.run(['go','run','./yaiwes/microtest'],cwd=root,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=180)
    if p.returncode:raise RuntimeError(p.stdout)
    prefix='YAIWES_CASBIN_RESULT=';payload=next((x[len(prefix):] for x in p.stdout.splitlines() if x.startswith(prefix)),None)
    if not payload:raise RuntimeError('CASBIN_RESULT_MARKER_MISSING')
    r=json.loads(payload);assert r['alice_data1_read'] and not r['alice_data1_write'] and r['bob_data2_write'];return r
if __name__=='__main__':print('YAIWES_CASBIN_ADAPTER_RESULT='+json.dumps(run_microtest(),sort_keys=True))
