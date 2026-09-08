$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)
. "$PSScriptRoot\python_bootstrap.ps1"
$pythonExe = Initialize-ProjectVenv
$env:PYTHONFAULTHANDLER="0"
$env:PY_COLORS="0"
$env:NO_COLOR="1"
$env:OMP_NUM_THREADS="1"
$env:OPENBLAS_NUM_THREADS="1"
$env:MKL_NUM_THREADS="1"
$env:NUMEXPR_NUM_THREADS="1"
Write-Host "DEVELOPMENT_TESTS=PYTEST"
& $pythonExe -m pytest -q --color=no -p no:faulthandler
if ($LASTEXITCODE -ne 0) { throw "pytest failed with exit code $LASTEXITCODE" }
Write-Host "DEVELOPMENT_TESTS=PASS"
