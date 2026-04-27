@echo off
setlocal

for %%I in ("%~dp0..\..\..") do set REPO=%%~fI
cd /d "%REPO%"

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

call :run_rank 2
if errorlevel 1 exit /b 1
call :run_rank 4
if errorlevel 1 exit /b 1
call :run_rank 8
if errorlevel 1 exit /b 1

endlocal
exit /b 0

:run_rank
set K=%~1
set EXTRACT_PREFIX=cardinal_v1_subspace_l24_k%K%_extract_v1
set VECTOR=%REPO%\results\%EXTRACT_PREFIX%_vectors.pt
set STATUS=%REPO%\results\%EXTRACT_PREFIX%.status
set LOG=%REPO%\results\%EXTRACT_PREFIX%_wrapper_console.log

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
  --scripture-targets fortitude_scripture ^
  --external-scripture-corpus "%EXTERNAL_CORPUS%" ^
  --extraction-method scripture_subspace_contrast ^
  --subspace-rank %K% ^
  --window-center 24 ^
  --scripture-runtime-alpha 3.0 ^
  --preflight-policy warn ^
  --output-prefix %EXTRACT_PREFIX% ^
  >> "%LOG%" 2>&1

if errorlevel 1 (
  echo FAILED > "%STATUS%"
  exit /b 1
)

echo FINISHED > "%STATUS%"

set PREFIX=cardinal_v1_subspace_l24_k%K%_alpha6p0_ratio_l20_fortitude_v1
echo STARTED > "results\%PREFIX%.status"

"%PYTHON%" -X faulthandler -u -m virtue_bench.cli iconoclast ^
  --model Qwen/Qwen3.5-9B ^
  --stage ratio ^
  --subset courage ^
  --runs 1 ^
  --limit 20 ^
  --temperature 0.0 ^
  --seed 42 ^
  --conditions control scripture_steer scripture_null_control ^
  --scripture-targets fortitude_scripture ^
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
