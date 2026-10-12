# F-065 · Lo editado en las líneas manda, la partida se elige de la obra y una línea se divide — requisitos (v3)

Rigor **critico** (lo aprobado es lo que sv9 da de alta en Sigrid, F-053). Servicios: **sv4-front** y
**sv6-valoracion-persist** (solo el DDL de `bloqueada`); sv9 y comun sin código (tests de contrato en sv9).
v2 = modelo del humano tras la PARADA 1 (2026-10-09): `progress/spec_F-065.md` §v2. Fuentes:
`progress/explore_F-065.md`, `progress/explore_front_detalle.md` y la tabla de `progress/propuestas_ficha_detalle.md`
(cada R cita su fila: M1–M4, X1–X11, X22, R6). **Fuera**: X4 (sugeridos de obra/proveedor) y el sumatorio X12 (F-066).

## Definiciones

- **Fila**: fila de `albaran_line_valuations` (lo que se aprueba). **Blanca**: línea del merge (lo leído).
- **Q** de una fila = `cantidad_convertida ?? cantidad_albaran`: la que enseña y edita la ficha, en la unidad del
  precio (`importe = precio × Q × (1 − dto/100)`, `ruesma_comun.importes`). **Reproducible**: F-036 R1.
- **Origen**: **Contrato** (antes «Sigrid»: `matched_contrato_line_id`, sin derivada) o **Nueva** (derivada). Lo
  decide la valoración (IA); al editar no se llama a la IA (respuesta 2 del humano).
- **Bloqueada**: fila guardada por el administrativo (columna `bloqueada`, R17).
- **Fila manual**: `line_kind` `manual` o `reparto`, bloqueada, con derivada `manual_override`, con
  `precio_unitario_agreement = 'manual'` o con `partida_action = 'almacen_elegido'`.

## Fase 1 · integridad (desplegar sola, antes de pasar F-053 a real)

### Cabecera y aprobado (M4, X3)
R1. El PUT `/api/documents/{id}` no debe tocar las líneas: ignora `lines` (no borra, no actualiza ni recalcula
nada de merge ni de valoración), y el front deja de mandarlas. Guardar la cabecera solo guarda la cabecera.

R2. CUANDO el administrativo deja 6 y 7 en dos filas Contrato de 8 y 10, trae una línea de contrato con 5 y luego
guarda la cabecera y aprueba, las filas deben quedar en 6, 7 y 5 y `total_valorado` en su suma (caso METALFIRE).

R3. El PUT no debe poner nunca `approved = false`; con `approved = true` sobre un pendiente, guarda la cabecera y
aprueba (con R20 y F-053 R37).

R4. SI el documento está aprobado, ENTONCES toda escritura de sv4 sobre él (PUT, edición, alta, borrado, bloqueo o
desbloqueo de filas, producto, almacén, traer, añadir, dividir, revalorar, volver a buscar) debe responder 409
«Albarán aprobado: desapruébalo para editar» sin cambios, comprobado en la misma sesión que el cerrojo de F-053.

R5. La ficha de un aprobado debe salir en solo lectura con un botón «Desaprobar para editar» (la desaprobación de
siempre, que vuelve a la ficha; F-053 R25 sigue impidiéndola con alta bloqueante).

### Edición de una fila (X1, X2, X7)
R6. CUANDO el PATCH `.../conciliacion/campos` trae cantidad Q, sv4 debe escribir `cantidad_convertida = Q` y
`cantidad_albaran` = (a) `Q / factor` si la fila era reproducible y `factor ≠ 0`; (b) `Q` si no tenía conversión
(`cantidad_convertida` nula y `factor` nulo o 1); (c) la que tenía, en otro caso (p. ej. contenedores).

R7. SI el PATCH no trae cantidad, ENTONCES sv4 debe conservar las dos cantidades y calcular el importe con Q.

R8. El front debe mandar en el PATCH solo los campos que el administrativo cambió (comparando números como
números, no textos); el backend trata un campo ausente como «no cambia» y uno presente a `null` como «vaciar».
SI nada cambia, ENTONCES no escribe importe, `importe_source`, descuento ni `review_required` (R13 aparte).

R9. La ficha debe pintar y mandar en filas Contrato el **precio aplicado** (`precio_unitario_final`), con el del
contrato en el `title`; guardar una fila sin tocar el precio no debe cambiar su precio ni su origen.

R10. Una fila Contrato editada (R6–R8) debe quedar con `cantidad_convertida` no nula: sv9 la admite (sin
`cantidad_sin_convertir`) y manda `cantidad = Q` con su `ctrpro_ide`.

R11. Lo que el administrativo cambia pisa lo valorado y ningún guardado lo devuelve a lo valorado. Las garantías de
F-019 R23–R24 y F-036 R1–R7 pasan a la fila (R6–R8); `_recalc_valuation_importes` y `_cantidades/_descuentos_del_
payload` se retiran y sus tests se reescriben sin perder casos.

R12. El importe que repinta la ficha al teclear debe ser el que guardará el backend (`precio × Q × (1 − dto/100)`),
también en filas no reproducibles (X7).

### Guardar = bloquear (X8)
R13. CUANDO el administrativo pulsa «Guardar» en una fila, sv4 debe aplicar lo cambiado (R6–R8) y marcarla
`bloqueada` en la misma transacción, también si no cambió nada; la fila pasa a solo lectura con «Desbloquear».

R14. SI una fila está bloqueada, ENTONCES editarla, reapuntarla, pasarla a almacén, cambiarle el producto,
dividirla o borrarla debe responder 409 «Línea guardada: desbloquéala para editarla»; «Almacén a todas» y «Borrar
todas» se saltan las bloqueadas y dicen cuántas.

R15. «Desbloquear» debe poner `bloqueada = false` con su entrada de «Deshacer»; bloquear también la tiene.

R16. Aprobar (ficha o listado) no debe exigir filas bloqueadas (respuesta 3 del humano).

R17. sv6 debe declarar `bloqueada BOOLEAN NOT NULL DEFAULT FALSE` en `albaran_line_valuations` (y sv4 la añade
defensivamente, como `codigo_externo`); revalorar la deja a `false` (lo arregla F-058).

### Guardados masivos y aprobar (X5, X6)
R18. «Guardar todas» debe guardar y bloquear solo las filas con cambios, mandando solo los campos cambiados; sin
ninguna, avisa «No hay cambios en las líneas».

R19. SI hay filas con cambios sin guardar y el administrativo pulsa «Guardar» o «Guardar y aprobar», ENTONCES sv4
debe avisar «Hay N líneas con cambios sin guardar» y no hacer nada.

R20. SI al aprobar (ficha o «Aprobar» del listado) alguna fila tiene cantidad o importe vacíos, ENTONCES sv4 no
debe aprobar y debe decir cuáles («Líneas sin cantidad o importe: 3, 5»).

R21. CUANDO la suma de importes de las filas difiere en 0,01 € o más de la suma de importes leídos de las
blancas, la ficha debe pedir confirmación antes de aprobar enseñando las dos cifras (no bloquea).

R22. CUANDO hay filas manuales y el administrativo pulsa «Valorar ahora», «Guardar y volver a buscar» o elige
otro contrato, sv4 debe pedir confirmación: «Revalorar descarta N líneas tocadas a mano».

### Traer líneas de contrato (X11, dato)
R23. «Traer líneas contrato» debe pedir la cantidad (obligatoria, ≠ 0) de cada línea elegida y crear filas
Contrato con la partida, precio y unidad de esa línea, `cantidad_convertida = cantidad_albaran = Q`, `factor` 1 e
importe calculado: válidas para sv9 sin más edición.

## Fase 2 · origen y partida (M2, M3, X9, X10, R6) — detalle en design §5.3

R24. La ficha debe llamar «Contrato» al origen que hoy dice «Sigrid» (solo textos; los datos no cambian).

R25. CUANDO cambian la partida (a una no vacía distinta de la de su línea de contrato), el precio unitario (también
al editar el importe, que reajusta el unitario) o la unidad de una fila Contrato, sv4 debe convertirla en Nueva
(derivada `manual_override` con los valores resultantes) **sin confirmación**; la insignia lo enseña.

R26. Vaciar la partida (almacén) o poner la de su línea de contrato no cambia el origen (F-051 D4 y R20; P10).
Editar descripción, cantidad, descuento o código externo no cambia el origen; ninguna edición llama a la IA.

R27. El combo de partida debe ofrecer «Almacén» primero y las partidas hoja de la obra (`/api/sigrid/partidas`,
una carga por ficha) con filtro predictivo por código y descripción; solo admite valores de la lista. Obra sin
partidas ⇒ solo «Almacén»; Sigrid no responde ⇒ solo «Almacén» y el aviso «No se pudieron cargar las partidas».
Elegir una solo manda `codigo_partida` (R25–R26) y cierra la lista; al teclear, vuelve arriba y «al» marca «Almacén».

R28. «Origen ✎» debe ser la única vía de reapuntar: elegir una línea de contrato deja la fila Contrato con la
partida y el precio de esa línea; elegir «Nueva», Nueva con los valores actuales. El combo de concepto pasa a texto
(sin reapuntar) y desaparece el aviso «pasará a NUEVA».

## Fase 3 · dividir (M1, X22; absorbe F-016) — detalle en design §5.4

R29. (v3, fase 3 bis) CUANDO el administrativo pulsa F7 en una fila (o su botón «Dividir»; F6 queda para el navegador),
la ficha debe abrir una ventana con el número de líneas (2–20) y la cantidad y la partida (combo de R27) de cada una; la
última se rellena sola (Q − las demás, en vivo, de solo lectura; en rojo si sale 0 o de otro signo) y «Aceptar» solo se
habilita si el reparto vale (R30). La columna «Acciones» no oculta nunca sus botones.

R30. `POST /api/documents/{id}/lines/{vid}/dividir {"partes": [{"cantidad", "codigo_partida"}]}`: 404 si la fila
no es del documento; 409 con alta bloqueante, aprobado (R4) o fila bloqueada (R14); 422 sin cambios si es
sintética, Q es nula o 0, alguna parte es nula, 0 o de signo distinto, o la suma difiere de Q en 0,005 o más.

R31. La original debe quedarse la parte 1 y cada parte k ≥ 2 nacer como fila `line_kind = 'reparto'`,
`merge_line_id` nulo, `parent_merge_line_id` de la original y sus campos copiados (design §5.4), con
`cantidad_convertida = qk` y `cantidad_albaran = ca0 × qk / Q`.

R32. El origen de cada parte sale de R25–R26: con la partida de la original (o vacía) conserva el origen y el
vínculo; con otra, Nueva con derivada propia.

R33. El importe de cada parte debe ser `round(importe0 × qk / Q, 2)` y la última absorber el redondeo (la familia
suma `importe0`); con `importe0` nulo, la fórmula canónica.

R34. Dividir debe ser UNA transacción con `total_valorado` recalculado y UNA entrada de «Deshacer» que borre las
partes y sus derivadas y restaure la original.

R35. La ficha debe pintar cada parte bajo su original («Parte k de N») y, MIENTRAS la familia no sume la cantidad
de su blanca, el aviso no bloqueante «Las partes de la línea N suman X; el albarán dice Y».

R36. sv9 debe mandar una parte Contrato como vinculada con su `ctrpro_ide`, cantidad y partida, y una Nueva sin
vincular con producto genérico; N partes al mismo `ctrpro` son N líneas (F-009 R12). Test de sv9, sin código.

R37. `docs/ARCHITECTURE.md` regla 20 y `azure-apps/albaranes.md` (`bloqueada`, `line_kind` `manual`/`reparto`)
deben actualizarse en la fase que introduce cada cambio.
