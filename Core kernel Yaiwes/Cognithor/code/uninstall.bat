@echo off
setlocal enabledelayedexpansion
title Cognithor Uninstaller
color 0F
chcp 65001 >nul 2>&1

echo.
echo    ____  ___   ____ _   _ ___ _____ _   _  ___  ____
echo   / ___^|/ _ \ / ___^| \ ^| ^|_ _^|_   _^| ^| ^| ^|/ _ \^|  _ \
echo  ^| ^|   ^| ^| ^| ^| ^|  _^|  \^| ^|^| ^|  ^| ^| ^| ^|_^| ^| ^| ^| ^| ^|_^) ^|
echo  ^| ^|___^| ^|_^| ^| ^|_^| ^| ^|\  ^|^| ^|  ^| ^| ^|  _  ^| ^|_^| ^|  _ ^<
echo   \____^|\___/ \____^|_^| \_^|___^| ^|_^| ^|_^| ^|_^|\___/^|_^| \_\
echo.
echo                    -- Uninstaller --
echo.

set "COGNITHOR_HOME=%USERPROFILE%\.jarvis"
set "VENV_DIR=%COGNITHOR_HOME%\venv"
set "INSTALL_DIR=%LOCALAPPDATA%\Cognithor"

:: ============================================================
::  Detect what is installed
:: ============================================================

echo   Scanning installation...
echo.

set HAS_VENV=0
set HAS_DATA=0
set HAS_INSTALL=0
set HAS_SHORTCUT=0
set HAS_OLLAMA=0

if exist "%VENV_DIR%" set HAS_VENV=1
if exist "%COGNITHOR_HOME%\config.yaml" set HAS_DATA=1
if exist "%INSTALL_DIR%\cognithor.bat" set HAS_INSTALL=1

set "DESKTOP_PATH="
for %%D in (
    "%USERPROFILE%\Desktop"
    "%USERPROFILE%\OneDrive\Desktop"
    "%USERPROFILE%\OneDrive\Schreibtisch"
    "%USERPROFILE%\Schreibtisch"
) do (
    if exist "%%~D\Cognithor.lnk" (
        set "DESKTOP_PATH=%%~D"
        set HAS_SHORTCUT=1
    )
)

:: Check Start Menu
set "STARTMENU_PATH="
if exist "%APPDATA%\Microsoft\Windows\Start Menu\Programs\Cognithor" (
    set "STARTMENU_PATH=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Cognithor"
    set HAS_SHORTCUT=1
)

:: Check if Ollama is running
tasklist /FI "IMAGENAME eq ollama.exe" 2>NUL | find /I /N "ollama.exe" >NUL
if not errorlevel 1 set HAS_OLLAMA=1

echo   Found:
if %HAS_VENV%==1    echo     [x] Virtual environment: %VENV_DIR%
if %HAS_DATA%==1    echo     [x] User data: %COGNITHOR_HOME%
if %HAS_INSTALL%==1 echo     [x] Packaged install: %INSTALL_DIR%
if %HAS_SHORTCUT%==1 echo     [x] Desktop/Start Menu shortcuts
if %HAS_OLLAMA%==1  echo     [x] Ollama process running
echo.

:: ============================================================
::  Ask what to remove
:: ============================================================

echo   What would you like to remove?
echo.
echo     1) Code only (venv, install dir, shortcuts, PATH)
echo        Keeps: your data, memory, config, Ollama
echo.
echo     2) Everything (code + all user data)
echo        Removes: venv, install dir, shortcuts, PATH,
echo                 ~/.jarvis (memory, vault, config, logs)
echo.
echo     3) Cancel
echo.

set /p "CHOICE=  Choose [1/2/3]: "

if "%CHOICE%"=="3" goto :cancelled
if "%CHOICE%"=="2" goto :confirm_full
if "%CHOICE%"=="1" goto :uninstall_code
goto :cancelled

:confirm_full
echo.
echo   WARNING: This will permanently delete ALL your data:
echo     - Memory (conversations, identity, episodic)
echo     - Knowledge Vault (documents, research)
echo     - Configuration (config.yaml, .env)
echo     - Databases (33 SQLCipher databases)
echo     - Skills (generated, community)
echo     - Logs and audit trail
echo.
set /p "CONFIRM=  Type DELETE to confirm: "
if not "%CONFIRM%"=="DELETE" (
    echo   Cancelled. Nothing was removed.
    pause
    exit /b 0
)

:: ============================================================
::  Uninstall
:: ============================================================

:uninstall_code
echo.
echo   Uninstalling...
echo.

:: Stop Ollama if running
if %HAS_OLLAMA%==1 (
    echo   [..] Stopping Ollama...
    taskkill /F /IM ollama.exe >nul 2>&1
    echo   [OK] Ollama stopped
)

:: Remove venv
if exist "%VENV_DIR%" (
    echo   [..] Removing virtual environment...
    rmdir /s /q "%VENV_DIR%" >nul 2>&1
    echo   [OK] venv removed: %VENV_DIR%
) else (
    echo   [--] No venv found
)

:: Remove packaged install
if exist "%INSTALL_DIR%" (
    echo   [..] Removing packaged install...
    rmdir /s /q "%INSTALL_DIR%" >nul 2>&1
    echo   [OK] Install dir removed: %INSTALL_DIR%
) else (
    echo   [--] No packaged install found
)

:: Remove desktop shortcut
if not "%DESKTOP_PATH%"=="" (
    del "%DESKTOP_PATH%\Cognithor.lnk" >nul 2>&1
    echo   [OK] Desktop shortcut removed
)

:: Remove Start Menu
if not "%STARTMENU_PATH%"=="" (
    rmdir /s /q "%STARTMENU_PATH%" >nul 2>&1
    echo   [OK] Start Menu entry removed
)

:: Clean PATH
echo   [..] Cleaning PATH...
for /f "tokens=2*" %%A in (
    'reg query "HKCU\Environment" /v Path 2^>nul'
) do set "CURRENT_PATH=%%B"

if defined CURRENT_PATH (
    :: Remove common Cognithor PATH entries
    set "NEW_PATH=!CURRENT_PATH!"
    set "NEW_PATH=!NEW_PATH:;%INSTALL_DIR%=!"
    set "NEW_PATH=!NEW_PATH:%INSTALL_DIR%;=!"
    set "NEW_PATH=!NEW_PATH:%INSTALL_DIR%=!"

    if not "!NEW_PATH!"=="!CURRENT_PATH!" (
        reg add "HKCU\Environment" /v Path /t REG_EXPAND_SZ /d "!NEW_PATH!" /f >nul 2>&1
        echo   [OK] PATH cleaned
    ) else (
        echo   [--] PATH was clean
    )
)

:: Remove marker file
if exist "%COGNITHOR_HOME%\.cognithor_initialized" (
    del "%COGNITHOR_HOME%\.cognithor_initialized" >nul 2>&1
    echo   [OK] Initialization marker removed
)

:: Full uninstall: remove user data
if "%CHOICE%"=="2" (
    echo.
    echo   [..] Removing user data...
    if exist "%COGNITHOR_HOME%" (
        rmdir /s /q "%COGNITHOR_HOME%" >nul 2>&1
        echo   [OK] User data removed: %COGNITHOR_HOME%
    )
)

echo.
echo   ============================================
echo   [OK] Cognithor uninstalled successfully.
echo   ============================================
echo.

if "%CHOICE%"=="1" (
    echo   Your data in %COGNITHOR_HOME% was preserved.
    echo   To remove it later: rmdir /s /q "%COGNITHOR_HOME%"
    echo.
)

echo   Note: Ollama and its models were NOT removed.
echo   To uninstall Ollama: winget uninstall Ollama.Ollama
echo   To remove models: rmdir /s /q "%USERPROFILE%\.ollama"
echo.

pause
exit /b 0

:cancelled
echo.
echo   Cancelled. Nothing was removed.
echo.
pause
exit /b 0
