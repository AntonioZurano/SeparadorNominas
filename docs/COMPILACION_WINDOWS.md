# Compilación para Windows

Esta guía describe cómo generar `SeparadorNominas.exe` con PyInstaller.

## Recomendación

Compila **en Windows 10 u 11**. Aunque el código Python puede desarrollarse en
otros sistemas, el ejecutable final debe generarse en Windows para maximizar
la compatibilidad.

## Pruebas rápidas en Windows (sync + build + run)

Si desarrollas en WSL y pruebas el `.exe` en Windows, usa este flujo:

1. En WSL: integra el trabajo en `development` y, cuando esté **aprobado para
   producción**, fusiona a `main` (solo con autorización expresa). El script
   de sync descarga la rama **`main`** (versión estable).
2. En Windows (PowerShell):

```powershell
Set-Location C:\Dev\SeparadorNominas
.\scripts\sync-build-run.ps1
```

El script:

1. Actualiza el código desde GitHub (`main` estable), con Git o descarga ZIP.
2. Ejecuta `scripts\build.ps1` (tests + PyInstaller).
3. Abre `dist\SeparadorNominas.exe`.

El desarrollo diario de features se hace en ramas desde `development`
(ver [`CONTRIBUTING.md`](../CONTRIBUTING.md)). `sync-build-run.ps1` no sustituye
ese flujo: sirve para probar el **estable** en Windows.

Parámetros útiles:

```powershell
.\scripts\sync-build-run.ps1 -NoLaunch      # solo sync + build
.\scripts\sync-build-run.ps1 -SkipBuild     # sync + abrir exe existente
.\scripts\sync-build-run.ps1 -RepoDir C:\Dev\SeparadorNominas
```

Primera instalación en `C:\Dev` (si aún no tienes la carpeta): clona o descarga el
ZIP del repositorio en `C:\Dev\SeparadorNominas` y ejecuta el script anterior.

## 1. Instalar Python

1. Descarga Python 3.11 o superior desde [python.org](https://www.python.org/).
2. Durante la instalación, marca **Add python.exe to PATH**.
3. Verifica:

```powershell
python --version
```

## 2. Crear el entorno virtual

Desde la raíz del proyecto:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Si PowerShell bloquea la activación:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

## 3. Instalar dependencias

```powershell
pip install --upgrade pip
pip install -r requirements-dev.txt
pip install -e .
```

## 4. Compilar con el script

```powershell
.\scripts\build.ps1
```

El script:

1. Prepara el entorno.
2. Ejecuta los tests.
3. Detiene la compilación si fallan.
4. Limpia `build/` y `dist/`.
5. Lanza PyInstaller en modo `--onefile --windowed`.

## 5. Compilación manual (alternativa)

```powershell
pyinstaller `
  --noconfirm `
  --clean `
  --onefile `
  --windowed `
  --name SeparadorNominas `
  --paths src `
  src\separador_nominas\main.py
```

Con icono personalizado:

```powershell
pyinstaller `
  --noconfirm `
  --clean `
  --onefile `
  --windowed `
  --name SeparadorNominas `
  --icon assets\icon.ico `
  --paths src `
  src\separador_nominas\main.py
```

## 6. Ubicación del ejecutable

```text
dist\
└── SeparadorNominas.exe
```

Características del ejecutable:

- No abre consola adicional (`--windowed` / `--noconsole`).
- Incluye dependencias necesarias.
- Muestra la interfaz gráfica al abrirse.

## 7. Icono

Si no existe `assets/icon.ico`, se usa el icono estándar.

Para añadirlo más adelante, coloca el `.ico` en `assets/` y vuelve a compilar.
Consulta `assets/README.md`.

## 8. Avisos de Windows Defender

Es habitual que Windows marque como desconocidos los `.exe` no firmados
generados con PyInstaller.

Opciones:

- Firmar digitalmente el ejecutable (recomendado en distribución interna).
- Distribuir el `.exe` por canales de confianza de la organización.
- Añadir una exclusión controlada solo si la política de seguridad lo permite.

## 9. Compatibilidad

- Objetivo: Windows 10 y Windows 11.
- Compilar en una máquina alineada con el entorno de destino.
- Probar al menos en un Windows 10 y un Windows 11 antes de distribuir.

## 10. Limitaciones

- El `.exe` monofichero puede tardar un instante en arrancar (extracción
  temporal de PyInstaller).
- Sin firma digital, algunos antivirus pueden mostrar avisos.
- No se genera instalador MSI/Setup en la versión 1.0.0.
