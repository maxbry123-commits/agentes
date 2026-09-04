#!/usr/bin/env python3
import argparse, hashlib, json, os, re, shutil, stat, subprocess, sys, tempfile, zipfile
from pathlib import Path, PurePosixPath
import extract_guardian_repair_v4_20260904 as g
import extract_dataset_independent_repair_20260904 as d

A=Path('Core kernel Yaiwes/Componentes recuperados A')
B=Path('Core kernel Yaiwes/Componentes recuperados B')
E=Path('Documentos proyectos Yaiwes/Evidencias extracción histórica/extraction')
EVID=Path('Documentos proyectos Yaiwes/Evidencias extracción histórica')
DATA={'HelpSteer2','PRM800K','Math-Shepherd'}

def load(p):
    try:return json.loads(p.read_text())
    except Exception:return None

def run_id_from(p,doc):
    try:return int(doc.get('run_id') or re.search(r'(\d+)',p.stem).group(1))
    except Exception:return 0

def baseline():
    rows=[]
    for p in E.glob('repair-*.json'):
        x=load(p)
        if x and isinstance(x.get('remaining_gaps'),list) and isinstance(x.get('retryable_gaps'),list) and isinstance(x.get('blocked_gaps'),list): rows.append((run_id_from(p,x),p,x))
    if not rows: raise RuntimeError('NO_FULL_GUARDIAN_BASELINE')
    return max(rows,key=lambda x:x[0])

def root_for(target):
    if str(target).startswith('Agente core kernel Yaiwes principal/'): return A
    if str(target).startswith('core kernel Yaiwes principal/'): return B
    raise RuntimeError('UNKNOWN_TARGET:'+str(target))

def key(row): return (row.get('target'),row.get('slug'))

def done_keys():
    done=set()
    for p in E.glob('canonical-*.json'):
        x=load(p) or {}
        for r in x.get('processed',[]):
            k=key(r)
            if all(k): done.add(k)
    for p in E.glob('dataset-recovery-*.json'):
        x=load(p) or {}; slug=x.get('slug')
        if slug and x.get('verdict')=='VERIFIED': done.add((f'Agente core kernel Yaiwes principal/{slug}',slug))
    return done

def unresolved():
    _,_,base=baseline(); done=done_keys(); out=[]; seen=set()
    for r in base['remaining_gaps']:
        k=key(r)
        if not all(k) or k in seen or k in done: continue
        seen.add(k); out.append({'target':k[0],'slug':k[1]})
    return out

def ls_children(root):
    txt=subprocess.check_output(['git','ls-tree','HEAD:'+root.as_posix()],text=True)
    out=[]
    for line in txt.splitlines():
        meta,name=line.split('\t',1); mode,typ,sha=meta.split()
        out.append((name,typ,sha))
    return out

def archive_names(root,slug):
    rx=re.compile(r'^'+re.escape(slug)+r'(?:_[0-9]{4})?\.zip$',re.I)
    return [n for n,t,_ in ls_children(root) if t=='blob' and rx.match(n)]

def emit_sparse():
    pats=['/Core kernel Yaiwes/scripts/','/Documentos proyectos Yaiwes/Evidencias extracción histórica/']
    for r in unresolved():
        root=root_for(r['target']); slug=r['slug']; names=archive_names(root,slug)
        if not names: raise RuntimeError(f'SOURCE_ARCHIVE_GAP:{root}:{slug}')
        pats += ['/'+root.as_posix()+'/'+n for n in names]
        pats.append('/'+root.as_posix()+'/'+slug+'/')
    print('\n'.join(dict.fromkeys(pats)))

def sha(p): return g.digest(p)

def safe_backup(src,base,rel):
    dst=base/PurePosixPath(rel)
    dst.parent.mkdir(parents=True,exist_ok=True)
    if dst.exists():
        if sha(dst)==sha(src): src.unlink(); return dst
        dst=dst.with_name(dst.name+'.'+sha(src)[:12])
        if dst.exists() and sha(dst)==sha(src): src.unlink(); return dst
    shutil.move(str(src),str(dst)); return dst

def evacuate_pointer_files(target,root,slug):
    st=g.tree_state(target); moved=[]
    bucket='A' if root==A else 'B'
    for rel in st.get('pointers',[]):
        p=target/PurePosixPath(rel)
        if p.is_file():
            b=safe_backup(p,EVID/'LFS pointer evidence'/bucket/slug,rel+'.pointer')
            moved.append({'path':rel,'backup':str(b)})
    return moved

def extract_stage(parts,stage,slug):
    excluded=[]; hashes={}; seen={}
    for z in sorted(parts,key=lambda p:p.name.lower()):
        hashes[str(z)]=sha(z)
        with zipfile.ZipFile(z) as a:
            bad=a.testzip()
            if bad: raise RuntimeError(f'CRC_FAIL:{z}:{bad}')
            for info in a.infolist():
                if info.is_dir(): continue
                if not g.validate_info(info): raise RuntimeError(f'UNSAFE_ZIP:{z}:{info.filename}')
                q=g.safe_name(info.filename)
                if q is None: raise RuntimeError(f'UNSAFE_ZIP:{z}:{info.filename}')
                rel=q.as_posix()
                with a.open(info) as f: data=f.read()
                ptr=g.parse_lfs_pointer_bytes(data) if len(data)<=1024 else None
                sig=('pointer',json.dumps(ptr,sort_keys=True)) if ptr else ('blob',hashlib.sha256(data).hexdigest())
                if rel in seen and seen[rel]!=sig: raise RuntimeError(f'ZIP_DUPLICATE_PATH:CROSS_PART:{rel}')
                seen[rel]=sig
                if ptr:
                    excluded.append({'path':rel,**ptr}); continue
                if len(data)>=g.MAX_GIT_BLOB: raise RuntimeError(f'GIT_BLOB_LIMIT_GAP:{rel}:{len(data)}')
                p=stage/q; p.parent.mkdir(parents=True,exist_ok=True)
                if p.exists() and hashlib.sha256(p.read_bytes()).hexdigest()!=hashlib.sha256(data).hexdigest(): raise RuntimeError(f'ZIP_DUPLICATE_PATH:{rel}')
                p.write_bytes(data)
    kids=list(stage.iterdir()); payload=stage
    if len(kids)==1 and kids[0].is_dir() and g.norm(kids[0].name)==g.norm(slug): payload=kids[0]
    return payload,hashes,excluded

def merge_source(payload,target,root,slug):
    copied=0; replaced=[]; bucket='A' if root==A else 'B'
    for p in sorted(x for x in payload.rglob('*') if x.is_file()):
        rel=p.relative_to(payload); q=target/rel; q.parent.mkdir(parents=True,exist_ok=True)
        if q.exists():
            if sha(q)==sha(p): continue
            b=safe_backup(q,EVID/'collision backups'/bucket/slug,rel.as_posix())
            replaced.append({'path':rel.as_posix(),'backup':str(b)})
        shutil.copy2(p,q); copied+=1
    return copied,replaced

def configure_dataset_root():
    d.ROOT=A
    for slug,cfg in d.CONFIG.items(): cfg['target']=A/slug

def repair_row(r):
    root=root_for(r['target']); slug=r['slug']; target=root/slug
    names=archive_names(root,slug); parts=[root/n for n in names]
    if not parts: raise RuntimeError(f'SOURCE_ARCHIVE_GAP:{root}:{slug}')
    before=g.completeness_state(target,parts,slug)
    if before['complete']:
        return {**r,'actual_target':str(target),'status':'VERIFIED_EXISTING_ACTUAL','files':before['files'],'tree_sha256':before['tree_sha256']}
    ptr_backups=evacuate_pointer_files(target,root,slug)
    with tempfile.TemporaryDirectory(prefix='yaiwes-final-close-') as td:
        stage=Path(td)/'stage'; stage.mkdir(); payload,hashes,excluded=extract_stage(parts,stage,slug)
        copied,replaced=merge_source(payload,target,root,slug)
    dataset=None
    if slug in DATA:
        if root!=A: raise RuntimeError(f'DATASET_UNEXPECTED_ROOT:{slug}:{root}')
        configure_dataset_root(); dataset=d.repair(slug)
    final=g.completeness_state(target,parts,slug)
    if not final['complete']:
        raise RuntimeError('FINAL_COMPLETENESS_GAP:'+json.dumps({'missing':final['missing_required'][:20],'pointer_missing':final['missing_required_pointer_files'][:20],'source_errors':final['source_errors'][:10],'pointers':final['pointers'][:20]},ensure_ascii=False))
    return {**r,'actual_target':str(target),'status':'FINAL_REPAIRED_VERIFIED','files':final['files'],'bytes':final['bytes'],'tree_sha256':final['tree_sha256'],'copied':copied,'collision_backups':replaced,'pointer_backups':ptr_backups,'excluded_lfs_source_members':final['excluded_lfs_source_members'],'dataset_recovery':dataset,'part_sha256':hashes}

def repair_all():
    rows=unresolved(); processed=[]; failures=[]
    for r in rows:
        try: processed.append(repair_row(r))
        except Exception as e: failures.append({**r,'error':str(e)})
    report={'schema':'yaiwes.canonical.final-close.v1','run_id':os.getenv('GITHUB_RUN_ID','local'),'selected':len(rows),'processed':processed,'failures':failures,'verdict':'REPAIR_PASS' if not failures else 'REPAIR_GAPS'}
    E.mkdir(parents=True,exist_ok=True); out=E/f"canonical-final-close-{os.getenv('GITHUB_RUN_ID','local')}.json"; out.write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n'); print(json.dumps(report,ensure_ascii=False))
    return 0 if not failures else 73

def verify():
    _,bp,base=baseline(); done=done_keys(); missing=[]; tree_missing=[]
    cache={}
    for r in base['remaining_gaps']:
        k=key(r)
        if not all(k): continue
        if k not in done: missing.append({'target':k[0],'slug':k[1]})
        root=root_for(k[0])
        if root not in cache: cache[root]={n:t for n,t,_ in ls_children(root)}
        if cache[root].get(k[1])!='tree': tree_missing.append({'target':str(root/k[1]),'slug':k[1]})
    report={'schema':'yaiwes.canonical.final-verification.v1','run_id':os.getenv('GITHUB_RUN_ID','local'),'baseline':bp.name,'baseline_remaining':len(base['remaining_gaps']),'done':len(base['remaining_gaps'])-len(missing),'missing_evidence':missing,'missing_target_trees':tree_missing,'verdict':'VERIFIED_CLOSED' if not missing and not tree_missing else 'GAPS_PENDING'}
    E.mkdir(parents=True,exist_ok=True); out=E/f"canonical-final-verification-{os.getenv('GITHUB_RUN_ID','local')}.json"; out.write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n'); print(json.dumps(report,ensure_ascii=False))
    return 0 if report['verdict']=='VERIFIED_CLOSED' else 74

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--emit-sparse',action='store_true'); ap.add_argument('--repair',action='store_true'); ap.add_argument('--verify',action='store_true'); a=ap.parse_args()
    if a.emit_sparse: emit_sparse(); return 0
    if a.repair: return repair_all()
    if a.verify: return verify()
    return 2
if __name__=='__main__': sys.exit(main())
