@echo off
setlocal EnableExtensions

set START_BATCH=%~1
if "%START_BATCH%"=="" set START_BATCH=01

set VERSION=%~2
if "%VERSION%"=="" set VERSION=1

for %%I in ("%~dp0..\..\..") do set REPO=%%~fI
set RESULTS=%REPO%\results\experiments\scripturevec14
set MANAGER=%~dp0run_scripturevec_qwen3_14b_chapter_hits_justice_confirmation_manager.ps1
set PREFIX=scripturevec14_qwen3_14b_chapter_hits_justice_a32_ratio_l40_manager_v%VERSION%

if not exist "%RESULTS%" mkdir "%RESULTS%"

start "ScriptureVec chapter-hit confirmation" /D "%REPO%" powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%MANAGER%" -StartBatch %START_BATCH% -Version %VERSION%

if errorlevel 1 (
  echo Failed to start confirmation manager.
  exit /b 1
)

echo Started %PREFIX% from batch %START_BATCH%.
endlocal
