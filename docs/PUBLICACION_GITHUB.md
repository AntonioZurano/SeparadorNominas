# Publicación del ejecutable en GitHub Releases

Esta guía describe cómo distribuir `SeparadorNominas.exe` como **asset** de
una [GitHub Release](https://docs.github.com/en/repositories/releasing-projects-on-github),
sin almacenar binarios en el historial Git.

## GitHub Releases frente a GitHub Packages

| Canal | Uso en este proyecto |
|-------|----------------------|
| **GitHub Releases** | Distribución del `.exe` de Windows + checksum SHA-256. |
| **GitHub Packages** | **No** se utiliza para el ejecutable. |

Reglas:

- Los binarios compilados **no** se suben mediante commits.
- Las carpetas `dist/` y `release-assets/` son locales y están en `.gitignore`.
- Cada Release está asociada a una **tag** de Git (`v2.5.0-beta.1`, `v2.0.0`, …).
- Las versiones de prueba pueden publicarse como **prereleases** cuando se ordene.

## Fuente de versión

La fuente principal es el archivo [`VERSION`](../VERSION) en la raíz.

También deben mantenerse coherentes (cuando se ordene un bump):

- `pyproject.toml` (`project.version`)
- `CHANGELOG.md` (sección de la versión)

Los scripts de publicación leen **solo** `VERSION`.

## Convención de nombres

```text
SeparadorNominas-vVERSION-win64.exe
SeparadorNominas-vVERSION-win64.exe.sha256
Tag: vVERSION
```

Ejemplo: `SeparadorNominas-v2.5.0-beta.1-win64.exe`.

El script `build.ps1` incluye hidden imports de `openpyxl`/`xlrd` para el
modo Excel; ver [`COMPILACION_WINDOWS.md`](COMPILACION_WINDOWS.md).

**Decisión:** no se publica un alias estable `SeparadorNominas-win64.exe`, para
evitar ambigüedad sobre qué versión se descarga. Cada Release usa el nombre
versionado.

## Requisitos

- Windows 10 u 11 (compilación y scripts PowerShell).
- Python 3.11+ y entorno del proyecto (ver [`COMPILACION_WINDOWS.md`](COMPILACION_WINDOWS.md)).
- Git.
- [GitHub CLI](https://cli.github.com/) (`gh`).
- Permisos de escritura en el repositorio.
- Autenticación con GitHub CLI (sin tokens en archivos del repo).

### Comprobar e instalar GitHub CLI

```powershell
gh --version
gh auth login
gh auth status
```

No guardes tokens ni credenciales en el repositorio ni en los scripts.

## Flujo completo

### 1. Código estable

El código debe estar integrado según el flujo del proyecto
([`CONTRIBUTING.md`](../CONTRIBUTING.md)): trabajo en rama → `development` →
pruebas → `main` (solo con autorización). La tag de la versión se crea **solo**
con autorización expresa.

### 2. Compilar en Windows

```powershell
git switch main   # o la rama autorizada para el release
git status
.\scripts\test.ps1
.\scripts\build.ps1
```

Resultado local:

```text
dist/SeparadorNominas.exe
```

### 3. Preparar assets (sin publicar)

```powershell
.\scripts\prepare-release.ps1
# o forzando comprobación de versión:
.\scripts\prepare-release.ps1 -Version "1.1.0"
```

Genera:

```text
release-assets/
├── SeparadorNominas-v1.1.0-win64.exe
└── SeparadorNominas-v1.1.0-win64.exe.sha256
```

Este paso **no** crea tags, Releases ni hace push.

### 4. Tag (autorización expresa)

La tag `vVERSION` debe existir en el remoto **antes** de publicar assets.
Los scripts **no** crean tags automáticamente.

### 5. Publicar assets en la Release

Simulación (recomendado primero):

```powershell
.\scripts\publish-release.ps1 -Version "1.1.0" -DryRun
```

Publicación real (solo con orden expresa):

```powershell
.\scripts\publish-release.ps1 -Version "1.1.0"
```

Confirmación interactiva:

```text
¿Deseas crear o actualizar esta GitHub Release? [S/N]
```

Solo continúa con `S`.

Prerelease o borrador:

```powershell
.\scripts\publish-release.ps1 -Version "1.1.0-rc.1" -Prerelease
.\scripts\publish-release.ps1 -Version "1.1.0" -Draft
```

## Resultado esperado

```text
GitHub
└── Releases
    └── SeparadorNominas v1.1.0
        ├── SeparadorNominas-v1.1.0-win64.exe
        └── SeparadorNominas-v1.1.0-win64.exe.sha256
```

## Descarga para usuarios

1. Abrir [Releases](https://github.com/AntonioZurano/SeparadorNominas/releases).
2. Elegir la versión.
3. Descargar el `.exe` desde **Assets**.
4. (Opcional) Verificar el SHA-256 con el archivo `.sha256`.

Patrón de URL de un asset versionado:

```text
https://github.com/AntonioZurano/SeparadorNominas/releases/latest/download/SeparadorNominas-v1.1.0-win64.exe
```

Esa URL incluye el número de versión en el nombre del archivo; cambia en cada
Release. Por eso no se publica un nombre fijo genérico.

## Notas de la Release

`publish-release.ps1`:

1. Intenta extraer la sección `## [VERSION]` de `CHANGELOG.md`.
2. Si no hay sección usable, usa `--generate-notes` de GitHub CLI.

Título: `SeparadorNominas vVERSION`.

## Si el asset ya existe

Los scripts **no** usan `--clobber`. Si el asset ya está en la Release, el
proceso se detiene.

Reemplazo manual (solo con autorización expresa):

```powershell
gh release delete-asset "v1.1.0" "SeparadorNominas-v1.1.0-win64.exe" --yes
gh release upload "v1.1.0" "release-assets\SeparadorNominas-v1.1.0-win64.exe"
```

(Repetir para el `.sha256` si procede.)

## Seguridad

Los scripts **no** deben:

- Guardar tokens ni credenciales.
- Hacer `push` automáticamente.
- Crear tags automáticamente.
- Sustituir assets automáticamente.
- Incluir PDFs ni datos de nóminas en una Release.

Ninguna IA debe ejecutar `publish-release.ps1` ni reemplazar assets sin una
orden expresa del responsable del repositorio.

## Scripts

| Script | Función |
|--------|---------|
| [`scripts/build.ps1`](../scripts/build.ps1) | Tests + PyInstaller → `dist/` |
| [`scripts/prepare-release.ps1`](../scripts/prepare-release.ps1) | Copia versionada + SHA-256 → `release-assets/` |
| [`scripts/publish-release.ps1`](../scripts/publish-release.ps1) | Publica assets en GitHub Releases |
| [`scripts/ReleaseCommon.ps1`](../scripts/ReleaseCommon.ps1) | Helpers compartidos |

No hay un script que combine build + publicación de forma automática.

## Pruebas de scripts (Pester)

En Windows:

```powershell
Install-Module Pester -Scope CurrentUser -Force
Invoke-Pester -Path .\scripts\tests
```

Estas pruebas no publican Releases reales.
