<!-- progress/review_F-065_fase3.md -->
Revisión incremental desde c1578c2 (pasada 3) hasta `8b940a8`; la 2, de `3516c40`; la 1, completa desde `7b46bd8`

# F-065 · fase 3 (R29–R37, dividir con F6) · review

- **Veredicto (pasada 3, al final): APPROVED.** Antes: CHANGES_REQUESTED por CR1 (pasada 1) y CR1b (pasada 2),
  resueltos.
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

## Cambio requerido en la pasada 1 (resuelto en las pasadas 2 y 3)

1. **CR1 · Media · números no finitos.** La reescritura del signo de `repartir` (`math.copysign`) dejaba pasar `NaN`,
   y los cuerpos JSON (`DivisionBody`, `ConciliacionEditBody`, `TraerLineasBody`) aceptaban `NaN`/`Infinity`. Así se
   escribían `NaN` en cantidades, importes y `total_valorado`, y sv9 habría descartado la línea en silencio. Detalle en
   `git show 3516c40:progress/review_F-065_fase3.md`.

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

## Pasada 2 · incremental desde `3516c40` hasta `1d967bf` (resumen)

Íntegra en `git show c1578c2:progress/review_F-065_fase3.md`. CHANGES_REQUESTED por **CR1b**:
`ConciliacionOverridePayload` («Origen ✎») seguía admitiendo `NaN`. Probado en una copia: la fila se quedaba sin
precio ni importe y el total bajaba de 2120 a 1200. Quedaron resueltos y falseados en una copia:
- CR1 en los tres cuerpos, el manejador del 422 sin el 500 y `repartir` con no finitos;
- el signo reescrito, que equivale en todo lo que llega;
- O1 (familia que no suma y se aprueba), O4 (ninguna parte a 0,00 €) y O3 (el texto de la original).
La mutación de lo nuevo, 28/28, se recalculó y cuadra.

## Pasada 3 · incremental desde `c1578c2` hasta `8b940a8`

- **Veredicto pasada 3: APPROVED.** CR1b resuelto y la auditoría de los cuerpos de escritura es completa. No quedan
  cambios requeridos en la fase 3.
- **Verificación**: `init.sh` exit 0, `PUERTA COBERTURA: 100.0% de 173 líneas (173/173)`; sv4 sin caché **1221
  passed**. Árbol limpio.
- **CR1b, falseado en una copia** (`sv4_copia8`):
  - Sin `allow_inf_nan=False` en `ConciliacionOverridePayload` ⇒ **5 failed**: el test de los cuerpos ×3 más las
    rutas `origen_nan` y `casar_blanca_inf`.
  - Sin él en `ValuationLineUpdate` ⇒ **4 failed**: los cuerpos ×3 más `put_ignoradas_nan`.
  - Las rutas responden 422 `finite_number` sin llamar al servicio, a través del manejador de la pasada 2.
- **Auditoría (comprobada)**: `app.py` tiene **25** rutas `post/put/patch/delete`.
  - Las que llevan cuerpo con números están todas protegidas: `ParteDivision`, `ConciliacionEditBody`,
    `LineaATraer`, `ConciliacionOverridePayload` (`PATCH …/conciliacion` y `POST …/by-merge/{id}/conciliacion`) y
    `ValuationLineUpdate` (PUT).
  - El resto son `Form` de texto, sin cuerpo o `ProductoSigridBody` (texto). Ninguna lee `request.json()` a mano.
    `_parse_optional_float` solo la usan los filtros del listado (GET).
- **`MergeLinePayload` sin proteger es correcto**:
  - Solo entra por `MergeDocumentUpdatePayload.lines` del PUT, y ni el repositorio ni el servicio leen
    `payload.lines` (grep sin resultados).
  - Que el PUT no toca las blancas ni las filas lo fija `test_f065_r1_put_con_las_blancas_no_toca_las_filas`, que
    compara la BBDD entera.
  - Además es el modelo con que se LEEN las blancas (`_merge_line_to_payload`): protegerlo rompería el detalle si una
    fila trajera `NaN`.
  - Un `NaN` ahí se valida y se descarta sin escribir nada.
- **Mutación (RM1)**:
  - Recalculé `c1578c2..HEAD`: **9 líneas, 2 mutantes** (`allow_inf_nan` → `True` en los dos modelos). Coincide.
    Después de `e4ac55a` solo hay estilo en los tests y `progress/`.
  - **No reejecuté la campaña: dura 201,4 s** (2 workers). RM2: 201,4 × 2 ÷ 2 = 201 s, frente a una línea base de
    ~70 s más la propia medición de la base: no es sospechoso, porque está por encima.
  - 0 supervivientes y 0 «sin veredicto». RM5 N/A.
- **Checkpoints**: [x] C1–C5, C4 bis completo (RED `6 failed, 11 passed`). La fase 3 queda pendiente de la MANUAL T27
  del humano (`current.md`), de fusionar, de `init.sh` en el árbol principal, de desplegar solo sv4 y de T28.
