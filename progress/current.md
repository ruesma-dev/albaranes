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

### Estado de la implementación (2026-08-14)

- T1 (`94d150e`), T2 (`a7f3576`), T3 (`3114a6f`) y T4 (`b23497a`)
  commiteadas; 67 tests nuevos de F-012 en verde.
- **T5** (comparación serie-vs-paralelo sobre F-011) se lanzó con tres
  desviaciones respecto a los comandos literales de `tasks.md`, todas
  documentadas y justificadas en `progress/impl_F-012.md`:
  1. `--rama ""` en ambos comandos: la rama `feature/F-011-evals-ia`
     sigue existiendo y ya está mergeada en `dev`, así que el camino por
     rama da alcance VACÍO (0 ficheros). Con `--rama ""` se fuerza el
     camino por commit de merge y sale el alcance real de F-011 (13
     ficheros, 3.812 líneas, 305 mutantes: los mismos del informe
     histórico).
  2. `--timeout 300` en ambos comandos: hoy la suite del árbol completo
     tarda ~130 s (93 s se los come el `setup` de
     `services/albaranes-comun/tests/test_humo_colas.py`), por encima del
     `timeout_por_mutante_s` de 120 s. Sin subirlo, TODOS los mutantes
     saldrían timeout en serie y en paralelo, y la comparación no
     compararía nada. No se toca `rigor.json`: el flag ya existía.
  3. Informes temporales fuera de `progress/`: el árbol tiene que estar
     limpio para que la campaña paralela arranque (R9), y un
     `progress/tmp_*.md` sin commitear lo ensucia. Van al scratchpad de
     la sesión y se pegan en el informe.
- T6 hecha: portado a arnes-base con commit local `0436314` (sin push).
  Contenido commiteado idéntico en los dos repositorios (mismo md5).
- T7 hecha: campaña de la propia F-012 lanzada CON la implementación
  paralela. Cuatro pasadas: 24 supervivientes → 6, cerrando 18 huecos de
  test reales por el camino. Los 6 finales están analizados en
  `progress/mutacion_F-012.md` (cinco equivalentes demostrables y uno
  aceptado y documentado). Ninguno queda en `PENDIENTE`.
- T5 hecha y es el criterio de éxito cumplido: mismos totales en serie y
  en paralelo (60 evaluados, 37 muertos, 23 supervivientes, 0 timeouts) y
  diff de informes limpio salvo fecha, «Tiempo total» y la ruta del propio
  fichero. **6.491,0 s en serie frente a 743,4 s en paralelo: 8,7×.**
- T8 hecha: `bash harness/init.sh` en verde (242 tests, cobertura de
  líneas cambiadas 95,8 %, exit 0).
- Feature lista para review. NO se marca `done`: eso es del líder tras el
  APROBADO del reviewer.

## Pendientes del humano (heredados)

- Push: `git push origin dev` (albaranes) y `git push origin main`
  (arnes-base, 1.4.0 revisada).
- Decisión de dominio de F-011 (desviación 1): ¿sv6 debe DESCARTAR las
  sintéticas prohibidas o basta precio null + revisión? (Si descarte:
  feature pequeña de sv6.)
- Rellenar los libros de evals/ground_truth/ y lanzar la primera pasada
  real: `python -m evals.runner --con-llm`.
