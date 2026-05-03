# dbt.ps1 — wrapper that loads .env then forwards all args to dbt
# Usage: .\dbt.ps1 run --select staging
#        .\dbt.ps1 test --select mart
#        .\dbt.ps1 debug

param([Parameter(ValueFromRemainingArguments)]$args)

$envFile = Join-Path $PSScriptRoot ".env"

if (-not (Test-Path $envFile)) {
    Write-Error ".env file not found at $envFile"
    exit 1
}

# Load each KEY=VALUE line from .env into the current shell session
Get-Content $envFile | ForEach-Object {
    if ($_ -match '^\s*([^#][^=]+)=(.*)$') {
        $key   = $Matches[1].Trim()
        $value = $Matches[2].Trim()
        [System.Environment]::SetEnvironmentVariable($key, $value, 'Process')
    }
}

# Run dbt from inside the project folder
$dbtExe = Join-Path $PSScriptRoot ".venv\Scripts\dbt.exe"
$projectDir = Join-Path $PSScriptRoot "sales_win_predictor"

Push-Location $projectDir
try {
    & $dbtExe @args
} finally {
    Pop-Location
}
