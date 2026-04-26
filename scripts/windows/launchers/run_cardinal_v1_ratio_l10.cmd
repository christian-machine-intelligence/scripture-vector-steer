@echo off
setlocal

for %%I in ("%~dp0..\..\..") do set REPO=%%~fI
cd /d "%REPO%"

set PREFIX=cardinal_v1_qwen35_ratio_l10_v1
set PYTHON=%REPO%\.venv\Scripts\python.exe
if not exist "%PYTHON%" set PYTHON=C:\Users\sethcodex\work\virtue-bench-2\.venv\Scripts\python.exe

set RUN_ROOT=%REPO%\..
set EXTERNAL_CORPUS=%RUN_ROOT%\lex-et-iustitia\subprojects\cardinal-virtue-geometry\data\generated\frozen_v1\selected_balanced_corpus.jsonl

if not exist results mkdir results

set PYTHONPATH=%REPO%\src
set PYTHONUNBUFFERED=1
set PYTHONFAULTHANDLER=1
set PYTHONIOENCODING=utf-8
set TORCH_SHOW_CPP_STACKTRACES=1
set PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True

echo STARTED > "results\%PREFIX%.status"

"%PYTHON%" -X faulthandler -u -m virtue_bench.cli iconoclast ^
  --model Qwen/Qwen3.5-9B ^
  --stage ratio ^
  --runs 1 ^
  --limit 10 ^
  --temperature 0.0 ^
  --seed 42 ^
  --conditions control scripture_steer scripture_null_control ^
  --scripture-targets prudence_scripture justice_scripture fortitude_scripture temperance_scripture ^
  --external-scripture-corpus "%EXTERNAL_CORPUS%" ^
  --extraction-method scripture_contrast ^
  --scripture-runtime-alpha 3.0 ^
  --preflight-policy warn ^
  --output-prefix %PREFIX% ^
  >> "results\%PREFIX%_wrapper_console.log" 2>&1

if errorlevel 1 (
  echo FAILED > "results\%PREFIX%.status"
  exit /b 1
)

echo FINISHED > "results\%PREFIX%.status"
endlocal
