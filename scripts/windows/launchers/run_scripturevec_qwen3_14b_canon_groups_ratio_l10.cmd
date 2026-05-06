@echo off
setlocal EnableExtensions

for %%I in ("%~dp0..\..\..") do set REPO=%%~fI
cd /d "%REPO%"

set PREFIX=scripturevec14_qwen3_14b_canon_groups_ratio_l10_v2
set PYTHON=%REPO%\.venv\Scripts\python.exe
if not exist "%PYTHON%" set PYTHON=C:\Users\sethcodex\work\virtue-bench-2\.venv\Scripts\python.exe

set CORPUS=%REPO%\results\experiments\scripturevec14\canon_discovery\canon_groups_v1.jsonl
set TARGETS=canon_torah canon_history canon_wisdom canon_major_prophets canon_minor_prophets canon_gospels canon_acts canon_pauline canon_general_epistles canon_revelation

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
  --preflight-policy warn ^
  --output-prefix experiments/scripturevec14/%PREFIX%

endlocal
