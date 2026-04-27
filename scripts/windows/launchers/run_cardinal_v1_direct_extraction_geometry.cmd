@echo off
setlocal

for %%I in ("%~dp0..\..\..") do set REPO=%%~fI
cd /d "%REPO%"

set PYTHON=%REPO%\.venv\Scripts\python.exe
if not exist "%PYTHON%" set PYTHON=C:\Users\sethcodex\work\virtue-bench-2\.venv\Scripts\python.exe

set RUN_ROOT=%REPO%\..
set EXTERNAL_CORPUS=%RUN_ROOT%\lex-et-iustitia\subprojects\cardinal-virtue-geometry\data\generated\frozen_v1\selected_balanced_corpus.jsonl
set OUTDIR=%REPO%\results\cardinal_virtue_geometry\direct_extraction_v1

if not exist results mkdir results
if not exist results\cardinal_virtue_geometry mkdir results\cardinal_virtue_geometry
if not exist "%OUTDIR%" mkdir "%OUTDIR%"

set PYTHONPATH=%REPO%\src
set PYTHONUNBUFFERED=1
set PYTHONFAULTHANDLER=1
set PYTHONIOENCODING=utf-8
set TORCH_SHOW_CPP_STACKTRACES=1
set PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True

call :build_and_analyze scripture_other_contrast
if errorlevel 1 exit /b 1
call :build_and_analyze scripture_dual_contrast
if errorlevel 1 exit /b 1

endlocal
exit /b 0

:build_and_analyze
set METHOD=%~1
set PREFIX=cardinal_v1_direct_%METHOD%_extract_v1
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
  --extraction-method %METHOD% ^
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
  --output-json "%OUTDIR%\%PREFIX%_geometry.json" ^
  --output-md "%OUTDIR%\%PREFIX%_geometry.md" ^
  >> "%LOG%" 2>&1

if errorlevel 1 (
  echo FAILED > "%STATUS%"
  exit /b 1
)

echo FINISHED > "%STATUS%"
exit /b 0
