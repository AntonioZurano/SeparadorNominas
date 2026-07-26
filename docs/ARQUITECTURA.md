# Arquitectura

## Visión general

`SeparadorNominas` separa la interfaz gráfica de la lógica de negocio para
facilitar pruebas, mantenimiento y futuras ampliaciones.

```text
┌────────────┐     ┌─────────────────┐     ┌──────────────┐
│  gui.py    │────▶│  pdf_service.py │────▶│   pypdf      │
│  (Tkinter) │     │  (orquestación) │     └──────────────┘
└────────────┘     └────────┬────────┘
                            │
           ┌────────────────┼────────────────┐
           ▼                ▼                ▼
   validators.py   filename_service.py   exceptions.py
```

## Responsabilidad de cada módulo

| Módulo | Responsabilidad |
|--------|-----------------|
| `main.py` | Punto de entrada, logging y arranque de la GUI. |
| `gui.py` | Interfaz Tkinter, diálogos, progreso y mensajes al usuario. |
| `pdf_service.py` | Separación de páginas con `pypdf` y resultado del proceso. |
| `filename_service.py` | Saneamiento de nombres, numeración y rutas sin sobrescritura. |
| `validators.py` | Validación de PDF, carpeta y nombre base. |
| `exceptions.py` | Excepciones de dominio con mensajes en español. |
| `constants.py` | Constantes de UI, nombres y límites. |

## Flujo de datos

1. El usuario selecciona un PDF.
2. `validators.validate_pdf_path` comprueba existencia, extensión y legibilidad.
3. La GUI propone nombre base y carpeta `*_separadas`.
4. Al pulsar **Separar nóminas**, un hilo de fondo llama a `split_pdf`.
5. Por cada página:
   - se construye el nombre (`build_page_filename`);
   - se evita sobrescritura (`get_available_path`);
   - se escribe un PDF de una sola página con `PdfWriter`.
6. El progreso se notifica al hilo principal mediante `root.after`.
7. Al terminar, se muestra el resumen y se habilita **Abrir carpeta de destino**.

## Separación entre GUI y lógica

- La GUI **no** manipula páginas PDF directamente.
- La lógica **no** importa Tkinter.
- Los tests cubren servicios y validadores sin necesidad de abrir ventanas.

## Manejo de errores

- Se usan excepciones propias (`SeparadorNominasError` y subclases).
- La GUI captura errores de dominio y muestra `user_message` en español.
- Los detalles técnicos se registran solo a nivel de tipo de error / traza
  controlada, sin contenido de nóminas.

## Procesamiento del PDF

- Biblioteca: `pypdf`.
- Cada página se copia al escritor sin convertir a imagen.
- Se conserva el contenido vectorial y el texto seleccionable del original.
- No se aplica compresión agresiva ni rasterizado.

## Decisiones de diseño

1. **Numeración adaptativa**: 1, 2, 3… / 01, 02… / 001, 002… según el total.
2. **Sin sobrescritura**: si existe `x_001.pdf`, se crea `x_001_2.pdf`.
3. **Threading + `after()`**: evita congelar la interfaz.
4. **Sin persistencia de rutas**: no se guardan preferencias en disco (v1.0.0).
5. **Sin telemetría ni red**: la aplicación es totalmente local.

## Cómo ampliar el proyecto

Orientaciones para versiones futuras (sin implementarlas aún):

- Extraer texto → nuevo módulo `text_extraction.py`.
- Detección de nombres → `worker_detection.py` + UI de revisión.
- Asociación correo → import CSV/Excel y servicio de matching.
- Outlook / M365 → capa de integración aislada, nunca mezclada con `pdf_service`.

Reglas:

- Mantener la separación GUI / lógica.
- Añadir tests para cada comportamiento nuevo.
- Actualizar `VERSION`, `CHANGELOG.md` y documentación afectada.
