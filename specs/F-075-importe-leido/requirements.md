# F-075 · La bandeja y la ficha muestran el importe leído del albarán — requisitos

Rigor **estandar** (sv4 solo pinta y consulta: sin DDL, sin escrituras, sin colas). Servicio:
**sv4-front**. Prioridad 1. Informe de spec y preguntas al humano: `progress/spec_F-075.md`.

## Origen

Correo de administración de obra (obra 0686): un albarán de DISCOIN con precios sale en la bandeja
con «Importe valorado —» y «Sin valoración». DISCOIN no tiene contrato en la obra: sv3 encuentra 0
contratos y no dispara `q-valoracion`, así que sv6 no valora. La vista «Obras» y la tarjeta
«Importe pendiente» también suman solo lo valorado. Merges de ejemplo: `dfdc8aab-08e1-49f0-978d-bb906515e748`
y `5dea6509-4a81-4192-b8b0-3a21041931ca`.

Decisión del humano (2026-10-15, literal): «aunque tenga contrato, el importe leído».

## Qué se lee hoy (investigación, detalle en `progress/spec_F-075.md` §2)

- IA1 (sv2, `config/prompts.yaml`) **no lee totales de cabecera**: ni total, ni base imponible, ni
  IVA («Evita subtotales, totales, IVA…»); `CabeceraAlbaran` no tiene esos campos.
- Por línea lee `precio` (unitario **sin IVA**), `descuento` y `precio_neto`, que es el **importe de
  la línea tras descuento** (ARCHITECTURE §13). Si el papel no lo trae, la IA lo calcula con
  `cantidad × precio × (1 − dto/100)`.
- sv3 lo persiste en `albaran_lines_merge.precio_neto`. sv4 **no escribe** las líneas del merge
  desde F-065: la cifra es la del papel (o la que dedujo la IA del papel), nunca la del contrato.
- sv4 ya suma `precio_neto` en la ficha (`suma_leida`, F-065 R21), solo para el aviso al aprobar.

## Definiciones

- **Importe del albarán**: suma de `precio_neto` de las líneas del merge del documento que lo
  tienen. Es **sin IVA**. No depende de contrato, valoración ni estado.
- **Importe valorado**: `albaran_valuations.total_valorado` (sin cambios).
- **Difieren**: los dos existen y `|valorado − albarán|`, redondeado a 2 decimales, es ≥ 0,01 €
  (el mismo umbral que F-065 R21).

## Cálculo (un único punto en sv4)

R1. El sistema debe calcular el importe del albarán como la suma de los `precio_neto` no nulos de
las líneas de `albaran_lines_merge` del documento, con su signo (un abono negativo resta), sin
redondear la suma; solo se redondea al pintar (2 decimales, formato `importe_eur`).

R2. SI el documento no tiene líneas o ninguna trae `precio_neto`, ENTONCES el importe del albarán
debe ser nulo (no 0), y se pinta «—» con el texto de ayuda «El albarán no trae importes».

R3. MIENTRAS unas líneas traigan `precio_neto` y otras no, el importe del albarán debe ser la suma de
las que lo traen y marcarse **parcial** con «N de M líneas sin importe». Las líneas sin importe no
suman nada: sv4 no las completa con el contrato ni con `cantidad × precio`.

R4. El sistema debe calcular la cifra con una sola función de dominio de sv4, y el aviso de F-065
R21 (`suma_leida` / `aviso_suma`) debe usar esa misma función y el mismo umbral «difieren».

R5. sv4 no debe persistir, recalcular ni escribir el importe del albarán: solo lo lee al pintar.
Sin DDL y sin sentencias que no sean SELECT.

## Bandeja (`/documents`)

R6. La bandeja debe mostrar en cada fila una columna «Importe albarán», con la aclaración visible
«sin IVA · leído», junto a «Importe valorado», tenga o no contrato o valoración el documento, también
en la papelera.

R7. La columna «Importe valorado» debe seguir mostrando lo que muestra hoy.

R8. CUANDO el importe valorado y el del albarán difieran, la fila debe mostrar una marca visible
junto al importe del albarán, con el texto «Valorado X · Albarán Y · Diferencia Z» (Z = valorado −
albarán). Si no difieren o falta alguno, sin marca.

R9. La bandeja debe poder ordenarse por «Importe albarán» (asc/desc, nulos al final, desempate por
recepción descendente como hoy), y los botones anterior/siguiente de la ficha deben recorrer ese
mismo orden.

R10. La columna «Importe albarán» debe tener su propio filtro mín/máx (`min_importe_albaran`,
`max_importe_albaran`); con él aplicado, los documentos con importe del albarán nulo quedan fuera. El
filtro mín/máx actual sigue filtrando por el importe valorado, sin cambios.

R11. Los filtros nuevos deben viajar en la paginación, la ordenación y la navegación de la ficha.
SI llegan con un valor no numérico a `/documents`, ENTONCES 422 como `min_importe`; en la ficha
(`_filters_from_query`) se ignoran (tolerante, como hoy).

R12. La cabecera de la bandeja debe mostrar, además de la tarjeta actual (rotulada «Pendiente
valorado»), una tarjeta «Pendiente según albarán» con la suma del importe del albarán de los
documentos activos no aprobados (los de importe nulo aportan 0).

R13. SI la consulta del importe del albarán falla, ENTONCES la bandeja debe pintarse igual, con
«—» en esa columna y 0 en esa tarjeta, y dejar traza en el log (best-effort, como el resto).

## Ficha (vista merge)

R14. La ficha en vista merge debe mostrar siempre un bloque «Importe del albarán (sin IVA, leído):
X €», con la marca de parcial (R3) o «—» (R2), haya o no valoración.

R15. CUANDO haya valoración, el bloque debe mostrar también el total valorado y la diferencia, con
la marca de R8 si difieren.

R16. La tabla «Líneas leídas del albarán (IA)» debe llevar una fila de pie «Total leído (sin IVA)»
con la misma cifra que el bloque de R14.

R17. Las vistas de un proveedor IA concreto (no editables) no muestran el bloque.

## Vistas «Obras» y «Proveedores»

R18. La vista «Obras» debe mostrar, junto a «Importe valorado», una columna «Importe albarán» con la
suma del importe del albarán de los documentos activos de la obra y, si alguno no trae importe, «N
sin importe» debajo.

R19. La vista «Proveedores» debe mostrar la misma columna con el mismo criterio.

R20. El «Importe valorado» de las dos vistas y de la tarjeta «Pendiente valorado» debe dar las
mismas cifras que hoy (última valoración por documento).

## Límites

R21. Ningún servicio distinto de sv4 cambia: ni prompts ni esquema de sv2, ni esquema de sv3, ni
sv5, sv6, sv9 o comun.

## Fuera de alcance

- Leer el total, la base imponible o el IVA de la cabecera del papel (sv2 + sv3, DDL): feature
  aparte si el humano la quiere (P2).
- Pintar las líneas leídas en la columna «Líneas valoradas» cuando no hay valoración (P4).
- Valorar o aprobar un albarán sin contrato (F-053 R37 lo sigue impidiendo sin valoración).
- El sumatorio al pie de las filas valoradas de F-066 (X12); F-075 le deja hecha la cifra.
- F-071 y F-073.
