<!-- progress/current.md -->
# Trabajo en curso

## F-012 — Campaña de mutación en paralelo (in_progress, 2026-08-13)

- Rama: `feature/F-012-mutacion-paralela`. Spec aprobada por el humano
  («F-012 aprobada, como recomiendas»), con las dos decisiones en la
  sección «Decisiones tomadas» de `design.md`:
  1. T5: comparación exacta serie-vs-paralelo con muestreo fijo
     (`--max-mutantes 60 --semilla 20260813`); campaña completa de F-011
     solo en paralelo, contrastada con el informe histórico a título
     informativo. No se repite la serie completa.
  2. Default de workers = `min(max(1, núcleos − 2), 16)`; aquí 22 lógicos
     ⇒ 16 workers.
- Diseño: coordinador que reutiliza `ejecutar_campania` por worker sobre
  `git worktree` detached en temp; reparto round-robin determinista;
  informe fusionado idéntico al de serie salvo fecha y tiempo;
  `--workers 1` = camino actual; portado a arnes-base (R12).
- Implementer lanzado sobre `specs/F-012-mutacion-paralela/`.
- Después: F-002 (spec_ready aprobada) → F-003..F-007 → F-013.

## Pendientes del humano (heredados)

- Push: `git push origin dev` (albaranes) y `git push origin main`
  (arnes-base, 1.4.0 revisada).
- Decisión de dominio de F-011 (desviación 1): ¿sv6 debe DESCARTAR las
  sintéticas prohibidas o basta precio null + revisión? (Si descarte:
  feature pequeña de sv6.)
- Rellenar los libros de evals/ground_truth/ y lanzar la primera pasada
  real: `python -m evals.runner --con-llm`.
