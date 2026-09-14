param(
    [Parameter(Mandatory=$true)]
    [string]$Dest
)

$ErrorActionPreference = 'Stop'

$RouterVersion = if ($env:ROUTER_VERSION) { $env:ROUTER_VERSION } else { '0.3.60' }

Write-Host "Fetching 9router@$RouterVersion from npm..."

$Scratch = New-Item -ItemType Directory -Path (Join-Path $env:TEMP "9router-fetch-$([guid]::NewGuid())")
try {
    Push-Location $Scratch
    '{"name":"_fetch","version":"0.0.0","private":true}' | Out-File -Encoding utf8 -NoNewline package.json
    & npm install "9router@$RouterVersion" --no-save --no-audit --no-fund --silent --ignore-scripts
    if ($LASTEXITCODE -ne 0) { throw "npm install 9router@$RouterVersion failed" }

    $Src = Join-Path $Scratch 'node_modules\9router\app'
    if (-not (Test-Path $Src)) {
        throw "9router@$RouterVersion did not install to expected layout ($Src missing)"
    }

    Pop-Location

    if (Test-Path $Dest) { Remove-Item -Recurse -Force $Dest }
    New-Item -ItemType Directory -Force -Path $Dest | Out-Null

    robocopy $Src $Dest /E /NJH /NJS /NDL /NFL /NP /MT:8 | Out-Null
    if ($LASTEXITCODE -ge 8) { throw "robocopy failed staging 9router (exit $LASTEXITCODE)" }
    $global:LASTEXITCODE = 0

    Write-Host "9router staged at: $Dest"
} finally {
    if (Test-Path $Scratch) { Remove-Item -Recurse -Force $Scratch }
}
