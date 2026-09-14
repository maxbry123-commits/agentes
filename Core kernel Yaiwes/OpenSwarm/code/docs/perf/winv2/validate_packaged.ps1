<#
.SYNOPSIS
  Task #10 automated checks: run AFTER installing the signed build. Confirms the
  winv2 structural fixes landed in the packaged app and reads the REAL cold/warm
  backend-http-ready from the app's own perf log. Manual GUI checks are in
  TASK10_CHECKLIST.md (App Builder preview, Skills list, onboarding).
.USAGE
  pwsh docs\perf\winv2\validate_packaged.ps1
#>
param(
    [string]$InstallRoot = (Join-Path $env:LOCALAPPDATA 'openswarm'),
    [string]$BackendLog = (Join-Path $env:APPDATA 'openswarm\data\backend.log')
)
$ErrorActionPreference = 'Stop'
$pass = 0; $fail = 0
function ok($m) { Write-Host "  PASS  $m" -ForegroundColor Green; $script:pass++ }
function bad($m) { Write-Host "  FAIL  $m" -ForegroundColor Red; $script:fail++ }
function info($m) { Write-Host "  ..    $m" -ForegroundColor DarkGray }

$app = Get-ChildItem $InstallRoot -Directory -Filter 'app-*' -EA SilentlyContinue | Sort-Object Name | Select-Object -Last 1
if (-not $app) { throw "no app-* under $InstallRoot (install the build first)" }
$res = Join-Path $app.FullName 'resources'
Write-Host "Validating packaged build: $res`n"

# #9 item 4: asar trimmed
$asar = Join-Path $res 'app.asar'
if (Test-Path $asar) {
    $asarMB = [math]::Round((Get-Item $asar).Length / 1MB, 1)
    if ($asarMB -lt 50) { ok "app.asar = ${asarMB} MB (trimmed; was ~607 MB)" } else { bad "app.asar = ${asarMB} MB (expected < 50)" }
    $insp = Join-Path $PSScriptRoot 'inspect_asar.js'
    if ((Get-Command node -EA SilentlyContinue) -and (Test-Path $insp)) {
        $out = & node $insp $asar 2>&1 | Out-String
        if ($out -match 'python-env|build-staging') { bad "asar STILL contains python-env/build-staging" } else { ok "asar excludes python-env + build-staging" }
    }
} else { bad "app.asar not found" }

# still shipped unpacked (runtime reads these)
if (Test-Path (Join-Path $res 'python-env\python.exe')) { ok "python-env shipped unpacked" } else { bad "python-env\python.exe missing" }
if (Test-Path (Join-Path $res 'node\x64\node.exe')) { ok "node bundled" } else { bad "node\x64\node.exe missing" }

# Bug #1: skills snapshot
if (Test-Path (Join-Path $res 'backend\apps\skill_registry\skills_snapshot.json')) { ok "skills snapshot shipped (catalog never empty)" } else { bad "skills_snapshot.json missing" }

# #9 item 2 / Bug #2: webapp node_modules pre-extracted or archive
$cache = Join-Path $res 'backend\apps\outputs\webapp_template_cache'
if (Test-Path (Join-Path $cache '*\node_modules\vite\bin\vite.js')) { ok "webapp node_modules PRE-EXTRACTED (zero first-app extract)" }
elseif (Test-Path (Join-Path $cache 'node_modules.*.tar.gz')) { info "webapp node_modules shipped as .tar.gz (extract path, not pre-extracted)" }
else { bad "no webapp node_modules tree/archive in resources" }

# perf: real cold/warm backend-http-ready from the app's own log
if (Test-Path $BackendLog) {
    $m = Select-String -Path $BackendLog -Pattern 'backend-http-ready t=(\d+)' -AllMatches
    $vals = @($m.Matches | ForEach-Object { [int]$_.Groups[1].Value })
    if ($vals.Count) {
        $recent = ($vals | Select-Object -Last 6 | ForEach-Object { [math]::Round($_ / 1000, 1) }) -join 's, '
        info "backend-http-ready recent: ${recent}s   (baseline: warm ~9-10s, cold 54-138s)"
        info "latest: $([math]::Round($vals[-1]/1000,1))s  -- first launch after install = COLD; relaunch for warm"
    } else { info "no backend-http-ready markers yet" }
} else { info "no backend.log yet (launch the app once first)" }

Write-Host "`n$pass passed, $fail failed. Manual GUI checks: TASK10_CHECKLIST.md (App Builder, Skills, onboarding)."
if ($fail) { exit 1 }
