$ErrorActionPreference = "Stop"
$completionRepo = Split-Path -Parent $PSScriptRoot
Set-Location $completionRepo

$completionPython = Join-Path $completionRepo ".venv-live\Scripts\python.exe"
if (-not (Test-Path $completionPython)) {
    throw "The existing .venv-live environment is required."
}

$completionEnv = Join-Path $completionRepo ".env"
if (-not (Test-Path $completionEnv)) {
    throw "No .env file is available."
}
Get-Content $completionEnv | ForEach-Object {
    if ($_ -match '^\s*([A-Z0-9_]+)\s*=\s*(.*)\s*$') {
        $completionName = $Matches[1]
        $completionValue = $Matches[2].Trim('"').Trim("'")
        if ($completionValue) {
            [Environment]::SetEnvironmentVariable(
                $completionName,
                $completionValue,
                "Process"
            )
        }
    }
}
if (-not $env:RESOLVEFLOW_COHERE_API_KEY) {
    throw "RESOLVEFLOW_COHERE_API_KEY is unavailable."
}

$env:PYTHONPATH = "python;."
& $completionPython eval\run_completion_live.py
exit $LASTEXITCODE
