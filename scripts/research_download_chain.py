import json, shutil, subprocess, sys, time
from pathlib import Path
DEST=Path(sys.argv[1]).resolve(); WORK=Path(sys.argv[2]).resolve(); SRC=WORK/'src'; PACK=WORK/'pack'
MANIFEST=DEST/'RESEARCH_DOWNLOAD_MANIFEST.jsonl'; ZIP_LIMIT=12900000; BATCH_LIMIT=90*1024*1024; CHUNK=8*1024*1024
REPOS=[('01','SearchOS','https://github.com/antins-labs/SearchOS.git'),('02','SearXNG','https://github.com/searxng/searxng.git'),('03','OpenDeepResearch','https://github.com/langchain-ai/open_deep_research.git'),('04','GPT-Researcher','https://github.com/assafelovic/gpt-researcher.git'),('05','STORM','https://github.com/stanford-oval/storm.git'),('06','Shandu','https://github.com/jolovicdev/shandu.git'),('07','Vane','https://github.com/ItzCrazyKns/Vane.git'),('08','Haystack','https://github.com/deepset-ai/haystack.git'),('09','Crawl4AI','https://github.com/unclecode/crawl4ai.git'),('10','Perplexica','https://github.com/cognitive-builder/Perplexica.git'),('11','Dagu','https://github.com/dagucloud/dagu.git'),('12','Conductor','https://github.com/conductor-oss/conductor.git'),('13','Temporal','https://github.com/temporalio/temporal.git'),('14','Argo-Workflows','https://github.com/argoproj/argo-workflows.git'),('15','Kestra','https://github.com/kestra-io/kestra.git'),('16','LangGraph','https://github.com/langchain-ai/langgraph.git'),('17','Hatchet','https://github.com/hatchet-dev/hatchet.git'),('18','Windmill','https://github.com/windmill-labs/windmill.git'),('19','Dagster','https://github.com/dagster-io/dagster.git'),('20','Prefect','https://github.com/PrefectHQ/prefect.git')]
def run(c,cwd=None): subprocess.run(c,cwd=cwd,check=True)
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
    run(['zip','-q','-r','-9','-y',str(full.resolve()),'.'],cwd=stage)
    if full.stat().st_size<=ZIP_LIMIT:
        out=PACK/f'{slug}_0001.zip'; full.replace(out); shutil.rmtree(stage,ignore_errors=True); return [(out,out.stat().st_size)]
    before=set(PACK.glob('*.zip')); run(['zipsplit','-n',str(ZIP_LIMIT),'-b',str(PACK.resolve()),str(full.resolve())]); full.unlink(missing_ok=True)
    made=[p for p in PACK.glob('*.zip') if p not in before and p != full]
    if not made: raise RuntimeError(f'zipsplit produced no parts for {slug}')
    out=[]
    for i,p in enumerate(sorted(made,key=lambda p:(p.stat().st_mtime,p.name)),1):
        q=PACK/f'{slug}_{i:04d}.zip'; p.replace(q); size=q.stat().st_size
        if size>ZIP_LIMIT: raise RuntimeError(f'ZIP part exceeds limit: {q} = {size}')
        subprocess.run(['unzip','-tq',str(q)],check=True); out.append((q,size))
    shutil.rmtree(stage,ignore_errors=True); return out
def push(label):
    for attempt in range(1,4):
        try:
            run(['git','fetch','origin','main']); run(['git','rebase','origin/main']); run(['git','push','origin','HEAD:main']); print(f'PUSH PASS {label} attempt {attempt}'); return
        except subprocess.CalledProcessError:
            if attempt==3: raise
            time.sleep(attempt*2)
def commit(n,label):
    if not n:return
    run(['git','add',str(DEST)])
    if subprocess.run(['git','diff','--cached','--quiet']).returncode==0:return
    run(['git','config','user.name','github-actions[bot]']); run(['git','config','user.email','41898282+github-actions[bot]@users.noreply.github.com']); run(['git','commit','-m',f'build(download): research queue batch {label} ({n} bytes)']); push(label)
DEST.mkdir(parents=True,exist_ok=True); SRC.mkdir(parents=True,exist_ok=True); PACK.mkdir(parents=True,exist_ok=True)
batch=batch_no=0
for number,slug,url in REPOS:
    print(f'===== QUEUE {number}/20: {slug} =====')
    if done(slug): print(f'{slug}: COMPLETE; skipping'); continue
    root=SRC/slug; shutil.rmtree(root,ignore_errors=True); run(['git','clone','--depth','1','--no-tags',url,str(root)])
    sha=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip(); shutil.rmtree(root/'.git',ignore_errors=True)
    parts=package(slug,root); print(f'{slug}: {len(parts)} ZIP part(s)')
    for z,size in parts:
        if batch and batch+size>BATCH_LIMIT: commit(batch,f'{batch_no:03d}'); batch=0; batch_no+=1
        shutil.copy2(z,DEST/z.name); batch+=size; print(f'  {z.name}: {size} bytes; batch={batch}')
    with MANIFEST.open('a') as f: f.write(json.dumps({'number':int(number),'slug':slug,'source':url,'source_commit':sha,'parts':len(parts),'status':'COMPLETE'},sort_keys=True)+'\n')
    shutil.rmtree(root,ignore_errors=True); shutil.rmtree(PACK,ignore_errors=True); PACK.mkdir(parents=True,exist_ok=True)
commit(batch,f'{batch_no:03d}-final'); print('===== QUEUE COMPLETE: 20/20 repositories processed =====')
