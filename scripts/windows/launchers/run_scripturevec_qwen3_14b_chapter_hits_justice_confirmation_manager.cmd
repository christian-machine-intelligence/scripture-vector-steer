@echo off
setlocal EnableExtensions EnableDelayedExpansion

set START_BATCH=%~1
if "%START_BATCH%"=="" set START_BATCH=01

set VERSION=%~2
if "%VERSION%"=="" set VERSION=1

for %%I in ("%~dp0..\..\..") do set REPO=%%~fI
cd /d "%REPO%"

set RESULTS=%REPO%\results\experiments\scripturevec14
set BATCH_LAUNCHER=%~dp0run_scripturevec_qwen3_14b_chapter_hits_justice_a32_ratio_l40_batch.cmd
set PREFIX_BASE=scripturevec14_qwen3_14b_chapter_hits_justice_a32_ratio_l40
set MANAGER_PREFIX=%PREFIX_BASE%_manager_v%VERSION%
set MANAGER_LOG=%RESULTS%\%MANAGER_PREFIX%.log
set MANAGER_STATUS=%RESULTS%\%MANAGER_PREFIX%.status.txt

if not exist "%RESULTS%" mkdir "%RESULTS%"

set KNOWN_BATCH=
for %%B in (01 02 03 04) do if "%START_BATCH%"=="%%B" set KNOWN_BATCH=1
if not defined KNOWN_BATCH (
  echo Unknown start batch: %START_BATCH%
  exit /b 2
)

echo [%DATE% %TIME%] START manager from batch %START_BATCH%, version %VERSION% >> "%MANAGER_LOG%"
echo RUNNING %START_BATCH% > "%MANAGER_STATUS%"

set SHOULD_RUN=
for %%B in (01 02 03 04) do (
  if "%%B"=="%START_BATCH%" set SHOULD_RUN=1
  if defined SHOULD_RUN (
    call :RUN_BATCH %%B
    if errorlevel 1 exit /b 1
  )
)

echo [%DATE% %TIME%] COMPLETE all batches >> "%MANAGER_LOG%"
echo COMPLETED > "%MANAGER_STATUS%"
exit /b 0

:RUN_BATCH
set BATCH=%~1
set BATCH_PREFIX=%PREFIX_BASE%_batch%BATCH%_v%VERSION%
set RATIO_STATUS=%RESULTS%\%BATCH_PREFIX%_ratio.status.json

if exist "%RATIO_STATUS%" (
  findstr /C:"\"state\": \"completed\"" "%RATIO_STATUS%" >nul 2>&1
  if not errorlevel 1 (
    echo [%DATE% %TIME%] SKIP completed batch %BATCH% >> "%MANAGER_LOG%"
    exit /b 0
  )
)

echo [%DATE% %TIME%] START batch %BATCH% >> "%MANAGER_LOG%"
echo RUNNING %BATCH% > "%MANAGER_STATUS%"

call "%BATCH_LAUNCHER%" %BATCH% %VERSION%
set EXITCODE=%ERRORLEVEL%

if not "%EXITCODE%"=="0" (
  echo [%DATE% %TIME%] FAILED batch %BATCH% code %EXITCODE% >> "%MANAGER_LOG%"
  echo FAILED %BATCH% code %EXITCODE% > "%MANAGER_STATUS%"
  exit /b %EXITCODE%
)

echo [%DATE% %TIME%] FINISHED batch %BATCH% >> "%MANAGER_LOG%"
exit /b 0
