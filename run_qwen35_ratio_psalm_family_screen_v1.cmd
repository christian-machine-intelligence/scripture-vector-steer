@echo off
setlocal EnableDelayedExpansion

cd /d C:\Users\sethcodex\work\virtue-bench-2
set PYTHONPATH=C:\Users\sethcodex\work\virtue-bench-2\src
set PYTHONUNBUFFERED=1
set PYTHONFAULTHANDLER=1
set PYTHONIOENCODING=utf-8
set TORCH_SHOW_CPP_STACKTRACES=1
set VIRTUE_BENCH_ICONOCLAST_CONSOLE=file

for %%F in (penitential wisdom trust lament royal) do (
  set VECTOR_ARTIFACT=results\homepc_qwen35_ratio_psalm_family_%%F_vectors_v1.pt
  call :run_family_scale %%F 0.75 x075
  if errorlevel 1 exit /b 1
  call :run_family_scale %%F 1.0 x100
  if errorlevel 1 exit /b 1
  call :run_family_scale %%F 1.5 x150
  if errorlevel 1 exit /b 1
  call :run_family_scale %%F 2.0 x200
  if errorlevel 1 exit /b 1
)

endlocal & exit /b 0

:run_family_scale
set FAMILY=%1
set SCALE=%2
set SCALE_LABEL=%3

.venv\Scripts\python.exe -X faulthandler -u -m virtue_bench.cli iconoclast ^
  --model Qwen/Qwen3.5-9B ^
  --stage ratio ^
  --runs 1 ^
  --limit 20 ^
  --temperature 0.0 ^
  --seed 42 ^
  --condition-profile psalm_reasoning_primary ^
  --psalm-family-lane %FAMILY% ^
  --extraction-method scripture_contrast ^
  --scripture-alpha-scale %SCALE% ^
  --preflight-policy off ^
  --vectors %VECTOR_ARTIFACT% ^
  --output-prefix homepc_qwen35_ratio_psalm_family_%FAMILY%_%SCALE_LABEL%_v1
if errorlevel 1 exit /b 1
goto :eof
