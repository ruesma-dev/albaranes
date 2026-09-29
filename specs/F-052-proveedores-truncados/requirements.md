<!-- specs/F-052-proveedores-truncados/requirements.md -->
# F-052 · Proveedores de la obra truncados y búsqueda de contrato veraz · Requisitos

Rigor **critico**. Servicios: **sv3** (dueño del cambio y del schema), **sv4**
y **`ruesma_comun`**. Diagnóstico con fichero:línea y evidencia (no se
repite): `progress/explore_salmedina_proveedor.md`.

Glosario:
- **Lista de proveedores de la obra**: `SELECT DISTINCT prv.cif, prv.raz` de
  los contratos `emp=1` de la obra (grano proveedor, no línea de contrato).
- **Texto de familia**: nombre de contrato + descripción de línea + código de
  producto de cada línea de contrato del proveedor en la obra.
- **Política de truncado**: `TOLERA` (se usa la respuesta y se registra
  WARNING) o `NO_TOLERA` (se lanza `SigridRespuestaTruncada`).
- **Rastro de búsqueda**: CIF, obra, resultado y fecha de la última búsqueda
  de contratos de un documento.
- **Doble de sigrid-api**: transporte HTTP falso (`design.md` §7); sin red.

## A. Lista de candidatos completa (sv3)

R1. CUANDO el CIF leído no existe en Sigrid y hay obra y nombre leídos, el
sistema debe buscar el candidato por nombre en la **lista de proveedores de la
obra** completa, sin depender del número de líneas de contrato de la obra.
(Caso de regresión: obra con 2.083 líneas y el proveedor bueno más allá de la
fila 1.000 en la consulta antigua.)

R2. CUANDO el resolver ejecuta el paso obra + familia, el sistema debe puntuar
**todos** los proveedores de la lista de proveedores de la obra, aunque sus
líneas de contrato sumen más de 1.000 filas.

R3. El sistema debe obtener el texto de familia de la obra **paginado** con
`OFFSET/FETCH` y un `ORDER BY` estable, pidiendo cada página con
`max_rows = tamaño de página + 1`, hasta recibir una página incompleta.

R4. SI el texto de familia alcanza el tope de páginas configurado, ENTONCES el
sistema debe lanzar `SigridRespuestaTruncada` y el paso obra + familia NO debe
deducir proveedor: degrada como ante cualquier fallo de la consulta y deja
WARNING en el log con la obra y las filas leídas.

R5. El resultado del paso obra + familia debe ser el mismo con independencia
del orden en que sigrid-api devuelva las filas (determinismo: tres llamadas
con órdenes distintos dan el mismo ganador).

## B. `truncated` nunca en silencio (sv3 y `ruesma_comun`)

R6. El sistema debe obligar a que cada llamada a `_post_sql_read` del cliente
de contratos de sv3 declare su política de truncado (parámetro sin valor por
defecto).

R7. SI una respuesta de sigrid-api trae `truncated=true` y la política es
`NO_TOLERA`, ENTONCES el sistema debe lanzar `SigridRespuestaTruncada` con la
etiqueta de la consulta y el número de filas recibidas.

R8. SI una respuesta trae `truncated=true` y la política es `TOLERA`, ENTONCES
el sistema debe devolver las filas y registrar un WARNING con la etiqueta.

R9. Cada consulta del cliente de contratos de sv3 debe llevar la política de
la tabla de `design.md` §3 (7 consultas). En particular:
`header_and_lines` (líneas por CIF + obra), `search_proveedores` y el texto de
familia deben ir **paginadas** y `NO_TOLERA`.

R10. CUANDO se llama a `search_proveedores`, el sistema debe devolver la lista
global completa aunque supere las 1.000 filas (hoy su `max_rows=5000` se
ignora y corta a 1.000).

R11. CUANDO se llama a `fetch_contratos` para una pareja CIF + obra con más
de 1.000 líneas, el sistema debe devolver todas las líneas agrupadas por
contrato en el mismo orden que hoy (`codigo_contrato`, `pos`).

R12. La paginación y la comprobación de `truncated` deben vivir en
`ruesma_comun.sigrid` como funciones puras (sin HTTP), y `con_paginacion`
debe rechazar con `ValueError` una SQL sin `ORDER BY`.

## C. Nota de revisión veraz (sv3)

R13. SI el CIF leído no existe y la consulta de proveedores de la obra falla
(error de red, HTTP, `ok=false` o truncado), ENTONCES la nota debe decir que
**no se pudo consultar** la lista de la obra, no que nadie casa.

R14. SI el CIF leído no existe y no hay obra válida, ENTONCES la nota debe
decir que **no hay obra** con la que buscar candidatos.

R15. SI el CIF leído no existe y no se leyó nombre de proveedor, ENTONCES la
nota debe decir que **no hay nombre leído** con el que comparar.

R16. SI la consulta funcionó y ningún proveedor llega al umbral, ENTONCES la
nota debe decir que ninguno de los N proveedores con contrato en la obra casa
con el nombre leído, con N el tamaño real de la lista.

R17. En los cuatro casos anteriores y en la propuesta, el motivo sellado debe
seguir siendo `proveedor_cif_no_casa:<cif>` y el prefijo de nota
`[AVISO] Proveedor` (sv4 los retira por prefijo: no se rompe).

## D. Rastro de la búsqueda de contratos (sv3 dueño, sv4 lector)

R18. El sistema debe añadir a `albaran_documents_merge`, con DDL idempotente
en sv3, las columnas `contratos_busqueda_cif`, `contratos_busqueda_obra`,
`contratos_busqueda_resultado` y `contratos_busqueda_at_utc`, todas nullable.

R19. CUANDO `ContratoEnrichmentService.enrich_merge_document` termina, el
sistema debe sellar el rastro con el CIF y la obra normalizados usados y el
resultado: `encontrados` (≥ 1, por Sigrid o por caché), `ninguno` (consulta
correcta, 0 contratos), `error` (la consulta lanzó, incluido truncado) o
`sin_datos` (faltaba CIF u obra). El sellado es best-effort: si falla, no
cambia el valor devuelto.

R20. CUANDO el re-fetch local de sv4 (modo solo-front) busca contratos, el
sistema debe sellar el mismo rastro con la misma semántica.

## E. El bloque de contrato de sv4 dice la verdad

R21. MIENTRAS no haya contratos y el rastro coincida con el CIF y la obra
actuales (normalizados) con resultado `ninguno`, el bloque debe decir «No se
encontró ningún contrato» con el CIF, la obra **y la fecha del rastro**.

R22. MIENTRAS el CIF o la obra actuales difieran del rastro, el bloque debe
decir con qué CIF y obra se buscó, que los datos actuales **todavía no se han
buscado** y ofrecer «Solo volver a buscar». Vale también cuando sí hay
contratos listados (son de la búsqueda anterior).

R23. MIENTRAS el resultado del rastro sea `error`, el bloque debe decir que la
última búsqueda **falló** y que eso no significa que no haya contrato.

R24. MIENTRAS el documento no tenga rastro (anterior a F-052), el bloque debe
decir que no consta con qué datos se buscó y ofrecer volver a buscar, sin
afirmar que no existe contrato.

R25. La decisión de qué mensaje toca debe ser una función pura de sv4
(`estado_busqueda`), probada sin plantilla ni BBDD.

## F. Consulta compartida (sv4)

R26. El selector de proveedores de sv4 y la lista de proveedores de la obra de
sv3 deben usar la **misma** SQL, definida una sola vez en
`ruesma_comun.sigrid.consultas` (decisión D2).

R27. SI la consulta de proveedores de la obra de sv4 trae `truncated=true`,
ENTONCES sv4 debe lanzar el error (`NO_TOLERA`); sus otras tres consultas
(`obras`, `contratos`, `partidas`) toleran con WARNING.

## G. Verificación real (MANUAL, humano)

R28. En local y en solo lectura contra sigrid-api, la lista de proveedores de
la obra 0691 debe traer 81 proveedores con B82899550 dentro en 5 llamadas
seguidas, con score de nombre 1,0 para SALMEDINA; y `fetch_contratos` de
B82899550 + 0691 debe devolver el contrato CTSU24/0402 (comando en `tasks.md`).

R29. En local, con el documento SS-0026122: cambiar el CIF en sv4 y guardar
debe mostrar el aviso de R22; «Solo volver a buscar» debe traer CTSU24/0402 y
el bloque debe pasar a mostrar el rastro nuevo.
