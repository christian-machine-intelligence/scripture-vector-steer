@echo off
setlocal EnableExtensions

if "%~1"=="" (
  echo Usage: %~nx0 01^|01S^|02^|03^|04^|05^|06^|07^|08^|09^|10^|11^|12^|13^|14^|15^|16^|17 [version]
  exit /b 2
)

set BATCH=%~1
set BATCH_LABEL=%BATCH%
set VERSION=%~2
if "%VERSION%"=="" set VERSION=1

for %%I in ("%~dp0..\..\..") do set REPO=%%~fI
cd /d "%REPO%"

set PYTHON=%REPO%\.venv\Scripts\python.exe
if not exist "%PYTHON%" set PYTHON=C:\Users\sethcodex\work\virtue-bench-2\.venv\Scripts\python.exe

set CORPUS=%REPO%\results\experiments\scripturevec14\canon_discovery\canon_justice_survivor_chapters_v1.jsonl

if "%BATCH%"=="01" set TARGETS=chapter_num_01 chapter_num_02 chapter_num_03 chapter_num_04 chapter_num_05 chapter_num_06 chapter_num_07 chapter_num_08 chapter_num_09 chapter_num_10
if "%BATCH%"=="01S" set TARGETS=chapter_num_01 chapter_num_02 chapter_num_04 chapter_num_05 chapter_num_06 chapter_num_07 chapter_num_08 chapter_num_09 chapter_num_10
if "%BATCH%"=="01S" set BATCH_LABEL=01_skip03
if "%BATCH%"=="02" set TARGETS=chapter_num_11 chapter_num_12 chapter_num_13 chapter_num_14 chapter_num_15 chapter_num_16 chapter_num_17 chapter_num_18 chapter_num_19 chapter_num_20
if "%BATCH%"=="03" set TARGETS=chapter_num_21 chapter_num_22 chapter_num_23 chapter_num_24 chapter_num_25 chapter_num_26 chapter_num_27 chapter_num_28 chapter_num_29 chapter_num_30
if "%BATCH%"=="04" set TARGETS=chapter_num_31 chapter_num_32 chapter_num_33 chapter_num_34 chapter_num_35 chapter_num_36 chapter_deu_01 chapter_deu_02 chapter_deu_03 chapter_deu_04
if "%BATCH%"=="05" set TARGETS=chapter_deu_05 chapter_deu_06 chapter_deu_07 chapter_deu_08 chapter_deu_09 chapter_deu_10 chapter_deu_11 chapter_deu_12 chapter_deu_13 chapter_deu_14
if "%BATCH%"=="06" set TARGETS=chapter_deu_15 chapter_deu_16 chapter_deu_17 chapter_deu_18 chapter_deu_19 chapter_deu_20 chapter_deu_21 chapter_deu_22 chapter_deu_23 chapter_deu_24
if "%BATCH%"=="07" set TARGETS=chapter_deu_25 chapter_deu_26 chapter_deu_27 chapter_deu_28 chapter_deu_29 chapter_deu_30 chapter_deu_31 chapter_deu_32 chapter_deu_33 chapter_deu_34
if "%BATCH%"=="08" set TARGETS=chapter_jdg_01 chapter_jdg_02 chapter_jdg_03 chapter_jdg_04 chapter_jdg_05 chapter_jdg_06 chapter_jdg_07 chapter_jdg_08 chapter_jdg_09 chapter_jdg_10
if "%BATCH%"=="09" set TARGETS=chapter_jdg_11 chapter_jdg_12 chapter_jdg_13 chapter_jdg_14 chapter_jdg_15 chapter_jdg_16 chapter_jdg_17 chapter_jdg_18 chapter_jdg_19 chapter_jdg_20
if "%BATCH%"=="10" set TARGETS=chapter_jdg_21 chapter_1ch_01 chapter_1ch_02 chapter_1ch_03 chapter_1ch_04 chapter_1ch_05 chapter_1ch_06 chapter_1ch_07 chapter_1ch_08 chapter_1ch_09
if "%BATCH%"=="11" set TARGETS=chapter_1ch_10 chapter_1ch_11 chapter_1ch_12 chapter_1ch_13 chapter_1ch_14 chapter_1ch_15 chapter_1ch_16 chapter_1ch_17 chapter_1ch_18 chapter_1ch_19
if "%BATCH%"=="12" set TARGETS=chapter_1ch_20 chapter_1ch_21 chapter_1ch_22 chapter_1ch_23 chapter_1ch_24 chapter_1ch_25 chapter_1ch_26 chapter_1ch_27 chapter_1ch_28 chapter_1ch_29
if "%BATCH%"=="13" set TARGETS=chapter_amo_01 chapter_amo_02 chapter_amo_03 chapter_amo_04 chapter_amo_05 chapter_amo_06 chapter_amo_07 chapter_amo_08 chapter_amo_09 chapter_act_01
if "%BATCH%"=="14" set TARGETS=chapter_act_02 chapter_act_03 chapter_act_04 chapter_act_05 chapter_act_06 chapter_act_07 chapter_act_08 chapter_act_09 chapter_act_10 chapter_act_11
if "%BATCH%"=="15" set TARGETS=chapter_act_12 chapter_act_13 chapter_act_14 chapter_act_15 chapter_act_16 chapter_act_17 chapter_act_18 chapter_act_19 chapter_act_20 chapter_act_21
if "%BATCH%"=="16" set TARGETS=chapter_act_22 chapter_act_23 chapter_act_24 chapter_act_25 chapter_act_26 chapter_act_27 chapter_act_28 chapter_heb_01 chapter_heb_02 chapter_heb_03
if "%BATCH%"=="17" set TARGETS=chapter_heb_04 chapter_heb_05 chapter_heb_06 chapter_heb_07 chapter_heb_08 chapter_heb_09 chapter_heb_10 chapter_heb_11 chapter_heb_12 chapter_heb_13

if not defined TARGETS (
  echo Unknown batch: %BATCH%
  exit /b 2
)

set PREFIX=scripturevec14_qwen3_14b_chapters_justice_a32_ratio_l10_batch%BATCH_LABEL%_v%VERSION%

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
  --limit 10 ^
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
