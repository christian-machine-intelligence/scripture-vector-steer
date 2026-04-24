param(
    [Parameter(Mandatory = $true)]
    [string]$ScriptPath,

    [string]$LaunchRecordPath = ""
)

$ErrorActionPreference = "Stop"

$resolvedScript = (Resolve-Path -LiteralPath $ScriptPath).Path
$argumentList = @(
    "-NoProfile",
    "-ExecutionPolicy", "Bypass",
    "-File", $resolvedScript
)

$child = Start-Process `
    -FilePath "powershell.exe" `
    -ArgumentList $argumentList `
    -WindowStyle Hidden `
    -PassThru

if ($LaunchRecordPath) {
    $record = [ordered]@{
        launched_at = (Get-Date).ToString("o")
        script_path = $resolvedScript
        pid = $child.Id
    }
    $record | ConvertTo-Json | Set-Content -LiteralPath $LaunchRecordPath
}

Write-Host "DETACHED_PID=$($child.Id)"
