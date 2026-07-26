# Pruebas

## Estrategia de testing

La versión 1.0.0 prioriza tests unitarios de la lógica de negocio:

- generación de nombres;
- validaciones;
- separación de PDF.

Los tests de interfaz gráfica no son obligatorios en esta versión.

## Qué módulos se prueban

| Módulo | Archivo de test |
|--------|-----------------|
| `filename_service.py` | `tests/test_filename_service.py` |
| `validators.py` | `tests/test_validators.py` |
| `pdf_service.py` | `tests/test_pdf_service.py` |

Coberturas clave:

- numeración y dígitos;
- caracteres inválidos de Windows;
- rutas alternativas ante colisiones;
- PDF de 1 y N páginas;
- PDF corrupto o inexistente;
- creación de carpeta de destino;
- un archivo de salida = una página.

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

Objetivo de la v1.0.0: cobertura razonable de la lógica principal
(filename, validators, pdf_service).

## Uso de archivos temporales

Todos los PDF de prueba se generan en tiempo de ejecución con `pypdf` y
`tmp_path` de pytest.

**No se incluyen nóminas reales ni datos personales en el repositorio.**

## Cómo añadir nuevos tests

1. Crea o amplía un archivo en `tests/`.
2. Genera PDFs sintéticos (páginas en blanco) cuando haga falta.
3. Usa `tmp_path` para entradas/salidas.
4. Comprueba comportamientos y excepciones de dominio.
5. Ejecuta la batería completa antes de subir cambios.
