# Download Konnect MCP server binary for Windows (v0.2.2)
$ErrorActionPreference = "Stop"

$version = "v0.2.2"
$repoRoot = Split-Path -Parent $PSScriptRoot
$binDir = Join-Path $repoRoot "bin"
$exePath = Join-Path $binDir "konnect.exe"
$zipUrl = "https://github.com/mixelpixx/Konnect/releases/download/$version/konnect-v0.2.2-x86_64-pc-windows-msvc.zip"
$zipPath = Join-Path $env:TEMP "konnect-$version-windows.zip"

New-Item -ItemType Directory -Force -Path $binDir | Out-Null
Write-Host "Downloading Konnect $version..."
Invoke-WebRequest -Uri $zipUrl -OutFile $zipPath
Expand-Archive -Path $zipPath -DestinationPath $binDir -Force
Remove-Item $zipPath -Force

if (-not (Test-Path $exePath)) {
    Write-Error "Expected $exePath after extract"
}

& $exePath --version
Write-Host "Installed: $exePath"
Write-Host "Reload MCP in Cursor to pick up konnect server."
