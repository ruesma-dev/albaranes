<!-- specs/F-002-obra-proveedor/requirements.md -->
# F-002 · Tanda 1 — Identificación de obra y proveedor (G1+G2) · Requisitos

Notación EARS. Cada requisito se traduce a >= 1 test con nombre trazable
(`test_f002_rN_...`). Los unit tests NO tocan red ni BBDD: los clientes de
sigrid-api y los repositorios se sustituyen por fakes/mocks.

Normativa de referencia: `docs/referencia/dominio_negocio_albaranes.md` §10.1
(reglas 🔶 de identificación) y `docs/ARCHITECTURE.md`.

## G1 — Obra solo de la lista de obras activas

- **R1.** CUANDO sv2 construye el prompt de IA1 (fase 1) y el proveedor de
  obras activas devuelve una lista no vacía, el sistema debe inyectar en el
  prompt un bloque con las obras (`codigo — nombre`), **ordenado por código
  ascendente**, limitado a `OBRAS_ACTIVAS_MAX` entradas, junto con la
  instrucción de que `obra_codigo` se elija SOLO de esa lista y que, si el
  documento no permite identificar la obra con seguridad, se devuelva `null`
  (nunca un código que no esté en la lista).
  *(El orden y formato fijos hacen el prompt determinista: compatible con las
  evals de ground truth de F-011.)*

- **R2.** SI la lista de obras no está disponible (funcionalidad
  deshabilitada, credenciales ausentes, error de sigrid-api o lista vacía),
  ENTONCES el sistema debe construir el prompt de fase 1 con una nota de
  «lista no disponible» en lugar del bloque, y la extracción debe continuar
  exactamente como hoy (sin lanzar excepción). *(La red determinista de sv3 —
  R5/R6 — sigue protegiendo aguas abajo.)*

- **R3.** MIENTRAS la caché de obras activas de sv2 no haya expirado
  (`OBRAS_ACTIVAS_TTL_S`), el sistema no debe volver a consultar sigrid-api:
  extraer N albaranes dentro del TTL produce exactamente 1 llamada.

- **R4.** El prompt de fase 1 (`albaran_factura_es`) debe instruir que
  `proveedor_nombre` es la **razón social del bloque fiscal** (la que
  acompaña al CIF) y que la marca comercial del logotipo NO es el proveedor.
  *(El texto actual dice «Puede venir en el logo»: se sustituye.)*

- **R5.** CUANDO el merge trae un `obra_codigo` normalizable (4 dígitos con 0
  inicial) y la consulta a Sigrid no encuentra esa obra, el sistema (sv3)
  debe dejar el documento SIN obra (`obra_codigo = NULL` en
  `albaran_documents_merge`), marcar `review_required = true`, añadir el
  motivo `obra_inexistente:<codigo>` a `review_reasons_json` y dejar una nota
  de revisión con prefijo `[AVISO] Obra`. Jamás debe quedar persistida una
  obra que no exista en Sigrid. *(Caso de referencia: obra 0937 inventada.)*

- **R6.** SI el merge trae un `obra_codigo` no nulo que NO normaliza (p. ej.
  «1234», «12345»), ENTONCES el sistema debe aplicar el mismo tratamiento que
  R5 con motivo `obra_codigo_invalido:<valor>`.

- **R7.** CUANDO un re-enriquecimiento posterior valida la obra (p. ej. el
  revisor la corrigió en sv4 y pulsó «volver a buscar»), el sistema debe
  retirar la nota `[AVISO] Obra` y los motivos `obra_*` de
  `review_reasons_json`; y CUANDO un documento ya descartado se reprocesa sin
  cambios, no deben duplicarse ni la nota ni el motivo (idempotencia).

## G2 — Proveedor = razón social por CIF

- **R8.** CUANDO el merge trae `proveedor_cif` y ese CIF existe en el maestro
  `prv` de Sigrid, el sistema (sv3) debe sobrescribir `proveedor_nombre` en
  el merge con la razón social canónica (`prv.raz`). *(El literal leído queda
  auditado en las tablas raw y en `raw_extraction_json`.)*

- **R9.** CUANDO el `proveedor_cif` leído NO existe en `prv` y el
  `proveedor_nombre` leído casa (score de nombre >= umbral del resolver) con
  un proveedor CON CONTRATO en la obra efectiva del documento, el sistema
  debe dejar una **propuesta a revisión**: nota con prefijo
  `[AVISO] Proveedor` que incluya el CIF y la razón social del candidato,
  `review_required = true` y motivo `proveedor_cif_no_casa:<cif>` — SIN
  sobrescribir automáticamente el CIF ni el nombre leídos. *(Caso de
  referencia: «GRUPO OTTO HORPRESOL» vs HORPRESOL, S.L.)*

- **R10.** SI el CIF leído no existe en `prv` y ningún candidato casa,
  ENTONCES el sistema debe marcar `review_required = true` con motivo
  `proveedor_cif_no_casa:<cif>` y nota indicando que el CIF no existe en
  Sigrid, sin proponer candidato.

- **R11.** CUANDO el merge NO trae `proveedor_cif`, el comportamiento actual
  del `HeaderResolverService` (deducción por nombre / familia+obra) debe
  mantenerse sin cambios (test de regresión).

## Guard de año (fecha del albarán vs recepción del email)

- **R12.** CUANDO el worker de sv3 procesa un mensaje de `q-persistencia`
  cuyo `correlation_key` tiene fila en `workflow_runs`, el sistema debe
  reconstruir el contexto de email desde `payload_json` (id, subject,
  sender, receivedDateTime) y pasarlo al pipeline, de modo que
  `email_received_datetime` quede persistido en el merge (hoy queda NULL en
  el modo colas). *(Prerrequisito del guard R13.)*

- **R13.** CUANDO la `fecha` del merge y la fecha de referencia de recepción
  distan más de `FECHA_GUARD_MAX_DIAS` (por defecto 365) en cualquier
  sentido, el sistema debe marcar `review_required = true`, añadir el motivo
  `fecha_albaran_fuera_de_rango:<fecha>` y dejar nota de revisión con prefijo
  `[AVISO] Fecha`. *(Caso de referencia: fecha 2023 en email de 2026.)*

- **R14.** SI `email_received_datetime` no está disponible en el merge,
  ENTONCES el guard debe usar la fecha actual (UTC) como referencia de
  recepción. *(El procesamiento ocurre a días de la recepción; el margen de
  un año absorbe la diferencia.)*

- **R15.** SI la `fecha` del merge es nula o no parseable como fecha ISO,
  ENTONCES el guard no debe actuar (la ausencia de fecha ya penaliza la
  confianza del merge por la vía existente).

## Transversales

- **R16.** SI cualquiera de las redes (obra, proveedor, guard de año) o sus
  consultas a Sigrid lanzan una excepción, ENTONCES la persistencia debe
  continuar (best-effort): el error se loguea y el documento queda como
  estaba antes de esa red.

- **R17.** DONDE la configuración lo indique, cada red debe poder
  desactivarse individualmente (`RED_OBRA_ENABLED`,
  `RED_PROVEEDOR_CIF_ENABLED`, `FECHA_GUARD_ENABLED` en sv3;
  `OBRAS_ACTIVAS_ENABLED` en sv2), con default activado; a `false` el
  comportamiento es exactamente el previo a esta feature.
