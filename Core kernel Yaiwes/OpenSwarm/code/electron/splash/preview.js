// Standalone splash preview — opens the splash window in isolation and
// cycles through every status state so you can eyeball the UI without
// running the full backend + frontend + electron stack.
//
// Run from the electron/ dir:
//   npx electron splash/preview.js
//
// Cycle (~26s total, then idles on the error state with action buttons):
//   0s   "Starting OpenSwarm…"
//   3s   "Connecting to dev backend…"
//   6s   "Loading components…"
//   9s   "Almost ready…"
//  12s   "Still starting (warning, no actions)"
//  18s   "Backend taking too long" (with View Logs / Restart / Quit buttons)
//  24s   error state: "OpenSwarm couldn't start" + last lines of stderr

const { app, BrowserWindow, ipcMain, shell } = require('electron');
const fs = require('fs');
const path = require('path');

let splashWindow = null;

function loadSplashDataUrl() {
  const html = fs.readFileSync(path.join(__dirname, 'splash.html'), 'utf8');
  const iconPath = path.join(__dirname, '..', 'build', 'icon.png');
  const iconBytes = fs.readFileSync(iconPath);
  const iconDataUrl = 'data:image/png;base64,' + iconBytes.toString('base64');
  const finalHtml = html.replace('__OPENSWARM_LOGO__', iconDataUrl);
  return 'data:text/html;charset=utf-8;base64,' + Buffer.from(finalHtml).toString('base64');
}

function emit(payload) {
  if (splashWindow && !splashWindow.isDestroyed()) {
    splashWindow.webContents.send('splash:status', payload);
    const txt = typeof payload === 'string' ? payload : payload.text;
    console.log(`[preview] -> ${txt}`);
  }
}

ipcMain.on('splash:action', (_e, action) => {
  console.log(`[preview] splash button clicked: ${action}`);
  if (action === 'quit') app.quit();
  else if (action === 'restart') { app.relaunch(); app.exit(0); }
  else if (action === 'open-logs') console.log('[preview] (would open log dir)');
});

app.whenReady().then(() => {
  splashWindow = new BrowserWindow({
    width: 460,
    height: 340,
    frame: false,
    resizable: false,
    skipTaskbar: false,   // keep visible in taskbar for the preview
    show: true,
    center: true,
    backgroundColor: '#0a0a10',
    title: 'OpenSwarm splash preview',
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false,
      sandbox: false,
      backgroundThrottling: false,
    },
  });
  splashWindow.setMenuBarVisibility(false);
  splashWindow.loadURL(loadSplashDataUrl());

  // Cycle through every state with delays so you can see each one.
  splashWindow.webContents.once('did-finish-load', () => {
    setTimeout(() => emit('Starting OpenSwarm…'),                          0);
    setTimeout(() => emit('Connecting to dev backend…'),                3000);
    setTimeout(() => emit('Loading components…'),                       6000);
    setTimeout(() => emit('Almost ready…'),                             9000);
    // Mirror the OS-tailored copy from main.js so the preview shows what
    // real users would see on this platform.
    const stillStarting = process.platform === 'win32'
      ? 'Still starting — Windows Defender is scanning files (first launch only)…'
      : process.platform === 'darwin'
        ? 'Still starting — macOS is verifying the bundle (first launch only)…'
        : 'Still starting (first launch is slower than subsequent launches)…';
    const takingTooLong = process.platform === 'win32'
      ? 'Backend is taking longer than usual. Defender scans of 14k files can take a few minutes on slow drives.'
      : process.platform === 'darwin'
        ? 'Backend is taking longer than usual. macOS first-launch checks can be slow on cold cache.'
        : 'Backend is taking longer than usual. You can wait, view logs, or restart.';
    setTimeout(() => emit({ text: stillStarting, level: 'warning' }),  12000);
    setTimeout(() => emit({
      text: takingTooLong,
      level: 'warning',
      showActions: true,
      logs: '[backend] uvicorn warming up...\n[backend] importing claude_agent_sdk...\n[backend] (still working)',
    }),                                                                18000);
    setTimeout(() => emit({
      text: "OpenSwarm couldn't start: Backend process exited with code 1 during startup",
      level: 'error',
      showActions: true,
      logs: '[backend] Traceback (most recent call last):\n[backend]   File "backend/main.py", line 48\n[backend] ImportError: simulated failure for splash preview',
    }),                                                                24000);
  });

  splashWindow.on('closed', () => { app.quit(); });
});
