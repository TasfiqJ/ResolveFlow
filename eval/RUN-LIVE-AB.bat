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

REM --- stale index.lock ------------------------------------------------------
REM Claude's file bridge cannot delete files, so a git command run through it
REM leaves .git\index.lock behind. That lock blocks every later git write. Only
REM offer to clear it when no git process is actually running.
if exist ".git\index.lock" (
    set "GITRUNNING="
    for /f "tokens=1" %%p in ('tasklist /fi "imagename eq git.exe" /nh 2^>nul ^| findstr /i "git.exe"') do set "GITRUNNING=1"
    echo.
    if defined GITRUNNING (
        echo   .git\index.lock exists AND a git.exe process is running.
        echo   Something is genuinely using this repository right now.
        echo   Close it and re-run. Not touching the lock.
        echo.
        pause
        exit /b 1
    )
    echo   Found a leftover .git\index.lock with no git process running.
    echo   This is almost certainly stale ^(Claude's bridge cannot delete files^).
    echo   Removing it only discards an empty lock; no repository data is lost.
    echo.
    set "RMLOCK="
    set /p "RMLOCK=Remove the stale lock and continue? [y/N] "
    if /i not "!RMLOCK!"=="y" (
        echo Cancelled. Nothing was changed.
        echo.
        pause
        exit /b 1
    )
    del /f /q ".git\index.lock" >nul 2>&1
    if exist ".git\index.lock" (
        echo   Could not remove the lock. Delete this file in Explorer, then re-run:
        echo     %CD%\.git\index.lock
        echo.
        pause
        exit /b 1
    )
    echo   Removed.
)

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

REM --- pick up the branch from the bundle ------------------------------------
REM Claude delivers the branch as a git bundle rather than fetching it into this
REM repository directly, because doing that through its file bridge is what
REM leaves the index.lock above behind. Fetching here runs on Windows, where
REM git can clean up after itself.
if exist "measured-evidence-v1.bundle" (
    if /i not "!CURRENT!"=="feat/measured-evidence-v1" (
        echo Updating feat/measured-evidence-v1 from measured-evidence-v1.bundle ...
        git fetch -f "measured-evidence-v1.bundle" feat/measured-evidence-v1:feat/measured-evidence-v1
        if errorlevel 1 (
            echo.
            echo   Could not read the bundle. Continuing with the branch already
            echo   in this repository, which may be older than Claude intended.
            echo.
        )
    )
)

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
