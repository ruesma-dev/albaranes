# F-075 · El importe del albarán manda: pie leído como control y paso directo sin contrato — requisitos (v2)

Rigor **critico** (lo aprobado lo da de alta sv9 en el ERP; cambia lo que lee IA1 en producción y lo que va a
revisión). Servicios: **comun**, **sv2-api**, **sv3-persistencia**, **sv5-valoracion-api** (solo el sobre
`no_contract`, R5 bis), **sv6-valoracion-persist**, **sv4-front**; sv9 sin código (tests de contrato).

> **Ajuste por decisión del humano (2026-10-18)**, a raíz del bloqueo del implementer (`progress/impl_F-075.md` §2):
> opción **A** (sv5 añade `precio_neto_albaran` y `descuento_albaran` al sobre `no_contract`, R5 bis) y matiz **M1**
> (R3: solo sin contrato seleccionado; con contrato seleccionado y 0 líneas, SKIP como hoy). Prioridad 1. Informe, respuestas de la PARADA 1 y preguntas v2:
`progress/spec_F-075.md` §v2. Corte propuesto en dos features: design §1. La v1 (solo sv4, importe junto al
valorado) queda **sustituida**.

## Origen y decisiones del humano (2026-10-15, literales)

DISCOIN, obra 0686 (merges `dfdc8aab-…` y `5dea6509-…`): el albarán trae precios, no hay contrato ⇒ «Importe
valorado —» y no se puede aprobar (F-053 R37). Respuestas a la PARADA 1 de la v1:
- P1: «como ya hay importe, no hay que valorar con contrato, manda el albarán y pisa».
- P2: «que lea el pie y sirva para revisar».
- P3: aceptada (líneas sin importe no suman; total marcado parcial).
- Sin contrato: «si trae importes no hace valorar ni contrato, pasa directo».

## Hechos del código que acotan la v2 (detalle: informe §v2.1)

- **Con contrato, lo leído YA manda línea a línea** (jul 2026, F-019): en sv6 el unitario y el importe declarados
  ganan al precio del contrato (`PriceReconciler`, `ImporteCalculator`: «el DECLARADO MANDA SIEMPRE»); el contrato
  aporta vínculo, partida y conversión, y su precio solo es respaldo cuando falta lo leído.
- Lo que la valoración con contrato añade y el papel no trae: **sintéticas** (M1–M7) y el precio del contrato en
  líneas sin importe.
- Sin contrato, sv3 no publica `q-valoracion` («SKIP: no hay contrato seleccionado con líneas»). Si publicara, sv5
  devuelve el sobre `no_contract` con las líneas del albarán en `context` y sv6 guarda una cabecera vacía.
- sv9 ya admite una valoración `no_contract` completa («valorado», `esta_valorado`): manda sus líneas sin vincular,
  producto por el mapeo de familia, sin `cod_contrato`, `precio = |importe|/|cantidad|`. sigrid-api no recalcula
  importes desde el contrato (F-009, H14).
- IA1 no lee el pie (ni base, ni IVA, ni total). IA2 devuelve el documento completo y su cabecera sustituye a la de
  fase 1.

## Definiciones

- **Importe leído de una línea**: su `precio_neto` del merge (importe tras descuento, sin IVA; ARCHITECTURE §13).
  No se completa con nada (P3).
- **Importe del albarán**: suma con signo de los importes leídos; nulo si ninguna línea lo trae; **parcial** si
  faltan algunos.
- **Trae importes**: al menos una línea del merge con importe leído no nulo.
- **Pie**: `base_imponible`, `tipo_iva_pct`, `cuota_iva`, `total_albaran` impresos al pie (euros salvo el tipo).
- **Valoración directa**: la que sv6 construye desde las líneas del albarán, sin contrato ni IA.

## 1 · Una sola definición (comun)

R1. `ruesma_comun.importes` debe ofrecer `importe_albaran(importes)` (total, líneas, con importe, parcial; P3), y
sv3, sv4 y sv6 deben usarla: nadie repite la regla.
R2. `ruesma_comun.importes` debe ofrecer `pie_cuadra(suma, pie, tolerancia)`: compara la suma con la base y, sin
base, con `total − cuota`; devuelve `cuadra`, `no_cuadra` o `no_comparable` (solo total, o nada).

## 2 · Paso directo sin contrato (sv3 + sv6)

R3. CUANDO sv3 termina de persistir un merge **sin contrato seleccionado** (código nulo) y el albarán trae importes,
sv3 debe publicar `q-valoracion` con `codigo_contrato` nulo (hoy lo omite). (M1, humano 2026-10-18.)
R4. SI el albarán no trae importes y no tiene contrato, ENTONCES sv3 no publica, como hoy. SI tiene contrato
seleccionado sin líneas, ENTONCES sv3 no publica, como hoy (M1: sv5 tomaría ese contrato del merge y no daría
`no_contract`).
R5 bis. El sobre `no_contract` de sv5 debe llevar, por línea, `precio_neto_albaran` (el `precio_neto` del merge, sin
derivar) y `descuento_albaran`, como ya los lleva el sobre con contrato. (Opción A, humano 2026-10-18.)
R5. CUANDO sv6 recibe un sobre `no_contract` y alguna línea de `context.lineas_albaran` trae importe leído, sv6 debe
persistir una valoración directa: cabecera `no_contract`, `contrato_codigo` nulo, `total_valorado` = suma de los
importes no nulos, y una línea `from_albaran` por cada línea del albarán.
R6. Cada línea directa debe llevar: `importe_calculado` = `precio_neto` leído (`importe_source = declared_albaran`)
o nulo; `cantidad_albaran` = `cantidad_convertida` = cantidad leída, factor 1, unidad del albarán; precio unitario
= el leído o, si falta, el despejado del importe (`ruesma_comun.importes`); partida final = la impresa o vacía
(almacén); descripción del albarán; una derivada `nueva_no_match` con `codigo_contrato` vacío (F-065: sin línea de
contrato ni derivada no se aprueba); y `review_required` con motivo `sin_importe_en_albaran` si su importe es nulo.
R7. La valoración directa no debe llamar a ninguna IA ni crear sintéticas.
R8. SI el sobre es `no_contract` y ninguna línea trae importe, ENTONCES sv6 persiste la cabecera vacía de hoy.
R9. Una valoración directa con todas las líneas con importe es «valorada» (`esta_valorado`, sin cambios): se aprueba
en sv4 y sv9 la da de alta sin código nuevo. Con alguna línea sin importe no se aprueba hasta que el administrativo
la complete (F-053 R37, F-065).
R10. Revalorar desde sv4 un documento sin contrato que trae importes debe rehacer la valoración directa (la
confirmación de F-065 avisa si se pierden filas tocadas a mano).

## 3 · Con contrato (P1; interpretación a validar, v2-P1)

R11. MIENTRAS haya contrato seleccionado con líneas, sv3 y sv6 deben valorar como hoy (vínculo, partida, conversión;
lo leído manda línea a línea; el precio del contrato solo cuando falta lo leído). F-075 no cambia ese cálculo.
R12. CUANDO un documento con contrato trae importes y su `total_valorado` difiere del importe del albarán en ≥ 0,01 €
(sintéticas o líneas sin importe), sv6 debe dejar la valoración a revisión con el motivo
`valorado_distinto_de_albaran:<valorado>!=<albaran>`, y sv4 enseñarlo.

## 4 · El pie (sv2 + sv3) como control

R13. IA1 debe devolver en la cabecera los cuatro campos del pie tal como están impresos (`null` si no figuran;
también en albaranes ya valorados del proveedor; no se derivan unos de otros, ARCHITECTURE §11).
R14. CUANDO la fase 2 devuelve el pie nulo y la fase 1 lo traía, sv2 debe conservar el de la fase 1.
R15. sv3 debe persistir los cuatro campos en `albaran_documents` y `albaran_documents_merge`, con la misma regla de
fusión por proveedor IA que los demás números de cabecera.
R16. CUANDO sv3 persiste un merge con pie, debe comparar el importe del albarán con el pie (R2, tolerancia
`PIE_TOLERANCIA_EUR`, defecto 0,02) y, si `no_cuadra`, marcar revisión con el motivo `pie_no_cuadra:<suma>!=<pie>`
y la nota «[AVISO] La suma de las líneas no cuadra con el pie del albarán».
R17. SI la comparación es `no_comparable` o el albarán no trae importes, ENTONCES no hay motivo.
R18. El aviso no bloquea: el documento sigue siendo aprobable si está valorado.

## 5 · sv4: qué se enseña

R19. La bandeja debe mostrar una columna «Importe»: el importe del albarán (rótulo «albarán · sin IVA») si trae
importes; si no, el valorado (rótulo «contrato»); «—» si ninguno. Parcial: «N de M sin importe» debajo.
R20. La fila debe llevar la marca ≠ con texto «Albarán X · Valorado Y · Pie Z» cuando el valorado difiera del
importe del albarán o el pie no cuadre.
R21. La columna debe ser ordenable y tener filtro mín/máx sobre esa misma cifra; viajan en la paginación y en la
navegación de la ficha. El filtro actual (solo valorado) se sustituye.
R22. Las tarjetas «Importe pendiente» y las vistas «Obras» y «Proveedores» deben sumar esa misma cifra por documento.
R23. La ficha (vista merge) debe mostrar siempre el importe del albarán, el pie (base, tipo, cuota, total, o «no
leído») y su comparación (cuadra / no cuadra / no comparable), y el valorado con la diferencia si existe; la tabla
de líneas leídas lleva el pie «Total leído (sin IVA)».
R24. El aviso de F-065 R21 debe usar `importe_albaran` de comun.
R25. SI una consulta del importe falla, ENTONCES la bandeja se pinta igual con «—» y traza en el log.

## 6 · sv9 (sin código) y evals

R26. Tests de contrato en sv9: una valoración directa completa produce una petición sin `cod_contrato`, todas las
líneas sin vincular, producto por familia, partida impresa o ninguna y `precio·cantidad = importe`; con una línea
sin importe, `no_admitido` (`no_valorado`).
R27. Los evals de IA1 deben observar los cuatro campos del pie; mientras el libro `IA1_extraccion` no los tenga
rellenos, el informe los declara «no medido» (como hoy `unidad` y `descuentos`). La pasada completa de evals es
exigible por tocar prompts y esquemas (rutas sensibles).

## Fuera de alcance

- Valorar sin contrato los albaranes **sin** importes (siguen como hoy).
- Quitar o recalcular sintéticas con contrato (R12 solo las marca); cambiar el cálculo o la IA de sv5 (solo se
  añaden dos claves al sobre `no_contract`, R5 bis).
- Aprobación automática.
- Backfill de merges ya guardados (decide el humano, v2-P6).
- F-064, F-071, F-073, F-066 X12.
