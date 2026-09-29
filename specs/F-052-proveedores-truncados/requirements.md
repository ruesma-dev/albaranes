<!-- specs/F-052-proveedores-truncados/requirements.md -->
# F-052 · Proveedores de la obra truncados y búsqueda de contrato veraz · Requisitos

Rigor **critico**. Servicios: **sv3** (dueño del cambio y del schema), **sv4**,
**`ruesma_comun`**. **v2 (2026-09-29)**, tras medir el grano:
`progress/explore_F-052_grano.md`. Causa raíz: `progress/explore_salmedina_proveedor.md`.

Glosario:
- **Consulta agregada de la obra**: la SQL de `design.md` §4, una fila por
  proveedor con contrato `emp=1` en la obra (`WITH` + `FOR XML PATH`). Medida:
  máx. 163 filas (0696) en las 74 obras de más de 1.000 líneas.
- **Texto de familia**: valores distintos y no vacíos de nombre de contrato,
  descripción de línea y código de producto del proveedor en la obra. El
  **texto por líneas** es el de hoy: esos tres campos concatenados línea a línea.
- **Política de truncado**: `TOLERA` (se usan las filas y se registra WARNING)
  o `NO_TOLERA` (se lanza `SigridRespuestaTruncada`).
- **Rastro de búsqueda**: CIF, obra, resultado y fecha de la última búsqueda
  de contratos de un documento. **Doble de sigrid-api**: `design.md` §7.

## A. Candidatos completos y texto de familia (sv3)

R1. CUANDO el CIF leído no existe en Sigrid y hay obra y nombre leídos, el
sistema debe buscar el candidato por nombre entre **todos** los proveedores con
contrato en la obra. (Regresión: obra con 2.083 líneas y el proveedor bueno
más allá de la fila 1.000 de la consulta antigua.)

R2. CUANDO el resolver ejecuta el paso obra + familia, el sistema debe puntuar
**todos** los proveedores con contrato en la obra (81 en el fixture 0691),
aunque sus líneas sumen más de 1.000.

R3. `fetch_contratos_resumen_por_obra` debe obtener candidatos y texto con **una
sola llamada** a la consulta agregada, sin paginar, `NO_TOLERA`, un resumen por CIF.

R4. Para cada proveedor, `familias_de_texto` sobre el texto de familia debe dar
el **mismo conjunto** que sobre el texto por líneas, aunque haya descripciones
repetidas, espacios sobrantes, valores vacíos o un orden distinto.

R5. El resultado del paso obra + familia y el de la red por nombre deben ser
los mismos con independencia del orden en que sigrid-api devuelva las filas
(tres barajados distintos, mismo ganador y mismo texto por CIF).

R6. SI la consulta agregada falla (red, HTTP, `ok=false`, truncado o el error
de serialización `FOR XML could not serialize`), ENTONCES el resolver debe
tratarlo como **consulta fallida**: la red por nombre redacta la nota de R15 y
el paso obra + familia degrada al fallback global por nombre, como hoy. Nunca
debe tratarse como «nadie casa».

## B. `truncated` nunca en silencio (sv3, sv4 y `ruesma_comun`)

R7. Cada llamada a `_post_sql_read` del cliente de contratos de sv3 debe
declarar su política de truncado (parámetro obligatorio, sin valor por defecto).

R8. SI una respuesta de sigrid-api trae `truncated=true` y la política es
`NO_TOLERA`, ENTONCES el sistema debe lanzar `SigridRespuestaTruncada` con la
etiqueta de la consulta y el número de filas recibidas.

R9. SI una respuesta trae `truncated=true` y la política es `TOLERA`, ENTONCES
el sistema debe devolver las filas y registrar un WARNING con la etiqueta.

R10. Cada consulta del cliente de contratos de sv3 debe llevar la política y la
lectura de `design.md` §3; solo `header_and_lines` y `search_proveedores` paginan.

R11. CUANDO se llama a `fetch_contratos` para una pareja CIF + obra con más
líneas que una página, el sistema debe devolver **todas** las líneas agrupadas
por contrato en el mismo orden que hoy (`codigo_contrato`, `pos`), leyéndolas
con `OFFSET/FETCH` y un `ORDER BY` estable.

R12. CUANDO se llama a `search_proveedores`, el sistema debe devolver la lista
global completa (3.543 el 2026-09-29; hoy se corta a 1.000: su `max_rows` se ignora).

R13. SI una lectura paginada alcanza su tope de páginas, ENTONCES debe lanzar
`SigridRespuestaTruncada` (en `fetch_contratos`: rastro `error`, R21).

R14. Comprobar `truncated` y paginar deben ser funciones puras de
`ruesma_comun.sigrid.lectura`; `con_paginacion` rechaza sin `ORDER BY` (`ValueError`).

## C. Nota de revisión veraz (sv3)

R15. SI el CIF leído no existe y la consulta agregada de la obra falla, ENTONCES
la nota debe decir que **no se pudo consultar** la lista de proveedores de la
obra, no que nadie casa.

R16. SI el CIF leído no existe y no hay obra válida, ENTONCES la nota debe
decir que **no hay obra** con la que buscar candidatos.

R17. SI el CIF leído no existe y no se leyó nombre de proveedor, ENTONCES la
nota debe decir que **no hay nombre leído** con el que comparar.

R18. SI la consulta funcionó y ningún proveedor llega al umbral, ENTONCES la
nota debe decir que ninguno de los N proveedores con contrato en la obra casa
con el nombre leído, con N el número real de proveedores devueltos.

R19. En R15–R18 y en la propuesta, el motivo sigue siendo
`proveedor_cif_no_casa:<cif>` y el prefijo `[AVISO] Proveedor` (sv4 los retira).

## D. Rastro de la búsqueda de contratos (sv3 dueño, sv4 lector)

R20. El sistema debe añadir a `albaran_documents_merge`, con DDL idempotente
en sv3, las columnas `contratos_busqueda_cif`, `contratos_busqueda_obra`,
`contratos_busqueda_resultado` y `contratos_busqueda_at_utc`, todas nullable.

R21. CUANDO `ContratoEnrichmentService.enrich_merge_document` termina, el
sistema debe sellar el rastro con el CIF y la obra normalizados usados y el
resultado: `encontrados` (≥ 1, por Sigrid o por caché), `ninguno` (consulta
correcta, 0 contratos), `error` (la consulta lanzó, incluido truncado) o
`sin_datos` (faltaba CIF u obra). El sellado es best-effort: si falla, no
cambia el valor devuelto.

R22. CUANDO el re-fetch local de sv4 (modo solo-front) busca contratos, el
sistema debe sellar el mismo rastro con la misma semántica.

## E. El bloque de contrato de sv4 dice la verdad

R23. MIENTRAS no haya contratos y el rastro coincida con el CIF y la obra
actuales (normalizados) con resultado `ninguno`, el bloque debe decir «No se
encontró ningún contrato» con el CIF, la obra **y la fecha del rastro**.

R24. MIENTRAS el CIF o la obra actuales difieran del rastro, el bloque debe
decir con qué CIF y obra se buscó, que los datos actuales **todavía no se han
buscado** y ofrecer «Solo volver a buscar», también con contratos listados.

R25. MIENTRAS el resultado del rastro sea `error`, el bloque debe decir que la
última búsqueda **falló** y que eso no significa que no haya contrato.

R26. MIENTRAS el documento no tenga rastro (anterior a F-052), el bloque debe
decir que no consta con qué datos se buscó, sin afirmar que no hay contrato.

R27. Qué mensaje toca lo decide una función pura de sv4 (`estado_busqueda`).

## F. Lookup de sv4

R28. SI la consulta de proveedores de la obra del lookup de sv4 trae
`truncated=true`, ENTONCES debe lanzar (`NO_TOLERA`); `obras`, `contratos` y
`partidas` toleran con WARNING. Su SQL **no se comparte** con sv3 (D2).

## G. Verificación real (MANUAL, humano, solo lectura contra sigrid-api)

R29. En local, la consulta agregada de la obra 0691 debe traer 81 proveedores
con B82899550 dentro en 5 llamadas seguidas, `truncated=false`, score de nombre
1,0 para SALMEDINA; y `fetch_contratos` de B82899550 + 0691 debe devolver el
contrato CTSU24/0402 (comando en `tasks.md`).

R30. En 0691 y 0696, el script de verificación debe comparar las familias por
CIF del texto agregado con las del texto por líneas (consulta sin tope) y dar
**0 diferencias**, 81 y 163 filas y el mismo conjunto de CIF que la lista
`DISTINCT cif, raz` del selector de sv4.

R31. En local, con el documento SS-0026122: cambiar el CIF en sv4 y guardar
debe mostrar el aviso de R24; «Solo volver a buscar» debe traer CTSU24/0402 y
el bloque debe pasar a mostrar el rastro nuevo.
