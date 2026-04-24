@echo off
set TASK=CodexHelpSmoke3
schtasks /Delete /TN "%TASK%" /F >nul 2>&1
schtasks /Create /TN "%TASK%" /SC ONCE /ST 23:59 /TR "\"C:\Users\sethcodex\work\virtue-bench-2\.venv\Scripts\python.exe\" \"C:\Users\sethcodex\work\virtue-bench-2\scripts\windows\run_iconoclast_job.py\" --worker --repo \"C:\Users\sethcodex\work\virtue-bench-2\" --output-prefix homepc_sched_help_smoke3 -- --help" /RU sethcodex /RP ICMIresearch /F
if errorlevel 1 exit /b 1
schtasks /Run /TN "%TASK%"
