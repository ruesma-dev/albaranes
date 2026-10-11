<!-- progress/impl_F-065_fase3.md -->
# F-065 · fase 3 (T21–T26) · informe del implementer

Rama `feature/F-065-lineas-editadas-y-reparto` (worktree `../albaranes-F-065`), con `dev` fusionado (`7b46bd8`, fast
forward: la fase 2 aprobada). Rigor `critico`. Servicios: **sv4** (código) y **sv9** (solo test de contrato). Sin DDL
(modelo M1). Despliegue: **solo sv4**. Alcance: R29–R37 (F6 dividir; absorbe F-016).

## 1. Commits

`2467983` T20 marcada (review de la fase 2 aprobada) · `b72341e` T21 RED · `941af3f` T22 dominio · `96a417f` T23
repositorio, servicio y ruta · `860b6c5` T24 detalle y front · `966b16b` T25 sv9 R36 y ARCHITECTURE · `0606240` T26 supervivientes cerrados · el commit de este informe (mutación, inventario, `current.md`) ·
`azure-apps` `a9aa68d` (rama `master` de ese repo, sin push).

## 2. Qué cambió

- **Dominio** (`review_models.py`): `repartir(q, ca0, importe0, precio, descuento, partes)` (pura): `cc = qk`,
  `ca = ca0 × qk / Q` (`None` si no hay), importe `round(importe0 × qk / Q, 2)` con la última absorbiendo el redondeo
  (sin `importe0`, la fórmula canónica de `ruesma_comun.importes`); `RepartoInvalido` (R30) para Q nula o 0, fuera de
  2–20 partes, parte nula, 0 o de otro signo (`math.copysign`), o suma a 0,005 o más de Q (umbral
  `0,005 − 1e-9`: `4 + 6,005 − 10` es 0,004999999999999005 en coma flotante y debe contar; 0,00499994 no). Mensajes que dicen qué falla («La parte 2 no tiene cantidad (o es 0).»,
  «Las partes suman 9; la línea tiene 10.»). `ParteDivision` (cantidad con coma decimal; partida recortada, vacía =
  `None` = almacén), `DivisionBody` (2–20 partes), `ParteCalculada`, `DivisionHecha(partes, derivadas)`,
  `aviso_reparto(numero, suma, leida)`. `DisplayLine.parte` y `.aviso_reparto`.
- **Repositorio** (`review_repository.py`): `dividir_linea(document_id, valuation_line_id, partes) -> DivisionHecha |
  None`. `_exigir_editable` (409: alta, aprobado, fila guardada) → fila del documento o `None` (404) → 422 si es
  `synthetic_modifier`, sin línea de contrato ni derivada, o con la marca «revisa la cantidad» → `repartir` → parte 1
  = la original (cantidades, importe, `importe_source='calculated'` y, si su partida cambia, la misma regla que editar)
  → partes k ≥ 2 `INSERT … VALUES` con `_COPIADAS_AL_DIVIDIR` (precio y su origen de contrato, unidades y categoría,
  factor, partida leída, confianza y método, descuento, código externo, producto Sigrid) más `line_kind='reparto'`,
  `merge_line_id` NULL, `parent_merge_line_id` = la blanca de la original (o su padre, si la original ya es una parte),
  `descripcion_linea` puesta (la de la original, el concepto de la blanca o el de su línea: CR1), sin revisión,
  desbloqueada → `_recalcular_total_in_session` (ROUND) → un solo `commit`. Origen (R32): `_pasa_a_nueva` = partida
  distinta de la actual y `cambia_origen` (la de su línea de contrato y la vacía no cambian el origen); Nueva ⇒ derivada
  `manual_override` propia con los valores de la fila. `_build_display_lines`: las hijas de cada blanca en el orden
  del cargador (sintéticas de sv6 al final, por id: el de `orden_filas_ficha`, así las partes van tras su original) y
  `_marcar_reparto` («Parte k de N», aviso en la primera). `_synthetic_to_display` conserva `manual` y `reparto`.
- **Servicio**: `dividir_linea` con UNA entrada de deshacer `dividir` («Dividir en N · partida descripción (doc)»):
  `restore` = original + su derivada (si era Nueva) + cabecera; `delete_created` = partes y derivadas nuevas.
- **Ruta** `POST /api/documents/{id}/lines/{vid}/dividir {"partes": [{"cantidad", "codigo_partida"}]}`: 200 con los
  ids; 404; 409 por el manejador común; 422 del cuerpo (validación) o `{"detail": motivo}` de `RepartoInvalido`.
- **Plantilla**: «Dividir» en las filas editables salvo sintéticas, con «revisa la cantidad» o sin cantidad
  (`data-q`, `data-partida`, vacía si está en almacén); «Parte k de N» y el aviso en la celda del concepto; `<dialog
  id="dividir-dialog">` solo si la ficha es editable. CSS de la ventana.
- **Front** (`app.js`): puras `faltaPorRepartir`, `repartoValido` (la regla de R30 en el navegador),
  `cuerpoDivision`; `wireDividir`: botón o F6 en la fila abre la ventana (aviso si hay filas con cambios sin guardar:
  dividir recarga), N (2–20) repinta conservando lo tecleado, partida con el combo de la obra (`attachPartidaCombo`
  admite `opciones.alElegirAlmacen`: en la ventana «Almacén» solo vacía la partida), «Falta: X» / «Sobra: X» /
  «Reparto completo.», «Aceptar» habilitado solo si vale, Enter acepta, error del servidor dentro de la ventana.
  **F7 quitado** (y su `duplicateRow`/`camposBody`); F8 se queda. Etiqueta «Dividir» en el historial de «Deshacer».
- **sv9** (sin código): `tests/test_f065_partes.py` + 4 tests R36 con el validador real.
- **Docs**: `docs/ARCHITECTURE.md` regla 20 (viñeta «Dividir»); `azure-apps/albaranes.md` §4 (`line_kind` `reparto`
  y lo que escribe sv4 al dividir) y su pie.

## 3. Decisiones (a confirmar en la review)

- **D1 · «Revisa la cantidad» no se divide** (lo pidió el coordinador: elegir lo más simple). 422 «Antes de dividir,
  revisa la cantidad: cambió la unidad (corrígela o guarda la fila).» y la ficha no pinta «Dividir» en esa fila. Por
  qué: la Q de esa fila no es de fiar (está en otra unidad), así que repartirla multiplicaría el error en N filas;
  heredar la marca obligaría a propagarla y a quitarla en N filas y a que CR3 contase N posiciones. Es el mismo trato
  que una Q nula (422), y resolverla es un «Guardar».
- **D2 · Las partes de una Nueva llevan siempre derivada propia** (también con la misma partida). R32 dice «conserva
  el origen»: siguen Nueva, pero una derivada compartida se editaría in situ desde dos filas (`update_line_conciliacion`
  cambia la derivada de la fila).
- **D3 · La parte 1 también puede cambiar de partida** en la ventana; se le aplica la regla de editar (Contrato con
  otra partida ⇒ Nueva; vacía ⇒ almacén; Nueva ⇒ su derivada). Por eso `DivisionHecha.derivadas` puede incluir la de
  la original y el deshacer guarda la derivada de una Nueva.
- **D4 · `dividir_linea` devuelve `DivisionHecha`** (partes y derivadas), no `list[int]` (design §5.4): el deshacer
  necesita borrar también las derivadas (R34). La ruta devuelve solo los ids de las partes.
- **D5 · Filas que no se dividen (422)**: además de R30, una fila sin línea de contrato ni derivada («revalora», como
  O2). Una fila `manual` (traída, sin blanca) SÍ se divide: sus partes no cuelgan de ninguna blanca (sin «Parte k de
  N» ni aviso, que no hay con qué comparar). Una parte se puede volver a dividir: sus partes cuelgan de la misma blanca.
- **D6 · El aviso de familia compara en la unidad del albarán** (`cantidad_albaran`, o la convertida si no hay) contra
  la cantidad de la blanca, con la tolerancia de R30: con conversión (t → kg) la Q de la ficha no es la de la blanca.
- **D7 · `partida_action`** de una parte: `almacen_elegido` si va a almacén; si no, la de la original (es rastro: nadie
  la lee para decidir). Las partes nacen sin `review_reasons_json` ni `importe_albaran_declarado` (el declarado era de
  la línea entera).

## 4. Fase RED (traza real)

Sobre `b72341e` (solo los tests), `.venv\Scripts\python -m pytest tests/test_f065_f3_dividir.py -q -p
no:cacheprovider` ⇒ **`81 failed, 2 passed in 10.82s`** (los 2 que pasaban: «sin Dividir en un aprobado / en una fila
bloqueada», guardas que no podían fallar sin botón). Traza resumida (`grep "^E "`, recuento por motivo):
```
21 E  ImportError: cannot import name 'RepartoInvalido' from 'domain.models.review_models'
18 E  AttributeError: 'AlbaranReviewRepository' object has no attribute 'dividir_linea'
13 E  ImportError: cannot import name 'repartir' from 'domain.models.review_models'
 8 E  AttributeError: '_Servicio' object has no attribute 'initialize'
 6 E  AttributeError: 'ReviewService' object has no attribute 'dividir_linea'
 4 E  AttributeError: 'DisplayLine' object has no attribute 'aviso_reparto'
 3 E  ValueError: substring not found                     (faltaPorRepartir, repartoValido, cuerpoDivision en app.js)
 2 E  AttributeError: 'DisplayLine' object has no attribute 'parte'
 1 E  assert ('Parte 1 de 2' in '<!-- templates/document_detail.html -->...
 1 E  assert ('"F6"' in '// static/app.js ...
 1 E  assert 'function attachPartidaCombo(input, opciones)' in '// static/app.js ...
 1 E  ImportError: cannot import name 'DivisionHecha' / 'DivisionBody' (uno cada uno)
```
Los 8 de `_Servicio` eran un fallo DEL TEST (el servicio falso de la ruta no tenía `initialize`); corregido en T23.
Para que la ruta tenga su RED de verdad, se repitió con `app.py` y `review_service.py` de `941af3f` (T22: dominio
hecho, sin ruta ni servicio) y los tests ya corregidos: `pytest … -k "ruta or deshacer" --tb=line` ⇒ **`15 failed, 1
passed`**: `assert 404 == 200` / `assert 404 == 422` / `assert 404 == 409` (la ruta no existía; el que pasa es el 404)
y `AttributeError: 'ReviewService' object has no attribute 'dividir_linea'` ×6. Después, ficheros restaurados a
`HEAD` (`git status` limpio). Tras T22: `-k dominio` 26 passed; T23: `-k "repositorio or deshacer or ruta"` 43
passed (con un arreglo del test: `poner_alta` sin `document_id=DOC` miraba el documento de F-053); T24: `-k
pintado` 10 passed y el fichero entero 84 passed. sv9 R36 (T25) pasa a la primera: es un test de contrato de un
servicio que NO cambia (R36 «sin código»), su valor es fijar lo que sv9 hace con las filas que ahora deja sv4.

## 5. Verificación (resultado real)

- Criterios de las tareas: T22 `-k dominio`, T23 `-k "repositorio or ruta or deshacer"`, T24 `-k "pintado or js"`
  (node v24) y T25 `pytest services/albaranes-alta-sigrid/tests/test_f065_partes.py -k r36` (4 passed), en verde.
- `tests/test_f065_f3_dividir.py`: **92 passed**. Suite de sv4 (sola): **1196 passed** (72,8 s). Suite de sv9
  (sola): **534 passed** (25,0 s).
- **`bash harness/init.sh`** (tal cual, worktree, salida a un log) sobre el árbol de este informe: **exit 0**; raíz `1083 passed`; sv4 `1196 passed`; sv9 `534 passed`; sv1–sv3, sv5, sv6 y comun en verde (caché: sin cambios); **`PUERTA COBERTURA: 100.0% de 147 líneas cambiadas cubiertas (147/147, umbral 80%, nivel critico)`**; rutas sensibles N/A; `PUERTA TAMAÑO` dentro de topes; **`ENTORNO LISTO. Puedes trabajar.`** Avisos previos (ruff 1250, F-053 `blocked`, infra sin tests, `[ADAPTAR]` de otras specs). T28 (el `init.sh` de cierre) se deja sin marcar: va después de T27.

## 6. Cobertura y mutación (T26)

- `PUERTA COBERTURA` (sobre `966b16b`, antes de T26): `100.0% de 146 líneas cambiadas cubiertas (146/146, umbral
  80%, nivel critico)`; la de `init.sh` final, en §5.
- **Mutación** `python -m harness.mutacion --feature F-065 --salida progress/mutacion_F-065_fase3.md` (alcance
  `7b46bd8..rama`: `review_models.py` 146, `review_repository.py` 350, `review_service.py` 42, `app.py` 31 = 569
  líneas de sv4; el JS y la plantilla no los muta la herramienta: los vigilan los tests con node y de render).
  **Final, sobre `0606240`: 99 mutantes, 99 muertos, 0 supervivientes, 0 timeouts, 0 sin veredicto, 2780,6 s**, 4
  workers, media 28,1 s × 4 ≈ 112 s por mutante frente a líneas base de 110,9–115,5 s (coherente, RM2).
- **Primera campaña** (`966b16b`, archivada fuera de git): 107 mutantes, 92 muertos, **15 supervivientes**, todos
  resueltos en `0606240` (ninguno queda como equivalente):
  - *Huecos reales, cerrados con tests* (11): la descripción de su línea de contrato cuando no hay otra y `None` si no
    hay ninguna (`or None`→`and None`, `(… or "")`→`and ""`); precio y unidad de la fila o, si faltan, de su línea
    (`is not None`→`is None`, dos `or`→`and` de la unidad); la original que pasa a Nueva con blanca deja
    `descripcion_linea` nula como al editar (`editada=False`→`True`, `sin_blanca` invertido); `is_valued` de una blanca
    (línea re-sangrada); la familia sin cantidad del albarán suma la convertida (`or 0.0`→`and 0.0`); la última parte
    en céntimos aunque el importe traiga más decimales (`round(…, 2)`→`3`, `10,006` ⇒ 5,00 + 5,01); la tolerancia
    (`round(…, 6)`→`7`: además era un error, 0,00499994 se rechazaba y R30 lo admite).
  - *Equivalentes eliminados reescribiendo el código* (4): `(cantidad > 0) != (q > 0)` con `>=` en cualquiera de los
    dos lados es inalcanzable (0 ya se rechazó) ⇒ `math.copysign(1.0, cantidad) != math.copysign(1.0, q)`; la clave
    `valuation_line_id or 0`→`or 1` del orden de las hijas ⇒ fuera el `sorted` (el cargador ya ordena así); `casada
    … or descripcion`→`and` en la derivada de una Nueva ⇒ la derivada lleva `descripcion` (la misma que la fila, más
    coherente). El umbral pasó de `round(…, 6)` a `0,005 − 1e-9` (ver arriba; JS igual).
- RM5: sin equivalentes en la campaña final, no aplica.

## 7. MANUAL T27

Comandos en `progress/current.md` (bloque F-065): F6 sobre una fila Contrato de 18 ⇒ 6 (su partida) / 7 (otra) / 5
(almacén), «Guardar y aprobar», la `SELECT` de T27, desaprobar, «Deshacer» y repetir.

## 8. Fuera de alcance y lo que falta

- Fuera: X4, X12 (F-066), conservar lo manual al revalorar (F-058: revalorar descarta las partes, y lo avisa R22
  porque `reparto` cuenta como fila manual); dividir las sintéticas de sv6; atajo Ctrl+D (P1 del explore; F6 es el de
  la spec). sv9 sin código.
- Falta: MANUAL T27 (humano), review de la fase 3, fusionar en `dev`, `init.sh` en el árbol principal y desplegar
  **solo sv4** (después del despliegue de la fase 2) y T28 (`init.sh` de cierre).

## 9. Evidencias

| Evidencia | Valor real |
|---|---|
| Tests ejecutados | sv4 **1196 passed** (92 nuevos en `test_f065_f3_dividir.py`); sv9 **534 passed** (4 nuevos R36); raíz 1083 passed; el resto en verde (`init.sh` exit 0) |
| Cobertura de las líneas cambiadas | **100,0 % (147/147)**, `PUERTA COBERTURA` de `init.sh` |
| Mutantes | **99 generados, 99 muertos, 0 supervivientes** (`progress/mutacion_F-065_fase3.md`, `0606240`); primera campaña 107/15 supervivientes, cerrados |
| Tiempo de la suite | sv4 72,8 s sola; sv9 25,0 s; mutación 2780,6 s (4 workers) |

## Pasada 2 (review `3516c40`: CHANGES_REQUESTED por CR1)

Commit `556afae` (código y tests) y el de este informe. sv4 solo; sin DDL; despliegue igual (**solo sv4**).

- **CR1 · números no finitos.** `ParteDivision`, `ConciliacionEditBody` y `LineaATraer` con `model_config =
  ConfigDict(allow_inf_nan=False)`: `NaN`/`±Infinity` del JSON son 422 (como texto ya lo eran: `_numero_es`). El 422
  por defecto de FastAPI devolvía el `NaN` en `input` y `JSONResponse` no sabe serializarlo (habría sido un 500):
  manejador de `RequestValidationError` en `app.py` que da el mismo 422 con los no finitos como texto
  (`sin_no_finitos`, recursiva). `repartir` rechaza Q no finita («sin cantidad»), importe no finito («El importe de la
  línea no es un número…») y una parte no finita («La parte k no tiene cantidad (vacía, 0 o no numérica).»).
- **El signo reescrito (RM5)**: se queda `math.copysign`, ahora detrás de las guardas (`== 0` y `isfinite`), y
  `test_f065_cr1p2_dominio_el_signo_reescrito_es_el_de_antes` lo demuestra ejecutando: sobre una rejilla de Q y parte
  finitas y ≠ 0 (de −1e9 a 1e9, ±1e-9 incluidos) decide igual que `(cantidad > 0) != (q > 0)`, y `NaN`, ±inf, 0 y −0,0
  (en Q y en la parte) los rechazan antes las guardas, que es lo que la reescritura había perdido.
- **O1 (P5)**: `test_f065_p5_una_familia_que_no_suma_avisa_pero_se_aprueba` (dividir 10 en 4 + 6, editar la parte a 5:
  aviso «suman 9; el albarán dice 10» y `set_approved` aprueba).
- **O4 (0,00 €)**: con `importe0 ≠ 0`, una parte que saldría a 0,00 € es 422 «La parte k saldría a 0,00 € (la línea
  tiene X €) y Sigrid no registra líneas de importe 0: repártela en menos partes.» Una línea a 0 € se reparte a 0 y,
  sin `importe0`, manda la fórmula (no hay importe que perder). Elegido el rechazo: es lo más simple y no esconde nada.
- **O3 (texto)**: la descripción de las partes es la que enseña la original: la fijada, la de su línea (contrato o
  derivada) y, solo si no hay, el concepto de la blanca (antes iba el concepto antes que la de su línea). La derivada de
  una parte Nueva lleva la misma. `docs/ARCHITECTURE.md` regla 20 al día (también 0,00 € y no finitos).
- **O2 (producto de una parte Nueva)**: anotado, sin cambio. Sin blanca no hay `tipo_familia`, así que en un documento
  mixto la parte Nueva toma el producto por defecto del documento salvo que se elija (se copia `producto_sigrid`); es
  el comportamiento de F-053 para cualquier Nueva sin blanca.

**RED** (los tests nuevos contra el código de `3516c40`, `pytest tests/test_f065_f3_dividir.py --tb=line`, ficheros
restaurados después) ⇒ **`17 failed, 97 passed`**:
```
:1075  Failed: DID NOT RAISE RepartoInvalido   ×3  (NaN, inf, -inf en una parte)
:1083  Failed: DID NOT RAISE RepartoInvalido       (mensajes de lo no finito)
:1109  Failed: DID NOT RAISE RepartoInvalido       (el signo reescrito: NaN pasaba)
:1129  Failed: DID NOT RAISE ValidationError   ×3  (los tres cuerpos)
:1159  assert 404 == 422                           (dividir con NaN llegaba al servicio)
:1194  assert 200 == 422                       ×3  (editar con NaN/Infinity y traer con -Infinity: 200)
:1202  ImportError: cannot import name 'sin_no_finitos'
:1226  Failed: DID NOT RAISE RepartoInvalido   ×3  (partes a 0,00 €)
:270   AssertionError: assert 'PUERTA EI2-90' == 'PUERTA CORTAFUEGOS EI2-90'   (O3)
```
Los de O1 y los de O3 con descripción fijada o sin la de su línea pasaban ya (guardas de lo que estaba bien).

**Verificación**: `test_f065_f3_dividir.py` **114 passed**; suite de sv4 sola **1218 passed** (44,8 s);
`bash harness/init.sh`: **exit 0**; raíz `1083 passed`; sv4 `1218 passed`; el resto en verde (caché); **`PUERTA COBERTURA: 100.0% de 171 líneas cambiadas cubiertas (171/171, umbral 80%, nivel critico)`**; rutas sensibles N/A; tamaño dentro de topes; **`ENTORNO LISTO. Puedes trabajar.`** (ruff 1254 avisos de deuda previa; los 12 que añadían los tests nuevos, corregidos con `ruff --fix` en el mismo commit).

**Mutación de lo nuevo** `python -m harness.mutacion --feature F-065 --base 3516c40 --rama HEAD --salida
progress/mutacion_F-065_fase3_pasada2.md` (alcance `3516c40..556afae`: 74 líneas de `review_models.py`,
`review_repository.py` y `app.py`): **28 mutantes, 28 muertos, 0 supervivientes, 0 timeouts, 746,8 s**, 4 workers
(líneas base 91,0–94,1 s; media 26,7 s × 4). Sin equivalentes (RM5: la única reescritura, el signo, queda demostrada
arriba). La campaña completa de la fase (`mutacion_F-065_fase3.md`, 99/99 sobre `0606240`) sigue siendo la de T26.
