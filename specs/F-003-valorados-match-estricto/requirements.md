<!-- specs/F-003-valorados-match-estricto/requirements.md -->
# F-003 · Tanda 2 — Albaranes valorados, match estricto y coherencia (G3+G4+G5) · Requisitos

Notación EARS. Cada requisito se traduce a >= 1 test con nombre trazable
(`test_f003_rN_...`). Los unit tests NO tocan red ni BBDD: los servicios de
sv6 son funciones/clases puras y se testean con DTOs construidos a mano; los
prompts se testean por contenido del YAML cargado con el repositorio real.

Normativa de referencia: `docs/referencia/dominio_negocio_albaranes.md`
§10.4 (albaranes que VIENEN valorados) y §10.5 (matching albarán↔contrato),
y `docs/ARCHITECTURE.md` (reglas 11 y 12 del resumen operativo).

Vocabulario: «importe leído» = importe de línea impreso en el documento y
transcrito por su etiqueta de columna (nuevo campo, ver R2); «importe
efectivo» = el leído si existe, o el derivado actual (`cantidad ×
precio_neto`) como fallback de compatibilidad.

## G3 — Transcribir, no recomponer

- **R1.** El prompt de IA1 (`albaran_factura_es`, sv2) debe instruir que en
  albaranes con columnas de valoración cada valor se TRANSCRIBE por su
  etiqueta de columna: `precio` solo de la columna de precio unitario
  (PRECIO, P.U., PRECIO UNIT.); `descuentos` solo de las columnas de
  descuento (DTO, DTO%, DTO1/DTO2…); `importe` solo de la columna de importe
  de línea (IMPORTE, TOTAL, NETO); `precio_neto` SOLO si figura impreso como
  precio unitario neto. PROHIBIDO derivar cualquiera de ellos de los demás:
  la instrucción actual «si no, calcula cantidad*precio*(1 - descuento/100)»
  (config/prompts.yaml, regla de `precio_neto`) debe desaparecer. Si un
  valor no figura → null, nunca calculado. *(Causa raíz del caso ×120:
  23.073,60 € persistidos por 191,40 € impresos.)*

- **R2.** El schema de extracción de sv2 (`domain/models/albaran_models.py`)
  debe ganar: `LineaAlbaran.importe` (float opcional, importe de línea
  leído), `LineaAlbaran.descuentos` (lista opcional de porcentajes, en el
  orden de las columnas del documento) y `CabeceraAlbaran.importe_total`
  (float opcional: total del albarán SIN IVA — base imponible si el
  documento la distingue; si el único total impreso incluye IVA, null).
  `descuento` (existente) lo rellena la IA solo cuando hay UN único
  descuento; con varios lo deja null (lo deriva sv3, R3).

- **R3.** CUANDO sv3 persiste una extracción (raw y merge), el sistema debe
  guardar los campos nuevos en columnas propias (`importe` y
  `descuentos_json` en `albaran_lines`/`albaran_lines_merge`;
  `importe_total` en `albaran_documents`/`albaran_documents_merge`, DDL
  idempotente `ADD COLUMN IF NOT EXISTS`); y SI una línea trae `descuentos`
  con más de un valor y `descuento` nulo, ENTONCES sv3 debe derivar de forma
  DETERMINISTA el descuento efectivo en cascada
  (`(1 − Π(1 − di/100)) × 100`, función pura con test). La IA jamás combina
  descuentos.

- **R4.** CUANDO sv5 construye el contexto de valoración, el sistema debe
  exponer por línea `importe_leido` (transcrito, null si el documento no lo
  imprime) además del `importe_albaran` efectivo (el leído si existe; si no,
  la derivación actual `cantidad × precio_neto` como fallback), y debe
  incluir `importe_total_albaran` en el `meta` del envelope (misma vía que
  `fecha_albaran`). SI el documento es anterior a esta feature (columnas
  NULL) o el sobre es antiguo, ENTONCES todo debe comportarse exactamente
  como hoy (campos null → guards no-op).

- **R5.** CUANDO el precio unitario final de una línea `from_albaran`
  procede del CONTRATO (`precio_source` ∈ {`contract_line_match`,
  `pdf_inference`, `both_agreed`}), el sistema (sv6) NO debe aplicar el
  descuento del albarán al calcular el importe; si la línea traía descuento,
  debe quedar el motivo de auditoría
  `descuento_albaran_no_aplicado_a_precio_contrato` en `review_reasons`.
  CUANDO el precio procede del albarán (`albaran_declared` /
  `albaran_calculated`), la fórmula actual con descuento se mantiene
  (regresión). *(Las sintéticas M1–M7 mantienen la herencia del descuento
  del padre salvo que el humano decida lo contrario — pregunta abierta P1.)*

## G4 — Guard aritmético

- **R6.** CUANDO una línea `from_albaran` trae `importe_leido`, precio
  declarado y cantidad, el sistema (sv6) debe verificar
  `precio × cantidad × (1 − dto_efectivo/100) ≈ importe_leido` con
  tolerancia `IMPORTE_TOLERANCE_PCT`; SI no cuadra, ENTONCES debe marcar la
  línea `review_required = true` con motivo
  `guard_aritmetico_linea:<calculado>!=<leido>` y el importe persistido debe
  seguir siendo el LEÍDO (jamás sustituirlo por el calculado ni por ningún
  valor inventado). *(Test del caso ×120: línea con cantidad 120,55, precio
  1,5877 e importe leído 191,40 → se persiste 191,40 con
  `importe_source='declared_albaran'`, nunca 23.073,60.)*

- **R7.** CUANDO el `meta` del envelope trae `importe_total_albaran`, el
  sistema (sv6) debe comparar la suma de los importes finales de las líneas
  `from_albaran` (las sintéticas NO suman: no están impresas) con ese total;
  SI difieren más de `IMPORTE_TOLERANCE_PCT`, ENTONCES la cabecera de la
  valoración debe quedar `review_required = true` con motivo
  `guard_aritmetico_total:<suma>!=<total>`. SI `importe_total_albaran` es
  null, el guard no actúa.

- **R8.** CUANDO el documento tiene exactamente UNA línea `from_albaran`,
  `importe_total_albaran` presente y la línea SIN `importe_leido`, el
  sistema debe usar el total como importe leído efectivo de esa línea, con
  motivo `importe_desde_total_documento`. *(Caso ORE OIL: una línea →
  importe = total.)* SI la línea única SÍ trae importe leído y difiere del
  total más allá de la tolerancia, aplica R7.

## G5 — Matching estricto

- **R9.** El prompt de IA3 (`valuation_es`, sv5) debe ampliar la sección «No
  cases productos diferentes» con la regla general: un ATRIBUTO SUSTANTIVO
  distinto (dimensión/espesor/diámetro, modelo o referencia, tipo o
  material, formato de venta) ⇒ `no_match`, con los casos de referencia:
  ladrillos de modelo distinto (CETOSA), «ELEMENTO BASE 0,5 mm» vs otro
  espesor, «BOLSA DE CUÑAS» vs cuñas en otro formato; y la máxima de
  negocio: mejor línea nueva SIN precio a revisión que un precio equivocado
  con apariencia de bueno. Las diferencias solo tipográficas o de formato
  (D-300 ≈ D300) siguen casando (la regla existente no se endurece ahí).

- **R10.** El prompt de IA4 (`conciliacion_es`, sv5) debe incorporar la
  misma REGLA DURA de atributo sustantivo (al nivel de la regla dura de años
  ya existente): si la descripción difiere en un atributo sustantivo, jamás
  casar por parecido textual; `no_match` y a revisión.

- **R11.** CUANDO sv6 recibe el envelope (tras IA4 y ANTES del build), una
  red determinista nueva debe comparar los tokens dimensionales
  normalizados (número + unidad: `0,5 mm`, `ø12`, `6 m3`…) de la
  descripción del albarán y de la línea de contrato casada en cada línea
  `from_albaran`; SI ambas descripciones contienen magnitudes del mismo tipo
  con valores distintos, ENTONCES debe anular el match
  (`matched_contrato_line_id = null`, `precio_unitario_contrato_db = null`,
  `precio_unitario_pdf_inferido = null`, `match_method = 'no_match'`) con
  motivo `atributo_sustantivo_mismatch:<albaran>!=<contrato>`. Los tokens
  numéricamente equivalentes con formato distinto (0,5 = 0.5 = 0,50;
  D-300 = D300) NO disparan la red. La red NO actúa sobre líneas de familia
  hormigón ni mortero (tienen su propia maquinaria posicional) ni sobre
  sintéticas.

- **R12.** CUANDO la red R11 anula un match, la línea debe seguir el
  mecanismo existente de «línea nueva» (`derived` con
  `origen='nueva_no_match'`) SIN precio de contrato y con
  `review_required = true` — nunca heredar el precio de la línea anulada.

## Transversales

- **R13.** DONDE la configuración lo indique, cada mecanismo nuevo de sv6
  debe poder desactivarse individualmente (`GUARD_ARITMETICO_ENABLED`,
  `RED_ATRIBUTO_SUSTANTIVO_ENABLED`, default true); a `false` el
  comportamiento es exactamente el previo a esta feature (tests de
  regresión).

- **R14.** SI un sobre en cola o una fila de BBDD es anterior a esta feature
  (campos nuevos ausentes/null), ENTONCES la valoración debe completarse sin
  error y con el comportamiento actual (semántica at-least-once de las
  colas: no se puede exigir redrive).

- **R15.** Los prompts tocados (IA1 de sv2; IA3 e IA4 de sv5) son rutas
  sensibles de la puerta de evals (F-011): el ground truth de
  `evals/ground_truth/` (IA1, IA3, IA4) debe actualizarse con los casos de
  esta feature (×120, ORE OIL, CETOSA, elemento base 0,5 mm, bolsa de
  cuñas) como parte del cierre — como fixtures ejecutables si F-011 ya está
  implementada, o como actualización de los libros Excel (MANUAL humano) si
  aún no.
