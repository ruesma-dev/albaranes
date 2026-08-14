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

## F-002 — Tanda 1: Identificación de obra y proveedor (done, 2026-08-14)

- Rama `feature/F-002-obra-proveedor`. **Primera feature sobre servicios
  reales (sv2 y sv3)**, con la regla dura del humano: SIN DESPLIEGUE hasta
  probar en local. Review: **APPROVED** (`progress/review_F-002.md`).
- Entregado: bloque determinista de obras activas en el prompt de IA1
  (consulta a sigrid-api con filtro provisional 4 dígitos y >0450
  configurable, cap 300) con secret pendiente-de-despliegue; redes
  deterministas en sv3 (obra inexistente → sin obra + revisión;
  canonicalización de proveedor por CIF conservando el literal en raw;
  propuesta por similitud con scorer de razón social; guard de año) y fix
  del gap de `email_received_datetime` en modo colas (R12). Sin DDL, sin
  tocar ruesma_comun.
- Evidencias: portero en verde; cobertura del diff 82,1 % (umbral 80);
  mutación paralela 108 mutantes / 13 supervivientes analizados; puerta de
  rutas sensibles APLICÓ por primera vez (prompts.yaml de sv2) en modo
  aviso con NO_EVALUABLE documentado (libros de evals vacíos).
- Desviación destacada (aceptada por el reviewer): scorer propio
  `_score_razon_social` porque el `_match_score` que fijaba el design
  puntuaba 0,33 el propio caso de referencia HORPRESOL — el design se
  contradecía; los caminos previos del resolver quedan intactos.
- Pendiente del humano: 5 verificaciones MANUAL en el pipeline LOCAL
  (guion en `progress/impl_F-002.md` §T12) y, tras validar, autorización
  expresa para desplegar (secret de sv2 + azure-apps/albaranes.md en ese
  mismo trabajo). Hallazgo lateral: el .gitignore de sv2 ignora *.example
  y su .env.example actualizado no entra en git.

## F-012 — Campaña de mutación en paralelo (done, 2026-08-14)

- Rama `feature/F-012-mutacion-paralela` (T1–T8, un intento inicial perdido
  por infraestructura sin tocar nada). Review: **APPROVED a la primera**
  (`progress/review_F-012.md`).
- Entregado: coordinador paralelo en `harness/mutacion` — reparto
  round-robin determinista, workers sobre `git worktree` desechables con
  limpieza y restauración garantizadas por worker, fusión de informes
  idéntica al formato en serie, `--workers` con default
  `min(max(1, núcleos−2), 16)`. Portado a `arnes-base` (commit `0436314`,
  md5 idéntico).
- Criterio de éxito cumplido y medido: muestreo con semilla (60 mutantes)
  con **totales idénticos** serie vs paralelo (37 muertos / 23
  supervivientes / 0 timeouts) y **6.491 s vs 743 s: 8,7×**.
- T7 usó la propia herramienta sobre sí misma: 4 pasadas, de 24
  supervivientes a 6 (cerrando 18 huecos de test reales); los 6 finales
  analizados (5 equivalentes demostrables, 1 aceptado). Cobertura de líneas
  cambiadas: 95,8 %. 242 tests en verde.
- Desviaciones de T5 (documentadas y aceptadas por el reviewer): `--rama ""`
  para el alcance por commit de merge, `--timeout 300` aplicado a ambos
  lados, informes temporales fuera de `progress/`.

## F-011 — Evals de IA con ground truth y puerta en el arnés (done, 2026-08-13)

- Rama `feature/F-011-evals-ia`, 16 commits (T1–T14 + lint + correcciones del
  review). Review: CHANGES_REQUESTED (una ruta ausente en la declaración y
  sin test que fijara el conjunto) → corregido → **APPROVED**
  (`progress/review_F-011.md`, con re-verificación).
- Entregado: `evals/` (conversor xlsx→fixtures con barrido de sensibles,
  comparador por criticidad crítico/laxo, runner determinista y con LLM,
  informes en progress/), puerta genérica de rutas sensibles
  (`harness/rutas_sensibles.py` + declaración de 14 rutas + sección 7 ter de
  init.sh + C4 ter en CHECKPOINTS) y propagación del mecanismo a arnes-base
  (1.4.0, módulo idéntico, verificado por el reviewer).
- Evidencias: 170+ tests trazables R1–R26 en verde; cobertura 88,8% de 1.254
  líneas cambiadas (umbral 80); mutación 305 mutantes / 133 supervivientes,
  todos analizados y recalculados de forma independiente; runner en
  NO_EVALUABLE (exit 2) por libros vacíos, que es lo esperado.
- Decisiones de dominio abiertas para el humano (documentadas en
  `progress/impl_F-011.md`, desviaciones 1 y 2): (1) sv6 no descarta las
  sintéticas prohibidas — les deja precio null y las manda a revisión; si el
  humano quiere descarte real, es feature de sv6; (2) obra/proveedor/CIF/
  fecha/nº de albarán no son observables por el eval extremo-a-extremo (los
  cubre el libro IA1) y el informe los lista como no observables.
- Deuda señalada: hueco `lineas_no_casadas` de sv5 (consecuencia de negocio,
  en el análisis de supervivientes); `ValorEsperado.desde_json` es código
  muerto (borrar o testar); automejoras 6.1/6.2 del review para arnes-base
  (cobertura sin medición ≠ 0%, y rutas mínimas en la declaración).
