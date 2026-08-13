<!-- specs/F-004-hormigon-fino/requirements.md -->
# F-004 · Tanda 3 — Hormigón fino y veto de mortero · Requisitos

Notación EARS. Cada requisito se traduce a >= 1 test con nombre trazable
(`test_f004_rN_...`). Los unit tests NO tocan red ni BBDD: se trabaja con
envelopes/DTOs construidos en el propio test (fixtures) y con lectura del
YAML de prompts como fichero local.

Normativa de referencia: `docs/referencia/dominio_negocio_albaranes.md`
§10.2 (reglas 🔶 de hormigón) y §10.3 (mortero D-*), y
`docs/ARCHITECTURE.md` (reglas 10, 11 y 12 de semántica de dominio).

Vocabulario: «sintética» = línea `line_kind='synthetic_modifier'` (M1–M9);
«base» = la línea del albarán de la que cuelga (`parent_merge_line_id`);
«partida de la base» = `codigo_partida_final` del record ya resuelto de esa
base; «tarifa en tabla» = línea de `lineas_contrato` del envelope.

## A — Re-apuntado determinista de incrementos (sv6, builder)

- **R1.** CUANDO el builder procesa una sintética cuyo
  `matched_contrato_line_id` apunta a una línea de contrato de OTRA partida
  distinta de la partida de la base, el sistema debe buscar primero la
  línea de contrato equivalente al modificador (predicado por `rol_linea`
  del `ModifierContractMatcher`) DENTRO de la partida de la base; si
  existe, debe re-apuntar el match a esa línea (esa pasa a ser
  `matched_contrato_line_id`, su precio pasa a ser el precio 1a que entra
  en la reconciliación) y NO debe crearse línea derivada.

- **R2.** CUANDO el builder procesa una sintética SIN match de contrato
  (`matched_contrato_line_id = null`) y la partida de la base está
  resuelta, el sistema debe intentar el mismo macheo determinista dentro de
  la partida de la base antes de caer a la derivada `nueva_no_match`; si
  existe la línea de incremento, debe casarla (sin derivada).

- **R3.** SI la partida de la base tiene líneas de contrato pero NINGUNA
  casa con el modificador, ENTONCES el sistema debe aplicar el fallback
  cross-partida SOLO cuando el precio del modificador sea uniforme en todo
  el contrato (política ya escrita en `ModifierContractMatcher`, con
  `requires_review=true`); y si tampoco hay match cross-partida, derivar
  línea nueva como hasta ahora. Es decir: **solo se deriva si el incremento
  de verdad no existe en el contrato**.

- **R4.** CUANDO el re-apuntado casa una sintética de
  `rol_linea='incremento_tiempo'`, el sistema debe marcar la línea
  `review_required=true` (la condición de aplicación del exceso no es
  verificable por el matcher), con el motivo que ya emite el matcher
  (`modifier_time_condition_needs_manual_check`).

- **R5.** CUANDO la sintética es de `rol_linea='incremento_year'`, el
  re-apuntado solo puede casar con una línea de contrato cuya descripción
  contenga ESE año (predicado existente del matcher), y el guard
  determinista de año (`_sanear_matches_incremento_year`) debe seguir
  ejecutándose sobre el resultado final: un incremento de año jamás queda
  casado con la tarifa de otro año (test de regresión del caso Horpresol).

- **R6.** DONDE `MODIFIER_TABLE_MATCH_ENABLED=false` (flag ya existente en
  settings de sv6), el sistema debe comportarse exactamente como antes de
  esta feature (sin re-apuntado; la sintética deriva o mantiene el match de
  la IA tal cual).

## B — La partida de un incremento existe en el contrato (o ALM/None)

- **R7.** CUANDO el builder resuelve una sintética cuya partida heredada de
  la base NO existe entre las `codigo_partida` de las líneas del contrato
  del envelope (comparación normalizada), el sistema debe persistir la
  sintética con `codigo_partida_final = null` (y su línea derivada, si la
  hay, con `codigo_partida = null`), `review_required = true` y motivo
  `modifier_partida_not_in_contract:<partida>` en `review_reasons`. Jamás
  debe persistirse un incremento con un literal de partida que no exista en
  el contrato.

- **R8.** CUANDO la base resolvió partida `null` (p. ej. base ALM/acopio),
  el sistema debe mantener el comportamiento actual para sus sintéticas
  (partida `null` heredada, sin motivo nuevo): test de regresión.

## C — Familia mortero (D-*) separada con veto determinista

- **R9.** CUANDO sv5 deriva la tipología de valoración y alguna línea trae
  `contexto_linea.tipo_familia='mortero'` sin que ninguna traiga
  `'residuos'` ni `'hormigon'`, el sistema debe derivar tipología
  `mortero` y elegir el prompt `valuation_mortero` (prioridad:
  residuos > hormigon > mortero > generico; el mecanismo
  `valuation_{tipologia}` ya existe).

- **R10.** El prompt `valuation_mortero` debe instruir que: (a) los códigos
  de mortero (familia D-*) NO siguen la nomenclatura posicional del
  hormigón y su tercer campo es RESISTENCIA, no árido; (b) el mortero solo
  lleva ARENA: está PROHIBIDO emitir sintéticas de árido, aditivo,
  plastificante, fibras o fratasado; (c) son admisibles el incremento de
  consistencia SOLO si el contrato lo tarifa de verdad (con tarifa real en
  tabla o PDF; sin tarifa NO se emite, a diferencia de la Forma C del
  hormigón) y el cemento especial si aparece en el documento; (d) M6/M7
  solo con señal explícita (mismas reglas D de abajo). *(Test: asserts de
  contenido sobre el YAML cargado con `YamlPromptRepository`.)*

- **R11.** CUANDO el builder de sv6 recibe sintéticas cuyo parent es una
  base con `contexto_linea.tipo_familia='mortero'`, el sistema debe
  ELIMINARLAS antes del build (no se persisten) si su rol es
  `incremento_arido` o `incremento_fratasado`, o si su rol es
  `incremento_aditivo` (cubre aditivo, plastificante y fibras), dejando log
  con el motivo. Este veto es determinista y actúa aunque el prompt ya lo
  prohíba (defensa en profundidad: la IA lo ha incumplido en un caso real,
  §9.3).

- **R12.** La red determinista de código de sv6
  (`_sinteticas_codigo_faltantes`) y la red M1 de años NO deben generar
  sintéticas para bases de familia `mortero` (hoy ya están limitadas a
  `tipo_familia='hormigon'`): test de regresión que lo fije.

- **R13.** CUANDO un documento mixto trae bases de hormigón Y de mortero
  (tipología derivada `hormigon`, prompt `valuation_es`), el prompt
  `valuation_es` debe indicar que para las bases con
  `tipo_familia='mortero'` NO se aplica la nomenclatura posicional ni se
  emiten las sintéticas prohibidas de R10(b); y el veto de R11 debe
  proteger igualmente esas bases en sv6 (el veto es por línea, no por
  documento).

- **R14.** CUANDO el re-apuntado (bloque A) actúa sobre una sintética cuya
  base es de familia `mortero`, el sistema debe restringir las candidatas a
  líneas de contrato cuya descripción contenga `MORTERO` (hoy el matcher
  hace lo inverso: las excluye por ser la base hormigón); sin candidata de
  mortero, sin match (conservador, a revisión).

- **R15.** DONDE `VETO_MORTERO_ENABLED=false` (flag nuevo, default `true`),
  el veto de R11 no debe actuar (comportamiento previo exacto).

## D — M6 (exceso de tiempo) y M7 (carga incompleta) solo con señal explícita

- **R16.** El prompt de sv5 (en `valuation_es` y `valuation_mortero`) debe
  emitir la sintética M6 SOLO cuando exista señal explícita de exceso en el
  documento: (a) exceso declarado (`exceso_declarado_min` o texto de exceso
  en `notas_tiempo`), o (b) horas explícitas del albarán + umbral explícito
  (del contrato o del albarán) cuyo cálculo dé exceso > 0. Deben eliminarse
  del prompt: la emisión «SIEMPRE, incluso con exceso=0» y la franquicia de
  60 min ASUMIDA sin política del contrato (punto 3 de M6.1). Cantidad 0
  sin texto de exceso → NO se emite. *(Regla 🔶 de §10.2.)*

- **R17.** El prompt de sv5 debe emitir la sintética M7 SOLO con señal en
  el documento: texto de carga incompleta (Condición A), cantidad impresa
  menor que el umbral tarifado del contrato (Condición B), o m³ no
  transportados con tarifa expresa (Condición C). El caso especial «texto
  de carga incompleta con cantidad ≥ umbral» se mantiene (emite con
  cantidad 0: HAY texto, deja trazabilidad). Sin tarifa de carga incompleta
  en el contrato sigue sin emitirse (regla actual).

- **R18.** CUANDO el builder de sv6 recibe una sintética
  `modifier_source='tiempo_exceso'` con `cantidad_override` nula o 0 y el
  contexto de su base NO trae `exceso_declarado_min`, el sistema debe
  eliminarla antes del build (guard determinista, defensa en profundidad
  del R16), con log.

- **R19.** CUANDO el builder de sv6 recibe una sintética
  `modifier_source='carga_incompleta'` con `cantidad_override` nula o 0 y
  el contexto de su base NO trae `carga_incompleta=true` ni
  `m3_no_transportados > 0`, el sistema debe eliminarla antes del build
  (guard determinista del R17), con log.

- **R20.** DONDE `M6M7_SENAL_GUARD_ENABLED=false` (flag nuevo, default
  `true`), los guards R18/R19 no deben actuar.

## Transversales

- **R21.** SI cualquiera de las piezas nuevas (re-apuntado, veto mortero,
  guards M6/M7, veto de partida) lanza una excepción inesperada, ENTONCES
  la valoración NO debe romperse de forma distinta a hoy: los vetos y
  guards se aplican dentro del build y cualquier fallo de datos se resuelve
  hacia el lado conservador (línea a revisión), nunca inventando precio o
  partida.

- **R22.** El schema Pydantic de sv5 (`documento_valoracion`) NO cambia en
  esta feature: no se añade ningún `modifier_source` ni rol nuevo (la regla
  de los 5 sitios de `docs/ARCHITECTURE.md` §10 no se dispara). Test de
  regresión: un envelope válido de antes de la feature sigue validando.

## Preguntas abiertas (validar por el humano ANTES de implementar)

- **P1 — M1 de años en mortero.** ¿Los incrementos por año aplican también
  a los contratos de mortero? Propuesta: sí (el incremento de año es del
  contrato, no del producto) y extender la red determinista M1 a bases
  `mortero`; pero §10.3 no lo dice y esta spec lo deja FUERA del alcance
  (la red M1 sigue solo-hormigón, R12) hasta respuesta. Si la respuesta es
  sí, se añade en esta misma feature (cambio pequeño: aflojar el filtro de
  familia de `_sinteticas_m1_faltantes` y permitir `incremento_year` en el
  prompt de mortero).
- **P2 — Condición B de M7 como «señal explícita».** La cantidad impresa
  menor que el umbral tarifado, ¿cuenta como señal del documento aunque no
  haya texto «CARGA INCOMPLETA»? La spec asume que SÍ (R17): la cantidad
  está impresa en el albarán y el contrato tarifa el mínimo. Confirmar.
- **P3 — Consistencia de mortero sin tarifa.** Se asume que en mortero la
  consistencia sin tarifa NO se emite (ni Forma C), R10(c). En hormigón la
  consistencia sin tarifa sigue emitiéndose a revisión (Forma C). Confirmar
  la asimetría.
- **P4 — M5 (gestión de residuos) en mortero.** ¿Se emite si el contrato
  de mortero la tarifa? La spec asume que sí (no está en la lista de vetos
  de §10.3). Confirmar.
