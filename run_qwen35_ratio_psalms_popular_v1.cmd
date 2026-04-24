@echo off
setlocal

cd /d C:\Users\sethcodex\work\virtue-bench-2
set PYTHONPATH=C:\Users\sethcodex\work\virtue-bench-2\src
set VIRTUE_BENCH_ICONOCLAST_CONSOLE=file

python -m virtue_bench.cli iconoclast ^
  --model Qwen/Qwen3.5-9B ^
  --stage ratio ^
  --runs 3 ^
  --limit 20 ^
  --temperature 0.7 ^
  --seed 42 ^
  --condition-profile scripture_only_compare ^
  --scripture-targets psalms ^
  --extraction-method scripture_contrast ^
  --psalm-vector-set popular ^
  --alpha-candidates 0.5,1.0,2.0,4.0,6.0,8.0 ^
  --preflight-policy skip ^
  --output-prefix homepc_qwen35_ratio_psalms_popular_v1

endlocal
