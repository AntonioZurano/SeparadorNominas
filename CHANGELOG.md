# Changelog

Todas las modificaciones relevantes de este proyecto se documentan en este archivo.

El formato está inspirado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/),
y este proyecto adhiere a [Versionado Semántico](https://semver.org/lang/es/).

## [Unreleased]

### Añadido

- Documentación del flujo Git (`main` / `development` / ramas de trabajo):
  `AGENTS.md`, `CONTRIBUTING.md`, `.cursor/rules/git-workflow.mdc`.
- Script `scripts/sync-build-run.ps1` para sincronizar desde GitHub, recompilar
  el `.exe` y abrir la aplicación en Windows.

### Cambiado

- Creación de entorno virtual en scripts PowerShell: fallback robusto a
  `python` cuando no existe el launcher `py`.
- Titular de la licencia MIT: Antonio Zurano Blázquez.
- Avisos RGPD/LOPDGDD en README y documentación de seguridad.
- `.gitignore` ampliado (documentos de oficina y credenciales).

## [1.1.0] - 2026-07-26

### Añadido

- Extracción local de texto de páginas PDF (`text_extraction_service`).
- Reconocimiento de nombre de trabajador por reglas/etiquetas locales
  (sin OCR, sin servicios externos, sin fuzzy matching).
- Normalización de nombres (`display` / clave de agrupación / nombre de archivo).
- Agrupación exacta por clave normalizada y escritura de un PDF por trabajador.
- Carpeta `No_reconocidas/` con un PDF por página no reconocida.
- Modo GUI «Reconocer y agrupar por trabajador» con resumen y confirmación
  antes de guardar.
- Progreso visible al crear PDF agrupados (barra + «Creando archivo i de n...»).
- Apertura de carpeta de destino desde WSL mediante el Explorador de Windows.
- Tests sintéticos (reportlab solo en dependencias de desarrollo).

### Conservado

- Modo «Separar una página por archivo» de la 1.0.x sin cambios de comportamiento.

## [1.0.1] - 2026-07-26

### Añadido

- `AGENTS.md` y reglas en `.cursor/rules/` para que agentes de IA comprendan
  el propósito, la arquitectura y el roadmap al abrir el proyecto.
- `docs/CONTEXTO_IA.md` como puntero al briefing para agentes.

## [1.0.0] - 2026-07-26

### Añadido

- Interfaz gráfica para seleccionar un PDF.
- Selección de carpeta de destino.
- Separación de una página por archivo.
- Numeración automática.
- Barra de progreso.
- Apertura de carpeta de destino.
- Validaciones y mensajes de error.
- Tests unitarios.
- Documentación técnica y de usuario.
- Compilación para Windows mediante PyInstaller.
