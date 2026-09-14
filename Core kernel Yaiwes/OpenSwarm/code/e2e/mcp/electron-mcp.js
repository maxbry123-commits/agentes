#!/usr/bin/env node
// MCP server giving a Claude Code instance a Playwright hand on the real packaged app (launch/click/type/screenshot/eval/read-log); wraps Electron _electron since @playwright/mcp is browser-only. App held across calls. See e2e/mcp/README.md.

'use strict';
const fs = require('fs');
const os = require('os');
const path = require('path');
const { _electron } = require('@playwright/test');
const { Server } = require('@modelcontextprotocol/sdk/server/index.js');
const { StdioServerTransport } = require('@modelcontextprotocol/sdk/server/stdio.js');
const { ListToolsRequestSchema, CallToolRequestSchema } = require('@modelcontextprotocol/sdk/types.js');

const REPO_ROOT = path.resolve(__dirname, '..', '..');

function packagedAppPath(explicit) {
  if (explicit) return explicit;
  if (process.env.E2E_APP_PATH) return process.env.E2E_APP_PATH;
  const dist = path.join(REPO_ROOT, 'electron', 'dist');
  const candidates = process.platform === 'win32'
    ? [path.join(dist, 'win-unpacked', 'OpenSwarm.exe')]
    : process.platform === 'darwin'
      ? ['mac-arm64', 'mac', 'mac-universal'].map((d) => path.join(dist, d, 'OpenSwarm.app', 'Contents', 'MacOS', 'OpenSwarm'))
      : [path.join(dist, 'linux-unpacked', 'openswarm')];
  const found = candidates.find((c) => { try { return fs.statSync(c).isFile(); } catch { return false; } });
  if (!found) throw new Error(`packaged app not found; build first or pass appPath. Looked in:\n  ${candidates.join('\n  ')}`);
  return found;
}

function backendLogPath() {
  if (process.platform === 'darwin') return path.join(os.homedir(), 'Library', 'Application Support', 'OpenSwarm', 'data', 'backend.log');
  if (process.platform === 'win32') return path.join(process.env.APPDATA || os.homedir(), 'OpenSwarm', 'data', 'backend.log');
  const xdg = process.env.XDG_DATA_HOME || path.join(os.homedir(), '.local', 'share');
  return path.join(xdg, 'OpenSwarm', 'data', 'backend.log');
}

let app = null;   // ElectronApplication
let page = null;  // main Page

async function findMainWindow(timeoutMs = 120000) {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    for (const w of app.windows()) {
      try {
        const ready = await w.evaluate(() => {
          const hasBridge = typeof window.openswarm?.getBackendPort === 'function';
          const root = document.getElementById('root');
          return hasBridge && !!root && root.childElementCount > 0;
        });
        if (ready) return w;
      } catch { /* navigating */ }
    }
    await new Promise((r) => setTimeout(r, 500));
  }
  throw new Error('main window with a mounted React root never appeared');
}

function text(s) { return { content: [{ type: 'text', text: typeof s === 'string' ? s : JSON.stringify(s, null, 2) }] }; }
function err(s) { return { content: [{ type: 'text', text: `ERROR: ${s}` }], isError: true }; }
function needPage() { if (!page) throw new Error('no app open; call app_launch first'); }

const TOOLS = [
  { name: 'app_launch', description: 'Launch the packaged OpenSwarm app and wait for the main window. Returns backend port + build provenance.', inputSchema: { type: 'object', properties: { appPath: { type: 'string', description: 'Optional explicit path to the packaged binary' } } } },
  { name: 'app_close', description: 'Close the running app.', inputSchema: { type: 'object', properties: {} } },
  { name: 'screenshot', description: 'Capture a PNG screenshot of the current main window (what a user would see).', inputSchema: { type: 'object', properties: { fullPage: { type: 'boolean' } } } },
  { name: 'snapshot', description: 'Return the accessibility tree of the page (structured "what is on screen" without pixels).', inputSchema: { type: 'object', properties: {} } },
  { name: 'click', description: 'Click an element by Playwright selector (CSS, text=..., role=..., etc.).', inputSchema: { type: 'object', properties: { selector: { type: 'string' } }, required: ['selector'] } },
  { name: 'fill', description: 'Type text into an input/textarea by selector (clears first).', inputSchema: { type: 'object', properties: { selector: { type: 'string' }, text: { type: 'string' } }, required: ['selector', 'text'] } },
  { name: 'press', description: 'Press a keyboard key (e.g. Enter, Escape, Control+A) on the focused element.', inputSchema: { type: 'object', properties: { key: { type: 'string' } }, required: ['key'] } },
  { name: 'wait_for', description: 'Wait until a selector is visible (default 30s).', inputSchema: { type: 'object', properties: { selector: { type: 'string' }, timeoutMs: { type: 'number' } }, required: ['selector'] } },
  { name: 'eval', description: 'Evaluate a JS expression in the renderer and return the JSON result (powerful: inspect anything, incl. window.openswarm).', inputSchema: { type: 'object', properties: { expression: { type: 'string' } }, required: ['expression'] } },
  { name: 'read_log', description: 'Return the tail of the app backend.log (provenance + [perf] marks + errors land here).', inputSchema: { type: 'object', properties: { tailLines: { type: 'number' } } } },
];

async function handle(name, a) {
  if (name === 'app_launch') {
    if (app) { try { await app.close(); } catch { /* */ } app = null; page = null; }
    app = await _electron.launch({ executablePath: packagedAppPath(a.appPath), args: [] });
    page = await findMainWindow();
    const info = await page.evaluate(async () => ({
      port: window.openswarm.getBackendPort ? await window.openswarm.getBackendPort() : null,
      build: window.openswarm.getBuildInfo ? await window.openswarm.getBuildInfo() : null,
    }));
    return text({ launched: true, ...info });
  }
  if (name === 'app_close') {
    if (app) { try { await app.close(); } catch { /* */ } }
    app = null; page = null;
    return text('closed');
  }
  if (name === 'screenshot') { needPage(); const buf = await page.screenshot({ fullPage: !!a.fullPage }); return { content: [{ type: 'image', data: buf.toString('base64'), mimeType: 'image/png' }] }; }
  if (name === 'snapshot') { needPage(); return text(await page.accessibility.snapshot()); }
  if (name === 'click') { needPage(); await page.click(a.selector, { timeout: 15000 }); return text(`clicked ${a.selector}`); }
  if (name === 'fill') { needPage(); await page.fill(a.selector, a.text, { timeout: 15000 }); return text(`filled ${a.selector}`); }
  if (name === 'press') { needPage(); await page.keyboard.press(a.key); return text(`pressed ${a.key}`); }
  if (name === 'wait_for') { needPage(); await page.waitForSelector(a.selector, { state: 'visible', timeout: a.timeoutMs || 30000 }); return text(`visible: ${a.selector}`); }
  if (name === 'eval') { needPage(); const r = await page.evaluate((expr) => eval(expr), a.expression); return text(r === undefined ? 'undefined' : r); }
  if (name === 'read_log') {
    const raw = (() => { try { return fs.readFileSync(backendLogPath(), 'utf8'); } catch { return ''; } })();
    const lines = raw.split(/\r?\n/);
    const n = a.tailLines || 80;
    return text(lines.slice(-n).join('\n') || '(backend.log empty or missing)');
  }
  throw new Error(`unknown tool ${name}`);
}

async function main() {
  const server = new Server({ name: 'openswarm-gui', version: '0.1.0' }, { capabilities: { tools: {} } });
  server.setRequestHandler(ListToolsRequestSchema, async () => ({ tools: TOOLS }));
  server.setRequestHandler(CallToolRequestSchema, async (req) => {
    try { return await handle(req.params.name, req.params.arguments || {}); }
    catch (e) { return err(e && e.message || String(e)); }
  });
  process.on('exit', () => { try { app && app.close(); } catch { /* */ } });
  await server.connect(new StdioServerTransport());
}

main().catch((e) => { process.stderr.write(`electron-mcp fatal: ${e && e.stack || e}\n`); process.exit(1); });
