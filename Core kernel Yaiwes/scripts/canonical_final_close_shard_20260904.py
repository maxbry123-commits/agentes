#!/usr/bin/env python3
import argparse, hashlib, os, sys
import canonical_final_close_20260904 as c

def install_filter(index,count):
    original=c.unresolved
    def filtered():
        out=[]
        for r in original():
            raw=(r['target']+'\0'+r['slug']).encode()
            bucket=int(hashlib.sha256(raw).hexdigest()[:16],16)%count
            if bucket==index: out.append(r)
        return out
    c.unresolved=filtered

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--shard-index',type=int,default=0)
    ap.add_argument('--shard-count',type=int,default=1)
    ap.add_argument('--emit-sparse',action='store_true')
    ap.add_argument('--repair',action='store_true')
    ap.add_argument('--verify',action='store_true')
    a=ap.parse_args()
    if a.verify: return c.verify()
    if a.shard_count<1 or not 0<=a.shard_index<a.shard_count: return 2
    install_filter(a.shard_index,a.shard_count)
    if a.emit_sparse: c.emit_sparse(); return 0
    if a.repair:
        os.environ['GITHUB_RUN_ID']=os.environ.get('GITHUB_RUN_ID','local')+f'-s{a.shard_index}'
        return c.repair_all()
    return 2
if __name__=='__main__': sys.exit(main())
