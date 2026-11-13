#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, os
from huggingface_hub import run_job

SCHEMA="yaiwes.websearch.hf-trigger.v1"
HF_NAMESPACE=os.getenv("HF_NAMESPACE","COMAND-CENTER-1")
ENGINE_REF=os.getenv("WEBSEARCH_ENGINE_REF","029f516ce049c327a158b915a8ec5517236baeab")
CPU_FLAVOR=os.getenv("HF_WEBSEARCH_FLAVOR","cpu-upgrade")
DEFAULT_PROVIDERS="ddgs,brave,tavily,serper,firecrawl"
RAW_ENGINE_URL=("https://raw.githubusercontent.com/maxbry123-commits/router-universal-router-inteligente-/"+ENGINE_REF+"/"
"%E2%9E%A1%EF%B8%8F%F0%9F%93%82motores%20de%20descarga%20extracci%C3%B3n%20copiado%20movimiento%20archivos%20router-universal-router-inteligente-/"
"%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20motor%20de%20b%C3%BAsqueda/websearch_engine.py")
SECRET_NAMES=("BRAVE_SEARCH_API_KEY","TAVILY_API_KEY","SERPER_API_KEY","FIRECRAWL_API_KEY","GITHUB_TOKEN")

def main():
    p=argparse.ArgumentParser(description="Trigger on-demand HF Job for Yaiwes web search")
    p.add_argument("query")
    p.add_argument("--providers",default=os.getenv("PROVIDERS",DEFAULT_PROVIDERS))
    p.add_argument("--limit",type=int,default=int(os.getenv("MAX_RESULTS_PER_PROVIDER","8")))
    p.add_argument("--timeout",default=os.getenv("HF_WEBSEARCH_TIMEOUT","20m"))
    p.add_argument("--worker",choices=("HF1","HF2","HF3"),default=os.getenv("HF_WORKER_ID","HF1"))
    p.add_argument("--volume",default=os.getenv("HF_WEBSEARCH_VOLUME",""))
    p.add_argument("--output-root",default=os.getenv("WEBSEARCH_OUTPUT_ROOT",""))
    p.add_argument("--publish-github",default=os.getenv("PUBLISH_GITHUB","auto"))
    p.add_argument("--result-repo",default=os.getenv("RESULT_REPO","maxbry123-commits/router-universal-router-inteligente-"))
    p.add_argument("--result-branch",default=os.getenv("RESULT_BRANCH","main"))
    p.add_argument("--result-root",default=os.getenv("RESULT_ROOT","router inteligente universal/websearch-results"))
    a=p.parse_args()
    q=a.query.strip()
    if not q: raise SystemExit(json.dumps({"schema":SCHEMA,"verdict":"INPUT_GAP","detail":"QUERY required"}))

    secrets={k:os.environ[k] for k in SECRET_NAMES if os.getenv(k)}
    bootstrap="import urllib.request;urllib.request.urlretrieve(%r,'/tmp/websearch_engine.py')"%RAW_ENGINE_URL
    command=["sh","-lc","python -m pip install -q ddgs==9.16.0 && python -c "+repr(bootstrap)+" && python /tmp/websearch_engine.py"]
    output_root=a.output_root or ("/data/websearch/results" if a.volume else "/tmp/websearch-results")
    env={
        "QUERY":q,
        "PROVIDERS":a.providers,
        "MAX_RESULTS_PER_PROVIDER":str(max(1,min(a.limit,20))),
        "WEBSEARCH_OUTPUT_ROOT":output_root,
        "PUBLISH_GITHUB":a.publish_github,
        "RESULT_REPO":a.result_repo,
        "RESULT_BRANCH":a.result_branch,
        "RESULT_ROOT":a.result_root,
    }
    job=run_job(
        image="python:3.12-slim",command=command,flavor=CPU_FLAVOR,namespace=HF_NAMESPACE,
        timeout=a.timeout,name=f"{a.worker.lower()}-websearch",env=env,secrets=secrets or None,
        volumes=[a.volume] if a.volume else None,
        labels={"yaiwes.engine":"websearch","yaiwes.worker":a.worker},
    )
    print(json.dumps({"schema":SCHEMA,"state":"DISPATCH","worker":a.worker,"job_id":job.id,"url":job.url,
        "namespace":HF_NAMESPACE,"flavor":CPU_FLAVOR,"providers":a.providers.split(","),"output_root":output_root,"volume":a.volume or None,"publish_github":a.publish_github},
        ensure_ascii=False,sort_keys=True))

if __name__=="__main__": main()
