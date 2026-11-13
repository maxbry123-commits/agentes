'use strict';
// Shared plumbing for the scripts/ci/ verifiers: locate the built artifact, launch it, read its backend.log, kill it cleanly. Helpers throw on misuse; callers own pass/fail.

const fs = require('fs');
const os = require('os');
const path = require('path');
const http = require('http');
const { spawn, execSync } = require('child_process');

// This file is scripts/ci/lib/ -> repo root is three up.
const REPO_ROOT = path.resolve(__dirname, '..', '..', '..');

function packagedAppPath(explicit) {
  if (explicit) return explicit;
  const dist = path.join(REPO_ROOT, 'electron', 'dist');
  const candidates = process.platform === 'win32'
    ? [path.join(dist, 'win-unpacked', 'OpenSwarm.exe')]
    : process.platform === 'darwin'
      ? ['mac-arm64', 'mac', 'mac-universal'].map((d) => path.join(dist, d, 'OpenSwarm.app', 'Contents', 'MacOS', 'OpenSwarm'))
      : [path.join(dist, 'linux-unpacked', 'openswarm')];
  const found = candidates.find((c) => { try { return fs.statSync(c).isFile(); } catch { return false; } });
  if (!found) throw new Error(`packaged app not found; build first or pass --app. Looked in:\n  ${candidates.join('\n  ')}`);
  return found;
}

// The on-disk thing the OS signs/scans: the .exe on win, the .app bundle on mac.
function signableTarget(appExecutable) {
  if (process.platform === 'darwin') {
    const i = appExecutable.indexOf('.app');
    return i === -1 ? appExecutable : appExecutable.slice(0, i + 4);
  }
  return appExecutable;
}

function backendLogPath() {
  if (process.platform === 'darwin') return path.join(os.homedir(), 'Library', 'Application Support', 'OpenSwarm', 'data', 'backend.log');
  if (process.platform === 'win32') return path.join(process.env.APPDATA || os.homedir(), 'OpenSwarm', 'data', 'backend.log');
  const xdg = process.env.XDG_DATA_HOME || path.join(os.homedir(), '.local', 'share');
  return path.join(xdg, 'OpenSwarm', 'data', 'backend.log');
}

// The bearer token the shell writes before bind; tests reuse it to call the authed API.
function authTokenPath() {
  const dir = path.dirname(backendLogPath());
  return path.join(dir, 'auth.token');
}

function gitHeadShort() {
  try { return execSync('git rev-parse HEAD', { cwd: REPO_ROOT }).toString().trim().slice(0, 12); } catch { return null; }
}

function readFileSafe(p) { try { return fs.readFileSync(p, 'utf8'); } catch { return ''; } }
function sleep(ms) { return new Promise((r) => setTimeout(r, ms)); }

function spawnApp(appPath, extraArgs = []) {
  // detached on posix so we can SIGKILL the whole process group (python + 9router children); on win we reap by image name.
  return spawn(appPath, extraArgs, { detached: process.platform !== 'win32', stdio: 'ignore', cwd: path.dirname(appPath) });
}

function killApp(child) {
  try {
    if (process.platform === 'win32') {
      if (child && child.pid) { try { execSync(`taskkill /PID ${child.pid} /T /F`, { stdio: 'ignore' }); } catch { /* gone */ } }
      try { execSync('taskkill /IM OpenSwarm.exe /T /F', { stdio: 'ignore' }); } catch { /* none */ }
    } else if (child && child.pid) {
      try { process.kill(-child.pid, 'SIGKILL'); } catch { try { child.kill('SIGKILL'); } catch { /* gone */ } }
    }
  } catch { /* best effort */ }
}

function healthCode(port, timeoutMs = 3000) {
  return new Promise((resolve) => {
    const req = http.get({ host: '127.0.0.1', port, path: '/api/health/check' }, (res) => { res.resume(); resolve(res.statusCode); });
    req.on('error', () => resolve(0));
    req.setTimeout(timeoutMs, () => { req.destroy(); resolve(0); });
  });
}

// Authenticated JSON call to the running backend; returns { status, json, text } (status 0 = never completed).
function apiRequest(port, { method = 'GET', path = '/', token = '', body = null, timeoutMs = 30000 } = {}) {
  return new Promise((resolve) => {
    const data = body != null ? Buffer.from(JSON.stringify(body)) : null;
    const headers = {};
    if (token) headers.Authorization = `Bearer ${token}`;
    if (data) { headers['Content-Type'] = 'application/json'; headers['Content-Length'] = data.length; }
    const req = http.request({ host: '127.0.0.1', port, path, method, headers }, (res) => {
      let buf = '';
      res.on('data', (c) => { buf += c; });
      res.on('end', () => { let json = null; try { json = JSON.parse(buf); } catch { /* non-json */ } resolve({ status: res.statusCode, json, text: buf }); });
    });
    req.on('error', () => resolve({ status: 0, json: null, text: '' }));
    req.setTimeout(timeoutMs, () => { req.destroy(); resolve({ status: 0, json: null, text: '' }); });
    if (data) req.write(data);
    req.end();
  });
}

// Reuse an already-running app (the user's logged-in creds): read the token + last logged port and confirm it answers. Returns { port, token } or null.
async function attachToRunning() {
  const token = readFileSafe(authTokenPath()).trim();
  const m = readFileSafe(backendLogPath()).match(/Backend ready on port (\d+)/g);
  if (!token || !m) return null;
  const port = Number(m[m.length - 1].match(/(\d+)/)[1]);   // last = most recent launch
  if (!port) return null;
  const code = await healthCode(port);
  return code === 200 ? { port, token } : null;
}

function parseProvenanceSha(log) {
  const m = log.match(/\[provenance\] OpenSwarm \S+ sha=([0-9a-f]+)/);
  return m ? m[1] : null;
}

function parsePerfMarks(log) {
  const marks = {};
  for (const key of ['app-launch', 'first-paint', 'backend-http-ready']) {
    const m = log.match(new RegExp(`\\[perf\\] ${key} t=(\\d+)`));
    if (m) marks[key] = Number(m[1]);
  }
  return marks;
}

// Pure, mutation-testable verdict on a backend.log (provenance == HEAD, perf marks present/ordered/non-degenerate); returns { failures, sha, marks }, empty failures == passed.
function bootFailures({ log, headShort } = {}) {
  const failures = [];
  const sha = parseProvenanceSha(log || '');
  if (!sha) failures.push('no [provenance] line in backend.log');
  else if (headShort && sha !== headShort) failures.push(`provenance sha ${sha} != git HEAD ${headShort}`);

  const marks = parsePerfMarks(log || '');
  const missing = ['app-launch', 'first-paint', 'backend-http-ready'].filter((k) => !(k in marks));
  if (missing.length) missing.forEach((k) => failures.push(`missing [perf] ${k}`));
  else {
    if (!(marks['app-launch'] <= marks['first-paint'] && marks['first-paint'] <= marks['backend-http-ready'])) {
      failures.push(`[perf] marks out of order: ${JSON.stringify(marks)}`);
    }
    if (!(marks['backend-http-ready'] > 0)) failures.push('[perf] backend-http-ready not > 0 (degenerate marks)');
  }
  return { failures, sha, marks };
}

// Launch the app and poll backend.log until HTTP-ready (or time out); returns { child, log, port }. Caller calls killApp.
async function launchAndWait({ appPath, timeoutMs = 180000, freshLog = true } = {}) {
  const logPath = backendLogPath();
  if (freshLog) {
    try { fs.mkdirSync(path.dirname(logPath), { recursive: true }); } catch { /* exists */ }
    try { fs.unlinkSync(logPath); } catch { /* none */ }
  }
  const child = spawnApp(appPath);
  let launchError = null;
  child.on('error', (e) => { launchError = e; });

  const deadline = Date.now() + timeoutMs;
  let log = '';
  let port = 0;
  while (Date.now() < deadline) {
    if (launchError) throw new Error(`could not launch app: ${launchError.message}`);
    log = readFileSafe(logPath);
    const m = log.match(/Backend ready on port (\d+)/);
    if (m) port = Number(m[1]);
    if (/\[perf\] backend-http-ready/.test(log)) break;
    await sleep(1000);
  }
  return { child, log, port, logPath };
}

module.exports = {
  REPO_ROOT,
  packagedAppPath,
  signableTarget,
  backendLogPath,
  authTokenPath,
  gitHeadShort,
  readFileSafe,
  sleep,
  spawnApp,
  killApp,
  healthCode,
  apiRequest,
  attachToRunning,
  parseProvenanceSha,
  parsePerfMarks,
  bootFailures,
  launchAndWait,
};
