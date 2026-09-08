import hashlib,json,os,shutil,subprocess,sys,time
from pathlib import Path
Q=Path('scripts/backend-watchdog-yaiwes-34-download-extract-20260908/QUEUE.json')
WORK=Path('_work/backend-watchdog-full-repair-02')
REPORT=Path('Core kernel Yaiwes/Backend watchdog workflow adaptativo/FULL_REPO_REPAIR_02.json')
LFS=b'version https://git-lfs.github.com/spec/v1'; LIM=100*1024*1024

def run(c,cwd=None,cap=False):
 k={'cwd':cwd,'check':True,'text':True}
 if cap:k['stdout']=subprocess.PIPE
 return subprocess.run(c,**k)
def retry(c,cwd=None):
 for n in range(1,4):
  try:return run(c,cwd,True)
  except subprocess.CalledProcessError:
   if n==3:raise
   time.sleep(n*5)
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def files(r):return sorted(x for x in r.rglob('*') if x.is_file())
def clone(url,out):
 shutil.rmtree(out,ignore_errors=True);out.parent.mkdir(parents=True,exist_ok=True)
 retry(['git','clone','--depth','1','--no-tags','--single-branch',url+'.git',str(out)])
 s=run(['git','rev-parse','HEAD'],out,True).stdout.strip();shutil.rmtree(out/'.git',ignore_errors=True);return s
def validate(r):
 fs=files(r)
 if not fs:raise RuntimeError('EMPTY_SOURCE_TREE')
 for p in fs:
  z=p.stat().st_size
  if z>=LIM:raise RuntimeError('GIT_BLOB_LIMIT_GAP:'+str(p.relative_to(r)))
  if z<=1024 and p.read_bytes().startswith(LFS):raise RuntimeError('SOURCE_LFS_POINTER_GAP:'+str(p.relative_to(r)))
 return [(p.relative_to(r).as_posix(),p.stat().st_size,sha(p)) for p in fs]
def install(c,src,commit,rec):
 dest=Path(c['destination']); inc=WORK/'incoming'/c['slug']; bak=WORK/'backup'/c['slug']
 shutil.rmtree(inc,ignore_errors=True);shutil.rmtree(bak,ignore_errors=True);inc.parent.mkdir(parents=True,exist_ok=True);shutil.copytree(src,inc,symlinks=True)
 (inc/'SOURCE_URL.txt').write_text(c['source_url']+'\n');(inc/'SOURCE_COMMIT.txt').write_text(commit+'\n');(inc/'SOURCE_LICENSE.txt').write_text('SOURCE_REPOSITORY_LICENSE_FILES_ONLY\n')
 (inc/'SOURCE_SHA256SUMS.txt').write_text(''.join(f'{d}  {r}\n' for r,_,d in rec))
 for r,s,d in rec:
  p=inc/r
  if not p.is_file() or p.stat().st_size!=s or sha(p)!=d:raise RuntimeError('STAGING_READBACK_FAIL:'+r)
 if dest.exists():bak.parent.mkdir(parents=True,exist_ok=True);dest.rename(bak)
 dest.parent.mkdir(parents=True,exist_ok=True);inc.rename(dest);shutil.rmtree(bak,ignore_errors=True)
 for r,s,d in rec:
  p=dest/r
  if not p.is_file() or p.stat().st_size!=s or sha(p)!=d:raise RuntimeError('DESTINATION_READBACK_FAIL:'+r)
def push(label):
 run(['git','add','--all']);
 if subprocess.run(['git','diff','--cached','--quiet']).returncode==0:return
 run(['git','config','user.name','github-actions[bot]']);run(['git','config','user.email','41898282+github-actions[bot]@users.noreply.github.com']);run(['git','commit','-m','repair(backend-watchdog): full repo '+label])
 for n in range(1,4):
  try:run(['git','fetch','origin','main']);run(['git','rebase','--autostash','origin/main']);run(['git','push','--no-verify','origin','HEAD:main']);return
  except subprocess.CalledProcessError:
   if n==3:raise
   time.sleep(n*3)
q=json.load(Q.open());g=[];ok=[]
for c in q['components']:
 try:
  src=WORK/'src'/c['slug'];commit=clone(c['source_url'],src);rec=validate(src);install(c,src,commit,rec);push(c['slug']);ok.append({'slug':c['slug'],'commit':commit,'files':len(rec)})
 except Exception as e:g.append({'slug':c['slug'],'error':str(e)})
REPORT.parent.mkdir(parents=True,exist_ok=True);REPORT.write_text(json.dumps({'expected':len(q['components']),'verified':len(ok),'gaps':g,'verified_items':ok},indent=2)+'\n');push('report')
if g:raise SystemExit('GAPS_REMAIN='+str(len(g)))
