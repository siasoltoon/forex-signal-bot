$ErrorActionPreference = 'Stop'

$model = if ($env:OLLAMA_MODEL) { $env:OLLAMA_MODEL } else { 'qwen2.5-coder:7b' }

Write-Host 'Checking Ollama...'
$ollama = Get-Command ollama -ErrorAction SilentlyContinue
if (-not $ollama) {
    $winget = Get-Command winget -ErrorAction SilentlyContinue
    if (-not $winget) { throw 'Ollama is missing and winget is unavailable. Install Ollama once, then rerun this script.' }
    Write-Host 'Installing Ollama via winget...'
    winget install --id Ollama.Ollama -e --accept-source-agreements --accept-package-agreements
}

$ollama = Get-Command ollama -ErrorAction SilentlyContinue
if (-not $ollama) { throw 'Ollama installation was not found in PATH. Restart PowerShell and rerun.' }

Write-Host "Pulling $model. This may take a while and several GB of disk/network space."
& ollama pull $model
if ($LASTEXITCODE -ne 0) { throw "ollama pull failed with exit code $LASTEXITCODE" }

Write-Host 'Verifying model availability...'
& ollama list
Write-Host "PC AI setup complete. Model: $model"
Write-Host 'Set AGENT_REPO_ROOT to the local forex-signal-bot checkout before starting the worker.'
