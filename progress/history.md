<!-- progress/history.md -->
# Histórico del arnés

Registro append-only. El líder mueve aquí el resumen de cada feature terminada.

---

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
