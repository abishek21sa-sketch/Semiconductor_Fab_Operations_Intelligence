$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$url = "https://archive.ics.uci.edu/static/public/179/secom.zip"
Invoke-WebRequest -Uri $url -OutFile (Join-Path $root "secom.zip")
Write-Host "EXTERNAL_DATA_REFRESH=PASS"
