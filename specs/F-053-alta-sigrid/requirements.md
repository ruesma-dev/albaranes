<!-- specs/F-053-alta-sigrid/requirements.md -->
# F-053 · Alta en Sigrid de los albaranes aprobados · Requisitos (v7)

Rigor **critico** (escribe en el ERP). Servicios: **sv9 nuevo** (`services/albaranes-alta-sigrid`), sv4, sv3 (DDL
y R45), sv6 (DDL), `ruesma_comun`, `infra`. Sustituye a F-013. Decisiones (P1–P7, D1–D4): `progress/spec_F-053.md`.
«Contrato» = `sigrid-api/specs/F-009-alta-albaran-compra/contrato_albaranes.md` (v8.2, `13fd99d`; huecos **Hn**, §5).

## Glosario

- **Alta**: la fila de `albaran_altas_sigrid` de un documento (una por documento); solo la escribe sv9. Estados:
  `en_curso`, `no_admitido`, `ya_en_sigrid`, `simulado`, `revisar`, `error`, `incierto`, `registrado`, `anulado`.
- **Bloqueante**: `en_curso`, `incierto` o `registrado`. **Espera**: `ALTA_SIGRID_ESPERA_INCIERTO_MIN` (15) min
  desde el último intento. **Modo**: `simulacion` si `ALTA_SIGRID_COMMIT` no es literalmente `true`; si lo es,
  `real`. **DESDE**: `ALTA_SIGRID_DESDE_UTC`; vacía = feature apagada.
- **Vinculada**: casa con una línea del contrato de la valoración con `sigrid_ide`, sin `derived_contrato_line_id`.
  Las demás (también la «ALM» impresa, H30): **sin vincular**. **Línea a registrar**: `importe_calculado` no nulo
  y ≠ 0 (positivo o negativo). **Cantidad**: la convertida si es vinculada; si no, la del albarán. **Sin partida**
  (= almacén, F-051 v4): `codigo_partida_final` vacío, tenga o no marca en `partida_action`. **Previa**: `commit=false`.
- **Producto** de una sin vincular: el elegido en sv4 (`producto_sigrid`) o, si no hay, el que da el **mapeo**
  `ALTA_SIGRID_PRODUCTO_POR_DEFECTO` (familia → código, clave `*` obligatoria; defecto `alquiler_maquinaria` →
  `QA9999`, `medios_auxiliares` (F-061) → `XA9999`, `*` → `MA9999`) a su `familia_efectiva` (`ruesma_comun.contratos.
  familias`: la de la línea, si no la del documento salvo mixto; sin familia, `*`). **Admitidos**: los del mapeo.
- **Valorado**: valoración de sv6 en `ok`, o manual completa del administrativo en sv4 (cabecera `manual` o
  `no_contract` con alguna línea con importe ≠ 0 y ninguna con importe nulo).

## A. Disparo en sv4
R1. CUANDO un documento no aprobado pasa a aprobado (POST `/documents/{id}/approve` o PUT
`/api/documents/{id}` con `approved=true`) y DESDE no está vacía, sv4 debe publicar en `q-feedback` un
`MensajeFeedback` con `accion="alta"`, el `document_id` y `approved_by`.
R2. CUANDO se guarda o aprueba un documento ya aprobado, sv4 no debe publicar.
R3. MIENTRAS DESDE esté vacía, sv4 debe comportarse como hoy: no publica ni pinta nada del alta ni del producto.
R4. SI falla la publicación de R1, ENTONCES sv4 debe mantener la aprobación y avisar de que el alta no se pidió.

## B. Entrada en sv9
R5. CUANDO sv9 recibe un mensaje de alta, debe, en una transacción con la fila del merge bloqueada
(`FOR UPDATE`), comprobar que el documento existe, está activo y aprobado con `approved_at_utc` ≥ DESDE, y
dejar el alta en `en_curso` (creándola si falta), guardando `approved_at_utc`, `approved_by` e `intentos + 1`.
R6. SI el documento no existe, no está aprobado, está en la papelera, se aprobó antes de DESDE o DESDE está
vacía, ENTONCES sv9 debe confirmar el mensaje sin tocar el alta ni llamar a sigrid-api.
R7. SI el alta está en `ya_en_sigrid`, `registrado` con adjunto colgado, o en `en_curso`/`incierto` sin
pasar la Espera, ENTONCES sv9 debe confirmar sin cambiar nada.
R8. SI el alta lleva en `en_curso` más que la Espera, ENTONCES sv9 debe pasarla a `incierto` sin llamar a sigrid-api.
R9. Tras R5, toda salida de sv9 (también por excepción) debe dejar el alta fuera de `en_curso`: `incierto`
si la grabación estaba en vuelo, `error` si no.

## C. Validación local (sin llamar a sigrid-api)
R10. sv9 debe declarar `no_admitido`, con **todos** los motivos a la vez, si: falta obra (`falta_obra`),
CIF (`falta_cif`) o número de albarán (`falta_numero_albaran`); el CIF normalizado (mayúsculas, sin espacios,
guiones ni puntos, sin `ES` delante de 9 caracteres) no es alfanumérico (`cif_no_valido`, H21); obra, CIF,
contrato o una partida pasan de 24 caracteres o el número de 128 (`campo_demasiado_largo`, H6); la fecha no
es `AAAA-MM-DD` válida (`fecha_ilegible`, local); no está valorado (`no_valorado`); no hay líneas a registrar
(`sin_lineas`); una tiene cantidad nula o 0 (`cantidad_no_valida`); una vinculada no tiene cantidad
convertida (`cantidad_sin_convertir`); una sin vincular no tiene descripción ni en la valoración ni en el
merge (`falta_descripcion`, H6); o el producto de una sin vincular no es admitido (`producto_no_admitido`).
R11. Casar con el contrato NO es requisito: una sin vincular es admisible igual que una vinculada, con
partida o sin ella, y una negativa igual que una positiva. Una línea sin partida nunca es motivo (F-051 v4).
R12. CUANDO el documento es admisible, sv9 debe construir la petición del modo extendido de `sigrid/albaran`
(contrato §2): `cod_obra`, `cif_proveedor` normalizado, `cod_contrato` de la valoración si lo tiene, también
sin vinculadas (H31), `referencia_externa` = `ALB-{document_id}`, `su_referencia` = número recortado,
`usu` = `ALTA_SIGRID_USUARIO` (H1), `fecha_albaran` en `AAAAMMDD`, `empide` = `ALTA_SIGRID_EMPIDE` o nulo,
nunca `lineas_recibidas` ni `naturaleza` (H34); y en `lineas`, una por línea a registrar, por `line_index` de su
línea del merge y las que no la tienen al final por `id` (H26): `referencia_linea` = id de la línea valorada
(≤ 24); vinculada, `ctrpro_ide` sin `unidad` ni `descripcion` (H7); sin vincular, su `producto`, `descripcion`
recortada a 128 y `unidad` a 8; `partida` = `codigo_partida_final` si no está vacío y, si lo está, ninguna clave
de partida (no hay campo `almacen`, H5); sin `paride` (H17; evolución con F-049, design §8); `precio` = |importe|
/ |cantidad| a 6 decimales (H14) y `cantidad` con el signo del importe (opuestos: R39): `cantidad·precio` = importe.
R13. sv9 debe dejar fuera de la petición las líneas con importe nulo o 0, también las vinculadas con cantidad (H29).

## D. Duplicados e idempotencia
R14. Antes de la previa, sv9 debe buscar en Sigrid (`sql/read`) albaranes de compra (`con.tip` 14) con el mismo
`dca.entcif` (normalizado) y `dca.entref` y otro `synckey` (altas a mano); si hay alguno, el alta pasa a
`ya_en_sigrid` con sus `ide` y `cod`, sin previa ni grabación.
R15. CUANDO la previa o la grabación respondan `estado` `idempotente`, sv9 debe pasar a `registrado` con su
`con_ide` y `cod` sin grabar nada; SI además algún `total` por `referencia_linea` difiere de lo pedido como en
R17, ENTONCES debe guardar el motivo `registrado_distinto` y enseñarlo en sv4 (H18; se corrige anulando,
R28). Un alta `incierto` pasada la Espera se retoma reenviando la misma petición.

## E. Previa, comparación y grabación real
R16. sv9 debe hacer la previa en los dos modos y guardar la petición y, de la respuesta, solo `estado`, `con_ide`,
`cod`, `avisos`, `lineas` y `totales`; nunca `cabecera` ni `filas` (H16).
R17. sv9 debe pasar el alta a `revisar`, con motivo, si en la previa: el `total` de una línea (por
`referencia_linea`) difiere de su `importe_calculado` en más de `ALTA_SIGRID_TOLERANCIA_EUR` (0,05)
(`importe_distinto`); falta o sobra una línea (`lineas_distintas`); su `partida` no es la pedida, también nula
frente a no nula (`partida_distinta`); o un aviso, de cabecera o de línea, tiene un `codigo` de
`ALTA_SIGRID_AVISOS_BLOQUEANTES` (`aviso_bloqueante`). Los demás se guardan y se enseñan.
R18. SI sigrid-api responde 400 (previa o grabación), ENTONCES sv9 debe llevar el alta al estado de la tabla de
design §2 según `details.codigo` (código que no esté en ella: `error`, H25), guardando `error`, `codigo` y `details.lineas`.
R19. MIENTRAS el modo sea `simulacion`, una previa sin motivos deja el alta `simulado` y sv9 nunca manda `commit=true`.
R39. SI no hay motivos de R10 y la fecha del albarán es posterior a hoy (Europe/Madrid) o anterior a hoy − 365
días (`fecha_no_plausible`, H19) o una línea a registrar tiene cantidad > 0 e importe < 0 (descuento) o cantidad
< 0 e importe > 0 (`signo_incoherente`, H8, con su `referencia_linea`), ENTONCES sv9 debe pasar el alta a
`revisar` con todos esos motivos sin llamar a sigrid-api. El descuento se da de alta a mano en Sigrid.
R46. SI una línea a registrar casa con una línea de contrato de un contrato distinto del de la valoración (D2), ENTONCES
es un motivo de R39 (`linea_de_otro_contrato`, con su `referencia_linea`) y sv9 debe dejar una ANOMALÍA en el log
(WARNING con documento, línea y los dos contratos; sin precios): indica un fallo aguas arriba (sv5/sv6).
R20. DONDE el modo sea `real`, tras una previa sin motivos sv9 debe repetir la misma petición con `commit=true`
**una sola vez**, sin reintento automático, y con `ok` y `estado` `creado` guardar `con_ide` y `cod` y pasar a `registrado`.
R21. SI hay tiempo agotado, error de conexión o 5xx, ENTONCES el alta pasa a `incierto` (grabación) o `error` (previa).
R22. CUANDO un alta queda `registrado` en modo `real`, sv9 debe adjuntar el PDF (de SharePoint) con
`concepto-grafico` (`contip` 14, `gratipide` 0, `usu` = `ALTA_SIGRID_USUARIO`, `sha256`); colgado = `ok` y
(`committed` o `idempotente`).
R23. SI el adjunto falla, ENTONCES el alta sigue `registrado` con el adjunto en error y otro mensaje de alta solo lo reintenta.
R24. sv9 debe reintentar con espera creciente lecturas, previas y adjunto ante fallos transitorios; nunca la grabación.

## G. Bloqueo y visibilidad en sv4
R25. MIENTRAS el alta sea bloqueante, sv4 debe rechazar desaprobar, guardar, deshacer, borrar, purgar, revalorar,
volver a buscar contratos, elegir producto (R41) y toda edición de líneas, sin cambiar nada y con el aviso
«Registrado en Sigrid como {cod}: corrígelo en Sigrid y pulsa "Ya lo he anulado en Sigrid"» (sin `cod` si no hay).
R26. Las operaciones de R25 que escriben en BBDD deben comprobar el alta dentro de su transacción, con la
fila del merge bloqueada (`FOR UPDATE`).
R27. El borrado múltiple y el vaciado de la papelera deben saltarse los bloqueantes y decir cuántos se saltaron.
R28. CUANDO el revisor pulsa «Ya lo he anulado en Sigrid» en un alta `registrado`, sv4 debe publicar
`accion="verificar_anulacion"`; sv9 debe pasar el alta a `anulado` solo si `sql/read` no encuentra ese
`con.ide`, y si lo encuentra dejarla `registrado` con el aviso «sigue en Sigrid». Tras `anulado`, «Solicitar alta»
repite el alta con la misma `referencia_externa` (anular en Sigrid borra el albarán, H9).
R29. MIENTRAS DESDE no esté vacía, la ficha de un documento aprobado debe enseñar el alta: estado, modo,
`cod` (en simulación, «se habría creado» con el código provisional), líneas (con su producto) y total de la
previa, motivos (también los de cada línea de `details.lineas`), avisos y adjunto.
R30. La ficha debe ofrecer «Solicitar alta en Sigrid» (`accion="alta"`) si el documento aprobado tiene
`approved_at_utc` ≥ DESDE y el alta falta, está en `no_admitido`/`revisar`/`error`/`simulado`/`anulado`, o
pasó la Espera en `incierto`/`en_curso`.
R31. El listado debe mostrar el estado del alta en cada documento aprobado que la tenga.

## H. Producto de las sin vincular (decisión del humano, 2026-10-05)
R40. MIENTRAS DESDE no esté vacía, la tabla de líneas valoradas de la ficha debe enseñar en cada sin
vincular a registrar su producto (código y nombre, «por defecto» si no se ha elegido) con un selector de los
admitidos, y en cada vinculada el producto de su línea de contrato, sin selector.
R41. CUANDO el administrativo elige un producto (o «por defecto») en una sin vincular, sv4 debe guardarlo en
`albaran_line_valuations.producto_sigrid` (`NULL` = por defecto) con su entrada de deshacer; SI la línea no es
del documento, es vinculada o el código no es admitido, ENTONCES debe responder 400 sin cambiar nada.
R42. CUANDO se revalora el documento, el producto elegido se pierde y la línea vuelve al de defecto, como el
almacén elegido (F-051 D5); conservarlo al revalorar es de F-058.
R43. sv9 debe ignorar `producto_sigrid` en una vinculada (manda `ctrpro_ide`).
R44. SI `ALTA_SIGRID_PRODUCTO_POR_DEFECTO` no es un objeto JSON de textos con clave `*`, ENTONCES sv9 y sv4
no deben arrancar, con el motivo en el log.

## I. Contratos y seguridad
R32. `MensajeFeedback` debe aceptar `accion` ∈ {`alta`, `verificar_anulacion`}, con defecto `alta`.
R33. sv9 solo debe llamar a `sql/read`, a `sigrid/albaran` (modo extendido) y a `concepto-grafico`.
R34. Solo sv9 debe escribir en `albaran_altas_sigrid`; sv4 solo la lee.
R35. Ni los logs ni el alta deben guardar la clave de sigrid-api, el PDF ni datos bancarios.
R36. El DDL de `albaran_altas_sigrid` debe vivir en sv3 y el de `producto_sigrid` en sv6, los dos idempotentes.
R37. SI el revisor aprueba (por cualquiera de los dos caminos de R1) un documento no valorado, ENTONCES sv4
debe rechazarlo sin cambiar nada, con el aviso «No se puede aprobar un albarán sin valorar», con DESDE vacía o no.
R38. sv4 y sv9 deben decidir «valorado» con `ruesma_comun` `esta_valorado` (R37, R10) y el producto con
`ruesma_comun.alta_sigrid.producto_efectivo` (R40, R43).
R45. SI sv3 reingresa un PDF (mismo `source_sha256`) y un merge con ese hash, activo o en la papelera, tiene un alta
bloqueante, ENTONCES, antes de subir nada a SharePoint, sv3 debe devolverlo como duplicado sin tocar nada: ni borrar,
ni reescribir clasificación o contexto de líneas, ni resolver cabecera, ni enriquecer obra o contratos, ni revalorar;
conserva documento, merge y alta, y lo deja en el log («un albarán no se puede pisar»; D1, D3).
