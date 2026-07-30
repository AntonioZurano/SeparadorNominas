#Requires -Version 5.1
<#
.SYNOPSIS
    Ejecuta tests y genera SeparadorNominas.exe con PyInstaller.
#>
$ErrorActionPreference = "Stop"

$ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $ProjectRoot

$VenvPath = Join-Path $ProjectRoot ".venv"
$Python = Join-Path $VenvPath "Scripts\python.exe"
$Activate = Join-Path $VenvPath "Scripts\Activate.ps1"

if (-not (Test-Path $Python)) {
    Write-Host "Creando entorno virtual en .venv ..."
    $created = $false
    if (Get-Command py -ErrorAction SilentlyContinue) {
        & py -3.11 -m venv $VenvPath
        if ($LASTEXITCODE -eq 0 -and (Test-Path $Python)) {
            $created = $true
        }
    }
    if (-not $created) {
        & python -m venv $VenvPath
    }
    if (-not (Test-Path $Python)) {
        throw "No se pudo crear el entorno virtual. Comprueba que Python 3.11+ esté en el PATH."
    }
}

& $Activate
& $Python -m pip install --upgrade pip
& $Python -m pip install -r (Join-Path $ProjectRoot "requirements-dev.txt")
& $Python -m pip install -e $ProjectRoot

Write-Host "Ejecutando tests previos a la compilación..."
& $Python -m pytest
if ($LASTEXITCODE -ne 0) {
    Write-Error "Los tests han fallado. Compilación cancelada."
    exit $LASTEXITCODE
}

$DistDir = Join-Path $ProjectRoot "dist"
$BuildDir = Join-Path $ProjectRoot "build"
$SpecFiles = Get-ChildItem -Path $ProjectRoot -Filter "*.spec" -ErrorAction SilentlyContinue

if (Test-Path $DistDir) {
    Remove-Item -Recurse -Force $DistDir
}
if (Test-Path $BuildDir) {
    Remove-Item -Recurse -Force $BuildDir
}
foreach ($spec in $SpecFiles) {
    Remove-Item -Force $spec.FullName
}

$Entry = Join-Path $ProjectRoot "src\separador_nominas\main.py"
$Icon = Join-Path $ProjectRoot "assets\icon.ico"
$IconArgs = @()
if (Test-Path $Icon) {
    $IconArgs = @("--icon", $Icon)
    Write-Host "Usando icono: $Icon"
} else {
    Write-Host "No se encontró assets\icon.ico. Se usará el icono estándar de Python/Windows."
}

Write-Host "Compilando con PyInstaller..."
# openpyxl / xlrd se importan de forma diferida; hay que forzarlos en el exe.
& $Python -m PyInstaller `
    --noconfirm `
    --clean `
    --onefile `
    --windowed `
    --name "SeparadorNominas" `
    --paths (Join-Path $ProjectRoot "src") `
    --hidden-import openpyxl `
    --hidden-import openpyxl.cell._writer `
    --hidden-import et_xmlfile `
    --hidden-import xlrd `
    @IconArgs `
    $Entry

if ($LASTEXITCODE -ne 0) {
    Write-Error "PyInstaller ha fallado."
    exit $LASTEXITCODE
}

$Exe = Join-Path $DistDir "SeparadorNominas.exe"
if (-not (Test-Path $Exe)) {
    Write-Error "No se encontró el ejecutable esperado: $Exe"
    exit 1
}

Write-Host ""
Write-Host "Compilación completada:"
Write-Host "  $Exe"
exit 0
