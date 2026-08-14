<!-- progress/current.md -->
# Trabajo en curso

## Estado tras el cierre de F-012 (2026-08-14)

- **F-012 done** (APPROVED a la primera). Resumen en `progress/history.md`.
- Siguiente por prioridad: **F-002** (obra y proveedor, `spec_ready` con
  decisiones aprobadas). Es la PRIMERA feature que toca servicios de
  producción (sv2 y sv3): el líder debe hacer PARADA 1 con el humano antes
  de lanzar su implementer.
- Cola después: F-003..F-007 (spec_ready con decisiones) → F-013 (registro
  en Sigrid, critico) → F-008/F-009/F-010.

## Pendientes del humano (heredados)

- Push: `git push origin dev` (albaranes) y `git push origin main`
  (arnes-base; lleva 1.4.0 + portero rápido + mutación paralela, todo
  revisado).
- Decisión de dominio de F-011 (desviación 1): ¿sv6 debe DESCARTAR las
  sintéticas prohibidas o basta precio null + revisión?
- Rellenar los libros de evals/ground_truth/ y lanzar la primera pasada
  real: `python -m evals.runner --con-llm`.
