@echo off
setlocal

for %%I in ("%~dp0..\..\..") do set REPO=%%~fI
cd /d "%REPO%"

set PYTHON=%REPO%\.venv\Scripts\python.exe
if not exist "%PYTHON%" set PYTHON=C:\Users\sethcodex\work\virtue-bench-2\.venv\Scripts\python.exe

set RUN_ROOT=%REPO%\..
set EXTERNAL_CORPUS=%RUN_ROOT%\lex-et-iustitia\subprojects\cardinal-virtue-geometry\data\generated\frozen_v1\selected_balanced_corpus.jsonl
set VECTOR_DIR=%REPO%\results\cardinal_virtue_geometry\candidate_vectors_v1

if not exist results mkdir results

set PYTHONPATH=%REPO%\src
set PYTHONUNBUFFERED=1
set PYTHONFAULTHANDLER=1
set PYTHONIOENCODING=utf-8
set TORCH_SHOW_CPP_STACKTRACES=1
set PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True

call :run_recipe partial_center_0p75
call :run_recipe scripture_plus_accent_1p0_1p0
call :run_recipe mixed_generic_other_1p0_1p0

endlocal
exit /b 0

:run_recipe
set RECIPE=%~1
set VECTOR=%VECTOR_DIR%\cardinal_v1_candidate_%RECIPE%_vectors.pt

call :run_one prudence prudence_scripture cardinal_v1_candidate_%RECIPE%_alpha6p0_ratio_l20_prudence_v1 6.0
if errorlevel 1 exit /b 1
call :run_one justice justice_scripture cardinal_v1_candidate_%RECIPE%_alpha6p0_ratio_l20_justice_v1 6.0
if errorlevel 1 exit /b 1
call :run_one courage fortitude_scripture cardinal_v1_candidate_%RECIPE%_alpha6p0_ratio_l20_fortitude_v1 6.0
if errorlevel 1 exit /b 1
call :run_one temperance temperance_scripture cardinal_v1_candidate_%RECIPE%_alpha6p0_ratio_l20_temperance_v1 6.0
if errorlevel 1 exit /b 1

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
  --vectors "%VECTOR%" ^
  --extraction-method auto ^
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
