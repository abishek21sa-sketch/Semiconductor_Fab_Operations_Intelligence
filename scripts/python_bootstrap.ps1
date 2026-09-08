$ErrorActionPreference = "Stop"

function Get-CompatiblePython {
    $candidates = @(
        @{ Exe = "python"; Args = @() },
        @{ Exe = "python3"; Args = @() },
        @{ Exe = "py"; Args = @("-3") }
    )

    foreach ($candidate in $candidates) {
        $command = Get-Command $candidate.Exe -ErrorAction SilentlyContinue
        if ($null -eq $command) { continue }

        try {
            $candidateArgs = $candidate.Args
            $versionText = & $candidate.Exe @candidateArgs -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}')" 2>$null
            if ($LASTEXITCODE -ne 0 -or -not $versionText) { continue }

            $version = [Version]($versionText.Trim())
            if (($version.Major -gt 3) -or ($version.Major -eq 3 -and $version.Minor -ge 11)) {
                return [PSCustomObject]@{
                    Exe = $candidate.Exe
                    Args = $candidate.Args
                    Version = $versionText.Trim()
                }
            }
        }
        catch {
            continue
        }
    }

    throw @"
Python 3.11 or newer was not found on PATH.
Install Python 3.11+ from python.org and enable 'Add python.exe to PATH', then open a new PowerShell window.
If Python is already installed, verify it with: python --version
"@
}

function Initialize-ProjectVenv {
    param(
        [string]$VenvPath = ".venv"
    )

    $venvPython = Join-Path $VenvPath "Scripts\python.exe"
    if (Test-Path $venvPython) {
        Write-Host "PYTHON_VENV=EXISTING ($venvPython)"
        return $venvPython
    }

    $python = Get-CompatiblePython
    Write-Host "PYTHON_BOOTSTRAP=$($python.Exe) $($python.Args -join ' ')"
    Write-Host "PYTHON_VERSION=$($python.Version)"

    $baseArgs = $python.Args
    & $python.Exe @baseArgs -m venv $VenvPath
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to create virtual environment at $VenvPath."
    }

    if (-not (Test-Path $venvPython)) {
        throw "Virtual environment creation completed without producing $venvPython."
    }

    return $venvPython
}
