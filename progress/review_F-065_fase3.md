<!-- progress/review_F-065_fase3.md -->
Revisión incremental desde 3516c40 (pasada 2) hasta `1d967bf`; la pasada 1 fue completa, de `7b46bd8` a `357732b`

# F-065 · fase 3 (R29–R37, dividir con F6) · review

- **Veredicto (pasada 2, al final): CHANGES_REQUESTED** por CR1b, que es CR1 en un cuarto cuerpo que no vi. La
  pasada 1 lo fue por CR1.
- **Nivel de rigor:** `critico` (declarado). Exige fase RED, cobertura ≥ 80 %, mutación con 0 supervivientes sin
  justificación aceptada y MANUAL con su comando exacto.
- Servicios: sv4 (código) y sv9 (solo test). Sin DDL. `azure-apps` `a9aa68d` y `ARCHITECTURE.md` regla 20 al día.

## Verificación ejecutada por el reviewer (resultado real)
- `bash harness/init.sh`: **exit 0**, raíz `1083 passed`, `PUERTA COBERTURA: 100.0% de 147 líneas (147/147)`,
  `ENTORNO LISTO`. Sin caché: **sv4 1196 passed**, **sv9 534 passed**. Árbol limpio.
- **De punta a punta, sv4 → sv9** (copia `sv4_copia6` + validador real de sv9, con las filas leídas como las lee
  `SQL_LINEAS` y montadas con `_linea_de_fila` de sv9). Tres divisiones:
  - fila Contrato 10 ud en 6 (su partida), 3 (otra) y 1 (almacén);
  - fila t→kg reproducible (2 t = 2000 kg) en 1200 (su partida) y 800 (otra);
  - fila de contenedores no reproducible (6 m³ = 2 cont.) en 1 (almacén) y 1 (otra).
- **Resultado de esas divisiones:** sv9 admite las 7 líneas, y cada parte va como debe:
  - vinculadas en Q con su `ctrpro`: 1200 kg a 0,05; 6 y 1 ud a 115, la de almacén con `partida None`;
  - Nuevas sin vincular, con `MA9999`, su descripción y la cantidad del albarán prorrateada: 3 UD, **0,8 T** a 50, 3 M3
    a 40;
  - **Σ cantidad × precio = 1490,00 = `total_valorado`.** Todas las partes llevan `descripcion_linea` (CR1 de la fase 2).
- **R36 de sv9 falseado en una copia** (`lineas_a_registrar` descarta las filas sin blanca): `-k r36` ⇒ **4 failed**,
  por ejemplo `['12','13'] == ['12','13','31','32']`. Los tests de contrato vigilan de verdad.
- **Una familia que no suma no bloquea (P5)** (copia): divido 10 en 6 + 4 y bajo la parte 1 a 3. La ficha avisa «Las
  partes de la línea 2 suman 9; el albarán dice 10» y `set_approved` ⇒ `True`.
- **Mutación (RM1)**:
  - Recalculé `7b46bd8..rama`: **4 ficheros, 569 líneas, 99 mutantes** (4 + 33 + 58 + 4). Coincide con el informe.
  - Desde `0606240` solo cambian `progress/` y `tasks.md`.
  - **No reejecuté la campaña: dura 2780,6 s según el informe.**
  - RM2: 2780,6 × 4 ÷ 99 = **112,3 s por mutante** frente a una línea base de 110,9–115,5 s; coherente.
  - Ni «no válida» ni «sin veredicto». RM5 N/A. RM6: no se quitó ninguna guarda.
  - **RM3 / equivalentes:** uno de los cuatro reescritos no es equivalente para todas las entradas (CR1).

## Cambio requerido

1. **CR1 · Media · números no finitos.** La reescritura del «equivalente» del signo admite `NaN`, y los cuerpos JSON
   aceptan `NaN`/`Infinity`.
   - **El cambio de comportamiento**: la primera versión de `repartir` rechazaba un `NaN` con Q positiva:
     `(NaN > 0) != (q > 0)`. La reescrita (`review_models.py:850`, `math.copysign`) lo deja pasar. Se reprodujo:
     `repartir(q=10, …, partes=[nan, 10])` ⇒ `ParteCalculada(cantidad_convertida=nan, …, importe=nan)`, sin error.
   - **Por qué llega**: `DivisionBody.model_validate_json('{"partes":[{"cantidad":NaN},{"cantidad":1}]}')` **lo
     acepta**. `_numero_es` solo filtra lo que llega como texto.
   - **Ya pasaba desde la fase 1**, que se me escapó en su review:
     - `ConciliacionEditBody` acepta `{"cantidad": NaN}`;
     - `TraerLineasBody` acepta `Infinity`.
   - **El efecto en BBDD**: escribe `NaN` en cantidades, importe y `total_valorado`. sv9 descartaría la línea en
     silencio, porque `abs(NaN) > ε` es falso.
   - **Alcance**: el front nunca lo manda (`JSON.stringify(NaN)` es `null`); hace falta una petición hecha a mano. Es
     barato de cerrar y el nivel es `critico`.
   - **Qué hacer**:
     - `allow_inf_nan=False` (o `math.isfinite` en `_numero_es` también para números) en `ParteDivision`,
       `ConciliacionEditBody` y `LineaATraer` ⇒ 422;
     - una guarda `math.isfinite` en `repartir`, para el dominio puro;
     - tests de los tres cuerpos y del dominio.

## Lo que pidió el líder (pasada 1, resumen; íntegro en `git show 3516c40:progress/review_F-065_fase3.md`)

- **Sigrid**: lo comprobé de punta a punta (arriba). Cantidades `qk` y `ca0 × qk / Q`; importes prorrateados, con la
  última parte absorbiendo el redondeo.
- **Deshacer**: una entrada; los tests comparan la BBDD entera antes y después.
- **No se divide**: aprobado o bloqueada (409); con la marca de unidad, huérfana, sintética, sin Q o con partes
  inválidas (422).
- **Lo demás**: el aviso de familia no bloquea (P5); F7 fuera y F8 se queda; D1–D7 razonables.

## Checkpoints

- **C1** [x] `init.sh` exit 0 · [x] ficheros del arnés.
- **C2** [x] una sola `in_progress` · [x] rama de la feature · [x] `current.md` al día con T27.
- **C3** [x] hexagonal: `repartir` es pura en el dominio; el repositorio, el servicio y la ruta solo la usan · [x]
  primera línea con ruta · [x] sin debug, secretos ni dependencias nuevas.
- **C3 · trampas**: [x] (1) merge; [x] (2) sin esquema nuevo (`line_kind = 'reparto'` sin CHECK; lectores: sv4 y sv9
  vía `SQL_LINEAS`, que no filtra por `line_kind`); [x] (3) cantidades: sin mezclar unidades.
- **C3 bis / C4 ter** N/A: no toca `docs/referencia/` y, según la puerta, ninguna ruta sensible.
- **C4** [x] R29–R36 con `test_f065_r29…r36_*`: 92 en sv4 y 4 en sv9, en verde · [x] sin red ni BBDD · [x] MANUAL T27
  en `current.md` con su comando.
- **C4 bis**:
  - [x] RED real (`81 failed, 2 passed`, y la ruta repetida aparte: `15 failed, 1 passed`) · [x] cobertura 147/147 ·
    [x] mutación recalculada · [x] RM1/RM2/RM6 · RM5 N/A · [x] Evidencias con 4 workers.
  - **[ ] RM3/equivalentes: el reescrito del signo cambia el comportamiento con `NaN` (CR1).**
- **C5** [x] T21–T26 `[x]` con un commit `F-065 Tn:` por tarea · [x] árbol limpio · [x] `features.json` = `in_progress`.

## Observaciones (no bloquean)

1. **Baja · falta un test de P5.** Ninguno fija que una familia que no suma se aprueba. Mi prueba lo confirma, pero
   conviene dejarlo escrito.
2. **Baja · producto de una parte Nueva.** Sin blanca no tiene `tipo_familia` (sv9 lo saca de `contexto_linea_json` de
   la blanca). En un documento mixto, la parte toma el producto comodín y no el de la familia de su línea, salvo que se
   elija producto (se copia `producto_sigrid`).
3. **Baja · cosmético.** Una parte Contrato hereda como `descripcion_linea` el concepto de la blanca (p. ej. «PUERTA
   EI2-90»), mientras su original enseña la descripción del contrato. Para sv9 da igual (va vinculada), pero en la
   ficha la familia sale con dos textos.
4. **Info · importes diminutos.** Con importes muy pequeños, una parte puede quedar a 0,00 €, y sv9 no registra las de
   importe 0 (F-053 R13). Es irrelevante en la práctica.

## Automejora (propuesta, no aplicada)

- `reviewer.md` (RM3): cuando un «equivalente» se elimina reescribiendo el código, probar la reescritura también con
  entradas límite que el resto del código no filtra (`NaN`, `±inf`, `-0.0`). «Inalcanzable» suele significar «no lo
  manda la UI».

## Pasada 2 · incremental desde `3516c40` hasta `1d967bf`

- **Veredicto pasada 2: CHANGES_REQUESTED** por **CR1b** (media, una línea y su test). Lo demás está resuelto.
- **Verificación**: `init.sh` exit 0, `PUERTA COBERTURA: 100.0% de 171 líneas (171/171)`; sv4 sin caché **1218
  passed**.
- **Mutación (RM1)**:
  - Recalculé `3516c40..HEAD`: **74 líneas, 28 mutantes** (23 + 2 + 3), los mismos sobre el SHA medido `556afae`.
    Después solo hay estilo en los tests y `progress/`.
  - **No reejecuté la campaña: dura 746,8 s.** RM2: 746,8 × 4 ÷ 28 = 106,7 s frente a una línea base de 91–94 s;
    coherente.
- **Lo resuelto**, cada punto falseado en una copia (`sv4_copia7`) contra `test_f065_f3_dividir.py`:
  - **CR1, los tres cuerpos**: `allow_inf_nan=False` ⇒ 422. Quitado en `ParteDivision`: 4 failed.
  - **CR1, el manejador del 422**: devuelve los no finitos como texto, sin el 500 de `JSONResponse`. Quitado: 4 failed.
  - **CR1, `repartir`**: rechaza Q, importe y partes no finitos. Sin `isfinite` en la parte: 3 failed.
- **El signo reescrito (RM5)**:
  - El test ejecuta una rejilla de finitos ≠ 0 frente a `(cantidad > 0) != (q > 0)`, y `NaN`, ±inf y ±0 quedan
    rechazados antes por las guardas.
  - Además es exacto: para un `x` finito y ≠ 0, `copysign(1, x) = 1` ⇔ `x > 0`. Equivale en todo lo que llega.
- **Los otros puntos**:
  - **O1**: `test_f065_p5_una_familia_que_no_suma_avisa_pero_se_aprueba`.
  - **O4 (ninguna parte a 0,00 €)**: 422 con mensaje que dice la parte y el importe. Quitada la guarda: 3 failed.
  - **O3**: las partes llevan el texto que enseña la original (la fijada, luego la de su línea, luego el concepto). Con
    el orden viejo: 1 failed.
  - **O2**: anotado sin cambio; es el comportamiento de F-053 para toda Nueva sin blanca. Razonable.

### CR1b · Media · `ConciliacionOverridePayload` («Origen ✎») sigue admitiendo `NaN`

- Es el mismo defecto que CR1, en el cuerpo de `PATCH …/conciliacion`. Tiene `precio_unitario: float | None`
  (`review_models.py:396`, sin `allow_inf_nan=False`), y la ruta (`app.py:1428`) lo pasa a `set_line_conciliacion`.
- Mi lista de CR1 nombraba tres cuerpos y se me pasó este; es de las escrituras el único con números que quedaba
  (los filtros del listado solo leen).
- Reproducido en la copia: `{"mode": "nueva", "precio_unitario": NaN}` se valida. La fila 11 se queda sin precio ni
  importe (SQLite guarda `NaN` como NULL) y el total baja de 2120 a 1200.
- En PostgreSQL quedaría `NaN`, que R20 no ve como vacío, y sv9 descartaría la línea en silencio.
- La UI no lo manda (el selector solo envía `mode` y la línea). **Qué hacer**: el mismo `model_config` en
  `ConciliacionOverridePayload`, y añadirlo al test de los cuerpos y al de la ruta, que debe dar 422 sin 500.

