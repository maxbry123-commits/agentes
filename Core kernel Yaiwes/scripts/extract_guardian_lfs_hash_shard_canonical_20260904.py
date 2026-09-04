#!/usr/bin/env python3
"""Process only selected non-dataset LFS groups and prove ordinary-code salvage."""
import argparse, json, os, sys, tempfile
from pathlib import Path
import extract_guardian_repair_20260903 as g
import extract_guardian_lfs_salvage_20260904 as s

def salvage_force(cfg,parent,slug,parts):
    target=g.target_for(cfg,parent,slug)
    with tempfile.TemporaryDirectory(prefix='canonical-lfs-') as td:
        stage=Path(td)/'stage'; stage.mkdir(); hashes,excluded=s.extract_members_without_lfs(parts,stage)
        kids=list(stage.iterdir()); payload=kids[0] if len(kids)==1 and kids[0].is_dir() and g.norm(kids[0].name)==g.norm(slug) else stage
        st=g.tree_state(payload)
        if not st['valid']: raise RuntimeError('SALVAGED_PAYLOAD_INVALID:'+json.dumps(st,ensure_ascii=False))
        copied=g.copy_no_overwrite(payload,target); final=g.tree_state(target)
        if not final['valid']: raise RuntimeError('DESTINATION_VALIDATION_GAP:'+json.dumps(final,ensure_ascii=False))
        if not excluded: raise RuntimeError('EXPECTED_LFS_POINTER_EVIDENCE_MISSING')
        return {'slug':slug,'target':str(target),'status':'LFS_POINTERS_EXCLUDED_PAYLOAD_VERIFIED','parts':len(parts),'part_sha256':hashes,'copied':copied,'files':final['files'],'bytes':final['bytes'],'tree_sha256':final['tree_sha256'],'excluded_lfs_pointer_count':len(excluded),'excluded_lfs_pointer_paths':excluded}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--shard-index',type=int,required=True); ap.add_argument('--shard-count',type=int,required=True); a=ap.parse_args(); observed=[]
    for cfg in g.MAPS:
        for (parent,slug),parts in g.groups(Path(cfg['src'])).items():
            if slug not in g.DATA_REQUIRED_SLUGS: observed.append((str(g.target_for(cfg,parent,slug)),cfg,parent,slug,parts))
    observed.sort(key=lambda x:(x[0].lower(),x[3].lower())); results=[]; failures=[]
    for _,cfg,parent,slug,parts in observed:
        try: results.append(salvage_force(cfg,parent,slug,parts))
        except Exception as e: failures.append({'slug':slug,'target':str(g.target_for(cfg,parent,slug)),'error':str(e),'retryable':False})
    report={'schema':'yaiwes.extraction.canonical-lfs-salvage.v2','run_id':os.getenv('GITHUB_RUN_ID','local'),'shard_index':a.shard_index,'shard_count':a.shard_count,'selected':[{'slug':x[3],'target':x[0]} for x in observed],'processed':results,'failures':failures,'verdict':'SHARD_PASS' if not failures else 'SHARD_GAPS'}
    out=Path('forensics/extraction')/f"canonical-lfs-{os.getenv('GITHUB_RUN_ID','local')}.json"; out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n'); print(json.dumps(report,ensure_ascii=False)); return 0
if __name__=='__main__': sys.exit(main())
