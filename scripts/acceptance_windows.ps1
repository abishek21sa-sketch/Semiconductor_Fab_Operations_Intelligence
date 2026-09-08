$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)
. "$PSScriptRoot\python_bootstrap.ps1"

$pythonExe = Initialize-ProjectVenv

function Invoke-PythonChecked {
    param(
        [Parameter(Mandatory=$true)][string]$Step,
        [Parameter(Mandatory=$true)][string[]]$Arguments
    )

    Write-Host "ACCEPTANCE_STEP=$Step"
    & $pythonExe @Arguments
    $exitCode = $LASTEXITCODE
    if ($exitCode -ne 0) {
        throw "$Step failed with exit code $exitCode"
    }
}

Invoke-PythonChecked -Step "PIP_UPGRADE" -Arguments @("-m", "pip", "install", "--upgrade", "pip")
Invoke-PythonChecked -Step "EDITABLE_INSTALL" -Arguments @("-m", "pip", "install", "-e", ".[dev]")
Invoke-PythonChecked -Step "DEVELOPMENT_TESTS" -Arguments @("-m", "pytest", "-q", "--color=no", "-p", "no:faulthandler")
Invoke-PythonChecked -Step "WINDOWS_FUNCTIONAL_ACCEPTANCE" -Arguments @(".\scripts\windows_functional_acceptance.py")
Invoke-PythonChecked -Step "REFERENCE_VALIDATION" -Arguments @(".\scripts\run_validation.py")
Invoke-PythonChecked -Step "FLAGSHIP_VALIDATION" -Arguments @(".\scripts\run_flagship_validation.py")
Invoke-PythonChecked -Step "V3_PRODUCT_VALIDATION" -Arguments @(".\scripts\run_v3_validation.py")
Invoke-PythonChecked -Step "V4_PRODUCT_VALIDATION" -Arguments @(".\scripts\run_v4_validation.py")
Invoke-PythonChecked -Step "V5_ENGINE_VALIDATION" -Arguments @(".\scripts\run_v5_validation.py")
Invoke-PythonChecked -Step "V6_COUPLED_VALIDATION" -Arguments @(".\scripts\run_v6_validation.py")
Invoke-PythonChecked -Step "V7_DATA_FABRIC_VALIDATION" -Arguments @(".\scripts\run_v7_validation.py")
Invoke-PythonChecked -Step "V72_DECISION_CENTER_VALIDATION" -Arguments @(".\scripts\run_v72_validation.py")
Invoke-PythonChecked -Step "PORTFOLIO_RESEARCH_VALIDATION" -Arguments @(".\scripts\run_portfolio_validation.py")
Invoke-PythonChecked -Step "ENTERPRISE_OPERABILITY" -Arguments @(".\scripts\run_enterprise_operability.py")
Invoke-PythonChecked -Step "COMPILEALL" -Arguments @("-m", "compileall", "-q", "src", "scripts")

Write-Host "ACCEPTANCE_STEP=WINDOWS_HTTP_SMOKE"
& "$PSScriptRoot\smoke_windows.ps1" -PythonExe $pythonExe
if ($LASTEXITCODE -ne 0) {
    throw "WINDOWS_HTTP_SMOKE failed with exit code $LASTEXITCODE"
}

Write-Host "FLAGSHIP_V7_2_ENTERPRISE_ACCEPTANCE=PASS"
