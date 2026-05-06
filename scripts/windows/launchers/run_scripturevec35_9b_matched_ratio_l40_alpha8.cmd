@echo off
setlocal

for %%I in ("%~dp0..\..\..") do set REPO=%%~fI
cd /d "%REPO%"

set PYTHON=%REPO%\.venv\Scripts\python.exe
if not exist "%PYTHON%" set PYTHON=C:\Users\sethcodex\work\virtue-bench-2\.venv\Scripts\python.exe

set RUN_ROOT=%REPO%\..
set EXTERNAL_CORPUS=%RUN_ROOT%\lex-et-iustitia\subprojects\cardinal-virtue-geometry\data\generated\frozen_v1\selected_balanced_corpus.jsonl
set VECTOR_ARTIFACT=%REPO%\results\experiments\scripturevec35\scripturevec35_qwen35_9b_targets_ratio_l10_v1_vectors.pt

if not exist results mkdir results

set PYTHONPATH=%REPO%\src
set PYTHONUNBUFFERED=1
set PYTHONFAULTHANDLER=1
set PYTHONIOENCODING=utf-8
set TORCH_SHOW_CPP_STACKTRACES=1
set PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
set VIRTUE_BENCH_CUDA_DEVICE=cuda:0
set VIRTUE_BENCH_HF_LOAD_IN_4BIT=0

call :run_one prudence prudence_scripture scripturevec35_qwen35_9b_matched_alpha8_ratio_l40_prudence_v1
call :run_one justice justice_scripture scripturevec35_qwen35_9b_matched_alpha8_ratio_l40_justice_v1
call :run_one courage fortitude_scripture scripturevec35_qwen35_9b_matched_alpha8_ratio_l40_courage_v1
call :run_one temperance temperance_scripture scripturevec35_qwen35_9b_matched_alpha8_ratio_l40_temperance_v1

endlocal
exit /b 0

:run_one
set SUBSET=%~1
set TARGET=%~2
set PREFIX=%~3

echo STARTED > "results\%PREFIX%.status"

"%PYTHON%" -X faulthandler -u -m virtue_bench.cli iconoclast ^
  --model Qwen/Qwen3.5-9B ^
  --stage ratio ^
  --subset %SUBSET% ^
  --runs 1 ^
  --limit 40 ^
  --temperature 0.0 ^
  --seed 42 ^
  --conditions control scripture_steer scripture_negative_alpha scripture_null_control ^
  --scripture-targets %TARGET% ^
  --external-scripture-corpus "%EXTERNAL_CORPUS%" ^
  --vectors "%VECTOR_ARTIFACT%" ^
  --extraction-method scripture_contrast ^
  --scripture-runtime-alpha 8.0 ^
  --preflight-policy warn ^
  --output-prefix experiments/scripturevec35/%PREFIX% ^
  >> "results\%PREFIX%_wrapper_console.log" 2>&1

if errorlevel 1 (
  echo FAILED > "results\%PREFIX%.status"
  exit /b 1
)

echo FINISHED > "results\%PREFIX%.status"
exit /b 0
