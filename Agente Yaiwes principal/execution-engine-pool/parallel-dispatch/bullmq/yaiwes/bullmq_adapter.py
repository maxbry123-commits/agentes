import json,subprocess
from pathlib import Path
PLUGIN_ID='yaiwes.parallel_dispatch.bullmq'
TARGET='Agente Yaiwes principal/execution-engine-pool/parallel-dispatch/bullmq'
def run_microtest(root):
    t=Path(root)/TARGET
    p=subprocess.run(['node',str(t/'yaiwes'/'bullmq_microtest.cjs')],cwd=t,text=True,capture_output=True,timeout=30)
    if p.returncode: raise RuntimeError(p.stderr[-1500:])
    line=next(x for x in p.stdout.splitlines() if x.startswith('YAIWES_BULLMQ_RESULT='))
    r=json.loads(line.split('=',1)[1])
    if r.get('input')!=21 or r.get('output')!=42: raise RuntimeError(str(r))
    return r
