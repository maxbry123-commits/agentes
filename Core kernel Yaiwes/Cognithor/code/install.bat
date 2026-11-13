@echo off
setlocal enabledelayedexpansion
title Cognithor Installer
color 0F
:: UTF-8 for Python output on Windows (cp1252 crashes on umlauts / emojis)
chcp 65001 >nul 2>&1
set "PYTHONIOENCODING=utf-8"
set "PYTHONUTF8=1"

:: ============================================================
::  COGNITHOR INSTALLER
::  Installiert Python, Ollama, venv, Abhaengigkeiten, Modelle.
::  Erkennt GPU automatisch und waehlt passenden Modus.
::
::  Nutzung:
::    install.bat              Standard-Installation (GPU auto-detect)
::    install.bat --lite       Lite-Modus erzwingen (nur qwen3:8b)
::    install.bat --full       Alles inkl. Voice + PostgreSQL
::    install.bat --uninstall  venv + Shortcuts entfernen
::    install.bat --silent     Non-interactive (use defaults)
:: ============================================================

echo.
echo    ____  ___   ____ _   _ ___ _____ _   _  ___  ____
echo   / ___^|/ _ \ / ___^| \ ^| ^|_ _^|_   _^| ^| ^| ^|/ _ \^|  _ \
echo  ^| ^|   ^| ^| ^| ^| ^|  _^|  \^| ^|^| ^|  ^| ^| ^| ^|_^| ^| ^| ^| ^| ^|_^) ^|
echo  ^| ^|___^| ^|_^| ^| ^|_^| ^| ^|\  ^|^| ^|  ^| ^| ^|  _  ^| ^|_^| ^|  _ ^<
echo   \____^|\___/ \____^|_^| \_^|___^| ^|_^| ^|_^| ^|_^|\___/^|_^| \_\
echo.
echo                    -- Installer --
echo.

:: ============================================================
::  COGNITHOR_HOME: prefer .cognithor, fallback to .jarvis
:: ============================================================
set "COGNITHOR_HOME=%USERPROFILE%\.cognithor"
if exist "%USERPROFILE%\.jarvis" if not exist "%USERPROFILE%\.cognithor" (
    set "COGNITHOR_HOME=%USERPROFILE%\.jarvis"
)
set "VENV_DIR=%COGNITHOR_HOME%\venv"
set "LOG_FILE=%COGNITHOR_HOME%\install.log"
set "MODE=all"
set "LITE=0"
set "FORCE_LITE=0"
set "VRAM_GB=0"
set "SILENT=0"

:: Ollama URL: from env or default
if defined COGNITHOR_OLLAMA_URL (
    set "OLLAMA_URL=%COGNITHOR_OLLAMA_URL%"
) else (
    set "OLLAMA_URL=http://localhost:11434"
)

:: ============================================================
::  Ensure home directory exists for logging
:: ============================================================
if not exist "%COGNITHOR_HOME%" mkdir "%COGNITHOR_HOME%"

:: Initialize log file
echo Cognithor Installer Log - %DATE% %TIME% > "%LOG_FILE%"
echo ================================================== >> "%LOG_FILE%"

:: ============================================================
::  Argumente parsen
:: ============================================================
:parse_args
if "%~1"=="" goto :args_done
if /i "%~1"=="--lite" (
    set "MODE=all"
    set "LITE=1"
    set "FORCE_LITE=1"
    shift
    goto :parse_args
)
if /i "%~1"=="--full" (
    set "MODE=full"
    shift
    goto :parse_args
)
if /i "%~1"=="--silent" (
    set "SILENT=1"
    shift
    goto :parse_args
)
if /i "%~1"=="--uninstall" (
    goto :uninstall
)
shift
goto :parse_args
:args_done

:: ============================================================
::  Logging helper --tee to console and log file
::  Usage: call :log "message"
:: ============================================================
:: We use a simple pattern: echo + append to log throughout
:: Define a goto-based tee macro isn't practical in cmd, so we
:: use >> "%LOG_FILE%" after key echo statements.

:: ============================================================
::  0. Repository erkennen oder herunterladen
:: ============================================================
call :log_section "0/10  Repository"

set "REPO_ROOT="

:: Pruefen ob install.bat aus einem Repo gestartet wurde
if exist "%~dp0pyproject.toml" (
    findstr /c:"cognithor" "%~dp0pyproject.toml" >nul 2>&1
    if not errorlevel 1 (
        set "REPO_ROOT=%~dp0"
        if "!REPO_ROOT:~-1!"=="\" set "REPO_ROOT=!REPO_ROOT:~0,-1!"
    )
)

:: Pruefen ob CWD ein Repo ist
if "%REPO_ROOT%"=="" (
    if exist "%CD%\pyproject.toml" (
        findstr /c:"cognithor" "%CD%\pyproject.toml" >nul 2>&1
        if not errorlevel 1 (
            set "REPO_ROOT=%CD%"
        )
    )
)

:: Pruefen ob bereits geclont
if "%REPO_ROOT%"=="" (
    if exist "%COGNITHOR_HOME%\cognithor\pyproject.toml" (
        set "REPO_ROOT=%COGNITHOR_HOME%\cognithor"
        call :log_msg "[OK] Existing repo: !REPO_ROOT!"
    )
)

:: Repo herunterladen
if "%REPO_ROOT%"=="" (
    call :log_msg "No local repository found."
    echo.

    :: Versuch 1: git clone (with retry)
    where git >nul 2>&1
    if not errorlevel 1 (
        call :log_msg "Cloning via git ..."
        if not exist "%COGNITHOR_HOME%" mkdir "%COGNITHOR_HOME%"
        set "RETRIES=0"
        :retry_git_clone
        git clone https://github.com/Alex8791-cyber/cognithor.git "%COGNITHOR_HOME%\cognithor" --quiet
        if errorlevel 1 (
            set /a RETRIES+=1
            if !RETRIES! LSS 3 (
                call :log_msg "Retrying git clone in 5 seconds... (attempt !RETRIES!/3)"
                timeout /t 5 /nobreak >nul
                goto :retry_git_clone
            )
            call :log_msg "[WARN] git clone failed after 3 attempts."
        ) else (
            set "REPO_ROOT=%COGNITHOR_HOME%\cognithor"
            call :log_msg "[OK] Repository cloned: !REPO_ROOT!"
        )
    )

    :: Versuch 2: PowerShell ZIP-Download
    if "!REPO_ROOT!"=="" (
        call :log_msg "Downloading repository as ZIP ..."
        if not exist "%COGNITHOR_HOME%" mkdir "%COGNITHOR_HOME%"
        powershell -NoProfile -Command "try { [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; $ProgressPreference = 'SilentlyContinue'; Invoke-WebRequest -Uri 'https://github.com/Alex8791-cyber/cognithor/archive/refs/heads/main.zip' -OutFile '%COGNITHOR_HOME%\cognithor.zip' -UseBasicParsing; Expand-Archive -Path '%COGNITHOR_HOME%\cognithor.zip' -DestinationPath '%COGNITHOR_HOME%' -Force; if (Test-Path '%COGNITHOR_HOME%\cognithor-main') { if (Test-Path '%COGNITHOR_HOME%\cognithor') { Remove-Item '%COGNITHOR_HOME%\cognithor' -Recurse -Force }; Rename-Item '%COGNITHOR_HOME%\cognithor-main' 'cognithor' }; Remove-Item '%COGNITHOR_HOME%\cognithor.zip' -Force; exit 0 } catch { Write-Host $_.Exception.Message; exit 1 }" 2>nul
        if not errorlevel 1 (
            if exist "%COGNITHOR_HOME%\cognithor\pyproject.toml" (
                set "REPO_ROOT=%COGNITHOR_HOME%\cognithor"
                call :log_msg "[OK] Repository downloaded: !REPO_ROOT!"
            )
        )
    )

    if "!REPO_ROOT!"=="" (
        call :log_msg "[FAIL] Could not download repository!"
        echo.
        echo   Please download manually:
        echo   https://github.com/Alex8791-cyber/cognithor/archive/refs/heads/main.zip
        echo   Extract and run install.bat from the folder.
        echo.
        if "%SILENT%"=="0" pause
        exit /b 1
    )
)

if "%REPO_ROOT%"=="" (
    call :log_msg "[FAIL] No repository found!"
    if "%SILENT%"=="0" pause
    exit /b 1
)

call :log_msg "[OK] Repo: %REPO_ROOT%"
echo.

:: ============================================================
::  1. Python pruefen / installieren
:: ============================================================
call :log_section "1/10  Check Python"

set "PYTHON_CMD="

:: Zuerst existierende Python-Installation suchen
where python >nul 2>&1
if not errorlevel 1 (
    python -c "import sys" >nul 2>&1
    if not errorlevel 1 (
        python -c "import sys; sys.exit(0 if sys.version_info >= (3,12) else 1)" 2>nul
        if not errorlevel 1 (
            set "PYTHON_CMD=python"
        )
    )
)

if "%PYTHON_CMD%"=="" (
    where py >nul 2>&1
    if not errorlevel 1 (
        py -c "import sys; sys.exit(0 if sys.version_info >= (3,12) else 1)" 2>nul
        if not errorlevel 1 (
            set "PYTHON_CMD=py"
        )
    )
)

:: Python nicht gefunden oder zu alt -> automatisch installieren
if "%PYTHON_CMD%"=="" (
    call :log_msg "Python 3.12+ not found. Attempting automatic installation..."
    echo.

    :: Versuch 1: winget
    where winget >nul 2>&1
    if not errorlevel 1 (
        call :log_msg "Installing Python 3.12 via winget ..."
        echo   (This may take 1-2 minutes.)
        winget install --id Python.Python.3.12 -e --accept-source-agreements --accept-package-agreements --silent
        if not errorlevel 1 (
            call :log_msg "[OK] Python installed via winget"
            echo.
            echo   IMPORTANT: Refreshing PATH...
            :: PATH neu laden --APPEND, never overwrite
            for /f "tokens=2*" %%a in ('reg query "HKCU\Environment" /v Path 2^>nul') do set "USER_PATH=%%b"
            for /f "tokens=2*" %%a in ('reg query "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Environment" /v Path 2^>nul') do set "SYS_PATH=%%b"
            set "PATH=!SYS_PATH!;!USER_PATH!;%PATH%"

            :: Nochmal suchen
            where python >nul 2>&1
            if not errorlevel 1 (
                python -c "import sys; sys.exit(0 if sys.version_info >= (3,12) else 1)" 2>nul
                if not errorlevel 1 (
                    set "PYTHON_CMD=python"
                )
            )
            if "!PYTHON_CMD!"=="" (
                :: Typische winget-Installationspfade pruefen
                for %%p in (
                    "%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
                    "%LOCALAPPDATA%\Programs\Python\Python313\python.exe"
                    "%ProgramFiles%\Python312\python.exe"
                    "%ProgramFiles%\Python313\python.exe"
                ) do (
                    if exist %%p (
                        set "PYTHON_CMD=%%~p"
                        goto :python_found
                    )
                )
            )
        ) else (
            call :log_msg "[WARN] winget installation failed."
        )
    )
)

:: Immer noch kein Python?
if "%PYTHON_CMD%"=="" (
    echo.
    call :log_msg "[FAIL] Could not install Python 3.12+!"
    echo.
    echo   Please install manually:
    echo   https://www.python.org/downloads/
    echo.
    echo   IMPORTANT: Check "Add Python to PATH" during installation!
    echo   Then run this script again.
    echo.
    if "%SILENT%"=="0" pause
    exit /b 1
)

:python_found
for /f "tokens=*" %%v in ('%PYTHON_CMD% --version 2^>^&1') do call :log_msg "[OK] %%v"
echo.

:: ============================================================
::  2. GPU-Erkennung (Auto-Lite)
:: ============================================================
call :log_section "2/10  GPU Detection"

set "GPU_NAME=No GPU detected"
set "VRAM_GB=0"
set "GPU_VENDOR=none"

:: --- NVIDIA Detection ---
where nvidia-smi >nul 2>&1
if not errorlevel 1 (
    :: GPU-Name und VRAM auslesen
    for /f "tokens=1,2 delims=," %%a in ('nvidia-smi --query-gpu^=name^,memory.total --format^=csv^,noheader^,nounits 2^>nul') do (
        set "GPU_NAME=%%a"
        set "RAW_VRAM=%%b"
        :: Trim leading spaces
        for /f "tokens=* delims= " %%x in ("!RAW_VRAM!") do set "RAW_VRAM=%%x"
        :: Validate that RAW_VRAM is numeric
        echo !RAW_VRAM!| findstr /r "^[0-9][0-9]*$" >nul 2>&1
        if not errorlevel 1 (
            set /a "VRAM_MB=!RAW_VRAM!"
            if !VRAM_MB! gtr 0 (
                set /a "VRAM_GB=!VRAM_MB! / 1024"
            )
        ) else (
            call :log_msg "[WARN] Could not parse VRAM value: !RAW_VRAM!"
        )
    )
    if !VRAM_GB! gtr 0 set "GPU_VENDOR=nvidia"
)

:: --- AMD Detection ---
if "%GPU_VENDOR%"=="none" (
    wmic path win32_VideoController get Name 2>nul | findstr /i "AMD Radeon" >nul
    if not errorlevel 1 (
        set "GPU_VENDOR=amd"
        set "GPU_NAME=AMD Radeon (VRAM detection not supported)"
        call :log_msg "[INFO] AMD GPU detected (VRAM detection not supported, using defaults)"
    )
)

if %VRAM_GB% gtr 0 (
    call :log_msg "[OK] GPU: %GPU_NAME% (%VRAM_GB% GB VRAM)"
) else if "%GPU_VENDOR%"=="none" (
    call :log_msg "[INFO] No NVIDIA/AMD GPU detected."
    echo   CPU mode -- Lite is recommended.
    if "%FORCE_LITE%"=="0" (
        set "LITE=1"
        call :log_msg "[INFO] Lite mode automatically enabled."
    )
)

:: Auto-Lite bei wenig VRAM (unter 12 GB -> kein Platz fuer qwen3:32b)
if %VRAM_GB% gtr 0 if %VRAM_GB% lss 12 (
    if "%FORCE_LITE%"=="0" (
        set "LITE=1"
        call :log_msg "[INFO] VRAM under 12 GB -- Lite mode automatically enabled."
        echo   (qwen3:8b statt qwen3:32b, spart ~14 GB VRAM)
    )
)

if %VRAM_GB% geq 12 (
    if "%FORCE_LITE%"=="0" (
        call :log_msg "[OK] Enough VRAM for standard mode (qwen3:32b)"
    )
)

:: Modus-Anzeige
echo.
if "%LITE%"=="1" (
    echo   Mode: LITE (6 GB VRAM)
) else if "%MODE%"=="full" (
    echo   Mode: FULL (all features incl. voice)
) else (
    echo   Mode: STANDARD (recommended)
)
echo   Home:  %COGNITHOR_HOME%
echo.

:: ============================================================
::  3. Admin-Warnung
:: ============================================================
echo %REPO_ROOT% | findstr /i "Program Files" >nul 2>&1
if not errorlevel 1 (
    call :log_msg "[WARN] Repo is in Program Files."
    echo   Recommendation: Install in %USERPROFILE%\cognithor or C:\cognithor.
    echo.
)

:: ============================================================
::  4. venv erstellen / aktivieren
:: ============================================================
call :log_section "3/10  Virtual Environment"

if not exist "%COGNITHOR_HOME%" mkdir "%COGNITHOR_HOME%"

if exist "%VENV_DIR%\Scripts\activate.bat" (
    call :log_msg "[OK] venv already exists: %VENV_DIR%"
    call "%VENV_DIR%\Scripts\activate.bat"
) else (
    echo   Creating venv in %VENV_DIR% ...
    %PYTHON_CMD% -m venv "%VENV_DIR%"
    if errorlevel 1 (
        call :log_msg "[FAIL] Could not create venv!"
        echo   Try: %PYTHON_CMD% -m pip install virtualenv
        if "%SILENT%"=="0" pause
        exit /b 1
    )
    call "%VENV_DIR%\Scripts\activate.bat"
    python -m pip install --upgrade pip setuptools wheel --quiet >nul 2>&1
    call :log_msg "[OK] venv created and activated"
)
echo.

:: ============================================================
::  5. pip install (mit sichtbarem Fortschritt + retry)
:: ============================================================
call :log_section "4/10  Install Python dependencies"

echo   Installing cognithor[%MODE%] ...
echo   (This may take 3-5 minutes on first run. Please do not close!)
echo.

:: pip install with retry logic
set "RETRIES=0"
:retry_pip_install
"%VENV_DIR%\Scripts\python.exe" -m pip install -e "%REPO_ROOT%[%MODE%]" --disable-pip-version-check --progress-bar on
if errorlevel 1 (
    set /a RETRIES+=1
    if !RETRIES! LSS 3 (
        call :log_msg "Retrying pip install in 5 seconds... (attempt !RETRIES!/3)"
        timeout /t 5 /nobreak >nul
        goto :retry_pip_install
    )
    echo.
    call :log_msg "[FAIL] pip install failed after 3 attempts!"
    echo   Try manually:
    echo     cd "%REPO_ROOT%"
    echo     pip install -e ".[all]"
    echo.
    if "%SILENT%"=="0" pause
    exit /b 1
)

echo.
call :log_msg "[OK] Dependencies installed"
echo.

:: ============================================================
::  6. Ollama pruefen / installieren
:: ============================================================
call :log_section "5/10  Check Ollama"

set "OLLAMA_CMD="
where ollama >nul 2>&1
if not errorlevel 1 (
    set "OLLAMA_CMD=ollama"
    goto :ollama_found
)

:: Standard-Pfade pruefen
if exist "%LOCALAPPDATA%\Programs\Ollama\ollama.exe" (
    set "OLLAMA_CMD=%LOCALAPPDATA%\Programs\Ollama\ollama.exe"
    goto :ollama_found
)
if exist "%ProgramFiles%\Ollama\ollama.exe" (
    set "OLLAMA_CMD=%ProgramFiles%\Ollama\ollama.exe"
    goto :ollama_found
)

:: Ollama nicht gefunden -> User fragen (or auto-yes in silent mode)
call :log_msg "Ollama not found."
echo.
if "%SILENT%"=="1" (
    set "INSTALL_OLLAMA=y"
) else (
    set /p "INSTALL_OLLAMA=  Install Ollama now via winget? [Y/n]: "
)
if /i "!INSTALL_OLLAMA!"=="n" goto :skip_ollama_install
if /i "!INSTALL_OLLAMA!"=="no" goto :skip_ollama_install

:: Versuch 1: winget
where winget >nul 2>&1
if not errorlevel 1 (
    call :log_msg "Installing Ollama via winget ..."
    winget install --id Ollama.Ollama -e --accept-source-agreements --accept-package-agreements --silent
    if not errorlevel 1 (
        call :log_msg "[OK] Ollama installed via winget"

        :: PATH neu laden --APPEND, never overwrite
        for /f "tokens=2*" %%a in ('reg query "HKCU\Environment" /v Path 2^>nul') do set "USER_PATH=%%b"
        for /f "tokens=2*" %%a in ('reg query "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Environment" /v Path 2^>nul') do set "SYS_PATH=%%b"
        set "PATH=!SYS_PATH!;!USER_PATH!"

        :: Erneut suchen
        where ollama >nul 2>&1
        if not errorlevel 1 (
            set "OLLAMA_CMD=ollama"
            goto :ollama_found
        )
        if exist "%LOCALAPPDATA%\Programs\Ollama\ollama.exe" (
            set "OLLAMA_CMD=%LOCALAPPDATA%\Programs\Ollama\ollama.exe"
            goto :ollama_found
        )
    ) else (
        call :log_msg "[WARN] winget installation failed."
    )
)

:skip_ollama_install
:: Immer noch kein Ollama
if "%OLLAMA_CMD%"=="" (
    echo.
    call :log_msg "[WARN] Ollama not installed."
    echo.
    echo   Please install manually: https://ollama.com/download
    echo   After installation, run this script again.
    echo.
    goto :skip_models
)

:ollama_found
call :log_msg "[OK] Ollama found: %OLLAMA_CMD%"

:: Pruefen ob Ollama-Server laeuft (use configurable URL)
"%VENV_DIR%\Scripts\python.exe" -c "import sys, urllib.request; urllib.request.urlopen('%OLLAMA_URL%/api/tags', timeout=3); sys.exit(0)" >nul 2>&1
if errorlevel 1 (
    echo   Starting Ollama server...
    start "" /b "%OLLAMA_CMD%" serve >nul 2>&1
    set "WAIT_COUNT=0"
    :wait_ollama
    if !WAIT_COUNT! geq 30 (
        call :log_msg "[WARN] Ollama server not responding after 30s."
        goto :skip_models
    )
    timeout /t 1 /nobreak >nul 2>&1
    "%VENV_DIR%\Scripts\python.exe" -c "import sys, urllib.request; urllib.request.urlopen('%OLLAMA_URL%/api/tags', timeout=2); sys.exit(0)" >nul 2>&1
    if errorlevel 1 (
        set /a WAIT_COUNT+=1
        goto :wait_ollama
    )
    call :log_msg "[OK] Ollama server started"
) else (
    call :log_msg "[OK] Ollama server already running"
)
echo.

:: ============================================================
::  7. Modelle pruefen / pullen
:: ============================================================
call :log_section "6/10  Ollama Models"

:: --- Disk space check before model download ---
call :log_msg "Checking available disk space..."
set "FREE_GB=0"
for /f "tokens=3" %%A in ('dir /-C "%USERPROFILE%" 2^>nul ^| findstr "bytes free"') do (
    set "FREE_BYTES=%%A"
)
if defined FREE_BYTES (
    :: Convert bytes to GB (approximate: divide by 1073741824 ~ shift by 30)
    :: cmd can't handle large numbers, use python
    "%VENV_DIR%\Scripts\python.exe" -c "import sys; b=int('%FREE_BYTES%'.replace(',','')); gb=b//1073741824; print(gb); sys.exit(0 if gb>=10 else 1)" > "%TEMP%\cog_free_gb.txt" 2>nul
    if errorlevel 1 (
        call :log_msg "[WARN] Less than 10 GB free disk space! Model downloads may fail."
        echo   Consider freeing disk space before continuing.
        echo.
    )
    for /f %%g in ('type "%TEMP%\cog_free_gb.txt" 2^>nul') do set "FREE_GB=%%g"
    if defined FREE_GB (
        call :log_msg "[INFO] Available disk space: !FREE_GB! GB"
    )
    del "%TEMP%\cog_free_gb.txt" >nul 2>&1
) else (
    call :log_msg "[INFO] Could not determine free disk space."
)

echo.
if "%LITE%"=="1" (
    echo   Required models: qwen3:8b, nomic-embed-text
) else (
    echo   Required models: qwen3:8b, qwen3:32b, nomic-embed-text
)
echo.
if "%SILENT%"=="1" (
    set "PULL_MODELS=y"
) else (
    set /p "PULL_MODELS=  Download missing models now? [Y/n]: "
)
if /i "!PULL_MODELS!"=="n" goto :skip_models
if /i "!PULL_MODELS!"=="no" goto :skip_models

if "%LITE%"=="1" (
    call :ensure_model qwen3:8b
    call :ensure_model nomic-embed-text
) else (
    call :ensure_model qwen3:8b
    call :ensure_model qwen3:32b
    call :ensure_model nomic-embed-text
)
echo.

:skip_models

:: ============================================================
::  8. Verzeichnisstruktur
:: ============================================================
call :log_section "7/10  Initialize directory structure"

if "%LITE%"=="1" (
    "%VENV_DIR%\Scripts\python.exe" -m jarvis --lite --init-only >nul 2>&1
) else (
    "%VENV_DIR%\Scripts\python.exe" -m jarvis --init-only >nul 2>&1
)
if errorlevel 1 (
    if not exist "%COGNITHOR_HOME%\memory" mkdir "%COGNITHOR_HOME%\memory"
    if not exist "%COGNITHOR_HOME%\logs" mkdir "%COGNITHOR_HOME%\logs"
    if not exist "%COGNITHOR_HOME%\cache" mkdir "%COGNITHOR_HOME%\cache"
    call :log_msg "[OK] Directories created manually"
) else (
    call :log_msg "[OK] Directory structure initialized"
)
echo.

:: ============================================================
::  9. Smoke-Test
:: ============================================================
call :log_section "8/10  Smoke-Test"

"%VENV_DIR%\Scripts\python.exe" -c "import sys; import cognithor; print(f'  [OK] cognithor v{cognithor.__version__}'); sys.exit(0)"
if errorlevel 1 (
    call :log_msg "[FAIL] Import test failed!"
    echo   Try: pip install -e "%REPO_ROOT%[all]"
    if "%SILENT%"=="0" pause
    exit /b 1
)
echo.

:: ============================================================
::  10. Desktop-Shortcut
:: ============================================================
call :log_section "9/10  Desktop shortcut"

set "BAT_PATH=%REPO_ROOT%\start_cognithor.bat"
if not exist "%BAT_PATH%" (
    call :log_msg "[INFO] start_cognithor.bat not found -- shortcut skipped"
    goto :skip_shortcut
)

set "DESKTOP_PATH="
if exist "%USERPROFILE%\Desktop" set "DESKTOP_PATH=%USERPROFILE%\Desktop"
if "%DESKTOP_PATH%"=="" if exist "%USERPROFILE%\OneDrive\Desktop" set "DESKTOP_PATH=%USERPROFILE%\OneDrive\Desktop"
if "%DESKTOP_PATH%"=="" if exist "%USERPROFILE%\OneDrive\Schreibtisch" set "DESKTOP_PATH=%USERPROFILE%\OneDrive\Schreibtisch"
if "%DESKTOP_PATH%"=="" if exist "%USERPROFILE%\Schreibtisch" set "DESKTOP_PATH=%USERPROFILE%\Schreibtisch"

if "%DESKTOP_PATH%"=="" (
    call :log_msg "[INFO] Desktop folder not found -- shortcut skipped"
    goto :skip_shortcut
)

if exist "%DESKTOP_PATH%\Cognithor.lnk" (
    call :log_msg "[OK] Desktop shortcut already exists"
    goto :skip_shortcut
)

powershell -NoProfile -Command "$ws = New-Object -ComObject WScript.Shell; $sc = $ws.CreateShortcut('%DESKTOP_PATH%\Cognithor.lnk'); $sc.TargetPath = '%BAT_PATH%'; $sc.WorkingDirectory = '%REPO_ROOT%'; $sc.Description = 'Cognithor Control Center starten'; $sc.WindowStyle = 1; $sc.Save()" >nul 2>&1
if errorlevel 1 (
    call :log_msg "[WARN] Could not create desktop shortcut"
) else (
    call :log_msg "[OK] Desktop shortcut created"
)

:skip_shortcut
echo.

:: ============================================================
::  Zusammenfassung
:: ============================================================
call :log_section "10/10  Summary"
echo.
call :log_msg "[OK] Cognithor successfully installed!"
echo.
echo   Start:
echo     start_cognithor.bat          Web UI (recommended)
echo     python -m jarvis             CLI mode
if "%LITE%"=="1" (
    echo     python -m jarvis --lite     Lite mode (6 GB VRAM)
)
echo.
if %VRAM_GB% gtr 0 (
    echo   Detected GPU: %GPU_NAME% (%VRAM_GB% GB VRAM)
)
if "%GPU_VENDOR%"=="amd" (
    echo   Detected GPU: %GPU_NAME%
)
if "%LITE%"=="1" (
    echo   Model mode: LITE (qwen3:8b, ~6 GB VRAM)
) else (
    echo   Model mode: STANDARD (qwen3:32b + qwen3:8b)
)
echo.
echo   Directories:
echo     %COGNITHOR_HOME%\              Home
echo     %COGNITHOR_HOME%\config.yaml   Configuration
echo     %COGNITHOR_HOME%\memory\       Memory
echo     %COGNITHOR_HOME%\logs\         Logs
echo.
call :log_msg "Install log saved to %LOG_FILE%"
echo.

if "%SILENT%"=="0" pause
exit /b 0

:: ============================================================
::  Hilfsfunktionen
:: ============================================================

:: --- log_section: print section header ---
:log_section
echo   ---------------------------------------------------------- >> "%LOG_FILE%"
echo     %~1 >> "%LOG_FILE%"
echo   ---------------------------------------------------------- >> "%LOG_FILE%"
echo   ----------------------------------------------------------
echo     %~1
echo   ----------------------------------------------------------
goto :eof

:: --- log_msg: echo to console and append to log ---
:log_msg
echo   %~1
echo   [%TIME%] %~1 >> "%LOG_FILE%"
goto :eof

:: --- ensure_model: check + pull with exact match and retry ---
:ensure_model
set "MODEL_NAME=%~1"
:: Use exact model name matching to avoid qwen3:8b matching qwen3:80b
:: We check if the model name appears as a complete entry (name:tag)
"%VENV_DIR%\Scripts\python.exe" -c "import sys, urllib.request, json; data=json.loads(urllib.request.urlopen('%OLLAMA_URL%/api/tags',timeout=5).read()); models=[m['name'] for m in data.get('models',[])]; found=any(m=='%MODEL_NAME%' or m=='%MODEL_NAME%:latest' or (m.split(':')[0]=='%MODEL_NAME%' and ':' not in '%MODEL_NAME%') for m in models); sys.exit(0 if found else 1)" >nul 2>&1
if not errorlevel 1 (
    call :log_msg "[OK] Model available: %MODEL_NAME%"
    goto :eof
)
call :log_msg "Downloading model: %MODEL_NAME% (may take a few minutes)..."
:: Retry logic for ollama pull
set "PULL_RETRIES=0"
:retry_ollama_pull
"%OLLAMA_CMD%" pull %MODEL_NAME%
if errorlevel 1 (
    set /a PULL_RETRIES+=1
    if !PULL_RETRIES! LSS 3 (
        call :log_msg "Retrying ollama pull in 5 seconds... (attempt !PULL_RETRIES!/3)"
        timeout /t 5 /nobreak >nul
        goto :retry_ollama_pull
    )
    call :log_msg "[WARN] Download failed after 3 attempts: %MODEL_NAME%"
    echo   Manually: ollama pull %MODEL_NAME%
) else (
    call :log_msg "[OK] Model installed: %MODEL_NAME%"
)
goto :eof

:: ============================================================
::  Deinstallation
:: ============================================================
:uninstall
echo.
echo   Uninstalling Cognithor
echo   ============================
echo.
echo   This will remove:
echo     - Virtual Environment (%VENV_DIR%)
echo     - Desktop shortcut
echo.
echo   NOT removed:
echo     - Your data in %COGNITHOR_HOME% (memory, logs, config)
echo     - Ollama and models
echo.
if "%SILENT%"=="1" (
    set "CONFIRM=y"
) else (
    set /p "CONFIRM=Continue? [y/N] "
)
if /i not "%CONFIRM%"=="y" (
    echo   Cancelled.
    if "%SILENT%"=="0" pause
    exit /b 0
)

if exist "%VENV_DIR%" (
    rmdir /s /q "%VENV_DIR%"
    echo   [OK] venv removed
) else (
    echo   [INFO] No venv found
)

set "DESKTOP_PATH="
if exist "%USERPROFILE%\Desktop\Cognithor.lnk" set "DESKTOP_PATH=%USERPROFILE%\Desktop"
if "%DESKTOP_PATH%"=="" if exist "%USERPROFILE%\OneDrive\Desktop\Cognithor.lnk" set "DESKTOP_PATH=%USERPROFILE%\OneDrive\Desktop"
if "%DESKTOP_PATH%"=="" if exist "%USERPROFILE%\OneDrive\Schreibtisch\Cognithor.lnk" set "DESKTOP_PATH=%USERPROFILE%\OneDrive\Schreibtisch"
if "%DESKTOP_PATH%"=="" if exist "%USERPROFILE%\Schreibtisch\Cognithor.lnk" set "DESKTOP_PATH=%USERPROFILE%\Schreibtisch"

if not "%DESKTOP_PATH%"=="" (
    del "%DESKTOP_PATH%\Cognithor.lnk" >nul 2>&1
    echo   [OK] Desktop shortcut removed
)

echo.
echo   [OK] Uninstallation complete.
echo   Data in %COGNITHOR_HOME% was NOT deleted.
echo   To fully remove: rmdir /s /q "%COGNITHOR_HOME%"
echo.
if "%SILENT%"=="0" pause
exit /b 0
