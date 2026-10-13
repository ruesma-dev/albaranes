<!-- progress/review_F-065_fase3bis.md -->
Revisión incremental desde `ee13554` (pasada 3), hasta `8b2d404`; la 2 desde `1bc0e5f`; la 1, completa `cd3baf1..321b572`

# F-065 · fase 3 bis (R27 v3–v4, R29 v3; design §5.5; T29–T38) · review

- **Veredicto (pasada 3, al final): APPROVED.**
  - La pasada 1 fue CHANGES_REQUESTED por CR1, CR2 y CR3; la 2 los dio por resueltos y fue APPROVED.
  - La pasada 3 es H1, aprobado por el humano como R27 v4.
- **Nivel de rigor:** `critico` (declarado). Exige fase RED, cobertura (o N/A con motivo), mutación con 0
  supervivientes y MANUAL con su comando.
- **Alcance:** solo sv4 y solo front (`app.js`, `styles.css`, `document_detail.html`) más tests y docs. La pasada 3
  toca solo `app.js` (`attachPartidaCombo`, que sirve a la fila y a «Dividir»).

## Pasada 1 (resumen; detalle en `1bc0e5f`)
- **`init.sh`** exit 0; sv4 sin caché, 1238 passed. RED reproducido: 17 failed contra `cd3baf1`.
- **D1**: el bloque «Columnas de tabla GENÉRICAS» es **idéntico** al de `860b6c5^` (290 líneas). No trae nada del
  duplicar ni de F7, y la bandeja (`sv4.listCols`) lo vuelve a usar.
- **Comprobado**: `pick` sigue marcando la fila; «Dividir» manda las cantidades exactas (6/7/**5**); `repartoValido` no
  cambió. Campaña 44/44 reejecutada.
- **Pedí tres cambios:**
  - **CR1**: el combo admitía texto fuera de la lista tras elegir.
  - **CR2**: la cabecera de «Acciones» no era sticky, porque perdía ante una regla con especificidad (0,2,3).
  - **CR3**: había un equivalente MUERTO (RM3) y faltaban el SHA, la línea y los fallos por fila.

## Pasada 2 (resumen; detalle en `ee13554`)
- **`init.sh`** exit 0; sv4 sin caché, 1247 passed. RED contra `1bc0e5f`: los 3 de CR1 y el de la cabecera fallan.
- **CR1**: `alAbrir` solo se toma al abrir por foco o clic.
- **CR2**: el selector lleva `tr.salmon-head`.
  - **Medido por mí en Chrome sin cabeza**: con el CSS anterior la cabecera era `relative` y estaba fuera de la caja;
    ahora la cabecera y la celda son `sticky`, pegadas al borde, opacas y encima en 9/9 puntos.
  - **Lo quitado del CSS era equivalente**: el `background` lo pisa la fila, que es más específica; `white-space:
    normal` es el valor heredado; los `z-index` son prescindibles en el orden del DOM. Chrome da las medidas
    idénticas con y sin ellos.
  - **El motor de cascada del test es válido para lo que mira.** Límites: sin longhands y la cadena de antepasados
    acaba en la tabla; los cubrí a mano.
- **CR3**: campaña reejecutada, **57/57 con las 57 filas iguales** (línea y fallos incluidos). RM1:
  `1b605415b0b4dd6f2ca99dfced7d8af94eb8fea0`. El #2 (`dialogo.open`) muere solo en el DOM falso; lo acepto, declarado.

## Pasada 3 · H1 → R27 v4: verificación ejecutada por el reviewer (resultado real)
- **`bash harness/init.sh`** (tal cual, `8b2d404`): **exit 0**, raíz `1083 passed`, `PUERTA COBERTURA: N/A (F-065 no
  cambia líneas Python de producción frente a dev)`, rutas sensibles N/A, `PUERTA TAMAÑO` dentro (150/150, 179/250),
  `ENTORNO LISTO`. sv4 salió de caché, así que lo corrí sin caché: **1259 passed** (77 s).
- **RED**: los tests de HEAD contra `app.js` de `2d64bc2` dan **21 failed, 17 passed**. Son los 19 del informe más los
  2 parametrizados de «borrar lo tecleado», añadidos en `0075ce4`. Casa con la traza del informe.
- **El código, comprobado:**
  - `marcadaAlTeclear(shown, texto)` devuelve 0 si `esAlmacenTecleado`. Si no, 1 si hay texto y alguna partida
    coincide, y -1 en otro caso.
  - Se usa solo con `textoNuevo`; al abrir por foco o clic, `activo` sigue a -1 tras `close`: **ninguna marcada**.
  - El Enter elige `shown[activo]` (con -1, `undefined`: nada; la guarda `activo >= 0` quitada era redundante), con
    `preventDefault` y `stopImmediatePropagation`. Las flechas siguen con `siguienteActivo`.
- **Conducta, reproducida con mi propio script** (DOM falso con las funciones reales de `app.js`):
  - **En la fila** añadí, en el MISMO input y registrado después, un oyente de Enter que cuenta guardados, como hace
    `wireConciliaEdit` (`app.js:1133`, cableado tras `wirePartidaCombos`, `:1185`).
  - Con «zzz», con «02.0x» y con foco sin teclear (valor «01.01»), **dos Enter** dan: **0 guardados, 0 POST
    `/almacen`**, lista abierta, y al salir vuelve «01.01».
  - Con «alba», el primer Enter elige «05.01» y cierra la lista; el segundo guarda la fila, que es lo esperado porque
    el valor es de la lista.
  - **CR1 sigue en pie**: elegir «02.03» con el ratón, teclear «02.0x» y salir ⇒ vuelve «02.03».
  - **En «Dividir»**, con el combo de verdad: teclear «zzz» en la partida 1 y pulsar Enter dos veces ⇒ `enviado =
    null` y los dos Enter quedan prevenidos; al salir vuelve «01.01».
  - Foco y Enter dos veces sin teclear ⇒ `enviado = null`. El test del implementer cubre «alba» + Enter ⇒ «05.01» y
    el Enter siguiente acepta `[6 → 05.01, 12 → 01.01]`; el «Almacén» de la fila nunca se llama desde la ventana.
- **Tests nuevos (`r27v4_*`)**, todos de conducta: «alba», «02.0» y «al» + Enter; sin coincidencias (Enter y al
  salir); foco + Enter, con y sin valor; borrar lo tecleado (`""` y `"   "`); las flechas mandan; la ventana «Dividir»;
  y la función pura como contrato. El de «otro texto» pasó a v4: ahora se marca la primera que coincide.
- **Campaña de la pasada 3**: reejecutada ENTERA sobre una copia de sv4 de HEAD en scratchpad, con el script base del
  informe y la lista `M` de la pasada 3.
  - Línea base `204 passed` (21 s). **15 mutantes, 15 muertos, 0 vivos**, en 5 min 26 s.
  - **Las 15 filas coinciden una a una** con la tabla del informe: `fichero:línea`, original, mutado, **nº de fallos**
    y veredicto (comparación automática).
  - **RM1**: `0075ce4900a27867ec0c1e6c0c80f46dcf5d5711` es `0075ce4`. De ahí a HEAD solo cambian `impl`, `mutacion`,
    `inventario` y `tasks`.
- **RM5, el equivalente #5** (quitar `shown.length > 1`), **demostrado ejecutando por mí**:
  - con el mutante aplicado en la copia, los tres ficheros sin `que_marca_al_teclear` dan **203 passed**: sobrevive;
  - con ese test, **1 failed** (`[1, 1, 0, 0, 0, 1, …] != [1, 1, 0, 0, 0, -1, …]`).
- **Por qué es equivalente en el combo**: sin coincidencias, `shown` solo tiene «Almacén»; la posición 1 no existe
  (`render` no marca nada y `shown[1]` es `undefined`), y con las flechas `siguienteActivo` lleva el 1 y el -1 al 0.
- **RM3, mismo criterio que el #2 de la pasada 2**: lo mata un test que fija el **contrato de la función** (-1 =
  ninguna), no un test textual, y el informe lo declara. Lo acepto, y no lo trato como equivalente muerto.

## Checkpoints (estado final)
- C1 [x] init exit 0 · [x] ficheros del arnés.
- C2 [x] solo F-065 `in_progress` · [x] rama `feature/F-065-lineas-editadas-y-reparto` · [x] `current.md` = sesión
  F-065 · [x] sin `done` nuevas.
- C3:
  - [x] hexagonal: no aplica a estático, no hay Python de producción.
  - [x] primera línea con ruta.
  - [x] sin prints (los `console.log` son la salida de los tests con node), sin secretos, sin dependencias.
  - [x] regla 20 de ARCHITECTURE al día (R27 v4).
- C3 bis **N/A**: no toca `docs/referencia/`.
- C4 [x] cada requisito con test que pasa (tabla) · [x] sin red ni BBDD · [x] MANUAL en `current.md` (paso 4 bis de
  T35 para R27 v4; T35 hecha por el humano).
- C4 bis:
  - [x] rigor `critico`.
  - [x] fase RED con salida real, en las tres pasadas.
  - [x] cobertura N/A con el motivo impreso: sin Python de producción.
  - [x] alcance de la herramienta vacío por lenguaje (recalculado en la pasada 1).
  - [x] campañas manuales reejecutadas enteras · [x] el tiempo cuadra · [x] sin «NO VÁLIDA».
  - [x] RM1, RM2 y RM3 (arriba).
  - [x] RM5: el equivalente #5, reproducido.
  - **RM6 N/A**: no se quitó ninguna guarda defensiva; `activo >= 0` era redundante, porque `shown[-1]` es
    `undefined`, y `if (elegido)` sigue.
  - [x] tablas con línea, texto exacto y fallos · [x] 0 supervivientes · [x] «Evidencias» · [x] N/A justificados.
- C4 ter **N/A**: la puerta de rutas sensibles da N/A.
- C5:
  - [x] T29–T38 `[x]` con sus commits `F-065 Tn:`; T35 hecha por el humano. T27 y T28 son MANUAL o posteriores.
  - [x] árbol limpio · [x] `features.json` (`in_progress`).

## Cobertura requisito → test (`tests/test_f065_f3bis_front.py` salvo indicación)
| Requisito | Tests |
|---|---|
| R29 v3 F7 sí, F6 no | `r29v3_f7_*` (4); `test_f065_f3_dividir::r29_js_f7_abre_la_ventana...` |
| R29 v3 última parte automática, roja, «Aceptar» | `r29v3_ultima_parte_*` (incluye el POST 6/7/5), `r29v3_estado_del_reparto`; `repartoValido` (T24) |
| R29 v3 «Acciones» a la vista | `cr2_la_cabecera_…_gana_la_cascada`, `cr2_la_celda_…_gana_la_cascada`, `r29v3_acciones_*` |
| D1 columnas y bandeja | `r29v3_columnas_el_bloque_esta_cableado`, `r29v3_columnas_anchos_orden_y_restablecer` |
| R27 v3 cerrar al elegir, «al» → Almacén | `r27v3_combo_*`, `r27v3_que_cuenta_como_almacen`, `cr1_tras_elegir_teclear_vuelve_a_abrir_la_lista` |
| R27 v4 marcada y Enter (fila y «Dividir») | `r27v4_*` (12 tests, 13 casos) |
| R27 solo valores de la lista | `cr1_*` (5), `r27v4_sin_coincidencias_*`; `test_f065_f2_origen` (`partidaValida`) |

## Observaciones (no bloquean)
- **O1 · Anchos guardados** (`acciones` a 156 px): anotado en la MANUAL; «↺ Columnas» lo arregla.
- **O3 · «Dividir», «Almacén» y luego texto inválido.** En la ventana, elegir «Almacén» deja la partida vacía sin
  actualizar `alAbrir`. Si luego se teclea algo inválido y se sale, vuelve la partida de antes. Sigue siendo un valor de
  la lista.
- **O4 · El código exacto no tiene prioridad (R27 v4).** La marcada es la PRIMERA que coincide por código **o
  descripción**, en el orden de sigrid-api. Si una partida anterior lleva el texto en la descripción, teclear un código
  exacto y pulsar Enter elegiría esa otra. La marcada se ve antes del Enter, y es lo que pidió el humano. Si molesta en
  la práctica, la mejora es priorizar el código exacto o el prefijo de código.
- **O5 · Teclado en la fila.** Con foco en la partida y sin teclear, el primer Enter ya no guarda la fila: la lista
  está abierta y no hay marcada. Hay que pulsar Esc y luego Enter. Es la consecuencia buscada de «sin marcada, nada»
  (el humano lo ha aprobado); conviene decirlo al desplegar.

## Automejora (propuesta de la pasada 1, sigue en pie)
- En `CHECKPOINTS.md` (C4 bis, campaña manual): un mutante de CSS que solo mata un test textual no cuenta como muerto;
  exigir un test de cascada o una medida en navegador.
