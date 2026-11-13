<#
.SYNOPSIS
  Task #10: track the user-facing DOWNLOAD speed + verify the signature of the
  signed build, then hand off to validate_packaged.ps1 for install/startup. Does
  NOT publish anything (downloads from the draft release / run artifacts only).
.USAGE
  pwsh docs\perf\winv2\measure_download_install.ps1 -Tag v1.3.86
#>
param(
    [string]$Tag = 'v1.3.86',
    [string]$WorkDir = (Join-Path $env:TEMP "os-dl-$Tag")
)
$ErrorActionPreference = 'Stop'
New-Item -ItemType Directory -Force -Path $WorkDir | Out-Null

# 1. Download the signed installer (timed) -> download speed.
$sw = [Diagnostics.Stopwatch]::StartNew()
gh release download $Tag --pattern '*Setup*.exe' --dir $WorkDir --clobber
$sw.Stop()
$exe = Get-ChildItem $WorkDir -Filter '*Setup*.exe' | Select-Object -First 1
if (-not $exe) { throw "no Setup .exe for $Tag (is the draft release built? try: gh run download <id>)" }
$mb = [math]::Round($exe.Length / 1MB, 1)
$secs = [math]::Round($sw.Elapsed.TotalSeconds, 1)
$mbps = if ($secs -gt 0) { [math]::Round($mb / $secs, 1) } else { 'inf' }
Write-Host ("DOWNLOAD: {0} MB in {1}s ({2} MB/s) -> {3}" -f $mb, $secs, $mbps, $exe.Name)

# 2. Verify it is really code-signed.
$sig = Get-AuthenticodeSignature $exe.FullName
Write-Host ("SIGNATURE: {0}  signer={1}" -f $sig.Status, $sig.SignerCertificate.Subject)
if ($sig.Status -ne 'Valid') { Write-Warning "signature is NOT Valid -- stop and investigate before installing" }

Write-Host ""
Write-Host "Installer: $($exe.FullName)"
Write-Host "Next (install timing): note the clock, run the installer, then time until %APPDATA%\openswarm\data\backend.log appears."
Write-Host "Then: pwsh docs\perf\winv2\validate_packaged.ps1   (structural + cold/warm startup)"
