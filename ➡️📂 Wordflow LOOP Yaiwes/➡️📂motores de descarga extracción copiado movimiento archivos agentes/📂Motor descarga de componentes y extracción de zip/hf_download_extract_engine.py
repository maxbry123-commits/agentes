#!/usr/bin/env python3
from __future__ import annotations
import base64, hashlib, json, os, pathlib, shutil, stat, subprocess, tempfile, time, zipfile

SCHEMA='yaiwes.hf.download-extract.v1'
LFS_POINTER=b'version https://git-lfs.github.com/spec/v1\n'
PART_SIZE=int(os.getenv('PART_SIZE_MIB','12'))*1024*1024
MAX_BLOB=int(os.getenv('MAX_GITHUB_BLOB_MIB','95'))*1024*1024
SOURCE_REPO=os.getenv('SOURCE_REPO','').strip(); SOURCE_REF=os.getenv('SOURCE_REF','HEAD').strip() or 'HEAD'
SLUG=os.getenv('SLUG','').strip(); DEST_REPO=os.getenv('DEST_REPO','maxbry123-commits/frontend').strip()
DEST_BRANCH=os.getenv('DEST_BRANCH','main').strip() or 'main'; DEST_ROOT=os.getenv('DEST_ROOT','📂componentes open soure fromtend').strip().strip('/')
TOKEN=os.getenv('GITHUB_TOKEN',''); PUBLISH=os.getenv('PUBLISH','0').lower() in {'1','true','yes'}

def run(argv,cwd=None,env=None,check=True):
    p=subprocess.run(argv,cwd=cwd,env=env,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    if check and p.returncode: raise RuntimeError(f'COMMAND_FAILED:{argv[0]}:{p.returncode}:{p.stdout[-3000:]}')
    return p.stdout.strip()

def sha256(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
    return h.hexdigest()

def repo_url(r):
    if r.startswith('https://github.com/'): return r[:-4] if r.endswith('.git') else r
    return 'https://github.com/'+(r[:-4] if r.endswith('.git') else r)

def slug_default(r): return r.rstrip('/').removesuffix('.git').split('/')[-1]

def no_lfs(d):
    run(['git','config','filter.lfs.clean','cat'],d); run(['git','config','filter.lfs.smudge','cat'],d)
    run(['git','config','--unset-all','filter.lfs.process'],d,check=False); run(['git','config','filter.lfs.required','false'],d)

def auth_env():
    e=dict(os.environ); raw=base64.b64encode(f'x-access-token:{TOKEN}'.encode()).decode()
    e.update({'GIT_CONFIG_COUNT':'1','GIT_CONFIG_KEY_0':'http.https://github.com/.extraheader','GIT_CONFIG_VALUE_0':f'AUTHORIZATION: basic {raw}','GIT_TERMINAL_PROMPT':'0'})
    return e

def acquire(work):
    d=work/'source'; d.mkdir(); run(['git','init','-q'],d); run(['git','remote','add','origin',repo_url(SOURCE_REPO)+'.git'],d); no_lfs(d)
    run(['git','fetch','--depth=1','--filter=blob:none','origin',SOURCE_REF],d); run(['git','checkout','-q','--detach','FETCH_HEAD'],d)
    return d,run(['git','rev-parse','HEAD'],d)

def scan_tree(d,enforce_blob_limit=False):
    rows=[]; total=0; ptr=[]; special=[]; oversized=[]
    for p in sorted(d.rglob('*'),key=lambda x:x.as_posix()):
        if '.git' in p.parts: continue
        m=p.lstat().st_mode; rel=p.relative_to(d).as_posix()
        if stat.S_ISLNK(m) or not (stat.S_ISREG(m) or stat.S_ISDIR(m)): special.append(rel); continue
        if not p.is_file(): continue
        size=p.stat().st_size; total+=size
        if size<=1024 and p.read_bytes()[:1024].startswith(LFS_POINTER): ptr.append(rel)
        if enforce_blob_limit and size>=MAX_BLOB: oversized.append({'path':rel,'bytes':size})
        rows.append((p,rel,m))
    if ptr: raise RuntimeError('SOURCE_LFS_POINTER_GAP:'+','.join(ptr[:30]))
    if special: raise RuntimeError('SOURCE_SPECIAL_FILE_GAP:'+','.join(special[:30]))
    if oversized: raise RuntimeError('GIT_BLOB_LIMIT_GAP:'+json.dumps(oversized[:20]))
    if not rows: raise RuntimeError('EMPTY_SOURCE_TREE')
    return rows,total

def tree_hash(d):
    h=hashlib.sha256(); count=0; total=0
    for p in sorted((x for x in d.rglob('*') if x.is_file() and '.git' not in x.parts),key=lambda x:x.as_posix()):
        rel=p.relative_to(d).as_posix(); h.update(rel.encode()+b'\0'); h.update(sha256(p).encode()+b'\n'); count+=1; total+=p.stat().st_size
    return {'files':count,'bytes':total,'sha256':h.hexdigest()}

def make_zip(rows,bundle):
    with zipfile.ZipFile(bundle,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6,allowZip64=True) as z:
        for p,rel,m in rows:
            i=zipfile.ZipInfo(rel,date_time=(1980,1,1,0,0,0)); i.compress_type=zipfile.ZIP_DEFLATED; i.create_system=3
            i.external_attr=((0o755 if m & stat.S_IXUSR else 0o644)&0xffff)<<16
            with p.open('rb') as f: z.writestr(i,f.read(),compress_type=zipfile.ZIP_DEFLATED,compresslevel=6)
    with zipfile.ZipFile(bundle) as z:
        bad=z.testzip()
        if bad: raise RuntimeError('ZIP_CRC_FAIL:'+bad)

def split_bundle(bundle,out,slug):
    out.mkdir(); parts=[]
    with bundle.open('rb') as f:
        i=1
        while True:
            b=f.read(PART_SIZE)
            if not b: break
            p=out/f'{slug}.bundle.zip.part-{i:04d}'; p.write_bytes(b)
            if p.stat().st_size>=MAX_BLOB: raise RuntimeError(f'GIT_BLOB_LIMIT_GAP:{p.name}:{p.stat().st_size}')
            parts.append({'name':p.name,'bytes':p.stat().st_size,'sha256':sha256(p)}); i+=1
    if not parts: raise RuntimeError('EMPTY_BUNDLE')
    return parts

def rebuild(parts_dir,parts,bundle_sha):
    r=parts_dir/'_reconstructed.bundle.zip'
    with r.open('wb') as w:
        for row in parts:
            p=parts_dir/row['name']
            if sha256(p)!=row['sha256']: raise RuntimeError('PART_HASH_MISMATCH:'+row['name'])
            with p.open('rb') as q: shutil.copyfileobj(q,w,1024*1024)
    if sha256(r)!=bundle_sha: raise RuntimeError('BUNDLE_RECONSTRUCTION_HASH_MISMATCH')
    with zipfile.ZipFile(r) as z:
        bad=z.testzip()
        if bad: raise RuntimeError('RECONSTRUCTED_ZIP_CRC_FAIL:'+bad)
    return r

def safe_extract(bundle,dst):
    dst.mkdir()
    with zipfile.ZipFile(bundle) as z:
        for info in z.infolist():
            n=info.filename.replace('\\','/'); q=pathlib.PurePosixPath(n)
            if q.is_absolute() or '..' in q.parts: raise RuntimeError('UNSAFE_ZIP_PATH:'+n)
            mode=(info.external_attr>>16)&0o170000
            if mode in {stat.S_IFLNK,stat.S_IFCHR,stat.S_IFBLK,stat.S_IFIFO,stat.S_IFSOCK}: raise RuntimeError('UNSAFE_ZIP_SPECIAL:'+n)
            out=dst/pathlib.Path(*q.parts)
            if info.is_dir(): out.mkdir(parents=True,exist_ok=True); continue
            out.parent.mkdir(parents=True,exist_ok=True)
            with z.open(info) as r, out.open('wb') as w: shutil.copyfileobj(r,w,1024*1024)
    scan_tree(dst,enforce_blob_limit=True)

def sparse_checkout(d,repo,branch,pathspec,env):
    d.mkdir(); run(['git','init','-q'],d); run(['git','remote','add','origin',f'https://github.com/{repo}.git'],d); no_lfs(d)
    run(['git','sparse-checkout','init','--no-cone'],d); (d/'.git/info/sparse-checkout').write_text('/'+pathspec.strip('/')+'/\n')
    run(['git','fetch','--depth=1','--filter=blob:none','origin',branch],d,env=env); run(['git','checkout','-q','-B',branch,'FETCH_HEAD'],d)

def publish(work,parts_dir,extracted,manifest_path,slug):
    if not TOKEN: return {'verdict':'WRITE_AUTH_GAP','detail':'GITHUB_TOKEN is not available'}
    env=auth_env(); rel=(pathlib.Path(DEST_ROOT)/slug).as_posix(); dst=work/'destination'; sparse_checkout(dst,DEST_REPO,DEST_BRANCH,rel,env)
    run(['git','config','user.name','yaiwes-hf-combined-engine'],dst); run(['git','config','user.email','yaiwes-hf-combined-engine@users.noreply.github.com'],dst)
    target=dst/rel
    if target.exists(): raise RuntimeError('DESTINATION_EXISTS:'+rel)
    target.mkdir(parents=True); shutil.copytree(extracted,target/'code',dirs_exist_ok=False); archives=target/'_archives'; archives.mkdir()
    for p in sorted(parts_dir.iterdir()):
        if p.is_file() and not p.name.startswith('_') and p.name!='DOWNLOAD_EXTRACT_MANIFEST.json': shutil.copy2(p,archives/p.name)
    shutil.copy2(manifest_path,target/'DOWNLOAD_EXTRACT_MANIFEST.json')
    scan_tree(target,enforce_blob_limit=True)
    run(['git','add','--sparse','--',rel],dst); run(['git','commit','-m',f'build(hf-combined): publish {slug} bundle and extracted tree'],dst)
    run(['git','fetch','origin',DEST_BRANCH],dst,env=env); reb=run(['git','rebase',f'origin/{DEST_BRANCH}'],dst,env=env,check=False)
    if 'CONFLICT' in reb:
        run(['git','rebase','--abort'],dst,check=False); raise RuntimeError('NON_FAST_FORWARD_CONFLICT')
    run(['git','push','origin',f'HEAD:{DEST_BRANCH}'],dst,env=env); commit=run(['git','rev-parse','HEAD'],dst)
    rb=work/'readback'; sparse_checkout(rb,DEST_REPO,DEST_BRANCH,rel,env); rt=rb/rel; remote=json.loads((rt/'DOWNLOAD_EXTRACT_MANIFEST.json').read_text())
    for row in remote['parts']:
        p=rt/'_archives'/row['name']
        if not p.exists() or sha256(p)!=row['sha256']: raise RuntimeError('READBACK_ARCHIVE_HASH_GAP:'+row['name'])
    actual=tree_hash(rt/'code')
    if actual['sha256']!=remote['extracted_tree']['sha256'] or actual['files']!=remote['extracted_tree']['files']: raise RuntimeError('READBACK_TREE_HASH_GAP')
    return {'verdict':'PUBLISHED_AND_EXTRACTED_READBACK_VERIFIED','commit':commit}

def main():
    t=time.time()
    if not SOURCE_REPO: raise SystemExit(json.dumps({'schema':SCHEMA,'verdict':'INPUT_GAP','detail':'SOURCE_REPO required'}))
    slug=SLUG or slug_default(SOURCE_REPO)
    with tempfile.TemporaryDirectory(prefix='yaiwes-hf-combined-') as td:
        work=pathlib.Path(td); src,commit=acquire(work); rows,src_bytes=scan_tree(src); src_tree=tree_hash(src)
        bundle=work/f'{slug}.bundle.zip'; make_zip(rows,bundle); bsha=sha256(bundle); parts_dir=work/'parts'; parts=split_bundle(bundle,parts_dir,slug)
        rebuilt=rebuild(parts_dir,parts,bsha); extracted=work/'extracted'; safe_extract(rebuilt,extracted); ext_tree=tree_hash(extracted)
        if ext_tree!=src_tree: raise RuntimeError('SOURCE_EXTRACTED_TREE_MISMATCH')
        manifest={'schema':SCHEMA,'source_repo':SOURCE_REPO,'source_ref':SOURCE_REF,'source_commit':commit,'slug':slug,'source_files':len(rows),'source_bytes':src_bytes,'source_tree':src_tree,'bundle_bytes':bundle.stat().st_size,'bundle_sha256':bsha,'parts':parts,'part_size_limit_bytes':PART_SIZE,'max_github_blob_bytes':MAX_BLOB,'no_lfs':True,'reconstruction_verified':True,'extraction_verified':True,'extracted_tree':ext_tree}
        mp=parts_dir/'DOWNLOAD_EXTRACT_MANIFEST.json'; mp.write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n')
        pub=publish(work,parts_dir,extracted,mp,slug) if PUBLISH else {'verdict':'DRY_RUN_DOWNLOAD_EXTRACT_VERIFIED'}
        verdict='VERIFIED_CLOSED' if pub['verdict'] in {'DRY_RUN_DOWNLOAD_EXTRACT_VERIFIED','PUBLISHED_AND_EXTRACTED_READBACK_VERIFIED'} else pub['verdict']
        print(json.dumps({**manifest,'publish':pub,'elapsed_seconds':round(time.time()-t,2),'verdict':verdict},ensure_ascii=False,sort_keys=True))
if __name__=='__main__': main()
