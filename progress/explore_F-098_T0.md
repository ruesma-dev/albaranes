<!-- progress/explore_F-098_T0.md -->
# F-098 · T0: lectura del árbol de partidas (solo lectura, 2026-10-24)

Autor: spec-author. Responde a design.md §9 y a la P6 tal como la planteó el humano. **La spec no se ha tocado**:
esto es la base para la v2, que espera a que se cierre la PARADA 1.

**Cómo se leyó.** Sigrid solo por `POST /api/sql/read` (siempre `SELECT`), con `SQL_PARTIDAS_POR_OBRA` de comun,
una obra por petición. Además, dos `SELECT` de conjunto (raíces y nivel 1 de las 723 obras de la empresa 1) y uno de
nombres de obra. Ninguna respuesta llegó con `truncated` (el script se para si llega una). La BBDD `albaranes` de
Azure se leyó con `default_transaction_read_only=on` y comprobando antes `SHOW transaction_read_only = on`. Las
claves salieron de Key Vault a variables del proceso y se borraron en `finally`. Los scripts están en el scratchpad,
no en el repo. Hojas, capítulos y R3 se calcularon como dice la spec v1: `_indexar` y `normalizar_partida` de comun,
y el límite letra↔dígito de R3.

**Universo.** Hay 19 obras: las 18 con albaranes en los últimos 90 días (más 3 documentos sin obra) y la 0727.
0692 y 0686 ya estaban entre las 18. La 0727 se añadió por ser la segunda obra Merkel. 277 líneas valoradas
`from_albaran` de 135 documentos activos.

## 1. Raíces y nivel de CD/CI/CP

- **CD, CI y CP son raíces en las 19 obras** (padre 0). R2 de v1 coincide con ese nivel en las 19.
- **Ninguna de las 19 tiene una sola raíz**: la rama de R2 que baja un nivel no se activa nunca.
- En las 723 obras de Sigrid, 669 tienen CD, CI y CP como raíces. Solo 6 tienen una única raíz: `LEV`
  (levantamiento, sin hijos) en 3, y `26`, `3` y `01` en tres obras antiguas (090207, 180307, `CP`). En ninguna de
  las 6 cuelgan CD, CI o CP.
- **Ninguna raíz se llama PRESUPUESTO**: en la 0459, «TOTAL PRESUPUESTO» es el `res` de la raíz `CD`.
- **«Siempre CD, CI y CP» no se cumple en 5 de las 19 obras.** Tienen otras raíces al mismo nivel:

| Obra | Raíces | Lo que hay fuera de CD/CI/CP (hojas) |
|---|---|---|
| 0686 | ANT., CD, CI, CP | `ANT.` «AJUSTES ALMACÉN» (4 hojas: `98.01`…`98.04`) |
| 0692 | CD, CI, CI.F2, CP | `CI.F2` «COSTES INDIRECTOS FASE 2» (91 hojas: `CI.01.01`…) |
| 0693 | CD, CI_F1, CI_F2, CP | **no hay `CI`**: `CI_F1` y `CI_F2` (66 hojas cada uno: `CI_F1.01.01`) |
| 0694 | CD, CI, CI0, CP | `CI0` «COSTES INDIRECTOS DEMOLICIONES» (34 hojas: `CI0.01.01`) |
| 0711 | CD, CD1, CI, CP | `CD1` «ANTICIPOS» (1 hoja de cod `CD2`) |

  Las 14 obras restantes tienen exactamente CD, CI y CP. En las 723 obras aparecen además `PD`, `CD1`, `CD'`,
  `100`, `CIP`, `CDP`, `POSTV`, `CP.00`… Las otras 54, casi todas antiguas, no tienen las tres como raíces.
- 0000 y 0278: `CD` es una hoja (sin hijos, cod `CD`).

## 2. Hojas cuyo cod no empieza por su capítulo (R3)

- **CD: ninguna hoja lleva el prefijo** en 16 obras. Las excepciones son la 0692 (ver §6) y la 0000 y la 0278, donde `CD` es la propia hoja.
- **CI y CP: todas las hojas lo llevan** (0 sin él en las 19).
- **Capítulos extra:** `ANT.` 4 de 4 sin su prefijo (`98.01`, `98.02`, `98.03`); `CI.F2` 91 de 91 (`CI.01.01`,
  `CI.01.02`, `CI.01.03`: empiezan por `CI`, no por `CI.F2`); `CD1` 1 de 1 (`CD2`); `CI0`, `CI_F1` y `CI_F2`, 0.
- **Tres ejemplos de CD por obra:** 0686 `01.01.01` · 0678 `01.01.01.01` · 0695 `01.01.01`, `E01`, `MK0101` ·
  0696 `P4.01.01` · 0693 `01.01`, `37.01` · 0711 `01.01`, `OC.01.01` · 0459 `01.01`, `PC-100`.
- **Lo que hay debajo de CD:** el cod de la hoja suele empezar por el de su subcapítulo (`01` ⇒ `01.01.01`). No
  siempre: 0695 tiene 970 hojas `PC01.01` bajo `37 PRECIOS NUEVOS` y 41 `OC00` bajo `38 ORDENES DE CAMBIO`.

## 3. Ambigüedad de la regla «sin CI/CP ⇒ CD»

- **Ningún cod ni ninguna clave de F-076 está a la vez en CD y en un capítulo que no sea CI/CP**: 0 en `ANT.`, `CD1`,
  `CI.F2`, `CI0`, `CI_F1` y `CI_F2`. Los `98.xx` de la 0686 no chocan con nada de CD.
- **La regla aplicada al pie de la letra** (sin CI/CP ⇒ buscar solo en CD; con CI/CP ⇒ solo en ese capítulo; con CD
  ⇒ quitarlo y buscar en CD) se simuló sobre el cod y sobre el código completo de cada hoja:
  - Todas las hojas de CD, CI y CP se encuentran a sí mismas. Las únicas excepciones son los cod que ya estaban
    repetidos (§4).
  - **No encuentra** las hojas de `ANT.` (4), `CD1` (1), `CI0` (34), `CI_F1` y `CI_F2` (132) ni 28 de `CI.F2`.
    Tampoco las encontraría ningún albarán.
  - **Encuentra otra hoja** en 63 hojas de `CI.F2` de la 0692: la lectura `CI.01.01` acaba en la `CI.1.1` de `CI`
    porque comparten clave. Es elegir una hoja equivocada en silencio.
- **El código completo no crea ambigüedad nueva** (el R-3 de design §7): el completo de una hoja no coincide con la
  clave del cod de otra en ninguna de las 19 obras.

## 4. Pares (obra, cod) repetidos entre hojas

0692: 7 (`CI.6.1`…`CI.6.4`…, en `CI` y en `CI.F2`) · 0696: 1 (`P4.08.05`) · 0711: 3 (`02.26n`, `02.27n`, `10.02.04`)
· resto: 0. Por clave: 0692 63, 0693 5 (`37.01` y `37-.01`), 0696 1, 0711 3. Todo esto ya era `ambigua` con F-076.

## 5. BBDD `albaranes` (solo lectura, documentos activos)

- **Partidas finales que casan solo por el código completo: 2 líneas, de 1 documento** (0686, pendiente, sin alta).
  Su partida final es `CD.21.02.21` y su cod sería `21.02.21`. En el resto de líneas `from_albaran`: 171 exactas,
  13 normalizables, 13 fuera de la lista (0694 `CI.14.18`, 0696 `P4.PJ.36.01`…, ajenas a F-098) y 78 vacías.
- **Hay 55 partidas finales que empiezan por CD y son correctas.** Son cods de Sigrid: `CD2.xx` de la 0692, que
  vienen de líneas de contrato. De ellas, 49 están aprobadas: 43 en altas `registrado`, 5 en `ya_en_sigrid` y 1 en `revisar`.
- **Cómo escriben los proveedores** (`codigo_partida_albaran`; el `codigo_imputacion` del merge da lo mismo):
  - **CD**: 5 lecturas, todas de la 0686 (`CD.21.02.21` ×2, `CD.07.14` ×2, `CD.99.01.64`). Las 5 casan como
    `completa`.
  - **CI**: 51 lecturas. 44 casan como `normalizada` (`CI.04.18` ⇒ `CI.4.18`) y 7 quedan fuera de la lista.
  - **CP**: ninguna.
  - Ejemplos sin prefijo: 0686 `99.01.64` y `07.17` (exactas); 0696 `P4.22.01.03.07` (exacta).

## 6. Los casos que pidió el humano

- **0692 y su «98».** Hoy **no tiene ningún capítulo 98**. Sus raíces son CD, CI, CI.F2 y CP; si lo tuvo, ya no está.
  - Su CD es mixto: `CD1 DEMOLICIONES` (28 hojas sin prefijo: `01.01`) y `CD2 FASE 2` (36 hojas cuyo cod es
    `CD2.01`). R3 da `CD.01.01` y `CD2.01`.
  - `CI.F2` repite la numeración de `CI`, con ceros (`CI.01.01` frente a `CI.1.1`). Su completo según R3 sería
    `CI.F2.CI.01.01`.
- **El «98» que el humano recuerda está en la 0686.** Allí el capítulo tiene cod `ANT.` (no `98`) y res «AJUSTES
  ALMACÉN». Sus 4 hojas son `98.01` a `98.04` (anticipos, anulación de imputaciones, ajuste de decimales): no
  empiezan por `ANT.` y no chocan con CD. R3 tal como está escrita daría `ANT..98.01`, **con doble punto: es un
  fallo de R3**.
- **Merkel son la 0695 y la 0727, y ninguna tiene P4 ni P5.** Su CD cuelga en `01`…`38`, con hojas `01.01.01`.
  **P4 y P5 están en la 0696** (88+88 viviendas, parcelas 04 y 05):
  - CD tiene debajo `P4 PARCELA 4` (1.354 hojas), `P5 PARCELA 5` (1.208), `P8 LINEAS ALMACEN` (1) y `CASETA V.` (6,
    con cod `P7.xx`).
  - **El cod de Sigrid ya trae el P4**: `P4.01.01`, `P5.02.01.01`. Coincide con lo que se escribe en el albarán
    (`P4.22.01.03.07`, que casó exacta). El completo según R3 es `CD.P4.01.01`.
- **Una sola raíz:** ver §1. Ninguna de las 19 obras la tiene, y en las 6 de Sigrid que la tienen la raíz no es
  PRESUPUESTO y no tiene CD, CI ni CP debajo.

## Qué implica para la spec

- **R2 aguanta, pero conviene simplificarla.** Capítulo = raíz de la cadena, **sin la rama de bajar un nivel**.
  - No se activa en ninguna obra con albaranes.
  - En las 6 obras de Sigrid donde se activaría (antiguas, sin CD/CI/CP) solo cambiaría `26` por `26.01`.
  - Quitarla elimina el riesgo R-1 de design §7: perder `CD` en una obra con solo CD.
  - Los chips salen de los datos (`ANT.`, `CI.F2`, `CI0`, `CI_F1`, `CD1`…), como dice ya R15.
- **R3 aguanta con un arreglo.** Al componer no se debe duplicar el separador final del capítulo: `ANT.` + `98.01` ⇒
  `ANT.98.01`, no `ANT..98.01`. Queda abierto si en `CI.F2` el completo debe ser `CI.F2.CI.01.01` o el cod tal cual:
  lo decide el humano. El límite letra↔dígito sí es necesario: sin él, `CD2.01` se pintaría como `CD.CD2.01`.
- **La regla del humano encaja con v1 si se expresa contra la lista**, no como una regla de texto.
  - «Sin CI/CP ⇒ CD» equivale a lo que ya hacen R6 y R3. Las hojas de CD no llevan `CD` en su cod, así que la
    lectura se compara con su cod (`normalizada` o `exacta`); `CD.xx` se compara con su completo (`completa`).
  - En las 19 obras, R6 da el mismo resultado que la regla para todas las hojas de CD, CI y CP. Además sí encuentra
    las de `ANT.`, `CD1`, `CI0`, `CI_F1` y `CI_F2`, que la regla literal pierde.
  - La única diferencia es `CI.F2`: las 63 claves compartidas con `CI` salen `ambigua` (a revisión) con R6. La regla
    literal las mandaría en silencio a `CI`.
  - **Recomendación: no restringir la búsqueda a CD. Mantener R6 sobre toda la lista.**
- **«Quitar CD al registrar» no debe hacerse quitando texto.**
  - Se cumple porque se guarda el cod de la hoja (P1 = a) y sv9 lo manda (R30).
  - Quitar `CD` del texto rompería 55 líneas de la 0692 (`CD2.01` ⇒ `2.01`; 48 ya están en Sigrid) y la hoja `CD2`
    de la 0711.
  - Conviene escribirlo en R6 o en R25: lo que se manda es el cod de la lista, nunca la lectura recortada.
- **R9 no choca con la regla del humano.** R9 prohíbe forzar un parecido que no está en la lista; la regla del humano
  se apoya en el árbol (R2/R3). En las 19 obras no hay ninguna hoja de CD con cod `CD.` que R9 tenga que proteger.
  - Se mantienen sus tres ejemplos.
  - Conviene añadir uno: `CI.01.01` no se lleva a `CI.1.1` de otro capítulo cuando hay dos candidatas (0692).
- **R6 no cambia.** Conviene añadir dos casos de test de datos reales: `ANT.` con `98.01` y `CI.F2`/`CI` de la 0692
  (`ambigua`).
- **Fixtures de R1–R13.** Sustituir la «raíz única» de design §3 por árboles medidos: 0686 (`ANT.`), 0692 (CD mixto
  y `CI.F2`), 0693 (sin `CI`) y 0696 (`P4` bajo CD).
- **P4: 2 líneas guardadas con prefijo** (1 documento pendiente de la 0686). Muy por debajo de ~20 ⇒ **P4 = b**:
  corregirlas a mano en la ficha. R32 y su script se pueden quitar.
- **P2:** en las obras con albaranes hay 11 cods repetidos (0692, 0696, 0711). No justifica meter `paride` en F-098.
