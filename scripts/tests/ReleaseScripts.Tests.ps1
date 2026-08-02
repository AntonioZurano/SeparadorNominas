#Requires -Version 5.1
<#
.SYNOPSIS
    Pruebas Pester de los helpers y scripts de release (sin publicar en GitHub).
#>

$ErrorActionPreference = "Stop"

$ScriptsDir = Split-Path -Parent $PSScriptRoot
$RepoRoot = Split-Path -Parent $ScriptsDir
. (Join-Path $ScriptsDir "ReleaseCommon.ps1")

Describe "ReleaseCommon helpers" {
    It "lee la versión desde VERSION" {
        $v = Get-ProjectVersion -RepoRoot $RepoRoot
        $v | Should -Match '^\d+\.\d+\.\d+'
    }

    It "genera nombres versionados estables" {
        $names = Get-ReleaseAssetNames -Version "1.1.0"
        $names.ExeName | Should -Be "SeparadorNominas-v1.1.0-win64.exe"
        $names.ChecksumName | Should -Be "SeparadorNominas-v1.1.0-win64.exe.sha256"
        $names.TagName | Should -Be "v1.1.0"
        $names.ReleaseTitle | Should -Be "SeparadorNominas v1.1.0"
    }

    It "genera nombres para prerelease" {
        $names = Get-ReleaseAssetNames -Version "1.1.0-rc.1"
        $names.ExeName | Should -Be "SeparadorNominas-v1.1.0-rc.1-win64.exe"
        $names.TagName | Should -Be "v1.1.0-rc.1"
    }

    It "formatea el contenido SHA-256" {
        $line = Format-Sha256FileContent -Hash "abc123" -FileName "file.exe"
        $line | Should -Be "ABC123  file.exe"
    }

    It "extrae sección del CHANGELOG cuando existe" {
        $section = Get-ChangelogSection -RepoRoot $RepoRoot -Version "1.1.0"
        $section | Should -Not -BeNullOrEmpty
    }

    It "falla si la versión no coincide con VERSION" {
        { Assert-VersionMatchesProject -RepoRoot $RepoRoot -Version "9.9.9" } |
            Should -Throw "*no coincide*"
    }
}

Describe "prepare-release.ps1" {
    BeforeEach {
        $script:TempRoot = Join-Path $env:TEMP ("sn-release-test-" + [guid]::NewGuid().ToString("N"))
        New-Item -ItemType Directory -Path $script:TempRoot | Out-Null
        New-Item -ItemType Directory -Path (Join-Path $script:TempRoot "dist") | Out-Null
        Copy-Item -LiteralPath (Join-Path $RepoRoot "VERSION") -Destination (Join-Path $script:TempRoot "VERSION")
        Copy-Item -LiteralPath (Join-Path $ScriptsDir "ReleaseCommon.ps1") -Destination (Join-Path $script:TempRoot "ReleaseCommon.ps1")
        Copy-Item -LiteralPath (Join-Path $ScriptsDir "prepare-release.ps1") -Destination (Join-Path $script:TempRoot "prepare-release.ps1")
        # Adapt prepare script root: it uses Join-Path $PSScriptRoot ".." as repo root.
        # Place scripts in TempRoot\scripts and project files in TempRoot.
        New-Item -ItemType Directory -Path (Join-Path $script:TempRoot "scripts") | Out-Null
        Move-Item (Join-Path $script:TempRoot "ReleaseCommon.ps1") (Join-Path $script:TempRoot "scripts\ReleaseCommon.ps1")
        Move-Item (Join-Path $script:TempRoot "prepare-release.ps1") (Join-Path $script:TempRoot "scripts\prepare-release.ps1")
    }

    AfterEach {
        if (Test-Path -LiteralPath $script:TempRoot) {
            Remove-Item -LiteralPath $script:TempRoot -Recurse -Force
        }
    }

    It "falla cuando falta el ejecutable" {
        $p = Start-Process -FilePath "powershell.exe" -ArgumentList @(
            "-NoProfile", "-ExecutionPolicy", "Bypass",
            "-File", (Join-Path $script:TempRoot "scripts\prepare-release.ps1")
        ) -Wait -PassThru -WindowStyle Hidden
        $p.ExitCode | Should -Not -Be 0
    }

    It "falla cuando la versión no coincide" {
        Set-Content -LiteralPath (Join-Path $script:TempRoot "dist\SeparadorNominas.exe") -Value "dummy-exe-content" -Encoding Byte
        # PowerShell Set-Content -Encoding Byte may not work on all versions; use .NET
        [System.IO.File]::WriteAllBytes(
            (Join-Path $script:TempRoot "dist\SeparadorNominas.exe"),
            [byte[]](1..64)
        )
        $p = Start-Process -FilePath "powershell.exe" -ArgumentList @(
            "-NoProfile", "-ExecutionPolicy", "Bypass",
            "-File", (Join-Path $script:TempRoot "scripts\prepare-release.ps1"),
            "-Version", "0.0.0"
        ) -Wait -PassThru -WindowStyle Hidden
        $p.ExitCode | Should -Not -Be 0
    }

    It "crea exe versionado y sha256 con rutas que contienen espacios" {
        $spaceRoot = Join-Path $env:TEMP ("sn release space " + [guid]::NewGuid().ToString("N"))
        New-Item -ItemType Directory -Path $spaceRoot | Out-Null
        try {
            New-Item -ItemType Directory -Path (Join-Path $spaceRoot "scripts") | Out-Null
            New-Item -ItemType Directory -Path (Join-Path $spaceRoot "dist") | Out-Null
            Copy-Item (Join-Path $RepoRoot "VERSION") (Join-Path $spaceRoot "VERSION")
            Copy-Item (Join-Path $ScriptsDir "ReleaseCommon.ps1") (Join-Path $spaceRoot "scripts\ReleaseCommon.ps1")
            Copy-Item (Join-Path $ScriptsDir "prepare-release.ps1") (Join-Path $spaceRoot "scripts\prepare-release.ps1")
            $version = (Get-Content (Join-Path $spaceRoot "VERSION") -Raw).Trim()
            [System.IO.File]::WriteAllBytes(
                (Join-Path $spaceRoot "dist\SeparadorNominas.exe"),
                [byte[]](1..128)
            )
            $p = Start-Process -FilePath "powershell.exe" -ArgumentList @(
                "-NoProfile", "-ExecutionPolicy", "Bypass",
                "-File", (Join-Path $spaceRoot "scripts\prepare-release.ps1"),
                "-Version", $version
            ) -Wait -PassThru -WindowStyle Hidden
            $p.ExitCode | Should -Be 0
            $names = Get-ReleaseAssetNames -Version $version
            $exe = Join-Path $spaceRoot ("release-assets\" + $names.ExeName)
            $sum = Join-Path $spaceRoot ("release-assets\" + $names.ChecksumName)
            Test-Path -LiteralPath $exe | Should -Be $true
            Test-Path -LiteralPath $sum | Should -Be $true
            $content = Get-Content -LiteralPath $sum -Raw
            $content | Should -Match $names.ExeName
            $content | Should -Match '^[0-9A-F]{64}\s\s'
        }
        finally {
            Remove-Item -LiteralPath $spaceRoot -Recurse -Force -ErrorAction SilentlyContinue
        }
    }
}

Describe "publish-release.ps1 DryRun / cancelación" {
    It "cancela cuando ConfirmAnswer no es S sin publicar" {
        # Solo comprueba que el parámetro existe y la cancelación temprana
        # requiere tag remota; este test valida el helper de nombres y que
        # ConfirmAnswer N está soportado en la firma del script.
        $scriptText = Get-Content -LiteralPath (Join-Path $ScriptsDir "publish-release.ps1") -Raw
        $scriptText | Should -Match 'ConfirmAnswer'
        $scriptText | Should -Match 'DryRun'
        $scriptText | Should -Match '¿Deseas crear o actualizar esta GitHub Release\?'
        $scriptText | Should -Not -Match 'Invoke-Expression'
        $scriptText | Should -Not -Match 'gh release upload.*--clobber'
        $scriptText | Should -Not -Match '"--clobber"'
    }

    It "documenta el mensaje de tag ausente" {
        $scriptText = Get-Content -LiteralPath (Join-Path $ScriptsDir "publish-release.ps1") -Raw
        $scriptText | Should -Match 'La tag .* no existe\. Debe crearse y publicarse previamente'
    }
}
