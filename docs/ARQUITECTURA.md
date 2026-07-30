# Arquitectura

## Visión general

`SeparadorNominas` separa la interfaz gráfica de la lógica de negocio para
facilitar pruebas, mantenimiento y futuras ampliaciones.

```text
┌────────────┐     ┌──────────────────┐
│  gui.py    │────▶│  pdf_service.py  │  (modo split)
│  + view    │     └──────────────────┘
└─────┬──────┘
      │            ┌─────────────────────────┐
      ├───────────▶│ grouped_pdf_service.py  │  (modo group)
      │            └─────────────────────────┘
      │            ┌─────────────────────────┐
      ├───────────▶│ worker_recognition +    │  (modo classify)
      │            │ classification + export │
      │            └─────────────────────────┘
      │            ┌─────────────────────────┐
      └───────────▶│ spreadsheet +           │  (modo classify_excel)
                   │ department_assignment   │
                   └─────────────────────────┘
```

## Responsabilidad de cada módulo

| Módulo | Responsabilidad |
|--------|-----------------|
| `main.py` | Punto de entrada, logging y arranque de la GUI. |
| `gui.py` | Interfaz Tkinter, modos, progreso, confirmación. |
| `classification_view.py` | Panel de clasificación (grupos / trabajadores). |
| `spreadsheet_import_view.py` | Panel Excel: hoja, columnas, vista previa. |
| `excel_summary_dialog.py` | Modal resumen departamentos / DNI tras analizar. |
| `summary_confirm_dialog.py` | Modal maximizado de confirmación al generar. |
| `ui_geometry.py` | Utilidad para maximizar ventanas Tk. |
| `pdf_service.py` | Separación de páginas con `pypdf` (modo clásico). |
| `text_extraction_service.py` | Extracción de texto seleccionable por página. |
| `recognition_rules.py` | Etiquetas, candidatos y filtros negativos. |
| `employee_name_service.py` | Reconocimiento de un nombre fiable por página. |
| `name_normalization.py` | Display, clave de agrupación y stem de archivo. |
| `grouping_service.py` | Agrupación por clave exacta (modo 1.1). |
| `grouped_pdf_service.py` | Análisis + escritura de PDFs agrupados por nombre. |
| `document_identifier_service.py` | DNI/NIE: normalizar, validar, extraer. |
| `worker_recognition_service.py` | Consolidar trabajadores; analizar clasificación. |
| `classification_models.py` | Modelos de sesión, trabajador y grupo. |
| `classification_service.py` | Grupos y asignaciones en memoria. |
| `group_export_service.py` | Exportación separada / conjunta por grupo. |
| `spreadsheet_models.py` | Modelos de importación Excel. |
| `spreadsheet_service.py` | Lectura `.xlsx`/`.xls`, hojas y columnas. |
| `department_normalization.py` | Clave y carpeta segura de departamentos. |
| `department_assignment_service.py` | Cruce Excel↔PDF y auto-grupos. |
| `session_service.py` | Ciclo de vida de la sesión (solo memoria). |
| `temporary_files_service.py` | Temporales del sistema y limpieza. |
| `recognition_models.py` | Dataclasses de análisis y resultado (modo group). |
| `filename_service.py` | Saneamiento de nombres, numeración y anti-sobrescritura. |
| `validators.py` | Validación de PDF, carpeta y nombre base. |
| `exceptions.py` | Excepciones de dominio con mensajes en español. |
| `constants.py` | Constantes de UI, nombres, etiquetas y límites. |

## Flujo de datos (modo separación)

1. El usuario selecciona un PDF.
2. `validators.validate_pdf_path` comprueba existencia, extensión y legibilidad.
3. La GUI propone nombre base y carpeta `*_separadas`.
4. Al pulsar **Separar nóminas**, un hilo de fondo llama a `split_pdf`.
5. Por cada página se escribe un PDF de una sola página.
6. El progreso se notifica al hilo principal mediante `root.after`.

## Flujo de datos (modo agrupar por nombre)

1. El usuario elige **Reconocer y agrupar por trabajador**.
2. Un hilo analiza: extraer texto → reconocer → agrupar (sin escribir).
3. La GUI muestra un resumen y pide confirmación.
4. Si el usuario confirma, otro hilo escribe:
   - `{Nombre_Trabajador}.pdf` por grupo (páginas en orden original);
   - `No_reconocidas/Pagina_XXX.pdf` por página no reconocida.
5. No se registran en logs el texto de las nóminas ni los nombres.

## Flujo de datos (modo clasificar por grupos)

1. El usuario elige **Clasificar trabajadores en grupos**.
2. Un hilo analiza: texto → DNI/NIE + nombre → `ClassificationSession`.
3. `ClassificationView` permite crear grupos y asignar trabajadores.
4. Resumen + confirmación; exportación vía `group_export_service`.
5. Sesión solo en memoria; limpieza al cerrar, limpiar o cambiar PDF.

Detalle de producto: [`CLASIFICACION_NOMINAS.md`](CLASIFICACION_NOMINAS.md).

## Separación entre GUI y lógica

- La GUI **no** manipula páginas PDF directamente.
- La lógica **no** importa Tkinter (excepto `classification_view` / `gui`).
- Los tests cubren servicios y validadores sin necesidad de abrir ventanas.

## Manejo de errores

- Se usan excepciones propias (`SeparadorNominasError` y subclases).
- La GUI captura errores de dominio y muestra `user_message` en español.
- Página sin texto o sin nombre/DNI fiable → no reconocida / parcial.
- Los detalles técnicos se registran solo a nivel de tipo de error, sin
  contenido de nóminas.

## Procesamiento del PDF

- Biblioteca: `pypdf`.
- Cada página se copia al escritor sin convertir a imagen.
- Se conserva el contenido vectorial y el texto seleccionable del original.
- Sin OCR: PDFs escaneados quedan como no reconocidos.

## Decisiones de diseño

1. **Numeración adaptativa** (modo separación): 1 / 01 / 001 según el total.
2. **Sin sobrescritura**: si existe el destino, se añade `_2`, `_3`, …
3. **Threading + `after()`**: evita congelar la interfaz.
4. **Confirmación previa** en modos agrupar y clasificar.
5. **Clave exacta** de nombre en modo 1.1; **DNI/NIE** en modo clasificación.
6. **Sin telemetría ni red**: la aplicación es totalmente local.
7. **Sin persistencia** de clasificación entre ejecuciones.

## Cómo ampliar el proyecto

- OCR local → capa opcional antes del reconocimiento.
- CSV/Excel con correo → versión 2.1+ del roadmap.
- Excel de departamentos → versión 2.5.0 (`IMPORTACION_EXCEL.md`).
- Outlook / M365 → versión 3.0 del roadmap, capa aislada.

Mantén siempre:

- GUI ≠ lógica de PDF.
- Mensajes de usuario en español.
- Tests para lógica nueva.
- Privacidad: no loguear datos personales.
