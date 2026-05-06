@echo off
setlocal EnableExtensions

if "%~1"=="" (
  echo Usage: %~nx0 01^|02
  exit /b 2
)

set BATCH=%~1

for %%I in ("%~dp0..\..\..") do set REPO=%%~fI
cd /d "%REPO%"

set PYTHON=%REPO%\.venv\Scripts\python.exe
if not exist "%PYTHON%" set PYTHON=C:\Users\sethcodex\work\virtue-bench-2\.venv\Scripts\python.exe

set CORPUS=%REPO%\results\experiments\scripturevec14\canon_discovery\canon_books_v1.jsonl

if "%BATCH%"=="01" set TARGETS=book_deu book_num book_jdg book_1sa book_2ki book_1ch book_neh book_sng book_amo book_hos
if "%BATCH%"=="02" set TARGETS=book_lam book_act book_hab book_jhn book_luk book_mrk book_nam book_heb book_rev

if not defined TARGETS (
  echo Unknown batch: %BATCH%
  exit /b 2
)

set PREFIX=scripturevec14_qwen3_14b_books_justice_candidates_a32_ratio_l40_batch%BATCH%_v1

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
  --subset justice ^
  --stage ratio ^
  --runs 1 ^
  --limit 40 ^
  --temperature 0.0 ^
  --seed 42 ^
  --condition-profile scripturevec35 ^
  --scripture-targets %TARGETS% ^
  --external-scripture-corpus "%CORPUS%" ^
  --extraction-method scripture_contrast ^
  --alpha-candidates 0.5,1.0,2.0,3.0,4.0,6.0,8.0 ^
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
