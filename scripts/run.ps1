#Requires -Version 5.1
<#
.SYNOPSIS
    Crea el entorno virtual (si hace falta) e inicia Separador de Nóminas PDF.
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
& $Python -m pip install -r (Join-Path $ProjectRoot "requirements.txt")
& $Python -m pip install -e $ProjectRoot

Write-Host "Iniciando Separador de Nóminas PDF..."
& $Python -m separador_nominas.main
exit $LASTEXITCODE
