# Extract a datasheet PDF to markdown, images, and YAML tables.
param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$RemainingArgs
)

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
Set-Location $repoRoot

if ($RemainingArgs.Count -eq 0) {
    uv run python scripts/extract_datasheet.py --help
    exit 1
}

& uv run python scripts/extract_datasheet.py @RemainingArgs
exit $LASTEXITCODE
