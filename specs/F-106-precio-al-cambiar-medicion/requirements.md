# F-106 · Al editar una fila, se mueve lo que toca y lo que se ve es lo que va a Sigrid — requisitos (v2)

Rigor **critico** (lo aprobado es lo que sv9 da de alta en Sigrid, F-053). Servicios: **comun**, **sv4-front** y
**sv9-alta-sigrid**. **sv6 y sv3 no se tocan.** Sin DDL. PARADA 1 contestada por el humano el 2026-10-26: las
decisiones cerradas y la nueva (D8) están en `design.md` §9.

Origen: AC26/30435 (CECOIS A 26017815, obra 0692). El albarán dice 10 × 11,20 −7 % = 104,16. Óscar cambió la cantidad
a 48 y «cambió el unitario y no el importe total»: Sigrid grabó 48 × 2,17 = 104,16 (sv9 despeja precio = importe /
cantidad, `validador_alta.py:294`). Por qué pasó, en `design.md` §3.

## Definiciones

- **Fila**: fila de `albaran_line_valuations` (regla 22). **Q** = `cantidad_convertida ?? cantidad_albaran` (la de la
  ficha). **P** = `precio_unitario_final` (bruto, regla 13). **d** = `descuento_albaran_aplicado`. **I** =
  `importe_calculado`.
- **Originales (grises)**: lo leído del albarán, `albaran_lines_merge` (cantidad, precio, `precio_neto`, descuento) y
  la cabecera `albaran_documents_merge`; la ficha los pinta en «Líneas leídas del albarán (IA) · solo lectura».
  **Importe del albarán** de una fila = `precio_neto` de su blanca.
- **Cuadra**: `|importe_de_linea(Q, P, d) − I| ≤ TOLERANCIA_CUADRE_EUR` (0,02 €). Con Q, P o I nulos o ilegibles,
  **no comparable**.
- **A Sigrid**: la cantidad (con signo) y el precio que sv9 pondrá en la petición de la línea.
- **Fila tocada a mano**: `es_fila_manual` (F-065 R22, `review_models.py:736`).

## Comun (`ruesma_comun`)

R1. `importes.cuadra_linea(cantidad, precio, descuento, importe, tolerancia=TOLERANCIA_CUADRE_EUR)` debe devolver
`True`/`False` según «cuadra» y `None` si no es comparable; nunca lanza.

R2. `importes.TOLERANCIA_CUADRE_EUR` debe valer 0,02 y ser la única constante de cuadre de línea de sv4 y sv9.

R3. `alta_sigrid.linea_a_sigrid(*, vinculada, cantidad_albaran, cantidad_convertida, importe)` debe devolver la
cantidad con el signo del importe y `round(|importe| / |cantidad|, 6)` (cantidad = la convertida si vinculada, si no
la del albarán), o `None` sin cantidad no nula o sin importe. Es la ÚNICA definición de «a Sigrid» (sv9 y sv4).

R4. Todo precio despejado (R7, R12) debe salir de `importes.unitario_despejado` (6 decimales), sin copia nueva.

## sv4 · editar una fila (PATCH `.../conciliacion/campos`)

R5. El cuerpo debe admitir `importe` (número, coma decimal, `NaN`/`±Inf` ⇒ 422, como los demás) y `cuadrar` ∈
{`importe`, `precio`}; otro valor de `cuadrar` ⇒ 422 sin escribir nada. `cuadrar` no es un campo de la fila.

R6. CUANDO cambian Q, P o d y no viene `importe`, sv4 debe guardar los Q, P y d resultantes e `I =
importe_de_linea(Q, P, d)` con `importe_source = 'calculated'`, en toda fila sea cual sea su origen (lo de hoy:
F-019 R23–R24, F-065 R11).

R7. CUANDO viene `importe` (solo o con Q o d), sv4 debe guardar `I` = el importe recibido redondeado a 2, `P =
unitario_despejado(I, Q resultante, d resultante)`, d sin cambios (o el recibido) e `importe_source = 'calculated'`.

R8. SI vienen `importe` y `precio_unitario` a la vez, ENTONCES 422 «Cambia el precio o el importe, no los dos» sin
escribir nada.

R9. SI con `importe` el precio no se puede despejar (Q nula o 0, o d del 100 %), ENTONCES: con importe 0, sv4 debe
guardar I = 0 y conservar P; con importe ≠ 0, 422 «No se puede calcular el precio con cantidad 0 o descuento del
100 %: cambia la cantidad, el descuento o el precio» sin escribir nada.

R10. Un P despejado por R7 o R12 debe tratarse como un precio cambiado: una fila Contrato pasa a Nueva (F-065 R25,
derivada `manual_override`) y en una Nueva su derivada recibe P, con las marcas manuales de hoy.

R11. Cambiar solo Q o d no debe cambiar el origen de la fila (F-065 R25, sin cambios).

R12. CUANDO el PATCH trae solo `cuadrar` sobre una fila que **no cuadra**, sv4 debe cuadrarla con Q y d actuales:
`importe` ⇒ como R6 (conserva P); `precio` ⇒ como R7 con el I actual (R9 y R10 incluidos). Sobre una fila que cuadra
o no comparable no debe escribir lo valorado (F-065 R8).

R13. Tras R6, R7 o R12 la fila editada debe cuadrar (con R7, para `Q × (1 − d) ≤ 40 000`, design §10 R-6), y
`total_valorado` se recalcula como hoy.

R14. El PATCH debe escribir solo en `albaran_line_valuations` y en la derivada de su fila; nunca en
`albaran_lines_merge` ni en `albaran_documents_merge` (los originales quedan idénticos).

R15. El PATCH no debe publicar en ninguna cola (`q-valoracion`, `q-persistencia`).

## sv4 · que la edición no la pise una revaloración (D8)

R16. CUANDO «Guardar» o el autoguardado de la cabecera haría relanzar la búsqueda de contratos (F-052 D4-A) y el
documento tiene filas tocadas a mano, sv4 no debe relanzarla y el mensaje debe decir «Guardado. No se ha vuelto a
buscar contratos porque hay N líneas tocadas a mano; «Volver a buscar» las descarta». Sin filas tocadas, como hoy.

R17. «Valorar ahora», cambiar de contrato y «Volver a buscar» deben seguir pidiendo la confirmación de F-065 R22;
conservar lo editado al revalorar es F-058, fuera de esta ficha.

## sv4 · la ficha

R18. CUANDO el administrativo teclea Q, P o d, la ficha debe repintar el importe con `importeDeFila` (hoy); CUANDO
teclea el importe, debe repintar P con 6 decimales (hoy 4) y conservar d. Con Q 0, d 100 % o Q vacía e importe ≠ 0,
no repinta P y marca el importe en rojo con el texto de R9.

R19. El PATCH debe llevar `importe` (y no `precio_unitario`) si de precio, importe, cantidad y dto el último tecleado
fue el importe; si no, P solo si cambió y nunca `importe`. Las tres vías de `enviarFila` (F-077) igual.

R20. Una fila con blanca (no sintética ni parte de reparto) cuyo I difiere de su importe del albarán
(`importes.difieren`, 0,01 €) debe enseñar bajo el importe «≠ albarán: 104,16» con `title` «El importe ya no es el
del albarán (104,16 €)», informativo, sin bloquear; al teclear se repinta. Las partes de un reparto conservan su
aviso (F-065 R35).

R21. Una fila que no cuadra debe pintarse en rojo con `title` «48 × 11,20 × (1 − 7 %) = 499,97 ≠ 104,16» y los
botones «Recalcular importe» (`cuadrar = importe`) y «Recalcular precio» (`cuadrar = precio`); desactivados si la
fila está bloqueada o el albarán aprobado.

R22. Cada fila a registrar debe enseñar «A Sigrid: 48 × 2,17 €» con R3: en el `title` del precio siempre y visible
bajo el precio cuando el precio a Sigrid difiere de P en más de 0,000001; al teclear se repinta (factor `cantidad a
Sigrid / Q` que pinta el servidor).

R23. El precio debe pintarse con los decimales guardados, hasta 6, sin ceros finales y al menos 2.

## sv4 · aprobar

R24. SI alguna fila a registrar (importe ≠ 0) no cuadra, ENTONCES sv4 no debe aprobar, ni desde la ficha ni desde el
listado: `LineasIncompletasError` con sus posiciones y «Líneas que no cuadran (cantidad × precio × (1 − dto) ≠
importe): 3». Las no comparables no cuentan; el aviso de R20 no bloquea.

## sv9 · alta

R25. sv9 debe leer de la fila `precio_unitario_final` y `descuento_albaran_aplicado` (`LineaAlta`, SQL de
`sql_alta_repository.py`).

R26. SI una línea a registrar no cuadra (R1 con su Q, P, d e I), ENTONCES sv9 debe dejar el alta `no_admitido` con
el motivo `linea_no_cuadra` (detalle «48 × 11,2 × (1 − 7 %) = 499,97 ≠ 104,16», referencia de la línea), sin llamar
a sigrid-api.

R27. Sin ese motivo, la petición debe ser idéntica a la de hoy: `_linea_peticion` toma cantidad y precio de R3.

R28. `TEXTOS_MOTIVO_ALTA` (sv4) debe tener el texto de `linea_no_cuadra`; el test que lo contrasta con sv9 lo exige.

## Altas ya grabadas (solo lectura)

R29. `services/albaranes-alta-sigrid/scripts/listar_altas_descuadradas_f106.py` debe listar, sin escribir nada, las
altas `registrado` en modo real con alguna línea que no cuadra o cuyo precio enviado (`peticion_json`) difiere de `P
× (1 − d)` más que la tolerancia: documento, `sigrid_cod`, referencia, Q, P, d, I y precio enviado, en CSV (UTF-8
BOM, `;`, coma decimal). Conexión por variables `PG_*`; lo lanza el humano.

## Regresión y documentación

R30. Los tests de F-019 R23–R26, F-036 y F-065 deben seguir en verde sin relajar aserciones. Única excepción
declarada: `test_f065_f1_js.py` («`importe_solo_ajusta_el_precio` = {}», F-065 R9) pasa a esperar `{"importe":
1000}` por R19.

R31. Caso CECOIS por fixture (sin red ni BBDD real): (a) fila 10 × 11,20 −7 % = 104,16 Contrato; PATCH `cantidad =
48` ⇒ I 499,97, P 11,20, sigue Contrato, aviso «≠ albarán: 104,16», sv9 manda 48 × 10,416; luego PATCH `importe =
104,16` ⇒ P 2,333333, Nueva, sin aviso, sv9 manda 48 × 2,17; la blanca, intacta. (b) fila ya incoherente (48, 11,20,
7, 104,16, `declared_albaran`, la de producción, design §3) ⇒ rojo, aprobar rechazado, sv9 `no_admitido`
`linea_no_cuadra`; un PATCH de partida o «Origen ✎ → Nueva» la deja sin cuadrar; «Recalcular precio» ⇒ P 2,333333.

R32. `docs/ARCHITECTURE.md` reglas 13, 20 y 25 deben recoger R6–R16, R22, R24 y R26; `azure-apps/albaranes.md` se
actualiza solo si describe el cuerpo del PATCH de fila o los motivos de sv9 (comprobarlo y anotarlo).
