<#
.SYNOPSIS
  #9 item 3 (DRAFT, build-gated): ship site-packages as sourceless .pyc only, so
  Windows Defender has ~half as many loose files to scan on a cold launch after
  an update. Compiles each module.py -> legacy module.pyc (next to the source,
  NOT in __pycache__), then deletes the .py whose .pyc exists and removes the
  redundant __pycache__ dirs. Python imports the sourceless .pyc directly.

.SCOPE
  TARGET SITE-PACKAGES ONLY by default. Do NOT strip the backend app code: the
  swarm-debug debugger reads our own .py source for frame annotation, and we want
  readable tracebacks for first-party code. Stdlib is handled by #9 item 1
  (zip-python-stdlib.ps1); this is the dependency tree.

.STATUS
  UNVALIDATED. Default is -DryRun (reports only). The .pyc magic must match the
  SHIPPED interpreter, so compile with the bundled python (-PythonExe). Some
  packages read their own source (inspect.getsource) and break sourceless; keep
  a keep-list and validate on a packaged EXE (Task #10) BEFORE wiring into a
  release. Intentionally NOT called by build-app-win.ps1 yet.

.USAGE
  pwsh scripts\strip-py-to-pyc.ps1 -TargetDir electron\python-env\Lib\site-packages            # dry run
  pwsh scripts\strip-py-to-pyc.ps1 -TargetDir <copy>\site-packages -PythonExe <env>\python.exe -Apply
#>
param(
    [Parameter(Mandatory = $true)][string]$TargetDir,
    [string]$PythonExe,
    [switch]$Apply
)

$ErrorActionPreference = 'Stop'
if (-not (Test-Path $TargetDir)) { throw "no target dir: $TargetDir" }

# Packages that read their own .py at runtime (inspect.getsource / exec of source
# / .py-relative data) -> keep their source. Conservative starting set; expand
# whatever validation flags. Matched against the top-level package dir name.
$KeepSource = @('pip', 'setuptools', 'pkg_resources', '_distutils_hack')

$allPy = Get-ChildItem -Recurse -File $TargetDir -Filter *.py -ErrorAction SilentlyContinue
$py = $allPy | Where-Object {
    $rel = $_.FullName.Substring($TargetDir.Length).TrimStart('\', '/')
    $top = ($rel -split '[\\/]')[0]
    $KeepSource -notcontains $top
}
$pyCount = ($py | Measure-Object).Count
$pyMB = [math]::Round((($py | Measure-Object -Property Length -Sum).Sum) / 1MB, 1)
$pycacheDirs = (Get-ChildItem -Recurse -Directory $TargetDir -Filter __pycache__ -ErrorAction SilentlyContinue | Measure-Object).Count
Write-Host ("#9 item 3: {0} .py files ({1} MB) eligible under {2}" -f $pyCount, $pyMB, $TargetDir)
Write-Host ("keep-source packages: {0} | __pycache__ dirs present: {1}" -f ($KeepSource -join ', '), $pycacheDirs)

if (-not $Apply) {
    Write-Host "DRY RUN. -Apply compiles to legacy .pyc (compileall -b) next to each source,"
    Write-Host "deletes each .py whose .pyc now exists, and removes __pycache__. Validate (Task #10):"
    Write-Host "  1. python.exe -c 'import backend.main' resolves (deps import sourceless)"
    Write-Host "  2. boot the packaged backend; exercise agents/app-builder/skills/MCP"
    Write-Host "  3. measure cold backend-http-ready vs baseline_startup.csv"
    return
}

if (-not $PythonExe) { throw "-PythonExe is required for -Apply (must be the SHIPPED interpreter; .pyc magic must match)" }
if (-not (Test-Path $PythonExe)) { throw "no python at $PythonExe" }

# 1. Compile to legacy sourceless .pyc next to each source (-b). -q quiet; it
#    continues past files that fail to compile (py2-only, optional) -> those keep
#    their .py since no sibling .pyc is produced.
& $PythonExe -m compileall -b -q $TargetDir
# compileall returns nonzero if ANY file failed; that is expected for odd files,
# so we don't treat it as fatal -- we only delete .py that actually got a .pyc.
$global:LASTEXITCODE = 0

# 2. Delete each eligible .py that now has a sibling .pyc.
$deleted = 0
foreach ($f in $py) {
    $pyc = [System.IO.Path]::ChangeExtension($f.FullName, '.pyc')
    if (Test-Path $pyc) { Remove-Item -Force $f.FullName; $deleted++ }
}
# 3. Remove redundant __pycache__ (we use the legacy .pyc next to source).
Get-ChildItem -Recurse -Directory $TargetDir -Filter __pycache__ -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force
Write-Host ("Removed {0} .py (kept {1} that did not compile). UNVALIDATED -- verify on the packaged EXE before shipping." -f $deleted, ($pyCount - $deleted))
