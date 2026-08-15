<!-- progress/current.md -->
# Trabajo en curso

## F-003 implementada, pendiente de review (2026-08-15)

- **F-003 `in_progress`**: implementación TERMINADA en la rama
  `feature/F-003-valorados-match-estricto`. Informe completo en
  `progress/impl_F-003.md`. Siguiente paso: **reviewer** contra
  `CHECKPOINTS.md`. Nadie marca `done` sin su APROBADO.
- `bash harness/init.sh` en **ENTORNO LISTO**; cobertura del diff 96,6 %;
  mutación 87/84/3 (los 3 supervivientes, equivalentes y analizados).
- La implementación se hizo en un **worktree aislado** (`wt-f003`) para no
  tocar el árbol principal mientras el humano ejecutaba servicios en local.
  El árbol principal no se ha modificado.
- **Sin despliegue** (regla dura del humano, vigente desde la PARADA 1): cero
  `az`, cero builds, cero secrets.

## Estado tras el cierre de F-002 (2026-08-14)

- **F-002 done** (APPROVED). Resumen en `progress/history.md`.
- Cola siguiente: F-004..F-007 (spec_ready con decisiones) → F-013 (registro
  en Sigrid, critico) → F-008/F-009/F-010.

## Pendientes del humano

- **De F-003**: las 6 verificaciones MANUAL locales (columnas nuevas y DDL
  idempotente, caso ×120, ORE OIL, total con IVA, CETOSA/espesores, descuento
  contra precio de contrato) — guion exacto en `progress/impl_F-003.md`.
- **De F-003, despliegue**: 4 imágenes (sv2, sv3, sv5, sv6) con **orden
  obligatorio sv3 → sv5 → sv6** (sv5 lee con SQL crudo columnas que crea
  sv3). Sin variables nuevas obligatorias ni secretos.
- **De F-003, evals**: rellenar en `evals/ground_truth/` los casos de la
  feature (×120 y ORE OIL en IA1; CETOSA, elemento base 0,5 mm y bolsa de
  cuñas en IA3/IA4, esperado «no casar»; sus entradas en INPUTS). Mientras
  estén vacíos, la puerta de rutas sensibles solo puede dar NO_EVALUABLE.
- Las 5 verificaciones MANUAL locales de F-002 (obra 0937, HORPRESOL, fecha
  2023, `email_received_datetime` por colas, nº de obras tras el filtro
  >0450).
- Push: `git push origin dev` (albaranes) y `git push origin main`
  (arnes-base).
- Hallazgo lateral repetido: el `.gitignore` de sv2 **y el de sv6** ignoran
  `*.example`, así que sus `.env.example` actualizados no entran en git —
  decidir si se corrige.
- Decisión de dominio de F-011 (desviación 1): ¿sv6 descarta las sintéticas
  prohibidas o basta precio null + revisión?
