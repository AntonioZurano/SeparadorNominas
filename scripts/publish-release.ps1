#Requires -Version 5.1
<#
.SYNOPSIS
    Publica el ejecutable versionado como asset de una GitHub Release.
.DESCRIPTION
    Valida versión, tag remota, assets y autenticación gh. Requiere confirmación.
    No crea tags ni hace push. No reemplaza assets existentes automáticamente.
.PARAMETER Version
    Versión a publicar (debe coincidir con VERSION), sin prefijo v obligatorio.
.PARAMETER Prerelease
    Marca la Release como prerelease.
.PARAMETER Draft
    Crea la Release como borrador.
.PARAMETER DryRun
    Ejecuta validaciones locales/remotas de lectura y muestra el plan sin publicar.
.PARAMETER ConfirmAnswer
    Respuesta simulada a la confirmación (S/N). Uso interno/tests.
.EXAMPLE
    .\scripts\publish-release.ps1 -Version "1.1.0" -DryRun
.EXAMPLE
    .\scripts\publish-release.ps1 -Version "1.1.0"
#>
param(
    [Parameter(Mandatory = $true)]
    [string]$Version,

    [switch]$Prerelease,

    [switch]$Draft,

    [switch]$DryRun,

    [string]$ConfirmAnswer = ""
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

. (Join-Path $PSScriptRoot "ReleaseCommon.ps1")

function Test-CommandAvailable {
    param([string]$Name)
    return [bool](Get-Command $Name -ErrorAction SilentlyContinue)
}

function Assert-GitClean {
    $status = & git status --porcelain
    if ($LASTEXITCODE -ne 0) {
        throw "No se ha podido comprobar el estado de Git."
    }
    if (-not [string]::IsNullOrWhiteSpace(($status | Out-String).Trim())) {
        throw "Hay cambios pendientes en el repositorio. Confirma o limpia el working tree antes de publicar."
    }
}

function Test-RemoteTagExists {
    param(
        [Parameter(Mandatory = $true)]
        [string]$TagName
    )
    $prev = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    $refs = & git ls-remote --tags origin $TagName 2>$null
    $code = $LASTEXITCODE
    $ErrorActionPreference = $prev
    if ($code -ne 0) {
        throw "No se ha podido consultar las tags remotas en origin."
    }
    return -not [string]::IsNullOrWhiteSpace(($refs | Out-String).Trim())
}

function Test-ReleaseExists {
    param(
        [Parameter(Mandatory = $true)]
        [string]$TagName
    )
    # gh escribe "release not found" en stderr; con Stop eso abortaría el script.
    $prev = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    & gh release view $TagName 1>$null 2>$null
    $code = $LASTEXITCODE
    $ErrorActionPreference = $prev
    return ($code -eq 0)
}

function Test-ReleaseAssetExists {
    param(
        [Parameter(Mandatory = $true)]
        [string]$TagName,
        [Parameter(Mandatory = $true)]
        [string]$AssetName
    )
    $prev = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    $json = & gh release view $TagName --json assets 2>$null
    $code = $LASTEXITCODE
    $ErrorActionPreference = $prev
    if ($code -ne 0) {
        return $false
    }
    return ($json -match [regex]::Escape('"name":"' + $AssetName + '"') -or
            $json -match [regex]::Escape('"name": "' + $AssetName + '"'))
}

try {
    $RepoRoot = Get-RepoRoot -ScriptRoot $PSScriptRoot
    Set-Location -LiteralPath $RepoRoot

    if (-not (Test-CommandAvailable -Name "git")) {
        throw "Git no está instalado o no está en el PATH."
    }
    if (-not (Test-CommandAvailable -Name "gh")) {
        throw "GitHub CLI (gh) no está instalado o no está en el PATH."
    }

    $prevAuth = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    & gh auth status 1>$null 2>$null
    $authCode = $LASTEXITCODE
    $ErrorActionPreference = $prevAuth
    if ($authCode -ne 0) {
        throw "GitHub CLI no está autenticado. Ejecuta: gh auth login"
    }

    $useVersion = $Version.Trim()
    if ($useVersion.StartsWith("v") -and ($useVersion -match '^v\d')) {
        $useVersion = $useVersion.Substring(1)
    }
    Assert-VersionMatchesProject -RepoRoot $RepoRoot -Version $useVersion | Out-Null

    $names = Get-ReleaseAssetNames -Version $useVersion
    $tagName = $names.TagName
    $assetsDir = Get-ReleaseAssetsDirectory -RepoRoot $RepoRoot
    $exePath = Join-Path $assetsDir $names.ExeName
    $checksumPath = Join-Path $assetsDir $names.ChecksumName

    if (-not (Test-Path -LiteralPath $exePath)) {
        throw ("No existe el ejecutable preparado: {0}. Ejecuta antes .\scripts\prepare-release.ps1." -f $exePath)
    }
    if (-not (Test-Path -LiteralPath $checksumPath)) {
        throw ("No existe el checksum preparado: {0}. Ejecuta antes .\scripts\prepare-release.ps1." -f $checksumPath)
    }
    if ((Get-Item -LiteralPath $exePath).Length -le 0) {
        throw "El ejecutable preparado está vacío."
    }

    $originUrl = & git remote get-url origin 2>$null
    if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($originUrl)) {
        throw "No existe el remoto origin."
    }

    Assert-GitClean

    # git fetch escribe progreso en stderr; con Stop abortaría el script.
    $prevEa = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    & git fetch origin --tags 1>$null 2>$null
    $fetchCode = $LASTEXITCODE
    $ErrorActionPreference = $prevEa
    if ($fetchCode -ne 0) {
        throw "No se ha podido actualizar tags desde origin."
    }
    $tagExistsRemote = Test-RemoteTagExists -TagName $tagName
    if (-not $tagExistsRemote) {
        if ($DryRun) {
            Write-Host ("AVISO DryRun: la tag {0} aún no existe en origin (esperado antes de autorizar el tag)." -f $tagName)
        }
        else {
            Write-Error ("La tag {0} no existe. Debe crearse y publicarse previamente con autorización expresa." -f $tagName)
            exit 1
        }
    }

    $tagCommit = "(pendiente de crear)"
    if ($tagExistsRemote) {
        # Coherencia: la tag debe resolverse localmente tras el fetch.
        $resolvedTag = & git rev-list -n 1 $tagName 2>$null
        if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($resolvedTag)) {
            throw ("No se ha podido resolver el commit de la tag local {0} tras fetch." -f $tagName)
        }
        $tagCommit = $resolvedTag
    }
    $headCommit = & git rev-parse HEAD
    if ($LASTEXITCODE -ne 0) {
        throw "No se ha podido obtener el commit HEAD."
    }

    $prevRepo = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    $repoSlug = & gh repo view --json nameWithOwner -q .nameWithOwner 2>$null
    $repoCode = $LASTEXITCODE
    $ErrorActionPreference = $prevRepo
    if ($repoCode -ne 0 -or [string]::IsNullOrWhiteSpace($repoSlug)) {
        $repoSlug = $originUrl
    }

    $releaseType = "Release estable"
    if ($Draft) { $releaseType = "Borrador (draft)" }
    elseif ($Prerelease) { $releaseType = "Prerelease" }

    $releaseExists = $false
    if ($tagExistsRemote) {
        $releaseExists = Test-ReleaseExists -TagName $tagName
        if ($releaseExists) {
            foreach ($assetName in @($names.ExeName, $names.ChecksumName)) {
                if (Test-ReleaseAssetExists -TagName $tagName -AssetName $assetName) {
                    throw ("Ya existe un asset con el nombre '{0}' en la Release {1}. No se reemplaza automáticamente. Consulta docs/PUBLICACION_GITHUB.md para el reemplazo manual autorizado." -f $assetName, $tagName)
                }
            }
        }
    }

    Write-Host ""
    Write-Host ("Repositorio: {0}" -f $repoSlug)
    Write-Host ("Versión: {0}" -f $useVersion)
    Write-Host ("Tag: {0}" -f $tagName)
    Write-Host ("Commit tag: {0}" -f $tagCommit)
    Write-Host ("Commit HEAD: {0}" -f $headCommit)
    Write-Host ("Tipo: {0}" -f $releaseType)
    Write-Host ("Ejecutable: {0}" -f $names.ExeName)
    Write-Host ("Checksum: {0}" -f $names.ChecksumName)
    if ($releaseExists) {
        Write-Host "Acción prevista: subir assets a Release existente (sin sobrescribir)."
    }
    elseif ($tagExistsRemote) {
        Write-Host "Acción prevista: crear Release nueva y adjuntar assets."
    }
    else {
        Write-Host "Acción prevista (tras crear tag): crear Release nueva y adjuntar assets."
    }
    if ($DryRun) {
        Write-Host ""
        Write-Host "DryRun: no se creará ni modificará ninguna Release."
        exit 0
    }

    $answer = $ConfirmAnswer
    if ([string]::IsNullOrWhiteSpace($answer)) {
        Write-Host ""
        $answer = Read-Host "¿Deseas crear o actualizar esta GitHub Release? [S/N]"
    }
    if ($answer.Trim().ToUpperInvariant() -ne "S") {
        Write-Host "Operación cancelada. No se ha modificado GitHub."
        exit 0
    }

    $notes = Get-ChangelogSection -RepoRoot $RepoRoot -Version $useVersion
    $notesFile = $null

    if (-not $releaseExists) {
        $createArgs = @(
            "release", "create", $tagName,
            $exePath,
            $checksumPath,
            "--title", $names.ReleaseTitle
        )
        if ($null -ne $notes) {
            $notesFile = Join-Path $env:TEMP ("separador-nominas-notes-{0}.md" -f $useVersion)
            Set-Content -LiteralPath $notesFile -Value $notes -Encoding utf8
            $createArgs += @("--notes-file", $notesFile)
        }
        else {
            $createArgs += "--generate-notes"
        }
        if ($Prerelease) { $createArgs += "--prerelease" }
        if ($Draft) { $createArgs += "--draft" }

        & gh @createArgs
        if ($LASTEXITCODE -ne 0) {
            throw "gh release create ha fallado."
        }
    }
    else {
        $uploadArgs = @(
            "release", "upload", $tagName,
            $exePath,
            $checksumPath
        )
        & gh @uploadArgs
        if ($LASTEXITCODE -ne 0) {
            throw "gh release upload ha fallado."
        }
    }

    if ($null -ne $notesFile -and (Test-Path -LiteralPath $notesFile)) {
        Remove-Item -LiteralPath $notesFile -Force -ErrorAction SilentlyContinue
    }

    Write-Host ""
    Write-Host "Publicación completada."
    Write-Host ("  https://github.com/{0}/releases/tag/{1}" -f $repoSlug, $tagName)
    exit 0
}
catch {
    Write-Error $_.Exception.Message
    exit 1
}
