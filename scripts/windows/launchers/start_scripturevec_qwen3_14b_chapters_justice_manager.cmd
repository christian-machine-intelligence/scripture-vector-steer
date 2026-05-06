@echo off
setlocal

for %%I in ("%~dp0..\..\..") do set REPO=%%~fI
cd /d "%REPO%"

if not exist results mkdir results

set PYTHON=%REPO%\.venv\Scripts\python.exe
if not exist "%PYTHON%" set PYTHON=C:\Users\sethcodex\work\virtue-bench-2\.venv\Scripts\python.exe

start "" /min "%PYTHON%" "%REPO%\scripts\windows\run_scripturevec_chapter_justice_screen.py" --repo "%REPO%"

echo ScriptureVec chapter Justice manager launched.
endlocal
