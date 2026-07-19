 cat /root/.openclaw/extras_gateway.py
"""
OpenClaw Extras Gateway - capa adicional sobre openclaw :18789
NO modifica el openclaw oficial. Solo agrega features.
"""
import os, json, subprocess, uuid, threading
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs

OPENCLAW_URL = "http://127.0.0.1:18789"
ANCHORS_DIR = "/root/.openclaw/anchors"
SKILLS_DIR = "/root/.openclaw/skills"
DEPLOY_DIR = "/root/.openclaw/deploy"
TASKS_FILE = "/root/.openclaw/tasks.json"
LOGS_DIR = "/root/.openclaw/logs"
LOGS_FILE = os.path.join(LOGS_DIR, "tasks.log")
ANCHOR_INDEX = os.path.join(ANCHORS_DIR, "index.json")
DEPLOY_HISTORY_FILE = os.path.join(DEPLOY_DIR, "history.json")

os.makedirs(os.path.join(ANCHORS_DIR, "documents"), exist_ok=True)
os.makedirs(os.path.join(ANCHORS_DIR, "skills"), exist_ok=True)
os.makedirs(SKILLS_DIR, exist_ok=True)
os.makedirs(DEPLOY_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)

TASKS = {}

def load_index():
    if os.path.exists(ANCHOR_INDEX):
        try:
            with open(ANCHOR_INDEX) as f: return json.load(f)
        except Exception: pass
    return {"documents": [], "skills": [], "updated_at": None}

def save_index(idx):
    idx["updated_at"] = datetime.now(timezone.utc).isoformat()
    with open(ANCHOR_INDEX, "w") as f: json.dump(idx, f, indent=2)

def add_anchor(kind, anchor_id, title, path, metadata=None):
    idx = load_index()
    entry = {"id": anchor_id, "title": title, "path": path, "kind": kind,
             "added_at": datetime.now(timezone.utc).isoformat(),
             "metadata": metadata or {}}
    key = "documents" if kind == "document" else "skills"
    idx[key] = [x for x in idx[key] if x.get("id") != anchor_id]
    idx[key].append(entry)
    save_index(idx)
    return entry

def load_tasks():
    global TASKS
    if os.path.exists(TASKS_FILE):
        try:
            with open(TASKS_FILE) as f: TASKS = {t["id"]: t for t in json.load(f)}
        except Exception: pass

def save_tasks():
    with open(TASKS_FILE, "w") as f: json.dump(list(TASKS.values()), f, indent=2)

def log_task(task_id, msg):
    with open(LOGS_FILE, "a") as f:
        f.write(f"[{datetime.now(timezone.utc).isoformat()}] [{task_id}] {msg}\n")

def create_task(steps, mode="sequential"):
    task_id = uuid.uuid4().hex[:12]
    task = {"id": task_id, "steps": steps, "mode": mode, "status": "pending",
            "current_step": 0, "results": [],
            "created_at": datetime.now(timezone.utc).isoformat(),
            "started_at": None, "finished_at": None, "log": []}
    TASKS[task_id] = task
    save_tasks()
    return task

def execute_task(task_id):
    task = TASKS[task_id]
    task["status"] = "running"
    task["started_at"] = datetime.now(timezone.utc).isoformat()
    log_task(task_id, f"started, {len(task['steps'])} steps")
    for i, step in enumerate(task["steps"]):
        task["current_step"] = i
        log_task(task_id, f"step {i+1}: {step.get('name', '?')}")
        try:
            cmd = step.get("command", "")
            kind = step.get("kind", "shell")
            if kind == "shell":
                r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=300)
                result = {"stdout": r.stdout, "stderr": r.stderr, "exit_code": r.returncode}
            elif kind == "http":
                import httpx
                r = httpx.post(step.get("url", ""), json=step.get("body", {}), timeout=60)
                result = {"status": r.status_code, "body": r.text[:1000]}
            else:
                result = {"error": f"unknown kind: {kind}"}
            task["results"].append({"step": i, "name": step.get("name"), "result": result, "ok": True})
        except Exception as ex:
            task["results"].append({"step": i, "name": step.get("name"), "error": str(ex), "ok": False})
            task["status"] = "failed"
            task["finished_at"] = datetime.now(timezone.utc).isoformat()
            log_task(task_id, f"FAILED: {ex}")
            save_tasks()
            return task
    task["status"] = "completed"
    task["finished_at"] = datetime.now(timezone.utc).isoformat()
    log_task(task_id, "completed")
    save_tasks()
    return task

def list_deploy_scripts():
    scripts = []
    for f in sorted(os.listdir(DEPLOY_DIR)):
        if f.endswith(".sh") and os.path.isfile(os.path.join(DEPLOY_DIR, f)):
            scripts.append({"name": f, "path": f"{DEPLOY_DIR}/{f}",
                            "size": os.path.getsize(os.path.join(DEPLOY_DIR, f))})
    return scripts

def run_deploy_script(name, args=None):
    path = os.path.join(DEPLOY_DIR, name)
    if not os.path.exists(path): return {"ok": False, "error": "not found"}
    if not name.endswith(".sh"): return {"ok": False, "error": "only .sh"}
    cmd = f"bash {path}" + (" " + " ".join(args) if args else "")
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=600)
        result = {"ok": r.returncode == 0, "exit_code": r.returncode,
                  "stdout": r.stdout[-2000:], "stderr": r.stderr[-1000:]}
        history = []
        if os.path.exists(DEPLOY_HISTORY_FILE):
            try:
                with open(DEPLOY_HISTORY_FILE) as f: history = json.load(f)
            except Exception: pass
        history.append({"script": name, "args": args, "result": result,
                        "at": datetime.now(timezone.utc).isoformat()})
        history = history[-50:]
        with open(DEPLOY_HISTORY_FILE, "w") as f: json.dump(history, f, indent=2)
        return result
    except Exception as ex:
        return {"ok": False, "error": str(ex)}

HTML_PAGE = """<!DOCTYPE html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>OpenClaw Extras</title>
<style>
body{font-family:system-ui,-apple-system,sans-serif;background:#0a0a0a;color:#eee;margin:0;padding:0}
header{background:#111;padding:12px 20px;border-bottom:1px solid #333;display:flex;justify-content:space-between;align-items:center;position:sticky;top:0;z-index:10}
header h1{font-size:16px;margin:0;font-weight:600}
nav{display:flex;gap:6px}
nav a{color:#aaa;text-decoration:none;padding:8px 14px;border-radius:6px;font-size:13px;transition:all .2s}
nav a:hover,nav a.active{background:#2a2a2a;color:#fff}
main{padding:20px;max-width:1400px;margin:0 auto}
.card{background:#1a1a1a;border:1px solid #2a2a2a;border-radius:8px;padding:20px;margin-bottom:16px}
.card h3{margin:0 0 12px 0;font-size:16px}
.btn{background:#c33;color:#fff;border:0;padding:8px 16px;border-radius:6px;cursor:pointer;font-size:13px;margin:4px}
.btn:hover{opacity:0.85}
.btn.ok{background:#3a7}
.btn.secondary{background:#555}
input,textarea,select{background:#0a0a0a;color:#eee;border:1px solid #333;border-radius:6px;padding:8px;width:100%;font-family:inherit;font-size:13px;box-sizing:border-box;margin-bottom:8px}
textarea{min-height:200px;font-family:monospace;font-size:12px}
label{display:block;margin:8px 0 4px 0;font-size:12px;color:#aaa;font-weight:500}
.anchor{padding:14px;background:#0a0a0a;border:1px solid #2a2a2a;border-radius:6px;margin-bottom:8px;display:flex;justify-content:space-between;align-items:center}
.anchor h4{margin:0;font-size:14px}
.anchor .meta{font-size:11px;color:#888;margin-top:4px}
.anchor a{color:#6af;font-size:12px;cursor:pointer;text-decoration:none}
pre{background:#000;padding:12px;border-radius:6px;overflow-x:auto;font-size:11px;max-height:500px;overflow-y:auto}
.status{padding:4px 10px;border-radius:4px;font-size:11px;display:inline-block;margin-left:8px}
.status.running{background:#c93;color:#000}
.status.completed{background:#3a7;color:#fff}
.status.failed{background:#c33;color:#fff}
.status.pending{background:#555;color:#fff}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:16px}
.muted{color:#888;font-size:12px}
.tag{background:#2a2a2a;padding:2px 8px;border-radius:3px;font-size:11px;margin-right:4px}
</style></head><body>
<header>
<h1>⚡ OpenClaw Extras</h1>
<nav>
<a href="?page=home" class="{home_active}">Home</a>
<a href="?page=anchors" class="{anchors_active}">📌 Anclajes</a>
<a href="?page=tasks" class="{tasks_active}">⚙️ Tareas</a>
<a href="?page=deploy" class="{deploy_active}">🚀 Deploy</a>
<a href="/chat?token=${OC_GATEWAY_TOKEN}" target="_blank">🤖 OpenClaw →</a>
</nav></header>
<main>
{body}
</main>
<script>
window.EXTRAS_PATH = window.location.pathname.endsWith('/') ? window.location.pathname : window.location.pathname.replace(/[^/]*$/, '');
</script>
</body></html>
"""

ANCHORS_PAGE = """
<div class="card">
<h3>📌 Documentos y Skills Anclados</h3>
<div class="grid" style="grid-template-columns: 1fr 1fr;">
<div>
<label>Tipo</label>
<select id="upl-kind"><option value="document">📄 Documento</option><option value="skill">🛠 Skill</option></select>
<label>Título</label>
<input id="upl-title" placeholder="Nombre del anclaje">
<label>Contenido</label>
<textarea id="upl-content" placeholder="Pega el markdown/texto aqui..."></textarea>
<button class="btn ok" onclick="upload()">💾 Guardar</button>
<button class="btn secondary" onclick="document.getElementById('content').style.display='none'">Cancelar</button>
</div>
<div>
<label>Buscar</label>
<input id="filter" placeholder="Filtrar..." onkeyup="filterList()">
<div id="list" style="max-height:500px;overflow-y:auto"></div>
</div>
</div>
</div>
<div id="content" class="card" style="display:none">
<h3 id="c-title"></h3>
<div class="muted" id="c-meta"></div>
<pre id="c-body"></pre>
<button class="btn secondary" onclick="document.getElementById('content').style.display='none'">Cerrar</button>
</div>
<script>
let A={docs:[],skills:[]};
async function load(){const r=await fetch('/anchors/api/list');A=await r.json();render();}
function render(){
  const all=[...A.docs.map(x=>({...x,kind:'document'})),...A.skills.map(x=>({...x,kind:'skill'}))];
  document.getElementById('list').innerHTML=all.length?all.map(a=>`<div class="anchor"><div><h4>${a.kind==='skill'?'🛠':'📄'} ${a.title}</h4><div class="meta"><span class="tag">${a.kind}</span>${a.added_at}</div></div><a onclick="view('${a.id}','${a.kind}')">Ver →</a></div>`).join(''):'<div class="muted">Sin anclajes aún</div>';
  filterList();
}
function filterList(){
  const q=document.getElementById('filter').value.toLowerCase();
  document.querySelectorAll('#list .anchor').forEach(el=>{el.style.display=el.textContent.toLowerCase().includes(q)?'flex':'none'});
}
async function upload(){
  const kind=document.getElementById('upl-kind').value;
  const title=document.getElementById('upl-title').value;
  const content=document.getElementById('upl-content').value;
  if(!title||!content){alert('Falta titulo o contenido');return;}
  const r=await fetch('/anchors/api/add',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({kind,title,content})});
  const j=await r.json();
  if(j.ok){document.getElementById('upl-title').value='';document.getElementById('upl-content').value='';load();}else{alert(j.error);}
}
async function view(id,kind){
  const r=await fetch(`/anchors/api/get?id=${id}&kind=${kind}`);
  const j=await r.json();
  document.getElementById('c-title').textContent=j.title;
  document.getElementById('c-meta').textContent=`${j.added_at} • ${j.path}`;
  document.getElementById('c-body').textContent=j.content;
  document.getElementById('content').style.display='block';
}
load();
</script>
"""

TASKS_PAGE = """
<div class="card">
<h3>⚙️ Sandbox de Tareas (Loop Pipeline)</h3>
<div class="muted">Cada linea es un paso. Formato: <code>nombre|comando</code> (con prefix <code>shell:</code> o <code>http:</code>).</div>
<label>Pasos</label>
<textarea id="steps" placeholder="build|shell:cd /opt/nct/chat-app && npm run build
test|shell:cd /opt/nct/chat-app && npm test
health|http:http://127.0.0.1:18789/"></textarea>
<label>Modo</label>
<select id="mode"><option value="sequential">Sequential (parar en error)</option><option value="continue">Continue (continuar en error)</option></select>
<button class="btn ok" onclick="run()">▶ Ejecutar Pipeline</button>
</div>
<div id="result" class="card" style="display:none">
<h3>Task <span id="r-id"></span> <span id="r-status" class="status"></span></h3>
<div class="muted" id="r-meta"></div>
<div id="r-steps"></div>
</div>
<script>
async function run(){
  const lines=document.getElementById('steps').value.split('\\n').filter(l=>l.trim());
  const steps=lines.map((line,i)=>{
    const[name,...rest]=line.split('|');
    const cmd=rest.join('|').trim();
    let kind='shell';
    let command=cmd;
    if(cmd.startsWith('http:')){kind='http';command=cmd.substring(5).trim();}
    else if(cmd.startsWith('shell:')){command=cmd.substring(6).trim();}
    return{name:name.trim()||'step'+(i+1),kind,command};
  });
  const r=await fetch('/tasks/api/create',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({steps,mode:document.getElementById('mode').value})});
  const j=await r.json();
  document.getElementById('result').style.display='block';
  document.getElementById('r-id').textContent=j.id;
  poll(j.id);
}
async function poll(id){
  for(let i=0;i<60;i++){
    const r=await fetch(`/tasks/api/get?id=${id}`);
    const j=await r.json();
    const st=document.getElementById('r-status');
    st.textContent=j.status;st.className='status '+j.status;
    document.getElementById('r-meta').textContent=`${j.created_at} → ${j.finished_at||'running'} (${j.results.length}/${j.steps.length} steps)`;
    document.getElementById('r-steps').innerHTML=j.results.map((r,i)=>`<div class="anchor" style="display:block"><h4>${i+1}. ${r.name} ${r.ok?'✅':'❌'}</h4><pre>${JSON.stringify(r.result||r.error,null,2).slice(0,2000)}</pre></div>`).join('');
    if(j.status==='completed'||j.status==='failed')break;
    await new Promise(r=>setTimeout(r,1500));
  }
}
</script>
"""

DEPLOY_PAGE = """
<div class="card">
<h3>🚀 Sistema de Despliegue</h3>
<div class="muted">Scripts en <code>/root/.openclaw/deploy/*.sh</code></div>
<div id="scripts"></div>
<button class="btn ok" onclick="runAll()">▶ Ejecutar Todos (en orden)</button>
</div>
<div id="result" class="card" style="display:none">
<h3>Resultado</h3>
<pre id="r-body"></pre>
</div>
<script>
async function load(){
  const r=await fetch('/deploy/api/scripts');
  const j=await r.json();
  document.getElementById('scripts').innerHTML=j.scripts.length?j.scripts.map(s=>`<div class="anchor"><div><h4>📜 ${s.name}</h4><div class="meta">${s.size} bytes</div></div><button class="btn ok" onclick="run('${s.name}')">▶ Ejecutar</button></div>`).join(''):'<div class="muted">Sin scripts</div>';
}
async function run(name){
  if(!confirm('Ejecutar '+name+'?'))return;
  const r=await fetch('/deploy/api/run',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name,args:[]})});
  const j=await r.json();
  document.getElementById('result').style.display='block';
  document.getElementById('r-body').textContent=JSON.stringify(j,null,2);
}
async function runAll(){
  if(!confirm('Ejecutar TODOS los scripts en orden?'))return;
  const r=await fetch('/deploy/api/run_all',{method:'POST'});
  const j=await r.json();
  document.getElementById('result').style.display='block';
  document.getElementById('r-body').textContent=JSON.stringify(j,null,2);
}
load();
</script>
"""

HOME_PAGE = """
<div class="card">
<h3>🎯 OpenClaw Extras</h3>
<p>Sistema paralelo al gateway openclaw oficial. NO modifica el openclaw :18789.</p>
<div class="grid">
<div class="card">
<h3>📌 Anclajes</h3>
<p>Documentos y skills persistentes. Subir, listar, leer.</p>
<a href="?page=anchors" class="btn ok">Abrir</a>
</div>
<div class="card">
<h3>⚙️ Tareas (Pipeline)</h3>
<p>Sandbox de loops: ejecuta pasos en cadena (shell o HTTP).</p>
<a href="?page=tasks" class="btn ok">Abrir</a>
</div>
<div class="card">
<h3>🚀 Deploy</h3>
<p>Ejecuta scripts .sh del VPS con confirmacion.</p>
<a href="?page=deploy" class="btn ok">Abrir</a>
</div>
<div class="card">
<h3>🤖 OpenClaw Oficial</h3>
<p>Gateway openclaw :18789 (intacto). UI original.</p>
<a href="/chat?token=${OC_GATEWAY_TOKEN}" target="_blank" class="btn secondary">Abrir Chat Oficial</a>
</div>
</div>
<h3 style="margin-top:24px">Estado del Sistema</h3>
<div class="card" id="sysinfo">Cargando...</div>
</div>
<script>
async function load(){
  const r=await fetch('/system/info');
  const j=await r.json();
  document.getElementById('sysinfo').innerHTML=Object.entries(j).map(([k,v])=>`<div style="padding:4px 0"><span class="tag">${k}</span> ${v}</div>`).join('');
}
load();setInterval(load,10000);
</script>
"""


class ExtrasHandler(BaseHTTPRequestHandler):
    def log_message(self, *a): pass

    def _ok(self, body, ct="application/json"):
        if isinstance(body, (dict, list)):
            body = json.dumps(body, indent=2, default=str)
        body = body.encode() if isinstance(body, str) else body
        self.send_response(200)
        self.send_header("Content-Type", ct)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _err(self, code, msg):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"error": msg}).encode())

    def _proxy_openclaw(self):
        import urllib.request
        url = f"{OPENCLAW_URL}{self.path}"
        try:
            req = urllib.request.Request(url, method=self.command)
            for k, v in self.headers.items():
                if k.lower() not in ("host", "content-length"):
                    req.add_header(k, v)
            cl = int(self.headers.get("Content-Length", 0))
            if cl: req.data = self.rfile.read(cl)
            with urllib.request.urlopen(req, timeout=10) as resp:
                self.send_response(resp.status)
                for k, v in resp.headers.items():
                    if k.lower() not in ("transfer-encoding", "connection"):
                        self.send_header(k, v)
                body = resp.read()
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
        except Exception as e:
            self._err(502, f"openclaw proxy: {e}")

    def _render_page(self, active, body_html):
        page = HTML_PAGE
        for n in ("home", "anchors", "tasks", "deploy"):
            page = page.replace(f"{{{n}_active}}", "active" if n == active else "")
        page = page.replace("{body}", body_html)
        self._ok(page, "text/html")

    def do_GET(self):
        path = urlparse(self.path).path
        qs = parse_qs(urlparse(self.path).query)

        if path in ("/", "/home"): self._render_page("home", HOME_PAGE)
        elif path in ("/anchors", "/anchors/"): self._render_page("anchors", ANCHORS_PAGE)
        elif path in ("/tasks", "/tasks/"): self._render_page("tasks", TASKS_PAGE)
        elif path in ("/deploy", "/deploy/"): self._render_page("deploy", DEPLOY_PAGE)
        elif path == "/anchors/api/list":
            self._ok({"documents": load_index().get("documents", []), "skills": load_index().get("skills", [])})
        elif path == "/anchors/api/get":
            anchor_id = qs.get("id", [""])[0]
            kind = qs.get("kind", ["document"])[0]
            items = load_index().get("documents" if kind == "document" else "skills", [])
            for item in items:
                if item["id"] == anchor_id:
                    try:
                        with open(item["path"]) as f: content = f.read()
                    except Exception as e: content = f"error: {e}"
                    self._ok({"id": anchor_id, "title": item["title"], "added_at": item["added_at"],
                              "path": item["path"], "content": content})
                    return
            self._err(404, "not found")
        elif path == "/tasks/api/list": self._ok({"tasks": list(TASKS.values())})
        elif path == "/tasks/api/get":
            tid = qs.get("id", [""])[0]
            if tid in TASKS: self._ok(TASKS[tid])
            else: self._err(404, "task not found")
        elif path == "/deploy/api/scripts": self._ok({"scripts": list_deploy_scripts()})
        elif path == "/deploy/api/history":
            history = []
            if os.path.exists(DEPLOY_HISTORY_FILE):
                try:
                    with open(DEPLOY_HISTORY_FILE) as f: history = json.load(f)
                except: pass
            self._ok({"history": history[-20:]})
        elif path == "/system/info":
            try:
                ok = subprocess.run(["curl", "-sf", "-m", "2", OPENCLAW_URL], capture_output=True).returncode == 0
            except: ok = False
            try:
                tunnel_up = subprocess.run(["pgrep", "-f", "cloudflared tunnel"], capture_output=True).returncode == 0
            except: tunnel_up = False
            self._ok({
                "openclaw_gateway": "running" if ok else "DOWN",
                "extras_gateway": "running on :18790",
                "tunnel": "running" if tunnel_up else "DOWN",
                "anchors_dir": ANCHORS_DIR,
                "deploy_dir": DEPLOY_DIR,
                "tasks_count": len(TASKS),
                "deploy_scripts": len(list_deploy_scripts()),
                "uptime": subprocess.run(["uptime", "-p"], capture_output=True, text=True).stdout.strip(),
            })
        else: self._proxy_openclaw()

    def do_POST(self):
        path = urlparse(self.path).path
        cl = int(self.headers.get("Content-Length", 0))
        body_raw = self.rfile.read(cl) if cl else b"{}"
        try: body = json.loads(body_raw.decode())
        except: body = {}

        if path == "/anchors/api/add":
            kind = body.get("kind", "document")
            title = body.get("title", "untitled")
            content = body.get("content", "")
            anchor_id = uuid.uuid4().hex[:8]
            subdir = "documents" if kind == "document" else "skills"
            path_full = os.path.join(ANCHORS_DIR, subdir, f"{anchor_id}.md")
            with open(path_full, "w") as f: f.write(f"# {title}\n\n{content}\n")
            os.chmod(path_full, 0o600)
            entry = add_anchor(kind, anchor_id, title, path_full)
            self._ok({"ok": True, "entry": entry})
        elif path == "/tasks/api/create":
            steps = body.get("steps", [])
            if not steps: self._err(400, "no steps"); return
            task = create_task(steps, body.get("mode", "sequential"))
            threading.Thread(target=execute_task, args=(task["id"],), daemon=True).start()
            self._ok({"ok": True, "id": task["id"]})
        elif path == "/deploy/api/run":
            self._ok(run_deploy_script(body.get("name"), body.get("args", [])))
        elif path == "/deploy/api/run_all":
            self._ok({"results": [{"name": s["name"], "result": run_deploy_script(s["name"])} for s in list_deploy_scripts()]})
        else: self._err(404, "unknown endpoint")


class ReusableServer(HTTPServer):
    allow_reuse_address = True
    daemon_threads = True



    def _chat_with_token(self, qs):
        token = qs.get("token", ["${OC_GATEWAY_TOKEN}"])[0]
        tunnel = "paperbacks-items-compute-min.trycloudflare.com"
        ws_url = f"wss://{tunnel}/"
        html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Cargando OpenClaw...</title>
<script>
  // 1) escribir token en localStorage antes de cargar openclaw
  localStorage.setItem('openclaw.control.settings.v1', JSON.stringify({{
    gateway: {{ url: '{ws_url}', token: '{token}' }},
    theme: 'claw', themeMode: 'dark'
  }}));
  // 2) redirigir al chat oficial
  window.location.replace('/chat?session=main&token={token}');
</script>
</head><body style="background:#0a0a0a;color:#eee;font-family:system-ui;display:flex;align-items:center;justify-content:center;height:100vh;margin:0">
<div>Cargando chat OpenClaw...</div></body></html>"""
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.send_header("Content-Length", str(len(html)))
        self.end_headers()
        self.wfile.write(html.encode())



    def _proxy_openclaw_with_prefix(self):
        """Proxy /openclaw/* a openclaw :18789 sin tocar el bundle de openclaw.
        Strip /openclaw del path antes de enviar."""
        import urllib.request
        # strip /openclaw del inicio
        subpath = self.path
        if subpath.startswith("/openclaw"):
            subpath = subpath[len("/openclaw"):] or "/"
        url = f"http://127.0.0.1:18789{subpath}"
        try:
            req = urllib.request.Request(url, method=self.command)
            for k, v in self.headers.items():
                if k.lower() not in ("host", "content-length"):
                    req.add_header(k, v)
            cl = int(self.headers.get("Content-Length", 0))
            if cl: req.data = self.rfile.read(cl)
            with urllib.request.urlopen(req, timeout=15) as resp:
                self.send_response(resp.status)
                for k, v in resp.headers.items():
                    if k.lower() not in ("transfer-encoding", "connection", "content-encoding"):
                        self.send_header(k, v)
                body = resp.read()
                # reescribo el HTML para que las rutas internas apunten a /openclaw/...
                ct = resp.headers.get("Content-Type", "")
                if "text/html" in ct:
                    body_str = body.decode("utf-8", errors="ignore")
                    # reemplazar "./" por "/openclaw/"
                    body_str = body_str.replace('href="./', 'href="/openclaw/')
                    body_str = body_str.replace('src="./', 'src="/openclaw/')
                    body_str = body_str.replace('href="/', 'href="/openclaw/')
                    body_str = body_str.replace('src="/', 'src="/openclaw/')
                    # FIX: las URL internas ya tienen /openclaw/ prepended, no duplicar
                    # pero las que ya eran absolutas (http://) quedan igual
                    # y las que tenian ./assets/xxx -> /openclaw/assets/xxx
                    body = body_str.encode()
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
        except Exception as e:
            self._err(502, f"openclaw proxy: {e}")


if __name__ == "__main__":
    load_tasks()
    defaults = {
        "healthcheck.sh": "#!/bin/bash\ncurl -sf http://127.0.0.1:18789/ && echo 'gateway OK'\n",
        "log_tail.sh": "#!/bin/bash\ntail -20 /root/.openclaw/logs/*.log 2>/dev/null\n",
        "restart_openclaw.sh": "#!/bin/bash\npkill -9 -f 'node.*18789' 2>/dev/null\nsleep 3\nnohup /usr/bin/node /usr/lib/node_modules/openclaw/dist/index.js gateway --port 18789 > /var/log/openclaw-fresh.log 2>&1 &\ndisown\nsleep 8\ncurl -sf -m 3 http://127.0.0.1:18789/ && echo 'restarted OK' || echo 'failed'\n",
        "restart_tunnel.sh": "#!/bin/bash\npkill -9 -f 'cloudflared tunnel --url' 2>/dev/null\nsleep 2\ncd /root\nnohup cloudflared tunnel --url http://127.0.0.1:18789 --no-autoupdate > /var/log/openclaw-watchdog-tunnel.log 2>&1 &\ndisown\nsleep 12\nNEWURL=$(grep -oE 'https://[a-z0-9-]+\\.trycloudflare\\.com' /var/log/openclaw-watchdog-tunnel.log | head -1)\necho \"$NEWURL\" > /root/.openclaw/current_tunnel_url.txt\nchmod 600 /root/.openclaw/current_tunnel_url.txt\necho \"new URL: $NEWURL\"\n",
    }
    for name, content in defaults.items():
        path = os.path.join(DEPLOY_DIR, name)
        if not os.path.exists(path):
            with open(path, "w") as f: f.write(content)
            os.chmod(path, 0o755)
    port = int(os.environ.get("EXTRAS_PORT", "18790"))
    server = ReusableServer(("0.0.0.0", port), ExtrasHandler)
    print(f"[extras-gateway] :{port}", flush=True)
    server.serve_forever()
root@vmi3428294:~# echo 