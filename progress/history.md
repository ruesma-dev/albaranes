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

## F-019 — Importe de línea: manda el unitario leído (done, 2026-08-18)

- Rama `feature/F-019-importe-unitario-manda`, 12 commits (T1–T11 + round
  trip). Review: CHANGES_REQUESTED (R18 sin ningún test automático) →
  corregido → **APPROVED** en segunda pasada
  (`progress/review_F-019.md`, que conserva los dos veredictos).
- Origen: la prueba local del humano del 18-08 con los dos albaranes de
  Feymaco del lote `alvaro_17082026` (`progress/prueba_local_feymaco_
  20260818.md`). La lectura de IA1 era exacta, pero el importe valorado salía
  multiplicado por la cantidad: 139,66 € reales → 6.238,14 €, y 19,41 € →
  970,50 €.
- Causa: el SELECT de sv5 (`sqlalchemy_valuation_context_repository.py`)
  calculaba `importe_albaran = cantidad × precio_neto` creyendo que
  `precio_neto` era un unitario neto, cuando el prompt de IA1 lo define como
  el IMPORTE de la línea. sv6 (`price_reconciler.py`) agravaba el efecto
  dando prioridad al importe sobre el unitario leído.
- Entregado: 2 cambios reales de producción (el `cantidad *` sale del sitio
  equivocado en sv5; la precedencia de sv6 pasa a «manda el unitario leído,
  el importe solo se despeja si faltan campos») y 57 tests nuevos. La
  protección contra partidas alzadas (cinta 18,84 € / PA 8.000 €) se conserva
  con test de regresión propio. sv2 no se tocó.
- Evidencias: 248 tests en la raíz + 11 en sv5 + 40 en sv6, todos en verde;
  cobertura 100 % de las 5 líneas cambiadas (umbral 80, nivel `critico`);
  mutación 4 generados / 4 muertos / 0 supervivientes. Fase RED con la salida
  real del fallo pegada en `progress/impl_F-019.md`.
- Efecto lateral saneado: ese importe inflado viajaba también al prompt de
  IA3, así que el LLM de valoración estaba viendo importes × cantidad.
- Puerta de rutas sensibles en AVISO (no bloquea): la pasada de evals
  declarada no se pudo ejecutar porque `evals/ground_truth/` sigue sin casos.
- PENDIENTE del humano: las 4 verificaciones MANUAL de T10 (reprocesar en
  local 2.137.569 → 139,66 € y 2.139.643 → 19,41 €, sin
  `unitario_declarado_vs_derivado_mismatch`, y un albarán de hormigón sin
  precios impresos que siga valorándose por contrato); decidir qué histórico
  se revalora (R20, sin script de backfill); y **reconciliar F-003 antes de
  arrancarla**: su R4 manda conservar el cálculo que F-019 acaba de corregir.

### F-019 — round trips 2 y 3 (cierre definitivo, 2026-08-18)

El cierre anterior era prematuro: la prueba local del humano demostró que el
criterio de aceptación (139,66 €) NO se cumplía. Dos round trips más:

- **Round trip 2**: la causa no estaba en sv5 ni en sv6, sino en **sv4**.
  `review_repository::_recalc_valuation_importes` recalculaba
  `cantidad × precio` **sin descuento** y pisaba en BBDD el importe y el total
  que sv6 había escrito bien. La pinza que lo demostró: el 2.137.569 tenía
  `updated_at_utc` seis minutos posterior a su creación (cuando el humano lo
  abrió en el portal) y quedaba en 232,76 €, mientras el 2.139.643 —mismo
  código, 22 s después, nunca abierto en el front— conservaba sus 19,41 €.
  La fórmula estaba escrita CUATRO veces en ese fichero. sv4 pasó de 0 a 44
  tests.
- **Round trip 3** (tres cambios exigidos por el reviewer): (1) el guardián de
  R24 decidía por el RESULTADO, así que pisaba justo las filas que sv6 protege
  a propósito (`declared_vs_calculated_mismatch`); ahora decide por las
  ENTRADAS. (2) La fórmula pura se movió a **`ruesma_comun/importes.py`**
  (regla dura de CLAUDE.md: nada de lógica copiada entre servicios), dejando
  la política en cada servicio; al unificarlas se descubrió que **las dos
  copias YA divergían**: un descuento ilegible reventaba sv6 con `ValueError`.
  (3) El cableado `payload → descuento` quedó cubierto por test.
- Evidencias finales: cobertura **93,1 %** (81/87, umbral 80); mutación 31
  generados / 28 muertos / 3 supervivientes verificados equivalentes; suites
  sv4 59, comun 49, sv6 53, todas ejecutadas en serie. **APPROVED en cuarta
  pasada** (`progress/review_F-019.md` conserva los cuatro veredictos).
- Lección para el arnés: el criterio «139,66 €» vivía solo en el guion MANUAL;
  ningún test comprobaba el AGREGADO ni el valor PERSISTIDO. Por ahí se coló.

## F-027 — Error de ×1000: la red KG→TN era código muerto (done, 2026-08-19)

- Rama `feature/F-027-conversion-kg-tn-muerta`, 11 commits (T1–T11).
  **APPROVED a la primera** (`progress/review_F-027.md`), rigor `critico`.
- Origen: la revisión del resto del lote alvaro_17082026
  (`progress/revision_resto_lote_20260818.md`, hallazgo H-1). El albarán 58826
  de MAHORSA se valoró en **468.763,40 €** (30.380 kg sin unidad impresa
  contra un contrato en TN a 15,43 €/TN) y el 58878 en 462.282,80 €.
- Causa: existía una red de plausibilidad de toneladas para exactamente ese
  caso, pero **nunca se ejecutaba**. Con las categorías de unidad sin casar, el
  builder llamaba al conversor con `cantidad=None` a propósito y el conversor
  salía por su guarda antes de llegar a la red.
- Entregado: un solo cambio de producción en `valuation_builder.py` — convertir
  SIEMPRE con la cantidad real y usar `category_match=False` solo para marcar
  revisión; y la unidad de destino pasa a ser la de la línea que pone el precio
  (`derived_line.unidad_medida`), no la del albarán.
- **La segunda mitad del ×1000**, descubierta al redactar la spec: con línea
  derivada, la conversión iba hacia la unidad del albarán (KG→KG, factor 1) y
  daba los mismos 468.763 € **sin que la IA fallara en nada**, y sin marcar
  revisión. Ese camino se habría activado al implementar F-024. Cerrado antes
  de abrirse.
- Números: 58826 pasa de 468.763,40 € a **468,76 €** (30,38 TN, factor 0,001).
  Los importes ya verificados NO se mueven: 224964 → 475,60 €, 225137 →
  980,10 €, 1167 → 871,20 €, Feymaco 2.137.569 → 139,66 € y 2.139.643 → 19,41 €.
- Los 468,76 € no son los 390,99 € del administrativo: la diferencia es el
  precio (15,43 en vez de 12,87), que es **F-031** y queda fuera a propósito.
- Riesgos asumidos y FIJADOS POR TEST (no en prosa): D2, se convierte también
  cuando la IA declara desacuerdo de unidades, marcando revisión; D3, el umbral
  de 1000 podría reinterpretar un albarán legítimo, que queda siempre marcado.
- PENDIENTE del humano: las verificaciones MANUAL de T10 y decidir qué
  histórico se revalora (R26/D5: sin script de backfill, se sanea desde sv4).

### F-034 — el mutador muta `is` / `is not` (cerrada 2026-08-20)

- **Por qué importaba**: `x is None` es LA guarda de ausencia en Python y el
  mutador no la conocía. Los dos defectos más caros del proyecto vivían en una
  guarda `is` —el `cantidad is None` que mataba la red KG→TN de F-027
  (468.763 €) y el `importe_albaran_declarado is not None` de F-019—, así que
  sus campañas de mutación se midieron ciegas justo en el punto que más
  importaba, declarando «0 supervivientes».
- **Entregado**: `ast.Is`/`ast.IsNot` en `COMPARACIONES`, delimitación por
  palabra entera para los operadores alfabéticos (`is` cabe dentro de
  «análisis»), y la puerta de evals condicionada a lo **versionado**: el
  `evals/ground_truth/` que la feature daba por inexistente **sí existe**, con
  seis `.xlsx`, pero `.gitignore` los excluye.
- **Tres pasadas de review, y las dos primeras acertaron.** La 1ª rechazó por un
  error del LÍDER: propagar el arnés 1.6.0 dentro de la rama de la feature
  después de medir las puertas (56 líneas declaradas, 1.057 reales). Se resolvió
  revirtiendo. **Regla que queda**: la propagación del arnés va en rama `chore/`
  y después del merge.
- La 2ª demostró que **la campaña de mutación mentía**: 18/1/0 en 111 s frente a
  9/8/2 al reejecutar. Dos mutantes declarados muertos eran semánticamente
  idénticos al original —imposibles de matar—, y de los 8 supervivientes
  **cuatro eran huecos reales** en el delimitador de palabra. Se cerraron con
  tests. Sin esa insistencia la feature habría cerrado con cuatro agujeros.
- **Causa probable de los falsos muertos**: bytecode rancio (CPython reutiliza
  el `.pyc` entre mutantes consecutivos). Lo arregla el arnés 1.6.0.
- **Coste**: ~600k tokens en dos implementers y tres reviewers. De ahí sale
  F-038, y las seis reglas de protocolo que la acompañan.

### Arnés 1.6.0 y 1.6.1 (2026-08-19 y 20)

- **1.6.0** — la campaña de mutación deja de poder mentir: línea base
  obligatoria, veredicto no binario (`BASE_ROTA`), restauración a prueba de
  muerte con centinela en disco, e `init.sh` que reconoce una campaña en curso.
  Más el porte de `is`/`is not` de F-034. Montar su prueba de verdad destapó
  dos defectos más: el aborto no nombraba nada cuando la suite muere en la
  RECOLECCIÓN, y el **bytecode rancio**. Evidencia medida sobre un repositorio de
  juguete: control 5/2/3, ANTES (paralelo) 5/5/0 declarándose fiable, DESPUÉS
  aborta nombrando el test culpable.
- **1.6.1** — el instalador ya no puede pisar estado del proyecto (F-035).
- Propagado a `albaranes`; los otros cuatro proyectos siguen atrás a propósito.

### F-035 — el instalador del arnes no pisa el estado del proyecto (cerrada 2026-08-20)

- **Origen**: el 19-ago, actualizando `albaranes` de 1.5.0 a 1.5.2, el propio
  instalador piso `harness/features.json` (34 features -> 1),
  `docs/ARCHITECTURE.md` (183 -> 37 lineas) y `current.md` e `history.md`.
  Se recupero entero porque nada estaba commiteado. El defecto no era del humano
  que pulso de mas: era que el instalador no distinguia entre ficheros DEL ARNES
  y ficheros DE ESTADO del proyecto.
- **Entregado** en `arnes-base` 1.6.2: `politica_ficheros.json` con tres
  categorias y aborto si algo queda sin clasificar, backup previo con manifiesto,
  precondiciones con `-IgnorarPrecondiciones`, normalizacion de finales de linea
  y una suite propia de 65 comprobaciones.
- **Lo que cerro la feature** no fue el verde de la suite: en la primera pasada,
  un mutante que anulaba el atajo del arnes puro **sobrevivia a las 47
  comprobaciones enteras**, porque todos los casos que lo tocaban usaban
  `-Forzar`. El reviewer volvio a aplicarlo en la segunda pasada y lo vio morir.
- **Hallazgo lateral que vale la pena recordar**: la verificacion MANUAL con
  `-SoloDiff` —que no escribe nada— destapo que `albaranes` tenia 12 tests de
  `test_mutacion_operadores.py` y `arnes-base` solo 9. Faltaban justo los que
  cierran los cuatro huecos de F-034. El instalador encontro una divergencia que
  se le habia pasado a todos.
- **Prueba de que funciona**: al lanzarlo contra este repositorio, los cuatro
  `[PROTEGIDO]` que aparecen son exactamente los cuatro ficheros que el
  incidente destruyo. Y 11 diffs que antes se enseñaban uno a uno resultaron ser
  solo finales de linea: ese ruido era lo que entrenaba a pulsar «Todos».

### F-038 — bajar el coste en tokens del ciclo SDD (cerrada 2026-08-20)

APPROVED en **dos** pasadas, la segunda ya incremental. Nació de una medición:
los subagentes de una sola sesión gastaron ~712.000 tokens y `progress/`
acumulaba 12.250 líneas. Cada línea de spec se paga tres veces —la escribe el
spec-author, la lee el implementer, la relee el reviewer—.

Lo que entregó, por orden de importancia real:

- **T0, el cimiento**: `ejecutor_para` acota la suite de la raíz a `tests`. Sin
  esto, cualquier fichero de `harness/` se juzgaba con `python -m pytest` SIN
  ruta, que moría en la recolección y se leía como `exit 1` = MUERTO. Las
  campañas sobre el propio arnés eran **falsos verdes**; desde la 1.6.0 abortaban
  en vez de mentir, pero no se podían ejecutar. Afecta a F-011 y F-012.
- **Muestreo por nivel de rigor**: `estandar` = 20 mutantes con semilla
  `20260820`, `critico` sin tope; `nivel_por_defecto` baja de `critico` a
  `estandar` (las 38 fichas ya declaran rigor, así que no cambió ninguna).
- **El informe de mutación imprime SHA de HEAD, línea base y media por mutante**.
  Ésa es la pieza que de verdad ahorra: convierte RM1 y RM2 de juicio en dato.
  En las dos pasadas de esta feature el reviewer **no reejecutó la campaña**.
- **Puerta de tamaño** (`harness/tamano.py` + sección 7 quater de `init.sh`),
  que mide **solo la feature en curso**: las 12 specs viejas quedan amnistiadas
  por construcción, sin lista de excepciones que mantener.
- Umbral de reejecución de 5 min a 60 s, revisión incremental por defecto, y las
  seis reglas RM1–RM6 repartidas entre `reviewer.md` y C4 bis.

**Topes recalibrados el mismo día**, antes de cerrar: `120/200/150/100` →
`150/250/220/140`. La mediana histórica del repositorio es ~484 líneas (impl) y
~475 (review); los originales recortaban un ~70 % y tanto el implementer como el
reviewer entregaron **clavados en el límite** (150/150 y 100/100), que es la
señal de que el tope estaba mandando sobre el contenido. Los nuevos recortan un
~55 %.

**Lección que dejó T17**: el flaky que se creyó ajeno era propio. T5 añadió al
informe la fila de reloj `Media por mutante evaluado (s)` y el test de paridad
serie/paralelo no extendió su filtro. Como la campaña corre con `-x`, **un fallo
intermitente de cualquier test se lee como MUERTO** — de ahí el falso muerto de
`mutacion.py:1781`. Una campaña de mutación no vale más que la suite que la juzga.

Altas relacionadas: **F-039** (prioridad 2; hereda verificar la campaña paralela
y remedir las campañas medidas con la invocación rota).
