# Guía de desarrollo

## Preparación del entorno

Requisitos:

- Python 3.11+
- Git
- PowerShell (en Windows)

```powershell
git clone https://github.com/AntonioZurano/SeparadorNominas.git
cd SeparadorNominas
git switch development
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
pip install -e .
```

Comprobar arranque:

```powershell
python -m separador_nominas.main
```

## Flujo Git

El desarrollo usa `main` (estable) y `development` (integración). Toda tarea
se hace en una rama hija de `development`.

- Instrucciones para humanos: [`CONTRIBUTING.md`](../CONTRIBUTING.md)
- Instrucciones para IAs: [`AGENTS.md`](../AGENTS.md)

Las ramas `release/*` son legado; no las uses para trabajo nuevo.

## Estructura del código

```text
src/separador_nominas/
├── main.py
├── gui.py
├── pdf_service.py
├── text_extraction_service.py
├── recognition_rules.py
├── employee_name_service.py
├── name_normalization.py
├── grouping_service.py
├── grouped_pdf_service.py
├── recognition_models.py
├── filename_service.py
├── validators.py
├── exceptions.py
└── constants.py
```

Los tests viven en `tests/` y no deben depender de la GUI.

## Convenciones

- PEP 8 + `ruff`.
- Type hints en APIs públicas.
- Docstrings en módulos, clases y funciones públicas.
- Mensajes de usuario en español.
- Sin dependencias innecesarias (runtime: `pypdf`, `openpyxl`, `xlrd==1.2.0`).
- Sin guardar contenido de nóminas ni DNI/departamentos en logs.

Ejecutar lint y tipos:

```powershell
ruff check src tests
ruff format src tests
mypy
```

## Cómo añadir funciones

1. Crea una rama desde `development` (p. ej. `feature/mi-cambio`).
2. Decide si el cambio pertenece a GUI, servicio o validador.
3. Implementa la lógica sin acoplarla a Tkinter.
4. Añade tests en `tests/`.
5. Actualiza documentación afectada.
6. Anota el cambio en `CHANGELOG.md` (Unreleased).
7. Ejecuta tests; **no** hagas merge/push/tag sin autorización.

## Cómo depurar

- Ejecuta desde consola (`python -m separador_nominas.main`) para ver logs.
- Los logs no deben incluir texto de nóminas.
- Reproduce fallos de PDF con archivos sintéticos en `tmp_path` (tests).
- Para problemas de UI, verifica que las actualizaciones usen `root.after`.

## Cómo actualizar dependencias

1. Actualiza versiones en `requirements.txt` / `requirements-dev.txt`.
2. Refleja el cambio en `pyproject.toml` si aplica.
3. Ejecuta tests.
4. Prueba la compilación en Windows.

## Cómo aumentar la versión

Solo cuando el responsable lo indique expresamente:

1. Acuerda el tipo de cambio (`MAJOR.MINOR.PATCH` o sufijo `-dev.N` / `-rc.N`).
2. Actualiza:
   - `VERSION`
   - `pyproject.toml` → `project.version`
   - `constants.APP_VERSION` (si se mantiene sincronizado)
   - `CHANGELOG.md`
3. Integra vía `development` → `main` y crea la tag **solo si se ordena**.

Detalle: [`CONTRIBUTING.md`](../CONTRIBUTING.md).

## Scripts útiles

| Script | Uso |
|--------|-----|
| `scripts/run.ps1` | Entorno + ejecución |
| `scripts/test.ps1` | Tests + cobertura |
| `scripts/build.ps1` | Tests + PyInstaller |
| `scripts/sync-build-run.ps1` | Sync `main` estable + build + abrir (Windows) |
