<!-- progress/review_F-065_fase3bis.md -->
Revisión incremental desde `edb8475` (pasada 5) hasta `42c9c98`; la 4 desde `553604d`, la 3 desde `ee13554`, la 2 desde `1bc0e5f`, la 1 completa

# F-065 · fase 3 bis (R27 v3–v5, R29 v3; design §5.5; T29–T44) · review

- **Veredicto (pasada 5, al final): APPROVED.** CR4 resuelto en los dos botones; O6 y O7 dentro de R27/R29.
  - Historial: pasada 1 CHANGES_REQUESTED (CR1–CR3); 2 y 3 APPROVED; 4 CHANGES_REQUESTED (CR4).
- **Nivel de rigor:** `critico` (declarado). Exige fase RED, cobertura (o N/A con motivo), mutación con 0
  supervivientes, RM5 sobre un equivalente si los hay, y MANUAL con su comando.
- **Alcance:** solo sv4 y solo front (`app.js`) más el DOM falso de los tests. Ningún Python de producción.

## Pasadas 1–4 (resumen; detalle en `1bc0e5f`, `ee13554`, `553604d` y `edb8475`)
- **Pasada 1**: CR1 (el combo admitía texto fuera de la lista tras elegir), CR2 (cabecera de «Acciones» no sticky),
  CR3 (un equivalente salía MUERTO). **Pasada 2**: resueltos; sticky medido en Chrome; campaña 57/57 reproducida.
- **Pasada 3** (H1 → R27 v4): Enter sin marcada no cae en «Almacén»; campaña 15/15 reproducida; equivalente #5
  demostrado ejecutando.
- **Pasada 4** (R27 v5): Enter en la partida nunca guarda; «Cargando partidas…»; campaña 38/38 reproducida (también sin
  textuales); RM6 verificado en `document_detail.html` (`cedit` gobierna fila y casilla). Rechazo por **CR4**:
  «Guardar»/«Guardar todas» armaban el cuerpo antes de `await` y validaban después (se podía enviar «zzzz»).

## Pasada 5 · CR4, O6, O7: verificación ejecutada por el reviewer (resultado real)
- **`bash harness/init.sh`** (tal cual, en `42c9c98`): **exit 0**, `ENTORNO LISTO`, raíz `1083 passed`,
  `PUERTA COBERTURA: N/A (F-065 no cambia líneas Python de producción frente a dev)`, rutas sensibles N/A, tamaño
  dentro (150/150, 195/250). sv4 salió de la caché: lo corrí sin ella con su venv: **1287 passed** (104 s).
- **Fase RED** (`git archive 20a6909` en el scratchpad; `app.js` idéntico al de `edb8475`), `-k "cr4 or o6 or o7"`:
  **6 failed, 4 passed**, los mismos seis que el informe (carrera ×2, dos clics ×2, O6 válida, O7 `{'envios': 2}`).
- **CR4, revisado en el código** (`static/app.js`):
  - «Guardar» (`:1206-1212`): `saveBtn.disabled = true` → `await cargarPartidasObra()` → `partidasMalas([tr], items)`
    (síncrona) → `_camposCambiados(tr)`. Entre validar y armar no hay ningún `await`: lo validado es lo enviado.
  - «Guardar todas» (`:1521-1531`): igual, y además las filas con cambios se recalculan TRAS la espera (`conCambios()`),
    así que una fila que se cambia durante la carga también se valida.
  - `cargarPartidasObra` nunca rechaza (`.catch` → `{items: [], error: true}`): el botón no se queda bloqueado.
  - Enter en otra celda → `saveBtn.click()`: con el botón desactivado no hace nada (en el navegador, igual; el DOM
    falso ahora lo imita, `dom_falso.js:192`).
- **Caminos buscados a propósito** (script mío en el scratchpad con los ayudantes del propio test):
  - **Enter en la cantidad** con «zzzz», casilla a «02.03» durante la carga, otro Enter, llega la lista ⇒ **un solo
    PATCH `{codigo_partida: "02.03"}`**.
  - «Guardar todas» con el cambio deshecho durante la carga ⇒ 0 peticiones y recarga (sin pérdida: no había cambios).
- **O6 y O7 no amplían el alcance**: no hay requisito, fichero ni ruta nuevos.
  - O6 solo cambia CUÁNDO se aplica R27 («lo demás vuelve al valor de antes»): al llegar la lista, no a ciegas.
  - O7 solo impide un segundo POST de un reparto que ya se envía (R29/R30). El servidor no cambia.
  - Dos huecos residuales de UX, sin riesgo de dato: O8 y O9 abajo.
- **Campaña** (`progress/mutacion_F-065_fase3bis.md` §«Pasada 5»), reejecutada ENTERA sobre `git archive 2fa95e3`
  con el venv de sv4 (el primer intento con el Python global daba base roja por falta de `fastapi`: lo descarté):
  - **Con los cuatro ficheros**: línea base `251 passed`; **19/19 muertos**. Las 19 filas coinciden una a una con el
    informe: línea, original, mutado y nº de fallos (1, 3, 1, 4, 1, 2, 1, 2, 3, 3, 2, 1, 1, 1, 1, 7, 1, 1, 1).
  - **Sin textuales** (mismo `-k` de la pasada 4): línea base `62 passed`; **19/19 muertos**.
  - **RM1**: `2fa95e378b369c760c1959fee671bbde95279361` es `2fa95e3`; lo posterior solo toca `progress/` y `specs/`.
  - **RM2**: base 33,2 s y ~20–30 s por mutante en mi máquina; coherente.
  - **RM3**: ningún equivalente. El más sospechoso, #15 (quitar `input.value !== alAbrir`), lo mata por CONDUCTA
    `o6_esc_cargando_con_una_partida_vieja_no_reabre`: con la vieja «99.99» y el foco dentro, el `input` que dispara
    el mutante reabre la lista (`cerrada: False`). Lo ejecuté aparte.
  - **RM5** N/A: no hay equivalentes declarados. **RM6** N/A: no se quitó ninguna guarda defensiva.
- **Pasadas 1–4 en pie**: `cr1_*`, `cr2_*`, `r27v4_*` (H1), `r27v5_*`, `cr4_*`, `o6_*`, `o7_*`: **50 passed**; CSS
  sin tocar en esta pasada (CR2 intacto).
- `git status` del worktree limpio tras todo (las copias viven en el scratchpad).

## Checkpoints (estado en la pasada 5)
- **C1**: [x] init exit 0 · [x] ficheros del arnés.
- **C2**: [x] solo F-065 `in_progress` · [x] rama de la feature · [x] `current.md` = sesión F-065 (pasada 5 y MANUAL
  4 quater) · [x] sin `done` nuevas.
- **C3**: [x] hexagonal: no aplica a estático, no hay Python de producción · [x] primera línea con ruta · [x] sin
  prints, sin secretos, sin dependencias · [x] design §5.5 al día (pasada 5).
- **C3 bis** N/A: no toca `docs/referencia/`.
- **C4**:
  - [x] **R27 v5, «no se guarda por ningún camino»**: ahora también en la carrera, en ambos botones (CR4 cerrado).
  - [x] sin red ni BBDD (node con DOM falso).
  - [x] MANUAL: paso 4 quater de T35 en `current.md`.
- **C4 bis**:
  - [x] rigor `critico` · [x] RED con salida real, reproducida · [x] cobertura N/A con el motivo impreso · [x] alcance
    de la herramienta vacío por lenguaje (JS), campaña a mano con texto exacto por fila.
  - [x] campaña reejecutada entera, también sin textuales · [x] RM1, RM2, RM3.
  - RM5 N/A (sin equivalentes) · RM6 N/A (sin guardas quitadas).
  - [x] 0 supervivientes · [x] «Evidencias» con los cuatro números · [x] N/A justificados.
- **C4 ter** N/A: la puerta de rutas sensibles da N/A.
- **C5**: [x] T42–T44 `[x]` con commits `F-065 Tn:` y los de la pasada · [x] árbol limpio · [x] `features.json`.

## Cobertura requisito → test (`tests/test_f065_f3bis_front.py`)
| Requisito | Tests |
|---|---|
| R29 v3 (F7, última parte, «Acciones») y D1 | `r29v3_*`, `cr2_*`, `test_f065_f3_dividir::r29_js_*` |
| R27 v3/v4 (cerrar al elegir, marcada, Enter) | `r27v3_*`, `r27v4_*`, `cr1_*` |
| R27 v5: Enter nunca guarda ni acepta; «Cargando…» | `r27v5_la_lista_se_abre_ya_cargando…`, `r27v5_al_y_enter_cargando…`, `r27v5_esc_mientras_carga…`, `r27v5_enter_con_la_lista_cerrada…`, `r27v4_en_la_ventana_dividir_lo_mismo` |
| R27 v5: fuera de la lista no se guarda | `r27v5_boton_guardar…`, `r27v5_enter_en_otra_celda…`, `r27v5_guardar_todas…`, `r27v5_guardar_y_aprobar…`, `r27v5_dividir_*`, `r27v5_sin_lista_de_sigrid…`, `r27v5_la_partida_mala_se_ve_en_rojo` |
| R27 v5 en la carrera (CR4) | `cr4_lo_validado_es_lo_enviado…` y `cr4_lo_que_se_vuelve_malo…` (×2 botones), `cr4_dos_clics…` (×2), `cr4_guardar_todas_sin_cambios…`, `cr4_guardar_todas_si_durante_la_carga_se_deshace…` |
| R27 al salir antes de la lista (O6) | `o6_salir_con_una_valida…`, `o6_salir_con_una_mala…`, `o6_esc_cargando_con_una_partida_vieja…` |
| R29/R30, un solo POST (O7) | `o7_dividir_dos_enter_seguidos_un_solo_post` |
| R27 v5: lo válido se guarda | `r27v5_lo_valido_se_sigue_guardando` (3 casos), `r27v5_una_partida_vieja_sin_tocar_no_se_valida` |

## Cambios requeridos
Ninguno.

## Observaciones (no bloquean)
- **O1 · Anchos guardados**: «Acciones» se queda a 156 px; anotado en la MANUAL.
- **O3 · «Dividir»**: tras elegir «Almacén», un texto inválido vuelve a la partida anterior, no a la vacía.
- **O4 · R27 v4**: el código exacto no tiene prioridad sobre una descripción que coincida antes.
- **O5 · Teclado**: en la partida, Enter ya no guarda nunca. Conviene decirlo al desplegar.
- **O8 · O6 revierte también con el foco dentro** (`app.js:912-915`). `!abierta` no significa solo «se salió»: un
  scroll o un resize durante la PRIMERA carga cierra la lista (`repos`) con el foco en la casilla.
  - Reproducido: foco, «puer», scroll, llega la lista ⇒ la casilla pasa a «01.01» bajo el cursor y la lista se reabre.
  - En la pasada 4 el texto se quedaba hasta el blur. No envía nada (sin riesgo de dato).
  - Arreglo de una línea: en esa rama, `if (document.activeElement !== input) { volverSiNoVale(); }`.
- **O9 · El cerrojo de O7 lo reabre `refrescar`**: retocar una cantidad mientras vuela el POST pone
  `aceptar.disabled = !repartoValido(…)` y un Enter manda un segundo POST (reproducido: `{envios: 2}`). El servidor
  rechaza el segundo (la línea ya está dividida). Si se quiere cerrar: un `let enviando` propio en vez de reutilizar
  `aceptar.disabled`.
- **Cosmético**: `app.js:961-962` repite el comentario «Solo valores de la lista: lo demás vuelve al valor de antes».

## Automejora (propuesta, de la pasada 4, sigue en pie)
- **En `CHECKPOINTS.md`** (C4, front asíncrono): cuando un guardado valida tras un `await`, el reviewer comprueba que lo
  enviado se arma DESPUÉS de validar, sin otro `await` entre medias. Es un hueco TOCTOU que reproduce cualquier
  validación asíncrona.
- **Nueva, en este fichero (`reviewer.md`)**: al reejecutar una campaña sobre una copia, usar el intérprete del venv
  del servicio (el que usa `init.sh`), no el global: si no, la base sale roja por dependencias y la campaña no vale.
