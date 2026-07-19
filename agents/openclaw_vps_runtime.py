 cat /opt/nct/agents/openclaw/runtime.py 2>/dev/null
#!/usr/bin/env python3
import os, sys, json, sqlite3, time, threading, subprocess, signal, urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer
from datetime import datetime, timezone

AGENT='openclaw'
SANDBOX=f'/opt/nct/agents/{AGENT}/sandbox'
WORKSPACE=f'{SANDBOX}/workspace'
GIT_DIR=f'{SANDBOX}/git'
DB=f'/opt/nct/agents/{AGENT}/memory.db'

os.makedirs(WORKSPACE,exist_ok=True)
os.makedirs(GIT_DIR,exist_ok=True)

conn=sqlite3.connect(DB,check_same_thread=False,timeout=10)
conn.execute('PRAGMA journal_mode=WAL')
conn.executescript('''CREATE TABLE IF NOT EXISTS state(key TEXT PRIMARY KEY, value TEXT, updated_at TEXT);
CREATE TABLE IF NOT EXISTS messages(id INTEGER PRIMARY KEY AUTOINCREMENT, role TEXT, content TEXT, meta TEXT, created_at TEXT);
CREATE TABLE IF NOT EXISTS tasks(id INTEGER PRIMARY KEY AUTOINCREMENT, status TEXT, prompt TEXT, model TEXT, result TEXT, attempts INTEGER DEFAULT 0, created_at TEXT, finished_at TEXT, error TEXT);
CREATE TABLE IF NOT EXISTS heartbeat(id INTEGER PRIMARY KEY AUTOINCREMENT, pid INTEGER, ram_mb REAL, cpu TEXT, last_task TEXT, status TEXT, created_at TEXT);
CREATE TABLE IF NOT EXISTS audit(id INTEGER PRIMARY KEY AUTOINCREMENT, action TEXT, target TEXT, payload TEXT, created_at TEXT);''')
conn.commit()

def g(k,d=None):
    c=conn.execute('SELECT value FROM state WHERE key=?',(k,)).fetchone()
    return json.loads(c[0]) if c else d
def s(k,v):
    conn.execute('INSERT OR REPLACE INTO state(key,value,updated_at) VALUES(?,?,?)',(k,json.dumps(v),datetime.now(timezone.utc).isoformat()));conn.commit()
def au(a,t='',p=''):
    conn.execute('INSERT INTO audit(action,target,payload,created_at) VALUES(?,?,?,?)',(a,t,p,datetime.now(timezone.utc).isoformat()));conn.commit()
def m(role,c,mt=None):
    conn.execute('INSERT INTO messages(role,content,meta,created_at) VALUES(?,?,?,?)',(role,c,json.dumps(mt or {}),datetime.now(timezone.utc).isoformat()));conn.commit()
def e(p,mod='main'):
    c=conn.execute("INSERT INTO tasks(status,prompt,model,created_at) VALUES(?,?,?,?)",('pending',p,mod,datetime.now(timezone.utc).isoformat()));conn.commit();return c.lastrowid
def nx():
    c=conn.execute("SELECT id,prompt,model FROM tasks WHERE status='pending' ORDER BY id LIMIT 1").fetchone()
    if not c: return None
    conn.execute("UPDATE tasks SET status='running',attempts=attempts+1 WHERE id=?",(c[0],));conn.commit();return c
def fi(tid,r,e=None):
    conn.execute("UPDATE tasks SET status=?,result=?,error=?,finished_at=? WHERE id=?",('done' if not e else 'failed',r,e,datetime.now(timezone.utc).isoformat(),tid));conn.commit()
def rc(n=10):
    return conn.execute('SELECT role,content,created_at FROM messages ORDER BY id DESC LIMIT ?',(n,)).fetchall()
def b(pid,ram,cpu,t,s2):
    conn.execute('INSERT INTO heartbeat(pid,ram_mb,cpu,last_task,status,created_at) VALUES(?,?,?,?,?,?)',(pid,ram,cpu,t,s2,datetime.now(timezone.utc).isoformat()));conn.commit()

def call_litellm(prompt, model='coder'):
    """Fallback: usa LiteLLM proxy que tiene keys funcionales"""
    try:
        body = json.dumps({'model': model, 'messages': [{'role':'user','content':prompt}], 'max_tokens': 2048}).encode()
        req = urllib.request.Request('http://127.0.0.1:4000/v1/chat/completions', data=body, headers={'Content-Type':'application/json','Authorization':'Bearer sk-mavis-cerebras-router'})
        with urllib.request.urlopen(req, timeout=60) as r:
            j = json.loads(r.read())
            return j.get('choices',[{}])[0].get('message',{}).get('content','') or '(litellm vacio)'
    except Exception as ex:
        return f'(litellm-err: {e})'

def call_openclaw_cli(prompt):
    """Intenta OpenClaw CLI. Si falla por 401, fallback a LiteLLM."""
    try:
        env = os.environ.copy(); env['HOME']='/root'
        r = subprocess.run(['/usr/bin/openclaw','agent','--agent','main','--local','-m',prompt], env=env, cwd=WORKSPACE, capture_output=True, text=True, timeout=15)
        out = (r.stdout or r.stderr).strip()
        if r.returncode == 0 and out and '401' not in out and 'Authentication' not in out:
            return out[:16000]
        # fallback
        return '[openclaw-cli-fail, fallback-litellm]\n' + call_litellm(prompt, 'coder')
    except subprocess.TimeoutExpired:
        return '[openclaw-timeout, fallback-litellm]\n' + call_litellm(prompt, 'coder')
    except Exception as ex:
        return f'[openclaw-err: {e}, fallback-litellm]\n' + call_litellm(prompt, 'coder')

def run(prompt, model='main'):
    m('user', prompt); au('chat_request','',prompt[:200])
    history = rc(20)
    ctx = '\n'.join(f"[{r}] {c[:500]}" for r,c,_ in reversed(history))
    full = f"""Eres OpenClaw agente de Max. SANDBOX: {WORKSPACE}. Responde conciso. Max es tu creador, usuario VIP.

HISTORIAL: {ctx}

USER: {prompt}"""
    # Prefer LiteLLM (fast, reliable); fallback to openclaw CLI
    txt = call_litellm(full, model)
    if 'litellm-err' in txt or 'vacio' in txt.lower() or len(txt) < 5:
        txt = call_openclaw_cli(full)
    ok = bool(txt) and 'err' not in txt.lower()[:50]
    m('assistant', txt, {'ok': ok, 'pid': os.getpid(), 'model': model}); au('chat_result','','ok' if ok else 'fail')
    return txt, ok

STOP = False
def worker():
    while not STOP:
        t = nx()
        if not t: time.sleep(2); continue
        tid, prompt, model = t
        try:
            o, ok = run(prompt, model); fi(tid, o, None if ok else 'no-ok')
        except Exception as ex: fi(tid,'',str(e))

def hb():
    while not STOP:
        try:
            r = subprocess.run(['ps','-o','pid,rss,pcpu,cmd','-p',str(os.getpid())],capture_output=True,text=True)
            ram = 0.0
            for ln in r.stdout.splitlines()[1:]:
                p = ln.split(None,3)
                if len(p)>=2:
                    try: ram=int(p[1])/1024.0
                    except: pass
                    break
            b(os.getpid(), round(ram,1), 'see-ps', str(g('last_task',''))[:200], 'running')
        except: pass
        time.sleep(30)


WEB_CHROME = '/opt/nct/agents/openclaw/.playwright-browsers/chromium-1223/chrome-linux64/chrome'

def web_dispatch(action, payload):
    try:
        script = '/tmp/web_' + action.replace('.','_') + '.cjs'
        with open(script, 'w') as f:
            if action == 'web.bridge_chrome':
                try:
                    subprocess.run(['pkill','-9','-f','chrome.*remote-debugging'], capture_output=True, timeout=5)
                    import time as _t; _t.sleep(1)
                    log = '/tmp/chrome_bridge.log'
                    subprocess.Popen([WEB_CHROME, '--headless','--no-sandbox','--disable-gpu','--remote-debugging-port=9222','--remote-debugging-address=127.0.0.1','--user-data-dir=/opt/nct/agents/openclaw/.chrome-data','about:blank'], stdout=open(log,'w'), stderr=subprocess.STDOUT, start_new_session=True)
                    _t.sleep(3)
                    import urllib.request as _ur2
                    v = _ur2.urlopen('http://127.0.0.1:9222/json/version', timeout=5).read().decode()
                    pj = _ur2.urlopen('http://127.0.0.1:9222/json', timeout=5).read().decode()[:500]
                    f.write('console.log(' + json.dumps({'ok': True, 'chrome_version': v, 'pages': pj}) + ')')
                except Exception as ex:
                    f.write('console.log(' + json.dumps({'ok': False, 'err': str(ex)[:300]}) + ')')
            elif action == 'web.navigate':
                url = payload.get('url','')
                f.write(_pw_nav(url))
            elif action == 'web.screenshot':
                url = payload.get('url',''); path = payload.get('path','/opt/nct/agents/openclaw/sandbox/workspace/ss.png')
                f.write(_pw_ss(url, path))
            elif action == 'web.verify_endpoints':
                targets = payload.get('targets', [])
                f.write(_pw_verify(targets))
            elif action == 'web.search':
                query = payload.get('query',''); engine = payload.get('engine','duckduckgo')
                f.write(_pw_search(query, engine))
            else:
                f.write("console.log(JSON.stringify({ok:false, err:'unknown-action'}))")
        r = subprocess.run(['node', script], capture_output=True, text=True, timeout=120)
        out = r.stdout.strip()
        try: return json.loads(out)
        except: return {'ok': False, 'raw': out[:1000], 'stderr': r.stderr[:500]}
    except subprocess.TimeoutExpired:
        return {'ok': False, 'err': 'web-timeout-120s'}
    except Exception as ex:
        return {'ok': False, 'err': str(e)}

def _pw_nav(url):
    return f'''const {{ chromium }} = require('/usr/lib/node_modules/openclaw/node_modules/playwright-core');
(async () => {{
  const b = await chromium.launch({{ headless: true, executablePath: '{WEB_CHROME}', args: ['--no-sandbox','--disable-gpu','--disable-dev-shm-usage'] }});
  const p = await (await b.newContext()).newPage();
  try {{
    const r = await p.goto({json.dumps(url)}, {{ waitUntil: 'domcontentloaded', timeout: 30000 }});
    const status = r ? r.status() : 0;
    const title = await p.title();
    const body = (await p.content()).slice(0, 500);
    console.log(JSON.stringify({{ ok: true, status, title, body }}));
  }} catch (e) {{ console.log(JSON.stringify({{ ok: false, err: String(e.message).slice(0,300) }})); }}
  await b.close();
}})();
'''

def _pw_ss(url, path):
    return f'''const {{ chromium }} = require('/usr/lib/node_modules/openclaw/node_modules/playwright-core');
(async () => {{
  const b = await chromium.launch({{ headless: true, executablePath: '{WEB_CHROME}', args: ['--no-sandbox','--disable-gpu','--disable-dev-shm-usage'] }});
  const p = await (await b.newContext()).newPage();
  try {{
    await p.goto({json.dumps(url)}, {{ waitUntil: 'domcontentloaded', timeout: 30000 }});
    await p.screenshot({{ path: {json.dumps(path)} }});
    console.log(JSON.stringify({{ ok: true, path: {json.dumps(path)} }}));
  }} catch (e) {{ console.log(JSON.stringify({{ ok: false, err: String(e.message).slice(0,300) }})); }}
  await b.close();
}})();
'''

def _pw_verify(targets):
    return f'''const {{ chromium }} = require('/usr/lib/node_modules/openclaw/node_modules/playwright-core');
(async () => {{
  const b = await chromium.launch({{ headless: true, executablePath: '{WEB_CHROME}', args: ['--no-sandbox','--disable-gpu','--disable-dev-shm-usage'] }});
  const p = await (await b.newContext()).newPage();
  const out = [];
  for (const t of {json.dumps(targets)}) {{
    try {{
      const r = await p.goto(t, {{ waitUntil: 'domcontentloaded', timeout: 20000 }});
      out.push({{ url: t, ok: true, status: r?r.status():0, title: await p.title() }});
    }} catch (e) {{
      out.push({{ url: t, ok: false, err: String(e.message).slice(0,200) }});
    }}
  }}
  console.log(JSON.stringify({{ ok: true, results: out }}));
  await b.close();
}})();
'''

def _pw_search(query, engine):
    url = f'https://duckduckgo.com/?q={query.replace(" ", "+")}' if engine == 'duckduckgo' else f'https://www.google.com/search?q={query.replace(" ", "+")}'
    return f'''const {{ chromium }} = require('/usr/lib/node_modules/openclaw/node_modules/playwright-core');
(async () => {{
  const b = await chromium.launch({{ headless: true, executablePath: '{WEB_CHROME}', args: ['--no-sandbox','--disable-gpu','--disable-dev-shm-usage'] }});
  const p = await (await b.newContext()).newPage();
  try {{
    await p.goto({json.dumps(url)}, {{ waitUntil: 'domcontentloaded', timeout: 30000 }});
    const title = await p.title();
    const body = (await p.content()).slice(0, 1500);
    console.log(JSON.stringify({{ ok: true, engine: {json.dumps(engine)}, title, body, url: {json.dumps(url)} }}));
  }} catch (e) {{ console.log(JSON.stringify({{ ok: false, err: String(e.message).slice(0,300) }})); }}
  await b.close();
}})();
'''

class H(BaseHTTPRequestHandler):
    def log_message(self,*_): pass
    def do_GET(self):
        if self.path == '/health':
            self.send_response(200); self.send_header('Content-Type','application/json'); self.end_headers()
            self.wfile.write(json.dumps({'ok':True,'agent':'openclaw','persistent':True,'sandbox':WORKSPACE,'memory':DB,'git':GIT_DIR,'pid':os.getpid(),'uptime_s':time.time()-START_T,'method':'openclaw CLI + LiteLLM fallback'}).encode()); return
        if self.path == '/state':
            self.send_response(200); self.send_header('Content-Type','application/json'); self.end_headers()
            self.wfile.write(json.dumps({'recent':[{'role':r,'content':c[:300]} for r,c,_ in rc(10)],'pending':conn.execute("SELECT COUNT(*) FROM tasks WHERE status='pending'").fetchone()[0],'done':conn.execute("SELECT COUNT(*) FROM tasks WHERE status='done'").fetchone()[0],'heartbeats':conn.execute('SELECT COUNT(*) FROM heartbeat').fetchone()[0]}).encode()); return
        self.send_response(404); self.end_headers()
    def do_POST(self):
        n = int(self.headers.get('Content-Length',0))
        body = json.loads(self.rfile.read(n)) if n else {}
        if self.path == '/web':
            act = body.get('action',''); payload = body.get('payload', {})
            au('web_request', act, json.dumps(payload)[:200])
            out = web_dispatch(act, payload)
            s('last_web', act + ' ' + json.dumps(payload)[:200])
            self.send_response(200); self.send_header('Content-Type','application/json'); self.end_headers()
            self.wfile.write(json.dumps(out).encode()); return
        if self.path == '/chat':
            p = body.get('prompt','').strip(); mod = body.get('model','main')
            if not p: self.send_response(400); self.end_headers(); return
            tid = e(p, mod); s('last_task', p); au('enqueue','',p[:200])
            txt, ok = run(p, mod); fi(tid, txt, None if ok else 'no-ok')
            self.send_response(200 if ok else 500); self.send_header('Content-Type','application/json'); self.end_headers()
            self.wfile.write(json.dumps({'ok':ok,'response':txt[:16000],'task_id':tid,'agent':'openclaw','method':'cli+litellm-fallback'}).encode()); return
        if self.path == '/orch':
            import urllib.request as _url
            body_dsl = body.get('dsl', 'v1')
            results = {}
            for ag, port in [('claude-vps', 8081), ('mimo-vps', 8082)]:
                url = f'http://127.0.0.1:{port}/run'
                req = _url.Request(url, data=json.dumps({'dsl': body_dsl}).encode(), headers={'Content-Type':'application/json'})
                try:
                    with _url.urlopen(req, timeout=120) as r:
                        results[ag] = json.loads(r.read())
                except Exception as ex:
                    results[ag] = {'ok': False, 'err': str(e)}
            all_ok = all(r.get('ok') for r in results.values())
            self.send_response(200); self.end_headers()
            self.wfile.write(json.dumps({'ok':all_ok,'agente':'openclaw-vps','orch_v':1,'results':results}).encode()); return
        if self.path == '/anchors':
            anchor_dir = '/opt/nct/anchors/openclaw-vps/'
            files = {}
            for root, dirs, fs in os.walk(anchor_dir):
                for fn in fs:
                    full = os.path.join(root, fn)
                    rel = full[len(anchor_dir):]
                    try:
                        files[rel] = {'mtime': os.path.getmtime(full), 'size': os.path.getsize(full)}
                    except: pass
            self.send_response(200); self.end_headers()
            self.wfile.write(json.dumps({'ok':True,'agente':'openclaw-vps','files':files}).encode()); return

        self.send_response(404); self.end_headers()

START_T = time.time()
s('start_time', START_T); s('workdir', WORKSPACE); s('sandbox', SANDBOX)
m('system', f'OpenClaw agent v4 CLI+LiteLLM-fallback {datetime.now(timezone.utc).isoformat()}')
au('startup','',f'pid={os.getpid()}')
threading.Thread(target=worker,daemon=True,name='worker').start()
threading.Thread(target=hb,daemon=True,name='heartbeat').start()
def term(*_): global STOP; STOP=True; au('shutdown','',''); sys.exit(0)
signal.signal(signal.SIGTERM,term); signal.signal(signal.SIGINT,term)
if __name__ == '__main__':
    print(f'[openclaw-agent v4] pid={os.getpid()} port=8083',flush=True)
    HTTPServer(('127.0.0.1',8083),H).serve_forever()
root@vmi3428294:~# echo 