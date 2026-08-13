@echo off
REM Double-click this file to run the live Cohere A/B.
REM It switches to the evaluation branch, runs the Embed v4 pass, the 32-run
REM A/B, and regenerates the published documents. Your API key is read from
REM .env into this process only and is never written to any artifact or commit.
setlocal
cd /d "%~dp0.."

echo ==========================================================
echo   ResolveFlow live A/B
echo   repo: %CD%
echo ==========================================================
echo.

for /f "tokens=*" %%b in ('git rev-parse --abbrev-ref HEAD') do set CURRENT=%%b
echo Current branch: %CURRENT%
if /i not "%CURRENT%"=="feat/measured-evidence-v1" (
    echo.
    echo This needs the branch 'feat/measured-evidence-v1'.
    echo Your uncommitted changes are carried across; nothing is discarded.
    set /p GO="Switch to it now? [y/N] "
    if /i not "%GO%"=="y" (
        echo Cancelled. Nothing was changed.
        pause
        exit /b 1
    )
    git checkout feat/measured-evidence-v1
    if errorlevel 1 (
        echo.
        echo Branch switch failed. Nothing was run.
        pause
        exit /b 1
    )
)

echo.
powershell -NoProfile -ExecutionPolicy Bypass -File "eval\run-live-ab.ps1"
set RC=%ERRORLEVEL%

echo.
if %RC%==0 (
    echo ==========================================================
    echo   Done. Artifacts are in eval\results\
    echo   Send ab-summary-cohere.json back to Claude.
    echo ==========================================================
) else (
    echo ==========================================================
    echo   Stopped with exit code %RC%.
    echo   4 = dry pass projected over the call cap, nothing spent
    echo   3 = call budget exhausted mid-run
    echo ==========================================================
)
echo.
pause
