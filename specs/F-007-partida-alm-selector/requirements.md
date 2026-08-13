<!-- specs/F-007-partida-alm-selector/requirements.md -->
# F-007 · Tanda 5 — Partida ALM por defecto y selector de candidatas en sv4 · Requisitos

Fuente normativa: `docs/referencia/dominio_negocio_albaranes.md` §10.8
(marcas 🔶). Dos bloques: la regla ALM por defecto vive en **sv6**
(`services/albaran-valoracion-persist`); el selector de candidatas y la
memoria obra+producto viven en **sv4** (`services/albaranes-front`).

Vocabulario usado aquí:

- **Familia destinada**: familia cuyo coste SÍ se destina a una partida a la
  entrada. Conjunto configurable `FAMILIAS_DESTINADAS`, por defecto
  `{hormigon, mortero, combustible, alquiler_maquinaria, residuos}`
  (indirectos y familias con regla de partida propia).
- **Suministro no destinado**: línea base `from_albaran` cuyo
  `contexto_linea` es nulo o tiene `tipo_familia = "otro"` (tipología
  «Genérico / Suministros», §9.1). Confirmado por el humano el 2026-08-13
  (Decisión D1 del design).
- **Estado «almacén»**: decidido por el humano (2026-08-13): **ALM NO es un
  código de partida real** — «ir a ALM» y «no tener código de partida» son
  lo mismo. Internamente se representa como `codigo_partida_final = NULL` +
  `partida_action` de almacén (`alm_default` o `alm_new_line_created`); en
  la vista de sv4 se muestra «Almacén»; al escribir en Sigrid (futura
  F-013) la partida irá EN BLANCO. El literal `ALM_CODIGO_PARTIDA` (config
  sv6, default `"ALM"`) es SOLO el texto impreso en el papel que sv6
  reconoce, jamás un valor persistido hacia Sigrid.
- **producto_clave**: descripción del recurso normalizada (mayúsculas, sin
  acentos, espacios colapsados, máx. 255), R13.

## sv6 — regla «partida ALM por defecto» (suministros no se destinan)

- **R1 (regresión).** El sistema debe conservar el comportamiento actual
  cuando la línea trae `codigo_partida_albaran` impreso: la partida del
  papel manda (§10.8 ✅), incluido el caso en que el papel imprime el
  literal ALM (`partida_action = "alm_new_line_created"`, derivada
  `origen = "alm_acopio"`, `codigo_partida_final = None`).
- **R2.** CUANDO sv6 valora una línea base `from_albaran` SIN
  `codigo_partida_albaran` y la línea es un suministro no destinado, el
  sistema debe resolver `codigo_partida_final = NULL` con el nuevo
  `partida_action = "alm_default"` y añadir la razón auditable
  `"alm_default_suministro_no_destinado"` al resultado del matcher (estado
  «almacén»: sin código de partida; la marca es el `partida_action`).
- **R3.** El sistema debe conservar, en una línea resuelta `alm_default`
  que SÍ tiene match de IA contra el contrato, el
  `matched_contrato_line_id` y el precio final calculado: la regla ALM
  cambia solo la imputación (partida), nunca la valoración económica.
- **R4.** CUANDO una línea de suministro no destinado sin partida impresa
  tampoco tiene match de IA, el sistema debe crear la línea derivada de
  respaldo (`origen = "nueva_no_match"`, `codigo_partida = NULL`)
  CONSERVANDO `partida_action = "alm_default"` en la línea de valoración
  (el fallback no debe pisar la marca de almacén).
- **R5.** MIENTRAS la línea pertenezca a una familia destinada
  (`tipo_familia` ∈ `FAMILIAS_DESTINADAS`), el sistema debe aplicar el
  matching de partida actual SIN la regla ALM por defecto (los indirectos
  SÍ se destinan a la entrada, §10.8; residuos ya tiene regla propia §10.6;
  hormigón/mortero se destinan con elección humana, R8–R10).
- **R6.** El sistema debe hacer que las líneas complementarias
  (`rol_linea != 'base'`) y las sintéticas hereden la partida final de su
  línea base también cuando la base resolvió `alm_default` (heredan
  `codigo_partida_final = NULL` con
  `partida_action = "inherited_from_base_line"` — comportamiento que ya
  existe hoy para base sin partida; solo se fija con test).
- **R7 (kill-switch).** DONDE `ALM_DEFAULT_ENABLED=false` (config nueva,
  por defecto `true`), el sistema debe comportarse exactamente como antes
  de esta feature (ningún `alm_default` emitido).

## sv4 — selector de partidas candidatas + memoria obra+producto

- **R8.** CUANDO el revisor abre el combo de partida de una línea salmón
  cuya descripción coincide (normalizada según R13) con líneas del
  contrato presentes en MÁS de una partida (clones de los contratos de
  hormigón), el combo debe mostrar primero un grupo «Candidatas (mismo
  recurso)» con exactamente esas partidas, antes de la lista general de
  partidas ya existente.
- **R9.** CUANDO el documento tiene `obra_codigo`, existe memoria para
  `(obra_codigo, producto_clave)` y la línea no tiene partida destinada
  (partida vacía/NULL, incluido el estado «almacén»), el detalle del
  documento debe exponer esa partida como `partida_sugerida` y el combo
  debe prerrellenarla como sugerencia visualmente marcada; el sistema NO
  debe persistirla sin acción humana explícita de guardado (la elección es
  humana, §10.8).
- **R10.** CUANDO el revisor destina una línea a una partida real (no
  vacía) por CUALQUIERA de los cuatro caminos existentes — (a) edición del
  campo partida de la fila salmón, (b) selección de línea de contrato en
  la fila salmón, (c) «+ a Sigrid» de una línea del albarán con línea de
  contrato (`mode=contract_line`), (d) «Traer líneas de contrato»
  (multiselección) —, el sistema debe upsertar
  `partida_memoria(obra_codigo, producto_clave) → codigo_partida`, con
  instante UTC y autor si se conoce. (Ampliación a los caminos (c) y (d)
  confirmada por el humano el 2026-08-13.)
- **R11.** SI la lectura o escritura de `partida_memoria` falla, ENTONCES
  el sistema debe completar igualmente la operación principal (cargar el
  detalle / guardar la línea) y registrar el fallo en el log (la memoria
  es best-effort, nunca bloquea la revisión).
- **R12.** SI el documento no tiene `obra_codigo` o la línea no produce
  `producto_clave` normalizable (sin descripción), ENTONCES el sistema no
  debe leer ni escribir memoria para esa línea.
- **R13.** El sistema debe normalizar `producto_clave` de forma
  determinista: mayúsculas, sin acentos (NFKD sin combinantes), espacios
  colapsados a uno, recorte a 255 caracteres; entradas `None` o en blanco
  producen `None`. Misma entrada ⇒ misma clave (es la misma normalización
  que usa `PartidaMatcher._normalize_desc` en sv6).
- **R14.** El sistema debe crear la tabla `partida_memoria` con DDL
  idempotente (`CREATE TABLE IF NOT EXISTS` + índices `IF NOT EXISTS`)
  dentro del `initialize()` de sv4, ejecutable N veces sin error.
- **R15.** MIENTRAS una línea salmón tenga `partida_action` de almacén
  (`alm_default` o `alm_new_line_created`) y el revisor no la haya
  destinado, la vista de sv4 debe mostrar «Almacén» en la columna partida
  — nunca la celda en blanco ni la partida de la línea de contrato casada
  resucitada por el fallback actual (que rellena con la partida del
  contrato cuando `codigo_partida_final` es NULL).

## Trazabilidad requisito → test

| R | Test previsto (sin red ni BBDD salvo indicación) |
|---|---|
| R1 | `test_f007_r1_*` unit de `PartidaMatcher` (partida impresa y ALM impreso, sin cambios) |
| R2 | `test_f007_r2_*` unit de `PartidaMatcher.match` con flag suministro |
| R3 | `test_f007_r3_*` unit (match IA conservado + precio intacto en builder) |
| R4 | `test_f007_r4_*` unit del fallback `nueva_no_match` del builder (conserva `partida_action="alm_default"`) |
| R5 | `test_f007_r5_*` unit del cálculo de flag en builder por familia |
| R6 | `test_f007_r6_*` unit herencia complementaria/sintética con base ALM |
| R7 | `test_f007_r7_*` unit con `alm_default_enabled=False` |
| R8 | `test_f007_r8_*` unit JS no hay: se testea el dato servido (candidatas derivables del JSON de líneas de contrato ya embebido) + verificación MANUAL en navegador |
| R9 | `test_f007_r9_*` unit de servicio con repositorio fake (sugerencia expuesta, no persistida) |
| R10 | `test_f007_r10_*` unit de la decisión de memorizar (qué se memoriza y qué no) con repositorio fake, cubriendo los cuatro caminos (a)–(d) |
| R11 | `test_f007_r11_*` unit: el fake lanza excepción y la operación principal termina OK |
| R12 | `test_f007_r12_*` unit (sin obra / sin descripción ⇒ no-op) |
| R13 | `test_f007_r13_*` unit puro del normalizador |
| R14 | `test_f007_r14_*` unit textual del DDL (contiene `IF NOT EXISTS`) + verificación MANUAL contra PG local (arrancar sv4 dos veces) |
| R15 | `test_f007_r15_*` unit del montaje del detalle (línea con `partida_action` de almacén ⇒ etiqueta «Almacén», sin fallback a la partida del contrato) + verificación MANUAL en navegador |
