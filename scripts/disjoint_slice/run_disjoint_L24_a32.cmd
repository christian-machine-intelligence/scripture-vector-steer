@echo off
setlocal EnableExtensions

REM ============================================================
REM  Disjoint-slice retest, cell L24 / runtime alpha 32
REM  (paper §5.2 "largest mean per-chapter delta" cell;
REM   also the sharpest alpha-collapse cell in the grid)
REM
REM  Evaluates the 16 confirmed chapter directions against items
REM  40..79 of the VirtueBench V2 Justice ratio bank using the
REM  same four-condition control battery as paper §3.4.
REM
REM  See scripts/disjoint_slice/README.md for the full plan.
REM ============================================================

for %%I in ("%~dp0..\..") do set REPO=%%~fI
cd /d "%REPO%"

if not defined PYTHON set PYTHON=%REPO%\.venv\Scripts\python.exe
if not exist "%PYTHON%" set PYTHON=C:\Users\sethcodex\work\virtue-bench-2\.venv\Scripts\python.exe
if not exist "%PYTHON%" (
  echo Could not find a Python interpreter. Set PYTHON to an absolute path before invoking.
  exit /b 2
)

if not defined MODEL_PATH set MODEL_PATH=C:\Users\sethcodex\models\Qwen3-14B

if not defined CORPUS_PATH set CORPUS_PATH=%REPO%\results\experiments\scripturevec14\canon_discovery\canon_justice_survivor_chapters_v1.jsonl
if not exist "%CORPUS_PATH%" (
  echo Chapter corpus not found at %CORPUS_PATH%
  echo Override with CORPUS_PATH= ^<absolute path to canon_justice_survivor_chapters_v1.jsonl^>
  exit /b 2
)

set TARGETS=chapter_deu_16 chapter_jdg_07 chapter_jdg_09 chapter_num_11 chapter_num_22 chapter_num_27 chapter_1ch_09 chapter_1ch_29 chapter_act_07 chapter_act_11 chapter_act_16 chapter_act_27 chapter_heb_02 chapter_heb_07 chapter_heb_09 chapter_heb_10

set CENTER_LAYER=24
set RUNTIME_ALPHA=32.0

set PREFIX=scripturevec14_qwen3_14b_disjoint_l40_o40_L%CENTER_LAYER%_a32_v1

if not exist results mkdir results
if not exist "results\experiments\scripturevec14_disjoint_slice" mkdir "results\experiments\scripturevec14_disjoint_slice"

set PYTHONPATH=%REPO%\src
set PYTHONUNBUFFERED=1
set PYTHONFAULTHANDLER=1
set PYTHONIOENCODING=utf-8
set TORCH_SHOW_CPP_STACKTRACES=1
set TORCH_DISABLE_ADDR2LINE=1
set PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
if not defined VIRTUE_BENCH_CUDA_DEVICE set VIRTUE_BENCH_CUDA_DEVICE=cuda:0
set VIRTUE_BENCH_HF_DEVICE_MAP=
set VIRTUE_BENCH_HF_MAX_MEMORY=

echo STARTED > "results\experiments\scripturevec14_disjoint_slice\%PREFIX%.status"
echo Cell L%CENTER_LAYER% / alpha %RUNTIME_ALPHA% on items 40..79

"%PYTHON%" -X faulthandler -u -m virtue_bench.cli iconoclast ^
  --model "%MODEL_PATH%" ^
  --subset justice ^
  --stage ratio ^
  --runs 1 ^
  --limit 40 ^
  --sample-offset 40 ^
  --temperature 0.0 ^
  --seed 42 ^
  --condition-profile scripturevec35 ^
  --scripture-targets %TARGETS% ^
  --external-scripture-corpus "%CORPUS_PATH%" ^
  --extraction-method scripture_contrast ^
  --window-center %CENTER_LAYER% ^
  --window-radius 3 ^
  --scripture-runtime-alpha %RUNTIME_ALPHA% ^
  --preflight-policy off ^
  --output-prefix experiments/scripturevec14_disjoint_slice/%PREFIX% ^
  >> "results\experiments\scripturevec14_disjoint_slice\%PREFIX%_wrapper_console.log" 2>&1

if errorlevel 1 (
  echo FAILED > "results\experiments\scripturevec14_disjoint_slice\%PREFIX%.status"
  exit /b 1
)

echo FINISHED > "results\experiments\scripturevec14_disjoint_slice\%PREFIX%.status"
echo Summary: results\experiments\scripturevec14_disjoint_slice\%PREFIX%_summary.json
endlocal
