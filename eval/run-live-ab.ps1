# Run the live Cohere A/B end to end on Windows.
#
#   powershell -ExecutionPolicy Bypass -File eval\run-live-ab.ps1
#
# Reads RESOLVEFLOW_COHERE_API_KEY from .env in the repository root. Makes an
# Embed v4 pass (2 calls, cached to disk), then the 32-run A/B against Cohere
# Chat and Rerank, then regenerates the published documents.
#
# The runner enforces its own budget: a 2-scenario dry pass runs first, the
# projection is printed, and the full pass is refused if the projection exceeds
# the cap. Retries against a 429 count against the budget. It aborts rather
# than overspending.

$ErrorActionPreference = "Stop"
$repo = Split-Path -Parent $PSScriptRoot
Set-Location $repo

Write-Host "== ResolveFlow live A/B ==" -ForegroundColor Cyan
Write-Host "repo: $repo"

# --- Python -----------------------------------------------------------------
$py = $null
foreach ($candidate in @("py -3", "python", "python3")) {
    $parts = $candidate.Split(" ")
    if (Get-Command $parts[0] -ErrorAction SilentlyContinue) { $py = $candidate; break }
}
if (-not $py) { throw "No Python found on PATH. Install Python 3.11+ and retry." }
Write-Host "python: $py"

# --- Virtual environment ----------------------------------------------------
$venv = Join-Path $repo ".venv-live"
if (-not (Test-Path (Join-Path $venv "Scripts\python.exe"))) {
    Write-Host "creating $venv ..." -ForegroundColor Yellow
    Invoke-Expression "$py -m venv `"$venv`""
}
$vpy = Join-Path $venv "Scripts\python.exe"

Write-Host "installing dependencies ..." -ForegroundColor Yellow
& $vpy -m pip install --upgrade pip --quiet
& $vpy -m pip install -e . --quiet
if ($LASTEXITCODE -ne 0) { throw "dependency install failed" }

# --- Credentials ------------------------------------------------------------
# Loaded into this process only. Never written to any artifact, log, or commit.
$envFile = Join-Path $repo ".env"
if (-not (Test-Path $envFile)) { throw "No .env found at $envFile" }
Get-Content $envFile | ForEach-Object {
    if ($_ -match '^\s*([A-Z0-9_]+)\s*=\s*(.*)\s*$') {
        $name = $Matches[1]
        $value = $Matches[2].Trim('"').Trim("'")
        if ($value) { [Environment]::SetEnvironmentVariable($name, $value, "Process") }
    }
}
if (-not $env:RESOLVEFLOW_COHERE_API_KEY) {
    throw "RESOLVEFLOW_COHERE_API_KEY is not set in .env"
}
Write-Host "api key: loaded (not displayed)" -ForegroundColor Green

$env:PYTHONPATH = "python;."

# --- 1. Embed the corpus once ----------------------------------------------
Write-Host "`n== step 1/4: Embed v4 pass (cached; skipped if already complete) ==" -ForegroundColor Cyan
& $vpy -m resolveflow.eval.embed_corpus
if ($LASTEXITCODE -ne 0) { throw "embed pass failed; no A/B was attempted" }

# --- 2. The A/B -------------------------------------------------------------
Write-Host "`n== step 2/4: live A/B, 16 scenarios x 2 builds x 1 trial (higher tool-round budget) ==" -ForegroundColor Cyan
Write-Host "One repetition (n=32 per build) at max_tool_rounds=4 so Command A+ can finish"
Write-Host "A 2-scenario dry pass measures the real cost first and scales the trial"
Write-Host "count down to whatever fits under the cap. It never exceeds it."
Write-Host "This sleeps to respect the per-minute limits and will take several minutes."
& $vpy -m resolveflow.eval.ab_cli --provider cohere --max-calls 300 --repetitions 1
$abExit = $LASTEXITCODE
if ($abExit -eq 4) {
    Write-Host "`nABORTED: the dry pass projected more calls than the cap allows." -ForegroundColor Red
    Write-Host "See eval\results\dry-pass-abort.json. No full run was performed." -ForegroundColor Red
    exit 4
}
if ($abExit -eq 3) {
    Write-Host "`nABORTED: the call budget was exhausted mid-run." -ForegroundColor Red
    exit 3
}
if ($abExit -ne 0) { throw "the A/B failed with exit code $abExit" }

# --- 3. Publish -------------------------------------------------------------
Write-Host "`n== step 3/4: regenerate published documents ==" -ForegroundColor Cyan
& $vpy -m resolveflow.eval.publish cohere
if ($LASTEXITCODE -ne 0) { throw "publish failed" }

Copy-Item "eval\results\ab-site-cohere.json" "apps\web\public\snapshots\" -Force

# --- 4. Verify every published checksum against disk ------------------------
Write-Host "`n== step 4/4: verify checksums ==" -ForegroundColor Cyan
& $vpy -m resolveflow.eval.verify_checksums cohere
if ($LASTEXITCODE -ne 0) {
    Write-Host "CHECKSUM MISMATCH. The manifest does not describe the files on disk." -ForegroundColor Red
    Write-Host "Do not publish these artifacts until this is understood." -ForegroundColor Red
    exit 5
}

# --- optional: safety_mode probe --------------------------------------------
# 12 extra calls. Records which (safety_mode, tools/documents) combinations the
# API accepts and which it refuses. Skipped automatically if the budget spent by
# the A/B leaves no comfortable headroom.
Write-Host "`n== optional: safety_mode acceptance probe (12 calls) ==" -ForegroundColor Cyan
$probe = Read-Host "Run the safety_mode probe? [y/N]"
if ($probe -eq "y" -or $probe -eq "Y") {
    & $vpy -m resolveflow.eval.safety_mode_probe
    if ($LASTEXITCODE -ne 0) {
        Write-Host "probe failed; the A/B artifacts above are unaffected." -ForegroundColor Yellow
    }
}

Write-Host "`n== done ==" -ForegroundColor Green
Write-Host "Artifacts written to eval\results\:"
Write-Host "  ab-summary-cohere.json      full result, every run"
Write-Host "  provider-calls-cohere.json  every provider call, hashed"
Write-Host "  results-table-cohere.md     the table"
Write-Host "  README.md                   methodology, regenerated"
Write-Host "  SHA256SUMS-cohere.md        checksums"
Write-Host "  runs\cohere\                per-run snapshots, live only"
Write-Host "  safety-mode-probe-cohere.json   if the probe was run"
Write-Host ""
Write-Host "Read results-table-cohere.md first. The sections that matter:"
Write-Host "  'Headline rates with 95% confidence intervals'"
Write-Host "  'guarded-v1 minus unsafe-v0'  - anything spanning zero is NOT a result"
Write-Host "  'Governance tax'              - what enforcement cost"
Write-Host "`nCommit them, then send eval\results\ab-summary-cohere.json back if you"
Write-Host "want the write-up updated."
