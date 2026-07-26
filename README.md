# Separador de Nóminas PDF

Miniaplicación de escritorio para **Windows 10 y Windows 11** que separa un
archivo PDF multipágina en un PDF independiente por cada página.

**Versión actual: 1.0.1**

## Para agentes de IA

Si eres un asistente o agente que abre este repositorio, empieza por
**[`AGENTS.md`](AGENTS.md)**: describe el propósito, el alcance de la 1.0.0, el
roadmap (qué no está implementado) y las reglas de arquitectura/privacidad.
También hay reglas en [`.cursor/rules/`](.cursor/rules/) para Cursor.

## Problema que resuelve

La asesoría suele entregar un único PDF donde cada página es la nómina de un
trabajador. Separar esas páginas a mano es lento y propenso a errores.

Esta aplicación permite:

1. Abrir el PDF completo.
2. Elegir una carpeta de destino.
3. Generar automáticamente un archivo por página.

Todo el proceso se ejecuta **en local**, sin subir archivos ni datos a Internet.

## Funciones de la versión 1.0.0

- Selección de un archivo PDF de origen.
- Selección de carpeta de destino.
- Nombre base editable para los archivos generados.
- Separación de una página por archivo (sin rasterizar).
- Numeración automática con ceros a la izquierda según el total de páginas.
- Barra de progreso y mensajes de estado en español.
- Aviso al finalizar y botón para abrir la carpeta de destino.
- Protección frente a sobrescritura accidental de archivos.
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
│  Nombre base de los archivos                             │
│  [ Nominas_Julio_2026                                    ]│
├──────────────────────────────────────────────────────────┤
│  [ Separar nóminas ]                                     │
│  [████████████░░░░░░░░░░░░]                              │
│  Procesando página 4 de 18...                            │
├──────────────────────────────────────────────────────────┤
│  Resultado                                               │
│  Se han generado 18 archivos.                            │
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

- No realiza OCR.
- No detecta automáticamente el nombre del trabajador.
- No envía correos ni se integra con Outlook / Microsoft 365.
- No incluye instalador ni firma digital del ejecutable.
- Pensada para PDFs con texto o contenido vectorial; los escaneados se
  separan página a página, pero sin reconocimiento de texto.

## Roadmap resumido

| Versión | Objetivo |
|---------|----------|
| 1.1.0   | Detección de nombre del trabajador y renombrado |
| 1.2.0   | Asociación trabajador ↔ correo (CSV/Excel) |
| 2.0.0   | Borradores de correo con Outlook / Microsoft 365 |

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

`1.0.1` — ver [VERSION](VERSION) y [CHANGELOG.md](CHANGELOG.md).
