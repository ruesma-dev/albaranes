<!-- progress/impl_F-065_fase3bis.md -->
# F-065 · fase 3 bis (T29–T34) · informe del implementer

Rama `feature/F-065-lineas-editadas-y-reparto` (worktree `../albaranes-F-065`, desde `cd3baf1` = lo fusionado en `dev`
como `f83acd4`). Rigor `critico`. Plan aprobado por el humano en la PARADA 1 (2026-10-12) más el dato del humano sobre
«Acciones» que llegó a mitad del trabajo (abajo, punto 5). **Solo sv4 y solo front**: `static/app.js`,
`static/styles.css`, `templates/document_detail.html` y tests. **Nada de servidor** (no hizo falta). Despliegue: solo sv4.

## 1. Commits

`6f0221f` spec v3 (R27, R29; design §5.5) y tareas T29–T35 · `420712d` T29 RED · `bef1ad1` T30 F7 · `bcff0af` T31 última
parte · `9cffa6c` T32 combo · `bb3d250` T33 Acciones y columnas · `2380376` T34 supervivientes de la mutación cerrados ·
`1c0b76d` T34 ARCHITECTURE y MANUAL · el commit de este informe (y `progress/mutacion_F-065_fase3bis.md`).

## 2. Qué cambió

1. **F7 divide, F6 no** (R29 v3). El `keydown` de `wireDividir` escucha `"F7"`; F6 ya no se intercepta (sin
   `preventDefault`: es del navegador). «(F7)» en el `title` del botón, comentarios de plantilla, CSS y JS. Del duplicar
   antiguo no queda nada (`duplicateRow`, `camposBody`, «Duplicar»: comprobado por test); el único otro atajo es F8.
2. **La última parte se rellena sola** (R29 v3). `faltaPorRepartir` redondea a 1e-6 (antes 1e-3: ahora es la cantidad
   que se manda, no un aviso). Nueva `estadoReparto(q, demás)` → `{resto, ultimaMal, mensaje}`: rojo si `resto · Q ≤ 0`
   (0 o de otro signo); mensajes «Reparto completo.», «Sobra: X», «La última parte quedaría a 0.», «Falta la cantidad de
   la parte k.», «La parte k no puede ser 0 ni de otro signo.». En la ventana, el input de la última es `readOnly`,
   `tabIndex = -1`, clase `dividir-auto` (gris, cursiva) y `dividir-resto-mal` (rojo) cuando toca; `refrescar` lo
   rellena en cada tecla y al cambiar N, que conserva solo las editables (no el resto viejo). **«Aceptar» sigue con
   `repartoValido` sobre todas**, sin cambios. Texto de la ventana: «…; la última se rellena sola con lo que falta.»
3. **El combo de partida no se reabre al elegir** (R27 v3). Diagnóstico confirmado con un test que lo reproduce (§4):
   `pick` despachaba `input` y el oyente de `input` del propio combo llamaba a `open()`. Ahora `pick` marca
   `eligiendo` mientras despacha y ese oyente lo ignora; el `input` sigue llegando a `wireConciliaEdit` (la fila queda
   con cambios: test). Vale también para la ventana «Dividir» (es la misma función).
4. **«Almacén» siempre localizable** (R27 v3). Hipótesis confirmada y **otra causa más**: además del `scrollTop`
   conservado, `activo` conservaba la POSICIÓN marcada al filtrar, que tras teclear apuntaba a otra partida; con «al»
   tras bajar 3 con flechas, Enter elegía «04.02 · Saneamiento general» (traza RED, §4). Ahora `open(textoNuevo)`: con
   texto nuevo, `scrollTop = 0` y la marcada es «Almacén» si `esAlmacenTecleado` (prefijo de «almacen» sin acentos ni
   mayúsculas, o lo trae entero: «a», «al», «alm», «Almacén (sin partida)») y, si no, ninguna. Al enfocar o pinchar,
   como antes.
5. **«Acciones» siempre a la vista.** Lo que encontré: **T24 (fase 3, `860b6c5`) borró por error el bloque entero
   «TANDA 2B — Columnas de tabla GENÉRICAS»** de `app.js` (291 líneas, junto con el F7 viejo): sin él, los `<col
   data-w>` no se aplican, no hay ordenar, arrastrar, redimensionar ni «↺ Columnas», y la bandeja (`sv4.listCols`)
   también lo perdió. Sin anchos, las columnas se reparten y la tabla crece con el contenido: es la causa de lo que vio
   el humano (con «Desbloquear» la tabla se ensanchaba y «Guardar»/«Dividir» salían de la vista). **Restaurado tal
   cual** (`diff` con `860b6c5^`: idéntico). Y, según el dato del humano: celda y cabecera `position: sticky; right: 0`
   con `z-index` y fondo opaco (`--paper`; zebra, hover y conciliación mandan por especificidad, todos opacos) y sombra
   a la izquierda; columna **fija** (`data-col-fixed`, ya no `draggable`: una sticky arrastrada al medio no tendría
   sentido) de **200 px** por defecto (antes 156); «Borrar ✕» → **«✕»** con `aria-label="Borrar"` y el mismo `title`;
   la celda sin `nowrap` ni `overflow: hidden` (si alguien la estrecha, los botones bajan de línea, no se recortan; cada
   botón `nowrap`). Qué botones salen: sin cambios. Con los anchos aplicados, la tabla mide la suma de las columnas y no
   depende de qué botones haya.
6. **Docs**: `docs/ARCHITECTURE.md` regla 20 (F7, última parte, combo, Acciones fija); `azure-apps` no cambia (sv4 no
   cambia lo que expone ni consume). Spec: R27 y R29 v3 (requirements 150/150), design §5.5, tareas T29–T35.

## 3. Decisiones y hallazgos para el líder

- **D1 · Restaurar el bloque de columnas** no estaba en el plan enseñado: es deshacer un borrado accidental de esta
  misma feature (vuelve el comportamiento de producción) y es la causa raíz del punto 5. Si el líder prefiere sacarlo
  aparte, es el commit `bb3d250` (y su test `test_f065_r29v3_columnas_*`).
- **D2 · `resto · Q ≤ 0` y `n · Q ≤ 0`** en vez de `=== 0 || signos distintos`: la mutación sacó que con Q > 0 media
  condición sobraba y con Q < 0 nadie la probaba (§6). Q nunca es 0 en la ventana (sin Q no hay botón, R30).
- **H1**: Enter sin marcada caía en «Almacén» (POST `/almacen`). No se tocó aquí; resuelto en la pasada 3 (R27 v4).
- **H2**: en la cabecera, «Guardar y aprobar» y «Desaprobar para editar» viven fuera de la tabla; no encontré nada que
  los oculte.
- **H3**: el arranque local (`infra/local/arrancar_local.ps1`) toma el código del árbol PRINCIPAL ($PSScriptRoot): la
  MANUAL T35 necesita `dev` con la rama fusionada o sv4 lanzado desde el worktree (anotado en `current.md`).

## 4. Fase RED (traza real)

Tests nuevos `tests/test_f065_f3bis_front.py` con un DOM mínimo para node (`tests/dom_falso.js`: elementos, clases,
`dataset`, eventos que burbujean, foco, selectores simples y descendientes), sobre `420712d` (solo tests, código de
`cd3baf1`): `.venv\Scripts\python -m pytest tests/test_f065_f3bis_front.py -q -p no:cacheprovider --tb=line` ⇒
**`16 failed in 0.43s`**, por motivo:
```
10 E   ValueError: substring not found          (estadoReparto, esAlmacenTecleado, enhanceTable: no existen)
 1 E   AssertionError: assert {'abierto': T...isos': 1, ...} == {...}      (ratón: 'cerrado': False)
 1 E   AssertionError: assert {'tras': {'ce...rrado': True}} == {...}      (Enter: ver abajo)
 1 E   assert ('"F7"' in '// static/app.js ...
 1 E   AssertionError: .salmon-table thead th[data-col="acciones"]          (no hay regla sticky)
 1 E   assert '<col data-col="acciones" data-w="200">' in '<!-- templates/document_detail.html ...
 1 E   assert 'var gridApi = enhanceTable(document.getElementById("lines-table"));' in '// static/app.js ...
```
Enter, salida real: `{'tras': {'cerrado': False, 'valor': '01.01', 'avisos': 1, 'prevenido': True}, 'otro':
{'prevenido': True, ...}}` — el panel se reabre y el SIGUIENTE Enter se lo come el combo en vez del «Guardar» de la fila.
Para que los que fallaban por función ausente tengan RED **de conducta**, se repitieron contra el mismo código viejo sin
extraer las funciones nuevas (el código viejo no las llama; script `scratchpad/red_conducta.py`), salida real:
```
f7_abre_dividir_y_f6_no: {'f6': {'abierta': True, 'prevenida': True}, 'f7': {'abierta': True, 'prevenida': False}}
ultima_parte_se_rellena_sola: inicial {'valores': ['', ''], 'mensaje': 'Falta: 18'}; forma {'soloLectura': False,
  'sinTab': 0, 'auto': False}; seis {'valores': ['6', ''], 'mensaje': 'Falta: 12', 'aceptar': False}; dieciocho
  {'valores': ['18', ''], 'mal': False, 'mensaje': 'Reparto completo.', 'aceptar': False}; enviado None
ultima_parte_con_decimales: {'decimales': {'valores': ['4,1', ''], 'mensaje': 'Falta: 6,15'}, 'casi': {...
  'mensaje': 'Sobra: 0,005'}}          (la milésima de antes redondeaba 0,0049 a 0,005)
combo_al_marca_almacen_arriba: {'antes': '02.03 · Puertas', 'tras': {'activa': '04.02 · Saneamiento general',
  'arriba': 150, ...}, 'almacen': 0, 'cerrado': False}   (Enter elegía «04.02» y la lista se reabría)
combo_otro_texto_vuelve_arriba_sin_marcar: {'activa': '01.01 · Cimentación', 'arriba': 90}
```
(Llama la atención «dieciocho»: con 18 en la primera y la segunda vacía, el código viejo decía «Reparto completo.».)
Tras cada tarea: T30 (F7 sin `estadoReparto`, mismo script) PASA; T31 `-k "f7 or ultima or estado or js"` **19 passed**;
T32 `test_f065_f3bis_front.py` + `test_f065_f2_origen.py` **61 passed** (4 de T33 aún en rojo); T33 el fichero **16
passed**; tras cerrar supervivientes, **17 passed**.

## 5. Verificación (resultado real)

- `test_f065_f3bis_front.py` 17 passed; sv4 sola 1237 passed (43,8 s); `node --check` OK; bloque restaurado idéntico
  a `860b6c5^` (`diff`). `bash harness/init.sh` (`32facbc`): **exit 0**, sv4 1238 passed, `ENTORNO LISTO` (la vuelta
  anterior, en rojo por la fila del inventario de mutación que faltaba: añadida).

## 6. Cobertura y mutación

- Cobertura de líneas cambiadas: **N/A** (sin Python de producción; el JS lo ejercitan los tests con node).
- Mutación: el generador del arnés da ALCANCE VACÍO (0 líneas Python); campañas **a mano** en
  `progress/mutacion_F-065_fase3bis.md` (la de la pasada 1, 44/44, no valía: la rehízo la pasada 2; ver cada pasada).

## 7. MANUAL y fuera de alcance

- MANUAL T35 (hecha por el humano) y sus pasos 4 bis y 4 ter, en `progress/current.md`. Fuera: el servidor (no valida
  la partida contra la obra, P11), cobertura de JS. Falta: review, fusionar, `init.sh` en el principal, desplegar sv4.

## 8. Evidencias (las últimas, pasada 4)

| Evidencia | Valor real |
|---|---|
| Tests ejecutados | sv4 **1275 passed** (`test_f065_f3bis_front.py`: 54) |
| Cobertura de las líneas cambiadas | **N/A** (`PUERTA COBERTURA`: sin Python de producción; JS cubierto por tests con node) |
| Mutantes | arnés: alcance vacío; **a mano, pasada 4: 38 generados, 38 muertos, 0 supervivientes** (pasadas 2 y 3: 57/57, 15/15) |
| Tiempo de la suite | sv4 99,7 s dentro de `init.sh`; línea base de la campaña 18,6 s |
| `bash harness/init.sh` | **exit 0** (`642da6d`), raíz 1083 passed, sv4 1275 passed, `ENTORNO LISTO` |

## Pasada 2 (review `1bc0e5f`: CHANGES_REQUESTED por CR1, CR2 y CR3)

Commits `02b65d1` (RED) · `15fae04` CR1 · `6bcd932` CR2 · `7b879ec` MANUAL · `333edf0`, `8f67a2a`, `3f904f5`, `1b60541`
(CR3: superviviente cerrado y CSS sin declaraciones muertas) · el de este informe. Solo sv4 y solo front. H1 sin tocar.

- **CR1 · el combo volvía a un texto fuera de la lista.** `open(textoNuevo)`: `alAbrir` solo se toma al abrir por foco
  o clic (`if (panel.hidden && !textoNuevo)`), nunca de lo tecleado. Cubre: elegir → teclear «02.0x» → blur (o Esc)
  ⇒ vuelve «02.03»; foco → Esc → teclear «zz» → blur ⇒ vuelve la original; y (de la campaña) teclear con la lista
  abierta → pinchar otra vez en la casilla → blur ⇒ vuelve la original. Más dos de control: lo válido tecleado se
  queda, y tras elegir, teclear vuelve a abrir la lista. `dom_falso.js` gana `blur()` (el foco pasa a `body` antes de
  disparar «blur», como el navegador).
- **CR2 · cabecera sticky.** Selector `.salmon-table thead tr.salmon-head th[data-col="acciones"]` (0,3,3), que gana a
  `.salmon-table thead tr.salmon-head th` (0,2,3, `relative`). Test con un **motor de cascada** (en el propio test):
  modela celda y cabecera como las pinta la plantilla y decide qué regla GANA cada propiedad (especificidad y orden).
- **Chrome sin cabeza** (`--dump-dom`, página de prueba con el `styles.css` real): con el CSS de la pasada 1 la
  cabecera salía `relative` (borde derecho en 1369 px frente a 720 de sus botones); ahora `sticky`, 720 y 720; botones
  dentro y fondo opaco; con `elementFromPoint`, la columna queda encima con y SIN `z-index` (equivalentes: fuera).
- **Quitado por no hacer nada** (habrían sido mutantes equivalentes, RM3): `background` de la celda (lo pone la fila,
  más específica), `white-space: normal` (es el heredado) y los `z-index` (arriba). El comentario del CSS lo explica.
- **MANUAL T35**: paso 3, teclear fuera de la lista tras elegir y salir; paso 5, la cabecera «Acciones» sigue encima
  de sus botones al desplazar, y **O1** (anchos guardados de antes: «Acciones» a 156 px; «↺ Columnas» la deja en 200).

**RED** (tests nuevos, `02b65d1`, contra el código de la pasada 1, `1bc0e5f`; `pytest tests/test_f065_f3bis_front.py -k "cr1
or cr2" -vv`) ⇒ **`4 failed, 3 passed`**:
```
cr1_elegir_y_teclear_..._al_salir     {'valor': '02.0x'} != {'valor': '02.03'}
cr1_elegir_teclear_y_esc              {'valor': '02.0x'} != {'valor': '02.03'}
cr1_foco_esc_teclear_y_salir          {'valor': 'zz'} != {'valor': '01.01'}
cr2_la_cabecera_..._gana_la_cascada   assert 'relative' == 'sticky'
```
(pasan los de control: lo válido se queda, el motor se comporta y la celda ya ganaba). El de pinchar en la casilla,
añadido por la campaña, contra el código con la guarda mutada: `{'valor': 'zz'} != {'valor': '01.01'}`.

**Mutación (CR3)**, rehecha entera, detalle y script en `progress/mutacion_F-065_fase3bis.md`: **HEAD
`1b605415b0b4dd6f2ca99dfced7d8af94eb8fea0`**; línea base de los tres ficheros de tests **192 passed, 7,8 s**; por fila
`fichero:línea`, original→mutado y nº de fallos (sin `-x`). Nuevos: 4 de la guarda de `alAbrir`, el del selector de la
cabecera, el del reinicio de `eligiendo` y los de cada declaración de «Acciones». Intermedia (`333edf0…`): 59
mutantes, **1 superviviente** (`panel.hidden && !textoNuevo` → `!textoNuevo`), cerrado con el test de pinchar en la
casilla. **Final: 57 mutantes, 57 muertos, 0 supervivientes, 0 equivalentes**; los 12 de CSS mueren también **sin**
los dos tests textuales (solo con el motor de cascada). Inventario actualizado. Nota en el informe de mutación sobre la
guarda `dialogo.open` (#2): muere por conducta; en el navegador el modal hace inalcanzable ese estado.

**Verificación**: `test_f065_f3bis_front.py` **26 passed**; los tres ficheros, 192 passed; **`bash harness/init.sh`**
(tal cual, worktree, `376d37a`): **exit 0**, raíz `1083 passed`, sv4 **`1247 passed`** (71,6 s, sin caché: sv4 cambió),
`PUERTA COBERTURA: N/A` (sin Python de producción), rutas sensibles N/A, tamaño dentro, **`ENTORNO LISTO`**.

## Pasada 3 (H1, R27 v4; aprobada por el humano el 2026-10-13, opción «a»)

Commits `2d64bc2`, `0034080` RED, `440beb6`, `77b1f97`, `3f3aeff`, `0075ce4`. `marcadaAlTeclear`: «Almacén» si
`esAlmacenTecleado`, si no la primera partida que coincide, si no ninguna; **Enter elige la marcada y, sin ella, nada**
(la lista sigue abierta). **RED** (`0034080` contra `2d64bc2`): `19 failed, 17 passed`; de conducta
(`scratchpad/red_v4.py`): «alba», «02.0», «zzz» y foco + Enter ⇒ `'almacen': 1` (la fila iba a almacén); «Dividir»
dejaba la partida vacía. **Verificación**: `init.sh` exit 0 (`e181863`, sv4 1259 passed). **Mutación a mano**: HEAD
`0075ce4900a27867ec0c1e6c0c80f46dcf5d5711`, línea base 204 passed, **15/15**; sin el test de la función pura vive #5
(`shown.length > 1`), equivalente en el combo y demostrado ejecutando (§«Pasada 3» de la ficha de mutación).

## Pasada 4 (R27 v5; aprobada por el humano el 2026-10-13; fallo de la MANUAL)

**El fallo**: «zzzz» o «al» + Enter en la partida GUARDABA la fila: la primera vez las partidas tardan (Sigrid), la lista
seguía cerrada, el combo soltaba el Enter (`if (panel.hidden) return;`) y llegaba al «Guardar» de `wireConciliaEdit`.
Con la lista abierta y sin marcada no había otro camino (v4 ya paraba el Enter). Commits `137fe8e` RED · `4c4fedb`
código · `f85ee2e` spec v5 y docs · `e1563f5` sin código redundante · el de este informe. Solo sv4 front; servidor igual.
- **Combo**: en la partida, Enter SIEMPRE es del combo: elige la marcada o nada; nunca guarda ni acepta «Dividir». La
  lista sale al momento con «Cargando partidas…»; `abierta` evita que una respuesta tardía reabra una lista cerrada.
- **`partidasInvalidas`** (+ `marcarPartida`: `partida-invalida`, `aria-invalid`, `title`): una partida CAMBIADA fuera
  de la lista no se envía por «Guardar», Enter en otra celda, «Guardar todas», «Aceptar» de «Dividir»; el aviso de
  «Guardar y aprobar» la marca. CSS en rojo, comprobado con el motor de cascada.
- **RED** (`137fe8e` contra `553604d`): `17 failed, 37 passed`; de conducta (`scratchpad/red_v5.py`): «zzzz»/«al» +
  Enter cargando ⇒ 1 PATCH; lista cerrada + Enter ⇒ 1 PATCH; Esc cargando ⇒ se reabría; «Guardar», Enter en la
  cantidad, Sigrid caído, «Guardar todas» y «Dividir» mandaban la partida mala.
- **Mutación a mano**: HEAD `e1563f565d582368e2a1ed549166bbb41b500a3f`, línea base 239 passed, **38/38**, también sin
  ningún test textual. `init.sh` exit 0 (`642da6d`, sv4 1275 passed).

## Pasada 5 (CR4 de la review, pasada 4; más O6 y O7)

**CR4**: «Guardar» y «Guardar todas» armaban el cuerpo ANTES de esperar la lista y validaban DESPUÉS: si la casilla
cambiaba mientras Sigrid tardaba, se validaba una cosa y se enviaba otra. Ahora desactivan el botón ya, esperan la lista
y en el mismo tick validan (`partidasMalas(filas, items)`, síncrona; `partidasInvalidas` queda para marcar en el aviso de
la cabecera) y arman el cuerpo; «Guardar todas» cuenta las filas con cambios tras la espera (una que vuelve a como
estaba no se manda). Si algo no vale, el botón vuelve a servir. **O6**: salir de la partida antes de que llegue la lista
ya no la deshace a ciegas: se decide al llegar (`volverSiNoVale`, que no toca lo que ya era el valor de antes). **O7**: en
`enviar` de «Dividir», «Aceptar» desactivado (reparto que no vale o envío en curso) es el cerrojo: dos Enter, un POST.
Sin tocar O3/O4 (observaciones sin petición). El `dom_falso.js` no deja hacer clic en un botón desactivado (como el
navegador). Commits `20a6909` RED · `2fa95e3` código y 2 tests de control · el de este informe.

**RED** (`20a6909` contra `edb8475`, `-k "cr4 or o6 or o7"`) ⇒ `6 failed, 4 passed`: la carrera mandaba
`{'codigo_partida': 'zzzz'}` (con «Guardar» y con «Guardar todas»); dos clics ⇒ `[{'cantidad': 6}, {'cantidad': 6}]`
(los dos botones); O6 ⇒ `{'alSalir': '01.01', 'alLlegar': '01.01'}` (deshacía «02.03»); O7 ⇒ `{'envios': 2}`. Pasaban
(control): lo que se vuelve malo durante la carga no se envía (×2), «zzzz» al salir vuelve al llegar, Esc con la vieja.
**Mutación a mano** (`progress/mutacion_F-065_fase3bis.md` §«Pasada 5»): HEAD `2fa95e378b369c760c1959fee671bbde95279361`,
línea base de los cuatro ficheros 251 passed, **19 mutantes, 19 muertos, 0 supervivientes** (entre ellos, el propio
fallo de CR4 como un solo mutante en cada botón); solo con conducta (62 tests, sin textuales): **19/19**.
**Verificación**: `bash harness/init.sh`: PENDIENTE_P5.
