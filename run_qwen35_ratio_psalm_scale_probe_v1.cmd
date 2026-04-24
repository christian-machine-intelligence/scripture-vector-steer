@echo off
setlocal

cd /d C:\Users\sethcodex\work\virtue-bench-2
set PYTHONPATH=C:\Users\sethcodex\work\virtue-bench-2\src
set PYTHONUNBUFFERED=1
set PYTHONFAULTHANDLER=1
set PYTHONIOENCODING=utf-8
set TORCH_SHOW_CPP_STACKTRACES=1
set VIRTUE_BENCH_ICONOCLAST_CONSOLE=file
set VECTOR_ARTIFACT=results\homepc_qwen35_ratio_psalm_scale_probe_vectors.pt

REM Baseline Psalm push
.venv\Scripts\python.exe -X faulthandler -u -m virtue_bench.cli iconoclast ^
  --model Qwen/Qwen3.5-9B ^
  --stage ratio ^
  --runs 1 ^
  --limit 10 ^
  --temperature 0.7 ^
  --seed 42 ^
  --condition-profile reasoning_primary ^
  --scripture-targets psalms ^
  --pooled-virtue-steer ^
  --extraction-method scripture_contrast ^
  --psalm-vector-set popular ^
  --psalm-vector-set trust ^
  --psalm-vector-set wisdom ^
  --psalm-vector-set penitential ^
  --scripture-alpha-scale 1.0 ^
  --preflight-policy off ^
  --vectors %VECTOR_ARTIFACT% ^
  --output-prefix homepc_qwen35_ratio_psalm_scale_probe_x100_v1
if errorlevel 1 exit /b 1

REM Slightly softer Psalm push
.venv\Scripts\python.exe -X faulthandler -u -m virtue_bench.cli iconoclast ^
  --model Qwen/Qwen3.5-9B ^
  --stage ratio ^
  --runs 1 ^
  --limit 10 ^
  --temperature 0.7 ^
  --seed 42 ^
  --condition-profile reasoning_primary ^
  --scripture-targets psalms ^
  --pooled-virtue-steer ^
  --extraction-method scripture_contrast ^
  --psalm-vector-set popular ^
  --psalm-vector-set trust ^
  --psalm-vector-set wisdom ^
  --psalm-vector-set penitential ^
  --scripture-alpha-scale 0.75 ^
  --preflight-policy off ^
  --vectors %VECTOR_ARTIFACT% ^
  --output-prefix homepc_qwen35_ratio_psalm_scale_probe_x075_v1
if errorlevel 1 exit /b 1

REM Stronger Psalm push
.venv\Scripts\python.exe -X faulthandler -u -m virtue_bench.cli iconoclast ^
  --model Qwen/Qwen3.5-9B ^
  --stage ratio ^
  --runs 1 ^
  --limit 10 ^
  --temperature 0.7 ^
  --seed 42 ^
  --condition-profile reasoning_primary ^
  --scripture-targets psalms ^
  --pooled-virtue-steer ^
  --extraction-method scripture_contrast ^
  --psalm-vector-set popular ^
  --psalm-vector-set trust ^
  --psalm-vector-set wisdom ^
  --psalm-vector-set penitential ^
  --scripture-alpha-scale 1.5 ^
  --preflight-policy off ^
  --vectors %VECTOR_ARTIFACT% ^
  --output-prefix homepc_qwen35_ratio_psalm_scale_probe_x150_v1
if errorlevel 1 exit /b 1

REM Much stronger Psalm push
.venv\Scripts\python.exe -X faulthandler -u -m virtue_bench.cli iconoclast ^
  --model Qwen/Qwen3.5-9B ^
  --stage ratio ^
  --runs 1 ^
  --limit 10 ^
  --temperature 0.7 ^
  --seed 42 ^
  --condition-profile reasoning_primary ^
  --scripture-targets psalms ^
  --pooled-virtue-steer ^
  --extraction-method scripture_contrast ^
  --psalm-vector-set popular ^
  --psalm-vector-set trust ^
  --psalm-vector-set wisdom ^
  --psalm-vector-set penitential ^
  --scripture-alpha-scale 2.0 ^
  --preflight-policy off ^
  --vectors %VECTOR_ARTIFACT% ^
  --output-prefix homepc_qwen35_ratio_psalm_scale_probe_x200_v1
if errorlevel 1 exit /b 1

endlocal & exit /b 0
