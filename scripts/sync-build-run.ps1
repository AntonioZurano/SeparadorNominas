#Requires -Version 5.1
<#
.SYNOPSIS
    Sincroniza SeparadorNominas desde GitHub, recompila el .exe y abre la aplicacion.

.DESCRIPTION
    Pensado para pruebas en Windows mientras el desarrollo se hace en WSL:
    1) Actualiza el codigo desde la rama remota (por defecto main).
    2) Ejecuta scripts/build.ps1 (tests + PyInstaller).
    3) Abre dist/SeparadorNominas.exe.

.PARAMETER RepoDir
    Carpeta local del proyecto. Por defecto: C:\Dev\SeparadorNominas

.PARAMETER Branch
    Rama de GitHub a sincronizar. Por defecto: main

.PARAMETER SkipBuild
    Solo sincroniza y abre el ejecutable existente (no recompila).

.PARAMETER NoLaunch
    Solo sincroniza y compila; no abre la aplicacion.

.EXAMPLE
    Set-Location C:\Dev\SeparadorNominas
    .\scripts\sync-build-run.ps1

.EXAMPLE
    .\scripts\sync-build-run.ps1 -RepoDir C:\Dev\SeparadorNominas -NoLaunch
#>
[CmdletBinding()]
param(
    [string] $RepoDir = "C:\Dev\SeparadorNominas",
    [string] $Branch = "main",
    [switch] $SkipBuild,
    [switch] $NoLaunch
)

$ErrorActionPreference = "Stop"

$RepoUrl = "https://github.com/AntonioZurano/SeparadorNominas.git"
$ZipUrl = "https://github.com/AntonioZurano/SeparadorNominas/archive/refs/heads/$Branch.zip"
$RepoOwner = "AntonioZurano"
$RepoName = "SeparadorNominas"

function Write-Step {
    param([string] $Message)
    Write-Host ""
    Write-Host "==> $Message" -ForegroundColor Cyan
}

function Get-GitExe {
    $cmd = Get-Command git -ErrorAction SilentlyContinue
    if ($cmd) {
        return $cmd.Source
    }
    $candidates = @(
        "C:\Program Files\Git\cmd\git.exe",
        "C:\Program Files\Git\bin\git.exe",
        "C:\Program Files (x86)\Git\cmd\git.exe"
    )
    foreach ($path in $candidates) {
        if (Test-Path $path) {
            return $path
        }
    }
    return $null
}

function Sync-WithGit {
    param(
        [string] $GitExe,
        [string] $Directory,
        [string] $BranchName
    )

    $gitDir = Join-Path $Directory ".git"
    if (-not (Test-Path $gitDir)) {
        return $false
    }

    Write-Step "Sincronizando con Git ($BranchName)..."
    Push-Location $Directory
    try {
        & $GitExe fetch origin
        if ($LASTEXITCODE -ne 0) {
            throw "git fetch ha fallado."
        }
        & $GitExe checkout $BranchName
        if ($LASTEXITCODE -ne 0) {
            throw "git checkout $BranchName ha fallado."
        }
        & $GitExe reset --hard "origin/$BranchName"
        if ($LASTEXITCODE -ne 0) {
            throw "git reset --hard origin/$BranchName ha fallado."
        }
        & $GitExe status -sb
    }
    finally {
        Pop-Location
    }
    return $true
}

function Sync-WithZip {
    param(
        [string] $Directory,
        [string] $BranchName,
        [string] $DownloadUrl
    )

    Write-Step "Git no disponible o carpeta sin .git. Descargando ZIP de '$BranchName'..."

    $parent = Split-Path -Parent $Directory
    if (-not (Test-Path $parent)) {
        New-Item -ItemType Directory -Force -Path $parent | Out-Null
    }

    # Evitar bloqueo si PowerShell esta dentro de RepoDir.
    if ((Get-Location).Path -like "$Directory*") {
        Set-Location $parent
    }

    $tempRoot = Join-Path $env:TEMP ("SeparadorNominas_sync_" + [guid]::NewGuid().ToString("N"))
    $zipPath = Join-Path $tempRoot "repo.zip"
    New-Item -ItemType Directory -Force -Path $tempRoot | Out-Null

    try {
        Invoke-WebRequest -Uri $DownloadUrl -OutFile $zipPath
        Expand-Archive -Path $zipPath -DestinationPath $tempRoot -Force

        $extracted = Get-ChildItem -Path $tempRoot -Directory |
            Where-Object { $_.Name -like "$RepoName-*" } |
            Select-Object -First 1
        if (-not $extracted) {
            throw "No se encontro la carpeta extraida del ZIP."
        }

        if (-not (Test-Path $Directory)) {
            New-Item -ItemType Directory -Force -Path $Directory | Out-Null
        }

        # Copiar contenido sobre la carpeta existente (preserva .venv).
        $excludeDirs = @(".venv", "dist", "build", ".git")
        Get-ChildItem -Path $extracted.FullName -Force | ForEach-Object {
            if ($excludeDirs -contains $_.Name) {
                return
            }
            $target = Join-Path $Directory $_.Name
            if ($_.PSIsContainer) {
                if (Test-Path $target) {
                    Remove-Item -Recurse -Force $target -ErrorAction SilentlyContinue
                }
                Copy-Item -Path $_.FullName -Destination $target -Recurse -Force
            }
            else {
                Copy-Item -Path $_.FullName -Destination $target -Force
            }
        }

        Write-Host "Codigo actualizado desde ZIP (se conserva .venv si existia)."
    }
    finally {
        if (Test-Path $tempRoot) {
            Remove-Item -Recurse -Force $tempRoot -ErrorAction SilentlyContinue
        }
    }
}

function Initialize-Repository {
    param(
        [string] $Directory,
        [string] $BranchName,
        [string] $GitExe
    )

    $parent = Split-Path -Parent $Directory
    if (-not (Test-Path $parent)) {
        New-Item -ItemType Directory -Force -Path $parent | Out-Null
        Write-Host "Creada carpeta: $parent"
    }

    if (-not (Test-Path $Directory)) {
        if ($GitExe) {
            Write-Step "Clonando repositorio en $Directory ..."
            & $GitExe clone --branch $BranchName $RepoUrl $Directory
            if ($LASTEXITCODE -ne 0) {
                throw "git clone ha fallado."
            }
            return
        }

        Sync-WithZip -Directory $Directory -BranchName $BranchName -DownloadUrl $ZipUrl
        return
    }

    if ($GitExe) {
        $ok = Sync-WithGit -GitExe $GitExe -Directory $Directory -BranchName $BranchName
        if ($ok) {
            return
        }
    }

    Sync-WithZip -Directory $Directory -BranchName $BranchName -DownloadUrl $ZipUrl
}

# --- Principal ---

Write-Host "SeparadorNominas - sync + build + run" -ForegroundColor Green
Write-Host "Repo: $RepoOwner/$RepoName  Rama: $Branch"
Write-Host "Carpeta: $RepoDir"

$gitExe = Get-GitExe
if ($gitExe) {
    Write-Host "Git detectado: $gitExe"
}
else {
    Write-Host "Git no detectado en PATH; se usara descarga ZIP si hace falta."
}

Initialize-Repository -Directory $RepoDir -BranchName $Branch -GitExe $gitExe

if (-not (Test-Path (Join-Path $RepoDir "scripts\build.ps1"))) {
    throw "No se encontro scripts\build.ps1 en $RepoDir"
}

Set-Location $RepoDir

$exePath = Join-Path $RepoDir "dist\SeparadorNominas.exe"

if (-not $SkipBuild) {
    Write-Step "Compilando con scripts\build.ps1 ..."
    & (Join-Path $RepoDir "scripts\build.ps1")
    if ($LASTEXITCODE -ne 0) {
        throw "La compilacion ha fallado (codigo $LASTEXITCODE). No se abrira la aplicacion."
    }
}
else {
    Write-Step "Omitiendo compilacion (-SkipBuild)."
}

if (-not (Test-Path $exePath)) {
    throw "No existe el ejecutable: $exePath"
}

if (-not $NoLaunch) {
    Write-Step "Abriendo SeparadorNominas.exe ..."
    Start-Process -FilePath $exePath
    Write-Host "Aplicacion lanzada."
}
else {
    Write-Step "Compilacion lista (-NoLaunch). Ejecutable:"
    Write-Host "  $exePath"
}

Write-Host ""
Write-Host "Proceso completado." -ForegroundColor Green
exit 0
