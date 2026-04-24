$ErrorActionPreference = "Stop"

$repo = "C:\Users\sethcodex\work\virtue-bench-2"
$prefix = "homepc_qwen35_ratio_reasoning_compare_thinking_v5"
$status = Join-Path $repo "results\$prefix.status"
$wrapper = Join-Path $repo "results\${prefix}_wrapper_console.log"

Set-Location $repo
$env:PYTHONPATH = Join-Path $repo "src"
$env:PYTHONUNBUFFERED = "1"
$env:PYTHONFAULTHANDLER = "1"
$env:PYTHONIOENCODING = "utf-8"
$env:TORCH_SHOW_CPP_STACKTRACES = "1"
$env:PYTORCH_CUDA_ALLOC_CONF = "expandable_segments:True"
$env:VIRTUE_BENCH_ICONOCLAST_CONSOLE = "file"

"STARTED" | Set-Content -Path $status -NoNewline
if (Test-Path $wrapper) {
    Remove-Item $wrapper -Force
}

$nativePrefExists = Get-Variable -Name PSNativeCommandUseErrorActionPreference -ErrorAction SilentlyContinue
if ($null -ne $nativePrefExists) {
    $PSNativeCommandUseErrorActionPreference = $false
}

$previousErrorActionPreference = $ErrorActionPreference
$ErrorActionPreference = "Continue"

& (Join-Path $repo ".venv\Scripts\python.exe") `
    -X faulthandler `
    -u `
    -m virtue_bench.cli `
    iconoclast `
    --model Qwen/Qwen3.5-9B `
    --stage ratio `
    --runs 3 `
    --limit 20 `
    --temperature 0.7 `
    --seed 42 `
    --condition-profile reasoning_compare `
    --scripture-targets psalms `
    --pooled-virtue-steer `
    --extraction-method scripture_contrast `
    --psalm-vector-set popular `
    --psalm-vector-set trust `
    --psalm-vector-set wisdom `
    --psalm-vector-set penitential `
    --enable-thinking `
    --alpha-candidates 0.5,1.0,2.0,4.0,6.0,8.0 `
    --preflight-policy skip `
    --output-prefix $prefix *> $wrapper

$ErrorActionPreference = $previousErrorActionPreference

if ($LASTEXITCODE -eq 0) {
    "FINISHED" | Set-Content -Path $status -NoNewline
    exit 0
}

"FAILED" | Set-Content -Path $status -NoNewline
exit $LASTEXITCODE
