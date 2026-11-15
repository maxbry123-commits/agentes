import json, os, shutil, subprocess, sys, time
from pathlib import Path
os.environ['GIT_LFS_SKIP_SMUDGE']='1'
os.environ['GIT_LFS_SKIP_PUSH']='1'
os.environ['GIT_TERMINAL_PROMPT']='0'
DEST=Path(sys.argv[1]).resolve(); WORK=Path(sys.argv[2]).resolve(); SRC=WORK/'src'; PACK=WORK/'pack'
MANIFEST=DEST/'RESEARCH_DOWNLOAD_MANIFEST.jsonl'; SPLIT_TARGET=12000000; MAX_ZIP=17*1000*1000; BATCH_LIMIT=90*1024*1024; CHUNK=8*1024*1024
REPOS=[('01','Kubernetes','https://github.com/kubernetes/kubernetes.git'),('02','Ray','https://github.com/ray-project/ray.git'),('03','AI-Scientist-v2','https://github.com/SakanaAI/AI-Scientist-v2.git'),('04','Reflexion','https://github.com/noahshinn/reflexion.git'),('05','Click','https://github.com/pallets/click.git'),('06','JSON-Schema','https://github.com/json-schema-org/json-schema-spec.git'),('07','OpenTelemetry-Python','https://github.com/open-telemetry/opentelemetry-python.git'),('08','pymerkle','https://github.com/fmerg/pymerkle.git'),('09','MINIX3','https://github.com/Stichting-MINIX-Research-Foundation/minix.git'),('10','durable_rules','https://github.com/jruizgit/rules.git'),('11','BullMQ','https://github.com/taskforcesh/bullmq.git'),('12','Traefik','https://github.com/traefik/traefik.git'),('13','Agenta','https://github.com/Agenta-AI/agenta.git'),('14','LMQL','https://github.com/eth-sri/lmql.git'),('15','XState','https://github.com/statelyai/xstate.git'),('16','Casbin','https://github.com/casbin/casbin.git'),('17','PydanticAI','https://github.com/pydantic/pydantic-ai.git'),('18','Ragas','https://github.com/explodinggradients/ragas.git'),('19','Stamina','https://github.com/hynek/stamina.git'),('20','Firecracker','https://github.com/firecracker-microvm/firecracker.git'),('21','AG2','https://github.com/ag2ai/ag2.git'),('22','MCP-TypeScript-SDK','https://github.com/modelcontextprotocol/typescript-sdk.git'),('23','Agno','https://github.com/agno-agi/agno.git'),('24','Helicone','https://github.com/Helicone/helicone.git'),('25','GrowthBook','https://github.com/growthbook/growthbook.git'),('26','Aider','https://github.com/Aider-AI/aider.git'),('27','Anthropic-Skills','https://github.com/anthropics/skills.git'),('28','OpenAI-Guardrails','https://github.com/openai/openai-guardrails-python.git'),('29','Kestra','https://github.com/kestra-io/kestra.git'),('30','Cadence','https://github.com/uber/cadence.git'),('31','Hatchet','https://github.com/hatchet-dev/hatchet.git'),('32','SQLite','https://github.com/sqlite/sqlite.git'),('33','Soul-Spec','https://github.com/AntonioTF5/soul-spec.git')]
def run(c,cwd=None): subprocess.run(c,cwd=cwd,check=True)
def note(**kw):
    MANIFEST.parent.mkdir(parents=True,exist_ok=True)
    with MANIFEST.open('a') as f: f.write(json.dumps(kw,sort_keys=True)+'\n')
def done(slug):
    if not MANIFEST.exists(): return False
    return any((lambda d:d.get('slug')==slug and d.get('status')=='COMPLETE')(json.loads(x)) for x in MANIFEST.read_text().splitlines() if x.strip())
def stage_repo(slug,root):
    stage=PACK/f'{slug}_stage'; shutil.rmtree(stage,ignore_errors=True); stage.mkdir(parents=True); records=[]
    for p in root.rglob('*'):
        if not p.is_file(): continue
        rel=p.relative_to(root); target=stage/slug/rel; target.parent.mkdir(parents=True,exist_ok=True); size=p.stat().st_size
        if size<=CHUNK: shutil.copy2(p,target); continue
        d=target.parent/(target.name+'.chunks'); d.mkdir(parents=True,exist_ok=True)
        with p.open('rb') as f:
            i=0
            while True:
                data=f.read(CHUNK)
                if not data: break
                (d/f'{target.name}.part-{i:04d}').write_bytes(data); i+=1
        records.append({'repo':slug,'path':str(rel),'chunks_dir':str(d.relative_to(stage)),'bytes':size,'chunk_bytes':CHUNK})
    if records: (stage/'SPLIT_FILES.json').write_text(json.dumps(records,indent=2))
    return stage
def package(slug,root):
    stage=stage_repo(slug,root); full=PACK/f'{slug}_full.zip'; full.unlink(missing_ok=True)
    run(['zip','-q','-r','-1','-y',str(full.resolve()),'.'],cwd=stage)
    if full.stat().st_size<=SPLIT_TARGET:
        out=PACK/f'{slug}_0001.zip'; full.replace(out); shutil.rmtree(stage,ignore_errors=True); return [(out,out.stat().st_size)]
    before=set(PACK.glob('*.zip'))
    try: run(['zipsplit','-n',str(SPLIT_TARGET),'-b',str(PACK.resolve()),str(full.resolve())])
    except subprocess.CalledProcessError:
        print(f'SKIP ZIPSPLIT FAIL {slug}',flush=True); shutil.rmtree(stage,ignore_errors=True); return []
    full.unlink(missing_ok=True)
    made=[p for p in PACK.glob('*.zip') if p not in before and p != full]
    if not made:
        print(f'SKIP ZIPSPLIT EMPTY {slug}',flush=True); shutil.rmtree(stage,ignore_errors=True); return []
    out=[]
    for i,p in enumerate(sorted(made,key=lambda p:(p.stat().st_mtime,p.name)),1):
        q=PACK/f'{slug}_{i:04d}.zip'; p.replace(q); size=q.stat().st_size
        if size>MAX_ZIP:
            print(f'SKIP MAX_ZIP {q} {size}',flush=True); shutil.rmtree(stage,ignore_errors=True); return []
        if subprocess.run(['unzip','-tq',str(q)]).returncode!=0:
            print(f'SKIP CRC {q}',flush=True); shutil.rmtree(stage,ignore_errors=True); return []
        out.append((q,size))
    shutil.rmtree(stage,ignore_errors=True); return out
def push(label):
    try:
        run(['git','fetch','origin','main']); run(['git','rebase','origin/main']); run(['git','push','origin','HEAD:main']); print(f'PUSH PASS {label}'); return
    except subprocess.CalledProcessError:
        print(f'SKIP PUSH FAIL {label}',flush=True); return
def commit(n,label):
    if not n:return
    run(['git','add','--sparse',str(DEST)])
    if subprocess.run(['git','diff','--cached','--quiet']).returncode==0:return
    run(['git','config','user.name','github-actions[bot]']); run(['git','config','user.email','41898282+github-actions[bot]@users.noreply.github.com']); run(['git','commit','-m',f'build(download): research queue batch {label} ({n} bytes)']); push(label)
DEST.mkdir(parents=True,exist_ok=True); SRC.mkdir(parents=True,exist_ok=True); PACK.mkdir(parents=True,exist_ok=True)
batch=batch_no=0; skipped=[]
CLONE=['git','-c','filter.lfs.smudge=','-c','filter.lfs.clean=','-c','filter.lfs.process=','-c','filter.lfs.required=false','clone','--depth','1','--single-branch','--no-tags']
for number,slug,url in REPOS:
    print(f'===== QUEUE {number}/33: {slug} =====')
    if done(slug): print(f'{slug}: COMPLETE; skipping'); continue
    root=SRC/slug; shutil.rmtree(root,ignore_errors=True)
    try: run(CLONE+[url,str(root)])
    except subprocess.CalledProcessError:
        print(f'SKIP CLONE FAIL {number} {slug} {url}',flush=True)
        note(number=int(number),slug=slug,source=url,status='SKIPPED',reason='clone'); skipped.append(number); continue
    sha=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip(); shutil.rmtree(root/'.git',ignore_errors=True)
    parts=package(slug,root)
    if not parts:
        print(f'SKIP PACKAGE {number} {slug}',flush=True)
        note(number=int(number),slug=slug,source=url,status='SKIPPED',reason='package'); skipped.append(number)
        shutil.rmtree(root,ignore_errors=True); continue
    print(f'{slug}: {len(parts)} ZIP part(s)')
    for z,size in parts:
        if batch and batch+size>BATCH_LIMIT: commit(batch,f'{batch_no:03d}'); batch=0; batch_no+=1
        shutil.copy2(z,DEST/z.name); batch+=size; print(f'  {z.name}: {size} bytes; batch={batch}')
    note(number=int(number),slug=slug,source=url,source_commit=sha,parts=len(parts),status='COMPLETE')
    shutil.rmtree(root,ignore_errors=True); shutil.rmtree(PACK,ignore_errors=True); PACK.mkdir(parents=True,exist_ok=True)
commit(batch,f'{batch_no:03d}-final')
print('SKIPPED',skipped)
print('===== QUEUE COMPLETE: 33/33 repositories processed =====')
