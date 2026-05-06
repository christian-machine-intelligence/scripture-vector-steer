@echo off
setlocal EnableExtensions

for %%I in ("%~dp0..\..\..") do set REPO=%%~fI
cd /d "%REPO%"

set SWEEP=scripturevec14_qwen3_14b_general_biblical_courage_alpha_sweep_ratio_l10_v1
set PYTHON=%REPO%\.venv\Scripts\python.exe
if not exist "%PYTHON%" set PYTHON=C:\Users\sethcodex\work\virtue-bench-2\.venv\Scripts\python.exe

set TARGETS=psalms proverbs gospels romans petrine
set VECTOR_ARTIFACT=%REPO%\results\experiments\scripturevec14\scripturevec14_qwen3_14b_general_biblical_ratio_l10_v1_vectors.pt

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

set SWEEP_FAILED=0
echo STARTED > "results\%SWEEP%.status"

call :run_alpha 32.0 a032
call :run_alpha 48.0 a048
call :run_alpha 64.0 a064
call :run_alpha 96.0 a096

if "%SWEEP_FAILED%"=="1" (
  echo FAILED > "results\%SWEEP%.status"
  exit /b 1
)

echo FINISHED > "results\%SWEEP%.status"
endlocal
exit /b 0

:run_alpha
set ALPHA=%~1
set TAG=%~2
set PREFIX=scripturevec14_qwen3_14b_general_biblical_courage_alpha_sweep_ratio_l10_%TAG%_v1

if exist "results\%PREFIX%.status" (
  findstr /C:"FINISHED" "results\%PREFIX%.status" >nul
  if not errorlevel 1 (
    echo SKIPPED %PREFIX% already FINISHED
    exit /b 0
  )
)

echo STARTED > "results\%PREFIX%.status"

"%PYTHON%" -X faulthandler -u -m virtue_bench.cli iconoclast ^
  --model C:\Users\sethcodex\models\Qwen3-14B ^
  --stage ratio ^
  --subset courage ^
  --runs 1 ^
  --limit 10 ^
  --temperature 0.0 ^
  --seed 42 ^
  --condition-profile scripturevec35 ^
  --scripture-targets %TARGETS% ^
  --vectors "%VECTOR_ARTIFACT%" ^
  --extraction-method scripture_contrast ^
  --scripture-runtime-alpha %ALPHA% ^
  --preflight-policy warn ^
  --output-prefix experiments/scripturevec14/%PREFIX% ^
  >> "results\%PREFIX%_wrapper_console.log" 2>&1

if errorlevel 1 (
  echo FAILED > "results\%PREFIX%.status"
  set SWEEP_FAILED=1
  exit /b 0
)

echo FINISHED > "results\%PREFIX%.status"
exit /b 0
