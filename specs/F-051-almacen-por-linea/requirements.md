<!-- specs/F-051-almacen-por-linea/requirements.md -->
# F-051 · Almacén por línea · Requisitos (v4, 2026-10-05)

Petición literal en la ficha (`harness/features.json`). Toca **sv2** (solo el
prompt de IA1), **sv6** y **sv4**. Rigor `critico`. Decisiones D1–D9, todas
del humano (PARADA 1 del 2026-10-05; D1 rehecha): `progress/spec_F-051.md`.

**Regla del humano** (2026-09-29; cerrada el 2026-10-02): «si hay una partida
en el documento esta aplica a todas las lineas, si hay partidas por linea, en
general aplica a las que esten marcadas». Concreción del 2026-10-02: (a) tres
líneas con «03.02» escrito solo junto a la segunda ⇒ la 1.ª y la 3.ª, almacén;
(b) partida de documento y otra junto a alguna línea ⇒ las marcadas la suya, el
resto la de documento (D9); (c) portes, complementos y similares sin marca
siguen la de su línea base. Lo decide **IA1 leyendo el papel**, nunca una regla.

## Vocabulario

- **Almacén** (D1, humano 2026-10-05): «no se asocia a partida» y «en el visor
  cuando una línea no tenga partida que sea almacén […] negocio ya funciona así
  a mano». **Línea en almacén** = con valoración y `codigo_partida_final` vacío,
  **tenga o no marca**; en Sigrid, sin partida y con almacén (F-053). Nunca «ALM».
- **Marcas de almacén** (`partida_action`; solo trazabilidad de quién o por qué,
  NO deciden el estado): `almacen_sin_partida` (nueva, sv6: el albarán no trae
  partida) y `almacen_elegido` (nueva, sv4: el revisor eligió «Almacén» o vació
  la partida); siguen `alm_new_line_created` (ALM impreso) e `inherited_from_base_line`.
- No existe un estado «sin partida» distinto de almacén (lo había en v3).
- **Código de documento**: partida manuscrita en cabecera, sello o margen, no
  junto a una línea. **Código de línea**: junto a una o agrupando varias.
- **Familia destinada**: familia efectiva (`ruesma_comun.contratos.familias.
  familia_efectiva`) en `FAMILIAS_DESTINADAS` de sv6; por defecto
  `hormigon,mortero,combustible,alquiler_maquinaria,residuos`.

## sv2 — IA1 decide a qué líneas va cada partida (solo prompt)

- **R25.** El prompt de fase 1 (`config/prompts.yaml`, `albaran_factura_es`)
  debe indicar que un código de línea se aplica SOLO a las líneas que marca o
  agrupa, aunque sea el único del documento, y que una línea sin código propio,
  sin código de documento y que no sea complemento de otra se devuelve con
  `codigo_imputacion` null, sin copiarle el de otra (irá a almacén), con el
  ejemplo (a).
- **R26 (regresión).** El prompt de fase 1 debe conservar: asociación por
  cercanía, raya, flecha o llave; márgenes superior o inferior ⇒ todo el
  documento; varios en márgenes sin relación clara ⇒ el primero; sin código
  claro ⇒ null; las líneas de un mismo vertido o servicio, mismo código.
- **R27.** Los cuatro prompts de fase 2 (genérico y por familia) deben recibir
  R25, R29 y R30 al incrustar `{prompt_fase_1}`, sin copia propia.
- **R29.** El prompt de fase 1 debe indicar que portes, bombeo, recargos,
  excesos y demás complementos sin código propio llevan el de la línea base a
  la que acompañan y no van a almacén (excepción (c)).
- **R30.** El prompt de fase 1 debe indicar que, CUANDO hay código de documento
  y además códigos de línea, cada línea marcada lleva el suyo y las demás el de
  documento (D9).

## sv6 — la valoración no inventa partida

- **R1.** CUANDO sv6 valora una línea base `from_albaran` sin
  `codigo_partida_albaran`, el sistema debe resolver
  `codigo_partida_final = NULL`, `partida_action = "almacen_sin_partida"` y
  añadir la razón `"almacen_sin_partida_en_albaran"`, en lugar de copiar la
  partida de la línea de contrato que casó la IA.
- **R2.** MIENTRAS una línea esté en el caso de R1 y la IA haya casado una
  línea de contrato, el sistema debe conservar ese `matched_contrato_line_id` y
  el precio final: el almacén cambia la imputación, nunca la valoración.
- **R3.** CUANDO una línea del caso de R1 no tiene match de la IA, el sistema
  debe crear la derivada de respaldo (`origen = "nueva_no_match"`,
  `codigo_partida = NULL`) conservando `partida_action = "almacen_sin_partida"`.
- **R4.** SI una línea del caso de R1 es de familia destinada, ENTONCES sv6 debe
  marcarla `review_required` con la razón `"partida_ausente_familia_destinada"`
  sin rellenar partida: sigue en almacén (D2: aviso no bloqueante).
- **R5.** MIENTRAS la línea sea de familia NO destinada (o sin familia), sv6
  NO debe marcar revisión por la ausencia de partida.
- **R6 (regresión).** CUANDO la línea trae `codigo_partida_albaran`, el sistema
  debe comportarse exactamente como hoy, incluido el literal impreso «ALM»
  (`alm_new_line_created`, derivada `alm_acopio`).
- **R7 (regresión).** Complementarias declaradas (`rol_linea` ≠ base con
  `ref_linea_base`) y sintéticas deben seguir heredando la partida final de su
  base (`inherited_from_base_line`): la de la base aunque ellas no traigan
  partida (excepción (c)), y `NULL` si la base está en almacén.
- **R8 (interruptor).** DONDE `ALMACEN_SIN_PARTIDA_ENABLED=false` (por defecto
  `true`), el sistema debe valorar exactamente como antes de F-051.
- **R9.** sv6 debe leer `FAMILIAS_DESTINADAS` como CSV sin distinguir
  mayúsculas ni espacios; vacío = «ninguna destinada».
- **R28.** MIENTRAS otra línea base del mismo albarán tenga partida, sv6 debe
  tratar la línea sin `codigo_partida_albaran` según R1: nunca le copia la de
  sus hermanas (qué línea lleva qué partida lo decide IA1).

## sv4 — pintar, elegir y asignar almacén

- **R10.** El sistema debe clasificar el estado de partida de cada línea con
  valoración con una función pura en dos valores, sin mirar `partida_action`:
  `partida` (código final no vacío) y `almacen` (vacío o solo espacios) (D1).
- **R11.** MIENTRAS una línea esté en almacén, toda vista de la ficha que pinte
  su partida (fila salmón —placeholder en editables, texto en solo lectura— y
  tabla de líneas valoradas) debe mostrar «Almacén» y NUNCA la partida de la
  línea de contrato casada ni la leída por IA1.
- **R12.** CUANDO el revisor guarda vacía la partida de una línea del albarán con
  partida, el sistema debe tratarlo como elegir «Almacén» (R14, R15), sin derivada.
- **R13.** CUANDO el revisor abre el desplegable de partida de cualquier línea
  editable, debe ofrecer como PRIMERA opción «Almacén (sin partida)», haya o no
  contrato, obra o líneas de contrato, y sea cual sea el texto del filtro.
- **R14.** CUANDO el revisor elige «Almacén» en una línea, el sistema debe
  persistir en su valoración `codigo_partida_final = NULL` y `partida_action =
  "almacen_elegido"`, sin tocar cantidad, precio, importe, descuento ni revisión.
- **R15.** CUANDO se asigna almacén a una línea casada con una línea de
  contrato de Sigrid, el sistema debe CONSERVAR `matched_contrato_line_id`
  (la fila sigue siendo «Sigrid», no pasa a «Nueva»).
- **R16.** CUANDO el revisor pulsa «Almacén a todas las líneas» y confirma, el
  sistema debe aplicar R14 y R15 a TODAS las líneas de valoración del documento
  (base, complementarias y sintéticas), también a las que tenían partida, en
  una sola transacción.
- **R17.** ANTES de aplicar R16, la ficha debe pedir confirmación indicando
  cuántas líneas perderán su partida.
- **R18.** CUANDO se aplica R14 o R16, el sistema debe registrar UNA entrada
  en `undo_log` que restaure el estado anterior de todas las líneas tocadas.
- **R19.** CUANDO el revisor guarda otros campos (cantidad, descuento…) de una
  línea en almacén sin tocar la partida, el sistema debe mantenerla en almacén
  y NO convertir una fila Sigrid en «Nueva».
- **R20.** CUANDO el revisor asigna una partida real a una línea en almacén,
  la línea debe dejar de estar en almacén; si coincide con la de su línea de
  contrato casada, la fila sigue siendo Sigrid.
- **R21.** El cálculo de confianza de sv4 debe puntuar la partida de una línea
  en almacén como resuelta (factor 1), tenga o no marca; una línea sin
  valoración sigue puntuando 0 como hoy.
- **R22.** SI la vista no es editable (`document.is_editable` falso) o la
  línea no tiene valoración, ENTONCES la ficha no debe ofrecer ni la opción ni
  el botón (misma regla que las demás ediciones de la fila salmón).
- **R23.** SI la petición de almacén nombra una línea ajena al documento,
  ENTONCES el sistema debe rechazarla sin modificar nada.

## Contrato hacia Sigrid (se documenta; lo implementa F-053)

- **R24.** El sistema debe documentar (`docs/ARCHITECTURE.md`, semántica de
  dominio) que una línea en almacén va a Sigrid sin partida y con almacén (F-053,
  `almacen: true` de F-009 de sigrid-api), que nadie la rellena desde el
  contrato, la plantilla ni otra línea, y que toda partida final vacía es almacén.

## Trazabilidad requisito → test

| R | Test previsto (unit, sin red ni BBDD) |
|---|---|
| R25–R27, R29, R30 | `test_f051_r25_*`…`_r30_*` sobre el texto real de `prompts.yaml` e instructions renderizadas (patrón `test_f043_prompt_fase1.py`) + evals (T21) + MANUAL (T23) |
| R1–R3 | `test_f051_r1_*`…`_r3_*` sobre `PartidaMatcher` y el builder de sv6 |
| R4, R5, R9 | `test_f051_r4_*`, `_r5_*`, `_r9_*` (política pura + builder) |
| R6–R8, R28 | `test_f051_r6_*`…`_r8_*`, `_r28_*` (no regresión: impresa, ALM, herencia, hermanas, interruptor apagado) |
| R10, R18, R21 | `test_f051_r10_*`, `_r18_*`, `_r21_*` puros en sv4 o del servicio con repositorio falso |
| R11 | `test_f051_r11_*` montaje del detalle y plantilla con repositorio falso + MANUAL navegador |
| R13 | `test_f051_r13_*`: el JS servido contiene la opción fija + MANUAL navegador |
| R12, R14–R16, R19, R20, R23 | `test_f051_r14_*`… con la sesión SQL simulada (SQL emitido y parámetros) |
| R17, R22 | `test_f051_r17_*` (recuento servido), `_r22_*` (plantilla con `is_editable` falso) + MANUAL navegador |
| R24 | revisión del reviewer (los docs dicen lo que hace el código) |
