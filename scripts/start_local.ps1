param(
    [string]$AdminEmail = "admin@evnation.local",
    [string]$AdminPassword = "Admin12345"
)

$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $projectRoot

$envPath = Join-Path $projectRoot ".env"
$examplePath = Join-Path $projectRoot ".env.example"

if (-not (Test-Path $envPath)) {
    Copy-Item $examplePath $envPath
    $secretKey = [Guid]::NewGuid().ToString("N") + [Guid]::NewGuid().ToString("N")
    $localDbPath = ($env:LOCALAPPDATA + '\EV_Nation\ev_nation.db') -replace '\\', '/'
    $envContent = Get-Content $envPath
    $envContent = $envContent -replace '^DATABASE_URL=.*$', "DATABASE_URL=sqlite:///$localDbPath"
    $envContent = $envContent -replace '^SECRET_KEY=.*$', "SECRET_KEY=$secretKey"
    $envContent | Set-Content $envPath
    Write-Host "Created .env from .env.example"
}

Write-Host "Startup bootstrap will create missing tables and the admin user automatically."

Write-Host ""
Write-Host "Admin login:"
Write-Host "  Email:    $AdminEmail"
Write-Host "  Password: $AdminPassword"
Write-Host ""
Write-Host "Starting server on http://127.0.0.1:8000"
uvicorn app.main:app --reload
