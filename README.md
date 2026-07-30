# Separador de Nóminas PDF

Miniaplicación de escritorio para **Windows 10 y Windows 11** que separa un
archivo PDF multipágina de nóminas: **una página por archivo**, **agrupación
por trabajador** o **clasificación en grupos** (DNI/NIE + departamentos).

**Versión actual: 2.0.0** (clasificación por grupos / DNI-NIE; Excel departamentos hacia 2.5.0)

## Para agentes de IA

Si eres un asistente o agente que abre este repositorio, empieza por
**[`AGENTS.md`](AGENTS.md)**: describe el propósito, el alcance, el roadmap, la
arquitectura/privacidad y el **flujo Git obligatorio**. También hay reglas en
[`.cursor/rules/`](.cursor/rules/) para Cursor.

## Contribuir / flujo Git

- `main`: solo versiones estables.
- `development`: integración y pruebas.
- Cada tarea: rama hija de `development` (`feature/…`, `fix/…`, etc.).
- Merges, tags y pushes: solo con autorización expresa.

Detalle: [`CONTRIBUTING.md`](CONTRIBUTING.md).

## Problema que resuelve

La asesoría suele entregar un único PDF donde cada página es la nómina de un
trabajador. Separar esas páginas a mano es lento y propenso a errores.

Esta aplicación permite:

1. Abrir el PDF completo.
2. Elegir una carpeta de destino.
3. Separar una página por archivo, reconocer y agrupar por trabajador,
   clasificar en grupos (DNI/NIE) **o** clasificar automáticamente mediante Excel.

Todo el proceso se ejecuta **en local**, sin subir archivos ni datos a Internet.

## Funciones de la versión 2.0.0

- Modo **Clasificar trabajadores en grupos** (sesión solo en memoria).
- Detección de DNI/NIE, grupos/reglas, exportación separada o conjunta.
- UX: selección con fondo azul, pasos 1–7, confirmación al reanalizar,
  modal al añadir que indica el grupo.
- Guía: [`docs/CLASIFICACION_NOMINAS.md`](docs/CLASIFICACION_NOMINAS.md).

## Funciones de la versión 1.1.0

- Todo lo de la 1.0.x (separación página a página).
- Modo **Reconocer y agrupar por trabajador** (texto seleccionable, sin OCR).
- Resumen y confirmación antes de guardar los PDF agrupados.
- Un PDF por trabajador; páginas no reconocidas en `No_reconocidas/`.
- Protección frente a sobrescritura accidental de archivos.

## Funciones de la versión 1.0.0

- Selección de un archivo PDF de origen.
- Selección de carpeta de destino.
- Nombre base editable para los archivos generados.
- Separación de una página por archivo (sin rasterizar).
- Numeración automática con ceros a la izquierda según el total de páginas.
- Barra de progreso y mensajes de estado en español.
- Aviso al finalizar y botón para abrir la carpeta de destino.
- Validaciones y mensajes de error comprensibles.

## Esquema de la interfaz

```text
┌──────────────────────────────────────────────────────────┐
│  Separador de Nóminas PDF                                │
├──────────────────────────────────────────────────────────┤
│  Archivo de origen                                       │
│  [ C:\...\Nominas_Julio_2026.pdf          ] [Seleccionar]│
├──────────────────────────────────────────────────────────┤
│  Carpeta de destino                                      │
│  [ C:\...\Nominas_Julio_2026_separadas    ] [Seleccionar]│
├──────────────────────────────────────────────────────────┤
│  Modo: (•) Separar una página / ( ) Agrupar trabajador   │
├──────────────────────────────────────────────────────────┤
│  Nombre base (solo modo separación)                      │
│  [ Nominas_Julio_2026                                    ]│
├──────────────────────────────────────────────────────────┤
│  [ Separar / Reconocer y agrupar ]                       │
│  [████████████░░░░░░░░░░░░]                              │
│  Analizando página 4 de 18...                            │
├──────────────────────────────────────────────────────────┤
│  Resultado / resumen de reconocimiento                   │
│  [ Abrir carpeta de destino ]                            │
└──────────────────────────────────────────────────────────┘
```

## Requisitos para desarrollo

- Windows 10/11 (recomendado para ejecución y compilación del `.exe`).
- Python **3.11** o superior.
- PowerShell 5.1 o superior (para los scripts de `scripts/`).

## Instalación

```powershell
cd SeparadorNominas
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
pip install -e .
```

O bien:

```powershell
.\scripts\run.ps1
```

## Ejecución

```powershell
.\scripts\run.ps1
```

Alternativa manual:

```powershell
.\.venv\Scripts\Activate.ps1
python -m separador_nominas.main
```

## Ejecución de tests

```powershell
.\scripts\test.ps1
```

O manualmente:

```powershell
pytest --cov=separador_nominas --cov-report=term-missing
```

Herramientas de calidad (opcionales):

```powershell
ruff check src tests
mypy
```

## Compilación del `.exe`

En Windows:

```powershell
.\scripts\build.ps1
```

Para **actualizar desde GitHub, recompilar y abrir** la app (útil si desarrollas
en WSL y pruebas en Windows):

```powershell
Set-Location C:\Dev\SeparadorNominas
.\scripts\sync-build-run.ps1
```

Resultado esperado:

```text
dist/
└── SeparadorNominas.exe
```

Detalles en [docs/COMPILACION_WINDOWS.md](docs/COMPILACION_WINDOWS.md).

## Estructura del proyecto

```text
SeparadorNominas/
├── AGENTS.md                # Briefing para IAs / agentes
├── CONTRIBUTING.md          # Flujo Git y contribución
├── .cursor/rules/           # Reglas Cursor (contexto persistente)
├── src/separador_nominas/   # Código de la aplicación
├── tests/                   # Tests unitarios
├── assets/                  # Recursos (icono opcional)
├── docs/                    # Documentación (incluye ROADMAP)
├── scripts/                 # Scripts PowerShell
├── requirements.txt
├── requirements-dev.txt
├── pyproject.toml
├── VERSION
└── README.md
```

## Seguridad y privacidad

- Procesamiento 100 % local.
- Sin telemetría ni conexiones externas.
- Sin almacenamiento del contenido de las nóminas en logs.
- El usuario es responsable del tratamiento conforme a la normativa de
  protección de datos aplicable (RGPD y normativa local).

Más detalle en [docs/SEGURIDAD_Y_PRIVACIDAD.md](docs/SEGURIDAD_Y_PRIVACIDAD.md).

## Aviso de protección de datos

Este repositorio público contiene **únicamente código fuente y documentación**.
**No incluye nóminas reales ni otros datos personales.**

La aplicación puede usarse para procesar documentos laborales sensibles en el
equipo del usuario. Quien la utilice con ficheros reales actúa como
responsable (o encargado, según el caso) del tratamiento y debe cumplir el
**RGPD** y la **LOPDGDD** (España), así como cualquier normativa aplicable.

La licencia MIT regula el uso del software; **no sustituye** las obligaciones
de protección de datos. Consulta
[docs/SEGURIDAD_Y_PRIVACIDAD.md](docs/SEGURIDAD_Y_PRIVACIDAD.md).

## Limitaciones actuales

- No realiza OCR (PDFs escaneados no permiten reconocer el nombre).
- No usa fuzzy matching: solo clave de nombre normalizada exacta.
- No incluye editor interactivo de coincidencias.
- No envía correos ni se integra con Outlook / Microsoft 365.
- No incluye instalador ni firma digital del ejecutable.

## Roadmap resumido

| Versión | Objetivo |
|---------|----------|
| 1.1.0   | Reconocimiento y agrupación por trabajador (**implementada**) |
| 2.0.0   | Clasificación por grupos / DNI-NIE (**implementada**) |
| 2.5.0   | Clasificación automática mediante Excel (**en desarrollo**) |
| 2.1.0+  | Asociación trabajador ↔ correo (CSV/Excel) |
| 3.0.0   | Borradores de correo con Outlook / Microsoft 365 |

Detalle completo en [docs/ROADMAP.md](docs/ROADMAP.md).

## Licencia

Distribuido bajo licencia **MIT**. Consulta el archivo [LICENSE](LICENSE).

Copyright (c) 2026 Antonio Zurano Blázquez.

El software se proporciona «tal cual» (*as is*), sin garantías. Este
repositorio **no incluye datos personales**. Si utilizas la aplicación con
nóminas u otros documentos con datos personales, eres responsable de su
tratamiento conforme al **RGPD** y la **LOPDGDD**, y a cualquier otra
normativa aplicable. La licencia MIT no exime de esas obligaciones.

## Versión actual

`2.0.0` — ver [VERSION](VERSION) y [CHANGELOG.md](CHANGELOG.md).
