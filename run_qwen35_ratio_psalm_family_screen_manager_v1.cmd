@echo off
setlocal

cd /d C:\Users\sethcodex\work\virtue-bench-2
set PYTHONPATH=C:\Users\sethcodex\work\virtue-bench-2\src
set PYTHONUNBUFFERED=1
set PYTHONFAULTHANDLER=1
set PYTHONIOENCODING=utf-8

start "" /min .venv\Scripts\python.exe scripts\windows\manage_psalm_family_screen.py ^
  --repo C:\Users\sethcodex\work\virtue-bench-2 ^
  --poll-seconds 60 ^
  --stale-minutes 45

endlocal
