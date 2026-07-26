# Recursos (assets)

Esta carpeta contiene recursos estáticos de la aplicación.

## Icono de la aplicación

El archivo `assets/icon.ico` se usa automáticamente al compilar con
`scripts/build.ps1` (PyInstaller `--icon`).

Si se elimina o no existe, la compilación usará el icono estándar de
Python/Windows.

Para sustituirlo:

1. Reemplaza `assets/icon.ico` por un nuevo `.ico`.
2. Vuelve a ejecutar `scripts/build.ps1`.

Recomendaciones del icono:

- Formato `.ico` multi-resolución (16, 32, 48, 256 px).
- Diseño simple y legible en tamaños pequeños.
- Evitar texto largo dentro del icono.

No incluyas en esta carpeta PDFs reales ni datos personales.
