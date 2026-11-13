# Task #10 — validate the winv2 changes on the REAL signed Windows build

Do not call winv2 "done" until a **code-signed, downloaded, installed, launched**
build passes this. Unit tests + dry-runs are necessary but not sufficient — the
build-script changes (asar exclusion, node_modules pre-extract) and the cold-start
wins only exist in a packaged EXE.

## 0. Produce the signed build
- Tag the winv2 HEAD and push: `git tag v1.3.86 && git push origin v1.3.86`.
- This runs `.github/workflows/release-windows.yml` (Azure code-signing) and creates
  a **draft** GitHub release (drafts do NOT auto-update existing users).
- Watch it: `gh run watch` / `gh run list --workflow=release-windows.yml`.
- If `build-app-win.ps1` errors on the new step 4b (pre-extract) or the asar
  `files` exclusion, fix and re-tag (delete the draft + tag first; never force-push
  an existing release tag).

## 1. Download + verify the signature (must be real signed bits)
- `gh release download v1.3.86 --pattern "*Setup*.exe" --dir .` (or from the draft release page).
- Verify Authenticode: `Get-AuthenticodeSignature .\OpenSwarm-Setup-x64.exe` → Status must be `Valid`, signer = the Azure Trusted Signing cert. NOT "NotSigned"/"UnknownError".

## 2. Install + first (COLD) launch — the headline metric
- Install the downloaded EXE (Squirrel → `%LOCALAPPDATA%\openswarm`).
- Launch once and let it fully load. This is the COLD launch (Defender scans fresh files).
- Then run the automated checker: `pwsh docs/perf/winv2/validate_packaged.ps1`.
- Acceptance (perf): cold `backend-http-ready` should be **far below the 54-138s baseline**
  (target: well under the 10s goal even cold, given the 639MB asar read is gone +
  fewer files to scan). Relaunch once for the warm number (target ~2-3s).

## 3. Automated structural checks (validate_packaged.ps1 must be all PASS)
- app.asar < 50 MB (was ~607 MB) — #9 item 4.
- app.asar does NOT contain python-env / build-staging — #9 item 4.
- `resources/python-env/python.exe` present (still shipped unpacked).
- `resources/node/x64/node.exe` present.
- `resources/backend/apps/skill_registry/skills_snapshot.json` present — Bug #1.
- webapp_template_cache has a pre-extracted `<digest>/node_modules/vite/bin/vite.js`
  (#9 item 2) — or a `.tar.gz` fallback.

## 4. Manual GUI checks (can't be automated)
- **Skills (Bug #1):** open the Skills page on a fresh launch → the catalog shows
  immediately (NOT empty). Run onboarding step 6/8 "Install a skill" → it finds the
  pdf skill (no `waitForSelector "skill-item-pdf" 15000ms` timeout).
- **App Builder (Bug #2):** create an app → the preview goes LIVE. No `[WinError 2]`,
  no "backend exited with code 1". First app should be quick (pre-extracted nm + vite).
  Bonus: test on a machine WITHOUT Git Bash to confirm the no-bash vite path.
- Sanity: send an agent message (9Router now starts in the background → first message
  may wait a moment for it; confirm it still answers).

## 5. Optional cold-start levers (only after 1-4 pass)
- #9 item 1 (`zip-python-stdlib.ps1 -Apply`) and item 3 (`strip-py-to-pyc.ps1 -Apply`)
  on a build copy, then re-run 1-4 + re-measure. Enable in the build only if green.
- #9 item 5 (`add-defender-exclusion.ps1`) is a user opt-in, validate separately.

## 6. Sign-off
- All of 1-4 green on the signed build → publish the draft release (un-draft) to ship 1.3.86.
- Record the real cold/warm numbers in `boot_breakdown.csv` / README "Results (AFTER)".
