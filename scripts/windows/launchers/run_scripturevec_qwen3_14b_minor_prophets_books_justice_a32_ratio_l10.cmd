@echo off
setlocal EnableExtensions

for %%I in ("%~dp0..\..\..") do set REPO=%%~fI
cd /d "%REPO%"

set PREFIX=scripturevec14_qwen3_14b_minor_prophets_books_justice_a32_ratio_l10_v1
set PYTHON=%REPO%\.venv\Scripts\python.exe
if not exist "%PYTHON%" set PYTHON=C:\Users\sethcodex\work\virtue-bench-2\.venv\Scripts\python.exe

set CORPUS=%REPO%\results\experiments\scripturevec14\canon_discovery\canon_books_v1.jsonl
set TARGETS=book_hos book_jol book_amo book_oba book_jon book_mic book_nam book_hab book_zep book_hag book_zec book_mal

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
  --limit 10 ^
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
