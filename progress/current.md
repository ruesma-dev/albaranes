<!-- progress/current.md -->
# Trabajo en curso

## Fase de specs (2026-08-13)

- F-001 cerrada (done, APPROVED). Su rama `feature/F-001-test-estructura`
  está pendiente de merge a `dev` por el humano.
- En curso: spec-author para F-011 (evals de IA) en la rama
  `feature/F-011-evals-ia`, y después para F-002 (obra y proveedor) en
  `feature/F-002-obra-proveedor`. Ambas quedarán en `spec_ready` a la
  espera de aprobación humana. El humano ya autorizó lanzar estas specs.

## Pendientes señalados por F-001 (decisión humana)

1. `init.sh` sección 7: acotar la recolección de pytest de la raíz
   (`testpaths` o argumento) — hoy ejecuta la suite de comun dos veces,
   ~100 s de peaje por portero. Mejora genérica: propagar a arnes-base.
2. Instalar `coverage` y `ruff` en el venv de la raíz antes de la primera
   feature que toque código de producción.
3. Automejoras de protocolo propuestas por el reviewer (ver
   `progress/review_F-001.md`, sección final): fase RED para features cuyo
   entregable es un test, y control del cero en la verificación de mutación.
