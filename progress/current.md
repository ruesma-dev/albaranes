<!-- progress/current.md -->
# Trabajo en curso

## Estado tras el cierre de F-011 (2026-08-13)

- **F-011 done** (APPROVED tras un ciclo de corrección). Resumen en
  `progress/history.md`; decisiones de dominio abiertas del humano en las
  desviaciones 1 y 2 de `progress/impl_F-011.md`.
- Siguiente por prioridad: **F-012** (mutación en paralelo, pending, sdd) →
  spec-author y PARAR en spec_ready.
- Después: F-002 (spec_ready aprobada con decisiones), F-003..F-007
  (spec_ready con decisiones cerradas), F-013 (registro en Sigrid, critico).
- Verificaciones MANUAL pendientes del humano (de F-011): pasada completa de
  evals con LLM cuando los libros de ground truth tengan casos
  (`python -m evals.runner --con-llm`), y push de arnes-base
  (`git -C C:/Users/pgris/PycharmProjects/arnes-base push origin main`) ya
  con la 1.4.0 revisada.
