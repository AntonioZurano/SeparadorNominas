# Guía de contribución — SeparadorNominas

Este documento describe el flujo de trabajo Git y las políticas de desarrollo.
Las instrucciones obligatorias para agentes de IA están en
[`AGENTS.md`](AGENTS.md).

## Estructura de ramas

```text
main
└── development
    ├── feature/nombre-de-la-feature
    ├── fix/nombre-del-fix
    ├── refactor/nombre-del-cambio
    ├── docs/nombre-documentacion
    └── test/nombre-pruebas
```

| Rama | Uso |
|------|-----|
| `main` | Solo versiones **estables**. Sin trabajo directo. |
| `development` | Integración y pruebas. Sin implementar la tarea encima. |
| `feature/*`, `fix/*`, … | Trabajo diario. **Siempre** desde `development`, nunca desde `main`. |

Las ramas `release/*` existentes son **legado histórico** y no forman parte del
flujo activo.

### Convención de nombres

- Prefijo según tipo + descripción en **kebab-case**.
- Ejemplos: `feature/renombrado-automatico`, `fix/error-pdf-protegido`,
  `docs/flujo-trabajo-git`.

## Flujo para una feature o fix

1. Revisar estado del repo (`git status`, rama activa, working tree limpio).
2. `git switch development` (actualizar remoto solo si está autorizado).
3. `git switch -c feature/nombre` (o `fix/…`).
4. Explicar el alcance; implementar **solo** ese alcance.
5. Añadir o actualizar tests.
6. Ejecutar pruebas (`pytest`) y lint disponible (`ruff`, `mypy`).
7. Actualizar documentación afectada y `CHANGELOG.md` (Unreleased).
8. Informar del resultado.
9. **Detenerse.** Esperar orden expresa para merge.

## Política de tests

- Obligatorios para lógica de negocio (`filename_service`, `validators`,
  `pdf_service`, etc.).
- PDFs sintéticos con `tmp_path`; **nunca** nóminas reales ni datos personales.
- Ejecutar la batería antes de solicitar integración.
- Detalle: [`docs/PRUEBAS.md`](docs/PRUEBAS.md).

## Política de documentación

- Actualizar los `.md` afectados en la misma rama que el código.
- Mantener coherencia con `AGENTS.md` y este archivo.
- No documentar como hecho lo que está en el roadmap sin implementar.

## Política de commits

- Commits pequeños, una responsabilidad.
- Formato recomendado (Conventional Commits en español):

```text
feat: ...
fix: ...
test: ...
docs: ...
refactor: ...
```

- No crear commits no solicitados si el entorno no lo permite o no se ha pedido.
- Antes de committear (si se solicita): listar archivos, tests y mensaje propuesto.

## Política de merges

- **Nunca** automáticos. Solo con autorización expresa del responsable.
- Preferir `git merge --no-ff`.
- **No** squash salvo orden explícita.
- Tras merge a `development`: repetir tests.
- Merge `development` → `main` solo para versión de producción ordenada.

## Política de tags

| Tipo | Ejemplo | Cuándo |
|------|---------|--------|
| Prueba | `v1.1.0-dev.1`, `v1.1.0-rc.1` | Sobre integración en `development`, si se ordena |
| Estable | `v1.1.0` | Tras merge a `main`, si se ordena |

Antes de crear una tag: proponer versión, motivo, archivos a actualizar y nombre
exacto. Esperar aprobación.

## Versionado semántico

```text
MAJOR.MINOR.PATCH
```

- **PATCH**: correcciones compatibles.
- **MINOR**: funcionalidades compatibles.
- **MAJOR**: incompatibles o cambios grandes de arquitectura.

Versiones de prueba: `1.1.0-dev.1`, `1.1.0-rc.1`.

Archivos a alinear cuando se ordene subir versión: `VERSION`, `pyproject.toml`,
`CHANGELOG.md`, `constants.APP_VERSION` y docs que muestren la versión.

No modificar la versión sin indicación expresa.

## Checklist antes de solicitar integración

```text
- [ ] La rama parte de development.
- [ ] El alcance es pequeño y concreto.
- [ ] El código funciona.
- [ ] Los tests pasan.
- [ ] Se han añadido tests nuevos cuando corresponde.
- [ ] Se ha actualizado la documentación.
- [ ] Se ha actualizado CHANGELOG.md.
- [ ] No se han añadido datos personales ni PDFs reales.
- [ ] No se ha realizado merge.
- [ ] No se ha creado tag.
- [ ] No se ha realizado push.
```

## Acciones que requieren autorización expresa

Merge a `development` o `main`, tags, push, eliminar ramas, rebase, reset
hard, force push, tocar secretos.
