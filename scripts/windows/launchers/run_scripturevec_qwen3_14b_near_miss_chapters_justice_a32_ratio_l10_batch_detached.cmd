@echo off
setlocal EnableExtensions

if "%~1"=="" (
  echo Usage: %~nx0 01^|02^|03^|04^|05^|06^|07^|08^|09^|10^|11^|12^|13^|14^|15^|16^|17^|18^|19^|20
  exit /b 2
)

set BATCH=%~1

for %%I in ("%~dp0..\..\..") do set REPO=%%~fI
cd /d "%REPO%"

set PYTHON=%REPO%\.venv\Scripts\python.exe
if not exist "%PYTHON%" set PYTHON=C:\Users\sethcodex\work\virtue-bench-2\.venv\Scripts\python.exe

set CORPUS=%REPO%\results\experiments\scripturevec14\canon_discovery\canon_justice_near_miss_chapters_v1.jsonl

if "%BATCH%"=="01" set TARGETS=chapter_1sa_01 chapter_1sa_02 chapter_1sa_03 chapter_1sa_04 chapter_1sa_05 chapter_1sa_06 chapter_1sa_07 chapter_1sa_08 chapter_1sa_09 chapter_1sa_10
if "%BATCH%"=="02" set TARGETS=chapter_1sa_11 chapter_1sa_12 chapter_1sa_13 chapter_1sa_14 chapter_1sa_15 chapter_1sa_16 chapter_1sa_17 chapter_1sa_18 chapter_1sa_19 chapter_1sa_20
if "%BATCH%"=="03" set TARGETS=chapter_1sa_21 chapter_1sa_22 chapter_1sa_23 chapter_1sa_24 chapter_1sa_25 chapter_1sa_26 chapter_1sa_27 chapter_1sa_28 chapter_1sa_29 chapter_1sa_30
if "%BATCH%"=="04" set TARGETS=chapter_1sa_31 chapter_2ki_01 chapter_2ki_02 chapter_2ki_03 chapter_2ki_04 chapter_2ki_05 chapter_2ki_06 chapter_2ki_07 chapter_2ki_08 chapter_2ki_09
if "%BATCH%"=="05" set TARGETS=chapter_2ki_10 chapter_2ki_11 chapter_2ki_12 chapter_2ki_13 chapter_2ki_14 chapter_2ki_15 chapter_2ki_16 chapter_2ki_17 chapter_2ki_18 chapter_2ki_19
if "%BATCH%"=="06" set TARGETS=chapter_2ki_20 chapter_2ki_21 chapter_2ki_22 chapter_2ki_23 chapter_2ki_24 chapter_2ki_25 chapter_neh_01 chapter_neh_02 chapter_neh_03 chapter_neh_04
if "%BATCH%"=="07" set TARGETS=chapter_neh_05 chapter_neh_06 chapter_neh_07 chapter_neh_08 chapter_neh_09 chapter_neh_10 chapter_neh_11 chapter_neh_12 chapter_neh_13 chapter_sng_01
if "%BATCH%"=="08" set TARGETS=chapter_sng_02 chapter_sng_03 chapter_sng_04 chapter_sng_05 chapter_sng_06 chapter_sng_07 chapter_sng_08 chapter_lam_01 chapter_lam_02 chapter_lam_03
if "%BATCH%"=="09" set TARGETS=chapter_lam_04 chapter_lam_05 chapter_hos_01 chapter_hos_02 chapter_hos_03 chapter_hos_04 chapter_hos_05 chapter_hos_06 chapter_hos_07 chapter_hos_08
if "%BATCH%"=="10" set TARGETS=chapter_hos_09 chapter_hos_10 chapter_hos_11 chapter_hos_12 chapter_hos_13 chapter_hos_14 chapter_nam_01 chapter_nam_02 chapter_nam_03 chapter_hab_01
if "%BATCH%"=="11" set TARGETS=chapter_hab_02 chapter_hab_03 chapter_mrk_01 chapter_mrk_02 chapter_mrk_03 chapter_mrk_04 chapter_mrk_05 chapter_mrk_06 chapter_mrk_07 chapter_mrk_08
if "%BATCH%"=="12" set TARGETS=chapter_mrk_09 chapter_mrk_10 chapter_mrk_11 chapter_mrk_12 chapter_mrk_13 chapter_mrk_14 chapter_mrk_15 chapter_mrk_16 chapter_luk_01 chapter_luk_02
if "%BATCH%"=="13" set TARGETS=chapter_luk_03 chapter_luk_04 chapter_luk_05 chapter_luk_06 chapter_luk_07 chapter_luk_08 chapter_luk_09 chapter_luk_10 chapter_luk_11 chapter_luk_12
if "%BATCH%"=="14" set TARGETS=chapter_luk_13 chapter_luk_14 chapter_luk_15 chapter_luk_16 chapter_luk_17 chapter_luk_18 chapter_luk_19 chapter_luk_20 chapter_luk_21 chapter_luk_22
if "%BATCH%"=="15" set TARGETS=chapter_luk_23 chapter_luk_24 chapter_jhn_01 chapter_jhn_02 chapter_jhn_03 chapter_jhn_04 chapter_jhn_05 chapter_jhn_06 chapter_jhn_07 chapter_jhn_08
if "%BATCH%"=="16" set TARGETS=chapter_jhn_09 chapter_jhn_10 chapter_jhn_11 chapter_jhn_12 chapter_jhn_13 chapter_jhn_14 chapter_jhn_15 chapter_jhn_16 chapter_jhn_17 chapter_jhn_18
if "%BATCH%"=="17" set TARGETS=chapter_jhn_19 chapter_jhn_20 chapter_jhn_21 chapter_2co_01 chapter_2co_02 chapter_2co_03 chapter_2co_04 chapter_2co_05 chapter_2co_06 chapter_2co_07
if "%BATCH%"=="18" set TARGETS=chapter_2co_08 chapter_2co_09 chapter_2co_10 chapter_2co_11 chapter_2co_12 chapter_2co_13 chapter_rev_01 chapter_rev_02 chapter_rev_03 chapter_rev_04
if "%BATCH%"=="19" set TARGETS=chapter_rev_05 chapter_rev_06 chapter_rev_07 chapter_rev_08 chapter_rev_09 chapter_rev_10 chapter_rev_11 chapter_rev_12 chapter_rev_13 chapter_rev_14
if "%BATCH%"=="20" set TARGETS=chapter_rev_15 chapter_rev_16 chapter_rev_17 chapter_rev_18 chapter_rev_19 chapter_rev_20 chapter_rev_21 chapter_rev_22

if not defined TARGETS (
  echo Unknown batch: %BATCH%
  exit /b 2
)

set PREFIX=scripturevec14_qwen3_14b_near_miss_chapters_justice_a32_ratio_l10_batch%BATCH%_v1

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

"%PYTHON%" scripts\windows\run_iconoclast_job.py ^
  --repo "%REPO%" ^
  --output-prefix %PREFIX% ^
  --detach ^
  --launch-record "results\%PREFIX%_launch.json" ^
  -- ^
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
  --output-prefix experiments/scripturevec14/%PREFIX%

endlocal
