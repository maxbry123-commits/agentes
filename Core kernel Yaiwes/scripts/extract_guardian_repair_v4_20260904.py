#!/usr/bin/env python3
"""Deterministic NO-LFS extraction guardian v4.

Ordinary Git members are required for every component. Git-LFS pointer members
are excluded only from non-dataset code scope and are recorded. Required dataset
pointer members must be recovered as exact bytes or a verified normal-Git split.
"""
import argparse, hashlib, json, os, re, shutil, stat, sys, tempfile, zipfile
from pathlib import Path, PurePosixPath

MAPS=[{"src":"core kernel Yaiwes principal","dst":"core kernel Yaiwes principal","layout":"flat"},{"src":"Agente core kernel Yaiwes principal","dst":"Agente core kernel Yaiwes principal","layout":"flat"}]
IGNORE={"RESEARCH_DOWNLOAD_MANIFEST.jsonl","EXTRACTION_GUARDIAN_REPORT.json"}
LFS_POINTER=b"version https://git-lfs.github.com/spec/v1\n"
MAX_GIT_BLOB=100*1024*1024
DATA_REQUIRED_SLUGS={"HelpSteer2","PRM800K","Math-Shepherd"}
NONRETRYABLE={"SOURCE_LFS_POINTER_GAP","GIT_BLOB_LIMIT_GAP","COLLISION_BLOCKED","UNSAFE_ZIP","ZIP_DUPLICATE_PATH","CRC_FAIL","MISSING_REQUIRED_SOURCE_FILES","DATA_RECOVERY_MISMATCH"}

def norm(s): return re.sub(r"[^a-z0-9]+","",s.lower())
def digest(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""): h.update(b)
    return h.hexdigest()
def is_lfs_pointer(path):
    try:
        if not path.is_file() or path.stat().st_size>1024: return False
        with path.open("rb") as f: return f.read(1024).startswith(LFS_POINTER)
    except OSError: return False
def parse_lfs_pointer_bytes(data):
    if not data.startswith(LFS_POINTER): return None
    s=data.decode("utf-8","replace")
    a=re.search(r"^oid sha256:([0-9a-f]{64})$",s,re.M); b=re.search(r"^size ([0-9]+)$",s,re.M)
    return {"sha256":a.group(1),"bytes":int(b.group(1))} if a and b else {"malformed":True}
def tree_state(root):
    files=[]; pointers=[]; oversized=[]
    if not root.exists(): return {"exists":False,"files":0,"bytes":0,"tree_sha256":None,"pointers":[],"oversized":[],"valid":False}
    h=hashlib.sha256(); total=0
    for p in sorted((x for x in root.rglob("*") if x.is_file()),key=lambda x:x.as_posix()):
        if p.name in IGNORE or p.suffix.lower()==".zip": continue
        rel=p.relative_to(root).as_posix(); size=p.stat().st_size; files.append(p); total+=size
        if is_lfs_pointer(p): pointers.append(rel)
        if size>=MAX_GIT_BLOB: oversized.append({"path":rel,"bytes":size})
        h.update(rel.encode()+b"\0"); h.update(digest(p).encode()+b"\n")
    return {"exists":True,"files":len(files),"bytes":total,"tree_sha256":h.hexdigest(),"pointers":pointers,"oversized":oversized,"valid":bool(files) and not pointers and not oversized}
def safe_name(name):
    n=name.replace("\\","/"); q=PurePosixPath(n)
    if q.is_absolute() or ".." in q.parts or re.match(r"^[A-Za-z]:",n): return None
    return q
def validate_info(info):
    q=safe_name(info.filename)
    if q is None: return False
    mode=(info.external_attr>>16)&0o170000
    return mode not in {stat.S_IFLNK,stat.S_IFCHR,stat.S_IFBLK,stat.S_IFIFO,stat.S_IFSOCK}
def groups(src):
    out={}
    if not src.exists(): return out
    for z in src.rglob("*.zip"):
        rel=z.relative_to(src)
        if len(rel.parts)>2: continue
        m=re.match(r"^(.*?)(?:_([0-9]{4}))?\.zip$",z.name,re.I)
        if m: out.setdefault((z.parent,m.group(1)),[]).append(z)
    return out
def target_for(cfg,parent,slug): return parent if cfg["layout"]=="parent" else Path(cfg["dst"])/slug

def archive_inventory(parts,slug):
    raw=[]; errors=[]
    for z in sorted(parts,key=lambda p:p.name):
        try:
            with zipfile.ZipFile(z) as a:
                bad=a.testzip()
                if bad: errors.append(f"CRC_FAIL:{z}:{bad}"); continue
                names=set()
                for info in a.infolist():
                    if info.is_dir(): continue
                    if not validate_info(info): errors.append(f"UNSAFE_ZIP:{z}:{info.filename}"); continue
                    q=safe_name(info.filename); key=str(q)
                    if key in names: errors.append(f"ZIP_DUPLICATE_PATH:{z}:{key}"); continue
                    names.add(key); pointer=None
                    if info.file_size<=1024:
                        with a.open(info) as f: pointer=parse_lfs_pointer_bytes(f.read(1024))
                    raw.append({"path":q,"pointer":pointer,"zip":str(z)})
        except (zipfile.BadZipFile,OSError) as e: errors.append(f"CRC_FAIL:{z}:{e}")
    paths=[r["path"] for r in raw]; strip=bool(paths) and all(len(q.parts)>1 and norm(q.parts[0])==norm(slug) for q in paths)
    ordinary=[]; pointers=[]; seen={}
    for row in raw:
        q=row["path"]; rel=PurePosixPath(*q.parts[1:]) if strip else q; key=rel.as_posix()
        sig=("pointer",json.dumps(row["pointer"],sort_keys=True)) if row["pointer"] else ("ordinary",None)
        if key in seen and seen[key]!=sig: errors.append(f"ZIP_DUPLICATE_PATH:CROSS_PART:{key}"); continue
        seen[key]=sig
        if row["pointer"]: pointers.append({**row["pointer"],"path":key,"zip":row["zip"]})
        else: ordinary.append(key)
    return {"ordinary":sorted(set(ordinary)),"pointers":pointers,"errors":errors}

def split_manifest_state(target,rel,sha256,nbytes):
    d=target/(rel+".parts"); m=d/"SPLIT_MANIFEST.json"
    if not m.is_file(): return {"valid":False,"reason":"manifest_missing"}
    try: doc=json.loads(m.read_text())
    except Exception as e: return {"valid":False,"reason":f"manifest_json:{e}"}
    if doc.get("source_sha256")!=sha256 or int(doc.get("source_bytes",-1))!=int(nbytes): return {"valid":False,"reason":"manifest_source_identity_mismatch"}
    parts=doc.get("parts")
    if not isinstance(parts,list) or not parts: return {"valid":False,"reason":"manifest_parts_missing"}
    h=hashlib.sha256(); total=0
    for item in parts:
        p=d/item.get("name","")
        if not p.is_file(): return {"valid":False,"reason":f"part_missing:{item.get('name')}"}
        ph=hashlib.sha256(); size=0
        with p.open("rb") as f:
            for b in iter(lambda:f.read(1024*1024),b""): ph.update(b); h.update(b); size+=len(b); total+=len(b)
        if item.get("sha256")!=ph.hexdigest() or int(item.get("bytes",-1))!=size: return {"valid":False,"reason":f"part_identity_mismatch:{item.get('name')}"}
    if total!=int(nbytes) or h.hexdigest()!=sha256: return {"valid":False,"reason":"joined_identity_mismatch"}
    return {"valid":True,"parts":len(parts),"bytes":total,"sha256":sha256}
def recovered_pointer_state(target,rec):
    rel=rec["path"]; sh=rec.get("sha256"); nb=rec.get("bytes")
    if rec.get("malformed") or not sh or nb is None: return {"valid":False,"path":rel,"reason":"malformed_source_pointer"}
    p=target/PurePosixPath(rel)
    if p.is_file() and not is_lfs_pointer(p):
        if p.stat().st_size==nb and digest(p)==sh: return {"valid":True,"path":rel,"mode":"exact_file","bytes":nb,"sha256":sh}
        return {"valid":False,"path":rel,"reason":"exact_file_identity_mismatch"}
    s=split_manifest_state(target,rel,sh,nb)
    return {"path":rel,"mode":"verified_split",**s}
def completeness_state(target,parts,slug):
    base=tree_state(target); inv=archive_inventory(parts,slug)
    missing=[r for r in inv["ordinary"] if not (target/PurePosixPath(r)).is_file()]
    required=[recovered_pointer_state(target,r) for r in inv["pointers"]] if slug in DATA_REQUIRED_SLUGS else []
    missing_ptr=[r for r in required if not r.get("valid")]
    excluded=[] if slug in DATA_REQUIRED_SLUGS else inv["pointers"]
    complete=base["valid"] and not inv["errors"] and not missing and not missing_ptr and bool(inv["ordinary"] or required)
    return {**base,"expected_ordinary_files":len(inv["ordinary"]),"missing_required":missing,"required_pointer_files":required,"missing_required_pointer_files":missing_ptr,"excluded_lfs_source_members":excluded,"source_errors":inv["errors"],"complete":complete}

def prior_blocked():
    out={}; base=Path("forensics/extraction")
    if not base.exists(): return out
    for p in sorted(base.glob("repair-*.json")):
        try: d=json.loads(p.read_text())
        except Exception: continue
        for f in d.get("failures",[]):
            err=str(f.get("error","")); code=err.split(":",1)[0]
            if code in NONRETRYABLE and f.get("slug"): out[f["slug"]]={"code":code,"detail":err,"evidence":str(p)}
    return out
def hard_blocked(slug,info):
    if not info: return False
    return not (info.get("code")=="SOURCE_LFS_POINTER_GAP" and slug not in DATA_REQUIRED_SLUGS)

def extract_members(parts,stage,slug):
    excluded=[]; hashes={}
    for z in sorted(parts,key=lambda p:p.name):
        hashes[str(z)]=digest(z)
        with zipfile.ZipFile(z) as a:
            bad=a.testzip()
            if bad: raise RuntimeError(f"CRC_FAIL:{z}:{bad}")
            names=set()
            for info in a.infolist():
                if not validate_info(info): raise RuntimeError(f"UNSAFE_ZIP:{z}:{info.filename}")
                q=safe_name(info.filename); key=str(q)
                if key in names: raise RuntimeError(f"ZIP_DUPLICATE_PATH:{z}:{key}")
                names.add(key)
                if info.is_dir(): (stage/q).mkdir(parents=True,exist_ok=True); continue
                dst=stage/q; dst.parent.mkdir(parents=True,exist_ok=True)
                with tempfile.NamedTemporaryFile(dir=dst.parent,delete=False) as tf:
                    tmp=Path(tf.name)
                    with a.open(info) as f: shutil.copyfileobj(f,tf,1024*1024)
                if is_lfs_pointer(tmp):
                    meta=parse_lfs_pointer_bytes(tmp.read_bytes()); tmp.unlink(missing_ok=True)
                    if slug in DATA_REQUIRED_SLUGS: raise RuntimeError(f"SOURCE_LFS_POINTER_GAP:{key}")
                    excluded.append({"path":key,**(meta or {})}); continue
                if tmp.stat().st_size>=MAX_GIT_BLOB:
                    size=tmp.stat().st_size; tmp.unlink(missing_ok=True); raise RuntimeError(f"GIT_BLOB_LIMIT_GAP:{key}:{size}")
                if dst.exists():
                    if digest(dst)!=digest(tmp): tmp.unlink(missing_ok=True); raise RuntimeError(f"COLLISION_BLOCKED:{key}")
                    tmp.unlink(missing_ok=True)
                else: os.replace(tmp,dst)
    return hashes,excluded
def copy_no_overwrite(src,dst):
    collisions=[]; copied=0
    for p in sorted(src.rglob("*")):
        if not p.is_file(): continue
        rel=p.relative_to(src); q=dst/rel; q.parent.mkdir(parents=True,exist_ok=True)
        if q.exists():
            if digest(p)!=digest(q): collisions.append(str(q))
        else: shutil.copy2(p,q); copied+=1
    if collisions: raise RuntimeError("COLLISION_BLOCKED:"+";".join(collisions[:20]))
    return copied
def extract_one(cfg,parent,slug,parts):
    target=target_for(cfg,parent,slug); existing=completeness_state(target,parts,slug)
    mirror_path=Path(cfg["mirror"])/slug if cfg.get("mirror") else None
    mirror_state=completeness_state(mirror_path,parts,slug) if mirror_path else {"complete":True}
    if existing["complete"] and mirror_state["complete"]: return {"slug":slug,"target":str(target),"status":"VERIFIED_EXISTING","files":existing["files"],"bytes":existing["bytes"],"tree_sha256":existing["tree_sha256"],"excluded_lfs_source_members":existing["excluded_lfs_source_members"]}
    if existing["pointers"]: raise RuntimeError("SOURCE_LFS_POINTER_GAP:existing:"+",".join(existing["pointers"][:20]))
    if existing["oversized"]: raise RuntimeError("GIT_BLOB_LIMIT_GAP:existing:"+json.dumps(existing["oversized"][:10]))
    with tempfile.TemporaryDirectory(prefix="extract-guardian-v4-") as tmp:
        stage=Path(tmp)/"stage"; stage.mkdir(); hashes,excluded=extract_members(parts,stage,slug)
        kids=list(stage.iterdir()); payload=stage
        if len(kids)==1 and kids[0].is_dir() and norm(kids[0].name)==norm(slug): payload=kids[0]
        st=tree_state(payload)
        if not st["files"]: raise RuntimeError("EMPTY_EXTRACTION")
        if st["pointers"]: raise RuntimeError("SOURCE_LFS_POINTER_GAP:"+",".join(st["pointers"][:20]))
        if st["oversized"]: raise RuntimeError("GIT_BLOB_LIMIT_GAP:"+json.dumps(st["oversized"][:10]))
        copied=copy_no_overwrite(payload,target); mirrors=[]
        if mirror_path: mirrors.append({"path":str(mirror_path),"copied":copy_no_overwrite(payload,mirror_path)})
        final=completeness_state(target,parts,slug)
        if final["source_errors"]: raise RuntimeError(final["source_errors"][0])
        if final["missing_required"]: raise RuntimeError("MISSING_REQUIRED_SOURCE_FILES:"+",".join(final["missing_required"][:20]))
        if final["missing_required_pointer_files"]: raise RuntimeError("SOURCE_LFS_POINTER_GAP:"+",".join(x["path"] for x in final["missing_required_pointer_files"][:20]))
        if not final["complete"]: raise RuntimeError("DESTINATION_VALIDATION_GAP")
        return {"slug":slug,"target":str(target),"status":"EXTRACTED_VERIFIED_CODE_SCOPE" if excluded else "EXTRACTED_VERIFIED","parts":len(parts),"part_sha256":hashes,"copied":copied,"mirrors":mirrors,"files":final["files"],"bytes":final["bytes"],"tree_sha256":final["tree_sha256"],"excluded_lfs_source_members":final["excluded_lfs_source_members"]}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--limit",type=int,default=10); ap.add_argument("--audit-only",action="store_true"); a=ap.parse_args()
    blocked=prior_blocked(); observed=[]; candidates=[]
    for cfg in MAPS:
        for (parent,slug),parts in groups(Path(cfg["src"])).items():
            target=target_for(cfg,parent,slug); state=completeness_state(target,parts,slug)
            mirror_path=Path(cfg["mirror"])/slug if cfg.get("mirror") else None; mirror_ok=not mirror_path or completeness_state(mirror_path,parts,slug)["complete"]
            observed.append((cfg,parent,slug,parts,target))
            if (not state["complete"] or not mirror_ok) and not hard_blocked(slug,blocked.get(slug)): candidates.append((cfg,parent,slug,parts,target))
    results=[]; failures=[]; successes=0
    if not a.audit_only:
        for cfg,parent,slug,parts,target in candidates:
            if successes>=a.limit: break
            try:
                row=extract_one(cfg,parent,slug,parts); results.append(row)
                if row["status"]!="VERIFIED_EXISTING": successes+=1
            except Exception as e:
                err=str(e); code=err.split(":",1)[0]; failures.append({"slug":slug,"target":str(target),"error":err,"retryable":code not in NONRETRYABLE})
                if code in NONRETRYABLE: blocked[slug]={"code":code,"detail":err,"evidence":"current-run"}
    remaining=[]; retryable=[]; blocked_rows=[]; excluded=[]
    for cfg,parent,slug,parts,target in observed:
        state=completeness_state(target,parts,slug); mirror_path=Path(cfg["mirror"])/slug if cfg.get("mirror") else None; mirror_ok=not mirror_path or completeness_state(mirror_path,parts,slug)["complete"]
        if state["excluded_lfs_source_members"]: excluded.append({"slug":slug,"target":str(target),"count":len(state["excluded_lfs_source_members"]),"members":state["excluded_lfs_source_members"][:50],"classification":"EXCLUDED_SOURCE_LFS_NONDATA_MEMBER"})
        if not state["complete"] or not mirror_ok:
            row={"slug":slug,"target":str(target),"mirror":cfg.get("mirror"),"missing_required":state["missing_required"][:20],"missing_required_count":len(state["missing_required"]),"missing_required_pointer_files":state["missing_required_pointer_files"][:20],"source_errors":state["source_errors"][:5]}; remaining.append(row)
            b=blocked.get(slug)
            if hard_blocked(slug,b): blocked_rows.append({**row,**b})
            else: retryable.append(row)
    report={"schema":"yaiwes.extraction.guardian.v4","scope":"ordinary_git_code_tree_plus_exact_required_datasets","run_id":os.getenv("GITHUB_RUN_ID","local"),"archive_groups":len(observed),"processed":results,"failures":failures,"excluded_lfs_source_members":excluded,"remaining_gaps":remaining,"retryable_gaps":retryable,"blocked_gaps":blocked_rows,"counts":{"remaining":len(remaining),"retryable":len(retryable),"blocked":len(blocked_rows),"processed":len(results),"excluded_lfs_groups":len(excluded)},"verdict":"VERIFIED_CLOSED" if not remaining and not failures else "GAPS_PENDING"}
    out=Path("forensics/extraction")/f"repair-{os.getenv('GITHUB_RUN_ID','local')}.json"; out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n"); print(json.dumps(report,ensure_ascii=False)); return 0
if __name__=="__main__": sys.exit(main())
