<!-- specs/F-006-residuos-pago/requirements.md -->
# F-006 · Tanda 4b — Residuos: lógica de pago LLEVAR/RETIRAR y canon

Fuente normativa: `docs/referencia/dominio_negocio_albaranes.md` §9.4 y §10.6
(reglas 🔶). La LECTURA de residuos (LER, volumen/peso por etiqueta,
llevadas/retiradas separadas, cálculo de contenedores) ya está entregada y
**NO se re-especifica aquí**: esta feature es solo la lógica de PAGO.

Vocabulario: LLEVAR/ENTREGAR = el gestor deja un contenedor (vacío) en obra.
RETIRAR = el gestor se lleva un contenedor (lleno) al vertedero. Señales
disponibles por línea: `contexto_linea.contenedores_entregados`,
`contexto_linea.contenedores_retirados` (ya capturados por IA2) y el léxico
de la descripción de la línea.

## Clasificación del movimiento (determinista, sv6)

- **R1.** CUANDO sv6 procese una línea con `contexto_linea.tipo_familia ==
  'residuos'`, el sistema debe clasificarla en uno de tres movimientos con
  señales deterministas y en este orden de precedencia:
  1. **RETIRAR** si `contenedores_retirados >= 1` O la descripción de la
     línea (albarán o contrato casado) contiene léxico de retirada
     (RETIRADA/RETIRAR, RECOGIDA, CAMBIO — un cambio incluye una retirada).
  2. **LLEVAR** si (sin señal de retirar) `contenedores_entregados >= 1` O
     la descripción contiene léxico de entrega (ENTREGA, LLEVADA,
     COLOCACIÓN, ALQUILER DE CONTENEDOR no; solo entrega física).
  3. **SIN_SENAL** en cualquier otro caso.

- **R2.** MIENTRAS una línea de residuos esté clasificada SIN_SENAL y traiga
  material (código LER, o `volumen_m3`/`peso_toneladas` > 0), el sistema
  debe tratarla como RETIRAR (el residuo salió de la obra: comportamiento
  facturable actual; no se degrada nada ya entregado).

## Solo LLEVAR ⇒ no se paga y no entra en Sigrid

- **R3.** CUANDO una línea de residuos quede clasificada LLEVAR, el sistema
  debe marcarla NO FACTURABLE: `no_facturable = true`,
  `importe_calculado = 0`, y añadir la razón
  `residuos_solo_llevar_no_facturable` a `review_reasons` (sin forzar
  `review_required` por sí sola: la decisión es determinista).

- **R4.** MIENTRAS una línea de residuos esté clasificada LLEVAR, el sistema
  NO debe aplicarle la regla `movimiento_residuos_sin_cantidad_asumido_1`
  (esa regla asume 1 movimiento FACTURABLE) ni generarle línea de canon.

- **R5.** El sistema debe persistir la marca en una columna nueva
  `albaran_line_valuations.no_facturable BOOLEAN NOT NULL DEFAULT FALSE`
  (sv6, dueño de la tabla, vía `ADD COLUMN IF NOT EXISTS`), de forma que el
  futuro consumidor de `q-feedback` (entrada al ERP, aún no construido)
  pueda excluir esas líneas de Sigrid. Ver Pregunta abierta P1 en design.md.

## RETIRAR ⇒ porte + canon

- **R6.** CUANDO una línea RETIRAR tenga a la vez `contenedores_entregados`
  y `contenedores_retirados` informados (ambos ⇒ solo cuenta RETIRAR), el
  número de contenedores facturables debe ser `contenedores_retirados`
  (las llevadas no suman ni restan), sustituyendo a la resta
  llevadas−retiradas de la prioridad 2 del cálculo entregado. El número
  EXPLÍCITO impreso (`contexto_linea.contenedores`, prioridad 1) sigue
  prevaleciendo sobre todo. Ver Pregunta abierta P2 en design.md.

- **R7.** CUANDO la valoración contenga al menos una línea RETIRAR
  facturable, el sistema debe incluir por cada una UNA línea sintética de
  CANON DE VERTEDERO con: `line_kind='synthetic_modifier'`,
  `modifier_source='canon_vertedero'`, `rol_linea='canon_vertedero'`,
  `parent_merge_line_id` = la línea de retirada, y casada
  (`matched_contrato_line_id`) con la línea CANON del contrato cuyo tipo de
  residuo corresponda al de la línea base (LER/descripcion).

- **R8.** El sistema debe fijar la partida de la línea de canon desde el
  RECURSO del contrato casado: `codigo_partida_final` = `codigo_partida` de
  la línea CANON del contrato (`partida_action='existing_matched'`). El
  sistema NUNCA debe inventar la partida ni copiarla de una línea de otro
  capítulo aunque se parezca (caso real 16.01 vs 15.01).

- **R9.** El sistema debe calcular la cantidad del canon según la categoría
  de unidad de la línea CANON del contrato: volumen (m³) →
  `contexto_linea.volumen_m3`; masa (Tn) → `contexto_linea.peso_toneladas`;
  unidades/contenedor → el número de contenedores facturables de la línea
  base. SI la magnitud requerida no viene en el albarán, ENTONCES el sistema
  debe dejar la cantidad a null y marcar la línea de canon a revisión con
  razón `canon_sin_magnitud`.

- **R10.** SI existe una línea RETIRAR facturable y NO se localiza línea
  CANON casable en el contrato (ni la emitió IA3 ni la encuentra la red
  determinista), ENTONCES el sistema debe marcar la línea de retirada a
  revisión (`review_required=true`) con razón
  `canon_vertedero_no_encontrado`, sin inventar precio ni partida ni
  crear línea derivada.

- **R11.** CUANDO IA3 ya haya emitido la sintética de canon para una línea
  de retirada, la red determinista de sv6 NO debe duplicarla (dedupe por
  `parent_merge_line_id` + `modifier_source='canon_vertedero'`, mismo
  patrón que la red M1 de años).

## Prompt de sv5 (valuation_residuos)

- **R12.** El prompt `valuation_residuos` de sv5 debe instruir: (a) citar
  en `razon_corta` las señales llevar/retirar de cada línea; (b) emitir la
  ÚNICA sintética permitida en residuos: la línea de canon
  (`modifier_source='canon_vertedero'`) por cada línea de retirada, casada
  con la línea CANON del contrato del tipo de residuo; (c) mantener la
  prohibición del resto de sintéticas (M1–M7 son de hormigón); (d) no
  calcular importes, no elegir partida, no inventar precios.

- **R13.** El schema Pydantic de sv5 (`ModifierSource`) debe aceptar el
  valor `'canon_vertedero'` y rechazar valores no listados (comportamiento
  Literal actual).

## Aislamiento y no-regresión

- **R14.** MIENTRAS una línea NO sea `tipo_familia='residuos'`, el sistema
  debe valorarla exactamente igual que antes de esta feature (las redes
  nuevas no se ejecutan; tests de regresión sobre hormigón/genérico).

- **R15.** DONDE el documento sea residuos con TODAS sus líneas LLEVAR, el
  sistema debe producir una valoración persistida con todas las líneas
  `no_facturable=true`, `total_valorado = 0` y sin líneas de canon.

## Puerta de rutas sensibles (F-011)

- **R16.** CUANDO se modifique el prompt `valuation_residuos`, el ground
  truth de evals de residuos (contrato de datos en `evals/`, pestaña de
  residuos de IA3) debe actualizarse con los casos LLEVAR / RETIRAR /
  ambos / canon. Verificación MANUAL (humano): F-011 aún no está
  implementada; se deja el dato preparado para su runner.

Regla de oro: R1–R11 y R13–R15 se verifican con unit tests sin red ni BBDD
(fixtures de envelope y de líneas de contrato). R12 se verifica con un test
que carga el YAML real y comprueba las instrucciones clave. R16 es manual.
