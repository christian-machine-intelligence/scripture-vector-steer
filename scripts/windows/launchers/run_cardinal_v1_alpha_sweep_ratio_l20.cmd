@echo off
setlocal

for %%I in ("%~dp0..\..\..") do set REPO=%%~fI
cd /d "%REPO%"

set PYTHON=%REPO%\.venv\Scripts\python.exe
if not exist "%PYTHON%" set PYTHON=C:\Users\sethcodex\work\virtue-bench-2\.venv\Scripts\python.exe

set RUN_ROOT=%REPO%\..
set EXTERNAL_CORPUS=%RUN_ROOT%\lex-et-iustitia\subprojects\cardinal-virtue-geometry\data\generated\frozen_v1\selected_balanced_corpus.jsonl
set VECTOR_ARTIFACT=%REPO%\results\cardinal_v1_qwen35_ratio_l10_v1_vectors.pt

if not exist results mkdir results

set PYTHONPATH=%REPO%\src
set PYTHONUNBUFFERED=1
set PYTHONFAULTHANDLER=1
set PYTHONIOENCODING=utf-8
set TORCH_SHOW_CPP_STACKTRACES=1
set PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True

call :run_alpha 1p5 1.5
call :run_alpha 6p0 6.0

endlocal
exit /b 0

:run_alpha
set ALABEL=%~1
set ALPHA=%~2

call :run_one prudence prudence_scripture cardinal_v1_alpha%ALABEL%_ratio_l20_prudence_v1 %ALPHA%
call :run_one justice justice_scripture cardinal_v1_alpha%ALABEL%_ratio_l20_justice_v1 %ALPHA%
call :run_one courage fortitude_scripture cardinal_v1_alpha%ALABEL%_ratio_l20_fortitude_v1 %ALPHA%
call :run_one temperance temperance_scripture cardinal_v1_alpha%ALABEL%_ratio_l20_temperance_v1 %ALPHA%
exit /b 0

:run_one
set SUBSET=%~1
set TARGET=%~2
set PREFIX=%~3
set ALPHA=%~4

echo STARTED > "results\%PREFIX%.status"

"%PYTHON%" -X faulthandler -u -m virtue_bench.cli iconoclast ^
  --model Qwen/Qwen3.5-9B ^
  --stage ratio ^
  --subset %SUBSET% ^
  --runs 1 ^
  --limit 20 ^
  --temperature 0.0 ^
  --seed 42 ^
  --conditions control scripture_steer scripture_null_control ^
  --scripture-targets %TARGET% ^
  --external-scripture-corpus "%EXTERNAL_CORPUS%" ^
  --vectors "%VECTOR_ARTIFACT%" ^
  --extraction-method scripture_contrast ^
  --scripture-runtime-alpha %ALPHA% ^
  --preflight-policy warn ^
  --output-prefix %PREFIX% ^
  >> "results\%PREFIX%_wrapper_console.log" 2>&1

if errorlevel 1 (
  echo FAILED > "results\%PREFIX%.status"
  exit /b 1
)

echo FINISHED > "results\%PREFIX%.status"
exit /b 0
