#!/usr/bin/env python3
"""Parallel deterministic shard wrapper for the NO-LFS extraction guardian."""
import argparse, json, os, sys
from pathlib import Path
import extract_guardian_repair_20260903 as g

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--offset',type=int,required=True)
    ap.add_argument('--limit',type=int,default=10)
    a=ap.parse_args()
    blocked=g.prior_blocked()
    observed=[]; candidates=[]
    for cfg in g.MAPS:
        for (parent,slug),parts in g.groups(Path(cfg['src'])).items():
            target=g.target_for(cfg,parent,slug)
            state=g.tree_state(target)
            mirror_path=Path(cfg['mirror'])/slug if cfg.get('mirror') else None
            mirror_ok=not mirror_path or g.tree_state(mirror_path)['valid']
            observed.append((cfg,parent,slug,parts,target))
            if (not state['valid'] or not mirror_ok) and slug not in blocked:
                candidates.append((cfg,parent,slug,parts,target))
    selected=candidates[a.offset:a.offset+a.limit]
    results=[]; failures=[]
    for cfg,parent,slug,parts,target in selected:
        try:
            results.append(g.extract_one(cfg,parent,slug,parts))
        except Exception as e:
            err=str(e); code=err.split(':',1)[0]
            failures.append({'slug':slug,'target':str(target),'error':err,'retryable':code not in g.NONRETRYABLE})
            if code in g.NONRETRYABLE:
                blocked[slug]={'code':code,'detail':err,'evidence':'current-run'}
    remaining=[]; retryable=[]; blocked_rows=[]
    for cfg,parent,slug,parts,target in observed:
        state=g.tree_state(target)
        mirror_path=Path(cfg['mirror'])/slug if cfg.get('mirror') else None
        mirror_ok=not mirror_path or g.tree_state(mirror_path)['valid']
        if not state['valid'] or not mirror_ok:
            row={'slug':slug,'target':str(target),'mirror':cfg.get('mirror')}
            remaining.append(row)
            if slug in blocked: blocked_rows.append({**row,**blocked[slug]})
            else: retryable.append(row)
    report={
      'schema':'yaiwes.extraction.guardian.shard.v1','run_id':os.getenv('GITHUB_RUN_ID','local'),
      'offset':a.offset,'limit':a.limit,'candidate_count_at_snapshot':len(candidates),
      'selected':[x[2] for x in selected],'processed':results,'failures':failures,
      'remaining_gaps':remaining,'retryable_gaps':retryable,'blocked_gaps':blocked_rows,
      'counts':{'remaining':len(remaining),'retryable':len(retryable),'blocked':len(blocked_rows),'processed':len(results)},
      'verdict':'SHARD_PASS' if not failures else 'SHARD_GAPS'
    }
    out=Path('forensics/extraction')/f"repair-{os.getenv('GITHUB_RUN_ID','local')}.json"
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
    print(json.dumps(report,ensure_ascii=False))
    return 0

if __name__=='__main__': sys.exit(main())
