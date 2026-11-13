#Requires -Version 5.1
<#
.SYNOPSIS
    Cognithor One-Liner Bootstrap for Windows.
.DESCRIPTION
    Installs Cognithor from scratch:
      1. Auto-installs Python 3.12 if missing (via winget)
      2. Detects GPU and auto-selects Lite mode if needed
      3. Clones repo (if not already in one) or uses current directory
      4. Creates venv in ~/.cognithor/venv/
      5. Installs dependencies via pip (with visible progress)
      6. Auto-installs Ollama if missing (via winget)
      7. Pulls models based on GPU capacity
      8. Initializes directory structure
      9. Runs smoke test
.PARAMETER Lite
    Force lite mode (qwen3:8b only, 6 GB VRAM). Auto-detected if GPU < 12 GB.
.PARAMETER Full
    Install all features including voice and PostgreSQL.
.PARAMETER Minimal
    Install core only (no web, no telegram).
.EXAMPLE
    # Run from cloned repo:
    .\install.ps1
    .\install.ps1 -Lite

    # One-liner from anywhere:
    irm https://raw.githubusercontent.com/Alex8791-cyber/cognithor/main/install.ps1 | iex
#>
param(
    [switch]$Lite,
    [switch]$Full,
    [switch]$Minimal
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

# ── Banner ────────────────────────────────────────────────────────────────
function Show-Banner {
    Write-Host ""
    Write-Host "   ____  ___   ____ _   _ ___ _____ _   _  ___  ____" -ForegroundColor Cyan
    Write-Host "  / ___|/ _ \ / ___| \ | |_ _|_   _| | | |/ _ \|  _ \" -ForegroundColor Cyan
    Write-Host " | |   | | | | |  _|  \| || |  | | | |_| | | | | |_) |" -ForegroundColor Cyan
    Write-Host " | |___| |_| | |_| | |\  || |  | | |  _  | |_| |  _ <" -ForegroundColor Cyan
    Write-Host "  \____|\___/ \____|_| \_|___| |_| |_| |_|\___/|_| \_\" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "              -- PowerShell Installer --" -ForegroundColor DarkCyan
    Write-Host ""
}

function Write-OK   { param($Msg) Write-Host "  [OK]      $Msg" -ForegroundColor Green }
function Write-Fail { param($Msg) Write-Host "  [ERROR]   $Msg" -ForegroundColor Red }
function Write-Warn { param($Msg) Write-Host "  [WARNING] $Msg" -ForegroundColor Yellow }
function Write-Info { param($Msg) Write-Host "  [INFO]    $Msg" -ForegroundColor Blue }
function Write-Step { param($Num, $Title)
    Write-Host ""
    Write-Host "  ----------------------------------------------------------" -ForegroundColor DarkGray
    Write-Host "    $Num  $Title" -ForegroundColor White
    Write-Host "  ----------------------------------------------------------" -ForegroundColor DarkGray
}

# ── Configuration ─────────────────────────────────────────────────────────
$JarvisHome = if ($env:COGNITHOR_HOME) { $env:COGNITHOR_HOME } elseif ($env:JARVIS_HOME) { $env:JARVIS_HOME } else { Join-Path $env:USERPROFILE ".cognithor" }
$VenvDir = Join-Path $JarvisHome "venv"
$RepoUrl = "https://github.com/Alex8791-cyber/cognithor.git"
$ForceLite = $Lite.IsPresent

if ($Full) { $InstallExtras = "full" }
elseif ($Minimal) { $InstallExtras = "" }
else { $InstallExtras = "all" }

# ── Main ──────────────────────────────────────────────────────────────────
function Main {
    Show-Banner

    # ── Step 1: Python ────────────────────────────────────────────────
    Write-Step "1/10" "Check Python"
    $python = Find-Python
    if (-not $python) {
        Write-Warn "Python 3.12+ not found. Attempting automatic installation..."

        # Try winget
        $wingetAvailable = $null -ne (Get-Command winget -ErrorAction SilentlyContinue)
        if ($wingetAvailable) {
            Write-Info "Installing Python 3.12 via winget ..."
            Write-Info "(This may take 1-2 minutes.)"
            try {
                & winget install --id Python.Python.3.12 -e --accept-source-agreements --accept-package-agreements --silent 2>&1 | Out-Null
                if ($LASTEXITCODE -eq 0) {
                    Write-OK "Python installed via winget"
                    # Refresh PATH
                    $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
                    $python = Find-Python
                }
            } catch {
                Write-Warn "winget installation failed: $_"
            }
        }

        if (-not $python) {
            Write-Fail "Could not install Python 3.12+!"
            Write-Host ""
            Write-Host "  Please install manually:" -ForegroundColor Yellow
            Write-Host "  https://www.python.org/downloads/" -ForegroundColor Yellow
            Write-Host ""
            Write-Host "  IMPORTANT: Check 'Add Python to PATH'!" -ForegroundColor Yellow
            Write-Host "  Then run this script again." -ForegroundColor Yellow
            return
        }
    }
    $pyVer = & $python --version 2>&1
    Write-OK "$pyVer"

    # ── Step 2: GPU Detection ─────────────────────────────────────────
    Write-Step "2/10" "GPU Detection"
    $gpuInfo = Detect-GPU
    $vramGB = $gpuInfo.VramGB

    if ($vramGB -gt 0) {
        Write-OK "GPU: $($gpuInfo.Name) ($vramGB GB VRAM)"
    } else {
        Write-Info "No NVIDIA GPU detected or nvidia-smi missing."
        Write-Info "CPU mode -- Lite is recommended."
        if (-not $ForceLite) {
            $Lite = $true
            Write-Info "Lite mode automatically enabled."
        }
    }

    # Auto-lite if VRAM < 12 GB
    if ($vramGB -gt 0 -and $vramGB -lt 12 -and -not $ForceLite) {
        $Lite = $true
        Write-Info "VRAM under 12 GB -- Lite mode automatically enabled."
        Write-Info "(qwen3:8b statt qwen3:32b, spart ~14 GB VRAM)"
    }

    if ($vramGB -ge 12 -and -not $Lite) {
        Write-OK "Enough VRAM for standard mode (qwen3:32b)"
    }

    $modeLabel = if ($Lite) { "LITE (6 GB VRAM)" } elseif ($Full) { "FULL" } elseif ($Minimal) { "MINIMAL" } else { "STANDARD" }
    Write-Host ""
    Write-Info "Mode: $modeLabel"
    Write-Info "Home:  $JarvisHome"

    # ── Step 3: Repository ────────────────────────────────────────────
    Write-Step "3/10" "Repository"
    $repoRoot = Find-Or-Clone-Repo $python
    if (-not $repoRoot) {
        Write-Fail "Could not find or clone repository."
        return
    }
    Write-OK "Repo: $repoRoot"

    # ── Step 4: Virtual Environment ───────────────────────────────────
    Write-Step "4/10" "Virtual Environment"
    if (-not (Test-Path (Join-Path $VenvDir "Scripts" "activate.bat"))) {
        Write-Info "Creating venv in $VenvDir ..."
        & $python -m venv $VenvDir
        if ($LASTEXITCODE -ne 0) {
            Write-Fail "Could not create venv!"
            return
        }
        # Upgrade pip
        & (Join-Path $VenvDir "Scripts" "python.exe") -m pip install --upgrade pip setuptools wheel --quiet 2>$null
        Write-OK "venv created"
    } else {
        Write-OK "venv already exists"
    }
    $venvPython = Join-Path $VenvDir "Scripts" "python.exe"

    # ── Step 5: pip install (visible progress) ────────────────────────
    Write-Step "5/10" "Python Dependencies"
    $spec = if ($InstallExtras) { "$repoRoot[$InstallExtras]" } else { "$repoRoot" }
    Write-Info "Installing cognithor[$InstallExtras] ..."
    Write-Info "(This may take 3-5 minutes on first run. Please do not close!)"
    Write-Host ""
    # Show pip output so user sees progress (no --quiet)
    & $venvPython -m pip install -e $spec --disable-pip-version-check --progress-bar on 2>&1 | ForEach-Object {
        $line = $_.ToString().Trim()
        if ($line -and $line -notmatch "^(Requirement already|  |$)") {
            Write-Host "  $line" -ForegroundColor DarkGray
        }
    }
    if ($LASTEXITCODE -ne 0) {
        Write-Fail "pip install failed!"
        Write-Host "  Manually: cd `"$repoRoot`" && pip install -e `".[all]`"" -ForegroundColor Yellow
        return
    }
    Write-OK "Dependencies installed"

    # ── Step 6: Ollama ────────────────────────────────────────────────
    Write-Step "6/10" "Check Ollama"
    $ollamaPath = Find-Ollama
    $ollamaReady = $false

    if (-not $ollamaPath) {
        Write-Warn "Ollama not found."
        $answer = Read-Host "  Install Ollama now via winget? [Y/n]"
        if ($answer -eq "n" -or $answer -eq "no") {
            Write-Host "  Please install manually: https://ollama.com/download" -ForegroundColor Yellow
        } else {
        Write-Info "Installing Ollama via winget ..."
        try {
            & winget install --id Ollama.Ollama -e --accept-source-agreements --accept-package-agreements --silent 2>&1 | Out-Null
            if ($LASTEXITCODE -eq 0) {
                Write-OK "Ollama installed via winget"
                # Refresh PATH
                $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
                $ollamaPath = Find-Ollama
            } else {
                Write-Warn "winget installation failed."
                Write-Host "  Please install manually: https://ollama.com/download" -ForegroundColor Yellow
            }
        } catch {
            Write-Warn "winget not available."
            Write-Host "  Please install Ollama manually: https://ollama.com/download" -ForegroundColor Yellow
        }
        } # end else (user said yes)
    }

    if ($ollamaPath) {
        Write-OK "Ollama: $ollamaPath"
        if (Test-OllamaRunning) {
            Write-OK "Ollama server running"
            $ollamaReady = $true
        } else {
            Write-Info "Starting Ollama server ..."
            Start-Process -FilePath $ollamaPath -ArgumentList "serve" -WindowStyle Hidden
            for ($i = 0; $i -lt 30; $i++) {
                Start-Sleep -Milliseconds 500
                if (Test-OllamaRunning) {
                    Write-OK "Ollama server started"
                    $ollamaReady = $true
                    break
                }
            }
            if (-not $ollamaReady) {
                Write-Warn "Ollama server not responding"
            }
        }
    }

    # ── Step 7: Models ────────────────────────────────────────────────
    Write-Step "7/10" "Ollama Models"
    if ($ollamaReady -and $ollamaPath) {
        if ($Lite) {
            Write-Info "Required models: qwen3:8b, nomic-embed-text"
        } else {
            Write-Info "Required models: qwen3:8b, qwen3:32b, nomic-embed-text"
        }
        $pullAnswer = Read-Host "  Download missing models now? [Y/n]"
        if ($pullAnswer -ne "n" -and $pullAnswer -ne "no") {
            if ($Lite) {
                Ensure-Model "qwen3:8b" $ollamaPath
                Ensure-Model "nomic-embed-text" $ollamaPath
            } else {
                Ensure-Model "qwen3:8b" $ollamaPath
                Ensure-Model "qwen3:32b" $ollamaPath
                Ensure-Model "nomic-embed-text" $ollamaPath
            }
        } else {
            Write-Info "Model download skipped by user."
        }
    } else {
        Write-Warn "Model download skipped (Ollama not ready)"
    }

    # ── Step 8: Init ──────────────────────────────────────────────────
    Write-Step "8/10" "Directory Structure"
    $initArgs = @("-m", "jarvis", "--init-only")
    if ($Lite) { $initArgs += "--lite" }
    & $venvPython $initArgs 2>$null
    if ($LASTEXITCODE -ne 0) {
        @("memory", "logs", "cache") | ForEach-Object {
            $p = Join-Path $JarvisHome $_
            if (-not (Test-Path $p)) { New-Item -ItemType Directory -Path $p -Force | Out-Null }
        }
        Write-OK "Directories created manually"
    } else {
        Write-OK "Directory structure initialized"
    }

    # ── Step 9: Smoke test ────────────────────────────────────────────
    Write-Step "9/10" "Smoke-Test"
    $smokeResult = & $venvPython -c "import cognithor; print(f'cognithor v{cognithor.__version__}')" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-OK "Import OK: $smokeResult"
    } else {
        Write-Fail "Import failed!"
        return
    }

    # ── Step 10: Summary ─────────────────────────────────────────────
    Write-Step "10/10" "Summary"
    Write-Host ""
    Write-OK "Cognithor successfully installed!"
    Write-Host ""
    if ($vramGB -gt 0) {
        Write-Host "  GPU: $($gpuInfo.Name) ($vramGB GB VRAM)" -ForegroundColor Gray
    }
    $modelMode = if ($Lite) { "LITE (qwen3:8b, ~6 GB VRAM)" } else { "STANDARD (qwen3:32b + qwen3:8b)" }
    Write-Host "  Model mode: $modelMode" -ForegroundColor Gray
    Write-Host ""
    Write-Host "  Start:" -ForegroundColor White
    Write-Host "    & `"$venvPython`" -m jarvis                 # CLI" -ForegroundColor Gray
    if ($Lite) {
        Write-Host "    & `"$venvPython`" -m jarvis --lite        # Lite mode" -ForegroundColor Gray
    }
    if (Test-Path (Join-Path $repoRoot "start_cognithor.bat")) {
        Write-Host "    start_cognithor.bat                       # Web-UI" -ForegroundColor Gray
    }
    Write-Host ""
    Write-Host "  Directories:" -ForegroundColor White
    Write-Host "    $JarvisHome\                               Home" -ForegroundColor Gray
    Write-Host "    $JarvisHome\config.yaml                    Configuration" -ForegroundColor Gray
    Write-Host "    $JarvisHome\memory\                        Memory" -ForegroundColor Gray
    Write-Host ""

    Write-Host "  Activate venv (for this shell):" -ForegroundColor White
    Write-Host "    & `"$VenvDir\Scripts\Activate.ps1`"" -ForegroundColor Gray
    Write-Host ""
}

# ── Helper: Find Python ──────────────────────────────────────────────────
function Find-Python {
    # Try python
    $py = Get-Command python -ErrorAction SilentlyContinue
    if ($py) {
        try {
            & python -c "import sys; exit(0 if sys.version_info >= (3,12) else 1)" 2>$null
            if ($LASTEXITCODE -eq 0) { return "python" }
        } catch {}
    }
    # Try py launcher
    $pyLauncher = Get-Command py -ErrorAction SilentlyContinue
    if ($pyLauncher) {
        try {
            & py -c "import sys; exit(0 if sys.version_info >= (3,12) else 1)" 2>$null
            if ($LASTEXITCODE -eq 0) { return "py" }
        } catch {}
    }
    # Try common installation paths after winget install
    $candidates = @(
        (Join-Path $env:LOCALAPPDATA "Programs\Python\Python312\python.exe"),
        (Join-Path $env:LOCALAPPDATA "Programs\Python\Python313\python.exe"),
        (Join-Path $env:ProgramFiles "Python312\python.exe"),
        (Join-Path $env:ProgramFiles "Python313\python.exe")
    )
    foreach ($c in $candidates) {
        if (Test-Path $c) {
            try {
                & $c -c "import sys; exit(0 if sys.version_info >= (3,12) else 1)" 2>$null
                if ($LASTEXITCODE -eq 0) { return $c }
            } catch {}
        }
    }
    return $null
}

# ── Helper: Detect GPU ───────────────────────────────────────────────────
function Detect-GPU {
    $result = [PSCustomObject]@{ Name = ""; VramGB = 0 }
    $nvidiaSmi = Get-Command nvidia-smi -ErrorAction SilentlyContinue
    if (-not $nvidiaSmi) { return $result }

    try {
        $output = & nvidia-smi --query-gpu=name,memory.total --format=csv,noheader,nounits 2>$null
        if ($LASTEXITCODE -eq 0 -and $output) {
            $firstLine = ($output -split "`n")[0].Trim()
            $parts = $firstLine -split ","
            if ($parts.Count -ge 2) {
                $result.Name = $parts[0].Trim()
                $vramMB = [int]($parts[1].Trim())
                $result.VramGB = [math]::Floor($vramMB / 1024)
            }
        }
    } catch {}
    return $result
}

# ── Helper: Find or Clone Repo ───────────────────────────────────────────
function Find-Or-Clone-Repo {
    param($Python)
    # Check if we're already in a repo (pyproject.toml present)
    if (Test-Path (Join-Path $PWD "pyproject.toml")) {
        $content = Get-Content (Join-Path $PWD "pyproject.toml") -Raw -ErrorAction SilentlyContinue
        if ($content -match 'name\s*=\s*"cognithor"') {
            return $PWD.Path
        }
    }
    # Check script's own directory (when running from downloaded file)
    $scriptDir = if ($PSScriptRoot) { $PSScriptRoot } else { $PWD.Path }
    if ($scriptDir -and (Test-Path (Join-Path $scriptDir "pyproject.toml"))) {
        $content = Get-Content (Join-Path $scriptDir "pyproject.toml") -Raw -ErrorAction SilentlyContinue
        if ($content -match 'name\s*=\s*"cognithor"') {
            return $scriptDir
        }
    }
    # Check if already cloned
    $cloneTarget = Join-Path $JarvisHome "cognithor"
    if (Test-Path (Join-Path $cloneTarget "pyproject.toml")) {
        Write-Info "Existing repo found: $cloneTarget"
        try {
            Push-Location $cloneTarget
            & git pull --quiet 2>$null
            Pop-Location
        } catch { Pop-Location }
        return $cloneTarget
    }
    # Try git clone
    $git = Get-Command git -ErrorAction SilentlyContinue
    if ($git) {
        Write-Info "Cloning repository to $cloneTarget ..."
        if (-not (Test-Path $JarvisHome)) { New-Item -ItemType Directory -Path $JarvisHome -Force | Out-Null }
        & git clone $RepoUrl $cloneTarget --quiet
        if ($LASTEXITCODE -eq 0) {
            return $cloneTarget
        }
        Write-Warn "git clone failed."
    }
    # Fallback: ZIP download
    Write-Info "Downloading repository as ZIP ..."
    if (-not (Test-Path $JarvisHome)) { New-Item -ItemType Directory -Path $JarvisHome -Force | Out-Null }
    $zipPath = Join-Path $JarvisHome "cognithor.zip"
    try {
        $ProgressPreference = 'SilentlyContinue'
        [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
        Invoke-WebRequest -Uri "https://github.com/Alex8791-cyber/cognithor/archive/refs/heads/main.zip" -OutFile $zipPath -UseBasicParsing
        Expand-Archive -Path $zipPath -DestinationPath $JarvisHome -Force
        $extractedDir = Join-Path $JarvisHome "cognithor-main"
        if (Test-Path $extractedDir) {
            if (Test-Path $cloneTarget) { Remove-Item $cloneTarget -Recurse -Force }
            Rename-Item $extractedDir "cognithor"
        }
        Remove-Item $zipPath -Force -ErrorAction SilentlyContinue
        if (Test-Path (Join-Path $cloneTarget "pyproject.toml")) {
            Write-OK "Repository downloaded"
            return $cloneTarget
        }
    } catch {
        Write-Warn "ZIP download failed: $_"
    }
    Write-Fail "Could not download repository."
    Write-Host "  Please download manually:" -ForegroundColor Yellow
    Write-Host "  https://github.com/Alex8791-cyber/cognithor/archive/refs/heads/main.zip" -ForegroundColor Yellow
    return $null
}

# ── Helper: Find Ollama ──────────────────────────────────────────────────
function Find-Ollama {
    $cmd = Get-Command ollama -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }
    $candidates = @(
        (Join-Path $env:LOCALAPPDATA "Programs\Ollama\ollama.exe"),
        (Join-Path $env:ProgramFiles "Ollama\ollama.exe")
    )
    foreach ($c in $candidates) {
        if (Test-Path $c) { return $c }
    }
    return $null
}

# ── Helper: Test Ollama Running ──────────────────────────────────────────
function Test-OllamaRunning {
    try {
        $resp = Invoke-WebRequest -Uri "http://localhost:11434/api/tags" -TimeoutSec 3 -UseBasicParsing -ErrorAction Stop
        return ($resp.StatusCode -eq 200)
    } catch {
        return $false
    }
}

# ── Helper: Ensure Model ─────────────────────────────────────────────────
function Ensure-Model {
    param($ModelName, $OllamaPath)
    try {
        $resp = Invoke-WebRequest -Uri "http://localhost:11434/api/tags" -TimeoutSec 5 -UseBasicParsing -ErrorAction Stop
        $data = $resp.Content | ConvertFrom-Json
        $baseName = ($ModelName -split ":")[0]
        $found = $data.models | Where-Object { $_.name -like "$baseName*" }
        if ($found) {
            Write-OK "Model available: $ModelName"
            return
        }
    } catch {}

    Write-Info "Downloading model: $ModelName (may take a few minutes) ..."
    & $OllamaPath pull $ModelName
    if ($LASTEXITCODE -eq 0) {
        Write-OK "Model installed: $ModelName"
    } else {
        Write-Warn "Download failed: $ModelName"
        Write-Host "  Manually: ollama pull $ModelName" -ForegroundColor Yellow
    }
}

# ── Run ───────────────────────────────────────────────────────────────────
Main
