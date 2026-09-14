from pathlib import Path
import json
ROOT=Path('📂coda workflow persistencias')
FIELD=ROOT/'🏈 cancha deportiva de fútbol'
TEAM='Swarm agent team Navy seals YAIWES'
KERNEL='''from dataclasses import dataclass,asdict\nfrom pathlib import Path\nimport json\n@dataclass\nclass State:\n task_id:str; status:str="PENDING"; step:int=0; payload:dict|None=None; evidence:list|None=None\n def __post_init__(self): self.payload={} if self.payload is None else self.payload; self.evidence=[] if self.evidence is None else self.evidence\nclass Kernel:\n def __init__(self,p): self.p=Path(p)\n def load(self,t): return State(t) if not self.p.exists() else State(**json.loads(self.p.read_text()))\n def save(self,s): self.p.parent.mkdir(parents=True,exist_ok=True); q=self.p.with_suffix(self.p.suffix+".tmp"); q.write_text(json.dumps(asdict(s),indent=2)); q.replace(self.p); return s\n def claim(self,t,p=None): s=self.load(t); s.status="CLAIMED"; s.payload.update(p or {}); return self.save(s)\n def checkpoint(self,t,step,e=None): s=self.load(t); s.status="CHECKPOINTED"; s.step=step; s.evidence+=([e] if e else []); return self.save(s)\n def retry(self,t,r): s=self.load(t); s.status="PENDING"; s.evidence.append({"retry":r}); return self.save(s)\n def recover(self,t): return self.load(t)\n def complete(self,t): s=self.load(t); s.status="RELEASED"; return self.save(s)\n'''
TEST='''from pathlib import Path\nimport tempfile,unittest\nfrom workflow_kernel import Kernel\nclass T(unittest.TestCase):\n def test_flow(self):\n  with tempfile.TemporaryDirectory() as d:\n   k=Kernel(Path(d)/"s.json"); assert k.claim("T").status=="CLAIMED"; assert k.checkpoint("T",2).step==2; assert k.recover("T").status=="CHECKPOINTED"; assert k.retry("T","x").status=="PENDING"; assert k.complete("T").status=="RELEASED"\nif __name__=="__main__":unittest.main()\n'''
def main():
 cs=sorted(x for x in ROOT.iterdir() if x.is_dir() and x.name.startswith('🏈 ')); assert len(cs)==24
 out=[]
 for c in cs:
  d=c/'code'/'yaiwes_internal'; d.mkdir(exist_ok=True); (d/'workflow_kernel.py').write_text(KERNEL); (d/'test_workflow_kernel.py').write_text(TEST)
  out.append({'component':c.name,'internal_kernel':str(d/'workflow_kernel.py')})
 (FIELD/'YAIWES-INTERNAL-KERNELS-V4.json').write_text(json.dumps({'team':TEAM,'count':24,'components':out},ensure_ascii=False,indent=2))
 print('INTERNAL_KERNELS=24')
if __name__=='__main__':main()
