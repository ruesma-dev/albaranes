<!-- progress/current.md -->
# Trabajo en curso

## F-001 — Test de estructura del monorepo (in_progress, 2026-08-13)

- Rama: `feature/F-001-test-estructura` (creada desde `dev`).
- sdd=false: el mini-spec son los `acceptance` de `harness/features.json`.
- PARADA 1 hecha por chat: el humano confirmó arrancar F-001 y lanzar
  después las specs de F-011 y F-002.
- Plan: implementer crea `tests/test_estructura_monorepo.py` (stdlib pura),
  fase RED con salida real, campaña de mutación, informe en
  `progress/impl_F-001.md`. Después reviewer contra CHECKPOINTS.md.
- Tras el cierre de F-001: spec-author para F-011 (evals) y F-002 (obra y
  proveedor), cada una en su rama, y PARAR en spec_ready para aprobación.

### Estado del implementer (2026-08-13) — terminado, a la espera del reviewer

- Implementación **completa**: `tests/test_estructura_monorepo.py` (4 tests,
  uno por criterio `acceptance` salvo R5, que es el propio `init.sh`).
  Commit `8dd31e1`. Informe completo en `progress/impl_F-001.md`.
- `bash harness/init.sh` en **verde** (exit 0) tras el cambio.
- Fase RED hecha con dos árboles rotos en el scratchpad, sin tocar el
  `harness/` real; las dos trazas de fallo están pegadas en el informe.
- Campaña de mutación lanzada: **0 mutantes** (el alcance excluye `tests/`),
  informe en `progress/mutacion_F-001.md`. Puerta de cobertura: **N/A** con el
  motivo que imprime `init.sh` (la feature no cambia líneas de producción).
- Verificaciones MANUAL (humano) pendientes: **ninguna**.
- Desviaciones respecto a los `acceptance`: **ninguna**. R5 no tiene test
  automatizado a propósito (un test que ejecutara `init.sh` se llamaría a sí
  mismo); se verifica ejecutando el portero, con su salida en el informe.
- Dos hallazgos para el líder, NO corregidos por quedar fuera de los ficheros
  que F-001 puede tocar (detalle en el informe): (1) crear `tests/` en la raíz
  hace que `init.sh` recolecte también los tests de `comun` y los ejecute dos
  veces, ~97 s extra por ejecución — se arregla acotando la recolección de la
  raíz, y eso es mejora del arnés a propagar a `arnes-base`; (2) `coverage` y
  `ruff` no están instalados en el venv de la raíz, lo que dejará sin datos la
  puerta de cobertura en la primera feature que toque producción.
