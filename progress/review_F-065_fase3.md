<!-- progress/review_F-065_fase3.md -->
Revisión completa (pasada 1) de la fase 3, desde `7b46bd8` (dev con la fase 2) hasta `357732b` (HEAD)

# F-065 · fase 3 (R29–R37, dividir con F6) · review

- **Veredicto: CHANGES_REQUESTED.** Un único cambio (CR1, media), pequeño. Lo demás, incluido todo lo que va a Sigrid,
  está bien y verificado de punta a punta.
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

## Lo que pidió el líder

- **Qué va a Sigrid**: lo comprobé de punta a punta, como se describe arriba.
  - `cantidad_convertida = qk`; `cantidad_albaran = ca0 × qk / Q` mantiene la conversión reproducible con el factor
    copiado; en contenedores no reproducibles se prorratean los m³.
  - Importe `round(importe0 × qk / Q, 2)`; la última parte absorbe el redondeo y la familia suma el original.
- **Deshacer**: una sola entrada; restaura la original, su derivada y la cabecera, y borra las partes y las derivadas
  nuevas. Los tests comparan **toda la BBDD** (`foto`) antes y después en tres repartos y en una Nueva.
- **No se divide**:
  - albarán aprobado (409) o fila bloqueada (409);
  - fila con la marca de unidad (422, D1), huérfana (422, D5), sintética, sin Q;
  - partes 0, nulas, de otro signo o que no suman (422 sin cambios).
  - La plantilla no pinta «Dividir» en esos casos.
- **Aviso de familia (D6)**: compara en la unidad del albarán; es aviso, no bloqueo. R20, O2 y CR3 siguen bloqueando lo
  suyo.
- **F7 eliminado sin romper nada**:
  - fuera `duplicateRow`/`camposBody` (que además mandaba todos los campos, la O6 de la fase 1);
  - F8 se queda;
  - en `app.js`/plantilla no quedan referencias a F7, salvo el comentario que lo explica.
- **D1–D7**: todas razonables.
  - D1 es lo más seguro: una Q en otra unidad no se multiplica en N filas.
  - D2 evita que dos filas compartan derivada.
  - D3 aplica a la parte 1 la misma regla que al editar.
  - D4 lo necesita el deshacer.
  - D5: la traída sí se divide; la huérfana, «revalora».
  - D6 compara en la unidad correcta.
  - D7: no copiar el declarado ni las razones es lo correcto, porque eran de la línea entera.

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
