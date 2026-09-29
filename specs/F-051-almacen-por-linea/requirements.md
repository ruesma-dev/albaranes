<!-- specs/F-051-almacen-por-linea/requirements.md -->
# F-051 · Almacén por línea · Requisitos

Petición literal del humano (2026-09-29) en la ficha de `harness/features.json`.
Toca **sv2** (`services/albaranes-api`, solo el prompt de IA1), **sv6**
(`services/albaran-valoracion-persist`) y **sv4** (`services/albaranes-front`).
Rigor `critico`. Hallazgos y decisiones en `progress/spec_F-051.md` (v1 y v2).

**Regla del humano (2026-09-29), literal**: «si hay una partida en el
documento esta aplica a todas las lineas, si hay partidas por linea, en
general aplica a las que esten marcadas». Y: «hasta ahora ia1 lo hace como
decimos excepto que no sabe qué hacer con línea sin partida». Lectura (a
confirmar en la PARADA 1 lo no literal): partida única de documento ⇒ todas
las líneas; partidas por línea ⇒ cada una a las líneas que marca o agrupa;
línea sin partida marcada ⇒ **vacía** (almacén); sin partida en ningún sitio
⇒ todas en almacén.

## Vocabulario

- **Almacén**: línea **sin partida** a propósito. No es un código: es
  `codigo_partida_final = NULL` más una **marca** en
  `albaran_line_valuations.partida_action`; en Sigrid, `dcapro.paride` vacío
  (índice 0). Nunca un literal «ALM» (humano, 2026-08-13, D2 de F-007).
- **Marcas de almacén** (`ACCIONES_ALMACEN`): `almacen_sin_partida` (nueva,
  sv6: el albarán no trae partida), `almacen_elegido` (nueva, sv4: lo eligió
  el revisor), `alm_new_line_created` (existe: el papel imprime «ALM») e
  `inherited_from_base_line` (existe: hereda la partida vacía de su base).
- **Línea en almacén**: partida final vacía **y** marca de almacén.
- **Línea sin partida**: partida final vacía **sin** marca (valoraciones
  anteriores a F-051, o el revisor borró el campo a mano): fallo, se avisa.
- **Familia destinada**: familia efectiva (`ruesma_comun.contratos.familias.
  familia_efectiva`) incluida en `FAMILIAS_DESTINADAS` de sv6; por defecto
  `hormigon,mortero,combustible,alquiler_maquinaria,residuos`.

## sv2 — IA1 deja vacía la línea sin partida (solo prompt)

- **R25.** El prompt de fase 1 de sv2 (`config/prompts.yaml`,
  `albaran_factura_es`) debe indicar que, CUANDO el papel marca partidas por
  línea, una línea sin partida marcada se devuelve con `codigo_imputacion`
  null, sin copiarle la de otra línea, aunque sea el único código escrito
  (esa línea es almacén). El caso mixto (partida de documento y además
  partidas en algunas líneas) queda como decisión D9.
- **R26 (regresión).** El prompt de fase 1 debe conservar las reglas que hoy
  ya cumple IA1: partida única de documento ⇒ todas las líneas; partida
  asociada por cercanía, raya, flecha o llave ⇒ las líneas que marca; sin
  código claro ⇒ null.
- **R27.** Los cuatro prompts de fase 2 (genérico y por familia) deben
  recibir la regla de R25 al incrustar `{prompt_fase_1}`, sin copia propia.

## sv6 — la valoración no inventa partida

- **R1.** CUANDO sv6 valora una línea base `from_albaran` sin
  `codigo_partida_albaran`, el sistema debe resolver
  `codigo_partida_final = NULL`, `partida_action = "almacen_sin_partida"` y
  añadir la razón `"almacen_sin_partida_en_albaran"`, en lugar de copiar la
  partida de la línea de contrato que casó la IA.
- **R2.** MIENTRAS una línea esté en el caso de R1 y la IA haya casado una
  línea de contrato, el sistema debe conservar ese
  `matched_contrato_line_id` y el precio final calculado: el almacén cambia la
  imputación, nunca la valoración económica.
- **R3.** CUANDO una línea del caso de R1 no tiene match de la IA, el sistema
  debe crear la derivada de respaldo (`origen = "nueva_no_match"`,
  `codigo_partida = NULL`) conservando `partida_action = "almacen_sin_partida"`.
- **R4.** SI una línea del caso de R1 es de una familia destinada, ENTONCES el
  sistema debe marcarla `review_required` con la razón
  `"partida_ausente_familia_destinada"`, sin rellenar ninguna partida.
- **R5.** MIENTRAS la línea sea de familia NO destinada (o sin familia), el
  sistema NO debe marcar revisión por la ausencia de partida.
- **R6 (regresión).** CUANDO la línea trae `codigo_partida_albaran`, el sistema
  debe comportarse exactamente como hoy, incluido el literal impreso «ALM»
  (`alm_new_line_created`, derivada `alm_acopio`).
- **R7 (regresión).** El sistema debe seguir haciendo que complementarias y
  sintéticas hereden la partida final de su base: con base en almacén heredan
  `NULL` con `partida_action = "inherited_from_base_line"`.
- **R8 (interruptor).** DONDE `ALMACEN_SIN_PARTIDA_ENABLED=false` (por defecto
  `true`), el sistema debe valorar exactamente como antes de F-051.
- **R9.** El sistema debe interpretar `FAMILIAS_DESTINADAS` como CSV sin
  distinguir mayúsculas ni espacios; vacío significa «ninguna destinada».
- **R28.** MIENTRAS otra línea base del mismo albarán tenga partida, sv6 debe
  tratar la línea sin `codigo_partida_albaran` según R1: nunca le copia la
  partida de sus hermanas (la herencia de R7 es solo base → complementaria).

## sv4 — pintar, elegir y asignar almacén

- **R10.** El sistema debe clasificar el estado de partida de cada línea
  salmón con una función pura en tres valores: `partida` (código no vacío),
  `almacen` (vacío y marca de almacén) y `sin_partida` (vacío sin marca).
- **R11.** MIENTRAS una línea esté en almacén, la ficha debe mostrar
  «Almacén» en la columna de partida —placeholder en filas editables, texto en
  filas de solo lectura— y NUNCA la partida de la línea de contrato casada.
- **R12.** MIENTRAS una línea esté `sin_partida`, la ficha debe mostrarla con
  aviso visual («Sin partida») distinto del de almacén.
- **R13.** CUANDO el revisor abre el desplegable de partida de cualquier línea
  editable, el desplegable debe ofrecer como PRIMERA opción «Almacén (sin
  partida)», haya o no contrato, obra o líneas de contrato, y sea cual sea el
  texto tecleado en el filtro.
- **R14.** CUANDO el revisor elige «Almacén» en una línea, el sistema debe
  persistir en esa línea de valoración `codigo_partida_final = NULL` y
  `partida_action = "almacen_elegido"`, sin tocar cantidad, precio, importe,
  descuento ni `review_required`.
- **R15.** CUANDO se asigna almacén a una línea casada con una línea de
  contrato de Sigrid, el sistema debe CONSERVAR `matched_contrato_line_id`
  (la fila sigue siendo «Sigrid», no pasa a «Nueva»).
- **R16.** CUANDO el revisor pulsa «Almacén a todas las líneas» y confirma, el
  sistema debe aplicar R14 y R15 a TODAS las líneas de valoración del
  documento (base, complementarias y sintéticas), también a las que ya tenían
  partida, en una sola transacción.
- **R17.** ANTES de aplicar R16, la ficha debe pedir confirmación indicando
  cuántas líneas tienen hoy partida y la perderán.
- **R18.** CUANDO se aplica R14 o R16, el sistema debe registrar UNA entrada
  en `undo_log` que restaure el estado anterior de todas las líneas tocadas.
- **R19.** CUANDO el revisor guarda otros campos (cantidad, descuento…) de
  una línea en almacén sin tocar la partida, el sistema debe mantenerla en
  almacén y NO convertir una fila Sigrid en «Nueva».
- **R20.** CUANDO el revisor asigna una partida real a una línea en almacén
  (desplegable o edición), la línea debe dejar de estar en almacén; si la
  partida coincide con la de su línea de contrato casada, la fila sigue siendo
  Sigrid.
- **R21.** El cálculo de confianza de sv4 debe puntuar la partida de una línea
  en almacén como resuelta (factor 1) y la de una línea `sin_partida` como no
  resuelta (factor 0).
- **R22.** SI la vista no es editable (`document.is_editable` falso) o la
  línea no tiene valoración, ENTONCES la ficha no debe ofrecer ni la opción ni
  el botón (misma regla que las demás ediciones de la fila salmón).
- **R23.** SI la petición de almacén nombra una línea que no pertenece al
  documento, ENTONCES el sistema debe rechazarla sin modificar nada.

## Contrato hacia Sigrid (se documenta; no se implementa aquí)

- **R24.** El sistema debe documentar (`docs/ARCHITECTURE.md`, semántica de
  dominio) que una línea en almacén va a Sigrid con `paride` vacío y que nadie
  la rellena desde el contrato, la plantilla ni la línea anterior del producto.

## Trazabilidad requisito → test

| R | Test previsto (unit, sin red ni BBDD) |
|---|---|
| R25–R27 | `test_f051_r25_*`…`_r27_*` sobre el texto real de `prompts.yaml` e instructions renderizadas (patrón de `test_f043_prompt_fase1.py`) + evals (T21) + MANUAL (T23) |
| R1–R3 | `test_f051_r1_*`…`_r3_*` sobre `PartidaMatcher` y el builder de sv6 |
| R4, R5, R9 | `test_f051_r4_*`, `_r5_*`, `_r9_*` (política pura + builder) |
| R6, R7, R28 | `test_f051_r6_*`, `_r7_*`, `_r28_*` (no regresión: partida impresa, ALM, herencia, hermanas) |
| R8 | `test_f051_r8_*` con el interruptor apagado |
| R10, R21 | `test_f051_r10_*`, `_r21_*` puros en sv4 |
| R11, R12 | `test_f051_r11_*`, `_r12_*` del montaje del detalle con repositorio falso + MANUAL navegador |
| R13 | `test_f051_r13_*`: la plantilla/JS servido contiene la opción fija + MANUAL navegador |
| R14–R16, R19, R20, R23 | `test_f051_r14_*`… con la sesión SQL simulada (SQL emitido y parámetros) |
| R17 | MANUAL navegador (diálogo con el recuento) + test del recuento servido |
| R18 | `test_f051_r18_*` del servicio con repositorio falso |
| R22 | `test_f051_r22_*` render de la plantilla con `is_editable` falso + MANUAL navegador |
| R24 | revisión del reviewer (los docs dicen lo que hace el código) |
