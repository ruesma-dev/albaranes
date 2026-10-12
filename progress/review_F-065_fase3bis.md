<!-- progress/review_F-065_fase3bis.md -->
Revisión incremental desde `1bc0e5f` (pasada 2), hasta `c28964c`; la pasada 1, completa: `cd3baf1..321b572`

# F-065 · fase 3 bis (R27 v3, R29 v3; design §5.5; T29–T35) · review

- **Veredicto (pasada 2, al final): APPROVED.** La pasada 1 fue CHANGES_REQUESTED por CR1, CR2 y CR3; los tres están
  resueltos y verificados por mí.
- **Nivel de rigor:** `critico` (declarado). Exige fase RED, cobertura (o N/A con motivo), mutación con 0
  supervivientes y MANUAL con su comando.
- **Alcance aprobado:** solo sv4 y solo front (`app.js`, `styles.css`, `document_detail.html`) más tests y docs. H1
  sigue sin tocar, pendiente del humano (abajo).

## Pasada 1 (resumen; detalle en `1bc0e5f`)
- `init.sh`: exit 0; sv4 sin caché 1238 passed. RED reproducido: **17 failed** contra el código de `cd3baf1`.
- **D1 verificado**: el bloque «Columnas de tabla GENÉRICAS» es **idéntico** al de `860b6c5^` (290 líneas, `diff`
  vacío) y no trae nada del duplicar ni de F7. La bandeja (`sv4.listCols`) lo vuelve a usar.
- **Comprobado**: el `input` de `pick` sigue marcando la fila; «Dividir» manda las cantidades exactas (6/7/**5**);
  `repartoValido` no cambió. Campaña 44/44 reejecutada entera, con los mismos totales.
- **Cambios pedidos:**
  - **CR1**: tras elegir, lo tecleado pasaba a ser «el valor de antes», y el blur o el Esc dejaban un texto fuera de la
    lista (rompía R27).
  - **CR2**: la cabecera de «Acciones» perdía la cascada ante `.salmon-table thead tr.salmon-head th` (0,2,3) y no era
    sticky.
  - **CR3**: «cabecera sin sticky» era un equivalente MUERTO (RM3); además faltaban el SHA completo, la línea y los
    fallos por fila.

## Pasada 2 · verificación ejecutada por el reviewer (resultado real)
- **`bash harness/init.sh`** (tal cual, `c28964c`): **exit 0**, raíz `1083 passed`, `PUERTA COBERTURA: N/A (F-065 no
  cambia líneas Python de producción frente a dev)`, rutas sensibles N/A, tamaño dentro, `ENTORNO LISTO`. Init sirvió
  sv4 de caché, así que lo corrí sin caché: **1247 passed** (39 s).
- **RED de la pasada 2**: los tests de `c28964c` contra `app.js` y `styles.css` de `1bc0e5f` (copia en scratchpad),
  `-k "cr1 or cr2"` ⇒ **4 failed, 5 passed**.
  - Fallan: los tres de CR1 (blur, Esc, y foco→Esc→teclear) y el de la cabecera.
  - Pasan los de control y el de «pinchar en la casilla», que solo mata el mutante #29.
- **CR1** (`app.js:890`, `if (panel.hidden && !textoNuevo)`): `alAbrir` solo se toma al abrir por foco o clic.
  Cubre los tres caminos y el control «lo válido se queda». `dom_falso.js` gana `blur()` (el foco pasa a `body` antes
  del evento, como en el navegador). En la fila, «Almacén» recarga la página: el `alAbrir` viejo no estorba. **Resuelto.**
- **CR2, comprobado por mi cuenta en Chrome sin cabeza.**
  - **Montaje**: página con el `styles.css` real y la estructura de la plantilla: `tr.salmon-head`,
    `tr.conciliacion-row`, `td.concilia-td.td-acciones`, un `.combo` (relativo) en la partida y 3 filas. Tabla de
    1460 px en una caja de 700 px.
  - **Medida**: `getComputedStyle`, `getBoundingClientRect` y `elementFromPoint` (9 puntos), con `scrollLeft` 0 y 300.
  - **CSS de `1bc0e5f`**: cabecera `relative`, con el borde derecho en 1461 px y luego en 1161 px, frente a los 700 px
    de la caja. **CR2 era real.**
  - **CSS de HEAD**: cabecera y celda `sticky` a 700 px con y sin desplazar; fondo `rgb(247, 244, 245)`;
    `white-space: normal`; la columna encima en **9/9** puntos.
- **Lo quitado del CSS era de verdad equivalente:**
  - **`background` de la celda**, (0,2,1): siempre pierde ante `tr.conciliacion-row > td.concilia-td`, (0,2,2), que
    casa con toda celda de «Acciones». La única está en la `<tr class="conciliacion-row …">` de
    `document_detail.html:720`. Zebra y hover también son opacos (`--paper-soft` #fafbfb, `--brand-soft` #f7eaee).
  - **`white-space: normal`**: es el valor heredado. Repasé las 17 reglas con `nowrap` de `styles.css` y ninguna cae en
    la celda ni en sus antepasados (`.table thead th`, `.combo-item`, `.linea-rev …`, `#lines-table td.line-index-cell`,
    etc.).
  - **Los dos `z-index`**: una sticky crea su propio contexto de apilamiento. Lo que puede quedar debajo (otras celdas,
    los `.combo` relativos de la misma fila y las cabeceras relativas) va antes en el DOM. El `.combo-panel` es `fixed`
    con `z-index: 1000` y sigue encima.
  - **Chrome lo confirma**: con HEAD más los dos `z-index` repuestos, las medidas salen **idénticas** a las de HEAD.
- **Validez del motor de cascada del test** (`test_f065_cr2_*`): calcula bien la especificidad con `#`, `.`, `[]` y
  etiquetas, los combinadores ` ` y `>`, y el orden a igual especificidad. Lo autocomprueba
  `test_f065_cr2_el_motor_de_cascada_se_comporta`.
  - **Límites declarados en el test**: sin `!important`; las pseudoclases, `+`, `~` y los atributos con otro operador
    no casan; las `@media` cuentan como si aplicaran. **Los que añado yo**: solo mira la propiedad pedida, sin
    longhands (una `background-color` no la ve), y la cadena de antepasados acaba en la tabla.
  - Ninguno de esos límites cambia lo que se vigila aquí: no hay `background-color` en estas celdas y los `nowrap` los
    repasé a mano (arriba).
  - Es un **test de conducta de la cascada**, no de forma; los 12 mutantes de CSS mueren también sin los dos tests
    textuales.
- **CR3 · campaña reejecutada ENTERA** con el script del informe, sobre una copia de sv4 de HEAD en scratchpad:
  línea base `192 passed` (9,4 s); **57 mutantes, 57 muertos, 0 vivos, 0 sin aplicar**, en 9 min 22 s (≈ 10 s por
  mutante sin `-x`, coherente).
  - **Las 57 filas coinciden una a una** con la tabla del informe: `fichero:línea`, original, mutado, **nº de fallos**
    y veredicto (comparación automática).
  - **RM1**: `1b605415b0b4dd6f2ca99dfced7d8af94eb8fea0` es `1b60541`. De ahí a HEAD solo cambian `impl`, `mutacion` e
    `inventario`.
- **RM3, revisado mutante por mutante en lo nuevo de CSS:**
  - Ninguno es equivalente:
    - sin `right: 0` la sticky no se pega;
    - sin `cursor: default` gana `grab`;
    - sin `overflow: visible` gana el `hidden` de `.salmon-table td.concilia-td`;
    - sin `text-align: right` los botones van a la izquierda;
    - con `nowrap` en la celda los botones ya no bajan de línea.
  - **Caso límite, el #2** (quitar `dialogo.open` de la guarda de F7): en un navegador actual, `showModal` deja la
    ficha inerte y el foco no puede estar en una fila con la ventana abierta. Muere en el DOM falso, que no modela
    `inert`.
  - **Lo acepto y no lo trato como equivalente muerto**: la guarda sí cambia la semántica de JS en cualquier DOM donde
    ese estado sea alcanzable, es código de la fase 3 y el informe lo declara (nota del #2). En la pasada 1, en
    cambio, la declaración no tenía efecto en ningún modelo.
- **MANUAL T35**: `current.md` añade los pasos de «texto fuera de la lista tras elegir» y «cabecera encima al
  desplazar», y la nota O1 (anchos guardados).

## Checkpoints (estado final)
- C1 [x] init exit 0 · [x] ficheros del arnés.
- C2 [x] solo F-065 `in_progress` · [x] rama `feature/F-065-lineas-editadas-y-reparto` · [x] `current.md` = sesión
  F-065 · [x] sin `done` nuevas.
- C3 [x] hexagonal: no aplica a estático, no hay Python de producción · [x] primera línea con ruta · [x] sin prints
  (los `console.log` son la salida de los tests con node), sin secretos, sin dependencias · [x] regla 20 de
  ARCHITECTURE al día; merge, schema e importes no se tocan.
- C3 bis **N/A**: no toca `docs/referencia/`.
- C4 [x] cada requisito con test que pasa (tabla) · [x] sin red ni BBDD · [x] MANUAL T35 y T27 con su comando.
- C4 bis:
  - [x] rigor `critico` · [x] fase RED con salida real, en las dos pasadas.
  - [x] cobertura N/A con el motivo impreso: no cambia Python de producción; el JS lo ejercitan los tests con node.
  - [x] alcance de la herramienta recalculado: `alcance_de_feature(..., base='cd3baf1')` ⇒ `lineas={}`, un 0 legítimo
    por lenguaje.
  - [x] campaña manual reejecutada entera · [x] el tiempo cuadra · [x] sin «NO VÁLIDA» · [x] RM1, RM2 y RM3 (arriba).
  - **RM5 N/A**: no hay equivalentes declarados.
  - **RM6 N/A**: no se quitó ninguna guarda; lo quitado es CSS sin efecto, demostrado arriba.
  - [x] tabla manual con línea, texto exacto y fallos · [x] 0 supervivientes · [x] «Evidencias» · [x] N/A justificados.
- C4 ter **N/A**: la puerta de rutas sensibles da N/A.
- C5 [x] T29–T34 `[x]` con sus commits `F-065 Tn:`; las de la pasada 2 son commits de review, como en las fases
  anteriores. T35, T27 y T28 son MANUAL o posteriores · [x] árbol limpio · [x] `features.json` (`in_progress`).

## Cobertura requisito → test (`tests/test_f065_f3bis_front.py` salvo indicación)
| Requisito | Tests |
|---|---|
| R29 v3 F7 sí, F6 no | `r29v3_f7_*` (4); `test_f065_f3_dividir::r29_js_f7_abre_la_ventana...` |
| R29 v3 última parte automática, roja, «Aceptar» | `r29v3_ultima_parte_*` (incluye el POST 6/7/5), `r29v3_estado_del_reparto`; `repartoValido` (T24) |
| R29 v3 «Acciones» a la vista | `cr2_la_cabecera_de_acciones_gana_la_cascada`, `cr2_la_celda_de_acciones_gana_la_cascada`, `r29v3_acciones_*` |
| D1 columnas y bandeja | `r29v3_columnas_el_bloque_esta_cableado`, `r29v3_columnas_anchos_orden_y_restablecer` |
| R27 v3 cerrar al elegir, «al» → Almacén | `r27v3_combo_*` (5), `r27v3_que_cuenta_como_almacen`, `cr1_tras_elegir_teclear_vuelve_a_abrir_la_lista` |
| R27 solo valores de la lista | `cr1_*` (blur, Esc, foco-Esc, pinchar, válida se queda); `test_f065_f2_origen` (`partidaValida`) |

## Observaciones (no bloquean)
- **H1 (gravedad media-alta, previo; reproducido igual en `cd3baf1` y HEAD).** Teclear sin flechas «02.0», «alba» o
  «puer» y pulsar Enter ⇒ `elegirAlmacen` ⇒ **POST `/almacen` inmediato**.
  - Es reversible antes de aprobar, pero si nadie lo ve llega al alta de Sigrid sin partida.
  - La MANUAL T35 enseña «teclear + Enter». **Recomiendo que el líder lo proponga al humano antes de desplegar**: que
    Enter sin marcada elija la primera partida que coincide, o nada.
- **O1 · Anchos guardados** (`acciones` a 156 px): anotado en la MANUAL; «↺ Columnas» lo arregla.
- **O3 · «Almacén» en «Dividir» y luego texto inválido.** En la ventana, elegir «Almacén» deja la partida vacía sin
  actualizar `alAbrir`. Si luego se teclea algo inválido y se sale, vuelve la partida de antes, no la vacía. Sigue
  siendo un valor de la lista, así que R27 se cumple; es un caso menor de experiencia de uso.

## Automejora (propuesta de la pasada 1, sigue en pie)
- En `CHECKPOINTS.md` (C4 bis, campaña manual): un mutante de CSS que solo mata un test textual no cuenta como muerto;
  exigir un test de cascada (como el motor de esta fase) o una medida en navegador. Sin ello, «44/44» escondía CR2.
