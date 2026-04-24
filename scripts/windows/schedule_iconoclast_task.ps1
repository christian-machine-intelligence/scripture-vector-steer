param(
    [Parameter(Mandatory = $true)]
    [string]$TaskName,
    [Parameter(Mandatory = $true)]
    [string]$PythonPath,
    [Parameter(Mandatory = $true)]
    [string]$ScriptPath,
    [Parameter(Mandatory = $true)]
    [string]$Repo,
    [Parameter(Mandatory = $true)]
    [string]$OutputPrefix,
    [Parameter(Mandatory = $true)]
    [string]$User,
    [Parameter(Mandatory = $true)]
    [string]$Password,
    [string[]]$PassThrough = @()
)

$results = Join-Path $Repo "results"
$statusPath = Join-Path $results ($OutputPrefix + ".status")
$wrapperPath = Join-Path $results ($OutputPrefix + "_wrapper_console.log")

Remove-Item -Force -ErrorAction SilentlyContinue $statusPath, $wrapperPath | Out-Null

$argParts = @(
    '"' + $ScriptPath + '"',
    "--worker",
    "--repo",
    '"' + $Repo + '"',
    "--output-prefix",
    $OutputPrefix
)
if ($PassThrough.Count -gt 0) {
    $argParts += "--"
    foreach ($item in $PassThrough) {
        if ($item -match '\s') {
            $argParts += '"' + $item + '"'
        } else {
            $argParts += $item
        }
    }
}

$action = New-ScheduledTaskAction -Execute $PythonPath -Argument ($argParts -join " ")
$trigger = New-ScheduledTaskTrigger -Once -At ((Get-Date).AddMinutes(1))

try {
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue | Out-Null
} catch {
}

Register-ScheduledTask `
    -TaskName $TaskName `
    -Action $action `
    -Trigger $trigger `
    -User $User `
    -Password $Password `
    -RunLevel Highest `
    -Force | Out-Null

Start-ScheduledTask -TaskName $TaskName
Write-Host "SCHEDULED_TASK_STARTED"
