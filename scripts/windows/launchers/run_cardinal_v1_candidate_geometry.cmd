@echo off
setlocal

for %%I in ("%~dp0..\..\..") do set REPO=%%~fI
cd /d "%REPO%"

set PYTHON=%REPO%\.venv\Scripts\python.exe
if not exist "%PYTHON%" set PYTHON=C:\Users\sethcodex\work\virtue-bench-2\.venv\Scripts\python.exe

set SOURCE_VECTOR=%REPO%\results\cardinal_v1_qwen35_ratio_l10_v1_vectors.pt
set OUTPUT_DIR=%REPO%\results\cardinal_virtue_geometry\candidate_vectors_v1
set LOCAL_RESULTS=%REPO%\results

if not exist results mkdir results
if not exist results\cardinal_virtue_geometry mkdir results\cardinal_virtue_geometry
if not exist "%OUTPUT_DIR%" mkdir "%OUTPUT_DIR%"

set PYTHONPATH=%REPO%\src
set PYTHONUNBUFFERED=1
set PYTHONFAULTHANDLER=1
set PYTHONIOENCODING=utf-8

set STATUS=%LOCAL_RESULTS%\cardinal_v1_candidate_geometry.status
set LOG=%LOCAL_RESULTS%\cardinal_v1_candidate_geometry_wrapper_console.log

echo STARTED > "%STATUS%"
echo Candidate vector geometry run started. > "%LOG%"

"%PYTHON%" -X faulthandler -u scripts\build_cardinal_candidate_vectors.py ^
  --vectors "%SOURCE_VECTOR%" ^
  --output-dir "%OUTPUT_DIR%" ^
  --prefix cardinal_v1_candidate ^
  >> "%LOG%" 2>&1

if errorlevel 1 (
  echo FAILED > "%STATUS%"
  exit /b 1
)

call :analyze target_vs_other
if errorlevel 1 exit /b 1
call :analyze partial_center_0p50
if errorlevel 1 exit /b 1
call :analyze partial_center_0p75
if errorlevel 1 exit /b 1
call :analyze scripture_plus_accent_1p0_1p0
if errorlevel 1 exit /b 1
call :analyze scripture_plus_accent_1p0_2p0
if errorlevel 1 exit /b 1
call :analyze mixed_generic_other_1p0_1p0
if errorlevel 1 exit /b 1

echo FINISHED > "%STATUS%"
endlocal
exit /b 0

:analyze
set SLUG=%~1
set VECTOR=%OUTPUT_DIR%\cardinal_v1_candidate_%SLUG%_vectors.pt
set OUTJSON=%OUTPUT_DIR%\cardinal_v1_candidate_%SLUG%_geometry.json
set OUTMD=%OUTPUT_DIR%\cardinal_v1_candidate_%SLUG%_geometry.md

"%PYTHON%" -X faulthandler -u scripts\analyze_cardinal_vector_geometry.py ^
  --vectors "%VECTOR%" ^
  --output-json "%OUTJSON%" ^
  --output-md "%OUTMD%" ^
  >> "%LOG%" 2>&1

if errorlevel 1 (
  echo FAILED > "%STATUS%"
  exit /b 1
)

exit /b 0
