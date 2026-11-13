#!/usr/bin/env python3
"""Recover required dataset bytes without Git LFS and prove source identity."""
import argparse, hashlib, json, os, re, shutil, tempfile, time, urllib.request, zipfile
from pathlib import Path, PurePosixPath
ROOT=Path("Agente core kernel Yaiwes principal"); LFS=b"version https://git-lfs.github.com/spec/v1\n"; CHUNK=45*1024*1024
CONFIG={
 "HelpSteer2":{"target":ROOT/"HelpSteer2","base":"https://huggingface.co/datasets/nvidia/HelpSteer2/resolve/990b2711a36180dd19d9c94b8627844866f8982a","source":"https://huggingface.co/datasets/nvidia/HelpSteer2","source_commit":"990b2711a36180dd19d9c94b8627844866f8982a","allowed":{"disagreements/disagreements.jsonl.gz","preference/preference.jsonl.gz","train.jsonl.gz","validation.jsonl.gz"}},
 "PRM800K":{"target":ROOT/"PRM800K","base":"https://huggingface.co/datasets/Mai0313/prm800k/resolve/6d38cda87e33f59d2a7ec63c3002984ed4f8e98b","source":"https://huggingface.co/datasets/Mai0313/prm800k","source_commit":"6d38cda87e33f59d2a7ec63c3002984ed4f8e98b","allowed":{"prm800k/data/phase1_test.jsonl","prm800k/data/phase1_train.jsonl","prm800k/data/phase2_test.jsonl","prm800k/data/phase2_train.jsonl","prm800k/math_splits/test.jsonl","prm800k/math_splits/train.jsonl"}},
 "Math-Shepherd":{"target":ROOT/"Math-Shepherd","base":"https://huggingface.co/datasets/peiyi9979/Math-Shepherd/resolve/c6042b88f2050c0ff35587de21185a8476176a2a","source":"https://huggingface.co/datasets/peiyi9979/Math-Shepherd","source_commit":"c6042b88f2050c0ff35587de21185a8476176a2a","allowed":{"math-shepherd.jsonl"}}
}
def norm(s): return re.sub(r"[^a-z0-9]+","",s.lower())
def sha(path):
 h=hashlib.sha256()
 with path.open("rb") as f:
  for b in iter(lambda:f.read(1024*1024),b""): h.update(b)
 return h.hexdigest()
def parse_pointer(data):
 if not data.startswith(LFS): return None
 s=data.decode("utf-8","replace"); a=re.search(r"^oid sha256:([0-9a-f]{64})$",s,re.M); b=re.search(r"^size ([0-9]+)$",s,re.M)
 if not a or not b: raise RuntimeError("MALFORMED_SOURCE_POINTER")
 return {"sha256":a.group(1),"bytes":int(b.group(1))}
def pointer_inventory(slug):
 zips=sorted(ROOT.glob(slug+"_*.zip")) or sorted(ROOT.glob(slug+".zip"))
 if not zips: raise RuntimeError(f"SOURCE_ARCHIVE_GAP:{slug}")
 allpaths=[]; pointers=[]
 for z in zips:
  with zipfile.ZipFile(z) as a:
   bad=a.testzip()
   if bad: raise RuntimeError(f"CRC_FAIL:{z}:{bad}")
   for i in a.infolist():
    if i.is_dir(): continue
    q=PurePosixPath(i.filename.replace("\\","/"))
    if q.is_absolute() or ".." in q.parts: raise RuntimeError(f"UNSAFE_ZIP:{i.filename}")
    allpaths.append(q)
    if i.file_size<=1024:
     with a.open(i) as f: p=parse_pointer(f.read(1024))
     if p: pointers.append((q,p,str(z)))
 strip=bool(allpaths) and all(len(q.parts)>1 and norm(q.parts[0])==norm(slug) for q in allpaths)
 out={}
 for q,p,z in pointers:
  rel=(PurePosixPath(*q.parts[1:]) if strip else q).as_posix(); row={"path":rel,**p,"archive":z}; prev=out.get(rel)
  if prev and (prev["sha256"],prev["bytes"])!=(row["sha256"],row["bytes"]): raise RuntimeError(f"POINTER_IDENTITY_COLLISION:{rel}")
  out[rel]=row
 return out
def url_for(cfg,rel):
 from urllib.parse import quote
 return cfg["base"].rstrip("/")+"/"+quote(rel,safe="/")+"?download=true"
def download(url,out):
 last=None
 for attempt in range(1,4):
  try:
   req=urllib.request.Request(url,headers={"User-Agent":"yaiwes-dataset-recovery/1.0"})
   with urllib.request.urlopen(req,timeout=180) as r,out.open("wb") as f: shutil.copyfileobj(r,f,4*1024*1024)
   return
  except Exception as e:
   last=e; out.unlink(missing_ok=True)
   if attempt<3: time.sleep(attempt*5)
 raise RuntimeError(f"HTTP_DOWNLOAD_GAP:{url}:{last}")
def verify_exact(p,r): return p.is_file() and p.stat().st_size==r["bytes"] and sha(p)==r["sha256"]
def verify_split(d,r):
 m=d/"SPLIT_MANIFEST.json"
 if not m.is_file(): return False
 try: doc=json.loads(m.read_text())
 except Exception: return False
 if doc.get("source_sha256")!=r["sha256"] or int(doc.get("source_bytes",-1))!=r["bytes"]: return False
 h=hashlib.sha256(); total=0
 for item in doc.get("parts",[]):
  p=d/item["name"]
  if not p.is_file(): return False
  ph=hashlib.sha256(); n=0
  with p.open("rb") as f:
   for b in iter(lambda:f.read(1024*1024),b""): ph.update(b); h.update(b); n+=len(b); total+=len(b)
  if item.get("sha256")!=ph.hexdigest() or int(item.get("bytes",-1))!=n: return False
 return total==r["bytes"] and h.hexdigest()==r["sha256"]
def install(tmp,target,rel,r,cfg):
 if tmp.stat().st_size!=r["bytes"] or sha(tmp)!=r["sha256"]: raise RuntimeError(f"DATA_RECOVERY_MISMATCH:{rel}")
 dst=target/PurePosixPath(rel)
 if r["bytes"]<CHUNK:
  dst.parent.mkdir(parents=True,exist_ok=True)
  if dst.exists():
   if not verify_exact(dst,r): raise RuntimeError(f"COLLISION_BLOCKED:{dst}")
   return {"path":rel,"mode":"exact_file","bytes":r["bytes"],"sha256":r["sha256"],"status":"VERIFIED_EXISTING"}
  os.replace(tmp,dst); return {"path":rel,"mode":"exact_file","bytes":r["bytes"],"sha256":r["sha256"],"status":"RECOVERED"}
 d=target/(rel+".parts")
 if d.exists():
  if verify_split(d,r): return {"path":rel,"mode":"verified_split","bytes":r["bytes"],"sha256":r["sha256"],"status":"VERIFIED_EXISTING"}
  raise RuntimeError(f"COLLISION_BLOCKED:{d}")
 d.mkdir(parents=True,exist_ok=False); parts=[]; h=hashlib.sha256(); total=0
 with tmp.open("rb") as f:
  idx=1
  while True:
   b=f.read(CHUNK)
   if not b: break
   name=f"part-{idx:04d}.bin"; p=d/name; p.write_bytes(b); ph=hashlib.sha256(b).hexdigest(); parts.append({"name":name,"bytes":len(b),"sha256":ph}); h.update(b); total+=len(b); idx+=1
 if total!=r["bytes"] or h.hexdigest()!=r["sha256"]: raise RuntimeError(f"SPLIT_RECONSTRUCTION_MISMATCH:{rel}")
 doc={"schema":"yaiwes.normal-git-split.v1","source_relative_path":rel,"source_sha256":r["sha256"],"source_bytes":r["bytes"],"chunk_max_bytes":CHUNK,"parts":parts,"reconstruction":"concatenate parts in listed order","recovery_source":cfg["source"],"recovery_source_commit":cfg["source_commit"]}; (d/"SPLIT_MANIFEST.json").write_text(json.dumps(doc,indent=2)+"\n"); tmp.unlink(missing_ok=True)
 return {"path":rel,"mode":"verified_split","bytes":r["bytes"],"sha256":r["sha256"],"parts":len(parts),"status":"RECOVERED"}
def repair(slug,verify_only=False):
 cfg=CONFIG[slug]; target=cfg["target"]; target.mkdir(parents=True,exist_ok=True); pointers=pointer_inventory(slug); selected={k:v for k,v in pointers.items() if k in cfg["allowed"]}; missing=cfg["allowed"]-set(selected); unexpected=set(pointers)-cfg["allowed"]
 if missing: raise RuntimeError("SOURCE_POINTER_EVIDENCE_GAP:"+",".join(sorted(missing)))
 if unexpected: raise RuntimeError("UNEXPECTED_DATA_POINTER_SCOPE:"+",".join(sorted(unexpected)))
 results=[]
 for rel,r in sorted(selected.items()):
  dst=target/PurePosixPath(rel); d=target/(rel+".parts")
  if verify_exact(dst,r): results.append({"path":rel,"mode":"exact_file","bytes":r["bytes"],"sha256":r["sha256"],"status":"VERIFIED_EXISTING"}); continue
  if verify_split(d,r): results.append({"path":rel,"mode":"verified_split","bytes":r["bytes"],"sha256":r["sha256"],"status":"VERIFIED_EXISTING"}); continue
  if verify_only: raise RuntimeError(f"DATA_RECOVERY_MISSING:{rel}")
  with tempfile.TemporaryDirectory(prefix="dataset-recovery-") as td:
   tmp=Path(td)/"payload"; download(url_for(cfg,rel),tmp); results.append(install(tmp,target,rel,r,cfg))
 doc={"schema":"yaiwes.dataset.pointer-recovery.v1","slug":slug,"policy":"NO_GIT_LFS","pointer_evidence":"source ZIP members","recovery_source":cfg["source"],"recovery_source_commit":cfg["source_commit"],"files":results,"verdict":"VERIFIED"}; (target/"SOURCE_POINTER_RECOVERY.json").write_text(json.dumps(doc,indent=2,ensure_ascii=False)+"\n"); return doc
def main():
 ap=argparse.ArgumentParser(); ap.add_argument("--slug",required=True,choices=sorted(CONFIG)); ap.add_argument("--verify-only",action="store_true"); a=ap.parse_args(); doc=repair(a.slug,a.verify_only); out=Path("forensics/extraction")/f"dataset-recovery-{a.slug}-{os.getenv('GITHUB_RUN_ID','local')}.json"; out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(doc,indent=2,ensure_ascii=False)+"\n"); print(json.dumps(doc,ensure_ascii=False)); return 0
if __name__=="__main__": raise SystemExit(main())
