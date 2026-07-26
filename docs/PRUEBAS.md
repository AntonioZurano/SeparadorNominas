# Pruebas

## Estrategia de testing

La versión 1.1.0 prioriza tests unitarios e integración sintética de la lógica:

- generación de nombres;
- validaciones;
- separación de PDF;
- extracción de texto;
- normalización y reconocimiento;
- agrupación y escritura agrupada.

Los tests de interfaz gráfica no son obligatorios en esta versión.

## Qué módulos se prueban

| Módulo | Archivo de test |
|--------|-----------------|
| `filename_service.py` | `tests/test_filename_service.py` |
| `validators.py` | `tests/test_validators.py` |
| `pdf_service.py` | `tests/test_pdf_service.py` |
| `text_extraction_service.py` | `tests/test_text_extraction_service.py` |
| `name_normalization.py` | `tests/test_name_normalization.py` |
| `employee_name_service.py` | `tests/test_employee_name_service.py` |
| `grouping_service.py` | `tests/test_grouping_service.py` |
| `grouped_pdf_service.py` | `tests/test_grouped_pdf_service.py` |

Coberturas clave:

- numeración y dígitos;
- caracteres inválidos de Windows;
- rutas alternativas ante colisiones;
- PDF de 1 y N páginas;
- PDF corrupto o inexistente;
- creación de carpeta de destino;
- un archivo de salida = una página (modo separación);
- agrupación por clave exacta y carpeta `No_reconocidas/`.

## Qué no se prueba todavía

- Interacciones completas de Tkinter.
- Diálogos nativos del sistema.
- Empaquetado PyInstaller de extremo a extremo en CI.
- PDFs protegidos con contraseña reales (se contemplan por código).

## Ejecución de pytest

```powershell
.\scripts\test.ps1
```

O:

```powershell
pytest --cov=separador_nominas --cov-report=term-missing
```

## Cobertura

La configuración en `pyproject.toml` mide cobertura del paquete
`separador_nominas`, omitiendo `gui.py` y `main.py` (acoplados a la UI /
arranque).

## Uso de archivos temporales

Los tests generan PDF sintéticos en carpetas temporales de pytest.
**No** se versionan nóminas reales. Para texto embebido se usa `reportlab`
solo como dependencia de desarrollo (`requirements-dev.txt`).
