@echo off
setlocal EnableExtensions

if "%~1"=="" (
  echo Usage: %~nx0 prudence^|justice^|courage^|temperance
  exit /b 2
)

set VIRTUE=%~1

for %%I in ("%~dp0..\..\..") do set REPO=%%~fI
cd /d "%REPO%"

set PREFIX=scripturevec14_qwen3_14b_canon_sample32_%VIRTUE%_a32_ratio_l10_v1
set PYTHON=%REPO%\.venv\Scripts\python.exe
if not exist "%PYTHON%" set PYTHON=C:\Users\sethcodex\work\virtue-bench-2\.venv\Scripts\python.exe

set VECTORS=%REPO%\results\experiments\scripturevec14\scripturevec14_qwen3_14b_canon_groups_sample32_ratio_l10_v1_vectors.pt
set TARGETS=canon_torah canon_history canon_wisdom canon_major_prophets canon_minor_prophets canon_gospels canon_acts canon_pauline canon_general_epistles canon_revelation

if not exist results mkdir results

set PYTHONPATH=%REPO%\src
set PYTHONUNBUFFERED=1
set PYTHONFAULTHANDLER=1
set PYTHONIOENCODING=utf-8
set TORCH_SHOW_CPP_STACKTRACES=1
set TORCH_DISABLE_ADDR2LINE=1
set PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
set VIRTUE_BENCH_CUDA_DEVICE=cuda:0
set VIRTUE_BENCH_HF_DEVICE_MAP=
set VIRTUE_BENCH_HF_MAX_MEMORY=
set VIRTUE_BENCH_HF_LOAD_IN_4BIT=1

echo STARTED > "results\%PREFIX%.status"

"%PYTHON%" -X faulthandler -u -m virtue_bench.cli iconoclast ^
  --model C:\Users\sethcodex\models\Qwen3-14B ^
  --subset %VIRTUE% ^
  --stage ratio ^
  --runs 1 ^
  --limit 10 ^
  --temperature 0.0 ^
  --seed 42 ^
  --condition-profile scripturevec35 ^
  --scripture-targets %TARGETS% ^
  --vectors "%VECTORS%" ^
  --scripture-runtime-alpha 32.0 ^
  --preflight-policy off ^
  --output-prefix experiments/scripturevec14/%PREFIX% ^
  >> "results\%PREFIX%_wrapper_console.log" 2>&1

if errorlevel 1 (
  echo FAILED > "results\%PREFIX%.status"
  exit /b 1
)

echo FINISHED > "results\%PREFIX%.status"
endlocal
