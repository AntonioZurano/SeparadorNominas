# Publicación GitHub Release — v2.5.0 (estable)

Checklist para cuando se autorice **subir a GitHub** el ejecutable estable
`2.5.0`. El código debe estar ya en `main` con `VERSION=2.5.0`.

**No ejecutar estos pasos sin orden expresa.**

Las betas `v2.5.0-beta.1` y `v2.5.0-beta.2` pueden permanecer como
prereleases históricas; no las borres salvo orden.

## Estado previo (ya hecho al fusionar a main)

- [ ] `main` contiene la versión estable `2.5.0`
- [ ] `VERSION`, `pyproject.toml` y `APP_VERSION` = `2.5.0`
- [ ] `APP_IS_PRERELEASE = False` (sin aviso BETA en UI)
- [ ] `CHANGELOG.md` tiene sección `## [2.5.0]`
- [ ] Working tree limpio en el clon de publicación

## 1. Tag estable (solo con autorización)

Desde el commit de `main` que corresponde a 2.5.0:

```bash
git switch main
git pull --ff-only origin main
git tag -a v2.5.0 -m "SeparadorNominas 2.5.0 (Excel departamentos)"
git push origin v2.5.0
```

La tag **debe existir en origin** antes de `publish-release.ps1`.

## 2. Build Windows

En `C:\Dev\SeparadorNominas` (o clon Windows autorizado):

```powershell
git fetch origin
git switch main
git pull --ff-only origin main
.\scripts\build.ps1
.\scripts\prepare-release.ps1 -Version "2.5.0"
```

Comprobar:

```text
release-assets/SeparadorNominas-v2.5.0-win64.exe
release-assets/SeparadorNominas-v2.5.0-win64.exe.sha256
```

`git status` no debe listar esos assets (están en `.gitignore`).

## 3. DryRun

```powershell
.\scripts\publish-release.ps1 -Version "2.5.0" -DryRun
```

**Sin** `-Prerelease` (es Release estable / Latest).

## 4. Publicar Release

```powershell
.\scripts\publish-release.ps1 -Version "2.5.0" -ConfirmAnswer "S"
```

URL esperada:

```text
https://github.com/AntonioZurano/SeparadorNominas/releases/tag/v2.5.0
```

Assets:

- `SeparadorNominas-v2.5.0-win64.exe`
- `SeparadorNominas-v2.5.0-win64.exe.sha256`

## 5. Notas UTF-8

Tras publicar, comprobar acentos (`clasificación`, `páginas`). Si hay
mojibake (p. ej. `clasificaciÃ³n`), corregir solo las notas:

```powershell
# Generar notes UTF-8 sin BOM desde CHANGELOG (sección 2.5.0) y:
gh release edit "v2.5.0" --notes-file "release-notes-v2.5.0.md"
```

Usar GitHub CLI reciente (Windows `gh` ≥ 2.96 o `~/.local/bin/gh`).
No reemplazar el `.exe` ni el checksum salvo orden.

## 6. Verificación final

- [ ] Release **no** marcada como prerelease
- [ ] Aparece como Latest (salvo otra política)
- [ ] Descarga del exe y SHA-256 coherentes
- [ ] Título UI: `Separador de Nóminas PDF — 2.5.0` (sin BETA)
- [ ] Betas anteriores siguen disponibles si se desea

## Referencias

- Flujo general: [`PUBLICACION_GITHUB.md`](PUBLICACION_GITHUB.md)
- Compilación: [`COMPILACION_WINDOWS.md`](COMPILACION_WINDOWS.md)
- Changelog: [`CHANGELOG.md`](../CHANGELOG.md)
