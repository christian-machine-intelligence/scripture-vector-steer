@echo off
setlocal

for %%I in ("%~dp0..\..\..") do set REPO=%%~fI
cd /d "%REPO%"

set PYTHON=%REPO%\.venv\Scripts\python.exe
if not exist "%PYTHON%" set PYTHON=C:\Users\sethcodex\work\virtue-bench-2\.venv\Scripts\python.exe

set RUN_ROOT=%REPO%\..
set EXTERNAL_CORPUS=%RUN_ROOT%\lex-et-iustitia\subprojects\cardinal-virtue-geometry\data\generated\frozen_v1\selected_balanced_corpus.jsonl
set GEOM_DIR=%REPO%\results\cardinal_virtue_geometry\layer_window_v1

if not exist results mkdir results
if not exist results\cardinal_virtue_geometry mkdir results\cardinal_virtue_geometry
if not exist "%GEOM_DIR%" mkdir "%GEOM_DIR%"

set PYTHONPATH=%REPO%\src
set PYTHONUNBUFFERED=1
set PYTHONFAULTHANDLER=1
set PYTHONIOENCODING=utf-8
set TORCH_SHOW_CPP_STACKTRACES=1
set PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True

call :run_center 16
if errorlevel 1 exit /b 1
call :run_center 24
if errorlevel 1 exit /b 1
call :run_center 31
if errorlevel 1 exit /b 1

endlocal
exit /b 0

:run_center
set CENTER=%~1
set PREFIX=cardinal_v1_layer_l%CENTER%_scripture_contrast_extract_v1
set VECTOR=%REPO%\results\%PREFIX%_vectors.pt
set STATUS=%REPO%\results\%PREFIX%.status
set LOG=%REPO%\results\%PREFIX%_wrapper_console.log

echo STARTED > "%STATUS%"

"%PYTHON%" -X faulthandler -u -m virtue_bench.cli iconoclast ^
  --model Qwen/Qwen3.5-9B ^
  --stage ratio ^
  --subset courage ^
  --runs 1 ^
  --limit 1 ^
  --temperature 0.0 ^
  --seed 42 ^
  --conditions control scripture_steer scripture_null_control ^
  --scripture-targets prudence_scripture justice_scripture fortitude_scripture temperance_scripture ^
  --external-scripture-corpus "%EXTERNAL_CORPUS%" ^
  --extraction-method scripture_contrast ^
  --window-center %CENTER% ^
  --scripture-runtime-alpha 3.0 ^
  --preflight-policy warn ^
  --output-prefix %PREFIX% ^
  >> "%LOG%" 2>&1

if errorlevel 1 (
  echo FAILED > "%STATUS%"
  exit /b 1
)

"%PYTHON%" -X faulthandler -u scripts\analyze_cardinal_vector_geometry.py ^
  --vectors "%VECTOR%" ^
  --output-json "%GEOM_DIR%\%PREFIX%_geometry.json" ^
  --output-md "%GEOM_DIR%\%PREFIX%_geometry.md" ^
  >> "%LOG%" 2>&1

if errorlevel 1 (
  echo FAILED > "%STATUS%"
  exit /b 1
)

call :run_behavior %CENTER% prudence prudence_scripture
if errorlevel 1 exit /b 1
call :run_behavior %CENTER% justice justice_scripture
if errorlevel 1 exit /b 1
call :run_behavior %CENTER% courage fortitude_scripture
if errorlevel 1 exit /b 1
call :run_behavior %CENTER% temperance temperance_scripture
if errorlevel 1 exit /b 1

echo FINISHED > "%STATUS%"
exit /b 0

:run_behavior
set CENTER=%~1
set SUBSET=%~2
set TARGET=%~3
set EXTRACT_PREFIX=cardinal_v1_layer_l%CENTER%_scripture_contrast_extract_v1
set VECTOR=%REPO%\results\%EXTRACT_PREFIX%_vectors.pt
set PREFIX=cardinal_v1_layer_l%CENTER%_scripture_contrast_alpha6p0_ratio_l20_%TARGET%_v1
set PREFIX=%PREFIX:_scripture=%

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
  --scripture-runtime-alpha 6.0 ^
  --preflight-policy warn ^
  --output-prefix %PREFIX% ^
  >> "results\%PREFIX%_wrapper_console.log" 2>&1

if errorlevel 1 (
  echo FAILED > "results\%PREFIX%.status"
  exit /b 1
)

echo FINISHED > "results\%PREFIX%.status"
exit /b 0
