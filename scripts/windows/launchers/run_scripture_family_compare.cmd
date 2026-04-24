@echo off
setlocal

for %%I in ("%~dp0..\..\..") do set REPO=%%~fI
cd /d "%REPO%"

set PYTHONPATH=%REPO%\src
set PYTHONUNBUFFERED=1
set PYTHONFAULTHANDLER=1
set PYTHONIOENCODING=utf-8
set TORCH_SHOW_CPP_STACKTRACES=1
set PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True

echo STARTED > results\homepc_qwen35_ratio_scripture_only_v1.status
if exist results\homepc_qwen35_ratio_scripture_only_v1_wrapper_console.log del /q results\homepc_qwen35_ratio_scripture_only_v1_wrapper_console.log

"%REPO%\.venv\Scripts\python.exe" -X faulthandler -u -m virtue_bench.cli iconoclast ^
  --model Qwen/Qwen3.5-9B ^
  --stage ratio ^
  --runs 3 ^
  --limit 20 ^
  --temperature 0.7 ^
  --seed 42 ^
  --condition-profile scripture_only_compare ^
  --scripture-targets psalms proverbs gospels ^
  --window-center 21 ^
  --window-radius 3 ^
  --preflight-policy skip ^
  --output-prefix homepc_qwen35_ratio_scripture_only_v1 ^
  >> results\homepc_qwen35_ratio_scripture_only_v1_wrapper_console.log 2>&1

if errorlevel 1 (
  echo FAILED > results\homepc_qwen35_ratio_scripture_only_v1.status
) else (
  echo FINISHED > results\homepc_qwen35_ratio_scripture_only_v1.status
)

endlocal & exit /b 0
