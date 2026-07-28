# Changelog

Todas las modificaciones relevantes de este proyecto se documentan en este archivo.

El formato está inspirado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/),
y este proyecto adhiere a [Versionado Semántico](https://semver.org/lang/es/).

## [Unreleased]

## [2.0.0] - 2026-07-28

### Añadido

- Modo **Clasificar trabajadores en grupos**: detección DNI/NIE, consolidación
  por documento, grupos en memoria, exportación separada o conjunta, UI de
  dos paneles.
- Módulos: `document_identifier_service`, `worker_recognition_service`,
  `classification_models`, `classification_service`, `group_export_service`,
  `session_service`, `temporary_files_service`, `classification_view`.
- Documentación: `docs/CLASIFICACION_NOMINAS.md`; checklist de pruebas UI
  `docs/PRUEBAS_UI.md`; roadmap reordenado (2.0 = clasificación; correo → 3.0).
- Tests unitarios e integración de clasificación (PDFs sintéticos).
- Script `scripts/generate_synthetic_classification_pdf.py` para generar un
  PDF sintético de 1500 páginas con casos de clasificación (salida en
  `pruebas/`, PDFs ignorados por Git).
- Documentación del flujo Git (`main` / `development` / ramas de trabajo):
  `AGENTS.md`, `CONTRIBUTING.md`, `.cursor/rules/git-workflow.mdc`.
- Script `scripts/sync-build-run.ps1` para sincronizar desde GitHub, recompilar
  el `.exe` y abrir la aplicación en Windows.

### Corregido

- **Selección visual en clasificación:** las filas seleccionadas se resaltan
  con fondo azul (Treeview nativo). «Seleccionar todos» / «Deseleccionar
  todos» y Ctrl+A actualizan esa selección; el contador muestra
  «Seleccionados: N».
- **Añadir / quitar del grupo:** solo actúan sobre las filas con fondo azul
  (selección visible), no sobre un set oculto.
- **Reanalizar con sesión activa:** modal de aviso si hay grupos o
  trabajadores en memoria; los PDF se escriben con «Generar», no al reanalizar.
- **Pasos numerados (modo clasificar):** botones 1–7 y texto de ayuda con el
  orden sugerido.
- **Modal al añadir trabajadores:** indica el/los nombre(s) y el **grupo de
  destino**.
- **Botón Generar tras el aviso de reanálisis:** se restaura si se cancela el
  modal; tras reanalizar, vuelve a mostrarse al terminar.

### Cambiado

- `VERSION` / `APP_VERSION` / `pyproject.toml` → **2.0.0**.
- Creación de entorno virtual en scripts PowerShell: fallback robusto a
  `python` cuando no existe el launcher `py`.
- Titular de la licencia MIT: Antonio Zurano Blázquez.
- Avisos RGPD/LOPDGDD en README y documentación de seguridad.
- `.gitignore` ampliado (documentos de oficina y credenciales).
- Roadmap: la v2.0.0 es clasificación por grupos; Outlook/correo a 3.0.0.

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
- Filtro negativo por tokens (evita rechazar apellidos como «Nieto» por «NIE»).
- Área Resultado con barra de desplazamiento para resúmenes largos.
- Feedback al abrir PDF grandes: validación en segundo plano con barra
  indeterminada («Abriendo y validando el PDF...»).
- Confirmación de escritura embebida (Generar/Cancelar junto a la barra)
  sin diálogo modal, para poder revisar el resumen con scroll.
- Sin diálogo final en modo agrupar: el resumen queda solo en Resultado.
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
