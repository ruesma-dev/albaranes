<!-- specs/F-006-residuos-pago/requirements.md -->
# F-006 · Tanda 4b — Residuos: lógica de pago LLEVAR/RETIRAR y canon

Fuente normativa: `docs/referencia/dominio_negocio_albaranes.md` §9.4 y §10.6
(reglas 🔶). La LECTURA de residuos (LER, volumen/peso por etiqueta,
llevadas/retiradas separadas, cálculo de contenedores) ya está entregada y
**NO se re-especifica aquí**: esta feature es solo la lógica de PAGO.
Las decisiones del humano (2026-08-13) sobre las preguntas abiertas de la
primera versión están incorporadas; ver «Decisiones tomadas» en design.md.

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
     Con señales de llevar Y retirar a la vez, la línea es RETIRAR
     («ambos ⇒ solo cuenta RETIRAR»: se paga como retirada).
  2. **LLEVAR** si (sin señal de retirar) `contenedores_entregados >= 1` O
     la descripción contiene léxico de entrega (ENTREGA, LLEVADA,
     COLOCACIÓN; solo entrega física).
  3. **SIN_SENAL** en cualquier otro caso.

- **R2.** MIENTRAS una línea de residuos esté clasificada SIN_SENAL y traiga
  material (código LER, o `volumen_m3`/`peso_toneladas` > 0), el sistema
  debe tratarla como RETIRAR (el residuo salió de la obra: comportamiento
  facturable actual; no se degrada nada ya entregado).

## Solo LLEVAR ⇒ no se paga y no se registra en Sigrid

- **R3.** CUANDO una línea de residuos quede clasificada LLEVAR, el sistema
  debe marcarla como NO REGISTRABLE en Sigrid: `no_registrar_sigrid = true`,
  `importe_calculado = 0`, y añadir la razón
  `residuos_solo_llevar_no_registrar_sigrid` a `review_reasons` (sin forzar
  `review_required` por sí sola: la decisión es determinista).

- **R4.** MIENTRAS una línea de residuos esté clasificada LLEVAR, el sistema
  NO debe aplicarle la regla `movimiento_residuos_sin_cantidad_asumido_1`
  (esa regla asume 1 movimiento FACTURABLE) ni contarla para el canon.

- **R5.** El sistema debe persistir la marca en una columna nueva
  `albaran_line_valuations.no_registrar_sigrid BOOLEAN NOT NULL DEFAULT
  FALSE` (sv6, dueño de la tabla, vía `ADD COLUMN IF NOT EXISTS`). Su
  consumidor futuro es **F-013** (registro del albarán en Sigrid,
  consumidor de `q-feedback`): esas líneas no se registran en el albarán de
  Sigrid. Semántica del nombre: los albaranes no «facturan»; la línea
  simplemente no se registra en Sigrid.

## RETIRAR ⇒ porte + canon

- **R6.** CUANDO una línea RETIRAR se valore, el número de contenedores debe
  seguir el cálculo YA ENTREGADO sin cambios (`residuos_container_calc`):
  prioridad 1 número explícito (`contexto_linea.contenedores`); prioridad 2
  resta `contenedores_entregados − contenedores_retirados` si ambos vienen y
  la resta es ≥ 1 (dirección confirmada por el humano: la del código; la
  redacción inversa de §10.6 era una errata, ya anotada en
  `docs/referencia`); prioridad 3 `ceil(volumen/tamaño)`. La regla «ambos ⇒
  solo cuenta RETIRAR» actúa en la CLASIFICACIÓN (R1: la línea es RETIRAR y
  se paga), NO en la cantidad. Ejemplo confirmado: llevadas 3 / retiradas 1
  → se facturan 2 contenedores.

- **R7.** CUANDO la valoración contenga al menos una línea RETIRAR
  facturable, el sistema debe incluir **UNA única** línea sintética de CANON
  DE VERTEDERO **por albarán** (no por línea de retirada) con:
  `line_kind='synthetic_modifier'`, `modifier_source='canon_vertedero'`,
  `rol_linea='canon_vertedero'`, `parent_merge_line_id` = la PRIMERA línea
  de retirada del albarán (orden de líneas), y casada
  (`matched_contrato_line_id`) con la línea CANON del contrato cuyo tipo de
  residuo corresponda al de las retiradas (LER/descripcion).

- **R8.** El sistema debe fijar la partida de la línea de canon POR HERENCIA
  de la primera línea de retirada (su `codigo_partida_final`, que a su vez
  procede del recurso del contrato; `partida_action=
  'inherited_from_base_line'`). SI la línea CANON del contrato casada
  declara una partida DISTINTA de la heredada, ENTONCES la línea de canon
  debe ir a revisión con razón `canon_partida_discrepante`. El sistema NUNCA
  debe inventar la partida (caso real 16.01 vs 15.01).

- **R9.** El sistema debe calcular SIEMPRE de forma determinista (aunque
  IA3 emita otra cosa) la cantidad del canon, AGREGADA sobre todas las
  líneas RETIRAR facturables del albarán, según la categoría de unidad de
  la línea CANON del contrato: volumen (m³) → suma de
  `contexto_linea.volumen_m3`; masa (Tn) → suma de
  `contexto_linea.peso_toneladas`; unidades/contenedor → suma de los
  contenedores calculados (R6). SI alguna retirada no aporta la magnitud
  requerida, ENTONCES la cantidad queda a null y la línea de canon va a
  revisión con razón `canon_sin_magnitud`.

- **R10.** SI existe una línea RETIRAR facturable y NO se localiza línea
  CANON casable en el contrato (ni la emitió IA3 ni la encuentra la red
  determinista), ENTONCES el sistema debe marcar la primera línea de
  retirada a revisión (`review_required=true`) con razón
  `canon_vertedero_no_encontrado`, sin inventar precio ni partida ni crear
  línea derivada.

- **R11.** CUANDO IA3 ya haya emitido sintética(s) de canon, la red
  determinista de sv6 NO debe añadir otra; y SI IA3 emitiera más de una, el
  sistema debe conservar solo la primera (la cantidad la recalcula sv6
  igualmente, R9) anotándolo en `review_reasons`
  (`canon_duplicado_descartado`).

## Prompt de sv5 (valuation_residuos)

- **R12.** El prompt `valuation_residuos` de sv5 debe instruir: (a) citar
  en `razon_corta` las señales llevar/retirar de cada línea; (b) emitir la
  ÚNICA sintética permitida en residuos: UNA línea de canon POR ALBARÁN
  (`modifier_source='canon_vertedero'`, parent = primera retirada) cuando
  haya retiradas, casada con la línea CANON del contrato del tipo de
  residuo; (c) mantener la prohibición del resto de sintéticas (M1–M7 son
  de hormigón); (d) no calcular importes ni cantidades del canon, no elegir
  partida, no inventar precios.

- **R13.** El schema Pydantic de sv5 (`ModifierSource`) debe aceptar el
  valor `'canon_vertedero'` y rechazar valores no listados (comportamiento
  Literal actual).

## Front de revisión (sv4)

- **R17.** CUANDO el revisor abra el detalle de un documento en sv4, toda
  línea de valoración con `no_registrar_sigrid = true` debe mostrar una
  etiqueta visible en la propia línea (texto «No se registra en Sigrid»),
  sin permitir editar la marca desde la UI en esta feature.

## Aislamiento y no-regresión

- **R14.** MIENTRAS una línea NO sea `tipo_familia='residuos'`, el sistema
  debe valorarla exactamente igual que antes de esta feature (las redes
  nuevas no se ejecutan; tests de regresión sobre hormigón/genérico).

- **R15.** DONDE el documento sea residuos con TODAS sus líneas LLEVAR, el
  sistema debe producir una valoración persistida con todas las líneas
  `no_registrar_sigrid=true`, `total_valorado = 0` y sin línea de canon.

## Puerta de rutas sensibles (F-011)

- **R16.** CUANDO se modifique el prompt `valuation_residuos`, el ground
  truth de evals de residuos (contrato de datos en `evals/`, pestaña de
  residuos de IA3) debe actualizarse con los casos LLEVAR / RETIRAR /
  ambos / canon. Verificación MANUAL (humano): F-011 aún no está
  implementada; se deja el dato preparado para su runner.

Regla de oro: R1–R11 y R13–R15 se verifican con unit tests sin red ni BBDD
(fixtures de envelope y de líneas de contrato). R12 se verifica con un test
que carga el YAML real y comprueba las instrucciones clave. R17 se verifica
con test unitario del mapeo del campo en sv4 (fixture de fila, sin BBDD)
más comprobación visual manual. R16 es manual.
