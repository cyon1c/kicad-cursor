# Add kicad-cursor scripts\bin to the user PATH for fetch-part and other shims.
param(
    [switch]$Uninstall
)

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$binDir = Join-Path $repoRoot "scripts\bin"

if (-not (Test-Path $binDir)) {
    Write-Error "Bin directory not found: $binDir"
    exit 1
}

$userPath = [Environment]::GetEnvironmentVariable("Path", "User")
$pathParts = $userPath -split ";" | Where-Object { $_ -ne "" }

if ($Uninstall) {
    $newParts = $pathParts | Where-Object { $_ -ne $binDir }
    $newPath = ($newParts -join ";").TrimEnd(";")
    [Environment]::SetEnvironmentVariable("Path", $newPath, "User")
    Write-Host "Removed from user PATH: $binDir"
    exit 0
}

if ($pathParts -contains $binDir) {
    Write-Host "Already on user PATH: $binDir"
} else {
    $newPath = if ($userPath) { "$userPath;$binDir" } else { $binDir }
    [Environment]::SetEnvironmentVariable("Path", $newPath, "User")
    Write-Host "Added to user PATH: $binDir"
}

$env:Path = "$env:Path;$binDir"
Write-Host ""
Write-Host "Available commands (open a new terminal if a command is not found):"
Write-Host "  fetch-part C702003"
Write-Host "  fetch-part C702003 --symbol"
Write-Host "  extract-datasheet --pdf datasheets/bq25619.pdf"
Write-Host "  extract-datasheet --all"
