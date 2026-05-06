$Repo = (Resolve-Path (Join-Path $PSScriptRoot "..\..\..")).Path
$Python = Join-Path $Repo ".venv\Scripts\python.exe"
$Script = Join-Path $Repo "scripts\windows\run_scripturevec_chapter_justice_screen.py"
$Stdout = Join-Path $Repo "results\scripturevec14_qwen3_14b_chapters_justice_a32_ratio_l10_all_v2_manager_stdout.log"
$Stderr = Join-Path $Repo "results\scripturevec14_qwen3_14b_chapters_justice_a32_ratio_l10_all_v2_manager_stderr.log"

if (-not (Test-Path $Python)) {
    $Python = "C:\Users\sethcodex\work\virtue-bench-2\.venv\Scripts\python.exe"
}

Start-Process `
    -WindowStyle Minimized `
    -FilePath $Python `
    -ArgumentList @($Script, "--repo", $Repo) `
    -WorkingDirectory $Repo `
    -RedirectStandardOutput $Stdout `
    -RedirectStandardError $Stderr

Write-Host "ScriptureVec chapter Justice manager launched."
