$ErrorActionPreference = "Stop"

$RootDir = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $RootDir

if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
}

uvicorn services.api.main:app --reload --host 127.0.0.1 --port 8000

