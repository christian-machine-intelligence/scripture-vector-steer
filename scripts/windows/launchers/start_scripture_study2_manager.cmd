@echo off
setlocal

for %%I in ("%~dp0..\..\..") do set REPO=%%~fI
cd /d "%REPO%"

if not exist results mkdir results

start "" /min "%REPO%\.venv\Scripts\python.exe" "%REPO%\scripts\windows\manage_scripture_study2.py" ^
  --repo "%REPO%" ^
  --poll-seconds 60 ^
  --stale-minutes 8

echo Scripture Vector Steer manager launched.
