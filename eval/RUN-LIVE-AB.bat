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
REM A remote file bridge cannot delete files, so a git command run through one
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
    echo   This is almost certainly stale ^(a remote bridge cannot delete files^).
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
    echo   Install Git for Windows, or check the branch out manually.
    echo.
    pause
    exit /b 1
)
echo Current branch: !CURRENT!

REM --- pick up the branch from the bundle ------------------------------------
REM The branch arrives as a git bundle rather than being fetched into this
REM repository directly, because doing that through its file bridge is what
REM leaves the index.lock above behind. Fetching here runs on Windows, where git
REM can clean up after itself.
if exist "measured-evidence-v1.bundle" (
    echo Reading measured-evidence-v1.bundle ...
    git fetch -f "measured-evidence-v1.bundle" feat/measured-evidence-v1:refs/bundle/measured-evidence-v1 >nul 2>&1
    if errorlevel 1 (
        echo   Could not read the bundle. Continuing with the branch already in
        echo   this repository, which may be older than the delivered bundle.
    ) else (
        if /i "!CURRENT!"=="feat/measured-evidence-v1" (
            REM Already on the branch: fast-forward onto the delivered commit.
            REM --ff-only so nothing is ever rewritten or discarded silently.
            git merge --ff-only refs/bundle/measured-evidence-v1 >nul 2>&1
            if errorlevel 1 (
                echo.
                echo   Could not fast-forward onto the delivered commit. Usually this
                echo   means generated files from a previous run are modified in your
                echo   working tree. They are reproducible outputs, so either:
                echo     git stash
                echo   or discard them:
                echo     git checkout -- eval/results
                echo   then run this again. Nothing was changed.
                echo.
                pause
                exit /b 1
            )
            echo   Up to date with the delivered commit.
        ) else (
            git branch -f feat/measured-evidence-v1 refs/bundle/measured-evidence-v1 >nul 2>&1
            echo   Branch updated from the bundle.
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
        echo Resolve the message above rather than forcing the switch.
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
    echo   Review eval\results\ab-summary-cohere.json for the measured result.
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
