"""Constantes centralizadas de la aplicación Separador de Nóminas PDF."""

from __future__ import annotations

APP_NAME: str = "Separador de Nóminas PDF"
APP_EXECUTABLE_NAME: str = "SeparadorNominas"
APP_VERSION: str = "2.0.0"

# Extensiones y nombres
PDF_EXTENSION: str = ".pdf"
OUTPUT_FOLDER_SUFFIX: str = "_separadas"
FILENAME_SEPARATOR: str = "_"
COLLISION_START_INDEX: int = 2
UNRECOGNIZED_FOLDER_NAME: str = "No_reconocidas"
UNRECOGNIZED_PAGE_PREFIX: str = "Pagina"

# Modos de procesamiento (GUI)
PROCESS_MODE_SPLIT: str = "split"
PROCESS_MODE_GROUP: str = "group"
PROCESS_MODE_CLASSIFY: str = "classify"

# Exportación por grupo (modo clasificación)
EXPORT_MODE_SEPARATE: str = "separate"
EXPORT_MODE_COMBINED: str = "combined"

# Etiquetas típicas de nómina (orden de prioridad)
EMPLOYEE_NAME_LABELS: tuple[str, ...] = (
    "NOMBRE Y APELLIDOS",
    "DATOS DEL TRABAJADOR",
    "TRABAJADOR",
    "EMPLEADO",
    "PERCEPTOR",
    "NOMBRE DEL TRABAJADOR",
    "NOMBRE",
)

# Límites de nombres de archivo en Windows
WINDOWS_INVALID_FILENAME_CHARS: str = '<>:"/\\|?*'
WINDOWS_RESERVED_NAMES: frozenset[str] = frozenset(
    {
        "CON",
        "PRN",
        "AUX",
        "NUL",
        "COM1",
        "COM2",
        "COM3",
        "COM4",
        "COM5",
        "COM6",
        "COM7",
        "COM8",
        "COM9",
        "LPT1",
        "LPT2",
        "LPT3",
        "LPT4",
        "LPT5",
        "LPT6",
        "LPT7",
        "LPT8",
        "LPT9",
    }
)
# Margen seguro para ruta completa en Windows (sufijo _NNN.pdf + posibles _N)
MAX_BASE_NAME_LENGTH: int = 180
DEFAULT_BASE_NAME: str = "nomina"

# Interfaz
WINDOW_MIN_WIDTH: int = 900
WINDOW_MIN_HEIGHT: int = 720
PROGRESS_IDLE: float = 0.0
PROGRESS_COMPLETE: float = 100.0

# Mensajes de estado (interfaz)
STATUS_READY: str = "Preparado para comenzar."
STATUS_OPENING_PDF: str = "Abriendo y validando el PDF..."
STATUS_PROCESSING_TEMPLATE: str = "Procesando página {current} de {total}..."
STATUS_ANALYZING_TEMPLATE: str = "Analizando página {current} de {total}..."
STATUS_WRITING_GROUPS: str = "Escribiendo archivos agrupados..."
STATUS_WRITING_TEMPLATE: str = "Creando archivo {current} de {total}..."
STATUS_WAITING_CONFIRMATION: str = (
    "Revisa el resumen y pulsa Generar o Cancelar."
)
STATUS_CONFIRM_PROMPT: str = "¿Generar archivos?"
STATUS_COMPLETED: str = "Proceso completado correctamente."
STATUS_ERROR: str = "Se ha producido un error."
STATUS_CANCELLED_SELECTION: str = "Selección cancelada."
STATUS_CANCELLED_BY_USER: str = "Proceso cancelado. No se ha guardado ningún archivo."
STATUS_CLASSIFYING: str = "Clasifica los trabajadores en grupos y pulsa Generar."
STATUS_CLEAR_SESSION_CONFIRM: str = (
    "Se eliminarán de la memoria todos los trabajadores, grupos y asignaciones "
    "de esta sesión. Los PDFs ya generados no se eliminarán."
)
STATUS_WRITING_CLASSIFICATION: str = "Escribiendo archivos de clasificación..."
STATUS_REANALYZE_CLASSIFY_CONFIRM: str = (
    "Ya hay una clasificación en memoria.\n\n"
    "Si continúas, se borrarán todos los grupos y asignaciones actuales "
    "y se volverá a analizar el PDF.\n\n"
    "Recuerda: para generar los archivos PDF debes pulsar «6. Generar», "
    "no «3. Analizar y clasificar».\n\n"
    "¿Quieres reanalizar y perder los grupos?"
)
STATUS_CLASSIFY_STEPS_HINT: str = (
    "Orden sugerido: 1 PDF → 2 Carpeta → 3 Analizar → 4 Crear grupo → "
    "5 Añadir al grupo → 6 Generar → 7 Abrir carpeta"
)

# Logging
LOG_FORMAT: str = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
LOG_DATE_FORMAT: str = "%Y-%m-%d %H:%M:%S"
LOGGER_NAME: str = "separador_nominas"
