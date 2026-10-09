# F-065 · Las líneas editadas en sv4 se respetan, la partida no rompe el vínculo y una línea se reparte — requisitos

Rigor **critico** (lo que se aprueba es lo que sv9 da de alta en Sigrid, F-053). Servicio: **sv4-front** (con el
modelo M1 de P4; M2 añadiría sv6 y sv3). sv9 y comun **no cambian**: solo tests de contrato en sv9. Prioridad 1.
Diagnóstico con fichero:línea: `progress/explore_F-065.md`. Decisiones abiertas P1–P9: `design.md` §7 y
`progress/spec_F-065.md`. Los requisitos están escritos con la **opción recomendada** de cada P; si el humano
elige otra, se reescriben los que la citan.

## Origen (correo de administración de obra, 2026-10-09; METALFIRE, contrato CTSU25/0359)

«Las unidades del albarán tengo que repartirlas en 3 partidas distintas.» · «Si le cambio las partidas me arrastra
del contrato, si le doy que no me la cambie me la pone como nueva.» · Puso 6 y 7 en las dos líneas de puerta (el
albarán dice 8 y 10) y trajo del contrato una tercera con 5: «Guardar todas» dejó 6+7+5 = 18; «Guardar y aprobar»
devolvió las dos primeras a 8 y 10 ⇒ **23 unidades servidas en vez de 18**.

## Definiciones

- **Fila salmón**: una fila de `albaran_line_valuations` (lo que se aprueba y va a Sigrid). **Blanca**: la línea
  de `albaran_lines_merge` (lo leído). **Q** de una fila salmón = `cantidad_convertida ?? cantidad_albaran`: la
  que la ficha enseña y edita, en la **unidad del precio** (`importe = precio × Q × (1 − dto/100)`).
- **Reproducible**: `conversion_reproducible(factor, cantidad_albaran, cantidad_convertida)` de sv4 (F-036 R1).
- **Fila SIGRID**: con `matched_contrato_line_id` y sin derivada. **NUEVA**: con `derived_contrato_line_id`.
- **Parte** de un reparto: fila salmón con `line_kind = 'reparto'` (R23). **Familia**: la fila original de un
  reparto más sus partes (mismo `merge_line_id` / `parent_merge_line_id`).

## A · Las ediciones se respetan (fase 1, urgente: bloquea desplegar F-053)

R1. CUANDO llega un PUT `/api/documents/{id}`, sv4 debe recalcular la valoración de una blanca SOLO si su
`cantidad` o su `descuento` (saneado: `0` = `NULL`) **difieren de los guardados en el merge antes del PUT**; una
blanca reenviada tal cual no toca ninguna fila salmón (ni cantidades, ni importe, ni `importe_source`, ni motivos).

R2. CUANDO el revisor deja 6 y 7 en dos filas SIGRID de 8 y 10, trae una línea de contrato con 5, guarda con el
PATCH de filas y después hace PUT con `approved = true`, las filas deben quedar en 6, 7 y 5 y `total_valorado` en
la suma de sus importes (caso METALFIRE, con los datos del correo).

R3. R1 vale para todo PUT del portal (Guardar, Guardar y aprobar, autoguardado de obra/proveedor, elegir contrato,
paso 1 de «Valorar ahora», «Guardar y volver a buscar»): todos pasan por `update_document_y_transicion`.

R4. CUANDO una blanca SÍ cambió (R1), sv4 debe aplicar a su fila salmón el recálculo de siempre (F-019 R23–R24,
F-036 R1–R7), sin cambios.

R5. CUANDO el PATCH `.../conciliacion/campos` trae cantidad Q, sv4 debe escribir `cantidad_convertida = Q` y
`cantidad_albaran` = (a) `Q / factor` si la fila era reproducible y `factor ≠ 0`; (b) `Q` si la fila no tenía
conversión (`cantidad_convertida` nula y `factor` nulo o 1); (c) la que tenía, en otro caso (conversión no
reproducible, p. ej. contenedores de residuos).

R6. SI el PATCH no trae cantidad, ENTONCES sv4 debe conservar `cantidad_albaran` y `cantidad_convertida` y
calcular el importe con Q (hoy copia Q en `cantidad_albaran` y anula la convertida).

R7. CUANDO el PATCH no cambia ningún valor de la fila (cantidad, descuento, partida, unidad, precio, descripción,
código externo), sv4 no debe tocar importe, `importe_source`, descuento ni `review_required`; solo debe completar
`cantidad_convertida` si está vacía (R5).

R8. CUANDO un PUT recalcula filas salmón (R4), su entrada de «Deshacer» debe guardar el estado previo de esas
filas, y deshacerla debe devolverlas a sus valores anteriores (hoy solo guarda cabecera y valoración).

R9. Una fila SIGRID editada en sv4 (R5–R7) debe quedar con `cantidad_convertida` no nula, de modo que el
validador de sv9 la admita (sin `cantidad_sin_convertir`) y mande `cantidad = Q` con su `ctrpro_ide`.

R10. F-019 R23–R24 y F-036 R1–R7 siguen vigentes con «lo que el revisor acaba de editar» = la blanca que cambió
(R1) o la fila salmón (R5–R7). Sus tests se reescriben con esa lectura, sin perder ningún caso que fijaban.

R11. CUANDO el revisor pulsa «Guardar todas», sv4 debe mandar el PATCH solo de las filas con algún campo
modificado; sin ninguna, avisa «No hay cambios en las líneas» y no manda nada.

R12. SI hay filas salmón con cambios sin guardar y el revisor pulsa «Guardar» o «Guardar y aprobar», ENTONCES sv4
debe avisar «Hay N líneas con cambios sin guardar: pulsa «Guardar todas» o recarga para descartarlos» y no
hacer el PUT.

## B · Cambiar la partida sin perder el vínculo (fase 2; depende de P1)

R13. CUANDO el revisor cambia la partida de una fila SIGRID por otra no vacía, sv4 debe escribir solo
`codigo_partida_final` y `partida_action = 'partida_elegida'`, conservando línea de contrato, precio, unidad y
cantidades: la fila sigue SIGRID (en sv9, vinculada con `partida`; sigrid-api avisa `partida_distinta_del_contrato`).

R14. CUANDO cambian la unidad o el precio de una fila SIGRID, sv4 debe seguir convirtiéndola en NUEVA (regla de
junio de 2026), y el aviso debe decir «Has cambiado la unidad o el precio…» (ya no «imputación»).

R15. El combo de partida debe ofrecer «Almacén (sin partida)» primero y después las **partidas** distintas de las
líneas del contrato del documento (código, sin repetir), además de admitir texto libre; elegir una debe guardar
solo `codigo_partida` por el PATCH de campos (R13) y recargar. **Nunca** debe reapuntar la línea de contrato.

R16. Reapuntar a otra línea de contrato debe seguir siendo posible por el combo de concepto y por «✎ Origen», con
la ayuda «Cambia el producto y el precio; la partida no cambia».

R17. CUANDO «Guardar todas» va a convertir alguna fila SIGRID en NUEVA (R14), sv4 debe pedir UNA confirmación con
el número de esas filas; si se cancela, no debe mandar ningún PATCH.

## C · Repartir una línea entre varias partidas (fase 3; absorbe F-016)

R18. sv4 debe ofrecer `POST /api/documents/{id}/lines/{vid}/dividir` con `{"partes": [{"cantidad",
"codigo_partida"}]}` de 2 a 20 partes; `codigo_partida` vacío o nulo = almacén.

R19. SI la fila es de otro documento o no existe, ENTONCES 404; SI el alta en Sigrid es bloqueante (F-053 R26),
ENTONCES 409 con el aviso de siempre y sin cambios.

R20. SI la fila es `synthetic_modifier`, Q es nula o 0, alguna parte tiene cantidad nula, 0 o de signo distinto
a Q, o hay menos de 2 o más de 20 partes, ENTONCES 422 con el motivo y sin cambios.

R21. SI la suma de las partes difiere de Q en 0,005 o más, ENTONCES 422 «Las partes suman X; la línea tiene Y» y
sin cambios (P5).

R22. CUANDO el reparto es válido, la fila original debe quedarse con la parte 1: `cantidad_convertida = q1`,
`cantidad_albaran = ca0 × q1 / Q` (ca0 nula ⇒ q1), su partida y su importe.

R23. Por cada parte k ≥ 2, sv4 debe crear una fila con `merge_line_id` nulo, `line_kind = 'reparto'`,
`parent_merge_line_id` = el `merge_line_id` de la original (o su `parent_merge_line_id` si no tiene), y copiar de
ella precio y su origen, unidades, `factor_conversion`, descuento, `producto_sigrid`, `codigo_externo`, motivo de
casado y la descripción (`descripcion_linea`, o el concepto de su blanca si no la tiene); con
`cantidad_convertida = qk` y `cantidad_albaran = ca0 × qk / Q`.

R24. Una parte de una fila SIGRID debe casar con la MISMA línea de contrato; una de una fila NUEVA debe llevar su
propia copia de la derivada (`origen = 'manual_override'`) con su partida.

R25. La partida de cada parte: vacía ⇒ `codigo_partida_final` NULL y `partida_action = 'almacen_elegido'`; si no,
la tecleada y `'partida_elegida'`. El vínculo se conserva (R13).

R26. El importe de cada parte debe ser `round(importe0 × qk / Q, 2)` y la última debe absorber el redondeo, de
modo que la familia sume `importe0`; con `importe0` nulo, la fórmula canónica con `precio` y `qk` (P6).

R27. El reparto debe ser UNA transacción con `total_valorado` recalculado (`ROUND(…, 2)`) y UNA entrada de
«Deshacer» que borre las partes y sus derivadas creadas y restaure la original y la cabecera.

R28. La ficha debe pintar cada parte justo debajo de su original con «Parte k de N», editable y borrable como
cualquier fila salmón; y un botón «Dividir» en cada fila salmón no sintética que abra un diálogo de N filas
(cantidad y partida) con lo que falta por repartir y «Aceptar» deshabilitado mientras la suma no sea Q.

R29. MIENTRAS la suma de `cantidad_albaran` de una familia difiera de la cantidad de su blanca, la ficha debe
mostrar el aviso no bloqueante «Las partes de la línea N suman X; el albarán dice Y» (no impide aprobar).

R30. Una parte SIGRID debe salir de sv9 como vinculada con su `ctrpro_ide`, `cantidad = qk` y su partida; N
partes al mismo `ctrpro` deben ser N líneas de la petición, sin sumarse (F-009 R12). Test de sv9, sin código nuevo.

R31. CUANDO el revisor pulsa «Valorar ahora» o «Guardar y volver a buscar» y la valoración tiene filas
`reparto` o `manual`, sv4 debe pedir confirmación: «Revalorar descarta N líneas añadidas o repartidas a mano»
(hasta F-058).

## Documentación

R32. `docs/ARCHITECTURE.md` debe llevar la regla 20 (Q en la unidad del precio, R1, R5, R13, el reparto y su
modelo) y `azure-apps/albaranes.md` los valores nuevos de `line_kind` (`manual`, `reparto`) y `partida_action`
(`partida_elegida`), en el mismo trabajo.
