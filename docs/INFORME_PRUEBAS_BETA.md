# Informe de pruebas — Beta 2.5.0

Plantilla para registrar resultados de la beta **2.5.0-beta.2**.
Copiar esta sección por cada ronda de pruebas.

**Importante:** no incluir nombres reales, DNI/NIE, salarios ni capturas de
nóminas. Describir fallos con datos sintéticos o códigos genéricos
(p. ej. «documento A», «departamento X»).

---

## Metadatos

| Campo | Valor |
|-------|--------|
| Versión probada | 2.5.0-beta.2 |
| Fecha | YYYY-MM-DD |
| Probador | |
| SO / arquitectura | Windows __ / 64-bit |
| Origen del binario | exe GitHub / build local / `python -m` |
| SHA-256 del exe (si aplica) | |

## Resumen

| Resultado global | OK / FALLÓ / BLOQUEADO |
|------------------|------------------------|
| Tests automáticos (`pytest`) | |
| Checklist manual | [`PRUEBAS_BETA_2.5.0.md`](PRUEBAS_BETA_2.5.0.md) |

## Casos ejecutados

| ID | Caso | Resultado | Notas (sin datos personales) |
|----|------|-----------|------------------------------|
| B1 | Aviso BETA al arrancar | | |
| B2 | Flujo feliz `.xlsx` | | |
| B3 | Flujo `.xls` | | |
| B4 | Duplicado mismo depto | | |
| B5 | Conflicto de departamentos | | |
| B6 | Sin coincidencia / sin DNI | | |
| B7 | Orden de páginas en conjunto | | |
| B8 | Limpiar sesión | | |
| B9 | Regresión modos 1.0/1.1/2.0 | | |

## Defectos encontrados

| # | Severidad | Descripción (sin PII) | Reproducible | Issue |
|---|-----------|------------------------|--------------|-------|
| 1 | | | Sí/No | |

## Conclusión

- [ ] Apto para seguir en beta
- [ ] Requiere fix antes de más testers
- [ ] Candidato a `rc` / estable (solo tras autorización)
