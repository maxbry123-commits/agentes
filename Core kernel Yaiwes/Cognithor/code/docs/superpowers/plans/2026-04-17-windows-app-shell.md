# Windows App Shell Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the ghost `python.exe` process with a proper `Cognithor.exe` that shows in the system tray, groups child processes via Job Objects, and provides clean shutdown.

**Architecture:** A C# .NET 8 WinForms app (`Cognithor.exe`) that creates a Windows Job Object, spawns Python + Ollama as children, shows a system tray icon with context menu, and polls the backend health endpoint to reflect status. Single-file self-contained publish (~12-15 MB).

**Tech Stack:** C# / .NET 8 / WinForms / Win32 P/Invoke (Job Objects) / Inno Setup

---

## File Map

| File | Action | Responsibility |
|------|--------|---------------|
| `launcher/Cognithor/Cognithor.csproj` | Create | Project file: WinExe, net8.0-windows, WinForms, self-contained |
| `launcher/Cognithor/Program.cs` | Create | Entry point, single-instance mutex |
| `launcher/Cognithor/ProcessManager.cs` | Create | Job Object P/Invoke, spawn/kill children |
| `launcher/Cognithor/HealthChecker.cs` | Create | HTTP health polling, status enum + event |
| `launcher/Cognithor/AppShell.cs` | Create | NotifyIcon, ContextMenu, wire health → icon |
| `launcher/Cognithor/Resources/app_icon.ico` | Copy | From `flutter_app/windows/runner/resources/app_icon.ico` |
| `installer/build_installer.py` | Modify | Add `step_launcher_exe()` between step 4 and 5 |
| `installer/cognithor.iss` | Modify | Add `Cognithor.exe` to files, switch shortcuts |

---

### Task 1: Project Scaffold + Build Verification

**Files:**
- Create: `launcher/Cognithor/Cognithor.csproj`
- Create: `launcher/Cognithor/Program.cs`
- Copy: `launcher/Cognithor/Resources/app_icon.ico`

- [ ] **Step 1: Create directory structure**

```bash
mkdir -p "launcher/Cognithor/Resources"
cp "flutter_app/windows/runner/resources/app_icon.ico" "launcher/Cognithor/Resources/app_icon.ico"
```

- [ ] **Step 2: Create Cognithor.csproj**

```xml
<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <OutputType>WinExe</OutputType>
    <TargetFramework>net8.0-windows</TargetFramework>
    <UseWindowsForms>true</UseWindowsForms>
    <ApplicationIcon>Resources\app_icon.ico</ApplicationIcon>
    <AssemblyName>Cognithor</AssemblyName>
    <RootNamespace>Cognithor</RootNamespace>
    <Version>0.92.1</Version>
    <Company>Cognithor</Company>
    <Product>Cognithor Agent OS</Product>
    <Description>Cognithor App Shell — system tray launcher</Description>
  </PropertyGroup>
  <ItemGroup>
    <Content Include="Resources\app_icon.ico">
      <CopyToOutputDirectory>PreserveNewest</CopyToOutputDirectory>
    </Content>
  </ItemGroup>
</Project>
```

- [ ] **Step 3: Create minimal Program.cs**

```csharp
using System;
using System.Threading;
using System.Windows.Forms;

namespace Cognithor;

static class Program
{
    [STAThread]
    static void Main(string[] args)
    {
        using var mutex = new Mutex(true, @"Global\CognithorAppShell", out bool created);
        if (!created)
        {
            MessageBox.Show("Cognithor is already running.", "Cognithor",
                MessageBoxButtons.OK, MessageBoxIcon.Information);
            return;
        }

        Application.EnableVisualStyles();
        Application.SetHighDpiMode(HighDpiMode.PerMonitorV2);
        Application.SetCompatibleTextRenderingDefault(false);

        // Placeholder — will be replaced with AppShell in Task 4
        var icon = new NotifyIcon
        {
            Icon = new System.Drawing.Icon("Resources\\app_icon.ico"),
            Text = "Cognithor - Starting...",
            Visible = true,
        };
        icon.DoubleClick += (_, _) => MessageBox.Show("Cognithor is running.");

        Application.ApplicationExit += (_, _) => { icon.Visible = false; icon.Dispose(); };
        Application.Run();
    }
}
```

- [ ] **Step 4: Build and verify**

Run:
```bash
cd launcher/Cognithor
dotnet build
```
Expected: Build succeeded, 0 errors. Output in `bin/Debug/net8.0-windows/Cognithor.exe`.

- [ ] **Step 5: Run smoke test**

Run: `dotnet run --project launcher/Cognithor` (manually verify tray icon appears, then close via Task Manager).

- [ ] **Step 6: Commit**

```bash
git add launcher/
git commit -m "feat(launcher): scaffold C# app shell with tray icon"
```

---

### Task 2: ProcessManager — Job Objects + Child Spawning

**Files:**
- Create: `launcher/Cognithor/ProcessManager.cs`

- [ ] **Step 1: Create ProcessManager.cs with Job Object P/Invoke**

```csharp
using System;
using System.ComponentModel;
using System.Diagnostics;
using System.IO;
using System.Runtime.InteropServices;

namespace Cognithor;

sealed class ProcessManager : IDisposable
{
    // --- Win32 P/Invoke for Job Objects ---

    [DllImport("kernel32.dll", CharSet = CharSet.Unicode, SetLastError = true)]
    static extern IntPtr CreateJobObject(IntPtr lpJobAttributes, string? lpName);

    [DllImport("kernel32.dll", SetLastError = true)]
    static extern bool SetInformationJobObject(IntPtr hJob, int jobInfoClass,
        ref JOBOBJECT_EXTENDED_LIMIT_INFORMATION info, int cbInfoLength);

    [DllImport("kernel32.dll", SetLastError = true)]
    static extern bool AssignProcessToJobObject(IntPtr hJob, IntPtr hProcess);

    [DllImport("kernel32.dll", SetLastError = true)]
    static extern bool CloseHandle(IntPtr hObject);

    const int JobObjectExtendedLimitInformation = 9;
    const uint JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE = 0x00002000;

    [StructLayout(LayoutKind.Sequential)]
    struct JOBOBJECT_BASIC_LIMIT_INFORMATION
    {
        public long PerProcessUserTimeLimit;
        public long PerJobUserTimeLimit;
        public uint LimitFlags;
        public UIntPtr MinimumWorkingSetSize;
        public UIntPtr MaximumWorkingSetSize;
        public uint ActiveProcessLimit;
        public UIntPtr Affinity;
        public uint PriorityClass;
        public uint SchedulingClass;
    }

    [StructLayout(LayoutKind.Sequential)]
    struct IO_COUNTERS
    {
        public ulong ReadOperationCount;
        public ulong WriteOperationCount;
        public ulong OtherOperationCount;
        public ulong ReadTransferCount;
        public ulong WriteTransferCount;
        public ulong OtherTransferCount;
    }

    [StructLayout(LayoutKind.Sequential)]
    struct JOBOBJECT_EXTENDED_LIMIT_INFORMATION
    {
        public JOBOBJECT_BASIC_LIMIT_INFORMATION BasicLimitInformation;
        public IO_COUNTERS IoInfo;
        public UIntPtr ProcessMemoryLimit;
        public UIntPtr JobMemoryLimit;
        public UIntPtr PeakProcessMemoryUsed;
        public UIntPtr PeakJobMemoryUsed;
    }

    // --- Fields ---

    readonly IntPtr _jobHandle;
    readonly string _baseDir;
    Process? _pythonProcess;
    Process? _ollamaProcess;

    public ProcessManager()
    {
        _baseDir = AppContext.BaseDirectory;
        _jobHandle = CreateJobObject(IntPtr.Zero, "CognithorJobObject");
        if (_jobHandle == IntPtr.Zero)
            throw new Win32Exception(Marshal.GetLastWin32Error());

        var info = new JOBOBJECT_EXTENDED_LIMIT_INFORMATION();
        info.BasicLimitInformation.LimitFlags = JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE;
        if (!SetInformationJobObject(_jobHandle, JobObjectExtendedLimitInformation,
                ref info, Marshal.SizeOf(info)))
            throw new Win32Exception(Marshal.GetLastWin32Error());
    }

    // --- Path Discovery ---

    string FindPython()
    {
        var local = Path.Combine(_baseDir, "python", "python.exe");
        if (File.Exists(local)) return local;

        var pathPython = FindOnPath("python.exe");
        if (pathPython != null) return pathPython;

        throw new FileNotFoundException("Python not found. Reinstall Cognithor.");
    }

    string? FindOllama()
    {
        var local = Path.Combine(_baseDir, "ollama", "ollama.exe");
        if (File.Exists(local)) return local;

        var appData = Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData);
        var system = Path.Combine(appData, "Programs", "Ollama", "ollama.exe");
        if (File.Exists(system)) return system;

        return FindOnPath("ollama.exe");
    }

    static string? FindOnPath(string exe)
    {
        var pathVar = Environment.GetEnvironmentVariable("PATH") ?? "";
        foreach (var dir in pathVar.Split(Path.PathSeparator))
        {
            var full = Path.Combine(dir.Trim(), exe);
            if (File.Exists(full)) return full;
        }
        return null;
    }

    // --- Spawn ---

    Process SpawnAndAssign(string exe, string args, bool createWindow = false)
    {
        var psi = new ProcessStartInfo
        {
            FileName = exe,
            Arguments = args,
            WorkingDirectory = _baseDir,
            UseShellExecute = false,
            CreateNoWindow = !createWindow,
        };
        var proc = Process.Start(psi)
            ?? throw new InvalidOperationException($"Failed to start {exe}");

        AssignProcessToJobObject(_jobHandle, proc.Handle);
        return proc;
    }

    public void StartAll()
    {
        StartOllama();
        StartPython();
    }

    void StartOllama()
    {
        var ollamaPath = FindOllama();
        if (ollamaPath == null) return;

        // Don't start if already running
        foreach (var p in Process.GetProcessesByName("ollama"))
        {
            if (!p.HasExited) return;
        }

        _ollamaProcess = SpawnAndAssign(ollamaPath, "serve");
    }

    void StartPython()
    {
        var pythonPath = FindPython();
        _pythonProcess = SpawnAndAssign(pythonPath, "-m cognithor --no-cli --api-port 8741");
    }

    public bool IsPythonRunning =>
        _pythonProcess is { HasExited: false };

    public void RestartBackend()
    {
        if (_pythonProcess is { HasExited: false })
        {
            try { _pythonProcess.Kill(entireProcessTree: true); } catch { }
            _pythonProcess.WaitForExit(5000);
        }
        StartPython();
    }

    public void KillAll()
    {
        if (_pythonProcess is { HasExited: false })
            try { _pythonProcess.Kill(entireProcessTree: true); } catch { }

        if (_ollamaProcess is { HasExited: false })
            try { _ollamaProcess.Kill(entireProcessTree: true); } catch { }
    }

    public void Dispose()
    {
        KillAll();
        if (_jobHandle != IntPtr.Zero)
            CloseHandle(_jobHandle);
    }
}
```

- [ ] **Step 2: Build and verify no compile errors**

Run:
```bash
cd launcher/Cognithor
dotnet build
```
Expected: Build succeeded, 0 errors.

- [ ] **Step 3: Commit**

```bash
git add launcher/Cognithor/ProcessManager.cs
git commit -m "feat(launcher): add ProcessManager with Job Objects and child spawning"
```

---

### Task 3: HealthChecker — HTTP Polling + Status Events

**Files:**
- Create: `launcher/Cognithor/HealthChecker.cs`

- [ ] **Step 1: Create HealthChecker.cs**

```csharp
using System;
using System.Net.Http;
using System.Windows.Forms;

namespace Cognithor;

enum AppStatus { Starting, Healthy, Unhealthy, Stopped }

sealed class HealthChecker : IDisposable
{
    readonly HttpClient _http;
    readonly System.Windows.Forms.Timer _timer;
    AppStatus _lastStatus = AppStatus.Starting;

    public event Action<AppStatus, AppStatus>? StatusChanged;

    public AppStatus CurrentStatus => _lastStatus;

    public HealthChecker(int intervalMs = 10_000)
    {
        _http = new HttpClient { Timeout = TimeSpan.FromSeconds(3) };
        _timer = new System.Windows.Forms.Timer { Interval = intervalMs };
        _timer.Tick += async (_, _) => await PollAsync();
    }

    public void Start() => _timer.Start();
    public void Stop() => _timer.Stop();

    async System.Threading.Tasks.Task PollAsync()
    {
        AppStatus newStatus;
        try
        {
            var resp = await _http.GetAsync("http://localhost:8741/api/v1/health");
            newStatus = resp.IsSuccessStatusCode ? AppStatus.Healthy : AppStatus.Unhealthy;
        }
        catch
        {
            newStatus = AppStatus.Stopped;
        }

        if (newStatus != _lastStatus)
        {
            var prev = _lastStatus;
            _lastStatus = newStatus;
            StatusChanged?.Invoke(prev, newStatus);
        }
    }

    public void Dispose()
    {
        _timer.Stop();
        _timer.Dispose();
        _http.Dispose();
    }
}
```

- [ ] **Step 2: Build and verify**

Run:
```bash
cd launcher/Cognithor
dotnet build
```
Expected: Build succeeded, 0 errors.

- [ ] **Step 3: Commit**

```bash
git add launcher/Cognithor/HealthChecker.cs
git commit -m "feat(launcher): add HealthChecker with HTTP polling and status events"
```

---

### Task 4: AppShell — Tray Icon, Menu, Wiring

**Files:**
- Create: `launcher/Cognithor/AppShell.cs`
- Modify: `launcher/Cognithor/Program.cs` (replace placeholder)

- [ ] **Step 1: Create AppShell.cs**

```csharp
using System;
using System.Diagnostics;
using System.Drawing;
using System.Windows.Forms;

namespace Cognithor;

sealed class AppShell : IDisposable
{
    readonly ProcessManager _processes;
    readonly HealthChecker _health;
    readonly NotifyIcon _trayIcon;
    readonly ToolStripMenuItem _statusItem;

    static readonly string Version = typeof(AppShell).Assembly
        .GetCustomAttribute<System.Reflection.AssemblyInformationalVersionAttribute>()
        ?.InformationalVersion ?? "dev";

    public AppShell(string[] args)
    {
        _processes = new ProcessManager();
        _health = new HealthChecker();

        // --- Context Menu ---
        var openItem = new ToolStripMenuItem("Open Command Center");
        openItem.Click += (_, _) => OpenBrowser();
        openItem.Font = new Font(openItem.Font, FontStyle.Bold);

        _statusItem = new ToolStripMenuItem("Status: Starting...") { Enabled = false };

        var restartItem = new ToolStripMenuItem("Restart Backend");
        restartItem.Click += (_, _) =>
        {
            SetStatus(AppStatus.Starting);
            _processes.RestartBackend();
        };

        var quitItem = new ToolStripMenuItem("Quit Cognithor");
        quitItem.Click += (_, _) => Shutdown();

        var versionItem = new ToolStripMenuItem($"v{Version}") { Enabled = false };

        var menu = new ContextMenuStrip();
        menu.Items.Add(openItem);
        menu.Items.Add(_statusItem);
        menu.Items.Add(new ToolStripSeparator());
        menu.Items.Add(restartItem);
        menu.Items.Add(quitItem);
        menu.Items.Add(new ToolStripSeparator());
        menu.Items.Add(versionItem);

        // --- Tray Icon ---
        _trayIcon = new NotifyIcon
        {
            Icon = LoadIcon(),
            Text = "Cognithor - Starting...",
            ContextMenuStrip = menu,
            Visible = true,
        };
        _trayIcon.DoubleClick += (_, _) => OpenBrowser();

        // --- Health Monitor ---
        _health.StatusChanged += (prev, next) =>
        {
            SetStatus(next);

            if (next == AppStatus.Stopped && prev != AppStatus.Starting)
            {
                _trayIcon.ShowBalloonTip(5000, "Cognithor",
                    "Backend has stopped. Right-click to restart.",
                    ToolTipIcon.Error);
            }
        };

        // --- Start ---
        _processes.StartAll();
        _health.Start();
    }

    void SetStatus(AppStatus status)
    {
        var (text, label) = status switch
        {
            AppStatus.Starting  => ("Cognithor - Starting...",  "Status: Starting..."),
            AppStatus.Healthy   => ("Cognithor - Running",      "Status: Running"),
            AppStatus.Unhealthy => ("Cognithor - Backend error", "Status: Error"),
            AppStatus.Stopped   => ("Cognithor - Backend stopped", "Status: Stopped"),
            _ => ("Cognithor", "Status: Unknown"),
        };
        _trayIcon.Text = text;
        _statusItem.Text = label;
    }

    static Icon LoadIcon()
    {
        var path = System.IO.Path.Combine(AppContext.BaseDirectory, "Resources", "app_icon.ico");
        if (System.IO.File.Exists(path))
            return new Icon(path);
        return SystemIcons.Application;
    }

    static void OpenBrowser()
    {
        Process.Start(new ProcessStartInfo
        {
            FileName = "http://localhost:8741",
            UseShellExecute = true,
        });
    }

    void Shutdown()
    {
        _health.Stop();
        _processes.KillAll();
        _trayIcon.Visible = false;
        Application.Exit();
    }

    public void Dispose()
    {
        _health.Dispose();
        _processes.Dispose();
        _trayIcon.Dispose();
    }
}
```

- [ ] **Step 2: Update Program.cs to use AppShell**

Replace the entire content of `launcher/Cognithor/Program.cs` with:

```csharp
using System;
using System.Threading;
using System.Windows.Forms;

namespace Cognithor;

static class Program
{
    [STAThread]
    static void Main(string[] args)
    {
        using var mutex = new Mutex(true, @"Global\CognithorAppShell", out bool created);
        if (!created)
        {
            MessageBox.Show("Cognithor is already running.\nCheck the system tray.",
                "Cognithor", MessageBoxButtons.OK, MessageBoxIcon.Information);
            return;
        }

        Application.EnableVisualStyles();
        Application.SetHighDpiMode(HighDpiMode.PerMonitorV2);
        Application.SetCompatibleTextRenderingDefault(false);

        using var shell = new AppShell(args);
        Application.Run();
    }
}
```

- [ ] **Step 3: Build and verify**

Run:
```bash
cd launcher/Cognithor
dotnet build
```
Expected: Build succeeded, 0 errors.

- [ ] **Step 4: Manual smoke test**

Run: `dotnet run --project launcher/Cognithor`

Verify:
- Tray icon appears near the clock
- Right-click shows context menu with all items
- "Open Command Center" opens browser (may show connection refused if backend not installed at this path — that's OK)
- "Quit Cognithor" exits cleanly
- Task Manager shows "Cognithor" under Apps (not as "python.exe")

- [ ] **Step 5: Commit**

```bash
git add launcher/Cognithor/AppShell.cs launcher/Cognithor/Program.cs
git commit -m "feat(launcher): add AppShell with tray icon, menu, and health wiring"
```

---

### Task 5: Publish as Single-File EXE

**Files:**
- Modify: `launcher/Cognithor/Cognithor.csproj` (add publish properties)

- [ ] **Step 1: Update .csproj with publish profile**

Add inside the existing `<PropertyGroup>`:

```xml
    <PublishSingleFile>true</PublishSingleFile>
    <SelfContained>true</SelfContained>
    <RuntimeIdentifier>win-x64</RuntimeIdentifier>
    <PublishTrimmed>true</PublishTrimmed>
    <TrimMode>partial</TrimMode>
```

Note: `TrimMode=partial` is needed because WinForms uses reflection for component initialization. Full trimming breaks `NotifyIcon`.

- [ ] **Step 2: Publish and verify**

Run:
```bash
cd launcher/Cognithor
dotnet publish -c Release
```
Expected: `bin/Release/net8.0-windows/win-x64/publish/Cognithor.exe` exists, ~12-20 MB.

- [ ] **Step 3: Verify published exe runs standalone**

Run: `bin/Release/net8.0-windows/win-x64/publish/Cognithor.exe` directly (no dotnet needed).

Verify: tray icon appears, same behavior as debug run.

- [ ] **Step 4: Commit**

```bash
git add launcher/Cognithor/Cognithor.csproj
git commit -m "feat(launcher): configure single-file self-contained publish"
```

---

### Task 6: Integrate into build_installer.py

**Files:**
- Modify: `installer/build_installer.py:359-375` (add step between launcher and inno)

- [ ] **Step 1: Add step_launcher_exe() function**

Add this function before `step_inno_setup()` in `installer/build_installer.py`:

```python
def step_launcher_exe() -> Path:
    """Step 5: Build Cognithor.exe (C# app shell)."""
    print("\n=== Step 5: Launcher EXE ===")

    launcher_proj = PROJECT_ROOT / "launcher" / "Cognithor" / "Cognithor.csproj"
    if not launcher_proj.exists():
        print(f"  [SKIP] {launcher_proj} not found")
        return Path("")

    dotnet = shutil.which("dotnet")
    if dotnet is None:
        print("  [SKIP] dotnet SDK not found — using .bat launcher only")
        return Path("")

    publish_dir = BUILD_DIR / "launcher_publish"
    subprocess.run(
        [
            dotnet, "publish", str(launcher_proj),
            "-c", "Release",
            "-r", "win-x64",
            "--self-contained",
            "-p:PublishSingleFile=true",
            "-p:PublishTrimmed=true",
            "-p:TrimMode=partial",
            "-o", str(publish_dir),
        ],
        check=True,
    )

    exe = publish_dir / "Cognithor.exe"
    if not exe.exists():
        print("  [ERROR] Cognithor.exe not found after publish")
        return Path("")

    dest = BUILD_DIR / "Cognithor.exe"
    shutil.copy2(exe, dest)
    print(f"  [OK] {dest} ({dest.stat().st_size / 1024 / 1024:.1f} MB)")
    return dest
```

- [ ] **Step 2: Update main() to call the new step**

In the `main()` function of `build_installer.py`, change from:

```python
    step_launcher()
    installer = step_inno_setup(version, python_dir, ollama_dir, flutter_dir)
```

To:

```python
    step_launcher()
    step_launcher_exe()
    installer = step_inno_setup(version, python_dir, ollama_dir, flutter_dir)
```

Note: `step_inno_setup` becomes step 6 in the log output.

- [ ] **Step 3: Commit**

```bash
git add installer/build_installer.py
git commit -m "feat(installer): add step_launcher_exe() to build Cognithor.exe"
```

---

### Task 7: Integrate into Inno Setup Script

**Files:**
- Modify: `installer/cognithor.iss:69-101` (files + icons sections)

- [ ] **Step 1: Add Cognithor.exe to [Files] section**

Add after the `cognithor.bat` line (line 74) in `cognithor.iss`:

```ini
; App shell (tray launcher)
Source: "{#BuildDir}\Cognithor.exe"; DestDir: "{app}"; Components: core; Flags: ignoreversion; Check: FileExists(ExpandConstant('{#BuildDir}\Cognithor.exe'))
```

- [ ] **Step 2: Update [Icons] section to use Cognithor.exe**

Replace the existing `[Icons]` section (lines 97-101) with:

```ini
[Icons]
Name: "{group}\Cognithor"; Filename: "{app}\Cognithor.exe"; IconFilename: "{app}\app_icon.ico"; Comment: "Start Cognithor"
Name: "{group}\Cognithor CLI"; Filename: "cmd.exe"; Parameters: "/k ""{app}\cognithor.bat"""; IconFilename: "{app}\app_icon.ico"; Comment: "Cognithor Command Line"
Name: "{group}\Uninstall Cognithor"; Filename: "{uninstallexe}"
Name: "{autodesktop}\Cognithor"; Filename: "{app}\Cognithor.exe"; IconFilename: "{app}\app_icon.ico"; Comment: "Start Cognithor"
```

Key changes: desktop + start menu shortcuts now point to `Cognithor.exe` instead of `cognithor.bat --ui`.

- [ ] **Step 3: Update [Run] section for post-install**

Replace the existing `[Run]` section (line 111-112) with:

```ini
[Run]
; Post-install: offer to start Cognithor
Filename: "{app}\Cognithor.exe"; Description: "Start Cognithor"; \
    Flags: nowait postinstall skipifsilent; Check: FileExists(ExpandConstant('{app}\Cognithor.exe'))
```

- [ ] **Step 4: Add Cognithor.exe to [UninstallDelete]**

Add to the `[UninstallDelete]` section:

```ini
Type: files; Name: "{app}\Cognithor.exe"
```

- [ ] **Step 5: Commit**

```bash
git add installer/cognithor.iss
git commit -m "feat(installer): switch shortcuts from .bat to Cognithor.exe"
```

---

### Task 8: Final Integration Test

- [ ] **Step 1: Full build from scratch**

Run:
```bash
cd launcher/Cognithor
dotnet publish -c Release -r win-x64 --self-contained -p:PublishSingleFile=true -p:PublishTrimmed=true
```
Verify: `Cognithor.exe` produced, ~12-20 MB.

- [ ] **Step 2: Copy exe to installer build dir and test**

```bash
cp launcher/Cognithor/bin/Release/net8.0-windows/win-x64/publish/Cognithor.exe installer/build/
```

- [ ] **Step 3: Manual acceptance test checklist**

Run `Cognithor.exe` from the install directory (or build dir with Python + Ollama available):

- [ ] Tray icon appears in system tray
- [ ] Task Manager shows "Cognithor" under Apps
- [ ] Right-click menu shows all items (Open, Status, Restart, Quit, version)
- [ ] "Open Command Center" opens browser to localhost:8741
- [ ] "Quit Cognithor" kills all child processes (verify Python + Ollama gone from Task Manager)
- [ ] Killing `Cognithor.exe` in Task Manager also kills Python + Ollama (Job Object)
- [ ] Second launch shows "already running" dialog (single-instance mutex)
- [ ] Health status changes icon tooltip when backend is up vs down

- [ ] **Step 4: Final commit**

```bash
git add -A
git commit -m "feat(launcher): Windows App Shell complete — tray icon, Job Objects, health monitor"
```
