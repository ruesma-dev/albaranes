<!-- progress/review_F-065_fase3bis.md -->
Revisión incremental desde `553604d` (pasada 4) hasta `9e30765`; la 3 desde `ee13554`, la 2 desde `1bc0e5f`, la 1 completa

# F-065 · fase 3 bis (R27 v3–v5, R29 v3; design §5.5; T29–T41) · review

- **Veredicto (pasada 4, al final): CHANGES_REQUESTED** por CR4: una carrera que deja enviar una partida fuera de la
  lista en «Guardar» y en «Guardar todas».
  - La pasada 1 fue CHANGES_REQUESTED por CR1–CR3.
  - Las pasadas 2 y 3 fueron APPROVED.
- **Nivel de rigor:** `critico` (declarado). Exige fase RED, cobertura (o N/A con motivo), mutación con 0
  supervivientes y MANUAL con su comando.
- **Alcance:** solo sv4 y solo front. El servidor no cambia: el diff no toca Python de producción.

## Pasadas 1–3 (resumen; detalle en `1bc0e5f`, `ee13554` y `553604d`)
- **Pasada 1**: D1 verificado (el bloque de columnas es idéntico al de `860b6c5^`) y la campaña 44/44 reejecutada.
  Pedí tres cambios:
  - **CR1**: el combo admitía texto fuera de la lista tras elegir;
  - **CR2**: la cabecera de «Acciones» no era sticky, por especificidad;
  - **CR3**: un mutante equivalente salía MUERTO y a la campaña le faltaban datos.
- **Pasada 2**: los tres, resueltos. Medí en Chrome sin cabeza que la cabecera queda sticky; el CSS quitado era
  equivalente; el motor de cascada es válido para lo que mira; reproduje la campaña 57/57 fila a fila.
- **Pasada 3** (R27 v4): Enter sin marcada no elige nada; un doble Enter no guarda la fila ni acepta «Dividir»; CR1
  sigue en pie; reproduje la campaña 15/15 fila a fila y demostré ejecutando el equivalente #5.

## Pasada 4 · R27 v5: verificación ejecutada por el reviewer (resultado real)
- **`bash harness/init.sh`** (tal cual, en `9e30765`):
  **exit 0**, `ENTORNO LISTO`, raíz `1083 passed`, `PUERTA COBERTURA: N/A (F-065 no cambia líneas Python de
  producción frente a dev)`, rutas sensibles N/A, tamaño dentro (150/150, 190/250). sv4 salió de la caché, así que lo
  corrí sin ella: **1275 passed** (44 s).
- **Fase RED**: los tests de `137fe8e` contra `app.js` y `styles.css` de `553604d` dan **17 failed, 37 passed**,
  exactamente lo que dice el informe.
- **El código, revisado:**
  - en la partida, Enter es siempre del combo: va en una cadena `if/else` antes de mirar `panel.hidden`;
  - la lista se pinta al momento con «Cargando partidas…» (`cargadas`);
  - `abierta` evita que una respuesta tardía reabra una lista que ya se cerró;
  - `marcarPartida` y `partidasInvalidas` se usan en «Guardar» (el botón, y Enter en otra celda vía
    `saveBtn.click()`), en «Guardar todas», en el aviso de «Guardar»/«Guardar y aprobar» y en `enviar` de
    «Dividir».
- **Caminos buscados a propósito.** Script mío sobre `_FILA_GUARDAR` (combo y `wireConciliaEdit`), con una respuesta
  de Sigrid que se suelta a mano. Todos se portan bien:
  - **Tab o blur durante la carga**: «zzzz» vuelve a «01.01» y la lista no se reabre al llegar la respuesta.
    «Guardar» manda solo `{cantidad: 6}`.
  - **«Guardar» con la carga pendiente y «zzzz» en la partida**: 0 peticiones antes de llegar la lista y 0 después.
    La partida queda en rojo.
  - **Sigrid caído**: «02.03» queda en rojo y no se hace ninguna petición. Vaciarla (almacén) manda
    `{codigo_partida: ""}`.
  - **Partida vieja fuera de la lista («99.99»), sin tocarla**: se manda `{cantidad: 6}` y no se pinta en rojo.
  - **Lo válido sigue guardándose**: elegir con «puer» + Enter y pulsar «Guardar» manda
    `{codigo_partida: "02.03"}`.
- **«Guardar y aprobar» y «Guardar» de la cabecera**: con filas cambiadas, `guardarCabecera` avisa y vuelve sin hacer el
  PUT. Además, `collectPayload` no lleva líneas (R1).
- **Otros caminos que escriben la partida**, todos sin texto tecleado: «Origen ✎» (`mode` e id de la línea de
  contrato), «Almacén» (POST `/almacen`), «Almacén a todas» y copiar las sin casar.
- **«Dividir»**: lee y valida después del `await`, y el cuerpo se arma en ese mismo tick: correcto.
- **RM6** (se quitó la guarda `if (!inp)` de `partidasInvalidas`). Verifiqué el invariante en quien construye el
  dato:
  - en `document_detail.html`, la clase `concilia-editable` de la fila (`:720`) y el `<input … js-partida-combo>`
    (`:742`) dependen de la MISMA condición `cedit` (`:718`), sin más ramas;
  - ningún JS añade `concilia-editable`.
- **Campaña** (`progress/mutacion_F-065_fase3bis.md` §«Pasada 4»), reejecutada ENTERA sobre una copia de HEAD en el
  scratchpad:
  - **Con los cuatro ficheros de tests**: línea base `239 passed`; **38/38 muertos**. Las **38 filas coinciden una a
    una** con la tabla del informe: línea, original, mutado, fallos y veredicto.
  - **Sin tests textuales** (el filtro `-k` del informe): línea base `50 passed`; **38/38 muertos**.
  - **RM1**: `e1563f565d582368e2a1ed549166bbb41b500a3f` es `e1563f5`; lo posterior es solo `impl`, `mutacion`,
    `inventario` y `current`.
  - **RM3**: los mutantes son de conducta o de cascada; no veo ningún equivalente.

## Cambios requeridos
1. **CR4 · Lo que se valida no es lo que se envía.**
   - **Dónde**: `static/app.js:1187-1189` («Guardar») y `:1483-1497` («Guardar todas»).
   - **Qué pasa**: «Guardar» arma `body = _camposCambiados(tr)` ANTES de `await partidasInvalidas([tr])`, que valida
     lo que haya en la casilla DESPUÉS de esperar a Sigrid. «Guardar todas» hace lo mismo con `envios`.
   - **Reproducido** (DOM falso, con la carga pendiente):
     1. `part.value = "zzzz"` sin pasar por el combo. Es justo el caso que el test
        `boton_guardar_con_partida_fuera_de_la_lista_no_envia` llama «la última barrera».
     2. `guardar.click()`.
     3. Durante la espera, la casilla pasa a «02.03».
     4. Llega la lista ⇒ **`PATCH … {"codigo_partida": "zzzz"}`**.
   - **Por qué lo pido aunque cueste llegar ahí**: en un navegador, el blur del combo ya devuelve lo inválido antes del
     clic. Pero R27 v5 promete «por ningún camino», y la barrera que lo cubre falla justo cuando Sigrid tarda, que es la
     condición del fallo de la MANUAL.
   - **Arreglo**: validar primero y armar el cuerpo después, sin `await` entre medias; en «Guardar todas», armar
     `envios` tras la validación. Recomendado: desactivar el botón antes del `await` (hoy dos clics durante la carga
     mandan dos PATCH).
   - **Verificación que pido**: un test RED con esa secuencia para «Guardar» y para «Guardar todas», y mutación a mano
     de las líneas movidas (incremental, con SHA completo, línea base y fallos por fila).

## Checkpoints (estado en la pasada 4)
- **C1**: [x] init exit 0 · [x] ficheros del arnés.
- **C2**: [x] solo F-065 `in_progress` · [x] rama de la feature · [x] `current.md` = sesión F-065 · [x] sin `done`
  nuevas.
- **C3**: [x] hexagonal: no aplica a estático, no hay Python de producción · [x] primera línea con ruta · [x] sin
  prints, sin secretos, sin dependencias · [x] ARCHITECTURE al día (R27 v5).
- **C3 bis** N/A: no toca `docs/referencia/`.
- **C4**:
  - [ ] **R27 v5, «no se guarda por ningún camino»**: el test de la última barrera existe y pasa, pero no cubre la
    carrera (CR4).
  - [x] sin red ni BBDD.
  - [x] MANUAL: paso 4 ter de T35.
- **C4 bis**:
  - [x] rigor `critico` · [x] RED con salida real · [x] cobertura N/A con el motivo impreso · [x] alcance de la
    herramienta vacío por lenguaje.
  - [x] campaña reejecutada entera, también sin textuales · [x] RM1, RM2 y RM3 · [x] RM6: invariante verificado
    (arriba).
  - RM5 N/A: no hay equivalentes declarados en la pasada 4.
  - [x] tabla con línea, texto exacto y fallos · [x] 0 supervivientes · [x] «Evidencias» · [x] N/A justificados.
- **C4 ter** N/A: la puerta de rutas sensibles da N/A.
- **C5**: [x] T39–T41 con sus commits `F-065 Tn:` y los de la pasada · [x] árbol limpio · [x] `features.json`.

## Cobertura requisito → test (`tests/test_f065_f3bis_front.py`)
| Requisito | Tests |
|---|---|
| R29 v3 (F7, última parte, «Acciones») y D1 | `r29v3_*`, `cr2_*`, `test_f065_f3_dividir::r29_js_*` |
| R27 v3/v4 (cerrar al elegir, marcada, Enter) | `r27v3_*`, `r27v4_*`, `cr1_*` |
| R27 v5: Enter nunca guarda ni acepta; «Cargando…» | `r27v5_la_lista_se_abre_ya_cargando…`, `r27v5_al_y_enter_cargando…`, `r27v5_esc_mientras_carga…`, `r27v5_enter_con_la_lista_cerrada…`, `r27v4_en_la_ventana_dividir_lo_mismo` |
| R27 v5: fuera de la lista no se guarda | `r27v5_boton_guardar…`, `r27v5_enter_en_otra_celda…`, `r27v5_guardar_todas…`, `r27v5_guardar_y_aprobar…`, `r27v5_dividir_*`, `r27v5_sin_lista_de_sigrid…`, `r27v5_la_partida_mala_se_ve_en_rojo` — **falta la carrera (CR4)** |
| R27 v5: lo válido se guarda | `r27v5_lo_valido_se_sigue_guardando` (3 casos), `r27v5_una_partida_vieja_sin_tocar_no_se_valida` |

## Observaciones (no bloquean)
- **O1 · Anchos guardados**: «Acciones» se queda a 156 px; está anotado en la MANUAL.
- **O3 · «Dividir»**: tras elegir «Almacén», un texto inválido vuelve a la partida anterior, no a la vacía.
- **O4 · R27 v4**: el código exacto no tiene prioridad sobre una descripción que coincida antes.
- **O5 · Teclado**: en la partida, Enter ya no guarda nunca (R27 v5, aprobado). Conviene decirlo al desplegar.
- **O6 · Validar contra una lista que aún no ha llegado**: si se teclea un código VÁLIDO y se sale con Tab antes de que
  lleguen las partidas, la casilla vuelve a la partida de antes sin avisar, porque el blur valida contra la lista
  vacía. Es seguro, pero confunde. Una vez arreglado CR4, se podría no revertir en el blur mientras `!cargadas` y dejar
  la decisión a la barrera del guardado.
- **O7 · Doble envío en «Dividir»** (previo a esta pasada): Enter en una cantidad llama a `enviar` aunque «Aceptar»
  esté desactivado.
  - Dos Enter seguidos pueden mandar dos POST `/dividir`, y la espera de las partidas agranda esa ventana.
  - El servidor rechaza el segundo si la suma ya no cuadra con Q.
  - Recomendado: en `enviar`, salir si `aceptar.disabled` o si ya hay un envío en curso.

## Automejora (propuesta)
- **En `CHECKPOINTS.md`** (C4, front asíncrono): cuando un guardado valida tras un `await`, el reviewer comprueba que lo
  enviado se arma DESPUÉS de validar.
- **Por qué**: es un hueco tipo TOCTOU (validar una cosa y enviar otra) y lo reproduce cualquier validación asíncrona.
