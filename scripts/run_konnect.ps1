# MCP launcher — avoids Windows splitting command paths that contain spaces.
$repoRoot = Split-Path -Parent $PSScriptRoot
$exe = Join-Path $repoRoot "bin\konnect.exe"
if (-not (Test-Path $exe)) {
    Write-Error "Konnect not found at $exe. Run scripts/install_konnect.ps1 first."
    exit 1
}

if (-not $env:KICAD_API_SOCKET) {
    $socketPath = Join-Path $env:TEMP "kicad\api.sock"
    $env:KICAD_API_SOCKET = "ipc://$socketPath"
}

# Konnect ignores sym-lib-table in some paths (github.com/mixelpixx/Konnect/issues/105).
# Point KICAD10_SYMBOL_DIR at the configured symbol library so symbols resolve by name.
$globalSymDir = $null
$configPath = Join-Path $repoRoot "kicad-cursor.yaml"
if (Test-Path $configPath) {
    $inSymbolLibrary = $false
    foreach ($line in Get-Content $configPath) {
        if ($line -match '^\s*symbolLibrary:\s*$') {
            $inSymbolLibrary = $true
            continue
        }
        if ($inSymbolLibrary -and $line -match '^\s*path:\s*(.+)$') {
            $globalSymDir = $Matches[1].Trim()
            break
        }
        if ($inSymbolLibrary -and $line -match '^\S') {
            break
        }
    }
}
if (-not $globalSymDir -and $env:KICAD_SYMBOL_LIBRARY) {
    $globalSymDir = $env:KICAD_SYMBOL_LIBRARY
}
if ($globalSymDir -and (Test-Path (Join-Path $globalSymDir "global.kicad_sym"))) {
    $env:KICAD10_SYMBOL_DIR = $globalSymDir
}

& $exe @args
