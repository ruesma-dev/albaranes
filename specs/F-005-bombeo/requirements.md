<!-- specs/F-005-bombeo/requirements.md -->
# F-005 · Tanda 4a — Tipología bombeo · Requisitos

Notación EARS. Cada requisito se traduce a >= 1 test con nombre trazable
(`test_f005_rN_...`). Los unit tests NO tocan red ni BBDD (fixtures/mocks).

Normativa de referencia: `docs/referencia/dominio_negocio_albaranes.md`
§9.5 y §10.7, **con la errata corregida en la cabecera del documento**: el
caso real PUMPING TEAM es **10,5 h × 20 m³/h = 210 m³** (el «5 h» del
§10.7 original está mal). Regla de negocio:

> m³ a facturar = horas de bombeo × rendimiento mínimo del contrato,
> aunque se bombeara menos. La línea de horas NO se factura aparte
> (queda embebida en el mínimo). El desplazamiento SÍ se factura.

## Modelo compartido (`ruesma_comun`)

- **R1.** El sistema debe admitir `'bombeo'` como valor de
  `ContextoLinea.tipo_familia` y dos campos opcionales nuevos en
  `ContextoLinea`: `horas_bombeo: float | None` (horas de servicio de
  bombeo declaradas por el albarán) y `m3_bombeados: float | None` (m³
  realmente bombeados si el documento los declara). Un `ContextoLinea`
  serializado ANTES de esta feature (sin esos campos) debe seguir
  validando (compatibilidad retroactiva; el modelo ya es
  `extra="ignore"`).

## sv2 — tipología a nivel documento

- **R2.** CUANDO la fase 1 clasifica alguna línea con
  `contexto_linea.tipo_familia='bombeo'` y el documento no trae señal LER,
  el `tipologia_resolver` debe consolidar la tipología `bombeo`.

- **R3.** CUANDO ninguna línea trae `contexto_linea` pero el texto de
  código/concepto de alguna línea contiene señal de bombeo (palabra
  «bombeo» o «bomba») Y NINGUNA línea del documento contiene una
  designación posicional de hormigón (`HA-25`, `HM-20`...), el resolver
  debe consolidar `bombeo` **aunque el texto contenga la palabra
  «hormigón»** (caso real: «SERVICIO DE BOMBEO DE HORMIGÓN» de un
  proveedor de bombeo, sin suministro). *(Hoy la palabra «hormig» sola
  enruta a hormigón; este requisito invierte esa prioridad solo cuando
  hay señal de bombeo y no hay designación.)*

- **R4.** CUANDO el documento contiene a la vez una designación posicional
  de hormigón (suministro de central) y menciones de bombeo («HORMIGÓN
  BOMBEADO HA-25»), el resolver debe consolidar `hormigon` (no `bombeo`).
  SI el documento trae un código LER válido, ENTONCES debe consolidar
  `residuos` con independencia de cualquier señal de bombeo (la regla
  dura LER existente no cambia).

- **R5.** CUANDO la tipología consolidada es `bombeo`, la fase 2 debe
  ejecutarse con `prompt_key='albaran_revision_fase2_bombeo'`, y ese
  prompt (en `config/prompts.yaml` de sv2) debe instruir de forma
  literal comprobable: (a) `tipo_familia='bombeo'` en todas las líneas
  del servicio de bombeo; (b) `horas_bombeo` con las horas totales de
  bombeo del documento en la línea base; (c) `m3_bombeados` si el
  documento declara m³ realmente bombeados; (d) el desplazamiento como
  línea con `rol_linea='desplazamiento'`; (e) prohibido calcular m³ a
  facturar (eso es de la valoración). *(El mecanismo de fallback
  existente —si el prompt no existe, cae al genérico— no se toca.)*

## sv5 — routing y contrato de salida

- **R6.** CUANDO el contexto de valoración contiene líneas con
  `tipo_familia='bombeo'` y ninguna de `residuos`, el sistema debe
  derivar la tipología de valoración `bombeo` y usar el prompt
  `valuation_bombeo` si existe en el repositorio de prompts (prioridad:
  `residuos` > `bombeo` > `hormigon` > `generico`).

- **R7.** El schema de salida de IA3 (`LineValuation` en sv5 y su réplica
  `LineValuationDto` en sv6) debe admitir el campo opcional
  `rendimiento_minimo_m3h: float | None` (rendimiento mínimo contractual
  en m³/hora que la IA lee del contrato). Envelopes sin ese campo deben
  seguir validando en ambos servicios (compatibilidad con sobres en cola).

- **R8.** El prompt `valuation_bombeo` (en `config/prompts.yaml` de sv5)
  debe instruir de forma literal comprobable: (a) casar la línea base de
  bombeo con la línea de contrato de bombeo tarifada en €/m³; (b) la
  diferencia de unidad horas vs m³ NO bloquea el match (es esperada,
  como en residuos); (c) leer el RENDIMIENTO MÍNIMO (m³/h) de la línea
  de contrato o del PDF/markdown del contrato y emitirlo en
  `rendimiento_minimo_m3h`, con `pdf_inference_reasoning` indicando de
  dónde sale; (d) NO calcular los m³ a facturar ni importes (los calcula
  otro servicio de forma determinista); (e) NO emitir líneas sintéticas;
  (f) la línea de desplazamiento se casa/tarifa con normalidad
  (rol `desplazamiento`); (g) si no encuentra el rendimiento en el
  contrato, emitir `rendimiento_minimo_m3h=null` y un review_reason.

## sv6 — regla determinista horas × rendimiento

- **R9.** CUANDO una línea base de bombeo (`tipo_familia='bombeo'`,
  `rol_linea` nulo o `'base'`) dispone de horas (por prioridad:
  `contexto_linea.horas_bombeo`; si falta, la `cantidad` de la propia
  línea cuando su unidad es de categoría `time`) y de un rendimiento
  mínimo (R10), el cálculo determinista debe devolver
  `m3_a_facturar = horas × rendimiento`. Con el caso real PUMPING TEAM
  (10,5 h, 20 m³/h) el resultado debe ser exactamente 210.0.

- **R10.** El rendimiento efectivo debe resolverse así: CUANDO la
  descripción de la línea de contrato casada contiene un patrón de
  rendimiento (p. ej. «20 m3/h», «20 M3/HORA», «mínimo 20 m³ por
  hora»), el sistema debe usar ese valor determinista; SI además la IA
  emitió `rendimiento_minimo_m3h` y discrepa del determinista, ENTONCES
  debe prevalecer el determinista, añadirse la razón
  `bombeo_rendimiento_discrepante:<ia>!=<contrato>` y forzarse
  `review_required=true`. CUANDO no hay patrón en la descripción pero la
  IA emitió `rendimiento_minimo_m3h`, el sistema debe usar el valor de
  la IA y forzar `review_required=true` con razón
  `bombeo_rendimiento_sin_verificacion_determinista` (el dato viene del
  PDF y no es contrastable de forma determinista).

- **R11.** SI la línea base de bombeo no dispone de horas o no dispone de
  ningún rendimiento (ni determinista ni de la IA), ENTONCES la línea
  debe valorarse SIN transformación de cantidad (comportamiento actual),
  con razón `bombeo_sin_horas` o `bombeo_sin_rendimiento` y
  `review_required=true`. Nunca se inventa un rendimiento por defecto.

- **R12.** SI el rendimiento efectivo está fuera del rango plausible
  (menor que 5 o mayor que 150 m³/h) o las horas superan 24, ENTONCES el
  cálculo se realiza igualmente pero la línea debe marcarse
  `review_required=true` con razón `bombeo_valores_implausibles:<detalle>`.

- **R13.** CUANDO el cálculo de R9 se aplica, la cantidad valorada y la
  cantidad de albarán persistidas deben ser los m³ calculados, el importe
  debe calcularse como m³ × precio unitario final (con el descuento de
  línea si lo hay), debe añadirse la razón trazable
  `bombeo_minimo_aplicado:<horas>x<rendimiento>`, y el desacuerdo de
  categoría de unidad horas vs m³ NO debe, por sí solo, forzar
  `review_required` (es el desacuerdo esperado de la tipología, como los
  m³ vs contenedor de residuos). Los m³ realmente bombeados
  (`m3_bombeados`) se conservan como metadato en `contexto_linea_json`
  sin afectar al importe, aunque sean menores que los facturados.

- **R14.** CUANDO además de la línea base transformada existe otra línea
  `from_albaran` del mismo documento de bombeo cuya unidad es de
  categoría `time` (la línea de horas facturada aparte), esa línea debe
  quedar con cantidad valorada 0 e importe 0, con razón
  `bombeo_horas_embebidas` (la regla de negocio: las horas van embebidas
  en el mínimo, no se facturan aparte). *(Si el albarán solo trae la
  línea de horas, esa línea ES la base y se transforma según R9; este
  requisito solo aplica cuando hay base y línea de horas separadas.)*

- **R15.** El sistema debe valorar la línea de `rol_linea='desplazamiento'`
  de un albarán de bombeo con el flujo normal de complementarias
  (SÍ se factura): ni se anula ni hereda la transformación de R9.

## Transversales

- **R16.** DONDE el documento no contenga ninguna línea de bombeo, el
  comportamiento de sv2, sv5 y sv6 debe ser idéntico al actual (tests de
  regresión: hormigón, mortero, residuos y genérico existentes siguen en
  verde con el mismo resultado).
