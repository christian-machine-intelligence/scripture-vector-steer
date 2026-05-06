param(
  [string]$StartBatch = "01",
  [string]$Version = "1"
)

$ErrorActionPreference = "Stop"

$Repo = (Resolve-Path (Join-Path $PSScriptRoot "..\..\..")).Path
$Manager = Join-Path $PSScriptRoot "run_scripturevec_qwen3_14b_chapter_hits_justice_confirmation_manager.ps1"

$arguments = @(
  "-NoProfile",
  "-ExecutionPolicy",
  "Bypass",
  "-File",
  $Manager,
  "-StartBatch",
  $StartBatch,
  "-Version",
  $Version
)

Start-Process -FilePath "powershell.exe" -ArgumentList $arguments -WorkingDirectory $Repo
Write-Host "Started chapter-hit confirmation manager from batch $StartBatch, version $Version."
