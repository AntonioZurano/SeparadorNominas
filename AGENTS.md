# AGENTS.md — Contexto para agentes de IA

Documento de arranque para **Cursor y cualquier otra IA** que abra este
repositorio. Léelo **antes** de modificar código, proponer funciones o tocar Git.

Detalle humano del flujo Git: [`CONTRIBUTING.md`](CONTRIBUTING.md).
Entorno y convenciones de código: [`docs/DESARROLLO.md`](docs/DESARROLLO.md).

## Qué es este proyecto

**SeparadorNominas** (`Separador de Nóminas PDF`) es una miniaplicación de
escritorio para **Windows 10/11** que separa un PDF multipágina de nóminas:
modo **una página por archivo**, **reconocer y agrupar por trabajador**, o
**clasificar trabajadores en grupos** (DNI/NIE + departamentos/reglas).

Caso de uso:

1. La asesoría entrega un único PDF.
2. Cada página es la nómina de un trabajador (a veces varias del mismo).
3. El usuario elige el PDF, la carpeta de destino y el modo de proceso.
4. La app genera archivos individuales o agrupados **sin subir nada a Internet**.

**Versión actual:** `2.5.0-beta.1` en preparación (ver `VERSION`).
Estable en `main`: `2.0.0`.

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

## Alcance de la v1.0.0 / v1.0.1 (implementado)

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
- Docs + scripts PowerShell (`run` / `test` / `build` / `sync-build-run`).

## Alcance de la v1.1.0 (implementado)

- Extracción local de texto con pypdf (sin OCR).
- Reconocimiento de nombre por etiquetas/reglas locales.
- Agrupación exacta por clave normalizada (sin fuzzy).
- Un PDF por trabajador; `No_reconocidas/Pagina_XXX.pdf` para el resto.
- Modo GUI + resumen/confirmación antes de escribir.

## Alcance de la v2.0.0 (implementado)

- Detección y validación de DNI/NIE; consolidación por documento.
- Pantalla de clasificación (grupos ↔ trabajadores); sesión solo en memoria.
- Exportación por grupo: separado o conjunto; multi-asignación permitida.
- UX: selección azul, pasos 1–7, confirmación al reanalizar.
- Detalle: [`docs/CLASIFICACION_NOMINAS.md`](docs/CLASIFICACION_NOMINAS.md).

## Alcance de la v2.5.0 (beta en preparación)

- Clasificación automática mediante Excel (DNI/NIE → departamento).
- Lectura local `.xlsx` / `.xls`; grupos automáticos; `No_clasificadas/`.
- Código integrado en `development`; prerelease `2.5.0-beta.1` en rama
  `release/2.5.0-beta.1`.
- Detalle: [`docs/IMPORTACION_EXCEL.md`](docs/IMPORTACION_EXCEL.md).
- Pruebas beta: [`docs/PRUEBAS_BETA_2.5.0.md`](docs/PRUEBAS_BETA_2.5.0.md).

## Fuera de alcance (NO implementar sin petición explícita)

- OCR.
- Fuzzy matching entre nombres.
- Persistencia de grupos, DNI o listados entre sesiones.
- CSV/Excel de empleados **con correo** (roadmap 2.1+; distinto del Excel
  de departamentos de la 2.5.0).
- Envío de correos / Outlook / Microsoft 365.
- Base de datos, telemetría, APIs externas, cuentas en la nube.

Esas capacidades están en el roadmap como **no implementadas**.

## Roadmap (resumen)

Detalle: [`docs/ROADMAP.md`](docs/ROADMAP.md).

| Versión | Estado | Objetivo |
|---------|--------|----------|
| **1.0.0** | **Implementada** | Separar PDF página a página |
| **1.0.1** | **Implementada** | Documentación para agentes de IA |
| **1.1.0** | **Implementada** | Extraer texto, reconocer nombre, agrupar por trabajador |
| **2.0.0** | **Implementada** | Clasificación por grupos / DNI-NIE |
| **2.5.0** | Beta `2.5.0-beta.1` | Clasificación automática mediante Excel |
| **2.1.0+** | No implementada | CSV/Excel con correo, asociar trabajador↔correo |
| **3.0.0** | No implementada | Borradores de correo, Outlook/M365 |
| Mejoras | No implementadas | OCR local, firma del exe, instalador, cifrado, multidioma |

## Arquitectura (obligatoria)

Código en `src/separador_nominas/`:

| Módulo | Responsabilidad |
|--------|-----------------|
| `main.py` | Entrada + logging |
| `gui.py` | Solo UI (Tkinter) |
| `pdf_service.py` | Separación PDF (1 página → 1 archivo) |
| `text_extraction_service.py` | Extracción de texto local |
| `recognition_rules.py` / `employee_name_service.py` | Reglas y reconocimiento |
| `name_normalization.py` | Clave / display / nombre de archivo |
| `grouping_service.py` | Agrupación por clave exacta |
| `grouped_pdf_service.py` | Análisis + escritura agrupada |
| `recognition_models.py` | Dataclasses de reconocimiento |
| `document_identifier_service.py` | DNI/NIE: detectar, normalizar, validar |
| `worker_recognition_service.py` | Consolidar trabajadores + análisis clasificación |
| `classification_models.py` | Dataclasses de sesión / grupos / trabajadores |
| `classification_service.py` | CRUD de grupos y asignaciones en memoria |
| `group_export_service.py` | Exportación separada o conjunta por grupo |
| `session_service.py` / `temporary_files_service.py` | Sesión en memoria y limpieza |
| `classification_view.py` | UI del modo clasificación (Tkinter) |
| `spreadsheet_models.py` / `spreadsheet_service.py` | Importación Excel departamentos |
| `department_normalization.py` | Clave / carpeta de departamentos |
| `department_assignment_service.py` | Cruce Excel↔PDF y auto-grupos |
| `spreadsheet_import_view.py` | UI del modo Excel |
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

## Modelo de ramas (obligatorio)

```text
main                 # solo versiones estables
└── development      # integración y pruebas
    ├── feature/...
    ├── fix/...
    ├── refactor/...
    ├── docs/...
    └── test/...
```

- **`main`**: únicamente versiones estables. Nunca commits de trabajo directo.
- **`development`**: integración. No implementar la tarea directamente sobre ella.
- **Ramas de trabajo**: siempre creadas **desde `development`**, nunca desde `main`.
- Las ramas históricas `release/*` son **legado**; el flujo activo es el anterior.

## Flujo obligatorio para cualquier tarea

```text
1. Leer AGENTS.md y la documentación relevante.
2. Comprobar el estado de Git.
3. Cambiar a development.
4. Crear una rama de trabajo.
5. Implementar un cambio pequeño.
6. Añadir o actualizar tests.
7. Ejecutar las pruebas.
8. Actualizar documentación.
9. Mostrar resultados.
10. Esperar autorización antes de hacer merge.
```

Comandos orientativos:

```bash
git switch development
git status
git switch -c feature/nombre-de-la-feature
```

Antes de modificar archivos: explicar brevemente el alcance.

Desarrollo incremental: un alcance pequeño por rama; actualizar
`CHANGELOG.md` (Unreleased); detenerse tras probar. **No fusionar
automáticamente.**

## Integración (solo con orden expresa)

### Hacia `development`

Cuando el usuario apruebe integrar una rama:

1. Tests + lint disponibles en la rama de trabajo.
2. Working tree limpio.
3. `git switch development` y `git merge --no-ff <rama>` (sin squash salvo orden).
4. Volver a ejecutar tests.
5. Actualizar versión/tag **solo si el usuario lo indica**.
6. **No push** sin autorización.

### Hacia `main`

Solo cuando el usuario ordene una versión de producción:

1. Tests en `development`.
2. Changelog y versión documentados.
3. `git switch main` y `git merge --no-ff development`.
4. Tests de nuevo; tag estable solo si se ordena.
5. **No push** sin autorización.

### Tags

- Prueba en `development`: p. ej. `v2.0.0-dev.1`, `v2.0.0-rc.1` (proponer antes; no decidir solos).
- Estable en `main`: p. ej. `v2.0.0`.
- Versionado semántico `MAJOR.MINOR.PATCH`. No cambiar `VERSION` sin indicación expresa.

## Acciones prohibidas sin autorización

```text
- Merge a development.
- Merge a main.
- Crear tags.
- Hacer push.
- Eliminar ramas.
- Reescribir historial.
- Usar reset --hard.
- Usar force push.
- Modificar secretos o credenciales.
```

Tampoco: `git rebase` sin orden; eliminar archivos o comandos destructivos sin
autorización; implementar funciones del roadmap no pedidas.

## Commits

Pequeños, una responsabilidad. Conventional Commits (español), p. ej.:

```text
feat: añade vista previa de archivos
fix: corrige validación de PDF protegido
docs: documenta flujo de ramas
```

Antes de committear (si se solicita): informar archivos, tests, resultado y
mensaje propuesto. No commits automáticos no solicitados.

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
.\scripts\build.ps1
.\scripts\sync-build-run.ps1   # sync main estable + build + abrir
```

## Mapa de documentación

| Documento | Para qué |
|-----------|----------|
| `README.md` | Visión general humana |
| `AGENTS.md` | Este briefing para IAs (fuente de verdad) |
| `CONTRIBUTING.md` | Flujo Git y contribución |
| `docs/CONTEXTO_IA.md` | Puntero corto hacia AGENTS.md |
| `docs/ARQUITECTURA.md` | Módulos y diseño |
| `docs/FUNCIONAMIENTO.md` | Manual de usuario |
| `docs/DESARROLLO.md` | Entorno y convenciones de código |
| `docs/COMPILACION_WINDOWS.md` | PyInstaller / `.exe` |
| `docs/PRUEBAS.md` | Estrategia de tests |
| `docs/PRUEBAS_UI.md` | Checklist manual de GUI |
| `docs/SEGURIDAD_Y_PRIVACIDAD.md` | Datos sensibles |
| `docs/CLASIFICACION_NOMINAS.md` | Modo clasificación por grupos (v2.0) |
| `docs/IMPORTACION_EXCEL.md` | Clasificación automática mediante Excel (v2.5) |
| `docs/PRUEBAS_BETA_2.5.0.md` | Checklist manual de la beta 2.5 |
| `docs/INFORME_PRUEBAS_BETA.md` | Plantilla de informe de pruebas beta |
| `docs/PUBLICACION_GITHUB.md` | Preparación y publicación de Releases |
| `docs/ROADMAP.md` | Versiones futuras |
| `CHANGELOG.md` | Historial de cambios |

## Restricciones de privacidad (críticas)

- No incluir nóminas reales ni datos personales en el repo ni en tests.
- Generar PDFs sintéticos en tests (`tmp_path` + `pypdf`).
- No registrar nombres, DNI, salarios ni texto de nóminas en logs.
- No añadir telemetría ni conexiones externas en la lógica actual.
