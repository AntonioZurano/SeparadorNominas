# Publicación GitHub Release — v2.5.0 (estable)

## Estado de publicación

| Campo | Valor |
|-------|--------|
| Estado | **Publicada** (Release estable / Latest) |
| Tag | `v2.5.0` |
| Commit del tag | `54c0aaace3e4ce558d4da7bf824065956c26e714` (merge a `main` de la línea 2.5.0) |
| URL | https://github.com/AntonioZurano/SeparadorNominas/releases/tag/v2.5.0 |
| Fecha de publicación (`publishedAt`) | 2026-08-02T16:20:14Z |
| Prerelease / borrador | No / No |
| Assets | `SeparadorNominas-v2.5.0-win64.exe`, `SeparadorNominas-v2.5.0-win64.exe.sha256` |

Las betas `v2.5.0-beta.1` y `v2.5.0-beta.2` permanecen como prereleases
históricas.

**Distinción:** «publicado» significa que la Release y sus assets existen en
GitHub. «Verificado» más abajo distingue hechos contrastados en documentación
o API de tareas del proceso de build que no se han vuelto a reproducir.

Este documento es el **registro** de la publicación estable 2.5.0. El flujo
general para futuras versiones está en
[`PUBLICACION_GITHUB.md`](PUBLICACION_GITHUB.md).

## Checklist de hechos (comprobado / no verificable)

### Código y documentación en el repositorio (comprobado)

- [x] `VERSION`, `pyproject.toml` y `APP_VERSION` = `2.5.0`
- [x] `APP_IS_PRERELEASE = False` (sin canal BETA en la UI estable)
- [x] `CHANGELOG.md` incluye la sección `## [2.5.0]`
- [x] El tip de `main` declara la misma versión (puede incluir commits
  documentales posteriores al tag, p. ej. captura del README)

### Tag y Release en GitHub (comprobado)

- [x] Existe el tag anotado `v2.5.0` apuntando al commit indicado arriba
- [x] Existe la Release `v2.5.0`, no marcada como prerelease ni draft
- [x] Aparece como **Latest** en la lista de Releases
- [x] Assets publicados con los nombres esperados (exe + `.sha256`)
- [x] Las prereleases beta.1 y beta.2 siguen listadas

### Proceso de build y publicación (histórico / no verificable aquí)

Estas tareas figuran en el **procedimiento histórico previsto** más abajo.
Su ejecución concreta en el momento de publicar **no se ha podido verificar**
con la evidencia disponible en el repositorio ni en la API de GitHub:

- [ ] Working tree limpio en el clon Windows usado para compilar (estado
  puntual del momento del build; **no verificable** a posteriori)
- [ ] Ejecución de `scripts/build.ps1` y `prepare-release.ps1` en esa sesión
  (**no verificable**; la existencia de assets en la Release no demuestra
  qué comandos o scripts los generaron)
- [ ] DryRun de `publish-release.ps1` (**no verificable**; sin registro
  conservado en el repo)
- [ ] Comprobación byte a byte del SHA-256 del exe frente al archivo
  `.sha256` en la máquina del lector (**pendiente de quien descargue**)
- [ ] Arranque visual del `.exe` y título UI «sin BETA»
  (**no verificado** en la redacción de este registro; el código estable
  tiene `APP_IS_PRERELEASE = False`)

## Procedimiento histórico previsto

Los apartados siguientes documentan el **procedimiento previsto** para
publicar la estable 2.5.0 según la guía del proyecto. Lo comprobado en
«Estado de publicación» es la existencia de la Release, el tag y los
assets; **eso no demuestra** que cada paso siguiente se ejecutara tal cual
ni que pueda revalidarse ahora.

**No** vuelvas a publicar la misma tag ni sustituyas el `.exe` sin orden
expresa.

### 1. Tag estable

Desde el commit de `main` correspondiente a la línea 2.5.0:

```bash
git switch main
git pull --ff-only origin main
git tag -a v2.5.0 -m "SeparadorNominas 2.5.0 (Excel departamentos)"
git push origin v2.5.0
```

La tag debía existir en origin antes de `publish-release.ps1`.

### 2. Build Windows

En el clon Windows autorizado (p. ej. `C:\Dev\SeparadorNominas`):

```powershell
git fetch origin
git switch main
git pull --ff-only origin main
.\scripts\build.ps1
.\scripts\prepare-release.ps1 -Version "2.5.0"
```

Assets esperados (gitignored):

```text
release-assets/SeparadorNominas-v2.5.0-win64.exe
release-assets/SeparadorNominas-v2.5.0-win64.exe.sha256
```

### 3. DryRun

```powershell
.\scripts\publish-release.ps1 -Version "2.5.0" -DryRun
```

Sin `-Prerelease` (Release estable / Latest).

### 4. Publicar Release

```powershell
.\scripts\publish-release.ps1 -Version "2.5.0" -ConfirmAnswer "S"
```

URL:

```text
https://github.com/AntonioZurano/SeparadorNominas/releases/tag/v2.5.0
```

### 5. Notas UTF-8

Tras publicar, conviene revisar acentos en las notas de la Release. Si hay
mojibake, corregir solo las notas (con autorización):

```powershell
gh release edit "v2.5.0" --notes-file "release-notes-v2.5.0.md"
```

Usar GitHub CLI reciente. No reemplazar el `.exe` ni el checksum salvo orden.

## Referencias

- Flujo general: [`PUBLICACION_GITHUB.md`](PUBLICACION_GITHUB.md)
- Compilación: [`COMPILACION_WINDOWS.md`](COMPILACION_WINDOWS.md)
- Changelog: [`CHANGELOG.md`](../CHANGELOG.md)
- Descarga para usuarios: sección correspondiente en [`README.md`](../README.md)
