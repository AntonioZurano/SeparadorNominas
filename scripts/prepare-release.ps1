#Requires -Version 5.1
<#
.SYNOPSIS
    Prepara el ejecutable versionado y su checksum SHA-256 en release-assets/.
.DESCRIPTION
    Copia dist/SeparadorNominas.exe a un nombre versionado y genera el .sha256.
    No crea tags, Releases ni modifica Git.
.PARAMETER Version
    Versión opcional. Si se indica, debe coincidir con el archivo VERSION.
.EXAMPLE
    .\scripts\prepare-release.ps1
.EXAMPLE
    .\scripts\prepare-release.ps1 -Version "1.1.0"
#>
param(
    [string]$Version = ""
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

. (Join-Path $PSScriptRoot "ReleaseCommon.ps1")

try {
    $RepoRoot = Get-RepoRoot -ScriptRoot $PSScriptRoot
    Set-Location -LiteralPath $RepoRoot

    $projectVersion = Get-ProjectVersion -RepoRoot $RepoRoot
    if (-not [string]::IsNullOrWhiteSpace($Version)) {
        Assert-VersionMatchesProject -RepoRoot $RepoRoot -Version $Version | Out-Null
        $useVersion = $Version.Trim()
    }
    else {
        $useVersion = $projectVersion
        if (-not (Test-VersionFormat -Version $useVersion)) {
            throw ("La versión del archivo VERSION ('{0}') no tiene un formato válido." -f $useVersion)
        }
    }

    $sourceExe = Join-Path $RepoRoot "dist\SeparadorNominas.exe"
    if (-not (Test-Path -LiteralPath $sourceExe)) {
        throw "No existe el ejecutable dist\SeparadorNominas.exe. Ejecuta antes .\scripts\build.ps1."
    }

    $sourceItem = Get-Item -LiteralPath $sourceExe
    if ($sourceItem.Length -le 0) {
        throw "El ejecutable dist\SeparadorNominas.exe está vacío."
    }

    $names = Get-ReleaseAssetNames -Version $useVersion
    $assetsDir = Get-ReleaseAssetsDirectory -RepoRoot $RepoRoot

    if (Test-Path -LiteralPath $assetsDir) {
        Get-ChildItem -LiteralPath $assetsDir -Force | Remove-Item -Recurse -Force -ErrorAction Stop
    }
    else {
        New-Item -ItemType Directory -Path $assetsDir -Force | Out-Null
    }
    if (-not (Test-Path -LiteralPath $assetsDir)) {
        throw "No se ha podido crear la carpeta release-assets/."
    }

    $destExe = Join-Path $assetsDir $names.ExeName
    $destChecksum = Join-Path $assetsDir $names.ChecksumName

    try {
        Copy-Item -LiteralPath $sourceExe -Destination $destExe -Force
    }
    catch {
        throw "No se ha podido copiar el ejecutable a release-assets/: $($_.Exception.Message)"
    }

    if (-not (Test-Path -LiteralPath $destExe)) {
        throw "No se ha podido copiar el ejecutable a release-assets/."
    }

    try {
        $hash = (Get-FileHash -LiteralPath $destExe -Algorithm SHA256).Hash
        $checksumContent = Format-Sha256FileContent -Hash $hash -FileName $names.ExeName
        Set-Content -LiteralPath $destChecksum -Value $checksumContent -Encoding ascii
    }
    catch {
        throw "No se ha podido calcular o escribir el checksum SHA-256: $($_.Exception.Message)"
    }

    $sizeMb = [math]::Round($sourceItem.Length / 1MB, 2)

    Write-Host ""
    Write-Host "Preparación de release completada."
    Write-Host ("  Versión:              {0}" -f $useVersion)
    Write-Host ("  Tag esperada:         {0}" -f $names.TagName)
    Write-Host ("  Ejecutable origen:    {0}" -f $sourceExe)
    Write-Host ("  Ejecutable preparado: {0}" -f $destExe)
    Write-Host ("  Tamaño:               {0} MB ({1} bytes)" -f $sizeMb, $sourceItem.Length)
    Write-Host ("  SHA-256:              {0}" -f $hash)
    Write-Host ("  Checksum:             {0}" -f $destChecksum)
    Write-Host ""
    Write-Host "Siguiente paso (solo con autorización y tag publicada):"
    Write-Host ("  .\scripts\publish-release.ps1 -Version `"{0}`"" -f $useVersion)
    exit 0
}
catch {
    Write-Error $_.Exception.Message
    exit 1
}
