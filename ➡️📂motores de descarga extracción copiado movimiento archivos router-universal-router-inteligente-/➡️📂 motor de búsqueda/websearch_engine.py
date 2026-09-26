#!/usr/bin/env python3
from __future__ import annotations
import argparse, base64, hashlib, html, json, os, pathlib, re, time, urllib.error, urllib.parse, urllib.request
from dataclasses import dataclass
from html.parser import HTMLParser

SCHEMA="yaiwes.websearch.engine.v1"
PROVIDERS=("ddgs","brave","tavily","serper","firecrawl")
UA=os.getenv("WEBSEARCH_USER_AGENT","Mozilla/5.0 (compatible; YaiwesWebSearch/1.0)")
TIMEOUT=float(os.getenv("WEBSEARCH_TIMEOUT_SECONDS","15"))
LIMIT=int(os.getenv("MAX_RESULTS_PER_PROVIDER","8"))
OUTPUT_ROOT=pathlib.Path(os.getenv("WEBSEARCH_OUTPUT_ROOT","/data/websearch/results" if pathlib.Path("/data").exists() else "./websearch-results"))

@dataclass
class Result:
    title:str; url:str; snippet:str; provider:str; rank:int

def req_json(url,method="GET",headers=None,payload=None):
    h={"User-Agent":UA,"Accept":"application/json"}; h.update(headers or {})
    body=None
    if payload is not None:
        body=json.dumps(payload).encode(); h.setdefault("Content-Type","application/json")
    r=urllib.request.Request(url,data=body,headers=h,method=method)
    with urllib.request.urlopen(r,timeout=TIMEOUT) as x: return json.loads(x.read().decode("utf-8","replace"))

def req_text(url):
    r=urllib.request.Request(url,headers={"User-Agent":UA,"Accept":"text/html"})
    with urllib.request.urlopen(r,timeout=TIMEOUT) as x: return x.read().decode("utf-8","replace")

def normalize_ddg(url):
    url=html.unescape(url)
    if url.startswith("//"): url="https:"+url
    p=urllib.parse.urlparse(url)
    if p.netloc.endswith("duckduckgo.com") and p.path.startswith("/l/"):
        q=urllib.parse.parse_qs(p.query)
        if q.get("uddg"): return q["uddg"][0]
    return url

class DDGParser(HTMLParser):
    def __init__(self):
        super().__init__(); self.rows=[]; self.in_result=False; self.ct=False; self.cs=False; self.title=""; self.url=""; self.snip=""
    def handle_starttag(self,tag,attrs):
        a=dict(attrs); c=set((a.get("class") or "").split())
        if tag=="div" and "result" in c:
            self.in_result=True; self.title=self.url=self.snip=""
        elif self.in_result and tag=="a" and "result__a" in c:
            self.ct=True; self.url=a.get("href","")
        elif self.in_result and tag in {"a","div"} and "result__snippet" in c: self.cs=True
    def handle_endtag(self,tag):
        if tag=="a": self.ct=False
        if tag in {"a","div"}: self.cs=False
        if tag=="div" and self.in_result and self.title and self.url:
            self.rows.append(Result(self.title.strip(),normalize_ddg(self.url),self.snip.strip(),"duckduckgo",len(self.rows)+1)); self.in_result=False
    def handle_data(self,data):
        if self.ct:self.title+=data
        elif self.cs:self.snip+=data

def ddgs(q,n):
    try:
        from ddgs import DDGS
    except ImportError as e:
        raise RuntimeError("MISSING_DEPENDENCY:ddgs") from e
    rows=list(DDGS().text(q,max_results=n))
    return [Result(x.get("title",""),x.get("href",""),x.get("body",""),"ddgs",i+1) for i,x in enumerate(rows[:n])]

def duckduckgo(q,n):
    p=DDGParser(); p.feed(req_text("https://html.duckduckgo.com/html/?"+urllib.parse.urlencode({"q":q}))); return p.rows[:n]

def brave(q,n):
    k=os.getenv("BRAVE_SEARCH_API_KEY","").strip()
    if not k: raise RuntimeError("MISSING_SECRET:BRAVE_SEARCH_API_KEY")
    d=req_json("https://api.search.brave.com/res/v1/web/search?"+urllib.parse.urlencode({"q":q,"count":n}),headers={"X-Subscription-Token":k})
    return [Result(x.get("title",""),x.get("url",""),x.get("description",""),"brave",i+1) for i,x in enumerate(d.get("web",{}).get("results",[])[:n])]

def tavily(q,n):
    k=os.getenv("TAVILY_API_KEY","").strip()
    if not k: raise RuntimeError("MISSING_SECRET:TAVILY_API_KEY")
    d=req_json("https://api.tavily.com/search","POST",payload={"api_key":k,"query":q,"max_results":n,"search_depth":"advanced","include_answer":False})
    return [Result(x.get("title",""),x.get("url",""),x.get("content",""),"tavily",i+1) for i,x in enumerate(d.get("results",[])[:n])]

def serper(q,n):
    k=os.getenv("SERPER_API_KEY","").strip()
    if not k: raise RuntimeError("MISSING_SECRET:SERPER_API_KEY")
    d=req_json("https://google.serper.dev/search","POST",{"X-API-KEY":k}, {"q":q,"num":n})
    return [Result(x.get("title",""),x.get("link",""),x.get("snippet",""),"serper",i+1) for i,x in enumerate(d.get("organic",[])[:n])]

def firecrawl(q,n):
    k=os.getenv("FIRECRAWL_API_KEY","").strip()
    if not k: raise RuntimeError("MISSING_SECRET:FIRECRAWL_API_KEY")
    base=os.getenv("FIRECRAWL_BASE_URL","https://api.firecrawl.dev").rstrip("/")
    d=req_json(base+"/v1/search","POST",{"Authorization":"Bearer "+k},{"query":q,"limit":n})
    rows=d.get("data",d.get("results",[]))
    return [Result(x.get("title",""),x.get("url",""),x.get("description",x.get("markdown",""))[:1200],"firecrawl",i+1) for i,x in enumerate(rows[:n])]

FUNCS={"ddgs":ddgs,"duckduckgo":duckduckgo,"brave":brave,"tavily":tavily,"serper":serper,"firecrawl":firecrawl}

def canon(url):
    p=urllib.parse.urlsplit(url.strip()); host=(p.hostname or "").lower()
    port=f":{p.port}" if p.port and p.port not in {80,443} else ""
    pairs=[(k,v) for k,v in urllib.parse.parse_qsl(p.query,keep_blank_values=True) if not k.lower().startswith(("utm_","fbclid","gclid"))]
    return urllib.parse.urlunsplit((p.scheme.lower() or "https",host+port,re.sub(r"/+$","",p.path or "/") or "/",urllib.parse.urlencode(pairs,doseq=True),""))

def aggregate(rows):
    out={}
    for r in rows:
        u=canon(r.url)
        if not urllib.parse.urlsplit(u).netloc: continue
        x=out.setdefault(u,{"title":r.title.strip(),"url":u,"snippet":re.sub(r"\s+"," ",r.snippet).strip()[:1600],"providers":[],"best_rank":r.rank,"score":0.0})
        if r.provider not in x["providers"]: x["providers"].append(r.provider)
        x["best_rank"]=min(x["best_rank"],r.rank); x["score"]+=max(0.0,1.0-(r.rank-1)*0.07)
        s=re.sub(r"\s+"," ",r.snippet).strip()[:1600]
        if len(s)>len(x["snippet"]): x["snippet"]=s
    for x in out.values():
        x["score"]=round(x["score"]+0.35*max(0,len(x["providers"])-1),4); x["providers"].sort()
    return sorted(out.values(),key=lambda x:(-x["score"],x["best_rank"],x["url"]))

def github_publish_summary(run_id, summary_path):
    mode=os.getenv("PUBLISH_GITHUB","auto").strip().lower()
    token=os.getenv("GITHUB_TOKEN","").strip()
    if mode in {"0","false","no","off"}:
        return {"state":"DISABLED"}
    if not token:
        return {"state":"SKIPPED","detail":"GITHUB_TOKEN missing"}
    repo=os.getenv("RESULT_REPO","maxbry123-commits/router-universal-router-inteligente-").strip()
    branch=os.getenv("RESULT_BRANCH","main").strip() or "main"
    root=os.getenv("RESULT_ROOT","router inteligente universal/websearch-results").strip().strip("/")
    dest=f"{root}/{run_id}/summary.md"
    encoded=urllib.parse.quote(dest,safe="/")
    api=f"https://api.github.com/repos/{repo}/contents/{encoded}"
    headers={"Authorization":"Bearer "+token,"Accept":"application/vnd.github+json","User-Agent":UA}
    check=urllib.request.Request(api+"?ref="+urllib.parse.quote(branch,safe=""),headers=headers)
    try:
        with urllib.request.urlopen(check,timeout=TIMEOUT):
            raise RuntimeError("RESULT_DESTINATION_EXISTS:"+dest)
    except urllib.error.HTTPError as e:
        if e.code!=404: raise
    raw=summary_path.read_bytes()
    payload={"message":f"feat(websearch-result): {run_id}","content":base64.b64encode(raw).decode(),"branch":branch}
    req=urllib.request.Request(api,data=json.dumps(payload).encode(),headers={**headers,"Content-Type":"application/json"},method="PUT")
    with urllib.request.urlopen(req,timeout=TIMEOUT) as r:
        created=json.loads(r.read().decode())
    rb=urllib.request.Request(api+"?ref="+urllib.parse.quote(branch,safe=""),headers=headers)
    with urllib.request.urlopen(rb,timeout=TIMEOUT) as r:
        obj=json.loads(r.read().decode())
    got=base64.b64decode((obj.get("content") or "").replace("\n",""))
    if got!=raw: raise RuntimeError("GITHUB_RESULT_READBACK_MISMATCH")
    return {"state":"PUBLISHED_READBACK_VERIFIED","repo":repo,"branch":branch,"path":dest,"url":obj.get("html_url"),"commit":created.get("commit",{}).get("sha")}

def write_outputs(query,providers,status,merged,root):
    jid=os.getenv("JOB_ID","").strip(); stamp=time.strftime("%Y%m%d-%H%M%S",time.gmtime()); digest=hashlib.sha256(query.encode()).hexdigest()[:10]
    run_id=jid or f"{stamp}-{digest}"; out=root/run_id; out.mkdir(parents=True,exist_ok=True)
    payload={"schema":SCHEMA,"query":query,"run_id":run_id,"created_at_epoch":int(time.time()),"providers_requested":providers,"provider_status":status,"result_count":len(merged),"results":merged,"llm_used":False,"verdict":"VERIFIED_CLOSED" if merged else "NO_RESULTS"}
    jp=out/"result.json"; mp=out/"summary.md"; jp.write_text(json.dumps(payload,indent=2,ensure_ascii=False,sort_keys=True)+"\n",encoding="utf-8")
    lines=[f"# Web search: {query}","",f"- Run: `{run_id}`",f"- Resultados: **{len(merged)}**","- LLM usado: **no**","","## Fuentes"]
    for i,x in enumerate(merged,1):
        lines+=["",f"### {i}. {x['title'] or x['url']}",f"- URL: {x['url']}",f"- Proveedores: {', '.join(x['providers'])}",f"- Score: {x['score']}"]
        if x["snippet"]: lines.append(f"- Extracto: {x['snippet']}")
    lines+=["","## Estado de proveedores","","```json",json.dumps(status,indent=2,ensure_ascii=False,sort_keys=True),"```",""]
    mp.write_text("\n".join(lines),encoding="utf-8")
    chk=json.loads(jp.read_text(encoding="utf-8"))
    if chk.get("query")!=query or chk.get("result_count")!=len(merged): raise RuntimeError("READBACK_MISMATCH")
    return {"run_id":run_id,"output_dir":str(out),"result_json":str(jp),"summary_md":str(mp),"verdict":payload["verdict"]}

def run(query,providers,limit,root):
    rows=[]; status={}
    for p in providers:
        fn=FUNCS.get(p)
        if not fn: status[p]={"state":"SKIPPED","detail":"UNKNOWN_PROVIDER"}; continue
        try:
            got=fn(query,limit); rows.extend(got); status[p]={"state":"PASS","results":len(got)}
        except Exception as e: status[p]={"state":"GAP","detail":str(e)[:500]}
    merged=aggregate(rows); out=write_outputs(query,providers,status,merged,root)
    persistence=github_publish_summary(out["run_id"],pathlib.Path(out["summary_md"])) if merged else {"state":"SKIPPED","detail":"NO_RESULTS"}
    return {"schema":SCHEMA,"query":query,"provider_status":status,"result_count":len(merged),"persistence":persistence,**out}

def main():
    a=argparse.ArgumentParser(); a.add_argument("query",nargs="?",default=os.getenv("QUERY","").strip()); a.add_argument("--providers",default=os.getenv("PROVIDERS",",".join(PROVIDERS))); a.add_argument("--limit",type=int,default=LIMIT); a.add_argument("--output-root",default=str(OUTPUT_ROOT)); x=a.parse_args()
    q=x.query.strip()
    if not q: raise SystemExit(json.dumps({"schema":SCHEMA,"verdict":"INPUT_GAP","detail":"QUERY required"}))
    ps=[p.strip().lower() for p in x.providers.split(",") if p.strip()]
    print(json.dumps(run(q,ps,max(1,min(x.limit,20)),pathlib.Path(x.output_root)),ensure_ascii=False,sort_keys=True))

if __name__=="__main__": main()
