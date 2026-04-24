$ErrorActionPreference = "Stop"

$repo = "C:\Users\sethcodex\work\virtue-bench-2"
$out = Join-Path $repo "results\detach_smoke_test.txt"

"started $(Get-Date -Format o)" | Set-Content -Path $out
Start-Sleep -Seconds 8
"finished $(Get-Date -Format o)" | Add-Content -Path $out

