 cat /root/.openclaw/clawd_panel.py
#!/usr/bin/env python3
"""
Clawd Panel v2 - Interface estilo Claude/Anthropic para OpenClaw.
Se conecta al openclaw oficial :18789 via WebSocket y al MCP bridge :18791.
NO toca el openclaw.
Sirve en :18792.

Features estilo Claude:
- Sidebar izquierdo: New chat, Search, Chats, Projects, Artifacts, Skills, Customize
- Top bar: Model selector (Sonnet 5 / Opus 4.8 / Fable 5 / MiniMax M3)
- Chat con textarea + boton + (adjuntar)
- Boton "Agregar al chat" con sheets (Camara, Fotos, Archivos, Investigacion, Busqueda web, Proyecto, Herramientas, Conectores)
- Directorio de skills estilo pills
- Selector de proyectos dropdown
- Profile pic + plan al fondo del sidebar
"""
import os, json, time, uuid, threading, base64, struct, urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer
from socketserver import ThreadingMixIn
from datetime import datetime, timezone

OPENCLAW_URL = "http://127.0.0.1:18789"
OPENCLAW_WS = "127.0.0.1"
OPENCLAW_PORT = 18789
OPENCLAW_TOKEN = "${OC_GATEWAY_TOKEN}"
MCP_URL = "http://127.0.0.1:18791"
ANCHORS_DIR = "/root/.openclaw/anchors"
PANEL_PORT = int(os.environ.get("PANEL_PORT", "18792"))

# ---- WebSocket client para openclaw ----
class OC:
    def __init__(self):
        self.sock = None
        self.lock = threading.Lock()
        self.connect()

    def connect(self):
        import socket as sk
        s = sk.create_connection((OPENCLAW_WS, OPENCLAW_PORT), timeout=10)
        key = base64.b64encode(os.urandom(16)).decode()
        s.send(f"GET / HTTP/1.1\r\nHost: {OPENCLAW_WS}:{OPENCLAW_PORT}\r\nUpgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\nAuthorization: Bearer {OPENCLAW_TOKEN}\r\nOrigin: http://127.0.0.1:18789\r\n\r\n".encode())
        buf = b""
        while b"connect.challenge" not in buf:
            try: c = s.recv(4096)
            except: break
            if not c: break
            buf += c
        hdr_end = buf.find(b"\r\n\r\n") + 4
        ws = buf[hdr_end:]
        plen = ws[1] & 0x7F
        if plen == 126: plen = struct.unpack("!H", ws[2:4])[0]; start = 4
        else: start = 2
        json.loads(ws[start:start+plen].decode())
        self.sock = s
        self._send(json.dumps({"type":"req","id":"c-p","method":"connect","params":{"minProtocol":1,"maxProtocol":10,"auth":{"token":OPENCLAW_TOKEN},"client":{"id":"openclaw-control-ui","version":"2026.6.11","platform":"web","mode":"ui"},"scopes":["operator.read","operator.write","operator.admin"]}}))
        start = time.time()
        while time.time() - start < 5:
            r = self._read(to=2)
            if not r: continue
            if r.get("id") == "c-p" and r.get("ok"):
                break
            if r.get("type") == "event": continue
        for _ in range(2):
            try: self._read(to=1)
            except: break

    def _send(self, msg):
        data = msg.encode()
        plen = len(data)
        mask = os.urandom(4)
        masked = bytes(b ^ mask[i%4] for i,b in enumerate(data))
        if plen < 126: h = bytes([0x81, plen | 0x80]) + mask
        elif plen < 65536: h = bytes([0x81, 126 | 0x80]) + struct.pack("!H", plen) + mask
        self.sock.send(h + masked)

    def _read(self, to=5):
        self.sock.settimeout(to)
        try: h = self.sock.recv(2)
        except: return None
        if len(h) < 2: return None
        plen = h[1] & 0x7F
        if plen == 126: plen = struct.unpack("!H", self.sock.recv(2))[0]
        elif plen == 127: plen = struct.unpack("!Q", self.sock.recv(8))[0]
        payload = b""
        while len(payload) < plen:
            try: c = self.sock.recv(plen - len(payload))
            except: break
            if not c: break
            payload += c
        if (h[0] & 0x0F) == 0x1:
            try: return json.loads(payload.decode())
            except: return None
        return None

    def call(self, method, params=None, timeout=10):
        with self.lock:
            try:
                if self.sock is None: self.connect()
                req_id = uuid.uuid4().hex[:8]
                self._send(json.dumps({"type":"req","id":req_id,"method":method,"params":params or {}}))
                start = time.time()
                while time.time() - start < timeout:
                    r = self._read(to=1)
                    if not r: continue
                    if r.get("type") == "event": continue
                    if r.get("id") == req_id: return r
                return {"ok": False, "error": "timeout"}
            except Exception as e:
                try: self.sock.close()
                except: pass
                self.sock = None
                return {"ok": False, "error": str(e)}

    def chat_send(self, message, session="agent:main:main", timeout=30):
        """Usa REST /v1/chat/completions - compatible con todos los modelos."""
        import urllib.request
        with self.lock:
            try:
                # Mapear session a modelo OpenClaw
                # session format: agent:m3:openai → usar m3
                m = session
                if "m3" in session and "research" not in session:
                    model = "openclaw/m3"
                elif "m25" in session or "m2.5" in session:
                    model = "openclaw/m25"
                elif "gemma" in session:
                    model = "openclaw/gemma"
                elif "groq" in session:
                    model = "openclaw/groq"
                elif "nvmxb" in session:
                    model = "openclaw/nvmxb"
                elif "nvbrs" in session:
                    model = "openclaw/nvbrs"
                elif "nvmos" in session:
                    model = "openclaw/nvmos"
                elif "nvwmx" in session:
                    model = "openclaw/nvwmx"
                elif "nvwbr" in session:
                    model = "openclaw/nvwbr"
                elif "nvgpt" in session:
                    model = "openclaw/nvgpt"
                elif "main" in session or "default" in session:
                    model = "openclaw/m3-research"
                else:
                    model = "openclaw/m3"  # default
                
                url = f"http://127.0.0.1:{OPENCLAW_PORT}/v1/chat/completions"
                payload = json.dumps({
                    "model": model,
                    "messages": [{"role": "user", "content": message}],
                    "max_tokens": 2000,
                    "stream": False
                }).encode()
                req = urllib.request.Request(url, data=payload, headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {OPENCLAW_TOKEN}"
                })
                with urllib.request.urlopen(req, timeout=timeout) as resp:
                    data = json.loads(resp.read().decode())
                    if "choices" in data and data["choices"]:
                        text = data["choices"][0]["message"].get("content", "")
                        return {"ok": True, "text": text, "events": []}
                    elif "error" in data:
                        return {"ok": False, "error": data["error"], "text": ""}
                    return {"ok": False, "error": "no choices", "text": ""}
            except Exception as e:
                return {"ok": False, "error": str(e), "text": ""}



oc = None
def get_oc():
    global oc
    if oc is None: oc = OC()
    return oc


# ---- HTML estilo Claude/Anthropic ----
HTML = r"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no">
<meta name="apple-mobile-web-app-capable" content="yes">
<title>OpenClaw</title>
<style>
* { box-sizing: border-box; -webkit-tap-highlight-color: transparent; margin: 0; padding: 0; }
body {
  font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", system-ui, sans-serif;
  background: #000; color: #fff;
  height: 100vh; overflow: hidden;
  -webkit-font-smoothing: antialiased;
}
.app { display: flex; height: 100vh; }

/* SIDEBAR estilo Claude */
.sidebar {
  width: 280px;
  background: #0a0a0a;
  border-right: 1px solid #1c1c1e;
  display: flex; flex-direction: column;
  flex-shrink: 0;
}
.sidebar-header {
  padding: 14px 16px;
  display: flex; align-items: center; gap: 12px;
  border-bottom: 1px solid #1c1c1e;
}
.sidebar-header .logo {
  font-size: 17px; font-weight: 600;
  display: flex; align-items: center; gap: 8px;
}
.sidebar-header .spacer { flex: 1; }
.sidebar-header .icon-btn {
  background: transparent; border: 0; color: #8e8e93;
  font-size: 20px; cursor: pointer; padding: 4px;
}
.nav-section { padding: 8px 12px; }
.nav-item {
  display: flex; align-items: center; gap: 12px;
  padding: 10px 12px; border-radius: 8px;
  color: #fff; font-size: 15px; cursor: pointer;
  text-decoration: none;
}
.nav-item:hover { background: #1c1c1e; }
.nav-item .icon { font-size: 18px; color: #fff; }
.nav-item .label { flex: 1; }
.nav-item.active { background: #1c1c1e; }
.divider { height: 1px; background: #1c1c1e; margin: 4px 12px; }
.section-title {
  font-size: 12px; color: #8e8e93; font-weight: 600;
  padding: 8px 12px 4px; text-transform: none;
}
.recent-item {
  padding: 8px 12px; cursor: pointer; border-radius: 8px;
  color: #fff; font-size: 14px; margin: 0 4px;
}
.recent-item:hover { background: #1c1c1e; }
.recent-item .meta { font-size: 11px; color: #8e8e93; margin-top: 2px; }
.sidebar-footer {
  margin-top: auto;
  padding: 12px;
  border-top: 1px solid #1c1c1e;
  display: flex; align-items: center; gap: 10px;
}
.avatar {
  width: 32px; height: 32px; border-radius: 50%;
  background: #fff; color: #000;
  display: flex; align-items: center; justify-content: center;
  font-size: 15px; font-weight: 600;
}
.profile { flex: 1; }
.profile .name { font-size: 14px; font-weight: 600; }
.profile .plan { font-size: 11px; color: #8e8e93; }

/* MAIN CHAT */
.main {
  flex: 1; display: flex; flex-direction: column;
  background: #000; min-width: 0;
}
.topbar {
  padding: 12px 20px;
  display: flex; align-items: center; gap: 16px;
  border-bottom: 1px solid #1c1c1e;
}
.model-selector {
  display: flex; align-items: center; gap: 8px;
  padding: 6px 12px; border-radius: 18px;
  background: #1c1c1e; cursor: pointer;
  font-size: 13px; font-weight: 500;
  color: #fff;
}
.model-selector:hover { background: #2c2c2e; }
.topbar .spacer { flex: 1; }
.topbar .icon-btn {
  background: transparent; border: 0; color: #fff;
  font-size: 18px; cursor: pointer; padding: 6px;
}

/* MESSAGES */
.messages {
  flex: 1; overflow-y: auto;
  padding: 24px 0; max-width: 800px; margin: 0 auto;
  width: 100%;
}
.message {
  padding: 16px 24px;
  display: flex; gap: 16px;
  border-bottom: 1px solid #0a0a0a;
}
.message .avatar {
  width: 32px; height: 32px; flex-shrink: 0;
}
.message .bubble { flex: 1; }
.message.user .bubble { color: #fff; }
.message.assistant .bubble { color: #fff; }
.message .meta {
  font-size: 12px; color: #8e8e93; margin-bottom: 4px;
}
.message .text { font-size: 15px; line-height: 1.6; white-space: pre-wrap; }
.message .text code {
  background: #1c1c1e; padding: 2px 6px; border-radius: 4px;
  font-family: monospace; font-size: 13px;
}

/* INPUT BAR */
.input-wrap {
  border-top: 1px solid #1c1c1e;
  padding: 12px 20px 20px;
  background: #000;
}
.input-bar {
  max-width: 800px; margin: 0 auto;
  display: flex; align-items: flex-end; gap: 8px;
  background: #1c1c1e; border-radius: 24px;
  padding: 8px 8px 8px 16px;
}
.input-bar .add-btn {
  width: 32px; height: 32px; border-radius: 50%;
  background: #2c2c2e; color: #fff; border: 0;
  font-size: 20px; cursor: pointer; flex-shrink: 0;
}
.input-bar textarea {
  flex: 1; background: transparent; color: #fff;
  border: 0; outline: 0; resize: none;
  font-family: inherit; font-size: 15px;
  padding: 8px 4px; max-height: 200px;
}
.input-bar .send-btn {
  width: 32px; height: 32px; border-radius: 50%;
  background: #0a84ff; color: #fff; border: 0;
  font-size: 18px; cursor: pointer; flex-shrink: 0;
}
.input-bar .send-btn:disabled {
  background: #2c2c2e; color: #8e8e93;
}

/* SHEETS estilo iOS */
.sheet-bg {
  position: fixed; inset: 0; background: rgba(0,0,0,0.6);
  display: none; z-index: 99;
}
.sheet-bg.open { display: block; }
.sheet {
  position: fixed; bottom: 0; left: 0; right: 0;
  background: #1c1c1e; border-top-left-radius: 16px; border-top-right-radius: 16px;
  max-height: 80vh; overflow-y: auto;
  transform: translateY(100%);
  transition: transform 0.3s ease-out;
  z-index: 100;
  padding: 8px 0;
}
.sheet.open { transform: translateY(0); }
.sheet .handle {
  width: 36px; height: 5px; background: #48484a;
  border-radius: 3px; margin: 0 auto 8px;
}
.sheet .sheet-header {
  display: flex; justify-content: space-between; align-items: center;
  padding: 8px 16px 16px; font-size: 17px; font-weight: 600;
}
.sheet .close-btn {
  background: transparent; border: 0; color: #8e8e93;
  font-size: 20px; cursor: pointer;
}
.sheet-option {
  display: flex; align-items: center; gap: 16px;
  padding: 12px 16px; cursor: pointer;
  border-bottom: 1px solid #0a0a0a;
}
.sheet-option:active { background: #2c2c2e; }
.sheet-option .icon {
  width: 40px; height: 40px; border-radius: 8px;
  background: #2c2c2e; color: #fff;
  display: flex; align-items: center; justify-content: center;
  font-size: 18px; flex-shrink: 0;
}
.sheet-option .label { flex: 1; font-size: 16px; color: #fff; }
.sheet-option .sub { font-size: 12px; color: #8e8e93; margin-top: 2px; }
.sheet-option .toggle {
  width: 44px; height: 26px; border-radius: 13px;
  background: #0a84ff; position: relative; cursor: pointer;
  border: 0;
}
.sheet-option .toggle.off { background: #39393d; }
.sheet-option .toggle::after {
  content: ''; position: absolute; top: 2px; left: 20px;
  width: 22px; height: 22px; border-radius: 50%;
  background: #fff; transition: 0.2s;
}
.sheet-option .toggle.off::after { left: 2px; }

/* MODEL PICKER */
.model-picker {
  position: fixed; top: 60px; left: 20px;
  background: #1c1c1e; border-radius: 12px;
  border: 1px solid #2c2c2e;
  min-width: 280px; z-index: 50;
  display: none; box-shadow: 0 10px 30px rgba(0,0,0,0.5);
}
.model-picker.open { display: block; }
.model-picker .item {
  padding: 10px 14px; cursor: pointer; color: #fff;
  font-size: 14px; border-bottom: 1px solid #0a0a0a;
  display: flex; align-items: center; gap: 10px;
}
.model-picker .item:last-child { border-bottom: 0; }
.model-picker .item:hover { background: #2c2c2e; }
.model-picker .item .check { color: #0a84ff; font-weight: 700; }

/* SKILLS directorio */
.skills {
  display: flex; flex-wrap: wrap; gap: 8px;
  padding: 12px 24px; max-width: 800px; margin: 0 auto;
  border-top: 1px solid #1c1c1e;
}
.skill-pill {
  background: #1c1c1e; color: #fff;
  padding: 6px 12px; border-radius: 16px;
  font-size: 13px; cursor: pointer;
  border: 0;
}
.skill-pill:hover { background: #2c2c2e; }

/* MOBILE */
@media (max-width: 768px) {
  .sidebar { display: none; }
  .messages { padding: 12px; }
}
</style>
</head>
<body>
<div class="app">
  <!-- SIDEBAR -->
  <aside class="sidebar">
    <div class="sidebar-header">
      <div class="logo">⚡ OpenClaw</div>
      <div class="spacer"></div>
      <button class="icon-btn" onclick="newChat()" title="Nuevo chat">+</button>
    </div>
    <div class="nav-section">
      <a class="nav-item" onclick="newChat()">
        <span class="icon">+</span><span class="label">Nuevo chat</span>
      </a>
      <a class="nav-item" onclick="alert('Buscar proximamente')">
        <span class="icon">🔍</span><span class="label">Buscar</span>
      </a>
      <a class="nav-item" onclick="showSheet('chats')">
        <span class="icon">💬</span><span class="label">Chats</span>
      </a>
      <a class="nav-item" onclick="showSheet('projects')">
        <span class="icon">📁</span><span class="label">Proyectos</span>
      </a>
      <a class="nav-item" onclick="showSheet('artifacts')">
        <span class="icon">📦</span><span class="label">Artefactos</span>
      </a>
      <a class="nav-item" onclick="showSheet('skills')">
        <span class="icon">🛠</span><span class="label">Skills</span>
      </a>
      <a class="nav-item" onclick="showSheet('scheduler')">
        <span class="icon">⏰</span><span class="label">Programados</span>
      </a>
      <a class="nav-item" onclick="showSheet('files')">
        <span class="icon">📂</span><span class="label">Archivos</span>
      </a>
    </div>
    <div class="divider"></div>
    <div class="section-title">Recientes</div>
    <div id="recent-chats">
      <div class="recent-item" onclick="loadChat('main')">
        <div>Sesion principal</div>
        <div class="meta">main</div>
      </div>
    </div>
    <div class="sidebar-footer">
      <div class="avatar">M</div>
      <div class="profile">
        <div class="name">Max</div>
        <div class="plan">Plan Pro</div>
      </div>
      <button class="icon-btn" onclick="showSettings()">⚙</button>
    </div>
  </aside>

  <!-- MAIN CHAT -->
  <main class="main">
    <div class="topbar">
      <button class="model-selector" id="model-btn" onclick="toggleModels()">
        <span>🤖</span>
        <span id="model-name">MiniMax M3</span>
        <span>▾</span>
      </button>
      <div class="spacer"></div>
      <button class="icon-btn" onclick="showSkills()">🛠</button>
    </div>

    <div class="model-picker" id="model-picker">
      <!-- modelos se cargan via API -->
    </div>

    <div class="messages" id="messages">
      <div class="message assistant">
        <div class="avatar">⚡</div>
        <div class="bubble">
          <div class="text">Hola Max. Soy OpenClaw conectado a 6 modelos (Gemma 4, MiniMax M3, MiniMax M2.5, OSS GPT 120B × 3 keys NVidia+Groq). Toca + para adjuntar o escribe tu mensaje.</div>
        </div>
      </div>
    </div>

    <div class="skills" id="skills-bar">
      <button class="skill-pill" onclick="useSkill('web')">/web-search</button>
      <button class="skill-pill" onclick="useSkill('research')">/research</button>
      <button class="skill-pill" onclick="useSkill('doc')">/doc</button>
      <button class="skill-pill" onclick="useSkill('artifacts')">/artifacts</button>
    </div>

    <div class="input-wrap">
      <div class="input-bar">
        <button class="add-btn" onclick="showAddSheet()" title="Adjuntar">+</button>
        <textarea id="input" rows="1" placeholder="Escribe a OpenClaw..."
                  onkeydown="if(event.key==='Enter'&&!event.shiftKey){event.preventDefault();sendMsg();}"
                  oninput="autoResize(this)"></textarea>
        <button class="send-btn" id="send-btn" onclick="sendMsg()" disabled>↑</button>
      </div>
    </div>
  </main>
</div>

<!-- Sheet: Add to chat (estilo Claude) -->
<div class="sheet-bg" id="sheet-bg" onclick="closeSheet()"></div>
<div class="sheet" id="add-sheet">
  <div class="handle"></div>
  <div class="sheet-header">
    <span>Agregar al chat</span>
    <button class="close-btn" onclick="closeSheet()">×</button>
  </div>
  <div style="display:flex;gap:12px;padding:0 16px 16px">
    <div class="sheet-option" style="flex:1;flex-direction:column;align-items:center;background:#1c1c1e;border-radius:12px;padding:16px 8px">
      <div class="icon" style="margin-bottom:8px">📷</div>
      <div style="font-size:13px">Cámara</div>
    </div>
    <div class="sheet-option" style="flex:1;flex-direction:column;align-items:center;background:#1c1c1e;border-radius:12px;padding:16px 8px">
      <div class="icon" style="margin-bottom:8px">🖼</div>
      <div style="font-size:13px">Fotos</div>
    </div>
    <div class="sheet-option" style="flex:1;flex-direction:column;align-items:center;background:#1c1c1e;border-radius:12px;padding:16px 8px">
      <div class="icon" style="margin-bottom:8px">📄</div>
      <div style="font-size:13px">Archivos</div>
    </div>
  </div>
  <div class="sheet-option">
    <div class="icon">🔍</div>
    <div class="label">Investigación<div class="sub">Búsqueda profunda con citas</div></div>
    <button class="toggle" onclick="this.classList.toggle('off')"></button>
  </div>
  <div class="sheet-option">
    <div class="icon">🌐</div>
    <div class="label">Búsqueda web</div>
    <button class="toggle" onclick="this.classList.toggle('off')"></button>
  </div>
  <div class="sheet-option" onclick="alert('Sin proyecto asignado')">
    <div class="icon">📁</div>
    <div class="label">Agregar al proyecto<div class="sub">Ninguno</div></div>
    <span>›</span>
  </div>
  <div class="sheet-option" onclick="alert('Auto')">
    <div class="icon">💼</div>
    <div class="label">Acceso a herramientas<div class="sub">Auto</div></div>
    <span>›</span>
  </div>
  <div class="sheet-option" onclick="alert('Conectores')">
    <div class="icon">🔌</div>
    <div class="label">Conectores</div>
    <span>›</span>
  </div>
</div>

<script>
let models = [];
let currentModel = null;
let currentSession = 'agent:main:main';

// cargar modelos
fetch('/api/models').then(r => r.json()).then(j => {
  if (j.ok && j.payload && j.payload.models) {
    models = j.payload.models;
    currentModel = models.find(m => m.id === 'MiniMax-M3') || models[0];
    if (currentModel) {
      document.getElementById('model-name').textContent = currentModel.name || currentModel.id;
    }
    const picker = document.getElementById('model-picker');
    picker.innerHTML = models.map(m => `
      <div class="item" onclick="selectModel('${m.provider}/${m.id}','${(m.name||m.id).replace(/'/g,"\\'")}')">
        <span style="flex:1">${m.name || m.id}</span>
        ${currentModel && m.id===currentModel.id ? '<span class="check">✓</span>' : ''}
      </div>
    `).join('');
  }
});

function toggleModels() {
  document.getElementById('model-picker').classList.toggle('open');
}
function selectModel(fullId, name) {
  currentModel = { id: fullId.split('/').slice(1).join('/'), provider: fullId.split('/')[0], name };
  document.getElementById('model-name').textContent = name;
  toggleModels();
}

function showAddSheet() { document.getElementById('add-sheet').classList.add('open'); document.getElementById('sheet-bg').classList.add('open'); }
function closeSheet() { document.querySelectorAll('.sheet').forEach(s => s.classList.remove('open')); document.getElementById('sheet-bg').classList.remove('open'); }
function showSettings() { alert('Configuracion: el sistema esta conectado via MCP a openclaw :18789 y al bridge :18791. Todos los servicios activos.'); }
function showSkills() { alert('Skills disponibles: web-search, research, doc, artifacts. Las ancladas se guardan en /root/.openclaw/anchors/skills/'); }
function newChat() { document.getElementById('messages').innerHTML = ''; currentSession = 'agent:main:main'; }
function useSkill(name) {
  document.getElementById('input').value = '/' + name + ' ';
  document.getElementById('input').focus();
}
function autoResize(el) {
  el.style.height = 'auto';
  el.style.height = Math.min(el.scrollHeight, 200) + 'px';
  document.getElementById('send-btn').disabled = el.value.trim() === '';
}
async function sendMsg() {
  const ta = document.getElementById('input');
  const msg = ta.value.trim();
  if (!msg) return;
  ta.value = ''; ta.style.height = 'auto';
  document.getElementById('send-btn').disabled = true;

  // agregar al UI
  const messages = document.getElementById('messages');
  messages.innerHTML += `
    <div class="message user">
      <div class="avatar" style="background:#fff;color:#000">M</div>
      <div class="bubble"><div class="text">${escapeHtml(msg)}</div></div>
    </div>
  `;
  messages.innerHTML += `
    <div class="message assistant" id="loading-msg">
      <div class="avatar">⚡</div>
      <div class="bubble"><div class="text">…pensando</div></div>
    </div>
  `;
  messages.scrollTop = messages.scrollHeight;

  const model = currentModel ? `${currentModel.provider}/${currentModel.id}` : '';
  const r = await fetch('/api/send', {
    method: 'POST',
    headers: {'Content-Type':'application/json'},
    body: JSON.stringify({message: msg, model: model, session: currentSession})
  });
  const j = await r.json();
  const lm = document.getElementById('loading-msg');
  if (j.ok && j.text) {
    lm.querySelector('.text').textContent = j.text;
  } else {
    lm.querySelector('.text').textContent = 'Error: ' + (j.error || 'unknown') + (j.text ? '\n' + j.text : '');
  }
  messages.scrollTop = messages.scrollHeight;
}
function escapeHtml(s) {
  return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}

// mantener foco en input
document.getElementById('input').addEventListener('input', e => autoResize(e.target));
</script>
</body>
</html>
"""


class Handler(BaseHTTPRequestHandler):
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

    def do_GET(self):
        path = self.path.split("?")[0]
        if path in ("/", "/index.html"):
            self._ok(HTML, "text/html; charset=utf-8")
        elif path == "/api/models":
            r = get_oc().call("models.list", {})
            # si la respuesta viene con ok=true pero models vacio, fallback a config
            if r.get("ok") and r.get("payload", {}).get("models"):
                self._ok(r)
            else:
                # fallback: devolver hardcoded
                self._ok({"ok": True, "payload": {"models": [
                    {"id": "gemma-4-31b", "name": "Gemma 4", "provider": "cerebras"},
                    {"id": "MiniMax-M3", "name": "MiniMax M3", "provider": "minimax"},
                    {"id": "MiniMax-M2.5", "name": "MiniMax M2.5", "provider": "minimax"},
                    {"id": "openai/gpt-oss-120b", "name": "OSS GPT 120B", "provider": "nvidia-maxbry"},
                    {"id": "openai/gpt-oss-120b", "name": "OSS GPT 120B", "provider": "nvidia-briseida"},
                    {"id": "openai/gpt-oss-120b", "name": "OSS GPT 120B", "provider": "groq"},
                ]}})
        elif path == "/api/health":
            try:
                oc = get_oc()
                self._ok({"ok": True, "openclaw_ws_connected": oc.sock is not None})
            except Exception as e:
                self._ok({"ok": False, "error": str(e)})
        else:
            self._ok({"error": "not found"}, "application/json")

    def do_POST(self):
        path = self.path.split("?")[0]
        cl = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(cl).decode()) if cl else {}
        if path == "/api/send":
            msg = body.get("message", "")
            session = body.get("session", "agent:main:main")
            if not msg:
                self._ok({"ok": False, "error": "no message"})
                return
            r = get_oc().chat_send(msg, session=session, timeout=30)
            self._ok(r)
        elif path == "/api/anchor":
            title = body.get("title", "untitled")
            content = body.get("content", "")
            kind = body.get("kind", "document")
            anchor_id = uuid.uuid4().hex[:8]
            subdir = "documents" if kind == "document" else "skills"
            os.makedirs(os.path.join(ANCHORS_DIR, subdir), exist_ok=True)
            path_full = os.path.join(ANCHORS_DIR, subdir, f"{anchor_id}.md")
            with open(path_full, "w") as f:
                f.write(f"# {title}\n\n{content}\n")
            os.chmod(path_full, 0o600)
            self._ok({"ok": True, "id": anchor_id, "path": path_full})
        else:
            self._ok({"error": "not found"})


class ThreadedServer(ThreadingMixIn, HTTPServer):
    allow_reuse_address = True
    daemon_threads = True


if __name__ == "__main__":
    print(f"Clawd Panel v2 arrancando en :{PANEL_PORT}", flush=True)
    try: get_oc()
    except Exception as e: print(f"WARN: {e}", flush=True)
    srv = ThreadedServer(("0.0.0.0", PANEL_PORT), Handler)
    print(f"Clawd Panel v2 LISTO en :{PANEL_PORT}", flush=True)
    srv.serve_forever()
root@vmi3428294:~# echo 