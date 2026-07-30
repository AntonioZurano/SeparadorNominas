#Requires -Version 5.1
<#
.SYNOPSIS
    Funciones compartidas para preparar y publicar releases de SeparadorNominas.
.NOTES
    Este archivo se carga con dot-sourcing desde prepare-release.ps1 y publish-release.ps1.
    No contiene tokens ni credenciales.
#>

Set-StrictMode -Version Latest

function Get-RepoRoot {
    param(
        [Parameter(Mandatory = $true)]
        [string]$ScriptRoot
    )
    return (Resolve-Path (Join-Path $ScriptRoot "..")).Path
}

function Get-ProjectVersion {
    param(
        [Parameter(Mandatory = $true)]
        [string]$RepoRoot
    )
    $versionPath = Join-Path $RepoRoot "VERSION"
    if (-not (Test-Path -LiteralPath $versionPath)) {
        throw "No existe el archivo VERSION en la raíz del repositorio."
    }
    $raw = Get-Content -LiteralPath $versionPath -Raw -ErrorAction Stop
    $version = ($raw -replace "[\r\n]+", "").Trim()
    if ([string]::IsNullOrWhiteSpace($version)) {
        throw "El archivo VERSION está vacío."
    }
    return $version
}

function Test-VersionFormat {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Version
    )
    # SemVer flexible: 1.1.0 | 1.1.0-rc.1 | 1.1.0-dev.1
    return [bool]($Version -match '^\d+\.\d+\.\d+([.-][A-Za-z0-9.-]+)?$')
}

function Assert-VersionMatchesProject {
    param(
        [Parameter(Mandatory = $true)]
        [string]$RepoRoot,
        [Parameter(Mandatory = $true)]
        [string]$Version
    )
    $projectVersion = Get-ProjectVersion -RepoRoot $RepoRoot
    if ($Version -ne $projectVersion) {
        throw ("La versión indicada '{0}' no coincide con VERSION ('{1}')." -f $Version, $projectVersion)
    }
    if (-not (Test-VersionFormat -Version $Version)) {
        throw ("La versión '{0}' no tiene un formato válido." -f $Version)
    }
    return $projectVersion
}

function Get-ReleaseTagName {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Version
    )
    if ($Version.StartsWith("v")) {
        return $Version
    }
    return "v$Version"
}

function Get-ReleaseAssetNames {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Version
    )
    $exeName = "SeparadorNominas-v$Version-win64.exe"
    return [pscustomobject]@{
        ExeName      = $exeName
        ChecksumName = "$exeName.sha256"
        TagName      = (Get-ReleaseTagName -Version $Version)
        ReleaseTitle = "SeparadorNominas v$Version"
    }
}

function Get-ReleaseAssetsDirectory {
    param(
        [Parameter(Mandatory = $true)]
        [string]$RepoRoot
    )
    return (Join-Path $RepoRoot "release-assets")
}

function Format-Sha256FileContent {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Hash,
        [Parameter(Mandatory = $true)]
        [string]$FileName
    )
    return ("{0}  {1}" -f $Hash.ToUpperInvariant(), $FileName)
}

function Get-ChangelogSection {
    param(
        [Parameter(Mandatory = $true)]
        [string]$RepoRoot,
        [Parameter(Mandatory = $true)]
        [string]$Version
    )
    $changelogPath = Join-Path $RepoRoot "CHANGELOG.md"
    if (-not (Test-Path -LiteralPath $changelogPath)) {
        return $null
    }
    $lines = Get-Content -LiteralPath $changelogPath
    $header = "## [$Version]"
    $start = -1
    for ($i = 0; $i -lt $lines.Count; $i++) {
        if ($lines[$i].StartsWith($header)) {
            $start = $i
            break
        }
    }
    if ($start -lt 0) {
        return $null
    }
    $buffer = New-Object System.Collections.Generic.List[string]
    for ($j = $start + 1; $j -lt $lines.Count; $j++) {
        if ($lines[$j] -match '^## \[') {
            break
        }
        [void]$buffer.Add($lines[$j])
    }
    $text = ($buffer -join "`n").Trim()
    if ([string]::IsNullOrWhiteSpace($text)) {
        return $null
    }
    return $text
}
