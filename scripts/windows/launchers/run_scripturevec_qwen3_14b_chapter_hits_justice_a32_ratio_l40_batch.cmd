@echo off
setlocal EnableExtensions

if "%~1"=="" (
  echo Usage: %~nx0 01^|02^|03^|04 [version]
  exit /b 2
)

set BATCH=%~1
set VERSION=%~2
if "%VERSION%"=="" set VERSION=1

for %%I in ("%~dp0..\..\..") do set REPO=%%~fI
cd /d "%REPO%"

set PYTHON=%REPO%\.venv\Scripts\python.exe
if not exist "%PYTHON%" set PYTHON=C:\Users\sethcodex\work\virtue-bench-2\.venv\Scripts\python.exe

set CORPUS=%REPO%\results\experiments\scripturevec14\canon_discovery\canon_justice_chapter_hits_v1.jsonl

if "%BATCH%"=="01" set TARGETS=chapter_num_08 chapter_num_09 chapter_num_11 chapter_num_22 chapter_num_27 chapter_num_31 chapter_deu_09 chapter_deu_16 chapter_jdg_07 chapter_jdg_09
if "%BATCH%"=="02" set TARGETS=chapter_jdg_15 chapter_1ch_03 chapter_1ch_09 chapter_1ch_13 chapter_1ch_29 chapter_amo_02 chapter_amo_03 chapter_amo_07 chapter_act_01 chapter_act_02
if "%BATCH%"=="03" set TARGETS=chapter_act_03 chapter_act_04 chapter_act_06 chapter_act_07 chapter_act_08 chapter_act_10 chapter_act_11 chapter_act_14 chapter_act_16 chapter_act_24
if "%BATCH%"=="04" set TARGETS=chapter_act_27 chapter_act_28 chapter_heb_01 chapter_heb_02 chapter_heb_05 chapter_heb_07 chapter_heb_09 chapter_heb_10

if not defined TARGETS (
  echo Unknown batch: %BATCH%
  exit /b 2
)

set PREFIX=scripturevec14_qwen3_14b_chapter_hits_justice_a32_ratio_l40_batch%BATCH%_v%VERSION%

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
  --limit 40 ^
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
