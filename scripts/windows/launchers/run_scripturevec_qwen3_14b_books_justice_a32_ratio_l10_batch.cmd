@echo off
setlocal EnableExtensions

if "%~1"=="" (
  echo Usage: %~nx0 01^|02^|03^|04^|05^|06
  exit /b 2
)

set BATCH=%~1

for %%I in ("%~dp0..\..\..") do set REPO=%%~fI
cd /d "%REPO%"

set PYTHON=%REPO%\.venv\Scripts\python.exe
if not exist "%PYTHON%" set PYTHON=C:\Users\sethcodex\work\virtue-bench-2\.venv\Scripts\python.exe

set CORPUS=%REPO%\results\experiments\scripturevec14\canon_discovery\canon_books_v1.jsonl

if "%BATCH%"=="01" set TARGETS=book_gen book_exo book_lev book_num book_deu book_jos book_jdg book_rut book_1sa book_2sa book_1ki
if "%BATCH%"=="02" set TARGETS=book_2ki book_1ch book_2ch book_ezr book_neh book_est book_job book_psa book_pro book_ecc book_sng
if "%BATCH%"=="03" set TARGETS=book_isa book_jer book_lam book_ezk book_dan book_hos book_jol book_amo book_oba book_jon book_mic
if "%BATCH%"=="04" set TARGETS=book_nam book_hab book_zep book_hag book_zec book_mal book_mat book_mrk book_luk book_jhn book_act
if "%BATCH%"=="05" set TARGETS=book_rom book_1co book_2co book_gal book_eph book_php book_col book_1th book_2th book_1ti book_2ti
if "%BATCH%"=="06" set TARGETS=book_tit book_phm book_heb book_jas book_1pe book_2pe book_1jn book_2jn book_3jn book_jud book_rev

if not defined TARGETS (
  echo Unknown batch: %BATCH%
  exit /b 2
)

set PREFIX=scripturevec14_qwen3_14b_books_justice_a32_ratio_l10_batch%BATCH%_v1

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
