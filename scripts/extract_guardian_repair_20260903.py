#!/usr/bin/env python3
"""Fail-closed ZIP extraction repair. Preserves archives and existing documents."""
import argparse, hashlib, json, os, re, shutil, stat, sys, tempfile, zipfile
from pathlib import Path, PurePosixPath

MAPS = [{"src":"core kernel Yaiwes principal","dst":"core kernel Yaiwes principal","layout":"flat"},{"src":"Agente core kernel Yaiwes principal","dst":"Agente core kernel Yaiwes principal","layout":"flat"}]
IGNORE = {"RESEARCH_DOWNLOAD_MANIFEST.jsonl", "EXTRACTION_GUARDIAN_REPORT.json"}

def norm(s): return re.sub(r"[^a-z0-9]+", "", s.lower())
def digest(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda:f.read(1024*1024), b""): h.update(b)
    return h.hexdigest()
def tree_digest(root):
    h=hashlib.sha256(); count=0; total=0
    for p in sorted((x for x in root.rglob("*") if x.is_file()), key=lambda x:x.as_posix()):
        rel=p.relative_to(root).as_posix()
        if p.name in IGNORE or p.suffix.lower()==".zip": continue
        h.update(rel.encode()+b"\0"); h.update(digest(p).encode()+b"\n")
        count+=1; total+=p.stat().st_size
    return h.hexdigest(),count,total
def safe_member(info):
    q=PurePosixPath(info.filename)
    if q.is_absolute() or ".." in q.parts: return False
    mode=(info.external_attr >> 16) & 0o170000
    return mode not in {stat.S_IFLNK, stat.S_IFCHR, stat.S_IFBLK, stat.S_IFIFO, stat.S_IFSOCK}
def groups(src):
    out={}
    if not src.exists(): return out
    for z in src.rglob("*.zip"):
        # Only archive payloads at source root, or one level below for parent layout.
        rel=z.relative_to(src)
        if len(rel.parts)>2: continue
        m=re.match(r"^(.*?)(?:_([0-9]{4}))?\.zip$",z.name,re.I)
        if not m: continue
        slug=m.group(1); out.setdefault((z.parent,slug),[]).append(z)
    return out
def target_for(cfg,parent,slug):
    src=Path(cfg["src"]); dst=Path(cfg["dst"])
    return parent if cfg["layout"]=="parent" else dst/slug
def extracted(target):
    if not target.exists(): return False
    return any(p.is_file() and p.suffix.lower()!=".zip" and p.name not in IGNORE for p in target.rglob("*"))
def copy_no_overwrite(src,dst):
    collisions=[]; copied=0
    for p in sorted(src.rglob("*")):
        if not p.is_file(): continue
        rel=p.relative_to(src); q=dst/rel; q.parent.mkdir(parents=True,exist_ok=True)
        if q.exists():
            if digest(p)!=digest(q): collisions.append(str(q))
        else:
            shutil.copy2(p,q); copied+=1
    if collisions: raise RuntimeError("COLLISION_BLOCKED: "+"; ".join(collisions[:20]))
    return copied
def extract_one(cfg,parent,slug,parts):
    target=target_for(cfg,parent,slug)
    if extracted(target):
        td,n,b=tree_digest(target)
        return {"slug":slug,"target":str(target),"status":"VERIFIED_EXISTING","files":n,"bytes":b,"tree_sha256":td}
    with tempfile.TemporaryDirectory(prefix="extract-guardian-") as tmp:
        stage=Path(tmp)/"stage"; stage.mkdir()
        part_hashes={}
        for z in sorted(parts,key=lambda p:p.name):
            part_hashes[str(z)]=digest(z)
            with zipfile.ZipFile(z) as a:
                bad=a.testzip()
                if bad: raise RuntimeError(f"CRC_FAIL {z}: {bad}")
                if any(not safe_member(i) for i in a.infolist()): raise RuntimeError(f"UNSAFE_ZIP {z}")
                a.extractall(stage)
        kids=[p for p in stage.iterdir()]
        payload=stage
        if len(kids)==1 and kids[0].is_dir() and norm(kids[0].name)==norm(slug): payload=kids[0]
        if not any(p.is_file() for p in payload.rglob("*")): raise RuntimeError(f"EMPTY_EXTRACTION {slug}")
        copied=copy_no_overwrite(payload,target)
        mirrors=[]
        if cfg.get("mirror"):
            m=Path(cfg["mirror"])/slug
            mirrors.append({"path":str(m),"copied":copy_no_overwrite(payload,m)})
        td,n,b=tree_digest(target)
        if n==0: raise RuntimeError(f"NO_REAL_FILES {slug}")
        return {"slug":slug,"target":str(target),"status":"EXTRACTED_VERIFIED","parts":len(parts),"part_sha256":part_hashes,"copied":copied,"mirrors":mirrors,"files":n,"bytes":b,"tree_sha256":td}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--limit",type=int,default=3); ap.add_argument("--audit-only",action="store_true"); a=ap.parse_args()
    pending=[]; observed=[]
    for cfg in MAPS:
        for (parent,slug),parts in groups(Path(cfg["src"])).items():
            t=target_for(cfg,parent,slug)
            row=(cfg,parent,slug,parts,t)
            observed.append(row)
            mirror_ok=not cfg.get("mirror") or extracted(Path(cfg["mirror"])/slug)
            if not extracted(t) or not mirror_ok: pending.append(row)
    results=[]; failures=[]
    if not a.audit_only:
        for cfg,parent,slug,parts,t in pending[:a.limit]:
            try: results.append(extract_one(cfg,parent,slug,parts))
            except Exception as e: failures.append({"slug":slug,"error":str(e)})
    remaining=[]
    for cfg,parent,slug,parts,t in observed:
        mirror_ok=not cfg.get("mirror") or extracted(Path(cfg["mirror"])/slug)
        if not extracted(t) or not mirror_ok: remaining.append({"slug":slug,"target":str(t),"mirror":cfg.get("mirror")})
    report={"schema":"yaiwes.extraction.guardian.v1","run_id":os.getenv("GITHUB_RUN_ID","local"),
      "archive_groups":len(observed),"pending_before":len(pending),"processed":results,
      "failures":failures,"remaining_gaps":remaining,
      "verdict":"VERIFIED_CLOSED" if not remaining and not failures else "GAPS_PENDING"}
    out=Path("forensics/extraction")/f"repair-{os.getenv('GITHUB_RUN_ID','local')}.json"
    out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n")
    print(json.dumps(report,ensure_ascii=False))
    if failures: return 2
    return 0
if __name__=="__main__": sys.exit(main())
