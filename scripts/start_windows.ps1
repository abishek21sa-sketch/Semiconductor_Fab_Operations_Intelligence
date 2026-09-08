$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)
. "$PSScriptRoot\python_bootstrap.ps1"

$pythonExe = Initialize-ProjectVenv

& $pythonExe -c "import fabops, fastapi, uvicorn" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "DEPENDENCIES=INSTALLING"
    & $pythonExe -m pip install -e ".[dev]"
    if ($LASTEXITCODE -ne 0) {
        throw "Dependency installation failed with exit code $LASTEXITCODE"
    }
} else {
    Write-Host "DEPENDENCIES=READY"
}

Write-Host "FABOPS_V3_WORKSTATION=http://127.0.0.1:9821/"
Write-Host "FABOPS_API_DOCS=http://127.0.0.1:9821/docs"
Write-Host "FABOPS_HEALTH=http://127.0.0.1:9821/health"
Write-Host "Press CTRL+C to stop the local server."

& $pythonExe -m uvicorn fabops.api.app:app --host 127.0.0.1 --port 9821
if ($LASTEXITCODE -ne 0) {
    throw "FabOps server exited with code $LASTEXITCODE"
}
