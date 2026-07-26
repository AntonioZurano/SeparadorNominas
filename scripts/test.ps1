#Requires -Version 5.1
<#
.SYNOPSIS
    Ejecuta los tests unitarios con cobertura.
#>
$ErrorActionPreference = "Stop"

$ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $ProjectRoot

$VenvPath = Join-Path $ProjectRoot ".venv"
$Python = Join-Path $VenvPath "Scripts\python.exe"
$Activate = Join-Path $VenvPath "Scripts\Activate.ps1"

if (-not (Test-Path $Python)) {
    Write-Host "Creando entorno virtual en .venv ..."
    py -3.11 -m venv $VenvPath
    if ($LASTEXITCODE -ne 0) {
        python -m venv $VenvPath
    }
}

& $Activate
& $Python -m pip install --upgrade pip
& $Python -m pip install -r (Join-Path $ProjectRoot "requirements-dev.txt")
& $Python -m pip install -e $ProjectRoot

Write-Host "Ejecutando tests con cobertura..."
& $Python -m pytest --cov=separador_nominas --cov-report=term-missing
exit $LASTEXITCODE
