@echo off
setlocal

for %%I in ("%~dp0..\..\..") do set REPO=%%~fI
cd /d "%REPO%"

set PREFIX=cardinal_v1_reasoning_judge_v1
set PYTHON=%REPO%\.venv\Scripts\python.exe
if not exist "%PYTHON%" set PYTHON=C:\Users\sethcodex\work\virtue-bench-2\.venv\Scripts\python.exe

set INDIR=%REPO%\results
set OUTDIR=%REPO%\results\cardinal_virtue_geometry
set PILOT_PREFIX=cardinal_v1_qwen35_ratio_l10_v1
set LOGS=%INDIR%\%PILOT_PREFIX%_ratio_logs.json

if not exist "%OUTDIR%" mkdir "%OUTDIR%"

set PYTHONPATH=%REPO%\src
set PYTHONUNBUFFERED=1
set PYTHONFAULTHANDLER=1
set PYTHONIOENCODING=utf-8

echo STARTED > "%OUTDIR%\%PREFIX%.status"

"%PYTHON%" -X faulthandler -u scripts\analyze_cardinal_reasoning_judge.py ^
  --logs "%LOGS%" ^
  --output "%OUTDIR%\%PREFIX%.json" ^
  --summary "%OUTDIR%\%PREFIX%.md" ^
  --model Qwen/Qwen3.5-9B ^
  --temperature 0.0 ^
  --max-tokens 96 ^
  --timeout 120 ^
  >> "%OUTDIR%\%PREFIX%_console.log" 2>&1

if errorlevel 1 (
  echo FAILED > "%OUTDIR%\%PREFIX%.status"
  exit /b 1
)

echo FINISHED > "%OUTDIR%\%PREFIX%.status"
endlocal
