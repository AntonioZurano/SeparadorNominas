# Arquitectura

## Visión general

`SeparadorNominas` separa la interfaz gráfica de la lógica de negocio para
facilitar pruebas, mantenimiento y futuras ampliaciones.

```text
┌────────────┐     ┌──────────────────┐     ┌──────────────┐
│  gui.py    │────▶│  pdf_service.py  │────▶│   pypdf      │
│  (Tkinter) │     │  (1 pág / archivo)│     └──────────────┘
└─────┬──────┘     └──────────────────┘
      │
      │            ┌─────────────────────────┐
      └───────────▶│ grouped_pdf_service.py  │
                   │ analyze + write grupos  │
                   └───────────┬─────────────┘
                               │
     ┌─────────────┬───────────┼────────────┬──────────────┐
     ▼             ▼           ▼            ▼              ▼
 text_extract  employee_name  grouping  name_norm   recognition_rules
```

## Responsabilidad de cada módulo

| Módulo | Responsabilidad |
|--------|-----------------|
| `main.py` | Punto de entrada, logging y arranque de la GUI. |
| `gui.py` | Interfaz Tkinter, modos, progreso, resumen y confirmación. |
| `pdf_service.py` | Separación de páginas con `pypdf` (modo clásico). |
| `text_extraction_service.py` | Extracción de texto seleccionable por página. |
| `recognition_rules.py` | Etiquetas, candidatos y filtros negativos. |
| `employee_name_service.py` | Reconocimiento de un nombre fiable por página. |
| `name_normalization.py` | Display, clave de agrupación y stem de archivo. |
| `grouping_service.py` | Agrupación por clave exacta. |
| `grouped_pdf_service.py` | Análisis + escritura de PDFs agrupados. |
| `recognition_models.py` | Dataclasses de análisis y resultado. |
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

## Flujo de datos (modo agrupar)

1. El usuario elige **Reconocer y agrupar por trabajador**.
2. Un hilo analiza: extraer texto → reconocer → agrupar (sin escribir).
3. La GUI muestra un resumen y pide confirmación.
4. Si el usuario confirma, otro hilo escribe:
   - `{Nombre_Trabajador}.pdf` por grupo (páginas en orden original);
   - `No_reconocidas/Pagina_XXX.pdf` por página no reconocida.
5. No se registran en logs el texto de las nóminas ni los nombres.

## Separación entre GUI y lógica

- La GUI **no** manipula páginas PDF directamente.
- La lógica **no** importa Tkinter.
- Los tests cubren servicios y validadores sin necesidad de abrir ventanas.

## Manejo de errores

- Se usan excepciones propias (`SeparadorNominasError` y subclases).
- La GUI captura errores de dominio y muestra `user_message` en español.
- Página sin texto o sin nombre fiable → no reconocida (no es error fatal).
- Los detalles técnicos se registran solo a nivel de tipo de error / traza
  controlada, sin contenido de nóminas.

## Procesamiento del PDF

- Biblioteca: `pypdf`.
- Cada página se copia al escritor sin convertir a imagen.
- Se conserva el contenido vectorial y el texto seleccionable del original.
- Sin OCR: PDFs escaneados quedan como no reconocidos.

## Decisiones de diseño

1. **Numeración adaptativa** (modo separación): 1 / 01 / 001 según el total.
2. **Sin sobrescritura**: si existe el destino, se añade `_2`, `_3`, …
3. **Threading + `after()`**: evita congelar la interfaz.
4. **Confirmación previa** en modo agrupar: no se escribe sin OK del usuario.
5. **Clave exacta** de agrupación (sin fuzzy) para evitar mezclas peligrosas.
6. **Sin telemetría ni red**: la aplicación es totalmente local.

## Cómo ampliar el proyecto

- OCR local → capa opcional antes de `employee_name_service`.
- Revisión manual editable → UI sobre `GroupingAnalysis` (fuera de 1.1.0).
- Asociación correo → import CSV/Excel y servicio de matching (1.2.0).
- Outlook / M365 → capa de integración aislada, nunca mezclada con `pdf_service`.

Mantén siempre:

- Procesamiento local.
- Tests.
- Mensajes en español.
- Documentación actualizada.
- Flujo Git `development` → rama de trabajo → merge solo con autorización.
