param(
  [string]$StartBatch = "01",
  [string]$Version = "1"
)

$ErrorActionPreference = "Stop"

$Repo = (Resolve-Path (Join-Path $PSScriptRoot "..\..\..")).Path
$Results = Join-Path $Repo "results\experiments\scripturevec14"
$Launcher = Join-Path $PSScriptRoot "run_scripturevec_qwen3_14b_chapter_hits_justice_a32_ratio_l40_batch.cmd"
$PrefixBase = "scripturevec14_qwen3_14b_chapter_hits_justice_a32_ratio_l40"
$ManagerPrefix = "${PrefixBase}_manager_v${Version}"
$ManagerLog = Join-Path $Results "${ManagerPrefix}.log"
$ManagerStatus = Join-Path $Results "${ManagerPrefix}.status.json"
$AllBatches = @("01", "02", "03", "04")

$startIndex = [Array]::IndexOf($AllBatches, $StartBatch)
if ($startIndex -lt 0) {
  throw "Unknown start batch: $StartBatch"
}

$Batches = $AllBatches[$startIndex..($AllBatches.Length - 1)]
New-Item -ItemType Directory -Force -Path $Results | Out-Null

function Write-ManagerLog {
  param([string]$Message)
  $line = "[$(Get-Date -Format s)] $Message"
  Add-Content -Path $ManagerLog -Value $line -Encoding utf8
  Write-Host $line
}

function Write-ManagerStatus {
  param(
    [string]$State,
    [string]$Batch = "",
    [string]$Note = ""
  )
  $payload = [ordered]@{
    state = $State
    batch = $Batch
    note = $Note
    version = $Version
    updated_at = (Get-Date).ToUniversalTime().ToString("o")
  }
  $payload | ConvertTo-Json | Set-Content -Path $ManagerStatus -Encoding utf8
}

function Get-BatchPrefix {
  param([string]$Batch)
  return "${PrefixBase}_batch${Batch}_v${Version}"
}

function Get-RatioStatusPath {
  param([string]$Batch)
  return Join-Path $Results "$(Get-BatchPrefix -Batch $Batch)_ratio.status.json"
}

function Test-RatioComplete {
  param([string]$Batch)
  $path = Get-RatioStatusPath -Batch $Batch
  if (-not (Test-Path $path)) {
    return $false
  }
  try {
    $status = Get-Content $path -Raw | ConvertFrom-Json
    return ($status.state -eq "completed")
  }
  catch {
    return $false
  }
}

function Read-ProgressLine {
  param([string]$Batch)
  $path = Get-RatioStatusPath -Batch $Batch
  if (Test-Path $path) {
    try {
      $status = Get-Content $path -Raw | ConvertFrom-Json
      return "batch ${Batch}: ratio $($status.completed_runs)/$($status.total_runs) $($status.condition)"
    }
    catch {
      return "batch ${Batch}: ratio status exists but is not readable yet"
    }
  }

  $runStatus = Join-Path $Results "$(Get-BatchPrefix -Batch $Batch)_run.status.json"
  if (Test-Path $runStatus) {
    try {
      $status = Get-Content $runStatus -Raw | ConvertFrom-Json
      return "batch ${Batch}: $($status.phase) $($status.note)"
    }
    catch {
      return "batch ${Batch}: run status exists but is not readable yet"
    }
  }

  return "batch ${Batch}: waiting for status"
}

Write-ManagerLog "Starting chapter-hit confirmation batches $($Batches -join ', ')"
Write-ManagerStatus -State "running" -Note "manager started"

try {
  foreach ($batch in $Batches) {
    if (Test-RatioComplete -Batch $batch) {
      Write-ManagerLog "Skipping completed batch $batch"
      continue
    }

    Write-ManagerLog "Starting batch $batch"
    Write-ManagerStatus -State "running" -Batch $batch -Note "batch started"

    $proc = Start-Process -FilePath "cmd.exe" -ArgumentList "/c `"$Launcher`" $batch $Version" -WorkingDirectory $Repo -NoNewWindow -PassThru
    while (-not $proc.HasExited) {
      Start-Sleep -Seconds 60
      $proc.Refresh()
      $progress = Read-ProgressLine -Batch $batch
      Write-ManagerLog $progress
      Write-ManagerStatus -State "running" -Batch $batch -Note $progress
    }

    $proc.WaitForExit()
    $exitCode = $proc.ExitCode
    if ($null -eq $exitCode -and (Test-RatioComplete -Batch $batch)) {
      $exitCode = 0
    }

    if ($exitCode -ne 0) {
      $message = "batch $batch failed with exit code $exitCode"
      Write-ManagerLog $message
      Write-ManagerStatus -State "failed" -Batch $batch -Note $message
      exit 1
    }

    Write-ManagerLog "Finished batch $batch"
  }

  Write-ManagerLog "Completed all chapter-hit confirmation batches"
  Write-ManagerStatus -State "completed" -Note "all batches complete"
}
catch {
  $message = $_.Exception.Message
  Write-ManagerLog "FAILED: $message"
  Write-ManagerStatus -State "failed" -Note $message
  exit 1
}
