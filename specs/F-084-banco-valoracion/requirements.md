<!-- specs/F-084-banco-valoracion/requirements.md -->
# F-084 · El banco de evals valora de verdad — requisitos (EARS)

Diagnóstico en `design.md` §1: 52 de los 59 casos no tienen líneas de contrato en
INPUTS y el adaptador de sv5 no da a la IA lo que le da producción. Servicios
tocados: **ninguno** (solo `evals/`). PARADA 1 resuelta el 2026-10-20 (design §11).

## A · Líneas de contrato desde Sigrid (`python -m evals.contratos lineas`)

**R1.** CUANDO el humano ejecuta `python -m evals.contratos lineas`, el sistema
debe leer de sigrid-api, una consulta por `contrato_codigo` distinto de los
casos de `evals/fixtures/inputs/`, las líneas del contrato y escribirlas en
`ground_truth/INPUTS.xlsx` › `CONTRATO_LINEAS`, una fila por línea y caso:
`caso_id`, `codigo_producto`, `descripcion_recurso`, `unidad`,
`precio_unitario`, `codigo_partida`, `linea_sigrid`, `comentario`.

**R2.** La consulta debe ser solo lectura: `POST /api/sql/read`, un `SELECT`
parametrizado por código, `emp = 1`, `ORDER BY` estable y las columnas de Sigrid
que persiste sv3 (`design.md` §7).

**R3.** SI falta `SIGRID_API_BASE_URL`, `SIGRID_API_FUNCTION_KEY` o
`SIGRID_API_DATABASE`, ENTONCES debe parar antes de pedir nada, código 2,
nombrando las variables y sin tocar el libro.

**R4.** SI la respuesta viene `truncated`, ENTONCES ese contrato falla
(`NO_TOLERA`), sus casos no se escriben, consta el motivo y el resto sigue.

**R5.** SI el código casa con ningún contrato o con más de un `ctr.ide`,
ENTONCES no se escribe ese contrato y el informe lo dice.

**R6.** El importador no debe tocar los casos que ya tienen líneas de contrato
(los 7 RES, con sus señuelos): sus filas de `CONTRATO_LINEAS` y `CONDICIONES`
quedan idénticas.

**R7.** Antes de escribir debe dejar la copia de seguridad del libro
(`escritura.copia_de_seguridad`); si nada cambia, no lo guarda.

**R8.** CUANDO se pasa `--dry-run`, no debe tocar el libro: solo el informe.

**R9.** CUANDO un caso no declara `fecha_albaran` en `CONDICIONES`, debe
escribirla desde `IA1.cabeceras.fecha` de su fixture; nunca pisa una existente.

**R10.** Debe dejar `progress/import_F-084.md`: por contrato, líneas leídas y
casos o motivo del fallo; por caso, cuántas de sus líneas IA3 `contrato_db`
tienen su precio esperado entre los de las líneas importadas (control del
contrato vigente, no emparejamiento). Solo recuentos, `caso_id` y `num_linea`.

**R11.** La identidad de una fila de `CONTRATO_LINEAS` debe ser (`caso_id`,
`codigo_producto`, `linea_sigrid`). SI el libro no tiene la columna
`linea_sigrid`, ENTONCES el importador la añade al final de los encabezados.

## B · Documento y cabecera del contrato (`python -m evals.contratos documentos`)

**R29.** CUANDO el humano ejecuta `python -m evals.contratos documentos`, el
sistema debe, por contrato, leer en solo lectura de la BBDD `albaranes` la fila
de `albaran_contratos_merge` que lee sv5 (la más reciente del código) y
descargar de SharePoint, con el descargador de sv5, el MD si hay
`md_sharepoint_relative_path` y si no el PDF, igual que `ValueAlbaranPipeline`.

**R30.** El documento debe quedar en `evals/inputs/contratos/` (no versionado)
y en `evals/fixtures/contratos/_indice.json` (versionado) el código, `tipo`
(`md`, `pdf` o `ninguno`), `sha256`, motivo y la cabecera (nombre, CIF y nombre
del proveedor, código y nombre de obra); nunca el contenido del documento.

**R31.** SI el contrato no está en la tabla, no tiene ruta, la descarga falla o
el PDF pasa de `MAX_PDF_MB` (40, el de sv5), ENTONCES `tipo = ninguno` con su
motivo y los demás contratos siguen.

**R34.** SI falta alguna variable de BBDD (`PG_*`) o de Graph/SharePoint
(`GRAPH_KEY`, `SHAREPOINT_*`), ENTONCES debe parar antes de conectar, código 2;
la sesión de BBDD se abre en solo lectura y no escribe en ningún sistema.

## C · El contexto de valoración es el de producción

**R12.** Las líneas de albarán del contexto de IA3 y del envelope estimulado
deben salir de UNA función: `descuento_albaran` = `descuentos`,
`precio_neto_albaran` = `importe` e `importe_albaran` = `importe` o, si falta,
`cantidad × precio_unitario × (1 − descuento/100)`, como el `SELECT` de sv5.

**R13.** SI `descuentos` trae más de un valor, ENTONCES el caso sale ERROR en
IA3 con motivo «descuento compuesto no representable».

**R14.** El contexto y el envelope deben llevar la `clasificacion` del documento
con la familia de la tipología del caso (`design.md` §6): sv5 elige el prompt
de producción y sv6 la familia efectiva.

**R15.** En el subproceso de sv5, las líneas pasan por `UnitCategoryPrefilter`
antes de llegar al LLM y al envelope.

**R16.** `fecha_albaran` y `numero_albaran` del contexto salen de `CONDICIONES`.

**R17.** El contexto debe llevar la cabecera del contrato del índice (R30), y el
informe declarar en IA3, IA4 y E2E cuántos casos se valoraron con `md`, `pdf` o
`ninguno`.

**R32.** CUANDO el contrato de un caso tiene documento en el índice y el fichero
local casa con su `sha256`, IA3 debe recibirlo como en el pipeline (MD como
`contrato_markdown`, PDF como adjunto), sin red y en la misma llamada.

**R33.** SI el índice declara documento pero el fichero local falta o no casa,
ENTONCES IA3, IA4 y E2E del caso salen OMITIDO con «documento del contrato no
disponible en local», y no se manda a sv5.

## D · Runner y veredicto

**R18.** SI un caso tiene `contrato_codigo` y ninguna línea de contrato en
INPUTS, ENTONCES IA3, IA4 y E2E salen OMITIDO con «sin líneas de contrato en
INPUTS», en las dos corridas, sin mandarlo a sv5.

**R19.** CUANDO `--fases` no incluye IA1 ni IA2, la pasada con LLM no invoca
sv2 ni exige sus claves.

**R20.** Sin `--proveedores`, IA3/IA4 usan `IA3_PROVIDER` del entorno o
`claude` (hoy `gemini`).

**R21.** El informe registra en IA3, IA4 y E2E proveedor y **modelo**
(`- Modelo: …`), con las líneas parseables intactas.

**R36.** El informe de la corrida determinista debe decir, en IA3, IA4 y E2E,
que **no mide el emparejamiento**: una línea sin emparejar en el ground truth
(`?`) sigue sin emparejar, porque emparejar es trabajo de IA3/IA4 y solo lo
mide la corrida con LLM. El banco no empareja por partida, precio ni texto.

## E · Lo que no cambia

**R23.** No se modifica sv5, sv6 ni ningún servicio, ni ninguna ruta de
`harness/rutas_sensibles.json`.

**R24.** Los 7 RES siguen igual: `tests/datos/afirmado_por_el_humano_RES.json`
pasa sin cambios y su determinista no empeora en ningún caso.

**R25.** Los tests no tocan red ni BBDD: sigrid-api con `httpx.MockTransport`,
BBDD y SharePoint con dobles, LLM con doble, libros en `tmp_path`.

**R26.** `evals/README.md` explica los dos subcomandos, de dónde leen, que son
solo lectura y los lanza el humano, y el orden importar → convertir →
determinista.

## F · Verificación y nueva línea base

**R27.** Tras importar y regenerar los fixtures, ningún caso con líneas importadas
debe salir OMITIDO por R18, FER-001 debe dar `importe_calculado` 19,41 en el
determinista y su informe debe llevar la advertencia de R36.

**R28.** Línea base: pasada con LLM de IA3, IA4 y E2E sobre los 59 casos con
`claude-opus-4-8`, lanzada por el humano (`design.md` §9). Vale con 0 casos
ERROR, el modelo en el informe y «obtenido None» ≤ 20 % de los fallos críticos
de IA3 de los casos evaluados (hoy 93 % y 95 %).
