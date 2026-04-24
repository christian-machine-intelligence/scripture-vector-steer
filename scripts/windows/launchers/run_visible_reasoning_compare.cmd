@echo off
setlocal

for %%I in ("%~dp0..\..\..") do set REPO=%%~fI
cd /d "%REPO%"

"%REPO%\.venv\Scripts\python.exe" "%REPO%\scripts\windows\run_iconoclast_job.py" ^
  --detach ^
  --repo "%REPO%" ^
  --output-prefix homepc_qwen35_ratio_reasoning_compare_visible_v14 ^
  --launch-record "%REPO%\results\homepc_qwen35_ratio_reasoning_compare_visible_v14_launch.json" ^
  -- ^
  --model Qwen/Qwen3.5-9B ^
  --stage ratio ^
  --runs 3 ^
  --limit 20 ^
  --temperature 0.7 ^
  --seed 42 ^
  --condition-profile reasoning_compare ^
  --scripture-targets psalms ^
  --pooled-virtue-steer ^
  --vectors "%REPO%\results\homepc_qwen35_ratio_reasoning_compare_thinking_v5_vectors.pt" ^
  --extraction-method scripture_contrast ^
  --psalm-vector-set popular ^
  --psalm-vector-set trust ^
  --psalm-vector-set wisdom ^
  --psalm-vector-set penitential ^
  --alpha-candidates 0.5,1.0,2.0,4.0,6.0,8.0 ^
  --preflight-policy off ^
  --output-prefix homepc_qwen35_ratio_reasoning_compare_visible_v14

endlocal
