<!-- progress/history.md -->
# Histórico del arnés

Registro append-only. El líder mueve aquí el resumen de cada feature terminada.

---

## F-001 — Test de estructura del monorepo (done, 2026-08-13)

- Rama `feature/F-001-test-estructura` (pendiente de merge a `dev` por el
  humano). Commits `8dd31e1` (test) y `564df13` (informes).
- Entregable: `tests/test_estructura_monorepo.py` — 4 tests trazables
  (R1–R4) que validan `harness/servicios.json` contra el árbol real; R5 es
  el propio portero (exit 0, justificado por escrito).
- Verificado: 4 passed en 0,02 s; portero completo en verde; fase RED con
  dos árboles rotos y trazas reales; mutación 0 mutantes (alcance vacío:
  `tests/` excluido por diseño), verificado de forma independiente por el
  reviewer con prueba de control (14 mutantes generables ignorando la
  exclusión). Review: APPROVED sin cambios (`progress/review_F-001.md`).
- Hallazgos que dejó (pendientes, fuera de su alcance): (1) `init.sh` corre
  la suite de `comun` dos veces (~100 s de peaje) porque la sección 7 lanza
  pytest sin acotar ruta — arreglo `testpaths`/argumento, a propagar a
  arnes-base; (2) `coverage` y `ruff` sin instalar en el venv raíz —
  instalarlos antes de la primera feature que toque producción; (3) dos
  automejoras de protocolo propuestas por el reviewer en su informe (fase
  RED para features-que-son-tests, control del cero en mutación).
