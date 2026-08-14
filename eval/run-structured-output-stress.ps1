$ErrorActionPreference = "Stop"

$repo = Split-Path -Parent $PSScriptRoot
Set-Location $repo

Get-Content .env | ForEach-Object {
    if ($_ -match '^\s*([^#][^=]*)=(.*)$') {
        [Environment]::SetEnvironmentVariable($matches[1].Trim(), $matches[2].Trim(), 'Process')
    }
}

if (-not $env:RESOLVEFLOW_COHERE_API_KEY) {
    throw "RESOLVEFLOW_COHERE_API_KEY is not set in .env"
}

$python = Join-Path $repo '.venv-live\Scripts\python.exe'
if (-not (Test-Path $python)) {
    throw "The live Python environment is missing at .venv-live\Scripts\python.exe"
}

& $python -m resolveflow.eval.structured_output_stress
