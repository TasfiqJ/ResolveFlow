@echo off
REM Double-click to run the live Cohere A/B.
REM Works whether this file sits in the repo root or in the repo's eval\ folder.
REM Your API key is read from .env into this process only; it is never written
REM to any artifact, log, or commit.
setlocal enabledelayedexpansion

REM --- locate the repository -------------------------------------------------
cd /d "%~dp0"
if not exist ".git" if exist "..\.git" cd /d "%~dp0.."
if not exist ".git" (
    echo.
    echo   Could not find the ResolveFlow repository.
    echo   This file must sit in the repo root or in its eval\ folder.
    echo   Looked in: %CD%
    echo.
    pause
    exit /b 1
)

echo ==========================================================
echo   ResolveFlow live A/B
echo   repo: %CD%
echo ==========================================================
echo.

REM --- git must be usable ----------------------------------------------------
set "CURRENT="
for /f "usebackq tokens=*" %%b in (`git rev-parse --abbrev-ref HEAD 2^>nul`) do set "CURRENT=%%b"
if not defined CURRENT (
    echo   git is not on PATH, or this folder is not a git repository.
    echo   Install Git for Windows, or tell Claude and it will send a version
    echo   that does not need git.
    echo.
    pause
    exit /b 1
)
echo Current branch: !CURRENT!

REM --- branch ----------------------------------------------------------------
if /i not "!CURRENT!"=="feat/measured-evidence-v1" (
    echo.
    echo This needs the branch 'feat/measured-evidence-v1'.
    echo Your uncommitted changes are carried across; nothing is discarded.
    echo.
    set "GO="
    set /p "GO=Switch to it now? [y/N] "
    if /i not "!GO!"=="y" (
        echo Cancelled. Nothing was changed.
        echo.
        pause
        exit /b 1
    )
    git checkout feat/measured-evidence-v1
    if errorlevel 1 (
        echo.
        echo Branch switch failed. Nothing was run.
        echo Send the message above to Claude rather than forcing it.
        echo.
        pause
        exit /b 1
    )
)

if not exist "eval\run-live-ab.ps1" (
    echo.
    echo   eval\run-live-ab.ps1 is missing. The branch may not have checked out.
    echo.
    pause
    exit /b 1
)

echo.
powershell -NoProfile -ExecutionPolicy Bypass -File "eval\run-live-ab.ps1"
set "RC=!ERRORLEVEL!"

echo.
if "!RC!"=="0" (
    echo ==========================================================
    echo   Done. Artifacts are in eval\results\
    echo   Send eval\results\ab-summary-cohere.json back to Claude.
    echo ==========================================================
) else (
    echo ==========================================================
    echo   Stopped with exit code !RC!
    echo     4 = dry pass projected over the call cap; nothing more spent
    echo     3 = call budget exhausted mid-run
    echo     other = see the error above
    echo ==========================================================
)
echo.
pause
