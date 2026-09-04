#!/usr/bin/env python3
"""Stable hash-sharded NO-LFS salvage for non-dataset components only."""
import argparse, hashlib, json, os, sys
from pathlib import Path
import extract_guardian_repair_20260903 as g
import extract_guardian_lfs_salvage_20260904 as s

def bucket(slug,count):
    return int(hashlib.sha256(slug.encode('utf-8')).hexdigest()[:16],16)%count

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--shard-index',type=int,required=True); ap.add_argument('--shard-count',type=int,required=True); a=ap.parse_args()
    if a.shard_count<1 or not 0<=a.shard_index<a.shard_count: return 2
    blocked=g.prior_blocked(); selected=[]
    for cfg in g.MAPS:
        for (parent,slug),parts in g.groups(Path(cfg['src'])).items():
            b=blocked.get(slug); target=g.target_for(cfg,parent,slug)
            if slug in g.DATA_REQUIRED_SLUGS: continue
            if not g.tree_state(target)['valid'] and b and b.get('code')=='SOURCE_LFS_POINTER_GAP' and bucket(slug,a.shard_count)==a.shard_index:
                selected.append((str(target),cfg,parent,slug,parts))
    selected.sort(key=lambda x:x[0]); results=[]; failures=[]
    for _,cfg,parent,slug,parts in selected:
        try: results.append(s.salvage_one(cfg,parent,slug,parts))
        except Exception as e: failures.append({'slug':slug,'target':str(g.target_for(cfg,parent,slug)),'error':str(e)})
    report={'schema':'yaiwes.extraction.lfs-hash-shard.v1','run_id':os.getenv('GITHUB_RUN_ID','local'),'shard_index':a.shard_index,'shard_count':a.shard_count,'selected':[x[3] for x in selected],'processed':results,'failures':failures,'verdict':'SHARD_PASS' if not failures else 'SHARD_GAPS'}
    out=Path('forensics/extraction')/f"lfs-hash-shard-{os.getenv('GITHUB_RUN_ID','local')}.json"; out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n'); print(json.dumps(report,ensure_ascii=False)); return 0 if not failures else 73
if __name__=='__main__': sys.exit(main())
