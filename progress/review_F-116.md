<!-- progress/review_F-116.md -->
Revisión completa (pasada 1) · `dev...10e1841` (base de rama `108cabc`)

# F-116 · review

**Veredicto: APPROVED**

Fuera de esta revisión por encargo del líder: T13 (M1 en Chrome y Edge, líder) y T14 (despliegue de sv4, humano).
Que sigan `[ ]` en `tasks.md` es lo esperado y no bloquea esta review; sí bloquean el `done`.

## Nivel de rigor

`estandar`, declarado en `harness/features.json`. Exige fase RED con salida real, puerta de cobertura, campaña de
mutación sin supervivientes `PENDIENTE` y sección «Evidencias». RM5 no aplica (solo en `critico`).

## Verificación ejecutada por el reviewer

- `bash harness/init.sh` en el worktree con `PYTHONPATH=<worktree>\services\albaranes-comun` y `ARNES_SIN_CACHE=1`:
  **EXIT 0, «ENTORNO LISTO»**. Raíz 1919; sv1 236; sv2 496; sv3 1608; **sv4 2501**; sv5 125; sv6 506 (+1 skipped);
  sv9 1073; comun 1342, todos passed. `PUERTA COBERTURA [OK] 100,0 %` (48/48); `RUTAS SENSIBLES` N/A con motivo
  impreso (no toca ninguna); `PUERTA TAMAÑO [OK]`. `git status` limpio después.
- Mutación, recálculo independiente (`alcance_de_feature("F-116")` + `generar_mutantes`, cálculo puro): 4 ficheros,
  **120 líneas, 7 mutantes**, igual que el informe. Los 7 (`not`, `aritmetico` `-`→`+` de conjuntos, dos
  `comparacion` `==`→`!=`, `is None`→`is not None`, `True`→`False` del `ok`) cambian el comportamiento: ninguno es
  equivalente, así que ninguno «muerto» es sospechoso (RM3).
- **Campaña no reejecutada: 1020,9 s (17 min) según el informe**, por encima del umbral de 60 s; me quedo en el
  recálculo puro y RM1–RM6.
- Lectura del diff completo de código (Python, `app.js`, plantilla, CSS) y de los cuatro tests viejos tocados.

## Checkpoints

**C1** [x] init.sh exit 0 · [x] ficheros del arnés presentes.
**C2** [x] una sola `in_progress` (F-116) · [x] rama `feature/F-116-guardado-automatico-ficha` · [x] `current.md`
con la sesión activa · [x] las `done` tienen su resumen (lo valida init.sh).
**C3** [x] hexagonal: `CabeceraEditBody` en dominio (solo pydantic), `update_cabecera_campos` en infraestructura,
`editar_cabecera` en aplicación, ruta en `interface_adapters` · [x] primera línea con ruta en los 4 tests nuevos,
specs e informe · [x] sin `print`/`console.log` de depuración (los `console.log` del diff son el canal de los
tests de node), sin secretos · [x] regla 20 de `ARCHITECTURE.md` actualizada y respetada (bloquear sigue siendo de
los botones).
**C3 bis** N/A: la feature no incorpora documentos de fuera (`docs/referencia/` intacto).
**C4** [x] cada requisito con test (tabla abajo) · [x] unit tests sin red ni BBDD real (SQLite en memoria y DOM
falso) · [x] MANUAL listadas: T13 y T14 en `tasks.md` e informe §6.
**C4 bis** [x] `rigor` declarado · [x] fase RED con salida real de T1–T3, T5 y T6–T10 (§4); R18 sin RED justificada
(fija lo que ya había) · [x] cobertura 100 % · [x] `mutacion_F-116.md` de la herramienta, totales recalculados ·
[x] muertos: campaña > 60 s, recálculo + RM1–RM6, dicho arriba · [x] coste por mutante 1020,9 × 4 ÷ 7 = 583 s, muy
por encima de 1 s · [x] sin «⚠ CAMPAÑA NO VÁLIDA», «Sin veredicto» = 0 · [x] RM1: SHA medido `0245fd6`; desde
entonces solo cambian `progress/` y `tasks.md`, nada del alcance · [x] RM2: línea base ~270 s, media 145,8 s
(coherente con `-x` y 7/7 muertos), 7 × 145,8 = 1020,6 ≈ total · N/A RM5 (rigor `estandar`) · N/A RM6 (no se
quitó ninguna guarda: 0 supervivientes) · N/A campaña manual (la automática dio 7) · N/A análisis de
supervivientes (no hay) · [x] «Evidencias» con los cuatro números y los workers · [x] ningún N/A sin motivo.
**C4 ter** N/A: la puerta dice que F-116 no toca rutas sensibles declaradas.
**C5** [x] T1–T12 y T15 `[x]` con un commit `F-116 Tn:` cada una (T11 y T15 sin código propio, marcadas en commits
del informe); T13/T14 MANUAL fuera de esta review · [x] sin temporales sin trackear en el worktree · [x]
`features.json` en `in_progress`, que es el estado real.

## Cobertura requisito → test

| Req. | Test(s) |
|---|---|
| R1–R6 | `test_f116_cabecera_api.py` (46: repositorio sobre SQLite, servicio con deshacer, ruta; R2 incluye `test_f116_r2_el_repositorio_rechaza_otros_campos_sin_escribir`) |
| R7–R9 | `test_f116_autoguardado_js.py::test_f116_r7_*`, `r8_elegir_en_el_calendario_guarda`, `r9_*` |
| R10–R12 | `test_f116_ficha.py` (r10, r12) y `test_f116_autoguardado_js.py::test_f116_r10_*`, `r11_*`, `r12_*` |
| R13–R17, R20 | `test_f116_autoguardado_js.py::test_f116_r13_*` … `r17_*`, `r20_enter_sigue_siendo_guardar_y_bloquear` |
| R18 | `test_f116_lineas_api.py` (6, con contraste `?bloquear=1`) |
| R19 | citado: `albaran-valoracion-persist/tests/test_f106_reaplicar.py::test_f106_r25_r32c_cantidad_editada_sobrevive_con_el_precio_nuevo` (su `_editar` no escribe `bloqueada`; verificado) |
| R21–R23, R25 | `test_f116_r21_*`, `r22_*` (3 + Guardar todas), `r23_r25_guardar_y_aprobar_con_el_cursor_en_la_fecha`, `r23_*` |
| R24, R27 | `test_f116_r24_*` (serie, orden, GET sin esperar, fallo no rompe), `r27_beforeunload_*` |
| R26 | `test_f116_r26_un_409_no_se_reintenta_solo`, `r26_un_409_de_linea_*` |
| R28 | `test_f116_r28_*` (etiqueta, refresco, solo los que van bien) |
| R29, R30 | suite completa de sv4 en verde (2501); tests viejos juzgados abajo |
| R31 | revisado: `ARCHITECTURE.md` regla 20, `sv4.md` (tabla y nota F-077), `azure-apps` `ec9ed4d` (local, sin push) |
| R32 | MANUAL (T13/T14), fuera de esta review |

## Juicio de las desviaciones del informe (§3)

1. **`test_f098_r21` 3 ⇒ 4: ACEPTADA.** R30 prohíbe *relajar* aserciones salvo las declaradas; esto no relaja: la
   cuenta exacta sube por la misma cuarta vía que R30 ya autoriza en `test_f106_r12`, y se **añade** una aserción
   (`autoguardarFila` usa `_camposCambiados(tr, lista.items)`), así que la regla de F-098 (mandar el código de la
   lista) queda más protegida. Fallo de la spec, no del código: ver propuesta P1.
2. Listas de funciones extraídas en tests viejos: aceptada; solo añade dependencias, ninguna aserción cambia.
3. `wireAutoguardadoFilas()` aparte de `wireConciliaEdit()`: aceptada; mismo orden de enganche (lo fija
   `test_f116_r13_se_engancha_despues_de_los_combos_de_partida`).
4. **Comparar con lo último ENCOLADO: ACEPTADA.** Con la comparación literal, A→B (en cola)→A no enviaba nada y
   quedaba guardado B, contra el objetivo de R7 («guarda lo escrito»). Repasado el turno (`_turnoCola`): si B
   falla con A ya en cola, A viaja; si B falla solo, `_enCola` vuelve a `undefined` y el siguiente `blur` compara
   con `data-guardado`, así que R11 (reintento) se mantiene. Lo fija `test_f116_r11_lo_que_se_vuelve_a_dejar_*`.
5–8. Aceptadas: `filasParaGuardar` deja el filtro en la función compartida; «Guardar todas» espera a la Cola antes
   de decidir «No hay cambios» (necesario para R23); quitar `data-autoguardada` al bloquear evita un 409 en el
   reintento; `new Event` sin datos basta.
9. `globalThis.fetch` con `bind`: aceptada (correcto en navegador y en node).
10–12. Aceptadas (literales de la spec; R19 citado y verificado; R18 sin RED posible).

## Puntos de riesgo pedidos por el líder

- **Cola y `fetch`:** solo se instala con `#autoguardado-estado` (ficha editable); el resto de páginas de sv4 que
  cargan `app.js` (`base.html`) siguen con el `fetch` original. GET/HEAD salen sin esperar; todo lo demás, en serie.
  Las tareas internas de la Cola usan `fetchRed` (sin interbloqueo); `cargarPartidasObra` y `avisoSumaVigente` son
  GET. No hay `new Request`, `XMLHttpRequest` ni `sendBeacon` en `app.js`. Los `<form method="post">` de la ficha
  (desaprobar, alta en Sigrid) solo existen con el albarán aprobado, donde no hay Cola ni autoguardado.
- **Nunca `?bloquear=1` en el autoguardado:** `autoguardarFila` pasa `{bloquear: false}`; `enviarFila` es la única
  que arma la URL (dos tests lo fijan). Las filas bloqueadas no son `concilia-editable` y no se enganchan; aunque un
  `blur` llegara tarde, el servidor da 409 a una fila guardada.
- **PATCH de cabecera:** `extra="forbid"` + lista blanca en el repositorio; el ORM solo emite UPDATE de las
  columnas tocadas (los 4 campos y los 2 sellos). No relanza contratos. El deshacer guarda la fila entera del merge,
  igual que el PUT de siempre (ver O2).
- **Botones:** los tres (y el «Guardar» de fila) hacen `await encolar(noop)` antes de elegir/armar, y sus PATCH y
  el PUT pasan por el `fetch` envuelto; siguen con `?bloquear=1`. «Guardar y aprobar» con cursor en la fecha:
  PATCH de cabecera antes del PUT (test R23/R25).
- **`beforeunload`:** solo con `pendientes > 0`; el contador baja antes de que el llamante siga (el `then` se
  engancha dentro de `encolar`), así que los `reload()` tras guardar no piden confirmación.
- **409:** no hay reintento automático en ninguna de las dos vías.

## Observaciones (no bloquean)

- **O1.** La Cola solo distingue el método en `fetch(url, init)`. Un `fetch(new Request(url, {method: "POST"}))`
  futuro se saltaría la Cola sin que nada lo avise. Hoy no existe ninguno.
- **O2.** Deshacer un autoguardado de cabecera restaura la fila entera del merge (como el PUT): si sv3 escribió el
  contrato después, el deshacer lo devolvería a como estaba. Comportamiento heredado, no introducido aquí.
- **O3.** Para T13, conviene mirar en Red que, tras salir de una celda y pulsar «Guardar todas», la fila
  autoguardada sale con `{}` y `?bloquear=1` (D2 = a), y que «✋» aparece al recargar.

## Cambios requeridos

Ninguno.

## Propuestas de automejora (para el humano, no aplicadas)

- **P1 (spec, F-116 R30):** anotar `test_f098_r21_los_guardados_mandan_el_cod_de_la_lista` junto a
  `test_f106_r12` (misma cuenta 3 ⇒ 4), para que la lista de R30 sea la real.
- **P2 (`specs/SPECS.md` o plantilla de design, genérico → `arnes-base`):** cuando una spec declare tests viejos
  que cambian por un **recuento** (`count(...) == N`), pedir al spec-author que haga `grep` de ese mismo literal en
  toda la suite: aquí había dos tests contando lo mismo y la spec solo vio uno.
- **P3 (sv4, test):** un test que falle si aparece `new Request(` en `app.js` mientras la Cola dependa de
  `init.method` (O1).
