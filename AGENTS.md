# AGENTS.md — Contexto para agentes de IA

Documento de arranque para cualquier IA o asistente que abra este repositorio.
Léelo **antes** de modificar código o proponer funciones nuevas.

## Qué es este proyecto

**SeparadorNominas** (`Separador de Nóminas PDF`) es una miniaplicación de
escritorio para **Windows 10/11** que separa un PDF multipágina en **un PDF por
página**.

Caso de uso:

1. La asesoría entrega un único PDF.
2. Cada página es la nómina de un trabajador.
3. El usuario elige el PDF, la carpeta de destino y un nombre base.
4. La app genera archivos individuales sin subir nada a Internet.

**Versión actual:** `1.0.1` (ver `VERSION`).

**Licencia:** MIT. Procesa documentos sensibles; el usuario es responsable del
tratamiento conforme a la normativa de protección de datos.

## Stack

| Pieza | Tecnología |
|-------|------------|
| Lenguaje | Python **≥ 3.11** |
| GUI | Tkinter |
| PDF | `pypdf` (sin rasterizar) |
| Tests | `pytest` + `pytest-cov` |
| Empaquetado | PyInstaller → `SeparadorNominas.exe` |
| Calidad | `ruff`, `mypy` |

Dependencias mínimas a propósito. No añadir librerías sin necesidad clara.

## Alcance de la v1.0.0 (implementado)

- Seleccionar PDF y carpeta de destino.
- Nombre base editable (sugerido desde el stem del PDF).
- Carpeta sugerida: `{stem}_separadas` junto al PDF.
- Un archivo PDF por página, calidad y texto seleccionable preservados.
- Numeración adaptativa: `1` / `01` / `001` según el total de páginas.
- Anti-sobrescritura: si existe `x_001.pdf` → `x_001_2.pdf`, etc.
- Progreso en UI (hilo + `after()`), mensajes en español.
- Abrir carpeta al terminar.
- Validaciones y excepciones de dominio.
- Tests de lógica (no GUI).
- Docs + scripts PowerShell (`run` / `test` / `build`).

## Fuera de alcance (NO implementar sin petición explícita)

- OCR.
- Detección automática de nombre/DNI del trabajador.
- CSV/Excel de empleados.
- Envío de correos / Outlook / Microsoft 365.
- Base de datos, telemetría, APIs externas, cuentas en la nube.

Esas capacidades están en el roadmap como **no implementadas**.

## Roadmap (resumen)

Detalle: [`docs/ROADMAP.md`](docs/ROADMAP.md).

| Versión | Estado | Objetivo |
|---------|--------|----------|
| **1.0.0** | **Implementada** | Separar PDF página a página |
| **1.0.1** | **Implementada** | Documentación para agentes de IA |
| **1.1.0** | No implementada | Extraer texto, detectar nombre, renombrar, vista previa/revisión |
| **1.2.0** | No implementada | CSV/Excel, asociar trabajador↔correo, informe de coincidencias |
| **2.0.0** | No implementada | Borradores de correo, Outlook/M365, revisión antes de enviar |
| Mejoras | No implementadas | OCR local, firma del exe, instalador, cifrado, multidioma |

## Arquitectura (obligatoria)

Código en `src/separador_nominas/`:

| Módulo | Responsabilidad |
|--------|-----------------|
| `main.py` | Entrada + logging |
| `gui.py` | Solo UI (Tkinter) |
| `pdf_service.py` | Separación PDF |
| `filename_service.py` | Nombres y rutas |
| `validators.py` | Validaciones |
| `exceptions.py` | Errores de dominio (mensajes en español) |
| `constants.py` | Constantes |

Reglas duras:

- **GUI ≠ lógica:** `gui.py` no manipula páginas; la lógica no importa Tkinter.
- Conservar arquitectura modular al ampliar.
- Tests en `tests/` para lógica nueva o cambiada.
- Mensajes de usuario en español, sin trazas técnicas ni datos personales.
- Procesamiento **100 % local**; sin red, sin telemetría, sin logs de contenido de nóminas.

Detalle: [`docs/ARQUITECTURA.md`](docs/ARQUITECTURA.md),
[`docs/SEGURIDAD_Y_PRIVACIDAD.md`](docs/SEGURIDAD_Y_PRIVACIDAD.md).

## Cómo evolucionar el proyecto

Antes de cada cambio:

1. Leer este archivo, `VERSION`, `CHANGELOG.md` y el código/docs afectados.
2. No romper la separación PDF de la 1.0.0.
3. No implementar requisitos no pedidos (sobre todo del roadmap futuro).
4. Añadir/actualizar tests.
5. Actualizar docs afectadas, `CHANGELOG.md` y, si aplica, `VERSION` + `pyproject.toml` + `constants.APP_VERSION`.
6. Explicar si se cambia la arquitectura.

Convención de ramas de release: `release/X.Y.Z`.

## Comandos útiles

```bash
# WSL / Linux (con .venv activo)
python -m separador_nominas.main
pytest -q
```

```powershell
# Windows
.\scripts\run.ps1
.\scripts\test.ps1
.\scripts\build.ps1   # → dist\SeparadorNominas.exe
```

## Mapa de documentación

| Documento | Para qué |
|-----------|----------|
| `README.md` | Visión general humana |
| `AGENTS.md` | Este briefing para IAs |
| `docs/CONTEXTO_IA.md` | Puntero corto hacia AGENTS.md |
| `docs/ARQUITECTURA.md` | Módulos y diseño |
| `docs/FUNCIONAMIENTO.md` | Manual de usuario |
| `docs/DESARROLLO.md` | Entorno y convenciones |
| `docs/COMPILACION_WINDOWS.md` | PyInstaller / `.exe` |
| `docs/PRUEBAS.md` | Estrategia de tests |
| `docs/SEGURIDAD_Y_PRIVACIDAD.md` | Datos sensibles |
| `docs/ROADMAP.md` | Versiones futuras |
| `CHANGELOG.md` | Historial de cambios |

## Restricciones de privacidad (críticas)

Al trabajar con este código:

- No incluir nóminas reales ni datos personales en el repo ni en tests.
- Generar PDFs sintéticos en tests (`tmp_path` + `pypdf`).
- No registrar nombres, DNI, salarios ni texto de nóminas en logs.
- No añadir telemetría ni conexiones externas en la lógica actual.
