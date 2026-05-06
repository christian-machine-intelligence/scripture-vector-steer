param(
  [string]$StartBatch = "03",
  [string]$Version = "1"
)

$ErrorActionPreference = "Stop"

$Repo = (Resolve-Path (Join-Path $PSScriptRoot "..\..\..")).Path
$Launcher = Join-Path $PSScriptRoot "run_scripturevec_qwen3_14b_chapters_justice_a32_ratio_l10_batch.cmd"
$Results = Join-Path $Repo "results\experiments\scripturevec14"
$PrefixBase = "scripturevec14_qwen3_14b_chapters_justice_a32_ratio_l10"
$AllBatches = @("02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12", "13", "14", "15", "16", "17")

$startIndex = [Array]::IndexOf($AllBatches, $StartBatch)
if ($startIndex -lt 0) {
  throw "Unknown start batch: $StartBatch"
}

$Batches = $AllBatches[$startIndex..($AllBatches.Length - 1)]

function Read-StatusLine {
  param([string]$Batch)

  $prefix = "${PrefixBase}_batch${Batch}_v${Version}"
  $ratioStatusPath = Join-Path $Results "${prefix}_ratio.status.json"
  $runStatusPath = Join-Path $Results "${prefix}_run.status.json"

  if (Test-Path $ratioStatusPath) {
    try {
      $status = Get-Content $ratioStatusPath -Raw | ConvertFrom-Json
      return "batch ${Batch}: ratio $($status.completed_runs)/$($status.total_runs) $($status.condition)"
    }
    catch {
      return "batch ${Batch}: ratio status exists but is not readable yet"
    }
  }

  if (Test-Path $runStatusPath) {
    try {
      $status = Get-Content $runStatusPath -Raw | ConvertFrom-Json
      return "batch ${Batch}: $($status.phase) $($status.note)"
    }
    catch {
      return "batch ${Batch}: run status exists but is not readable yet"
    }
  }

  return "batch ${Batch}: waiting for first status file"
}

function Test-RatioComplete {
  param([string]$Batch)

  $prefix = "${PrefixBase}_batch${Batch}_v${Version}"
  $ratioStatusPath = Join-Path $Results "${prefix}_ratio.status.json"

  if (-not (Test-Path $ratioStatusPath)) {
    return $false
  }

  try {
    $status = Get-Content $ratioStatusPath -Raw | ConvertFrom-Json
    return ($status.state -eq "completed")
  }
  catch {
    return $false
  }
}

Write-Host "[heartbeat] Starting batches $($Batches -join ', ') at $(Get-Date -Format s)"
Write-Host "[heartbeat] Repo: $Repo"

foreach ($batch in $Batches) {
  Write-Host "===== BATCH $batch START $(Get-Date -Format s) ====="
  $args = "/c `"$Launcher`" $batch $Version"
  $proc = Start-Process -FilePath "cmd.exe" -ArgumentList $args -WorkingDirectory $Repo -NoNewWindow -PassThru

  while (-not $proc.HasExited) {
    Start-Sleep -Seconds 30
    $proc.Refresh()
    Write-Host "[heartbeat] $(Get-Date -Format s) $(Read-StatusLine -Batch $batch)"
  }

  $proc.WaitForExit()
  $exitCode = $proc.ExitCode
  if ($null -eq $exitCode -and (Test-RatioComplete -Batch $batch)) {
    $exitCode = 0
  }
  Write-Host "===== BATCH $batch END code=$exitCode $(Get-Date -Format s) ====="
  if ($exitCode -ne 0) {
    throw "Batch $batch failed with exit code $exitCode"
  }
}

Write-Host "[heartbeat] Finished all requested batches at $(Get-Date -Format s)"
