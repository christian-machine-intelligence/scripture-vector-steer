@echo off
setlocal

set REPO=C:\Users\sethcodex\work\virtue-bench-2
cd /d "%REPO%"

if not exist results mkdir results

start "" /min "%REPO%\.venv\Scripts\python.exe" "%REPO%\scripts\windows\manage_scripture_study2.py" ^
  --repo "%REPO%" ^
  --poll-seconds 60 ^
  --stale-minutes 8

echo Scripture Study 2 manager launched.
