<!-- specs/F-077-guardar-y-aprobar/requirements.md -->
# F-077 · Ficha: guardar y aprobar de una vez · Requisitos (v1, 2026-10-16)

Servicio: **sv4** únicamente (`services/albaranes-front`). Rigor `estandar`. Alcance aprobado por el humano en la
PARADA 1 (2026-10-16); decisiones y preguntas abiertas en `progress/spec_F-077.md`. **Sustituye a F-065 R19** (el
aviso «Hay N líneas con cambios sin guardar»); F-065 R21 (confirmación de la suma) se mantiene.

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

## B. Panel «Alta en Sigrid»: «Alta en curso…» hasta que responda sv9

- R14. El alta de un documento está **pendiente** SI el documento admite alta (feature activa; aprobado; activo;
  `approved_at_utc` ≥ DESDE: la regla de F-053 R6/R30) Y además:
  (a) no hay fila en `albaran_altas_sigrid`, o su estado es repetible (`ESTADOS_ALTA_REPETIBLES` de comun, los que sv9
  vuelve a procesar) y su `approved_at_utc` es nulo, ilegible o anterior al `approved_at_utc` del merge, y no ha
  pasado la Espera desde el `approved_at_utc` del merge; o
  (b) la fila es de la aprobación vigente (mismo instante), está `en_curso` y no ha pasado la Espera desde su
  `ultimo_intento_at_utc`.
  En cualquier otro caso no está pendiente. Los instantes se comparan como instantes UTC (`leer_instante_utc`), no
  como texto, y la Espera con `espera_pasada` de comun.
- R15. MIENTRAS el alta esté pendiente, el panel (`#alta-sigrid`) debe pintar «Alta en curso…» y «La ficha se
  actualizará sola cuando Sigrid responda.», con `data-pendiente="1"` y el id del documento en `data-document-id`, y
  NO debe pintar nada del resultado anterior (estado, modo, código, intentos, usuario, aviso, motivos, líneas,
  totales, avisos) ni sus botones («Solicitar alta en Sigrid», «Reintentar adjunto», «Ya lo he anulado en Sigrid»).
  Incluye el caso sin fila de sv9 tras aprobar: ni «Sin alta en Sigrid todavía.» ni «Solicitar alta en Sigrid».
- R16. sv4 debe exponer `GET /api/documents/{id}/alta-sigrid/pendiente`, que responde `{"pendiente": <bool>}` con
  R14 (solo lectura: estado de aprobación del merge y alta, sin cerrojo); 404 si el documento no existe; con la
  feature apagada (DESDE vacía), `{"pendiente": false}` sin leer el alta.
- R17. MIENTRAS el panel tenga `data-pendiente="1"`, la ficha debe consultar R16 cada 3 s durante el primer minuto y
  cada 15 s después; CUANDO responda `pendiente: false`, debe recargar la página una sola vez. Un error de red o una
  respuesta no ok distinta de 404 no paran el sondeo; un 404 lo para. Sin `data-pendiente="1"`, ninguna consulta.
- R18. sv4 no debe escribir `albaran_altas_sigrid` (F-053 R34) ni publicar en ninguna cola por pintar el panel ni
  por sondear.
- R19. Fuera de pendiente, el panel debe ser el de hoy (F-053 R29, R30), incluido «Sin alta en Sigrid todavía.».

## C. Tooltip del ⚠ de la partida

- R20. CUANDO una fila con línea del albarán (`from_albaran`) tiene `agree_partida == false`, la casilla de partida
  editable (clase `cedit-warn`) y el ⚠ de la ficha en solo lectura deben llevar en el `title`, después de la
  descripción de la partida (si la hay) y en línea aparte, «No coincide con la partida leída en el albarán (<código
  leído>)», donde el código leído es el `codigo_imputacion` de su línea del albarán, recortado.
- R21. CUANDO una fila sin línea del albarán (sintética, `manual` o `reparto`) tiene `agree_partida == false`, el
  texto debe ser «No coincide con la partida de su línea de contrato (<código>)»: en esas filas `agree_partida`
  compara la partida final con la de su línea de contrato, no con nada leído.
- R22. El cálculo de `agree_partida` no cambia. Con `agree_partida` true o nulo, el `title` debe ser el de hoy. El
  aviso «Partida no válida…» de F-065 R27 v5 sigue sustituyendo el `title` mientras la casilla esté en rojo y, al
  corregirla, debe volver el de R20/R21.

## D. Motivos de línea que hoy no se ven (ampliación del 2026-10-16, misma PARADA 1)

Caso real: documento `86c13097-…`, `no_admitido` con `motivos_json = [{"codigo": "falta_descripcion", "detalle": "",
"referencia_linea": "386"}]` y `peticion_json`/`respuesta_json` vacíos (sv9 rechazó en local, antes de llamar a
Sigrid; la 386 es una línea manual sin descripción). `motivos_documento` descarta los que llevan `referencia_linea` y
la tabla `alta.lineas` sale de la petición, vacía: el panel decía «No admitido» sin ninguna razón.

- R25. Todo motivo del alta con `referencia_linea` que no casa con ninguna fila de la tabla de líneas del panel
  (`alta.lineas`, por `referencia_linea`) debe pintarse en la lista de motivos del panel, después de los del documento,
  como «Línea N: <texto legible>», seguido de « · <detalle>» si el detalle no está vacío y del código entre `<code>`.
- R26. N debe ser la posición de esa línea valorada en la tabla de líneas de la ficha (filas con conciliación, en el
  orden en que se pintan, desde 1; `referencia_linea` es el id de la línea valorada). SI no casa con ninguna fila de la
  ficha, ENTONCES «Línea (ref. <referencia_linea>)».
- R27. El texto legible debe salir de una tabla de sv4 por código, al menos: `falta_descripcion` «La línea no tiene
  descripción»; `cantidad_no_valida` «La línea no tiene cantidad (o es 0)»; `cantidad_sin_convertir` «La línea no tiene
  la cantidad en la unidad del contrato»; `producto_no_admitido` «Producto de Sigrid no admitido»;
  `campo_demasiado_largo` «Un campo de la línea es demasiado largo para Sigrid»; `signo_incoherente` «La cantidad y el
  importe tienen signos distintos»; `linea_de_otro_contrato` «La línea es de otro contrato»; `lineas_distintas` «La
  línea no coincide con lo que devolvió Sigrid»; `importe_distinto` «El importe no coincide con el de Sigrid»;
  `registrado_distinto` «Lo registrado en Sigrid no coincide con la línea»; `partida_distinta` «Sigrid devolvió otra
  partida»; `aviso_bloqueante` «Sigrid dio un aviso que impide el alta»; `partida_no_encontrada` «La partida no existe
  en la obra en Sigrid». Un código desconocido se enseña tal cual (nunca se pierde el motivo).
- R28. Los motivos de línea que sí casan con una fila de la tabla del panel deben seguir pintándose solo en su fila
  (F-053 R29), sin repetirse en la lista; los del documento, como hoy. MIENTRAS el alta esté pendiente, ninguno (R15).

## E. No funcionales

- R23. Los tests de los requisitos centrales (R1, R3, R4, R14, R15, R20, R25, R26) deben pasar por fase RED antes de
  su código; los tests no deben tocar red ni BBDD: el JS se ejecuta con node sobre `tests/dom_falso.js` (patrón de
  `test_f065_f3bis_front.py`) con `fetch`, `setTimeout`, `alert`, `confirm` y `location` falsos; el servidor con dobles
  y `TestClient`; las plantillas con `render_detalle`. Cada R tiene al menos un test `test_f077_rN_…`.
- R24. `docs/ARCHITECTURE.md` (reglas 19 y 20) y `services/albaranes-front/sv4.md` (tabla de endpoints) deben
  describir el comportamiento nuevo en el mismo trabajo.
