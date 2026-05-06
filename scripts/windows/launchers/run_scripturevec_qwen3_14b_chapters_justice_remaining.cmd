@echo off
setlocal EnableExtensions EnableDelayedExpansion

set VERSION=%~1
if "%VERSION%"=="" set VERSION=1

set BATCHES=02 03 04 05 06 07 08 09 10 11 12 13 14 15 16 17

echo [remaining] Starting strict-survivor chapter batches, version %VERSION%
echo [remaining] Repo root: %~dp0..\..\..

for %%B in (%BATCHES%) do (
  echo ===== BATCH %%B START %DATE% %TIME% =====
  call "%~dp0run_scripturevec_qwen3_14b_chapters_justice_a32_ratio_l10_batch.cmd" %%B %VERSION%
  set EXITCODE=!ERRORLEVEL!
  echo ===== BATCH %%B END code=!EXITCODE! %DATE% %TIME% =====
  if not "!EXITCODE!"=="0" (
    echo [remaining] Stopping after failed batch %%B.
    exit /b !EXITCODE!
  )
)

echo [remaining] Finished all strict-survivor chapter batches.
