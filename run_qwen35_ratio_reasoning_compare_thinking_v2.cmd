@echo off
setlocal

cd /d C:\Users\sethcodex\work\virtue-bench-2
set PYTHONPATH=C:\Users\sethcodex\work\virtue-bench-2\src
set PYTHONUNBUFFERED=1
set PYTHONFAULTHANDLER=1
set PYTHONIOENCODING=utf-8
set TORCH_SHOW_CPP_STACKTRACES=1
set PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
set VIRTUE_BENCH_ICONOCLAST_CONSOLE=file

echo STARTED > results\homepc_qwen35_ratio_reasoning_compare_thinking_v2.status
if exist results\homepc_qwen35_ratio_reasoning_compare_thinking_v2_wrapper_console.log del /q results\homepc_qwen35_ratio_reasoning_compare_thinking_v2_wrapper_console.log

.venv\Scripts\python.exe -X faulthandler -u -m virtue_bench.cli iconoclast --model Qwen/Qwen3.5-9B --stage ratio --runs 3 --limit 20 --temperature 0.7 --seed 42 --condition-profile reasoning_compare --scripture-targets psalms --pooled-virtue-steer --extraction-method scripture_contrast --psalm-vector-set popular --psalm-vector-set trust --psalm-vector-set wisdom --psalm-vector-set penitential --enable-thinking --alpha-candidates 0.5,1.0,2.0,4.0,6.0,8.0 --preflight-policy skip --output-prefix homepc_qwen35_ratio_reasoning_compare_thinking_v2 >> results\homepc_qwen35_ratio_reasoning_compare_thinking_v2_wrapper_console.log 2>&1

if errorlevel 1 (
  echo FAILED > results\homepc_qwen35_ratio_reasoning_compare_thinking_v2.status
) else (
  echo FINISHED > results\homepc_qwen35_ratio_reasoning_compare_thinking_v2.status
)

endlocal & exit /b 0
