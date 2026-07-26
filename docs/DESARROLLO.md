# Guía de desarrollo

## Preparación del entorno

Requisitos:

- Python 3.11+
- Git
- PowerShell (en Windows)

```powershell
git clone <url-del-repositorio>
cd SeparadorNominas
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
pip install -e .
```

Comprobar arranque:

```powershell
python -m separador_nominas.main
```

## Estructura del código

```text
src/separador_nominas/
├── main.py              # Entrada
├── gui.py               # Interfaz
├── pdf_service.py       # Separación PDF
├── filename_service.py  # Nombres y rutas
├── validators.py        # Validaciones
├── exceptions.py        # Errores de dominio
└── constants.py         # Constantes
```

Los tests viven en `tests/` y no deben depender de la GUI.

## Convenciones

- PEP 8 + `ruff`.
- Type hints en APIs públicas.
- Docstrings en módulos, clases y funciones públicas.
- Mensajes de usuario en español.
- Sin dependencias innecesarias.
- Sin guardar contenido de nóminas en logs.

Ejecutar lint y tipos:

```powershell
ruff check src tests
ruff format src tests
mypy
```

## Cómo añadir funciones

1. Decide si pertenece a GUI, servicio o validador.
2. Implementa la lógica sin acoplarla a Tkinter.
3. Añade tests en `tests/`.
4. Actualiza documentación afectada.
5. Anota el cambio en `CHANGELOG.md`.
6. Si cambia la versión, actualiza `VERSION` y `pyproject.toml`.

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

1. Acuerda el tipo de cambio (MAJOR.MINOR.PATCH).
2. Actualiza:
   - `VERSION`
   - `pyproject.toml` → `project.version`
   - `constants.APP_VERSION` (si se mantiene sincronizado)
   - `CHANGELOG.md`
3. Crea rama `release/X.Y.Z` cuando proceda.

## Scripts útiles

| Script | Uso |
|--------|-----|
| `scripts/run.ps1` | Entorno + ejecución |
| `scripts/test.ps1` | Tests + cobertura |
| `scripts/build.ps1` | Tests + PyInstaller |
