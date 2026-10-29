# F-106 · Lo editado a mano en la ficha cuadra, va así a Sigrid y sobrevive a revalorar — requisitos (v3)

Rigor **critico**. comun, sv4, sv9 (fase A) y sv6 (fase B, DDL); sv3 y sv5 no. D1–D13 cerradas (`design.md` §10).

Origen: AC26/30435 (CECOIS). El papel dice 10 × 11,20 −7 % = 104,16; la fila acabó en Q 48, P 11,2, I 104,16
`declared_albaran` y sv9 grabó 48 × 2,17 (`validador_alta.py:294`). Por qué, `design.md` §3.

## Definiciones

- **Fila**: fila de `albaran_line_valuations`. **Q** = `cantidad_convertida ?? cantidad_albaran`; **P** =
  `precio_unitario_final` (bruto); **d** = `descuento_albaran_aplicado`; **I** = `importe_calculado`.
- **Originales (grises)**: `albaran_lines_merge` (blancas) y `albaran_documents_merge`; la ficha los pinta en
  «Líneas leídas del albarán (IA)». **Importe del albarán** de una fila = `precio_neto` de su blanca.
- **Cuadra**: `|importe_de_linea(Q, P, d) − I| ≤ 0,02 €`; con Q, P o I nulos o ilegibles, **no comparable**.
- **A Sigrid**: cantidad (con signo) y precio que sv9 pondrá en la petición de la línea.
- **Edición**: `edicion_manual_json` de la fila: los campos que sv4 puso a mano con su valor, los valores de sv6
  antes de la primera edición (`calculado`) y, en las filas que crea sv4, `fila_entera`.
- **Pareja** de una fila editada en una valoración nueva: la fila nueva con su misma clave (R24).

# Fase A · editar, cuadrar y dar de alta lo que se ve

## Comun

R1. `importes.cuadra_linea(cantidad, precio, descuento, importe, tolerancia=TOLERANCIA_CUADRE_EUR)` devuelve
`True`/`False` según «cuadra» y `None` si no es comparable; nunca lanza. `TOLERANCIA_CUADRE_EUR = 0,02`, única
constante de cuadre de línea de sv4, sv6 y sv9.

R2. `alta_sigrid.linea_a_sigrid(*, vinculada, cantidad_albaran, cantidad_convertida, importe)` devuelve la cantidad
con el signo del importe y `round(|importe| / |cantidad|, 6)` (la convertida si vinculada, si no la del albarán), o
`None`; es la ÚNICA definición de «a Sigrid» (sv9 y sv4).

R3. `edicion_manual.recalcular_fila(*, cantidad, precio, descuento, importe, editados)` aplica la regla D1 (R5–R7)
y la usan sv4 (PATCH) y sv6 (reaplicar); todo precio despejado sale de `importes.unitario_despejado` (6 decimales).

## sv4 · PATCH `.../conciliacion/campos`

R4. El cuerpo admite `importe` (número, coma decimal, `NaN`/`±Inf` ⇒ 422) y `cuadrar` ∈ {`importe`, `precio`}; otro
valor de `cuadrar` ⇒ 422 sin escribir. `cuadrar` no es un campo de la fila.

R5. CUANDO cambian Q, P o d sin `importe`, sv4 guarda los resultantes e `I = importe_de_linea(Q, P, d)`,
`importe_source = 'calculated'`, sea cual sea el origen de la fila (lo de hoy, F-019 R23–R24, F-065 R11).

R6. CUANDO viene `importe` (solo o con Q o d), sv4 guarda I = el recibido a 2 decimales, `P = unitario_despejado(I, Q, d)`
con los Q y d resultantes, d sin cambios (o el recibido), `importe_source = 'calculated'`.

R7. SI vienen `importe` y `precio_unitario` a la vez ⇒ 422 «Cambia el precio o el importe, no los dos». SI con `importe` no se puede despejar (Q nula o 0, o d del 100 %): importe 0 ⇒ I = 0 y P se conserva; importe ≠ 0
⇒ 422 «No se puede calcular el precio con cantidad 0 o descuento del 100 %: cambia la cantidad, el descuento o el
precio», sin escribir.

R8. Un P despejado (R6, R9) es un precio cambiado: una Contrato pasa a Nueva (F-065 R25) y en una Nueva su derivada recibe P. Cambiar solo Q o d no cambia el origen.

R9. CUANDO el PATCH trae solo `cuadrar` sobre una fila que **no cuadra**: `importe` ⇒ como R5; `precio` ⇒ como R6
con el I actual (R7, R8). Sobre una que cuadra o no comparable, no escribe lo valorado (F-065 R8).

R10. Tras R5, R6 o R9 la fila cuadra (con R6, si `Q × (1 − d) ≤ 40 000`) y `total_valorado` se recalcula. El PATCH
escribe solo en `albaran_line_valuations` y en la derivada de su fila, nunca en los originales, y no publica en colas.

## sv4 · la ficha

R11. Al teclear Q, P o d, la ficha repinta el importe (`importeDeFila`, hoy); al teclear el importe, repinta P con 6
decimales (hoy 4) y conserva d; con Q 0, d 100 % o Q vacía e importe ≠ 0, no repinta y marca el importe en rojo con
el texto de R7.

R12. El PATCH lleva `importe` (y no `precio_unitario`) si, de precio, importe, cantidad y dto, el último tecleado fue
el importe; si no, P solo si cambió y nunca `importe`. Igual por las tres vías de `enviarFila` (F-077).

R13. Una fila con blanca (no sintética ni parte) cuyo I difiere de su importe del albarán (`importes.difieren`, 0,01 €)
enseña bajo el importe «≠ albarán: 104,16» (`title` «El importe ya no es el del albarán (104,16 €)»), informativo y
repintado al teclear. Las partes de un reparto conservan su aviso (F-065 R35).

R14. Una fila que no cuadra se pinta en rojo con `title` «48 × 11,20 × (1 − 7 %) = 499,97 ≠ 104,16» y los botones
«Recalcular importe» (`cuadrar = importe`) y «Recalcular precio» (`cuadrar = precio`), desactivados si la fila está
bloqueada o el albarán aprobado.

R15. Cada fila a registrar enseña «A Sigrid: 48 × 2,17 €» (R2) en el `title` del precio y, visible bajo él, cuando el
precio a Sigrid difiere de P en más de 0,000001; al teclear se repinta (factor `cantidad a Sigrid / Q` del servidor).
El precio se pinta con los decimales guardados, hasta 6, sin ceros finales y al menos 2.

## sv4 · aprobar · sv9 · altas grabadas

R16. SI alguna fila a registrar (importe ≠ 0) no cuadra, sv4 no aprueba (ficha ni listado): `LineasIncompletasError`
con posiciones y «Líneas que no cuadran (cantidad × precio × (1 − dto) ≠ importe): 3». Las no comparables no
cuentan; R13 no bloquea. Almacén = fila sin partida, sin excepción: cuadra o bloquea (humano, 2026-10-29).

R17. sv9 lee además P y d de la fila (`LineaAlta`, `SQL_LINEAS`). SI una línea a registrar no cuadra, sv9 deja el alta `no_admitido` con el motivo `linea_no_cuadra` (detalle «48 ×
11,2 × (1 − 7 %) = 499,97 ≠ 104,16», referencia), sin llamar a sigrid-api; sin él, la petición es la de hoy
(`_linea_peticion` con R2). `TEXTOS_MOTIVO_ALTA` (sv4) tiene su texto.

R18. `scripts/listar_altas_descuadradas_f106.py` (sv9) lista sin escribir las altas reales `registrado` con una línea
que no cuadra o con precio enviado ≠ `P × (1 − d)` (CSV UTF-8 BOM, `;`, coma decimal; `PG_*`; lo lanza el humano).

# Fase B · revalorar conserva lo editado a mano (D8 = c)

R19. sv6 añade `albaran_line_valuations.edicion_manual_json TEXT NULL` (`ADD COLUMN IF NOT EXISTS` en su
`schema_contribution.py`); al valorar solo la escribe al reaplicar (R23–R27).

R20. Toda vía de sv4 que escribe una fila actualiza su edición en la misma transacción: PATCH (campos cambiados, con
`importe` y el P despejado), «Origen ✎» (origen), almacén y «almacén a todas» (partida vacía), producto Sigrid,
«Guardar»/bloquear y desbloquear (`bloqueada`). La primera vez guarda en `calculado` la fila tal como la dejó sv6.

R21. Las filas que crea sv4 (Añadir línea, Traer líneas del contrato, «+ a Sigrid», partes de Dividir) nacen con
`fila_entera`; Dividir registra además la Q nueva de la original.

R22. `es_fila_manual` pasa a comun (`ruesma_comun.edicion_manual`); una fila con edición cuenta como tocada.

R23. CUANDO sv6 reemplaza la valoración de un documento (`replace_valuation`, cualquier vía: «Valorar ahora», cambiar
contrato, «Volver a buscar», «Guardar» que relanza la búsqueda, sv3 con `force`), debe leer en la misma transacción
las filas con edición de la anterior (y las legadas de R27) y reaplicarlas antes de confirmar.

R24. La clave de pareja es `merge_line_id` en las filas con blanca, y (`parent_merge_line_id`, `modifier_source`) en
las sintéticas cuando la valoración nueva tiene exactamente una; las `fila_entera` no tienen pareja.

R25. Con pareja, sv6 aplica a la fila nueva los campos de la edición con `recalcular_fila` (R3) y guarda en
`calculado` los valores que acaba de calcular; la edición se conserva.

R26. Sin pareja, la fila editada se conserva entera si su blanca (`merge_line_id` o `parent_merge_line_id`) existe o
si es una `fila_entera` sin blanca; si su blanca ya no existe, se pierde y la cabecera lleva el motivo
`ediciones_perdidas:N`. Una valoración nueva sin filas (`failed`, `no_contract`) conserva igual las editadas.

R27. Una fila legada (sin edición y `es_fila_manual`) cuenta como `fila_entera` (sin relleno en producción). Una
edición con origen Nueva recrea su derivada `manual_override` con su P; una editada vinculada a una línea que no es del
contrato de la valoración nueva pasa a Nueva con su P y el motivo `front_contrato_cambiado`.

R28. sv6 bloquea la cabecera (`SELECT … FOR UPDATE`) antes de leer las ediciones (un PATCH sobre una fila que ya no
existe ⇒ 409 «La valoración ha cambiado: recarga la ficha»); total y contadores salen de las filas finales.

R29. En la ficha, una fila con edición enseña «✋» con `title` campo a campo («Cantidad: 48 (calculado 10)»); una `fila_entera`, «✋ añadida a mano».

R30. «Volver a lo calculado» (POST `.../lines/{vid}/volver-a-calculado`) restaura `calculado`, borra la edición y
desbloquea, con deshacer; 409 en aprobado o con alta bloqueante; una `fila_entera` no lo tiene (✕). La confirmación
de revalorar (F-065 R22) dice «Revalorar conserva N líneas puestas a mano. ¿Continuar?». Fuera de alcance: el «✕» de
una fila con blanca vuelve al revalorar (como hoy).

# Regresión y documentación

R31. Los tests de F-019 R23–R26, F-036, F-065 y F-078 siguen en verde sin relajar aserciones, salvo los declarados:
`test_f065_f1_js.py` (`importe_solo_ajusta_el_precio` ⇒ `{"importe": 1000}`, R12), el texto de F-065 R22 (R30) y,
por enmiendas del humano del 2026-10-29: en `test_f065_f1_fila.py` `test_f065_r8_dominio_campos_presentes[cuerpo8-campos8]` y
`test_f065_r8_un_campo_desconocido_no_cuenta_como_cambio`, la clave desconocida pasa de `importe` a `importe_calculado`;
y el fixture (no la aserción) de `test_f075_r9_valoracion_directa_completa_se_aprueba` (P 2,5 en la fila 12) y de
`test_f078_r17_junto_a_las_de_f065_y_desde_guardar_y_aprobar` (P 12,5 en la 386), que no cuadraban (R16); y por R15
`test_f065_f1_fila.py::test_f065_r9_plantilla_precio_aplicado_y_el_del_contrato_en_el_title`: `value="120.0000"` ⇒ `"120.00"`.

R32. Casos por fixture, sin red ni BBDD real: (a) CECOIS por el PATCH: 10 × 11,20 −7 % = 104,16; `cantidad = 48` ⇒ I
499,97 `calculated`, «≠ albarán»; `importe = 104,16` ⇒ P 2,333333, Nueva, sv9 48 × 2,17; blanca intacta. (b) la
fila de producción (48, 11,20, 7, 104,16 `declared_albaran`) ⇒ rojo, no se aprueba, sv9 `linea_no_cuadra`. (c)
revalorar (SQLite de sv6) con esa edición, con contrato cambiado, sin blanca y con valoración `failed` (R23–R28).

R33. `docs/ARCHITECTURE.md` reglas 13, 20, 22 y 25 recogen R5–R10, R15, R16, R17 y R19–R30; `azure-apps/albaranes.md`
se actualiza si describe el PATCH de fila, los motivos de sv9 o las columnas de valoración (comprobarlo y anotarlo).
