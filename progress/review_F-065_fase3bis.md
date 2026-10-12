<!-- progress/review_F-065_fase3bis.md -->
Revisión completa (pasada 1) de la fase 3 bis: `cd3baf1..321b572` (lo anterior, aprobado en `review_F-065_fase3.md`)

# F-065 · fase 3 bis (R27 v3, R29 v3; design §5.5; T29–T35) · review

- **Veredicto: CHANGES_REQUESTED** (CR1 regresión de R27, CR2 cabecera «Acciones» no sticky, CR3 campaña a rehacer).
- **Nivel de rigor:** `critico` (declarado en `features.json`). Exige fase RED, cobertura (o N/A con motivo),
  mutación con 0 supervivientes y MANUAL con su comando exacto.
- Alcance según lo aprobado: solo sv4 y solo front (`app.js`, `styles.css`, `document_detail.html`) más tests y docs.

## Verificación ejecutada por el reviewer (resultado real)
- `bash harness/init.sh` (tal cual, worktree, `321b572`): **exit 0**, raíz `1083 passed`, `PUERTA COBERTURA: N/A (F-065
  no cambia líneas Python de producción frente a dev)`, `PUERTA TAMAÑO` dentro, `ENTORNO LISTO`. Init sirvió sv4 **de
  caché**, así que corrí la suite de sv4 sin caché: **1238 passed** (47 s).
- **D1, bloque «Columnas de tabla GENÉRICAS»**: extraído de `860b6c5^` y de `HEAD` (desde la cabecera hasta su `})();`):
  290 líneas cada uno, `diff` **idéntico**. Dentro no hay `F7`, `F6`, `duplic`, `camposBody` ni `standalone`; en todo
  `app.js` solo queda `"F7"` en `wireDividir` y el `lines/standalone` de «Añadir línea», que ya estaba en `cd3baf1`. La
  bandeja vuelve a funcionar: `documents_list.html:89` declara `data-cols-store="sv4.listCols"`, y el bloque la recoge
  con `querySelectorAll('table[data-cols-store]')`. `app.js` se carga desde `base.html`.
- **El `input` de `pick`** sigue llegando a `wireConciliaEdit`, que escucha en el propio input (`app.js:1107`).
  `eligiendo` solo apaga el `open` del combo. Los tests de ratón y de Enter lo comprueban con `avisos: 1`.
- **«Dividir» manda exactamente las cantidades.** `repartoValido` no cambió (sin diff). `enviar` y `cuerpoDivision` mandan
  `cantidades()`, con la última = resto. Comprobado en el test: 6/7/**5** con sus partidas.
- **Fase RED reproducida**: los tests de HEAD contra `app.js`, CSS y plantilla de `cd3baf1` (copia en scratchpad) dan
  **17 failed**. La traza del informe, con su RED de conducta, es coherente.
- **Mutación**:
  - Recalculé el alcance con `harness.alcance.alcance_de_feature('F-065', base='cd3baf1', rama='HEAD')`: `lineas={}`.
    Solo cambian `.py` de tests, así que el 0 es legítimo **por lenguaje** (el generador solo muta Python).
  - Reejecuté **entera** la campaña a mano: el script del informe, sobre una copia de sv4 en scratchpad. Resultado:
    **44 mutantes, 44 muertos, 0 vivos** en 149 s. Línea base de los 3 ficheros: 12–14 s (183 passed). Eso son
    ≈ 3,4 s por mutante con `-x`, coherente.
- **Reproducciones propias** (DOM falso + funciones de `app.js` de cada ref, script en scratchpad): las de CR1 y H1, abajo.

## Checkpoints
- C1 [x] init exit 0 · [x] ficheros del arnés.
- C2 [x] solo F-065 `in_progress` · [x] rama `feature/F-065-lineas-editadas-y-reparto` · [x] `current.md` = sesión
  F-065 (fase 3 bis y MANUAL T35/T27) · [x] sin `done` nuevas.
- C3 [x] hexagonal: no aplica a estático, no hay Python de producción · [x] primera línea con ruta
  (`dom_falso.js`, test, informes) · [x] sin prints (los `console.log` son la salida de los tests con node), sin
  secretos, sin dependencias nuevas · [x] reglas de ARCHITECTURE: regla 20 al día; merge, schema e importes no se tocan.
- C3 bis **N/A**: no toca `docs/referencia/` (0 ficheros en el diff).
- C4 [ ] **requisitos con test que pasa**: R27 «solo admite valores de la lista» se rompe en un camino nuevo y ningún
  test lo vigila (CR1). R29 v3 «Acciones no oculta sus botones»: el test de la cabecera es textual y pasa con una regla
  que no se aplica (CR2) · [x] sin red ni BBDD · [x] MANUAL T35 y T27 en `current.md` con comando.
- C4 bis:
  - [x] rigor `critico` declarado.
  - [x] fase RED con salida real.
  - [x] cobertura N/A, con el motivo impreso por `init.sh`: no cambia Python de producción. El JS lo ejercitan los tests
    con node.
  - [x] informe de la herramienta: alcance vacío recalculado; la herramienta no escribe informe y se sustituyó por
    campaña manual.
  - [x] muertos comprobados: campaña reejecutada entera.
  - [x] el tiempo cuadra.
  - [x] sin «CAMPAÑA NO VÁLIDA».
  - [ ] **RM1**: el informe cita `2380376` abreviado, no el SHA completo. Lo cambiado después (`1c0b76d`..`321b572`) es
    solo documentación, así que el alcance medido sí es el revisado.
  - [x] RM2: coherente (arriba).
  - [ ] **RM3**: «cabecera sin sticky» es equivalente en el navegador y sale MUERTO (CR2/CR3).
  - **RM5 N/A**: no hay equivalentes declarados.
  - **RM6 N/A**: no se quitó ninguna guarda. `resto * q <= 0` es una reescritura equivalente de la misma condición y
    la cubren casos con Q < 0.
  - [ ] **tabla manual**: tiene fichero y texto exacto original→mutado (lo reproduje entero), pero **sin línea ni nº
    de fallos** (CR3).
  - [x] sin supervivientes.
  - [x] «Evidencias» con los cuatro números.
  - [x] los N/A van justificados.
- C4 ter **N/A**: `PUERTA RUTAS SENSIBLES` N/A (no toca rutas declaradas).
- C5 [x] T29–T34 `[x]` con sus commits `F-065 Tn:`. T35, T27 y T28 son MANUAL o posteriores, y es lo esperado ·
  [x] árbol limpio · [x] `features.json` coherente (`in_progress`).

## Cobertura requisito → test (`tests/test_f065_f3bis_front.py` salvo indicación)
| Requisito | Tests |
|---|---|
| R29 v3 F7 sí, F6 no | `r29v3_f7_abre_dividir_y_f6_no`, `_f7_fuera_de_una_fila_no_hace_nada`, `_f7_en_titulos_y_nada_del_duplicar_antiguo`, `_f7_con_la_ventana_abierta_no_la_reinicia`; `test_f065_f3_dividir::r29_js_f7_abre_la_ventana...` |
| R29 v3 última parte automática, roja, «Aceptar» | `r29v3_ultima_parte_se_rellena_sola` (incluye el POST 6/7/5), `_con_decimales_y_negativas`, `_estado_del_reparto`; `repartoValido` con los tests de T24 |
| R29 v3 «Acciones» a la vista | `r29v3_acciones_siempre_a_la_vista` (**textual**, ver CR2), `_acciones_ancho_estable_y_botones_compactos` |
| D1 columnas y bandeja | `r29v3_columnas_el_bloque_esta_cableado`, `_columnas_anchos_orden_y_restablecer` |
| R27 v3 cerrar al elegir | `r27v3_combo_elegir_con_el_raton…`, `_con_enter…`, `_teclear_sigue_abriendo_la_lista` |
| R27 v3 «al» → Almacén | `r27v3_combo_al_marca_almacen_arriba`, `_otro_texto_vuelve_arriba_sin_marcar`, `_que_cuenta_como_almacen` |
| R27 solo valores de la lista | `test_f065_f2_origen` (`partidaValida`, función pura) — **falta la conducta tras elegir (CR1)** |

Sobre los tests con `dom_falso.js`: los del combo y de «Dividir» **prueban conducta**. Ejecutan las funciones reales
de `app.js` con eventos, foco y `fetch` doble, y miran el estado resultante y el cuerpo enviado. Los de CSS y plantilla
son textuales (sin navegador no hay otra), y por eso no ven la cascada (CR2).

## Cambios requeridos
1. **CR1 · Regresión de R27 («solo admite valores de la lista»): `app.js:885-886`, `open(textoNuevo)`.**
   - **Qué pasa**: antes, `pick` reabría el panel. Ahora queda cerrado con el foco dentro. La tecla siguiente llama a
     `open(true)` con `panel.hidden`, y eso **captura lo tecleado como `alAbrir`**: el blur y el Esc «restauran» el
     texto inválido.
   - **Reproducido** (fila con partida vacía; elegir «02.03» con el ratón; teclear «02.0x»; blur):
     - **HEAD ⇒ queda «02.0x»** y la fila se marca con cambios;
     - **`cd3baf1` ⇒ vuelve «02.03»**.
   - **Alcance**:
     - en la fila, «Guardar» mandaría `codigo_partida = "02.0x"`. El servidor no valida contra la obra (design P11):
       sigrid-api lo rechazaría en el alta con `partida_no_encontrada`;
     - en «Dividir» (misma función) iría en el POST `/dividir`;
     - el mismo hueco ya existía en un camino raro (foco → Esc → teclear → blur) y el arreglo debe cubrirlo también.
   - **Arreglo sugerido**: `if (panel.hidden && !textoNuevo) { alAbrir = input.value; }`, o capturar `alAbrir` en
     `focus`.
   - **Tests**, RED primero: elegir y luego teclear inválido + blur ⇒ vuelve la elegida; elegir, teclear y Esc ⇒ vuelve
     la elegida; foco, Esc, teclear y blur ⇒ vuelve la original.
2. **CR2 · La cabecera de «Acciones» no es sticky: `styles.css:1629`.**
   - **Qué pasa**: `.salmon-table thead th[data-col="acciones"]` tiene especificidad (0,2,2) y pierde ante
     `.salmon-table thead tr.salmon-head th` (`styles.css:1515-1517`), que es (0,2,3) y pone `position: relative` y
     `cursor: grab`. El `<tr>` es `class="salmon-head"` (`document_detail.html:695`).
   - **Efecto**: con scroll horizontal, las celdas quedan pegadas a la derecha bajo la cabecera de otra columna, y
     «Acciones» se va con el scroll.
   - **Arreglo**: subir la especificidad, por ejemplo `.salmon-table thead tr.salmon-head th[data-col="acciones"]`.
   - **Test**: uno que falle hoy; por ejemplo, que la regla de la cabecera tenga especificidad ≥ la de la regla
     genérica que fija `position`.
   - **MANUAL T35, paso 5**: añadir «la cabecera “Acciones” sigue encima de sus botones al desplazar en horizontal».
3. **CR3 · Rehacer la campaña a mano tras CR1 y CR2.**
   - **RM3**: el mutante «cabecera sin sticky» quita una declaración que ya perdía la cascada; es equivalente en el
     navegador y salió MUERTO solo porque el test lee texto. Un equivalente muerto invalida la campaña.
   - **Añadir** mutantes de lo nuevo: la guarda de `alAbrir` y el selector.
   - **El informe debe declarar**:
     - el **SHA completo** de HEAD medido (RM1);
     - la línea base de los tres ficheros de tests;
     - por fila: `fichero:línea`, texto original→mutado y **nº de fallos** (sin `-x`, o contándolos).
   - **Inventario**: actualizar la fila de `inventario_mutacion_F-039.md`.

## Observaciones (no bloquean)
- **H1 (gravedad media-alta, previo, no se toca aquí).** Reproducido igual en `cd3baf1` y en HEAD: «02.0», «alba» y
  «puer» + Enter (sin flechas) ⇒ `elegirAlmacen` ⇒ **POST `/almacen` inmediato**.
  - «alba» es el prefijo de «Albañilería»: quien teclea el principio de su partida y pulsa Enter manda la línea a
    almacén sin confirmación.
  - Es reversible antes de aprobar, pero si pasa inadvertido llega al alta de Sigrid sin partida.
  - La MANUAL T35 (paso 4) enseña justo «teclear + Enter», así que conviene que el líder proponga al humano, antes de
    desplegar, que Enter sin marcada elija la primera partida que coincide (o nada). Es un cambio de R27 fuera de lo
    aprobado.
- **O1 · Anchos guardados.** `widths()` guarda todas las columnas al redimensionar una: quien redimensionó antes de T24
  tiene `acciones = 156` en `sv4.salmonCols.width.v1` y no verá los 200. Los botones bajan de línea en vez de
  recortarse, y «↺ Columnas» lo arregla. Mencionarlo en la MANUAL o en la nota de despliegue.
- **O2.** H2 y H3 del informe: de acuerdo. El arranque local usa el árbol principal, y está anotado.

## Automejora (propuesta, no aplicada)
- En `CHECKPOINTS.md` (C4 bis, campaña manual): **un mutante de CSS que solo mata un test textual no cuenta como
  muerto** si no se ha comprobado que la regla gana la cascada; exigir al menos la comparación de especificidad con las
  reglas existentes del mismo elemento. Es lo que dejó pasar CR2 con «44/44».
