# Roadmap

Estado actual: **versión 1.1.0** (estable). La clasificación por grupos se
desarrolla como objetivo **2.0.0** en rama de feature hasta merge autorizado.

Las versiones siguientes están **expresamente no implementadas** en `main`
hasta su integración.

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

## Versión 2.0.0 (en desarrollo — clasificación por grupos)

- Detectar DNI/NIE y nombre; consolidar páginas por documento.
- Pantalla de clasificación (grupos ↔ trabajadores).
- Asignación manual a grupos/reglas (multi-asignación permitida).
- Exportación por grupo: un PDF por trabajador o un PDF conjunto.
- Sesión solo en memoria; sin persistencia de datos personales.
- Conservar los modos de separación y agrupación por nombre de 1.0/1.1.

Detalle: [`CLASIFICACION_NOMINAS.md`](CLASIFICACION_NOMINAS.md).

## Versión 2.1.0 / posterior (no implementada — listados)

Antes: roadmap 1.2.0. Aplazada tras priorizar la clasificación.

- Importar listado CSV o Excel de trabajadores.
- Asociar trabajador y correo electrónico.
- Validar trabajadores sin correo.
- Generar informe de coincidencias.

## Versión 3.0.0 (no implementada — correo)

Antes: roadmap 2.0.0 (Outlook). Reordenada al priorizar clasificación.

- Crear borradores de correo.
- Integración segura con Outlook o Microsoft 365.
- Adjuntar la nómina correspondiente.
- Revisión manual antes del envío.
- Registro de envíos sin almacenar datos salariales.

## Posibles mejoras (no implementadas)

- OCR local para PDFs escaneados.
- Orden manual o alfabético en PDF conjunto.
- Firma digital del ejecutable.
- Instalador para Windows.
- Actualizaciones controladas.
- Protección mediante contraseña.
- Cifrado opcional de archivos.
- Soporte multidioma.
- Revisión manual editable de nombres detectados.

## Principios de evolución

- Conservar la arquitectura modular.
- No romper la separación PDF de la v1.0.0 ni la agrupación por nombre 1.1.0.
- Añadir tests y documentación con cada cambio.
- Versionar de forma semántica (`VERSION` + `CHANGELOG.md`) **cuando se ordene**.
- Mantener el procesamiento local y la privacidad como requisito no negociable.
- Integrar cada versión del roadmap mediante el flujo Git
  (`development` → pruebas → `main`); ver [`CONTRIBUTING.md`](../CONTRIBUTING.md).
- No implementar ítems del roadmap sin petición explícita.
