@echo off
setlocal EnableExtensions EnableDelayedExpansion

for %%I in ("%~dp0..\..\..") do set REPO=%%~fI
cd /d "%REPO%"

if not exist results mkdir results

set MANAGER_PREFIX=scripturevec14_qwen3_14b_chapters_justice_a32_ratio_l10_all_v1
set MANAGER_STATUS=results\%MANAGER_PREFIX%.status
set MANAGER_LOG=results\%MANAGER_PREFIX%_manager.log

echo STARTED > "%MANAGER_STATUS%"
echo [%date% %time%] STARTED > "%MANAGER_LOG%"

for %%B in (01 02 03 04 05 06 07 08 09 10 11 12 13 14 15 16 17) do (
  set BATCH_PREFIX=scripturevec14_qwen3_14b_chapters_justice_a32_ratio_l10_batch%%B_v1
  if exist "results\!BATCH_PREFIX!.status" (
    findstr /C:"FINISHED" "results\!BATCH_PREFIX!.status" >nul
    if not errorlevel 1 (
      echo [%date% %time%] SKIP batch %%B already finished >> "%MANAGER_LOG%"
    ) else (
      echo [%date% %time%] RUN batch %%B >> "%MANAGER_LOG%"
      call "%REPO%\scripts\windows\launchers\run_scripturevec_qwen3_14b_chapters_justice_a32_ratio_l10_batch.cmd" %%B
      if errorlevel 1 (
        echo FAILED batch %%B > "%MANAGER_STATUS%"
        echo [%date% %time%] FAILED batch %%B >> "%MANAGER_LOG%"
        exit /b 1
      )
    )
  ) else (
    echo [%date% %time%] RUN batch %%B >> "%MANAGER_LOG%"
    call "%REPO%\scripts\windows\launchers\run_scripturevec_qwen3_14b_chapters_justice_a32_ratio_l10_batch.cmd" %%B
    if errorlevel 1 (
      echo FAILED batch %%B > "%MANAGER_STATUS%"
      echo [%date% %time%] FAILED batch %%B >> "%MANAGER_LOG%"
      exit /b 1
    )
  )
)

echo FINISHED > "%MANAGER_STATUS%"
echo [%date% %time%] FINISHED >> "%MANAGER_LOG%"
endlocal
