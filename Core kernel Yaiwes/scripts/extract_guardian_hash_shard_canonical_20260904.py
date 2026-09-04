#!/usr/bin/env python3
"""Stable hash-sharded retryable extraction worker for the canonical Yaiwes core."""
import argparse, hashlib, json, os, sys
from pathlib import Path
import extract_guardian_repair_20260903 as g

def bucket(slug,count):
    return int(hashlib.sha256(slug.encode('utf-8')).hexdigest()[:16],16)%count

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--shard-index',type=int,required=True); ap.add_argument('--shard-count',type=int,required=True); ap.add_argument('--limit',type=int,default=40); a=ap.parse_args()
    if a.shard_count<1 or not 0<=a.shard_index<a.shard_count: return 2
    blocked=g.prior_blocked(); observed=[]; candidates=[]
    for cfg in g.MAPS:
        for (parent,slug),parts in g.groups(Path(cfg['src'])).items():
            target=g.target_for(cfg,parent,slug); state=g.completeness_state(target,parts,slug)
            mirror=Path(cfg['mirror'])/slug if cfg.get('mirror') else None; mirror_ok=not mirror or g.completeness_state(mirror,parts,slug)['complete']
            observed.append((cfg,parent,slug,parts,target))
            if (not state['complete'] or not mirror_ok) and not g.hard_blocked(slug,blocked.get(slug)) and bucket(slug,a.shard_count)==a.shard_index:
                candidates.append((cfg,parent,slug,parts,target))
    candidates.sort(key=lambda x:(x[2].lower(),str(x[4])))
    results=[]; failures=[]
    for cfg,parent,slug,parts,target in candidates[:a.limit]:
        try: results.append(g.extract_one(cfg,parent,slug,parts))
        except Exception as e:
            err=str(e); code=err.split(':',1)[0]; failures.append({'slug':slug,'target':str(target),'error':err,'retryable':code not in g.NONRETRYABLE})
    report={'schema':'yaiwes.extraction.hash-shard.v1','run_id':os.getenv('GITHUB_RUN_ID','local'),'shard_index':a.shard_index,'shard_count':a.shard_count,'candidate_count':len(candidates),'selected':[x[2] for x in candidates[:a.limit]],'processed':results,'failures':failures,'verdict':'SHARD_PASS' if not failures else 'SHARD_GAPS'}
    out=Path('forensics/extraction')/f"hash-shard-{os.getenv('GITHUB_RUN_ID','local')}.json"; out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n'); print(json.dumps(report,ensure_ascii=False)); return 0 if not failures else 73
if __name__=='__main__': sys.exit(main())
