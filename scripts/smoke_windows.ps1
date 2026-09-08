param(
    [Parameter(Mandatory=$true)][string]$PythonExe,
    [int]$Port = 9822
)

$ErrorActionPreference = "Stop"
$baseUrl = "http://127.0.0.1:$Port"
$stdout = Join-Path $env:TEMP "fabops-smoke-$PID.stdout.log"
$stderr = Join-Path $env:TEMP "fabops-smoke-$PID.stderr.log"
$process = $null

try {
    $process = Start-Process -FilePath $PythonExe `
        -ArgumentList @("-m", "uvicorn", "fabops.api.app:app", "--host", "127.0.0.1", "--port", "$Port") `
        -RedirectStandardOutput $stdout `
        -RedirectStandardError $stderr `
        -PassThru `
        -WindowStyle Hidden

    $ready = $false
    for ($i = 0; $i -lt 40; $i++) {
        if ($process.HasExited) {
            throw "Uvicorn exited before readiness with code $($process.ExitCode). See $stderr"
        }
        try {
            $health = Invoke-RestMethod -Uri "$baseUrl/health" -Method Get -TimeoutSec 2
            if ($health.status -eq "ok") {
                $ready = $true
                break
            }
        } catch {
            Start-Sleep -Milliseconds 250
        }
    }

    if (-not $ready) {
        throw "Uvicorn did not become healthy at $baseUrl/health"
    }

    $root = Invoke-WebRequest -Uri "$baseUrl/" -Method Get -TimeoutSec 5 -UseBasicParsing
    if ($root.StatusCode -ne 200) {
        throw "Operator console returned HTTP $($root.StatusCode)"
    }
    if ($root.Content -notmatch "FAB_BAY_RISK_HEATMAP|Semiconductor|Fab") {
        throw "Operator console response did not contain expected fab UI content"
    }

    Write-Host "WINDOWS_HTTP_SMOKE=PASS"
    Write-Host "SMOKE_ROOT=$baseUrl/"
    Write-Host "SMOKE_HEALTH=$baseUrl/health"
}
finally {
    if ($process -and -not $process.HasExited) {
        Stop-Process -Id $process.Id -Force -ErrorAction SilentlyContinue
        $process.WaitForExit()
    }
    Remove-Item $stdout, $stderr -Force -ErrorAction SilentlyContinue
}
