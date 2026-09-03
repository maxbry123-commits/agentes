#!/usr/bin/env python3
"""Fail-closed deterministic ZIP extraction guardian. Git LFS is prohibited."""
import argparse, hashlib, json, os, re, shutil, stat, sys, tempfile, zipfile
from pathlib import Path, PurePosixPath

MAPS = [{"src":"core kernel Yaiwes principal","dst":"core kernel Yaiwes principal","layout":"flat"},{"src":"Agente core kernel Yaiwes principal","dst":"Agente core kernel Yaiwes principal","layout":"flat"}]
IGNORE = {"RESEARCH_DOWNLOAD_MANIFEST.jsonl", "EXTRACTION_GUARDIAN_REPORT.json"}
LFS_POINTER = b"version https://git-lfs.github.com/spec/v1\n"
MAX_GIT_BLOB = 100 * 1024 * 1024
NONRETRYABLE = {
    "SOURCE_LFS_POINTER_GAP", "GIT_BLOB_LIMIT_GAP", "COLLISION_BLOCKED",
    "UNSAFE_ZIP", "ZIP_DUPLICATE_PATH", "CRC_FAIL"
}

def norm(s): return re.sub(r"[^a-z0-9]+", "", s.lower())

def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda: f.read(1024*1024), b""):
            h.update(b)
    return h.hexdigest()

def is_lfs_pointer(path):
    try:
        if not path.is_file() or path.stat().st_size > 1024:
            return False
        with path.open("rb") as f:
            return f.read(1024).startswith(LFS_POINTER)
    except OSError:
        return False

def tree_state(root):
    files = []
    pointers = []
    oversized = []
    if not root.exists():
        return {"exists":False,"files":0,"bytes":0,"tree_sha256":None,"pointers":[],"oversized":[],"valid":False}
    h = hashlib.sha256(); total = 0
    for p in sorted((x for x in root.rglob("*") if x.is_file()), key=lambda x:x.as_posix()):
        if p.name in IGNORE or p.suffix.lower() == ".zip":
            continue
        rel = p.relative_to(root).as_posix()
        size = p.stat().st_size
        files.append(p); total += size
        if is_lfs_pointer(p):
            pointers.append(rel)
        if size >= MAX_GIT_BLOB:
            oversized.append({"path":rel,"bytes":size})
        h.update(rel.encode()+b"\0"); h.update(digest(p).encode()+b"\n")
    return {
        "exists":True, "files":len(files), "bytes":total,
        "tree_sha256":h.hexdigest(), "pointers":pointers, "oversized":oversized,
        "valid":bool(files) and not pointers and not oversized
    }

def safe_name(name):
    n = name.replace("\\", "/")
    q = PurePosixPath(n)
    if q.is_absolute() or ".." in q.parts or re.match(r"^[A-Za-z]:", n):
        return None
    return q

def validate_info(info):
    q = safe_name(info.filename)
    if q is None:
        return False
    mode = (info.external_attr >> 16) & 0o170000
    return mode not in {stat.S_IFLNK, stat.S_IFCHR, stat.S_IFBLK, stat.S_IFIFO, stat.S_IFSOCK}

def groups(src):
    out = {}
    if not src.exists():
        return out
    for z in src.rglob("*.zip"):
        rel = z.relative_to(src)
        if len(rel.parts) > 2:
            continue
        m = re.match(r"^(.*?)(?:_([0-9]{4}))?\.zip$", z.name, re.I)
        if not m:
            continue
        slug = m.group(1)
        out.setdefault((z.parent, slug), []).append(z)
    return out

def target_for(cfg, parent, slug):
    return parent if cfg["layout"] == "parent" else Path(cfg["dst"]) / slug

def prior_blocked():
    blocked = {}
    base = Path("forensics/extraction")
    if not base.exists():
        return blocked
    for p in sorted(base.glob("repair-*.json")):
        try:
            d = json.loads(p.read_text())
        except Exception:
            continue
        for f in d.get("failures", []):
            err = str(f.get("error",""))
            code = err.split(":",1)[0]
            if code in NONRETRYABLE and f.get("slug"):
                blocked[f["slug"]] = {"code":code,"detail":err,"evidence":str(p)}
    return blocked

def extract_members(parts, stage):
    seen = {}
    part_hashes = {}
    for z in sorted(parts, key=lambda p:p.name):
        part_hashes[str(z)] = digest(z)
        with zipfile.ZipFile(z) as a:
            bad = a.testzip()
            if bad:
                raise RuntimeError(f"CRC_FAIL:{z}:{bad}")
            names = set()
            for info in a.infolist():
                if not validate_info(info):
                    raise RuntimeError(f"UNSAFE_ZIP:{z}:{info.filename}")
                q = safe_name(info.filename)
                key = str(q)
                if key in names:
                    raise RuntimeError(f"ZIP_DUPLICATE_PATH:{z}:{key}")
                names.add(key)
                if info.is_dir():
                    (stage / q).mkdir(parents=True, exist_ok=True)
                    continue
                dst = stage / q
                dst.parent.mkdir(parents=True, exist_ok=True)
                with tempfile.NamedTemporaryFile(dir=dst.parent, delete=False) as tf:
                    tmp = Path(tf.name)
                    with a.open(info) as src:
                        shutil.copyfileobj(src, tf, 1024*1024)
                if dst.exists():
                    if digest(dst) != digest(tmp):
                        tmp.unlink(missing_ok=True)
                        raise RuntimeError(f"COLLISION_BLOCKED:{key}")
                    tmp.unlink(missing_ok=True)
                else:
                    os.replace(tmp, dst)
                seen[key] = True
    return part_hashes

def copy_no_overwrite(src, dst):
    collisions=[]; copied=0
    for p in sorted(src.rglob("*")):
        if not p.is_file():
            continue
        rel=p.relative_to(src); q=dst/rel
        q.parent.mkdir(parents=True,exist_ok=True)
        if q.exists():
            if digest(p) != digest(q):
                collisions.append(str(q))
        else:
            shutil.copy2(p,q); copied += 1
    if collisions:
        raise RuntimeError("COLLISION_BLOCKED:"+";".join(collisions[:20]))
    return copied

def extract_one(cfg, parent, slug, parts):
    target = target_for(cfg,parent,slug)
    existing = tree_state(target)
    mirror_path = Path(cfg["mirror"])/slug if cfg.get("mirror") else None
    mirror_state = tree_state(mirror_path) if mirror_path else {"valid":True}
    if existing["valid"] and mirror_state["valid"]:
        return {"slug":slug,"target":str(target),"status":"VERIFIED_EXISTING",
                "files":existing["files"],"bytes":existing["bytes"],"tree_sha256":existing["tree_sha256"]}
    if existing["pointers"]:
        raise RuntimeError("SOURCE_LFS_POINTER_GAP:existing:"+",".join(existing["pointers"][:20]))
    if existing["oversized"]:
        raise RuntimeError("GIT_BLOB_LIMIT_GAP:existing:"+json.dumps(existing["oversized"][:10]))

    with tempfile.TemporaryDirectory(prefix="extract-guardian-") as tmp:
        stage=Path(tmp)/"stage"; stage.mkdir()
        part_hashes=extract_members(parts,stage)
        kids=list(stage.iterdir()); payload=stage
        if len(kids)==1 and kids[0].is_dir() and norm(kids[0].name)==norm(slug):
            payload=kids[0]
        state=tree_state(payload)
        if not state["files"]:
            raise RuntimeError("EMPTY_EXTRACTION")
        if state["pointers"]:
            raise RuntimeError("SOURCE_LFS_POINTER_GAP:"+",".join(state["pointers"][:20]))
        if state["oversized"]:
            raise RuntimeError("GIT_BLOB_LIMIT_GAP:"+json.dumps(state["oversized"][:10]))
        copied=copy_no_overwrite(payload,target)
        mirrors=[]
        if mirror_path:
            mirrors.append({"path":str(mirror_path),"copied":copy_no_overwrite(payload,mirror_path)})
        final=tree_state(target)
        if not final["valid"]:
            raise RuntimeError("DESTINATION_VALIDATION_GAP")
        return {"slug":slug,"target":str(target),"status":"EXTRACTED_VERIFIED",
                "parts":len(parts),"part_sha256":part_hashes,"copied":copied,"mirrors":mirrors,
                "files":final["files"],"bytes":final["bytes"],"tree_sha256":final["tree_sha256"]}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--limit",type=int,default=10)
    ap.add_argument("--audit-only",action="store_true")
    a=ap.parse_args()

    blocked=prior_blocked()
    observed=[]; candidates=[]; remaining=[]
    for cfg in MAPS:
        for (parent,slug),parts in groups(Path(cfg["src"])).items():
            target=target_for(cfg,parent,slug)
            state=tree_state(target)
            mirror_path=Path(cfg["mirror"])/slug if cfg.get("mirror") else None
            mirror_ok=not mirror_path or tree_state(mirror_path)["valid"]
            observed.append((cfg,parent,slug,parts,target))
            if not state["valid"] or not mirror_ok:
                remaining.append({"slug":slug,"target":str(target),"mirror":cfg.get("mirror")})
                if slug not in blocked:
                    candidates.append((cfg,parent,slug,parts,target))

    results=[]; failures=[]; successes=0
    if not a.audit_only:
        for cfg,parent,slug,parts,target in candidates:
            if successes >= a.limit:
                break
            try:
                row=extract_one(cfg,parent,slug,parts)
                results.append(row)
                if row["status"] != "VERIFIED_EXISTING":
                    successes += 1
            except Exception as e:
                err=str(e)
                code=err.split(":",1)[0]
                failures.append({"slug":slug,"target":str(target),"error":err,"retryable":code not in NONRETRYABLE})
                if code in NONRETRYABLE:
                    blocked[slug]={"code":code,"detail":err,"evidence":"current-run"}

    remaining=[]; retryable=[]; blocked_rows=[]
    for cfg,parent,slug,parts,target in observed:
        state=tree_state(target)
        mirror_path=Path(cfg["mirror"])/slug if cfg.get("mirror") else None
        mirror_ok=not mirror_path or tree_state(mirror_path)["valid"]
        if not state["valid"] or not mirror_ok:
            row={"slug":slug,"target":str(target),"mirror":cfg.get("mirror")}
            remaining.append(row)
            if slug in blocked:
                blocked_rows.append({**row,**blocked[slug]})
            else:
                retryable.append(row)

    report={
      "schema":"yaiwes.extraction.guardian.v2",
      "run_id":os.getenv("GITHUB_RUN_ID","local"),
      "archive_groups":len(observed),
      "processed":results,
      "failures":failures,
      "remaining_gaps":remaining,
      "retryable_gaps":retryable,
      "blocked_gaps":blocked_rows,
      "counts":{
        "remaining":len(remaining),
        "retryable":len(retryable),
        "blocked":len(blocked_rows),
        "processed":len(results)
      },
      "verdict":"VERIFIED_CLOSED" if not remaining and not failures else "GAPS_PENDING"
    }
    out=Path("forensics/extraction")/f"repair-{os.getenv('GITHUB_RUN_ID','local')}.json"
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n")
    print(json.dumps(report,ensure_ascii=False))
    return 0

if __name__=="__main__":
    sys.exit(main())
