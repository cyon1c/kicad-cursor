# Invoke fetch_part.py from the kicad-cursor repo (LCSC -> global KiCad library).
param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$RemainingArgs
)

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
Set-Location $repoRoot

if ($RemainingArgs.Count -eq 0) {
    uv run python scripts/fetch_part.py --help
    exit 1
}

& uv run python scripts/fetch_part.py @RemainingArgs
exit $LASTEXITCODE
