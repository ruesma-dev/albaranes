Revisión incremental desde e598ecb (C2 aprobado en c6709ff; e598ecb solo toca la spec) hasta HEAD `a9b0d16` · pasada 1 de D, D bis y CR-D1

# F-048 · Review de los cambios de C2 (CR-C3..C5), del bloque D (sv3), del D bis (sv4) y de CR-D1

**Veredicto: APPROVED.** No hay bloqueantes. Dejo tres menores y un aviso para el líder (C), que la spec
no resuelve. CR-D1 cierra el choque con la red de obra y no hay otro camino que borre los motivos
nuevos ni que los resucite mal. **Rigor** `critico` (declarado): exige RED, cobertura ≥ 80 %,
mutación (T34) y evals (T40).

## Qué se ejecutó (resultados reales)

- `bash harness/init.sh` tal cual: exit 0, **ENTORNO LISTO**. Raíz `865 passed in 117.59s`, servicios
  de caché, `PUERTA COBERTURA 99.5 % (639/642)`, `PUERTA TAMAÑO` OK. El `[AVISO]` de evals (5 rutas
  sensibles, ahora con `lectura_correo.py`) es el esperado: se cubre en T40.
- A mano, una detrás de otra y cada una en su pytest: **comun `272 passed, 3 skipped in 101.84s`** ·
  **sv2 `368 passed in 4.24s`** · **sv3 `233 passed in 1.58s`** · **sv4** (su venv) `223 passed in 3.69s`.
  `git status` limpio.

## RED reproducidos en copias del scratchpad (coinciden con el informe)

1. **CR-D1**: una copia de comun con los valores viejos (`obra_correo_*`), puesta delante en
   `PYTHONPATH` y comprobada con `ruesma_comun.__file__`. Con los tests de HEAD en sv3 (`-k cr_d1`) da
   `4 failed, 15 deselected`. En las filas 3 y 5 falla con `TypeError: ... not NoneType`, porque la red
   dejó la columna a NULL; en las dos del prefijo, con `'obra_correo_*'.startswith('obra_')`. Con HEAD: verde.
2. **CR-C3**: una copia de sv2 en HEAD (`git archive`) con el `lectura_correo.py` de `e598ecb` da
   `19 failed, 6 passed`: 14 `ValidationError` de `LecturaCorreo`, más la evidencia sin recortar. Es la
   cifra exacta del informe.

## CR-C3, CR-C4 y CR-C5 (menores 1–3 y aviso B de la review de C2): cerrados

- **CR-C3** (`sv2 domain/models/lectura_correo.py:67-90`): hay dos validadores `before`. `evidencia`
  se recorta a `MAX_EVIDENCIA`, que se importa de comun, y un número pasa a texto. `obra_codigos`
  convierte los números en `str` (`945.0` ⇒ `945`), descarta `bool` y objetos, y envuelve un valor
  suelto en una lista. El schema que ve el LLM no cambia (hay test). El test del handler
  (`test_f048_r24_lectura_tolerante.py:222`) comprueba que llegan 160 caracteres a `env1`, a
  `env2.debug.phase_1_json` y a `final.debug.phase_2...`; y como `origen_datos` viaja en el envelope
  final, así llega también a los blobs y a la BBDD. Un `[945]` ya no tumba la fase 1 y cruza con la
  lista (`:238`). El log opt-in (b) queda escrito en el informe.
- **CR-C4**: `albaranes-comun/tests/test_f048_r36_retry_policy.py` (12 tests) cubre los tres caminos
  de log, y vive en la suite de comun, que es la que usará T34.
- **CR-C5** (`origen_datos_resolver.py:134-148`): en la fila 4, `valor_final` y la cabecera se
  escriben con la forma de la lista, y `valor_papel` guarda lo que se leyó (tests parametrizados:
  `945`, `09-45` y `0945`). Sin lista, se deja como lo leyó IA1. En la fila 5 la cabecera no se toca
  (`test_f048_r19_r22_tabla_d5.py:218`). T25 demuestra que la red de sv3 encuentra `0945` y que
  descartaba `09-45`.

## sv3 (T23–T26)

- **R26**: `DocumentoAlbaran.origen_datos: OrigenDatos | None` usa el contrato de comun, sin copiarlo
  (`extraction_models.py:88`). `_sanear_envelope` solo filtra `meta`, así que `data.origen_datos` pasa
  intacto (`persistence_worker.py:41-52`). El test recorre el handler REAL con envelopes nuevos, viejos
  y con un campo futuro, y ninguno lanza (no van a poison). El `forbid` de `data` sigue en pie.
- **R27**: `build_merge_analysis` rehace `data` y ahora copia `origen_datos=openai.data.origen_datos`
  (`albaran_confidence_service.py:274`). Es el agujero por el que F-043 perdía la clasificación. El
  `save()` real sobre una sesión doble lo lleva hasta `raw_extraction_json`. Sin DDL: solo cambian dos
  ficheros de producción de sv3.
- **R29–R31** (`:125-151`, `:615`): los únicos disparadores son la fila 3 (`discrepancia`) y la 5
  (`correo_ambiguo`). Hay un test de las otras filas con los motivos de hoy, y en la base (96,42 %)
  `review_required=true` lo pone solo el motivo, sin tocar la confianza ni la obra. No se duplica:
  `save()` sustituye la columna entera (delete + insert, `sqlalchemy_albaran_repository.py:2029`).
  Los nombres se importan de comun, y un test por inspección comprueba que no hay literales.

## Red de obra y demás caminos que filtran o reescriben `review_reasons_json`

Revisé todos los sitios de sv3, sv4 y sv6 que leen o escriben la columna:
- sv3 `retirar_revision_obra` (`:1966`, prefijo `obra_`): ya no los toca (hay test CR-D1 con el
  servicio real y la función pura real). `marcar_revision_cabecera` y `descartar_obra_no_valida` solo
  AÑADEN, sin duplicar. `reenrich_by_merge_id` (el «volver a buscar» de sv4) no recalcula los motivos.
  La rama de duplicado no llama a `save()`; ya estaba declarado.
- sv4 `review_repository.py:3340-3390` solo depura `proveedor_cif_no_casa:`, así que no le afecta.
  `update_document` (`:3070`, el guardado del revisor) no toca ni los motivos ni `review_required`.
  Los `review_required = FALSE` de sv4 son de `albaran_line_valuations`, no del documento.
- sv6 solo escribe en sus tablas de valoración. **Nada pierde los motivos ni los resucita mal.**

## sv4 (T27–T28): plantilla renderizada con la plantilla real y el conftest de sv4 (en una copia)

| Caso | Resultado |
|---|---|
| Fila 3 + motivo | `warning origen-duda`: «el correo dice 0945 y el papel dice 0937. Se ha usado la del correo.» |
| Fila 5 (con papel / sin papel) | `warning`: «…varias obras (0945, 0320) y ninguna es la del papel (0937)» / «…el papel no trae obra» |
| Fila 4 | `info`: «…una es la del papel (945). Se ha usado esa.» |
| Fila 1 fuera de lista | `info`, con los candidatos escapados (probé `<script>`: sale `&lt;script&gt;`) |
| Fila 2, sin bloque, JSON roto, `None`, bloque inválido, raíz lista | no se pinta el aviso y la ficha abre |

Los dos motivos salen en el bloque «Motivos de revisión» que ya existía, y el `warning` depende SOLO
del motivo: con la fila 3 sin su motivo, sale `info`. sv4 no escribe nada: `review_repository.py` no
cambia en el diff. Los nombres (`MOTIVOS_REVISION_ORIGEN` y los `MOTIVO_CORREO_*`) se importan de comun.

## Bloqueantes: ninguno. Menores (no bloquean):

1. **Quedan los nombres viejos en el papeleo del líder.** Aparecen en `harness/features.json:534`
   (la descripción de F-048, que se copia a `BACKLOG.md:104`) y en `progress/current.md:93-95`.
   Además, `progress/impl_F-048.md:129` sigue diciendo que T37 y T39 citan `obra_correo_*`, cuando
   `a9b0d16` ya lo corrigió. Hay que cambiarlo antes de cerrar, porque es lo que se lee al retomar y
   lo que copiará T32 en `azure-apps/`.
2. **`review_models.py:696`**: cuando el correo cita varios códigos fuera de la lista, el aviso dice
   «el correo cita A, B, que no está en la lista». La concordancia está en singular. Es solo texto.
3. **`review_models.py:691`**: en la fila 4 el aviso cita `valor_papel` (`945`), mientras la cabecera
   ya lleva `0945` desde CR-C5. Es veraz, porque es lo que leyó el papel, pero al revisor le pueden
   parecer dos obras distintas. Se puede citar `valor_final`, o las dos lecturas.

## Aviso para el líder (C): el revisor corrige la obra a mano

La spec no lo fija. Hoy pasa esto: `update_document` cambia `obra_codigo` y el «volver a buscar»
lleva a sv3 por `reenrich_by_merge_id`, donde la red retira `obra_*`, pero **`correo_obra_*` se
queda**. `review_required` no baja, igual que con cualquier otro motivo (D7 de F-002: el cierre es
del revisor). El aviso sigue en `warning` y dice «Se ha usado la del correo (0945)» cuando la
cabecera ya muestra la obra del revisor. **No se pierde nada ni se corrompe nada**, pero el aviso
queda obsoleto. Es el mismo patrón que `proveedor_cif_no_casa` colgado en SS-0801977, y ese caso
acabó con una depuración propia. Opciones:
(a) aceptarlo: el motivo explica por qué entró en revisión;
(b) que sv4 lo PINTE distinto cuando `obra_codigo` ≠ `origen.obra.valor_final` («el revisor cambió
la obra»), sin escribir nada, compatible con R35;
(c) retirarlo, lo que choca con R35 y design §6.
Mi recomendación es (b), como ficha aparte o en T38.

## Checkpoints (bloque intermedio)

- **C1** [x] init.sh exit 0 · [x] ficheros · **C2** [x] una sola feature `in_progress` (sin bloqueadas) ·
  [x] rama · [x] `current.md` al día (menor 1 aparte) · N/A `history.md`: nada pasa a `done`.
- **C3** [x] hexagonal: sv3 marca en `application` y el modelo va en `domain`; sv4 solo pinta, en
  `domain/models` + plantilla · [x] primera línea con la ruta en todos los `.py` del diff · [x] sin prints,
  secretos ni dependencias nuevas · [x] sin DDL · [x] la obra la decide sv2, y sv3 y sv4 no recalculan.
- **C3 bis** N/A: no se toca `docs/referencia/`.
- **C4** [x] R26–R35 con `test_f048_rN_*` en verde (ver tabla) · [x] sin red ni BBDD (dobles de sesión
  y de Sigrid) · [x] el extremo a extremo es T37–T39 (MANUAL), que ya cita `correo_obra_*`.
- **C4 bis** [x] rigor declarado · [x] RED real, 2 reproducidos (uno de CR-D1) · [x] cobertura 99,5 %
  · **N/A mutación y RM1–RM6**: la campaña es T34 sobre la feature completa, y medir ahora dejaría de
  valer en cuanto entren E–G (RM1) · [x] «Evidencias» con los cuatro números.
- **C4 ter** [x] exigencia `aviso` con motivo: las 5 rutas sensibles se evalúan en T40, que se factura
  y necesita el visto bueno del humano. **Bloqueará la review final** si falta.
- **C5** [x] T23–T28 `[x]` con commits `F-048 Tn:`, más CR-C3..C5 y CR-D1 · [x] árbol limpio ·
  [x] `features.json` en `in_progress`.

## Trazabilidad

| R | Tests |
|---|---|
| R26 | `albaranes-persistencia/tests/test_f048_r26_modelo.py` (handler real, sin poison) |
| R27 | `test_f048_r27_merge.py` (`build_merge_analysis` y `save()` sobre sesión doble) |
| R28 | `test_f048_r28_red_obra.py` (+ fila 4 con la forma de la lista) |
| R29–R31, CR-D1 | `test_f048_r29_r31_motivos_revision.py` (19); comun `test_f048_r24_origen_datos.py` |
| R32–R34 | `albaranes-front/tests/test_f048_r32_r34_vista_avisos.py` (13) |
| R34–R35 | `test_f048_r35_vista_modelo.py` (27) |
| R17/R24 (CR-C3), R36 (CR-C4), D4 bis (CR-C5) | `test_f048_r24_lectura_tolerante.py`, comun `test_f048_r36_retry_policy.py`, `r19_r22 ::fila4_*` |

**Automejora** (propuesta, no aplicada; vale para `arnes-base`): en C4, «si una feature añade valores a
una lista que otra red filtra por PREFIJO, el test recorre esa red real». CR-D1 salió porque el
implementer lo buscó, no porque lo pidiera ningún checkpoint.
