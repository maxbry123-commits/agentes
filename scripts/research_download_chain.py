import json, shutil, subprocess, sys, time
from pathlib import Path

DEST = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path('Download code/archivos').resolve()
WORK = Path(sys.argv[2]).resolve() if len(sys.argv) > 2 else Path('_work/research-download').resolve()
SRC, PACK = WORK / 'src', WORK / 'pack'
MANIFEST = DEST / 'RESEARCH_DOWNLOAD_MANIFEST.jsonl'
ZIP_LIMIT, BATCH_LIMIT, CHUNK_LIMIT = 15*1024*1024, 90*1024*1024, 12*1024*1024
REPOS = [
('01','SearchOS','https://github.com/antins-labs/SearchOS.git'),
('02','SearXNG','https://github.com/searxng/searxng.git'),
('03','OpenDeepResearch','https://github.com/langchain-ai/open_deep_research.git'),
('04','GPT-Researcher','https://github.com/assafelovic/gpt-researcher.git'),
('05','STORM','https://github.com/stanford-oval/storm.git'),
('06','Shandu','https://github.com/jolovicdev/shandu.git'),
('07','Vane','https://github.com/ItzCrazyKns/Vane.git'),
('08','Haystack','https://github.com/deepset-ai/haystack.git'),
('09','Crawl4AI','https://github.com/unclecode/crawl4ai.git'),
('10','Perplexica','https://github.com/cognitive-builder/Perplexica.git'),
('11','Dagu','https://github.com/dagucloud/dagu.git'),
('12','Conductor','https://github.com/conductor-oss/conductor.git'),
('13','Temporal','https://github.com/temporalio/temporal.git'),
('14','Argo-Workflows','https://github.com/argoproj/argo-workflows.git'),
('15','Kestra','https://github.com/kestra-io/kestra.git'),
('16','LangGraph','https://github.com/langchain-ai/langgraph.git'),
('17','Hatchet','https://github.com/hatchet-dev/hatchet.git'),
('18','Windmill','https://github.com/windmill-labs/windmill.git'),
('19','Dagster','https://github.com/dagster-io/dagster.git'),
('20','Prefect','https://github.com/PrefectHQ/prefect.git')]

def run(c, cwd=None): subprocess.run(c, cwd=cwd, check=True)
def done(slug):
    if not MANIFEST.exists(): return False
    return any(json.loads(x).get('slug') == slug and json.loads(x).get('status') == 'COMPLETE' for x in MANIFEST.read_text().splitlines() if x.strip())

def make_zip(slug, root, files, part, out):
    stage = PACK / f'{slug}__part_{part:04d}'; shutil.rmtree(stage, ignore_errors=True); stage.mkdir(parents=True)
    split=[]
    for p in files:
        rel=p.relative_to(root); target=stage/slug/rel; target.parent.mkdir(parents=True, exist_ok=True); size=p.stat().st_size
        if size <= CHUNK_LIMIT: shutil.copy2(p,target)
        else:
            d=target.parent/(target.name+'.chunks'); d.mkdir(parents=True,exist_ok=True)
            with p.open('rb') as f:
                i=0
                while data:=f.read(CHUNK_LIMIT): (d/f'{target.name}.part-{i:04d}').write_bytes(data); i+=1
            split.append({'repo':slug,'path':str(rel),'chunks_dir':str(d.relative_to(stage)),'bytes':size})
    if split: (stage/'SPLIT_FILES.json').write_text(json.dumps(split,indent=2))
    out=Path(out).resolve(); out.parent.mkdir(parents=True,exist_ok=True); out.unlink(missing_ok=True)
    run(['zip','-q','-r','-9','-y',str(out),'.'],cwd=stage)
    if not out.is_file(): raise RuntimeError(f'ZIP was not created: {out}')
    size=out.stat().st_size; shutil.rmtree(stage,ignore_errors=True); return size

def partition(slug, root, files):
    pending=sorted(files,key=str); groups=[]; part=1; probe_no=0
    while pending:
        lo,hi,best=1,len(pending),None
        while lo<=hi:
            mid=(lo+hi)//2; probe_no+=1; probe=PACK/f'.probe_{slug}_{part:04d}_{probe_no:04d}.zip'
            size=make_zip(slug,root,pending[:mid],part,probe)
            if size<=ZIP_LIMIT:
                if best: best[1].unlink(missing_ok=True)
                best=(mid,probe,size); lo=mid+1
            else: probe.unlink(missing_ok=True); hi=mid-1
        if not best:
            probe_no+=1; probe=PACK/f'.probe_{slug}_{part:04d}_{probe_no:04d}.zip'; size=make_zip(slug,root,pending[:1],part,probe)
            if size>ZIP_LIMIT: raise RuntimeError(f'Cannot package {pending[0]} under 15 MiB')
            best=(1,probe,size)
        n,probe,size=best; final=PACK/f'{slug}_{part:04d}.zip'; probe.replace(final); groups.append((final,size)); pending=pending[n:]; part+=1
    return groups

def push_batch(label):
    for attempt in range(1,4):
        try:
            run(['git','fetch','origin','main']); run(['git','rebase','origin/main']); run(['git','push','origin','HEAD:main']); print(f'PUSH PASS {label} attempt {attempt}'); return
        except subprocess.CalledProcessError:
            if attempt==3: raise
            time.sleep(attempt*2)

def commit_batch(n,label):
    if not n:return
    run(['git','add',str(DEST)])
    if subprocess.run(['git','diff','--cached','--quiet']).returncode==0:return
    run(['git','config','user.name','github-actions[bot]']); run(['git','config','user.email','41898282+github-actions[bot]@users.noreply.github.com'])
    run(['git','commit','-m',f'build(download): research queue batch {label} ({n} bytes)']); push_batch(label)

DEST.mkdir(parents=True,exist_ok=True); SRC.mkdir(parents=True,exist_ok=True); PACK.mkdir(parents=True,exist_ok=True)
batch=0; batch_no=1
for number,slug,url in REPOS:
    print(f'===== QUEUE {number}/20: {slug} =====')
    if done(slug): print(f'{slug}: COMPLETE; skipping'); continue
    root=SRC/slug; shutil.rmtree(root,ignore_errors=True); run(['git','clone','--depth','1','--no-tags',url,str(root)])
    sha=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip(); shutil.rmtree(root/'.git',ignore_errors=True)
    parts=partition(slug,root,[p for p in root.rglob('*') if p.is_file()])
    for z,size in parts:
        if batch and batch+size>BATCH_LIMIT: commit_batch(batch,f'{batch_no:03d}'); batch_no+=1; batch=0
        shutil.copy2(z,DEST/z.name); batch+=size
    with MANIFEST.open('a') as f: f.write(json.dumps({'number':int(number),'slug':slug,'source':url,'source_commit':sha,'parts':len(parts),'status':'COMPLETE'},sort_keys=True)+'\n')
    shutil.rmtree(root,ignore_errors=True); shutil.rmtree(PACK,ignore_errors=True); PACK.mkdir(parents=True,exist_ok=True)
commit_batch(batch,f'{batch_no:03d}-final')
print('===== QUEUE COMPLETE: 20/20 repositories processed =====')
