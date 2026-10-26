# F-106 · Al cambiar la medición, el precio se recalcula y lo que se ve es lo que va a Sigrid — requisitos (v1)

Rigor **critico** (lo aprobado es lo que sv9 da de alta en Sigrid, F-053). Servicios: **comun**, **sv4-front** y
**sv9-alta-sigrid**. **sv6 no se toca** (F-100 está `in_progress` sobre sv6). Sin DDL. Decisiones abiertas D0–D7 en
`design.md` §8: cada R marcada con (Dn) asume la opción **recomendada** y cambia si el humano elige otra.

Origen: AC26/30435 (CECOIS A 26017815, obra 0692). La IA leyó 11,20 −7 % e importe 104,16 (10 ud); la fila
acabó con Q 48, precio 11,20, dto 7 e importe 104,16 `declared_albaran`; la ficha lo enseñó así (48 × 11,20 ×
0,93 = 499,97 ≠ 104,16) y sv9 mandó precio = 104,16 / 48 = 2,17 (`validador_alta.py:294`), que nadie vio.

## Definiciones

- **Fila**: fila de `albaran_line_valuations` (regla 22). **Q** = `cantidad_convertida ?? cantidad_albaran` (la de la
  ficha, en la unidad del precio). **P** = `precio_unitario_final` (unitario **bruto**, regla 13). **d** =
  `descuento_albaran_aplicado`. **I** = `importe_calculado`.
- **Importe del albarán**: fila con `importe_source = 'declared_albaran'` (el importe es el leído y nadie lo ha
  recalculado). Las demás (`calculated`, `none`) no lo tienen.
- **Cuadra**: `|importe_de_linea(Q, P, d) − I| ≤ TOLERANCIA_CUADRE_EUR` (D5: 0,02 €). Con Q, P o I nulos o
  ilegibles, **no comparable** (ni cuadra ni deja de cuadrar).
- **A Sigrid**: la cantidad (con signo) y el precio que sv9 pondrá en la petición de la línea.
- **Recalcular**: qué magnitud sigue a un cambio de Q o de d: `precio` (se conservan I y d) o `importe` (se
  conserva P).

## Comun (`ruesma_comun`)

R1. `importes.cuadra_linea(cantidad, precio, descuento, importe, tolerancia=TOLERANCIA_CUADRE_EUR)` debe devolver
`True`/`False` según la definición de «cuadra», y `None` si no es comparable; nunca lanza.

R2. `importes.TOLERANCIA_CUADRE_EUR` debe valer 0,02 y ser la única constante de cuadre de línea que usan sv4 y sv9.
(D5)

R3. `alta_sigrid.linea_a_sigrid(*, vinculada, cantidad_albaran, cantidad_convertida, importe)` debe devolver la
cantidad con el signo del importe y el precio `round(|importe| / |cantidad|, 6)` (cantidad = la convertida si
vinculada, si no la del albarán), o `None` si no hay cantidad no nula o importe. Es la ÚNICA definición de «a
Sigrid»: sv9 la usa para construir la petición y sv4 para enseñarla.

R4. El precio recalculado (R6, R7, R12) debe salir de `importes.unitario_despejado` (6 decimales), sin copia nueva.

## sv4 · editar una fila (PATCH `.../conciliacion/campos`)

R5. El cuerpo del PATCH debe admitir la clave opcional `recalcular` ∈ {`precio`, `importe`}; otro valor ⇒ 422 y
no se escribe nada.

R6. CUANDO cambia Q (y no P) en una fila **con importe del albarán** y `recalcular` es `precio` o no viene, sv4 debe
guardar `P = unitario_despejado(I, Q nueva, d)` y dejar I, `importe_source` y d como estaban. (D1)

R7. CUANDO cambia d (y no P) en una fila con importe del albarán y `recalcular` es `precio` o no viene, sv4 debe
guardar `P = unitario_despejado(I, Q, d nuevo)`, el d nuevo, y dejar I y `importe_source`. (D4)

R8. CUANDO cambia Q o d con `recalcular = importe`, o en una fila **sin** importe del albarán y sin `recalcular`,
sv4 debe conservar P y guardar `I = importe_de_linea(Q, P, d)` con `importe_source = 'calculated'` (lo de hoy,
F-065 R11, F-019 R23).

R9. CUANDO cambia P (tecleado, o al editar el importe, que reajusta P), sv4 debe recalcular I como hoy (F-065 R25
incluido: una fila Contrato pasa a Nueva). SI además viene `recalcular = precio`, ENTONCES 422.

R10. El P recalculado por R6/R7/R12 no debe cambiar el origen: una fila Contrato sigue Contrato con su
`matched_contrato_line_id`; en una Nueva, su derivada recibe el P nuevo (como hoy en la edición in situ).

R11. Una fila con P recalculado por R6/R7/R12 debe quedar con `precio_unitario_agreement = 'manual'` y
`precio_unitario_source = 'manual_despejado'` (cuenta como tocada a mano para revalorar, F-065 R22).

R12. CUANDO el PATCH trae solo `recalcular` (sin campos que cambien) sobre una fila que **no cuadra**, sv4 debe
cuadrarla con Q y d actuales: `precio` ⇒ R6; `importe` ⇒ R8. Sobre una fila que cuadra o no comparable, no debe
escribir lo valorado (F-065 R8; con «Guardar», solo bloquea).

R13. SI P no se puede despejar (Q nula o 0, d del 100 %, I nulo), ENTONCES con `recalcular` ausente sv4 debe aplicar
R8; con `recalcular = precio` explícito, 422 «No se puede recalcular el precio: …» sin escribir nada.

R14. Tras R6–R13 la fila editada debe cuadrar (o ser no comparable), y `total_valorado` se recalcula como hoy.

## sv4 · la ficha

R15. CUANDO el administrativo teclea Q o d en una fila con importe del albarán, la ficha debe repintar P con R6/R7
(6 decimales) y dejar el importe; en las demás, repintar el importe como hoy (`importeDeFila`, F-065 R12).

R16. CUANDO la ficha repinta P por R15, debe enseñar en la fila el aviso «Precio recalculado para mantener el importe
del albarán: 11,20 → 2,333333» con el control «Mantener el precio», que pasa la fila a `recalcular = importe` y
repinta (P de antes, importe nuevo); entonces el control dice «Mantener el importe» y deshace el paso. (D2)

R17. El P repintado por R15 no debe viajar como `precio_unitario` en el PATCH (no es un precio tecleado, R10); el
PATCH lleva `recalcular` con lo elegido. Las tres vías de guardar filas (`enviarFila`, F-077) lo hacen igual.

R18. La ficha debe pintar en rojo una fila que no cuadra, con `title` «48 × 11,20 × (1 − 7 %) = 499,97 ≠ 104,16», y
los botones «Ajustar precio» (`recalcular = precio`, R12) y «Ajustar importe» (`recalcular = importe`). Una fila
bloqueada o un aprobado los enseña desactivados (como el resto de la edición).

R19. Cada fila a registrar debe enseñar «A Sigrid: 48 × 2,17 €» con los valores de R3: en el `title` del precio
siempre, y visible bajo el precio cuando el precio a Sigrid difiere de P en más de 0,000001 (descuento, conversión
o fila que no cuadra). Al teclear se repinta con el mismo cálculo (en JS, con el factor `cantidad a Sigrid / Q` que
pinta el servidor).

R20. El precio de la fila debe pintarse con los decimales guardados, hasta 6, sin ceros finales y al menos 2. (D5)

## sv4 · aprobar

R21. SI alguna fila a registrar (importe ≠ 0) **no cuadra**, ENTONCES sv4 no debe aprobar, ni desde la ficha ni
desde el listado: `LineasIncompletasError` con sus posiciones y el texto «Líneas que no cuadran (cantidad × precio ×
(1 − dto) ≠ importe): 3». Las no comparables no cuentan. (D2)

## sv9 · alta

R22. sv9 debe leer de la fila `precio_unitario_final` y `descuento_albaran_aplicado` (`LineaAlta`, SQL de
`sql_alta_repository.py`).

R23. SI una línea a registrar no cuadra (R1 con su Q, P, d e I), ENTONCES sv9 debe dejar el alta `no_admitido` con
el motivo `linea_no_cuadra` (detalle «48 × 11,2 × (1 − 7 %) = 499,97 ≠ 104,16», referencia de la línea), sin llamar
a sigrid-api. (D7)

R24. Sin ese motivo, la petición debe ser idéntica a la de hoy: `_linea_peticion` toma cantidad y precio de R3.

R25. `TEXTOS_MOTIVO_ALTA` (sv4) debe tener el texto legible de `linea_no_cuadra`; el test que contrasta los textos
con las fuentes de sv9 lo exige.

## Altas ya grabadas (solo lectura)

R26. `services/albaranes-alta-sigrid/scripts/listar_altas_descuadradas_f106.py` debe listar, sin escribir nada, las
altas `registrado` en modo real con alguna línea que no cuadra o cuyo precio enviado (`peticion_json`) difiere de
`P × (1 − d)` más que la tolerancia: documento, `sigrid_cod`, referencia de línea, Q, P, d, I y precio enviado, en
CSV (UTF-8 BOM, `;`, coma decimal). Sin red: la conexión llega por variables `PG_*`. (D6)

## Regresión y documentación

R27. Lo que no es cambio de Q, d o P, y las filas sin importe del albarán, deben comportarse como hoy: los tests de
F-019 R23–R26, F-036 y F-065 siguen en verde. Los que fijan «cambiar Q o d en una fila `declared_albaran` recalcula
el importe» (F-019 R24, F-065 R11) se conservan mandando `recalcular = importe`; ninguna aserción se relaja.

R28. Caso CECOIS por fixture (sin red ni BBDD real): (a) fila 10 ud, 11,20, 7 %, 104,16 `declared_albaran` y PATCH
`cantidad = 48` ⇒ P 2,333333, I 104,16, d 7, cuadra, sigue Contrato, y la petición de sv9 lleva 48 × 2,17; (b) fila
ya incoherente (48, 11,20, 7, 104,16) ⇒ ficha en rojo con «A Sigrid: 48 × 2,17 €», aprobar rechazado y sv9
`no_admitido` `linea_no_cuadra`.

R29. `docs/ARCHITECTURE.md` reglas 13 y 20 deben recoger R6–R13, R19, R21 y R23; `azure-apps/albaranes.md` se
actualiza solo si describe el cuerpo del PATCH de fila o los motivos de sv9 (comprobarlo y anotarlo).
