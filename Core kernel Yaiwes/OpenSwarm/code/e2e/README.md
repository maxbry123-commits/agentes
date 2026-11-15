# End-to-end tests (packaged app, macOS + Windows)

Playwright tests that launch the **packaged** OpenSwarm desktop app (the real
built binary, asar + bundled python-env + real paths) and drive it the way a user
would. The same specs run unchanged on macOS and Windows; CI builds the artifact
per-OS, then runs these. No provider API key is needed (no agent turn), so the
suite is hermetic and deterministic on a clean machine.

## What it checks (per OS)

- Main window paints the React shell (first meaningful paint).
- The preload bridge (`window.openswarm`) is exposed.
- The real backend the app spawned reaches HTTP-ready (`/api/health/check` -> 200).
- Provenance: the running app's `getBuildInfo()` sha matches `electron/build-info.json`.
- App version is reported.

## Run locally

1. Build the app first (produces `electron/dist/...`):
   - Windows: `pwsh scripts/build-app-win.ps1`
   - macOS:   `bash scripts/build-app.sh`
2. Then:
   ```
   cd e2e
   PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1 npm ci   # Electron ships its own Chromium
   npm test
   ```

Override the binary location with `E2E_APP_PATH=/path/to/app` if your build
output lives elsewhere. Auto-detection covers `win-unpacked/OpenSwarm.exe` and the
mac `OpenSwarm.app` variants.

## CI

`.github/workflows/e2e.yml` runs this on a `windows-latest` + `macos-latest`
matrix: it builds the unsigned app, then runs the suite. Tag-driven signed
releases are covered separately by `release-windows.yml` / `release-macos.yml`.
