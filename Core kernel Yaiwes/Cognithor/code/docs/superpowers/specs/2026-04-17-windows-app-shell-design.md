# Windows App Shell — Design Spec

**Date:** 2026-04-17
**Status:** Approved
**Goal:** Make Cognithor feel like a native Windows application — own process name, system tray icon, grouped child processes, clean shutdown.

## Problem

Cognithor runs as a Python process behind a `.bat` launcher. In Task Manager it shows as `python.exe`, has no icon in the taskbar or system tray, and there's no clean way to stop it. It feels like a ghost application.

## Solution

A thin C# (.NET 8) wrapper — `Cognithor.exe` — that:

1. Appears as "Cognithor" in Task Manager under "Apps"
2. Lives in the system tray with the Cognithor owl icon
3. Groups all child processes (Python, Ollama, etc.) via a Windows Job Object
4. Provides a context menu for Open UI, Restart, and Quit
5. Monitors backend health and reflects status via tray icon color

## Architecture

```
Cognithor.exe (WinForms, GUI subsystem)
  |
  +-- Job Object (JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE)
  |     +-- python.exe -m cognithor --no-cli --api-port 8741
  |     +-- ollama.exe serve  (if installed)
  |     +-- (future companion processes)
  |
  +-- System Tray (NotifyIcon)
  |     +-- Icon: app_icon.ico (green/yellow/red overlay)
  |     +-- DoubleClick -> open browser to localhost:8741
  |     +-- ContextMenu:
  |           +-- "Open Command Center"   -> browser
  |           +-- "Status: Running"       -> disabled label
  |           +-- separator
  |           +-- "Restart Backend"       -> kill + respawn python
  |           +-- "Quit Cognithor"        -> clean shutdown
  |           +-- "v0.92.1"              -> disabled label
  |
  +-- Health Monitor (Timer, 10s interval)
        +-- GET http://localhost:8741/api/v1/health
        +-- healthy   -> green icon
        +-- starting  -> yellow icon
        +-- down/err  -> red icon
```

## Lifecycle

| Event | Behavior |
|-------|----------|
| User launches Cognithor.exe | Creates Job Object, spawns Python + Ollama, shows tray icon (yellow) |
| Health check succeeds | Tray icon turns green, tooltip "Cognithor - Running" |
| User double-clicks tray | Opens `http://localhost:8741` in default browser |
| User clicks X on any window | Minimizes to tray, keeps running |
| User right-clicks tray -> Quit | Disposes Job Object (kills all children), exits |
| Python process crashes | Tray turns red, tooltip "Backend stopped", balloon notification |
| User clicks Restart | Kills Python process, respawns, tray turns yellow |
| Cognithor.exe crashes/killed | Job Object auto-closes, all children die (OS guarantee) |

## File Structure

```
launcher/
  Cognithor.sln
  Cognithor/
    Cognithor.csproj
    Program.cs              -- Entry point, single-instance mutex
    AppShell.cs             -- NotifyIcon, ContextMenu, health timer
    ProcessManager.cs       -- Job Object via P/Invoke, process spawn/kill
    HealthChecker.cs        -- HTTP health polling, status enum
    Resources/
      app_icon.ico          -- copied from flutter_app/windows/runner/resources/
      icon_green.ico        -- healthy state
      icon_yellow.ico       -- starting state
      icon_red.ico          -- error state
```

## Key Components

### ProcessManager.cs

Responsibilities:
- Create a Windows Job Object with `JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE`
- Spawn child processes and assign them to the job
- Track PIDs for individual restart
- Provide `KillAll()` for clean shutdown

P/Invoke signatures needed:
- `CreateJobObject`, `SetInformationJobObject`, `AssignProcessToJobObject` from kernel32.dll
- Use `JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE` so that closing the job handle kills all assigned processes

Process spawn:
- Python: `<install_dir>\python\python.exe -m cognithor --no-cli --api-port 8741`
- Ollama: `<install_dir>\ollama\ollama.exe serve` (if `ollama.exe` exists)
- Both spawned with `CREATE_NO_WINDOW` to suppress console popups
- Working directory: `<install_dir>`

### AppShell.cs

Responsibilities:
- Create `NotifyIcon` with icon and tooltip
- Build `ContextMenuStrip` with menu items
- Handle double-click (open browser)
- Handle Quit (call `ProcessManager.KillAll()`, `Application.Exit()`)
- Handle Restart (call `ProcessManager.RestartBackend()`)
- Update icon based on `HealthChecker` status
- Single-instance enforcement via named Mutex (`Global\CognithorAppShell`)

### HealthChecker.cs

Responsibilities:
- `System.Windows.Forms.Timer` at 10-second interval
- `HttpClient.GetAsync("http://localhost:8741/api/v1/health")`
- Parse response, emit `StatusChanged` event
- States: `Starting`, `Healthy`, `Unhealthy`, `Stopped`
- Timeout: 3 seconds per request
- On transition to `Stopped`: show balloon notification

### Program.cs

```csharp
[STAThread]
static void Main(string[] args)
{
    // Single instance check
    using var mutex = new Mutex(true, @"Global\CognithorAppShell", out bool created);
    if (!created) { /* activate existing instance */ return; }

    Application.EnableVisualStyles();
    Application.SetHighDpiMode(HighDpiMode.PerMonitorV2);

    var shell = new AppShell(args);
    Application.Run();
}
```

## Build & Packaging

### Cognithor.csproj

```xml
<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <OutputType>WinExe</OutputType>
    <TargetFramework>net8.0-windows</TargetFramework>
    <UseWindowsForms>true</UseWindowsForms>
    <ApplicationIcon>Resources\app_icon.ico</ApplicationIcon>
    <PublishSingleFile>true</PublishSingleFile>
    <SelfContained>true</SelfContained>
    <RuntimeIdentifier>win-x64</RuntimeIdentifier>
    <PublishTrimmed>true</PublishTrimmed>
    <AssemblyName>Cognithor</AssemblyName>
    <Version>0.92.1</Version>
    <Company>Cognithor</Company>
    <Product>Cognithor Agent OS</Product>
  </PropertyGroup>
</Project>
```

Build command: `dotnet publish -c Release -r win-x64 --self-contained -p:PublishSingleFile=true -p:PublishTrimmed=true`

Expected output: single `Cognithor.exe` (~12-15 MB)

### Integration into build_installer.py

New step `step_launcher_exe()`:
1. Check `dotnet` SDK is available
2. Run `dotnet publish` in `launcher/Cognithor/`
3. Copy `Cognithor.exe` to `installer/build/`

### Integration into cognithor.iss (Inno Setup)

- Desktop shortcut: `Cognithor.exe` (not `cognithor.bat`)
- Start menu shortcut: `Cognithor.exe`
- `cognithor.bat` remains for CLI users who run from terminal
- Add `Cognithor.exe` to installed files

## Path Discovery

`Cognithor.exe` needs to find the embedded Python and Ollama. Strategy:

1. Look for `python\python.exe` relative to own directory (installer layout)
2. Fall back to `where python` on PATH
3. Ollama: check `ollama\ollama.exe` relative, then `%LOCALAPPDATA%\Programs\Ollama\ollama.exe`

Config file (optional): `cognithor-launcher.json` next to the exe, overrides paths.

## Icon States

| State | Icon | Tooltip |
|-------|------|---------|
| Starting | Yellow owl | "Cognithor - Starting..." |
| Healthy | Green owl | "Cognithor - Running" |
| Unhealthy | Red owl | "Cognithor - Backend error" |
| Stopped | Red owl | "Cognithor - Backend stopped" |

Icon variants are the same base owl icon with a small colored dot overlay in the bottom-right corner. Generated from `app_icon.ico` at build time or shipped as separate `.ico` files.

## Testing

- Manual: launch `Cognithor.exe`, verify tray icon, open UI, restart, quit
- Verify Task Manager shows "Cognithor" under Apps
- Verify killing `Cognithor.exe` in Task Manager also kills Python + Ollama
- Verify closing the last window does NOT exit (stays in tray)
- Verify double-click opens browser
- Verify restart recovers from crashed Python

## Out of Scope

- Auto-start on Windows login (can be added later via registry key)
- Windows Service mode (separate feature)
- macOS/Linux equivalents (separate design)
- Flutter desktop embedding in the wrapper (use browser for now)

## Migration

- Existing `.bat` launcher stays functional for CLI/terminal users
- Installer switches default shortcut from `.bat` to `.exe`
- No breaking changes to the Python backend
