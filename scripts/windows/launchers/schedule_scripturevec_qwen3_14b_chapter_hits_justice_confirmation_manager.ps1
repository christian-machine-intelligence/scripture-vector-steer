param(
  [string]$StartBatch = "01",
  [string]$Version = "1",
  [string]$TaskName = "ScriptureVecChapterHitJusticeConfirmation"
)

$ErrorActionPreference = "Stop"

$Repo = (Resolve-Path (Join-Path $PSScriptRoot "..\..\..")).Path
$Manager = Join-Path $PSScriptRoot "run_scripturevec_qwen3_14b_chapter_hits_justice_confirmation_manager.ps1"
$Argument = "-NoProfile -ExecutionPolicy Bypass -File `"$Manager`" -StartBatch $StartBatch -Version $Version"

$Action = New-ScheduledTaskAction `
  -Execute "powershell.exe" `
  -Argument $Argument `
  -WorkingDirectory $Repo

$Trigger = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(1)
$Principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive

Register-ScheduledTask `
  -TaskName $TaskName `
  -Action $Action `
  -Trigger $Trigger `
  -Principal $Principal `
  -Force | Out-Null

Start-ScheduledTask -TaskName $TaskName

Write-Host "Scheduled and started $TaskName from batch $StartBatch, version $Version."
