# Roadmap

Estado actual: **versión 1.1.0** (en rama de feature hasta merge autorizado).

La funcionalidad de separación PDF corresponde a la **1.0.0**.
La **1.0.1** añade documentación orientada a agentes de IA.
La **1.1.0** añade reconocimiento local de texto y agrupación por trabajador.

Las versiones siguientes están **expresamente no implementadas**.

## Versión 1.0.1 (implementada)

- `AGENTS.md` y contexto para agentes de IA.
- Reglas Cursor en `.cursor/rules/`.
- `docs/CONTEXTO_IA.md`.

## Versión 1.1.0 (implementada)

- Extraer texto seleccionable de cada página (pypdf, sin OCR).
- Reconocer el nombre del trabajador mediante reglas locales (etiquetas).
- Agrupar páginas por nombre normalizado exacto.
- Generar un PDF por trabajador; páginas no reconocidas en `No_reconocidas/`.
- Resumen y confirmación antes de escribir archivos.
- Conservar el modo «una página por archivo» de la 1.0.0.

Fuera de 1.1.0 (siguen pendientes): OCR, editor interactivo de coincidencias,
DNI como clave, fuzzy matching.

## Versión 1.2.0 (no implementada)

- Importar listado CSV o Excel de trabajadores.
- Asociar trabajador y correo electrónico.
- Validar trabajadores sin correo.
- Generar informe de coincidencias.

## Versión 2.0.0 (no implementada)

- Crear borradores de correo.
- Integración segura con Outlook o Microsoft 365.
- Adjuntar la nómina correspondiente.
- Revisión manual antes del envío.
- Registro de envíos sin almacenar datos salariales.

## Posibles mejoras (no implementadas)

- OCR local para PDFs escaneados.
- Firma digital del ejecutable.
- Instalador para Windows.
- Actualizaciones controladas.
- Protección mediante contraseña.
- Cifrado opcional de archivos.
- Soporte multidioma.
- Revisión manual editable de nombres detectados.

## Principios de evolución

- Conservar la arquitectura modular.
- No romper la separación PDF de la v1.0.0.
- Añadir tests y documentación con cada cambio.
- Versionar de forma semántica (`VERSION` + `CHANGELOG.md`) **cuando se ordene**.
- Mantener el procesamiento local y la privacidad como requisito no negociable.
- Integrar cada versión del roadmap mediante el flujo Git
  (`development` → pruebas → `main`); ver [`CONTRIBUTING.md`](../CONTRIBUTING.md).
- No implementar ítems del roadmap sin petición explícita.
