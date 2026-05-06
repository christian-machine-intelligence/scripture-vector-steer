@echo off
setlocal EnableExtensions

for %%I in ("%~dp0..\..\..") do set REPO=%%~fI
cd /d "%REPO%"

set RUN=scripturevec14_qwen3_14b_confirmed_chapter_layerloc_v1
set PYTHON=%REPO%\.venv\Scripts\python.exe
if not exist "%PYTHON%" set PYTHON=C:\Users\sethcodex\work\virtue-bench-2\.venv\Scripts\python.exe

set CORPUS=%REPO%\results\experiments\scripturevec14\canon_discovery\canon_justice_chapter_confirmed_hits_v1.jsonl
set TARGETS=chapter_deu_16 chapter_jdg_07 chapter_jdg_09 chapter_num_11 chapter_num_22 chapter_num_27 chapter_1ch_09 chapter_1ch_29 chapter_act_07 chapter_act_11 chapter_act_16 chapter_act_27 chapter_heb_02 chapter_heb_07 chapter_heb_09 chapter_heb_10

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

set RUN_FAILED=0
echo STARTED > "results\%RUN%.status"

call :run_center_alpha 24 32.0 a032
call :run_center_alpha 28 32.0 a032
call :run_center_alpha 29 16.0 a016
call :run_center_alpha 29 24.0 a024
call :run_center_alpha 29 32.0 a032
call :run_center_alpha 29 48.0 a048
call :run_center_alpha 29 64.0 a064
call :run_center_alpha 29 96.0 a096
call :run_center_alpha 30 32.0 a032
call :run_center_alpha 31 16.0 a016
call :run_center_alpha 31 24.0 a024
call :run_center_alpha 31 32.0 a032
call :run_center_alpha 31 48.0 a048
call :run_center_alpha 31 64.0 a064
call :run_center_alpha 31 96.0 a096
call :run_center_alpha 32 16.0 a016
call :run_center_alpha 32 24.0 a024
call :run_center_alpha 32 32.0 a032
call :run_center_alpha 32 48.0 a048
call :run_center_alpha 32 64.0 a064
call :run_center_alpha 32 96.0 a096
call :run_center_alpha 33 32.0 a032
call :run_center_alpha 36 32.0 a032

if "%RUN_FAILED%"=="1" (
  echo FAILED > "results\%RUN%.status"
  exit /b 1
)

echo FINISHED > "results\%RUN%.status"
endlocal
exit /b 0

:run_center_alpha
set CENTER=%~1
set ALPHA=%~2
set TAG=%~3

call :extract_center %CENTER%
if errorlevel 1 (
  set RUN_FAILED=1
  exit /b 0
)

call :run_behavior %CENTER% %ALPHA% %TAG%
if errorlevel 1 (
  set RUN_FAILED=1
  exit /b 0
)

exit /b 0

:extract_center
set CENTER=%~1
set PREFIX=scripturevec14_qwen3_14b_confirmed_chapter_layerloc_l%CENTER%_extract_v1
set VECTOR=%REPO%\results\experiments\scripturevec14\%PREFIX%_vectors.pt

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
  --subset justice ^
  --runs 1 ^
  --limit 1 ^
  --temperature 0.0 ^
  --seed 42 ^
  --conditions control scripture_steer scripture_negative_alpha scripture_null_control ^
  --scripture-targets %TARGETS% ^
  --external-scripture-corpus "%CORPUS%" ^
  --extraction-method scripture_contrast ^
  --window-center %CENTER% ^
  --window-radius 3 ^
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
exit /b 0

:run_behavior
set CENTER=%~1
set ALPHA=%~2
set TAG=%~3
set EXTRACT_PREFIX=scripturevec14_qwen3_14b_confirmed_chapter_layerloc_l%CENTER%_extract_v1
set VECTOR=%REPO%\results\experiments\scripturevec14\%EXTRACT_PREFIX%_vectors.pt
set PREFIX=scripturevec14_qwen3_14b_confirmed_chapter_layerloc_l%CENTER%_%TAG%_v1

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
  --subset justice ^
  --runs 1 ^
  --limit 10 ^
  --temperature 0.0 ^
  --seed 42 ^
  --conditions control scripture_steer scripture_negative_alpha scripture_null_control ^
  --scripture-targets %TARGETS% ^
  --external-scripture-corpus "%CORPUS%" ^
  --vectors "%VECTOR%" ^
  --extraction-method auto ^
  --scripture-runtime-alpha %ALPHA% ^
  --preflight-policy off ^
  --output-prefix experiments/scripturevec14/%PREFIX% ^
  >> "results\%PREFIX%_wrapper_console.log" 2>&1

if errorlevel 1 (
  echo FAILED > "results\%PREFIX%.status"
  exit /b 1
)

echo FINISHED > "results\%PREFIX%.status"
exit /b 0
