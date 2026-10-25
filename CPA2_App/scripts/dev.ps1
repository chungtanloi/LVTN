param([int]$WebPort = 3000, [int]$ApiPort = 8000)
$ErrorActionPreference = 'Stop'
$appRoot = Split-Path -Parent $PSScriptRoot
$apiRoot = Join-Path $appRoot 'api'
$webRoot = Join-Path $appRoot 'web'
$venvPython = Join-Path $apiRoot '.venv/Scripts/python.exe'
if (-not (Test-Path -LiteralPath $venvPython)) { throw 'Create the API virtual environment and install requirements-dev.txt first. See CPA2_App/README.md.' }
$pythonExe = $venvPython
$nodeCommand = Get-Command node -ErrorAction SilentlyContinue
if ($nodeCommand) { $nodeExe = $nodeCommand.Source }
else {
    $nodeExe = Join-Path $env:USERPROFILE '.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe'
    if (-not (Test-Path -LiteralPath $nodeExe)) { throw 'Install Node.js 20.9 or newer first.' }
}
$env:PATH = (Split-Path -Parent $nodeExe) + [IO.Path]::PathSeparator + $env:PATH
$nextCli = Join-Path $webRoot 'node_modules/next/dist/bin/next'
if (-not (Test-Path -LiteralPath $nextCli)) { throw 'Run pnpm install inside CPA2_App/web first.' }
foreach ($port in @($WebPort, $ApiPort)) {
    if (Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue) { throw "Port $port is already in use. Choose other ports with -WebPort and -ApiPort." }
}
$randomBytes = New-Object byte[] 32
$randomGenerator = [Security.Cryptography.RandomNumberGenerator]::Create()
$randomGenerator.GetBytes($randomBytes)
$randomGenerator.Dispose()
$env:CPA2_SERVICE_KEY = [Convert]::ToBase64String($randomBytes)
$env:CPA2_API_URL = "http://127.0.0.1:$ApiPort"
$env:CPA2_DEMO_MODE = 'true'
$env:PYTHONIOENCODING = 'utf-8'
$apiProcess = $null
try {
    $apiProcess = Start-Process -FilePath $pythonExe -ArgumentList @('-m', 'uvicorn', 'cpa2_api.main:app', '--host', '127.0.0.1', '--port', $ApiPort) -WorkingDirectory $apiRoot -WindowStyle Hidden -PassThru
    $apiReady = $false
    for ($attempt = 0; $attempt -lt 30; $attempt++) {
        if ($apiProcess.HasExited) { throw 'CPA2 API stopped during startup. Run uvicorn manually to inspect the startup error.' }
        try {
            $health = Invoke-RestMethod -Uri "http://127.0.0.1:$ApiPort/health" -TimeoutSec 1
            if ($health.status -eq 'ok') { $apiReady = $true; break }
        } catch { Start-Sleep -Milliseconds 250 }
    }
    if (-not $apiReady) { throw 'CPA2 API did not become ready.' }
    Write-Host "CPA2 demo: http://127.0.0.1:$WebPort"
    Write-Host 'Synthetic profiles only. Ctrl+C stops both services.'
    Push-Location $webRoot
    try { & $nodeExe $nextCli dev --hostname 127.0.0.1 --port $WebPort } finally { Pop-Location }
} finally {
    if ($apiProcess -and -not $apiProcess.HasExited) { Stop-Process -Id $apiProcess.Id }
    Remove-Item Env:CPA2_SERVICE_KEY -ErrorAction SilentlyContinue
}
