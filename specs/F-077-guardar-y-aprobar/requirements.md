<!-- specs/F-077-guardar-y-aprobar/requirements.md -->
# F-077 · Ficha: guardar y aprobar de una vez · Requisitos (v2, 2026-10-16)

Servicio: **sv4** únicamente (`services/albaranes-front`). Rigor `estandar`. Alcance APROBADO por el humano en la
PARADA 1 (2026-10-16, P1–P4 resueltas); decisiones en `progress/spec_F-077.md`. **Sustituye a F-065
R19** (el aviso «Hay N líneas con cambios sin guardar»); F-065 R21 (confirmación de la suma) se mantiene.

Vocabulario: **fila con cambios** = fila editable (`tr.concilia-editable`) con id de valoración y cuerpo de PATCH no
vacío (`_camposCambiados`, F-065 R8); **PATCH de fila** = `PATCH /api/documents/{id}/lines/{vid}/conciliacion/campos
?bloquear=1` con solo los campos cambiados (el del «Guardar» de cada fila, F-065 R13); **PUT de cabecera** =
`PUT /api/documents/{id}` (F-065 R1); **Espera** = `ALTA_SIGRID_ESPERA_INCIERTO_MIN` (F-053, 15 min por defecto).

## A. «Guardar y aprobar» y «Guardar» guardan antes las filas

- R1. CUANDO el administrativo pulsa «Guardar y aprobar» (`#approve-btn`) o «Guardar» de la cabecera (`#save-btn`),
  la ficha debe enviar primero, una a una y en el orden de la tabla, el PATCH de fila de cada fila con cambios y, solo
  si todos responden ok, el PUT de cabecera (`approved` true con «Guardar y aprobar», false con «Guardar»).
- R2. SI no hay filas con cambios, ENTONCES la ficha no debe enviar ningún PATCH y el resto del flujo es el de hoy
  (con «Guardar y aprobar», la confirmación de R6 con el `data-aviso-suma` pintado; después el PUT).
- R3. Antes de enviar nada, la ficha debe esperar la lista de partidas de la obra y, tras la espera y en el mismo
  tick, calcular las filas con cambios, validarlas con la regla de F-065 R27 v5 y armar sus cuerpos (lo validado es lo
  enviado, F-065 CR4). SI alguna partida cambiada no es de la lista, ENTONCES no debe enviar ningún PATCH ni el PUT,
  debe dejar esa casilla en rojo y avisar «Hay partidas no válidas (en rojo): elige una de la lista o déjala vacía
  (almacén).».
- R4. SI un PATCH de fila falla (respuesta no ok o error de red), ENTONCES la ficha debe parar sin enviar más PATCH ni
  el PUT, marcar esa fila en rojo (clase `fila-no-guardada` en el `tr` y el motivo en su `title`) y avisar «No se pudo
  guardar una línea (en rojo): <motivo>.» seguido de «No se ha aprobado el albarán.» («Guardar y aprobar») o «No se ha
  guardado la cabecera.» («Guardar»). No recarga la página. El motivo es el `detail` del servidor como hoy.
- R5. Las filas guardadas antes de un fallo quedan guardadas y bloqueadas (no atómico, aceptado por el humano). La
  ficha debe consolidar cada fila nada más guardarla (lo enviado pasa a ser su valor inicial, sin `cedit-dirty`, con
  sus casillas y su «Guardar» desactivados), de modo que un segundo intento no la reenvíe.
- R6. CUANDO se pulsa «Guardar y aprobar» y hay aviso de suma, la ficha debe pedir confirmación con él antes del PUT
  (F-065 R21). SI se guardó al menos una fila en este intento, ENTONCES el aviso debe ser el vigente tras guardarlas
  (`aviso_suma` de `GET /api/documents/{id}`), no el pintado al cargar.
- R7. SI el administrativo cancela esa confirmación, ENTONCES no se aprueba; con filas guardadas en este intento, la
  ficha debe recargarse; sin ninguna, no hace nada más.
- R8. SI la lectura del aviso vigente (R6) falla, ENTONCES no se aprueba: la ficha debe avisar «No se pudo comprobar la
  suma de las líneas: recarga y vuelve a aprobar.» y recargarse.
- R9. SI el PUT de cabecera falla tras haber guardado filas en este intento, ENTONCES la ficha debe dar el aviso de
  hoy («Error al guardar: <detalle>») y recargarse; sin filas guardadas, como hoy (aviso, sin recargar).
- R10. Mientras dura el flujo, «Guardar» y «Guardar y aprobar» deben estar desactivados: un segundo clic no repite
  ningún PATCH ni el PUT. Al parar sin navegar (R3, R4, R7 sin filas guardadas) vuelven a estar activos.
- R11. El servidor no cambia: el PATCH de fila, el PUT de cabecera y sus validaciones (F-065 R4, R14, R20, R25; F-053
  R25, R37) son los de hoy; las filas sin cantidad o importe (F-065 R20) las sigue rechazando el PUT.
- R12. El «Guardar» de cada fila, «Guardar todas» y R1 deben enviar el PATCH de fila con una única función compartida
  de `app.js` (sin copias de la petición ni de la lectura del motivo); los dos primeros no cambian de comportamiento.
- R13. La ficha no debe volver a avisar «Hay N líneas con cambios sin guardar» (F-065 R19 sustituido por R1–R10).

## B. Panel «Alta en Sigrid»: «Alta en curso…» solo mientras sv9 procesa

- R14. La **fase** del panel debe ser:
  · `en_curso` SI el documento admite alta (feature activa; aprobado; activo; `approved_at_utc` ≥ DESDE: la regla de
  F-053 R6/R30), no han pasado **5 minutos** desde el `approved_at_utc` del merge y además: (a) no hay fila en
  `albaran_altas_sigrid`; o (b) la fila es de una aprobación anterior (su `approved_at_utc` nulo, ilegible o anterior al
  del merge) y su estado es repetible (`ESTADOS_ALTA_REPETIBLES` de comun: los que sv9 vuelve a procesar); o (c) la
  fila es de la aprobación vigente (mismo instante) y está `en_curso`;
  · `sin_respuesta` en esos mismos casos (a)–(c) cuando ya han pasado los 5 minutos;
  · `resultado` en cualquier otro caso (también con un estado que sv9 ignora ante la nueva aprobación, como
  `ya_en_sigrid` o `registrado`: esa fila es la respuesta).
  Los instantes se comparan como instantes UTC (`leer_instante_utc` de comun), no como texto.
- R15. MIENTRAS la fase sea `en_curso`, el panel (`#alta-sigrid`) debe pintar «Alta en curso…» y «La ficha se
  actualizará sola cuando Sigrid responda.», con `data-fase="en_curso"` y el id del documento en `data-document-id`, y
  NO debe pintar nada del resultado anterior (estado, modo, código, intentos, usuario, aviso, motivos, líneas,
  totales, avisos), ni «Sin alta en Sigrid todavía.», ni ningún botón.
- R16. CUANDO la fase sea `sin_respuesta`, el panel debe pintarse como error (clase `error`) con «Sigrid no ha
  respondido en 5 minutos. El alta aún puede completarse: recarga la página más tarde para ver el resultado.», sin el
  resultado anterior, sin sondear, y con «Solicitar alta en Sigrid» solo si `alta_puede_solicitar` (F-053 R30, sin
  cambios: con fila `en_curso` no se ofrece hasta la Espera, porque sv9 lo ignoraría, F-053 R7).
- R17. CUANDO la fase sea `resultado`, el panel debe ser el de hoy (F-053 R29, R30), salvo que con estado
  `no_admitido`, `revisar` o `error` debe pintarse como error (clase `error`, «Error en el alta en Sigrid: <estado>»)
  con todos sus motivos (D). Los demás estados, como hoy.
- R18. sv4 debe exponer `GET /api/documents/{id}/alta-sigrid/fase`, que responde `{"fase": "en_curso" |
  "sin_respuesta" | "resultado"}` con R14 (solo lectura: estado de aprobación del merge y alta, sin cerrojo); 404 si
  el documento no existe; con la feature apagada (DESDE vacía), `"resultado"` sin leer el alta.
- R19. MIENTRAS el panel tenga `data-fase="en_curso"`, la ficha debe consultar R18 cada **3 s fijos**; CUANDO la fase
  deje de ser `en_curso`, debe recargar la página una sola vez. Un error de red o una respuesta no ok distinta de 404 no
  paran el sondeo; un 404 lo para. Con otra fase, ninguna consulta. El tope de 5 min lo decide el servidor (R14).
- R20. sv4 no debe escribir `albaran_altas_sigrid` (F-053 R34) ni publicar en ninguna cola por pintar el panel ni
  por sondear.

## C. El ⚠ de la partida: solo con lectura del albarán, y con tooltip

- R21. La casilla de partida (clase `cedit-warn`) y el ⚠ de solo lectura deben pintarse SOLO en filas con línea del
  albarán (`from_albaran`) de origen Contrato (`kind == "assigned"`) con `agree_partida == false`. En filas sin línea
  del albarán (sintéticas, `manual`, `reparto`) y en las Nueva, nunca (la insignia «Nueva» ya dice que no coincide con
  el contrato).
- R22. Donde haya ⚠ (R21), el `title` debe llevar, después de la descripción de la partida (si la hay) y en línea
  aparte, «No coincide con la partida leída en el albarán (<código leído>)», con el `codigo_imputacion` de su línea
  del albarán, recortado.
  > Nota 2026-10-17 (implementación, aceptado en review): separador « · », no línea aparte (el de la nota de F-076): `title` =
  > «descripción · [Normalizada: X → Y, F-076] · No coincide con…»; la nota y el aviso se excluyen.
- R23. El cálculo de `agree_partida` y el ✓ (`cedit-ok`) no cambian. Sin ⚠, el `title` es el de hoy. El aviso
  «Partida no válida…» de F-065 R27 v5 sigue sustituyendo el `title` mientras la casilla esté en rojo y, al
  corregirla, debe volver el de R22.

## D. Motivos del alta: siempre visibles y legibles

Caso real: documento `86c13097-…`, `no_admitido` con `motivos_json = [{"codigo": "falta_descripcion", "detalle": "",
"referencia_linea": "386"}]` y `peticion_json`/`respuesta_json` vacíos (sv9 rechazó en local, antes de llamar a
Sigrid; la 386 es una línea manual sin descripción). `motivos_documento` descarta los que llevan `referencia_linea` y
la tabla `alta.lineas` sale de la petición, vacía: el panel decía «No admitido» sin ninguna razón.

- R24. Todo motivo del alta con `referencia_linea` que no casa con ninguna fila de la tabla de líneas del panel
  (`alta.lineas`, por `referencia_linea`) debe pintarse en la lista de motivos, después de los del documento, como
  «Línea N: <texto legible>».
- R25. N debe ser la posición de esa línea valorada en la tabla de líneas de la ficha (filas con conciliación, en el
  orden en que se pintan, desde 1; `referencia_linea` es el id de la línea valorada). SI no casa con ninguna fila de la
  ficha, ENTONCES «Línea (ref. <referencia_linea>)».
- R26. Todo motivo del panel —del documento, de una fila de la tabla o suelto (R24)— debe pintarse con su **texto
  legible**, seguido de « · <detalle>» si el detalle no está vacío, y con el código en el `title` (no como texto). El
  texto sale de una tabla de sv4 por código (lista cerrada y textos en `progress/spec_F-077.md`, Anexo A; p. ej.
  `falta_descripcion` ⇒ «La línea no tiene descripción»); `http_<NNN>` ⇒ «sigrid-api respondió con HTTP <NNN>»; un
  código desconocido se enseña tal cual (nunca se pierde el motivo).
- R27. La tabla debe cubrir todo código que sv9 puede escribir hoy en `motivos_json`: un test lee como texto (sin
  importar sv9) `validador_alta.py`, `comparador_previa.py`, `clasificador.py`, `alta_sigrid_service.py` y
  `alta_models.py` (`TipoFallo`) de `services/albaranes-alta-sigrid` y falla si aparece un código sin texto.
- R28. Los motivos de línea que casan con una fila de la tabla del panel deben seguir pintándose solo en su fila
  (F-053 R29), sin repetirse en la lista. Con la fase `en_curso` o `sin_respuesta`, ninguno (R15, R16).

## E. No funcionales

- R29. Los tests de los requisitos centrales (R1, R3, R4, R14, R15, R16, R21, R24, R26) deben pasar por fase RED antes
  de su código. Ningún test toca red ni BBDD: el JS se ejecuta con node sobre `tests/dom_falso.js` (patrón de
  `test_f065_f3bis_front.py`) con `fetch`, `setTimeout`, `alert`, `confirm` y `location` falsos; el servidor con dobles
  y `TestClient`; las plantillas con `render_detalle`. Cada R tiene al menos un test `test_f077_rN_…`.
- R30. `docs/ARCHITECTURE.md` (reglas 19 y 20) y `services/albaranes-front/sv4.md` (tabla de endpoints) deben
  describir el comportamiento nuevo en el mismo trabajo.
