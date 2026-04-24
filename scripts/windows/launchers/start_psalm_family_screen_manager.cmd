@echo off
setlocal

for %%I in ("%~dp0..\..\..") do set REPO=%%~fI
cd /d "%REPO%"

set PYTHONPATH=%REPO%\src
set PYTHONUNBUFFERED=1
set PYTHONFAULTHANDLER=1
set PYTHONIOENCODING=utf-8

start "" /min "%REPO%\.venv\Scripts\python.exe" "%REPO%\scripts\windows\manage_psalm_family_screen.py" ^
  --repo "%REPO%" ^
  --poll-seconds 60 ^
  --stale-minutes 45

endlocal
