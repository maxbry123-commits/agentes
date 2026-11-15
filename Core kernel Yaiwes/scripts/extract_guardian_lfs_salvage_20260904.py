#!/usr/bin/env python3
"""Salvage blocked extraction groups by excluding Git-LFS pointer placeholders only.

The real non-LFS payload is preserved. Every excluded pointer path is recorded as evidence.
"""
import argparse, json, os, shutil, tempfile, zipfile
from pathlib import Path
import extract_guardian_repair_20260903 as g


def extract_members_without_lfs(parts, stage):
    excluded=[]; hashes={}
    for z in sorted(parts, key=lambda p:p.name):
        hashes[str(z)] = g.digest(z)
        with zipfile.ZipFile(z) as a:
            bad=a.testzip()
            if bad:
                raise RuntimeError(f"CRC_FAIL:{z}:{bad}")
            names=set()
            for info in a.infolist():
                if not g.validate_info(info):
                    raise RuntimeError(f"UNSAFE_ZIP:{z}:{info.filename}")
                q=g.safe_name(info.filename)
                key=str(q)
                if key in names:
                    raise RuntimeError(f"ZIP_DUPLICATE_PATH:{z}:{key}")
                names.add(key)
                if info.is_dir():
                    (stage/q).mkdir(parents=True,exist_ok=True)
                    continue
                dst=stage/q; dst.parent.mkdir(parents=True,exist_ok=True)
                with tempfile.NamedTemporaryFile(dir=dst.parent,delete=False) as tf:
                    tmp=Path(tf.name)
                    with a.open(info) as src:
                        shutil.copyfileobj(src,tf,1024*1024)
                if g.is_lfs_pointer(tmp):
                    excluded.append(f"{z}:{key}")
                    tmp.unlink(missing_ok=True)
                    continue
                if tmp.stat().st_size >= g.MAX_GIT_BLOB:
                    size=tmp.stat().st_size; tmp.unlink(missing_ok=True)
                    raise RuntimeError(f"GIT_BLOB_LIMIT_GAP:{key}:{size}")
                if dst.exists():
                    if g.digest(dst)!=g.digest(tmp):
                        tmp.unlink(missing_ok=True)
                        raise RuntimeError(f"COLLISION_BLOCKED:{key}")
                    tmp.unlink(missing_ok=True)
                else:
                    os.replace(tmp,dst)
    return hashes,excluded


def salvage_one(cfg,parent,slug,parts):
    target=g.target_for(cfg,parent,slug)
    current=g.tree_state(target)
    if current['valid']:
        return {'slug':slug,'target':str(target),'status':'VERIFIED_EXISTING','files':current['files'],'bytes':current['bytes'],'tree_sha256':current['tree_sha256'],'excluded_lfs_pointer_paths':[]}
    with tempfile.TemporaryDirectory(prefix='extract-lfs-salvage-') as tmp:
        stage=Path(tmp)/'stage'; stage.mkdir()
        hashes,excluded=extract_members_without_lfs(parts,stage)
        kids=list(stage.iterdir()); payload=stage
        if len(kids)==1 and kids[0].is_dir() and g.norm(kids[0].name)==g.norm(slug):
            payload=kids[0]
        state=g.tree_state(payload)
        if not state['valid']:
            raise RuntimeError('SALVAGED_PAYLOAD_INVALID:'+json.dumps(state,ensure_ascii=False))
        copied=g.copy_no_overwrite(payload,target)
        final=g.tree_state(target)
        if not final['valid']:
            raise RuntimeError('DESTINATION_VALIDATION_GAP:'+json.dumps(final,ensure_ascii=False))
        return {'slug':slug,'target':str(target),'status':'LFS_POINTERS_EXCLUDED_PAYLOAD_VERIFIED','parts':len(parts),'part_sha256':hashes,'copied':copied,'files':final['files'],'bytes':final['bytes'],'tree_sha256':final['tree_sha256'],'excluded_lfs_pointer_count':len(excluded),'excluded_lfs_pointer_paths':excluded}


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--shard-index',type=int,required=True)
    ap.add_argument('--shard-count',type=int,required=True)
    a=ap.parse_args()
    if a.shard_count<1 or not (0<=a.shard_index<a.shard_count):
        raise SystemExit(2)
    blocked=g.prior_blocked(); candidates=[]
    for cfg in g.MAPS:
        for (parent,slug),parts in g.groups(Path(cfg['src'])).items():
            target=g.target_for(cfg,parent,slug)
            b=blocked.get(slug)
            if not g.tree_state(target)['valid'] and b and b.get('code')=='SOURCE_LFS_POINTER_GAP':
                candidates.append((str(target),cfg,parent,slug,parts))
    candidates.sort(key=lambda x:x[0])
    selected=[row for i,row in enumerate(candidates) if i%a.shard_count==a.shard_index]
    results=[]; failures=[]
    for _,cfg,parent,slug,parts in selected:
        try:
            results.append(salvage_one(cfg,parent,slug,parts))
        except Exception as e:
            failures.append({'slug':slug,'target':str(g.target_for(cfg,parent,slug)),'error':str(e)})
    report={'schema':'yaiwes.extraction.lfs-salvage.v1','run_id':os.getenv('GITHUB_RUN_ID','local'),'shard_index':a.shard_index,'shard_count':a.shard_count,'candidate_count_at_snapshot':len(candidates),'selected':[x[0] for x in selected],'processed':results,'failures':failures,'verdict':'SHARD_PASS' if not failures else 'SHARD_GAPS'}
    out=Path('forensics/extraction')/f"lfs-salvage-{os.getenv('GITHUB_RUN_ID','local')}.json"
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
    print(json.dumps(report,ensure_ascii=False))
    return 0 if not failures else 73

if __name__=='__main__':
    raise SystemExit(main())
