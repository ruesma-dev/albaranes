<!-- progress/spec_F-078.md -->
# F-078 · La línea valorada guarda lo que se ve · PARADA 1 (spec v1, 2026-10-16)

Spec: `specs/F-078-linea-guarda-lo-que-se-ve/` (requirements 26 R, design, tasks T1–T15). Rama
`feature/F-078-linea-guarda-lo-que-se-ve` (worktree `../albaranes-F-078`), `spec_ready`, prioridad 1, rigor `critico`.
Sin código tocado. Producción: solo lecturas (`SET default_transaction_read_only = on`), secreto leído de Key Vault a
una variable de entorno, nunca a fichero.

## 1. El caso (86c13097-98f8-4e4b-91af-6a378c28d9cf, mortero, CTSU24/0176, aprobado)

| Fila | Tipo | En la fila | Lo que pinta la ficha y de dónde | Lo que hace sv9 |
|---|---|---|---|---|
| 385 | `from_albaran` Nueva (derivada 238 `manual_override`) | `descripcion_linea` vacía, `unidad_albaran` vacía, `unidad_contrato` m3, Q 3 (convertida nula, factor 1) | «MORTERO M-5» (derivada), m3, 01.05.07, 100,60 | manda «Mortero M-5» (concepto del merge) y **sin unidad** |
| 386 | `manual` Nueva (derivada 239) | `descripcion_linea` vacía, `unidad_albaran` vacía, `unidad_contrato` M3, partida vacía | «CARGA INCOMPLETA» (derivada), M3, Almacén, 12,50 | `falta_descripcion` ⇒ `no_admitido` |

Producto «MA9999 · Suministro de materiales»: `producto_sigrid` vacío ⇒ el por defecto, que sv4 (al pintar) y sv9 (al
mandar) calculan con la misma función de comun (`producto_efectivo`) sobre los mismos datos (familia de la blanca y
`tipologia` del merge). Coinciden; no hay hueco ahí. El alta del caso se lanzó en **modo `real`** (2 intentos a las
09:16 UTC, ambos `falta_descripcion`); en la tabla de altas hay además 1 `registrado` (real) y 1 `simulado`.

## 2. Inventario: quién escribe la fila y qué deja vacío

Escriben `albaran_line_valuations` solo **sv6** (replace) y **sv4**; sv3 no (su DDL de valoración se retiró), sv5 no
la lee, sv9 solo la lee. Huecos = campo que la ficha pinta sacándolo de otra tabla.

| Vía | Concepto | Unidad que lee sv9 (`unidad_albaran`) | Q que lee sv9 | Otros |
|---|---|---|---|---|
| sv6 base casada (Contrato) | vacío (ficha: la de la línea de contrato) | la del papel; vacía si IA1 no la leyó | `cantidad_convertida` nula con factor 1 si falta la unidad del papel | — |
| sv6 base Nueva (`missing_partida`, `nueva_no_match`, `no_ia_match`) | vacío (ficha: la derivada, que puede ser la del CONTRATO, p. ej. «MATERIAL DE FERRETERIA») | la del papel o vacía | idem | — |
| sv6 sintética casada / derivada | la de la IA; en derivada la ficha pinta la de la derivada («— AÑO 2026») | = unidad | a veces nula | — |
| sv4 «+ a Sigrid» y «Copiar sin casar → Nueva» | Contrato: concepto del papel; Nueva: concepto (y derivada) | **nula** | Contrato = cantidad; Nueva igual | Nueva: unidad nula en fila y derivada |
| sv4 «Añadir línea» | vacía (todo vacío; se rellena por PATCH) | nula | nula | — |
| sv4 PATCH de fila | Nueva sin blanca: se guarda; **con blanca sin editar: nula** (F-065 CR1/H1); Contrato: solo si difiere | **nunca la escribe** (solo `unidad_contrato` y la derivada) | `cantidades_tras_editar` | ok |
| sv4 «Origen ✎» → contrato | **a NULL a propósito** | no la toca | rehecha | — |
| sv4 «Origen ✎» → Nueva / Dividir | como PATCH (CR1) | copia | ok | partes con descripción puesta |
| sv4 «Traer líneas contrato» | puesta | **nula** | = Q | vinculadas: sv9 no usa la unidad |
| sv4 almacén, producto, bloquear, borrar, deshacer | no tocan estos campos (deshacer restaura la fila de entonces) | | | |

Por campo de «Líneas a Sigrid»:

| Campo | La ficha lo pinta hoy de | sv9 lo lee de | Debe quedar en |
|---|---|---|---|
| Origen | casada / derivada | ids + `sigrid_ide` | la fila (ya) |
| Partida | `codigo_partida_final` (F-051) | igual | la fila (ya) |
| Concepto | Contrato: fila o línea de contrato; Nueva: derivada | fila; si vacía, concepto del merge (solo sin vincular) | `descripcion_linea`, siempre |
| Q | `cantidad_convertida` ?? `cantidad_albaran` | vinculada: convertida; sin vincular: del albarán | la fila; convertida llena sin conversión |
| Unidad | unidad de la línea de contrato / derivada | `unidad_albaran` (sin vincular) | `unidad_contrato` y, sin conversión, `unidad_albaran` |
| Precio | Contrato: fila o contrato; Nueva: derivada | importe / cantidad | `precio_unitario_final` (ya) |
| Importe | fila; si nulo, fórmula en Jinja | `importe_calculado` | la fila (ya; nulo = vacío) |
| Dto, Cód. externo | fila | no se mandan | la fila (ya) |
| Producto | elegido o por defecto (comun) | igual | sin cambio (P5) |

## 3. Medición en producción (solo lectura, 2026-10-16)

Universo: 42 valoraciones (una por documento), **105 filas, todas de documentos activos** (0 en papelera; 0 filas sin
casada ni derivada). 35 filas de 12 documentos aprobados, 70 de 30 pendientes. 23 vinculadas, 82 sin vincular.
Todo `factor_conversion` es 1 (103) o nulo (2): **ninguna fila con conversión real**.

| Hueco (fila vs. ficha) | Aprobado | Pendiente | Total | from_albaran | manual | synthetic |
|---|---|---|---|---|---|---|
| Concepto vacío en la fila que la ficha rellena | 34 | 59 | **93** | 86 | 4 | 3 |
| … de ellas, sv9 no tendría ninguno (`falta_descripcion`) | 3 | 3 | **6** | 0 | 3 | 3 |
| … sv9 manda el concepto del papel y la ficha enseña otro texto (exacto) | 2 | 14 | **16** | 16 | 0 | 0 |
| Sin vincular con `unidad_albaran` vacía y unidad visible (sv9 sin unidad) | 2 | 5 | **7** | 5 | 2 | 0 |
| Vinculada con `cantidad_convertida` nula, factor 1 (sv9: `cantidad_sin_convertir`) | 3 | 3 | **6** | 3 | 1 | 2 |
| Unidad de Q (`unidad_contrato`) distinta o vacía frente a la visible | 0 | 0 | 0 | | | |
| Precio vacío o distinto del visible | 0 | 0 | 0 | | | |
| Importe nulo que la ficha calcula | 0 | 0 | 0 | | | |
| Producto por defecto (no guardado; coincide ficha/sv9) | 25 | 57 | 82 | | | |

Las 16 de «otro texto»: 13 derivadas `missing_partida` de documentos de ferretería que la ficha enseña «MATERIAL DE
FERRETERIA» (la línea del contrato) y sv9 mandaría «DISCO C/ACERO 230 BOSCH», «SIKAFLEX 11 FC…», etc.; la 385 (solo
mayúsculas); la 545 «CONTENEDOR 6 M3 - 170904» frente a «Puesta de contenedor de 6 m3 (Nº contenedor 947)». Las 6
sin descripción: manuales 371, 372 (43fb8c2d, aprobado), 386 (el caso) y sintéticas 402, 405, 406 (4348ecdc,
pendiente). Las 6 vinculadas sin convertida: 401, 403, 404 (4348ecdc) y 420, 421, 423 (6ae68ed1, METALFIRE,
aprobado). Documentos con algún hueco que cambia lo que sv9 manda o rechaza: **4 aprobados y 8 pendientes**.

## 4. Propuesta (detalle en design.md)

1. **comun** `ruesma_comun.linea_valorada.fila_como_se_ve`: la regla con la que pintaba la ficha, escrita una vez.
2. **sv6**: antes de cada `replace_valuation` con líneas, `completar_registros` la aplica a cada registro (filas
   nuevas ya completas; sirve también al builder directo de F-075).
3. **sv4**: la ficha pinta solo la fila (vacío = vacío); el PATCH guarda la descripción en toda fila y la unidad
   también en `unidad_albaran` sin conversión; «Origen ✎», «+ a Sigrid», «Traer» y «Dividir» dejan la fila
   materializada; no se aprueba con filas sin vincular sin descripción.
4. **Relleno**: script de sv6, lectura por defecto; con `--aplicar` lo lanza el humano con autorización aparte.
5. **sv9 sin código** (tests de contrato). Sin DDL. **Orden**: sv6 → relleno → sv4; luego «Solicitar alta» en
   86c13097.

Ficheros: crear 1 módulo de comun, 1 servicio y 1 script de sv6 y sus tests, tests de sv4 y sv9; modificar
`run_valuation_pipeline.py` (sv6), `review_repository.py`, `review_models.py`, `document_detail.html`, `app.py`
(sv4), ARCHITECTURE (regla 22) y `azure-apps/albaranes.md`. Fuera: sv9, sv5, sv3, sv2, DDL, `app.js`, producto
por defecto, conversiones reales en filas sin vincular, la descripción de las vinculadas.

## 5. Solapes con otras features

- **F-053**: sv9 no cambia. Los `no_admitido` por `falta_descripcion` (hoy 1, el caso) se reintentan con «Solicitar
  alta en Sigrid» tras el relleno (T14). El relleno salta documentos con alta bloqueante (1 `registrado`).
- **F-065**: R10 sustituye CR1/H1 («con blanca y sin editar, la descripción va nula y sv9 manda la del papel») y el
  override de Contrato solo si difiere; R12 cambia el `NULL` deliberado de «Origen ✎» → contrato. Tests de F-065 a
  actualizar, listados en design §2. Dividir y PATCH conservan su lógica de cantidades y origen.
- **F-075** (rama abierta): su `ValoracionDirectaBuilder` persiste por otra rama del pipeline de sv6: debe pasar por
  `completar_registros` (quien fusione segundo añade la llamada; un test lo exige). Ambas tocan
  `run_valuation_pipeline.py` y `review_repository.py`: conflicto de texto.
- **F-076** (rama abierta): normaliza la partida del sobre antes del build en el mismo pipeline; F-078 actúa después
  y no toca partidas. Conflicto de texto en `run_valuation_pipeline.py`, sin interacción de reglas.
- **F-077** (rama abierta, solo sv4): toca `review_repository.py` junto a `agree_partida` (~L4641, ~L4787) y la
  plantilla de partida; F-078 toca `_load_conciliation_map_in_session` y el importe. Conflicto de texto. Su «Guardar
  y aprobar» usa el PATCH de fila: con R10–R11 lo que guarda queda completo. R17 (descripción) amplía la validación
  del PUT que F-077 R11 da por fija: avisar al implementer de F-077 si F-078 entra antes.
- **F-058** (pendiente): revalorar sigue descartando lo manual; lo que sv6 cree ya va completo.

## 6. Riesgos

- sv4 desplegado antes del relleno pintaría vacías 93 descripciones (por eso el orden). - Con P1 = (b) (aprobada) no
  cambia lo que va a Sigrid; la ficha pasa a enseñar el concepto del papel en 16 filas (antes, el de la derivada). - «Deshacer» de acciones anteriores restaura filas con huecos (se ven vacías; relleno
  idempotente). - El relleno escribe en documentos aprobados (35 filas) sin cambiar lo que enseña la ficha.

## 7. Preguntas (opción por defecto en negrita; la spec está escrita con ella)

1. **P1 · Descripción de las Nueva que sv6 crea desde una línea de contrato** (16 filas, p. ej. «MATERIAL DE
   FERRETERIA» frente a «DISCO C/ACERO 230 BOSCH»): (a) **se guarda la que se ve hoy (la de la derivada) y es la que
   va a Sigrid**; (b) sv6 guarda el concepto del papel y la ficha pasa a enseñar ese.
2. **P2 · F-065 CR1/H1**: **sustituida: la descripción se guarda siempre en la fila, con o sin blanca y sin
   editar**. Alternativa: mantenerla (entonces el principio no se cumple en las Nueva con blanca).
3. **P3 · Vinculadas con `cantidad_convertida` nula y factor 1** (6): **se guarda Q = cantidad del albarán, la que
   se ve** (lo mismo que ya hace el PATCH, F-065 R10). Con factor nulo no se toca (va a revisión; sv9 la rechaza).
4. **P4 · Unidad para sv9**: **sin conversión, `unidad_albaran` = la unidad que se ve** (7 filas). Con conversión
   real en una sin vincular (0 filas hoy), sv9 seguiría mandando cantidad y unidad del papel: **fuera de F-078**.
5. **P5 · Producto Sigrid por defecto**: **no se guarda** (F-053 se mantiene; ficha y sv9 ya coinciden).
   Alternativa: guardarlo al crear la fila (sv6 necesitaría el mapeo de producto).
6. **P6 · Aprobar con una fila sin vincular y sin descripción**: **sv4 no aprueba («Líneas sin descripción: …»)**.
   Alternativa: solo pintarla vacía y que sv9 la rechace como hoy.
7. **P7 · Relleno**: **script de sv6, solo lectura por defecto; `--aplicar` lo lanzas tú; incluye aprobados y
   pendientes; salta papelera y alta bloqueante**. Alternativas: no tocar aprobados; o sentencias en el arranque
   de sv6 (descartado: escribiría datos en cada arranque).
8. **P8 · Descripción editada en una fila Contrato vinculada** (2 filas): Sigrid usa la de su línea de contrato.
   **Fuera de F-078** (si quieres, ficha nueva para avisarlo en la ficha).
9. **P9 · Último respaldo del concepto**: si ni la fila ni su línea tienen texto, **sv6 y el relleno guardan el
   concepto de la blanca (lo que sv9 manda hoy)** (1 fila hoy). Alternativa: dejarla vacía.
10. **P10 · Alcance y rigor**: **servicios comun, sv6 y sv4; sv9 sin código; rigor `critico`; prioridad 1**.

## PARADA 1: APROBADA (2026-10-16)

Decisiones del humano (vía el líder):

- **P1 = (b)**: en las Nueva que sv6 crea desde una línea de contrato (y, por la misma regla, toda Nueva con blanca
  sin descripción propia) se guarda el **concepto del papel** (p. ej. «DISCO C/ACERO 230 BOSCH»); la ficha pasa a
  enseñar ese y es el que va a Sigrid. La spec, escrita con (a), queda ajustada: glosario «Lo que se guarda» y
  función `fila_a_guardar` (antes `fila_como_se_ve`), R2, R19, R25; design §3 y D1; tasks T2 y T13. Efecto en las
  **16 filas** de §3: lo que manda sv9 no cambia (ya mandaba el concepto del papel); lo que pinta la ficha sí (la
  385 pasa de «MORTERO M-5» a «Mortero M-5»; las 13 de ferretería, de «MATERIAL DE FERRETERIA» a su concepto; la 545,
  a «Puesta de contenedor de 6 m3 (Nº contenedor 947)»). Las Nueva sin blanca (manual, reparto, sintéticas) siguen
  con la descripción de su derivada.
- **P8**: fuera de F-078; registrada en `dev` como **F-079** (pending, sv4: avisar al editar la descripción de una
  línea vinculada a contrato). Referenciada en design D5.
- **P2–P7, P9, P10**: opción por defecto (la que ya fijaba la spec).

Estado: `spec_ready` (aprobada). No se implementa todavía: espera turno (F-072 está `in_progress`).

