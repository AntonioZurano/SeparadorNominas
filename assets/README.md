# Recursos (assets)

Esta carpeta contiene recursos estáticos de la aplicación.

## Icono de la aplicación

En la versión 1.0.0 la compilación usa el icono estándar si no existe un
archivo propio.

Para añadir un icono personalizado en futuras versiones:

1. Coloca un archivo `icon.ico` en esta carpeta (`assets/icon.ico`).
2. Vuelve a ejecutar `scripts/build.ps1`.
3. El script detectará el icono automáticamente y lo incluirá en el `.exe`.

Recomendaciones del icono:

- Formato `.ico` multi-resolución (16, 32, 48, 256 px).
- Diseño simple y legible en tamaños pequeños.
- Evitar texto largo dentro del icono.

No incluyas en esta carpeta PDFs reales ni datos personales.
