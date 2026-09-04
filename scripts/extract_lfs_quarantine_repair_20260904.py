#!/usr/bin/env python3
"""Install all non-LFS source bytes for known blocked archives; quarantine only non-code LFS placeholders.

The source ZIPs remain untouched. Pointer placeholders are never published as files and every exclusion
is recorded with its pointer metadata. Any code-like pointer fails closed.
"""
import argparse, json, os, re, shutil, tempfile
from pathlib import Path
import extract_guardian_repair_20260903 as g

ROOT_SLUGS = {
    "core": (Path("core kernel Yaiwes principal"), {
        "Microsoft-AutoGen","AG2","Prometheus-Evaluator-LM","TruLens","Cerbos","Microsoft-Agent-Framework"
    }),
    "agent": (Path("Agente core kernel Yaiwes principal"), {
        "HelpSteer2","BAML","autogen","TruLens","Cerbos","Microsoft-Agent-Framework","PRM800K"
    }),
}
IMAGE_FONT = {".png",".jpg",".jpeg",".gif",".webp",".svg",".ttf",".otf",".ico"}
DATA_EXT = {".json",".jsonl",".gz"}
DATA_HINTS = ("/data/","/train","/test","/validation","/preference","/disagreements","/math_splits/","/bfcl/")

def pointer_meta(path: Path):
    txt=path.read_text(errors="replace")[:2048]
    oid=None; size=None
    m=re.search(r"^oid sha256:([0-9a-f]{64})$",txt,re.M)
    if m: oid=m.group(1)
    m=re.search(r"^size (\d+)$",txt,re.M)
    if m: size=int(m.group(1))
    return {"oid_sha256":oid,"declared_size":size,"pointer_sha256":g.digest(path)}

def noncode_pointer(rel: str):
    low="/"+rel.lower().replace("\\","/")
    ext=Path(rel).suffix.lower()
    if ext in IMAGE_FONT: return True
    if ext in DATA_EXT and any(h in low for h in DATA_HINTS): return True
    if low.endswith(".lfs.baml") and "/tests/" in low: return True
    return False

def payload_root(stage: Path, slug: str):
    kids=list(stage.iterdir())
    if len(kids)==1 and kids[0].is_dir() and g.norm(kids[0].name)==g.norm(slug):
        return kids[0]
    return stage

def remove_existing_pointer_placeholders(target: Path):
    removed=[]
    if not target.exists(): return removed
    for p in sorted(x for x in target.rglob("*") if x.is_file() and g.is_lfs_pointer(x)):
        rel=p.relative_to(target).as_posix()
        if not noncode_pointer(rel):
            raise RuntimeError("LFS_POINTER_CODELIKE_BLOCKED:existing:"+rel)
        removed.append({"path":rel,**pointer_meta(p)})
        p.unlink()
    return removed

def repair_one(root: Path, slug: str, parts):
    target=root/slug
    with tempfile.TemporaryDirectory(prefix="lfs-quarantine-") as td:
        stage=Path(td)/"stage"; stage.mkdir()
        part_hashes=g.extract_members(parts,stage)
        payload=payload_root(stage,slug)
        exclusions=[]
        for p in sorted(x for x in payload.rglob("*") if x.is_file() and g.is_lfs_pointer(x)):
            rel=p.relative_to(payload).as_posix()
            if not noncode_pointer(rel):
                raise RuntimeError("LFS_POINTER_CODELIKE_BLOCKED:"+rel)
            exclusions.append({"path":rel,**pointer_meta(p),"classification":"NON_CODE_SOURCE_LFS_PLACEHOLDER"})
            p.unlink()
        if not exclusions:
            raise RuntimeError("EXPECTED_LFS_POINTERS_NOT_FOUND")
        state=g.tree_state(payload)
        if not state["files"]: raise RuntimeError("EMPTY_EXTRACTION")
        if state["pointers"]: raise RuntimeError("SOURCE_LFS_POINTER_GAP:"+",".join(state["pointers"][:20]))
        if state["oversized"]: raise RuntimeError("GIT_BLOB_LIMIT_GAP:"+json.dumps(state["oversized"][:10]))
        existing_removed=remove_existing_pointer_placeholders(target)
        copied=g.copy_no_overwrite(payload,target)
        evidence={
          "schema":"yaiwes.source-lfs-exclusions.v1","slug":slug,
          "policy":"source ZIP retained; only non-code Git-LFS pointer placeholders excluded from installed tree",
          "source_parts":[{"path":str(p),"sha256":part_hashes[str(p)]} for p in sorted(parts,key=lambda x:x.name)],
          "excluded":exclusions,"removed_existing_placeholders":existing_removed
        }
        (target/"SOURCE_LFS_EXCLUSIONS.json").write_text(json.dumps(evidence,indent=2,ensure_ascii=False)+"\n")
        final=g.tree_state(target)
        if not final["valid"]: raise RuntimeError("DESTINATION_VALIDATION_GAP:"+json.dumps(final))
        return {"slug":slug,"target":str(target),"status":"EXTRACTED_NO_LFS_VERIFIED","copied":copied,
                "excluded_count":len(exclusions),"files":final["files"],"bytes":final["bytes"],"tree_sha256":final["tree_sha256"]}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--root",choices=ROOT_SLUGS,required=True); a=ap.parse_args()
    root, wanted=ROOT_SLUGS[a.root]
    grouped={slug:parts for (parent,slug),parts in g.groups(root).items() if parent==root and slug in wanted}
    rows=[]; failures=[]
    for slug in sorted(wanted):
        target=root/slug
        if g.tree_state(target)["valid"]:
            rows.append({"slug":slug,"target":str(target),"status":"VERIFIED_EXISTING"}); continue
        parts=grouped.get(slug)
        if not parts:
            failures.append({"slug":slug,"error":"ARCHIVE_GROUP_MISSING"}); continue
        try: rows.append(repair_one(root,slug,parts))
        except Exception as e: failures.append({"slug":slug,"error":str(e)})
    remaining=[slug for slug in sorted(wanted) if not g.tree_state(root/slug)["valid"]]
    report={"schema":"yaiwes.extraction.lfs-quarantine-repair.v1","run_id":os.getenv("GITHUB_RUN_ID","local"),
            "root":str(root),"processed":rows,"failures":failures,"remaining":remaining,
            "counts":{"wanted":len(wanted),"valid":len(wanted)-len(remaining),"remaining":len(remaining),"failures":len(failures)},
            "verdict":"PASS" if not remaining and not failures else "GAPS"}
    out=Path("forensics/extraction")/f"lfs-repair-{a.root}-{os.getenv('GITHUB_RUN_ID','local')}.json"
    out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n")
    print(json.dumps(report,ensure_ascii=False))
    return 0 if report["verdict"]=="PASS" else 2

if __name__=="__main__": raise SystemExit(main())
