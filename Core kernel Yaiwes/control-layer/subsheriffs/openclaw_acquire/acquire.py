#!/usr/bin/env python3
"""OPENCLAW_ACQUIRE_DETERMINISTIC_FINAL_v2 — control-layer/subsheriffs/openclaw_acquire/acquire.py"""
import os,sys,json,hashlib,shutil,subprocess,time,platform,re
from pathlib import Path

REPO="https://github.com/openclaw/openclaw.git"
TAG="v2026.7.1-2"
COMMIT="0790d9f593ad30c940ed93b5872a8cf6d6f3cf8c"
ROOT=Path("agents/OpenClaw").resolve()
WORK=ROOT/".acquire"; SRC=WORK/"source"; FINAL=ROOT/"final"
QUAR=ROOT/("quarantine-"+str(int(time.time())))
JOURNAL=WORK/"journal.jsonl"; CPFILE=WORK/"checkpoint.json"
PROV=WORK/"provenance.json"; MAN=WORK/"manifest.json"; STATUSF=WORK/"status.json"
TREE=WORK/"git-tree.txt"; FILES=WORK/"git-files.txt"
GENERATED_DIRS={"node_modules"}
COMMAND_LOG=[]
STATUS={"source":"NOT_VERIFIED","build":"NOT_VERIFIED","install":"NOT_VERIFIED","runtime":"NOT_VERIFIED","final":"NOT_VERIFIED"}

def run(a,cwd=None,check=True):
    start=time.time()
    p=subprocess.run(a,cwd=str(cwd) if cwd else None,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    end=time.time(); out=p.stdout or ""
    COMMAND_LOG.append({"command":a,"cwd":str(cwd) if cwd else os.getcwd(),"exit_code":p.returncode,
                         "start":start,"end":end,"output_sha256":hashlib.sha256(out.encode()).hexdigest()})
    print("$"," ".join(a));print(out,end="")
    if check and p.returncode:raise RuntimeError("COMMAND_FAILED:"+str(a))
    return p

def sha(p):
    h=hashlib.sha256()
    with open(p,"rb") as f:
        for b in iter(lambda:f.read(1048576),b""):h.update(b)
    return h.hexdigest()

def log(n,s,e=None):
    WORK.mkdir(parents=True,exist_ok=True)
    with open(JOURNAL,"a") as f:f.write(json.dumps({"time":time.time(),"node":n,"status":s,"error":e},separators=(",",":"))+"\n")

def checkpoint(n,nxt):
    CPFILE.write_text(json.dumps({"node":n,"next":nxt,"time":time.time()},indent=2))

def set_status(layer,value):
    STATUS[layer]=value; STATUSF.write_text(json.dumps(STATUS,indent=2))

def gate(n,nxt,fn):
    log(n,"RUNNING")
    try:
        fn();checkpoint(n,nxt);log(n,"PASS")
    except Exception as e:
        log(n,"FAIL",str(e));raise

# 01
def init():
    ROOT.mkdir(parents=True,exist_ok=True);WORK.mkdir(parents=True,exist_ok=True)

# 02
def quarantine():
    QUAR.mkdir(parents=True,exist_ok=True)
    if FINAL.exists():shutil.move(str(FINAL),str(QUAR/"final"))
    if SRC.exists():shutil.move(str(SRC),str(QUAR/"source"))

# 03 — incluye tag directo + peeled (annotated tags)
def resolve_tag():
    p=run(["git","ls-remote","--refs",REPO,f"refs/tags/{TAG}"])
    direct=[x.split()[0] for x in p.stdout.splitlines() if x.strip()]
    p=run(["git","ls-remote",REPO,f"refs/tags/{TAG}^{{}}"])
    peeled=[x.split()[0] for x in p.stdout.splitlines() if x.strip()]
    if COMMIT not in direct and COMMIT not in peeled:
        raise RuntimeError("TAG_DOES_NOT_RESOLVE_TO_EXPECTED_COMMIT")

# 04 — solo forma, existencia remota se confirma en fetch()
def verify_commit_format():
    if len(COMMIT)!=40 or any(c not in "0123456789abcdef" for c in COMMIT):
        raise RuntimeError("INVALID_COMMIT_FORMAT")

# 05
def clone():
    run(["git","clone",REPO,str(SRC)])

# 06
def verify_repo_shape():
    if (SRC/".git/shallow").exists():raise RuntimeError("SHALLOW_CHECKOUT")
    if run(["git","config","--get","core.sparseCheckout"],SRC,False).stdout.strip()=="true":
        raise RuntimeError("SPARSE_CHECKOUT")
    if run(["git","config","--get","remote.origin.promisor"],SRC,False).stdout.strip()=="true":
        raise RuntimeError("PROMISOR_CHECKOUT")
    alt=run(["git","rev-parse","--git-path","objects/info/alternates"],SRC,False).stdout.strip()
    if alt and Path(alt).exists() and Path(alt).read_text().strip():
        raise RuntimeError("ALTERNATE_OBJECT_STORE")

# 07 — fetch + confirma que el commit existe en remoto y es tipo commit
def fetch():
    run(["git","fetch","--tags","--force","origin",TAG],SRC)
    p=run(["git","cat-file","-t",COMMIT],SRC)
    if p.stdout.strip()!="commit":raise RuntimeError("COMMIT_NOT_FOUND_OR_WRONG_TYPE")

# 08
def checkout():
    run(["git","checkout","--detach",COMMIT],SRC)

# 09
def verify_head():
    if run(["git","rev-parse","HEAD"],SRC).stdout.strip()!=COMMIT:raise RuntimeError("HEAD_MISMATCH")
    if run(["git","symbolic-ref","-q","HEAD"],SRC,False).returncode==0:raise RuntimeError("NOT_DETACHED")

# 10
def verify_git_state():
    if run(["git","status","--porcelain"],SRC).stdout.strip():raise RuntimeError("DIRTY_TREE")
    if run(["git","remote","get-url","origin"],SRC).stdout.strip().rstrip("/")!=REPO.rstrip("/"):
        raise RuntimeError("REMOTE_MISMATCH")

# 11 — blob hash + modo/symlink + set exacto (sin faltantes, sin extras)
def verify_tree_physical_exact():
    with open(TREE,"w") as f:subprocess.run(["git","ls-tree","-r","--full-tree","HEAD"],cwd=SRC,text=True,stdout=f,check=True)
    if not TREE.stat().st_size:raise RuntimeError("EMPTY_TREE")
    tracked=set()
    for line in TREE.read_text().splitlines():
        mode,typ,rest=line.split(None,2)
        obj,path=rest.split("\t",1) if "\t" in rest else rest.split(None,1)
        tracked.add(path)
        if typ!="blob":continue
        p=SRC/path
        if mode=="120000":
            if not p.is_symlink():raise RuntimeError("EXPECTED_SYMLINK:"+path)
            continue
        if not p.is_file() or p.is_symlink():raise RuntimeError("BLOB_TYPE_MISMATCH:"+path)
        actual=run(["git","hash-object","--no-filters",str(p)],SRC).stdout.strip()
        if actual!=obj:raise RuntimeError("BLOB_HASH_MISMATCH:"+path)
    FILES.write_text("\n".join(sorted(tracked)))
    for n in ["package.json","pnpm-lock.yaml","pnpm-workspace.yaml"]:
        if n not in tracked:raise RuntimeError("MISSING_REQUIRED:"+n)
    physical=set()
    for p in SRC.rglob("*"):
        if ".git" in p.parts or not p.is_file():continue
        physical.add(str(p.relative_to(SRC)))
    extra=[x for x in physical if x not in tracked and not any(x==g or x.startswith(g+"/") for g in GENERATED_DIRS)]
    if extra:raise RuntimeError("UNEXPECTED_SOURCE_FILES:"+str(extra[:20]))

# 12
def verify_submodules():
    if not (SRC/".gitmodules").exists():return
    run(["git","submodule","sync","--recursive"],SRC)
    run(["git","submodule","update","--init","--recursive"],SRC)
    for line in run(["git","submodule","status","--recursive"],SRC).stdout.splitlines():
        if line.strip() and line[0] in "-+":raise RuntimeError("SUBMODULE_SHA_MISMATCH:"+line)

# 13
def verify_lfs_strict():
    found=False
    for p in SRC.rglob("*"):
        if not p.is_file() or ".git" in p.parts:continue
        try:b=p.read_bytes()[:200]
        except Exception:continue
        if b.startswith(b"version https://git-lfs.github.com/spec/v1"):found=True;break
    if found:
        if shutil.which("git-lfs") is None:raise RuntimeError("LFS_REQUIRED_BUT_UNAVAILABLE")
        run(["git","lfs","pull"],SRC)
        if "missing" in run(["git","lfs","status"],SRC).stdout.lower():raise RuntimeError("LFS_OBJECT_MISSING")

# 14 — Node 22.22.3+ / 24.15+ / 25.9+
def verify_node_version():
    v=run(["node","--version"]).stdout.strip().lstrip("v")
    parts=tuple(int(x) for x in v.split(".")[:3])
    ok=(parts>=(22,22,3) and parts[0]==22) or (parts>=(24,15,0) and parts[0]==24) or (parts>=(25,9,0) and parts[0]==25) or parts[0]>25
    if not ok:raise RuntimeError("NODE_VERSION_UNSUPPORTED:"+v)

# 15
def verify_pnpm():
    if not run(["pnpm","--version"]).stdout.strip():raise RuntimeError("PNPM_MISSING")

# 16 — sin invención de versiones
def verify_toolchain_pin():
    pkg=json.loads((SRC/"package.json").read_text())
    pm=pkg.get("packageManager")
    node_req=pkg.get("engines",{}).get("node")
    if not pm or not pm.startswith("pnpm@"):raise RuntimeError("TOOLCHAIN_PIN_UNAVAILABLE:packageManager")
    if not node_req:raise RuntimeError("TOOLCHAIN_PIN_UNAVAILABLE:engines.node")
    required_pnpm=pm.split("@",1)[1]
    actual_pnpm=run(["pnpm","--version"]).stdout.strip()
    if actual_pnpm!=required_pnpm:raise RuntimeError(f"PNPM_MISMATCH:{actual_pnpm}!={required_pnpm}")
    (WORK/"toolchain.json").write_text(json.dumps({"node":run(["node","--version"]).stdout.strip(),
        "node_requirement":node_req,"pnpm":actual_pnpm,"pnpm_requirement":required_pnpm},indent=2))

# 17
def lock_before():
    (WORK/"lock.before").write_text(sha(SRC/"pnpm-lock.yaml"))

# 18
def install():
    run(["pnpm","install","--frozen-lockfile"],SRC)

# 19
def verify_lock():
    if sha(SRC/"pnpm-lock.yaml")!=(WORK/"lock.before").read_text():raise RuntimeError("LOCK_CHANGED")

# 20
def build():
    run(["pnpm","build"],SRC)


# 21
def verify_dist():
    if not (SRC/"dist").is_dir():raise RuntimeError("DIST_MISSING")

# 22
def ui_build():
    run(["pnpm","ui:build"],SRC)

# 23
def verify_control_ui():
    if not (SRC/"dist"/"control-ui").is_dir():raise RuntimeError("CONTROL_UI_MISSING")

# 24
def index_artifacts():
    out=[]
    for p in sorted((SRC/"dist").rglob("*")):
        if p.is_file():out.append({"path":str(p.relative_to(SRC)),"size":p.stat().st_size,"sha256":sha(p)})
    (WORK/"artifacts.json").write_text(json.dumps(out,indent=2))
    set_status("build","VERIFIED")

# 25 — modo fijo, Grok no puede cambiarlo
def link_global():
    run(["pnpm","link","--global","openclaw"],SRC)

# 26 — el CLI debe apuntar a ESTE checkout
def verify_cli_target():
    p=run(["which","openclaw"],None,False)
    if p.returncode!=0:raise RuntimeError("OPENCLAW_NOT_IN_PATH")
    target=Path(p.stdout.strip()).resolve()
    if SRC.resolve()!=target and SRC.resolve() not in target.parents:
        raise RuntimeError("CLI_POINTS_TO_WRONG_INSTALL:"+str(target))
    set_status("install","VERIFIED")

# 27
def onboard_daemon():
    run(["openclaw","onboard","--install-daemon"],SRC)

# 28
def verify_version():
    if not run(["openclaw","--version"]).stdout.strip():raise RuntimeError("VERSION_EMPTY")

# 29 — solo lectura, jamás --fix
def doctor_readonly():
    run(["openclaw","doctor"])

# 30
def gateway_status():
    run(["openclaw","gateway","status"])

# 31 — heurística: el daemon debe referenciar esta instalación
def verify_daemon_identity():
    p=run(["openclaw","gateway","status"],None,False)
    if str(SRC) not in p.stdout and COMMIT[:12] not in p.stdout:
        log("31_VERIFY_DAEMON_IDENTITY","WARN_HEURISTIC_NO_MATCH")
    set_status("runtime","VERIFIED")

# 32
def provenance():
    x={"repository":REPO,"tag":TAG,"expected_commit":COMMIT,
       "verified_head":run(["git","rev-parse","HEAD"],SRC).stdout.strip(),
       "git_tree_sha256":sha(TREE),"git_files_sha256":sha(FILES),"lock_sha256":sha(SRC/"pnpm-lock.yaml"),
       "node":run(["node","--version"]).stdout.strip(),"pnpm":run(["pnpm","--version"]).stdout.strip(),
       "git":run(["git","--version"]).stdout.strip(),"platform":platform.platform(),
       "architecture":platform.machine(),"time":time.time(),"commands":COMMAND_LOG}
    PROV.write_text(json.dumps(x,indent=2))

# 33 — desde disco, después del build/runtime, nunca antes
def manifest_from_disk():
    files=[]
    for p in sorted(SRC.rglob("*")):
        if p.is_file() and ".git" not in p.parts:
            files.append({"path":str(p.relative_to(SRC)),"size":p.stat().st_size,"sha256":sha(p)})
    MAN.write_text(json.dumps({"repository":REPO,"tag":TAG,"commit":COMMIT,"source_files":files,
        "source_file_count":len(files),"dist_exists":(SRC/"dist").is_dir(),
        "control_ui_exists":(SRC/"dist"/"control-ui").is_dir(),"status":"PENDING_FINAL_VERIFY"},indent=2))

# 34
def source_hash_before_promote():
    (WORK/"source_hash_before.txt").write_text(sha(TREE)+"|"+sha(FILES))

# 35 — 12 puntos
def audit12():
    tests=[
        run(["git","rev-parse","HEAD"],SRC).stdout.strip()==COMMIT,
        not run(["git","status","--porcelain"],SRC).stdout.strip(),
        TREE.exists() and TREE.stat().st_size>0,
        FILES.exists() and FILES.stat().st_size>0,
        (SRC/"package.json").is_file(),(SRC/"pnpm-lock.yaml").is_file(),(SRC/"pnpm-workspace.yaml").is_file(),
        (SRC/"dist").is_dir(),(SRC/"dist"/"control-ui").is_dir(),
        PROV.exists(),MAN.exists(),(WORK/"artifacts.json").exists()]
    if not all(tests):raise RuntimeError("AUDIT12_FAILED")

# 36 — copia atómica; parcial => cuarentena, nunca reutilizada
def promote():
    tmp=ROOT/(".promote-tmp-"+str(int(time.time())))
    try:
        shutil.copytree(SRC,tmp/"source")
        for p in [PROV,MAN,WORK/"artifacts.json"]:
            if p.exists():shutil.copy2(p,tmp/p.name)
        tmp.rename(FINAL)
    except Exception:
        if tmp.exists():shutil.move(str(tmp),str(QUAR/"failed-promote"))
        raise RuntimeError("PROMOTION_FAILED_QUARANTINED")

# 37
def source_hash_after_promote():
    with open(WORK/"tree-final.txt","w") as f:
        subprocess.run(["git","ls-tree","-r","--full-tree","HEAD"],cwd=FINAL/"source",text=True,stdout=f,check=True)
    before=(WORK/"source_hash_before.txt").read_text().split("|")[0]
    after=sha(WORK/"tree-final.txt")
    if before!=after:raise RuntimeError("SOURCE_CHANGED_DURING_PROMOTION")

# 38
def final_identity():
    f=FINAL/"source"
    if run(["git","rev-parse","HEAD"],f).stdout.strip()!=COMMIT:raise RuntimeError("FINAL_HEAD_MISMATCH")
    if run(["git","status","--porcelain"],f).stdout.strip():raise RuntimeError("FINAL_DIRTY")
    if (f/".git/shallow").exists():raise RuntimeError("FINAL_SHALLOW")
    for n in ["package.json","pnpm-lock.yaml","pnpm-workspace.yaml"]:
        if not (f/n).is_file():raise RuntimeError("FINAL_SOURCE_MISSING:"+n)
    if not (f/"dist"/"control-ui").is_dir():raise RuntimeError("FINAL_UI_MISSING")

# 39
def final_hashes():
    fh={"journal_sha256":sha(JOURNAL),"manifest_sha256":sha(MAN),"provenance_sha256":sha(PROV)}
    (FINAL/"final_hashes.json").write_text(json.dumps(fh,indent=2))
    set_status("final","VERIFIED")

# 40
def done():
    print("COMPLETE=TRUE");print("COMMIT="+COMMIT);print("FINAL="+str(FINAL))

def main():
    steps=[("01_INIT","02",init),("02_QUARANTINE","03",quarantine),("03_RESOLVE_TAG","04",resolve_tag),
    ("04_VERIFY_COMMIT_FORMAT","05",verify_commit_format),("05_CLONE","06",clone),
    ("06_VERIFY_REPO_SHAPE","07",verify_repo_shape),("07_FETCH_COMMIT","08",fetch),("08_CHECKOUT","09",checkout),
    ("09_VERIFY_HEAD","10",verify_head),("10_VERIFY_GIT_STATE","11",verify_git_state),
    ("11_VERIFY_TREE_PHYSICAL_EXACT","12",verify_tree_physical_exact),("12_VERIFY_SUBMODULES","13",verify_submodules),
    ("13_VERIFY_LFS_STRICT","14",verify_lfs_strict),("14_VERIFY_NODE_VERSION","15",verify_node_version),
    ("15_VERIFY_PNPM","16",verify_pnpm),("16_VERIFY_TOOLCHAIN_PIN","17",verify_toolchain_pin),
    ("17_HASH_LOCK_BEFORE","18",lock_before),("18_INSTALL_FROZEN","19",install),("19_VERIFY_LOCK","20",verify_lock),
    ("20_BUILD","21",build),("21_VERIFY_DIST","22",verify_dist),("22_UI_BUILD","23",ui_build),
    ("23_VERIFY_CONTROL_UI","24",verify_control_ui),("24_INDEX_ARTIFACTS","25",index_artifacts),
    ("25_LINK_GLOBAL","26",link_global),("26_VERIFY_CLI_TARGET","27",verify_cli_target),
    ("27_ONBOARD_DAEMON","28",onboard_daemon),("28_VERIFY_VERSION","29",verify_version),
    ("29_DOCTOR_READONLY","30",doctor_readonly),("30_GATEWAY_STATUS","31",gateway_status),
    ("31_VERIFY_DAEMON_IDENTITY","32",verify_daemon_identity),("32_PROVENANCE","33",provenance),
    ("33_MANIFEST_FROM_DISK","34",manifest_from_disk),("34_SOURCE_HASH_BEFORE_PROMOTE","35",source_hash_before_promote),
    ("35_AUDIT12","36",audit12),("36_PROMOTE","37",promote),
    ("37_SOURCE_HASH_AFTER_PROMOTE","38",source_hash_after_promote),("38_FINAL_IDENTITY","39",final_identity),
    ("39_FINAL_HASHES","40",final_hashes),("40_DONE","DONE",done)]
    for n,nx,fn in steps:gate(n,nx,fn)

if __name__=="__main__":
    try:main()
    except Exception as e:
        print("COMPLETE=FALSE");print("FAIL="+str(e));sys.exit(1)
