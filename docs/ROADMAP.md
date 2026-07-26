# Roadmap

Estado actual: **versión 1.0.1**.

La funcionalidad de separación PDF corresponde a la **1.0.0**.
La **1.0.1** añade documentación orientada a agentes de IA.

Las versiones siguientes están **expresamente no implementadas**.

## Versión 1.0.1 (implementada)

- `AGENTS.md` y contexto para agentes de IA.
- Reglas Cursor en `.cursor/rules/`.
- `docs/CONTEXTO_IA.md`.

## Versión 1.1.0 (no implementada)

- Extraer texto de cada página.
- Detectar nombre del trabajador cuando el PDF contenga texto seleccionable.
- Renombrar automáticamente los archivos.
- Vista previa de nombres detectados.
- Revisión manual de coincidencias.

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

## Principios de evolución

- Conservar la arquitectura modular.
- No romper la separación PDF de la v1.0.0.
- Añadir tests y documentación con cada cambio.
- Versionar de forma semántica (`VERSION` + `CHANGELOG.md`).
- Mantener el procesamiento local y la privacidad como requisito no negociable.
