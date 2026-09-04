#!/usr/bin/env python3
"""Process only retry groups materialized by the canonical sparse workflow."""
import argparse, json, os, sys
from pathlib import Path
import extract_guardian_repair_20260903 as g

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--shard-index',type=int,required=True); ap.add_argument('--shard-count',type=int,required=True); a=ap.parse_args()
    observed=[]
    for cfg in g.MAPS:
        for (parent,slug),parts in g.groups(Path(cfg['src'])).items(): observed.append((str(g.target_for(cfg,parent,slug)),cfg,parent,slug,parts))
    observed.sort(key=lambda x:(x[0].lower(),x[3].lower())); results=[]; failures=[]
    for _,cfg,parent,slug,parts in observed:
        target=g.target_for(cfg,parent,slug)
        try: results.append(g.extract_one(cfg,parent,slug,parts))
        except Exception as e:
            err=str(e); code=err.split(':',1)[0]; failures.append({'slug':slug,'target':str(target),'error':err,'retryable':code not in g.NONRETRYABLE})
    report={'schema':'yaiwes.extraction.canonical-retry.v2','run_id':os.getenv('GITHUB_RUN_ID','local'),'shard_index':a.shard_index,'shard_count':a.shard_count,'selected':[{'slug':x[3],'target':x[0]} for x in observed],'processed':results,'failures':failures,'verdict':'SHARD_PASS' if not failures else 'SHARD_GAPS'}
    out=Path('forensics/extraction')/f"canonical-retry-{os.getenv('GITHUB_RUN_ID','local')}.json"; out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n'); print(json.dumps(report,ensure_ascii=False)); return 0
if __name__=='__main__': sys.exit(main())
