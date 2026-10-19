<!-- specs/F-084-banco-valoracion/requirements.md -->
# F-084 · El banco de evals valora de verdad — requisitos (EARS)

Diagnóstico con evidencia en `design.md` §1. En una frase: **52 de los 59 casos
no tienen ni una línea de contrato en `evals/fixtures/inputs/`**, así que IA3 no
tiene contra qué casar, sv6 no tiene precio y sale «obtenido None» con cualquier
modelo, y también en el modo determinista, que no llama a ningún LLM. Además el
adaptador de sv5 no le da a la IA lo que sí le da producción (descuento,
clasificación, categoría de unidad, fecha). Ningún servicio está mal: el banco
está mal alimentado.

Servicios que se tocan: **ninguno** (solo `evals/`, sus tests, `README` y el
documento de `azure-apps/`). Preguntas abiertas P1–P7 en `design.md` §11; los
requisitos que dependen de una llevan su marca.

## A · Las líneas de contrato llegan a INPUTS desde Sigrid (P1)

**R1.** CUANDO el humano ejecuta `python -m evals.contratos_sigrid`, el sistema
debe leer de sigrid-api, con UNA consulta por `contrato_codigo` distinto de los
casos de `evals/fixtures/inputs/`, las líneas de ese contrato y escribirlas en
`ground_truth/INPUTS.xlsx` › `CONTRATO_LINEAS`, una fila por línea y caso, con
`caso_id`, `codigo_producto`, `descripcion_recurso`, `unidad`,
`precio_unitario`, `codigo_partida`, `linea_sigrid` y `comentario`.

**R2.** La consulta debe ser solo lectura: `POST /api/sql/read` con un único
`SELECT` parametrizado por el código del contrato, `emp = 1` y `ORDER BY`
estable, las mismas columnas de Sigrid que persiste sv3 (`design.md` §7).

**R3.** SI falta alguna de `SIGRID_API_BASE_URL`, `SIGRID_API_FUNCTION_KEY` o
`SIGRID_API_DATABASE`, ENTONCES el sistema debe parar antes de cualquier
petición, con código 2, nombrando las variables y sin tocar el libro.

**R4.** SI la respuesta de un contrato viene `truncated`, ENTONCES ese contrato
debe fallar (política `NO_TOLERA` de `ruesma_comun.sigrid.lectura`), sus casos
no se escriben, el motivo consta en el informe y los demás contratos siguen.

**R5.** SI el código casa con ningún contrato o con más de uno (`ctr.ide`
distintos), ENTONCES no se escribe nada de ese contrato y el informe lo dice.

**R6.** El importador no debe tocar un caso que ya tenga líneas de contrato en
el libro (los 7 RES, con sus señuelos escritos a mano): sus filas de
`CONTRATO_LINEAS` y `CONDICIONES` quedan idénticas.

**R7.** Antes de escribir, el sistema debe dejar la copia de seguridad del libro
(`evals.revision.escritura.copia_de_seguridad`); si nada cambia, el libro no se
guarda (su sha256 no se mueve).

**R8.** CUANDO se pasa `--dry-run`, el sistema no debe tocar el libro: solo
escribe el informe de R10.

**R9.** CUANDO un caso no declara `fecha_albaran` en `CONDICIONES`, el sistema
debe escribirla desde `IA1.cabeceras.fecha` de su fixture (el ground truth de
la extracción); nunca pisa una condición que ya exista.

**R10.** El sistema debe dejar `progress/import_F-084.md` con, por contrato,
líneas leídas, casos rellenados o motivo del fallo; y por caso, la
**cobertura**: de sus líneas IA3 con `precio_source = contrato_db`, cuántas
tienen su `precio_unitario_final` esperado en una sola línea importada, en
varias o en ninguna. Solo recuentos, `caso_id` y `num_linea`: ni precios, ni
descripciones, ni CIF.

**R11.** La identidad de una fila de `CONTRATO_LINEAS` debe ser (`caso_id`,
`codigo_producto`, `linea_sigrid`): dos líneas del mismo producto no se funden.
SI la tabla del libro no tiene la columna `linea_sigrid`, ENTONCES el
importador la añade al final de su fila de encabezados.

## B · El contexto de valoración es el de producción

**R12.** Las líneas de albarán del contexto de IA3 (corrida con LLM) y del
envelope estimulado (determinista) deben salir de UNA sola función, con
`descuento_albaran` = `descuentos`, `precio_neto_albaran` = `importe` (el
leído) e `importe_albaran` = `importe` o, si falta,
`cantidad × precio_unitario × (1 − descuento/100)`, la misma regla que el
`SELECT` de sv5 (`sqlalchemy_valuation_context_repository.py`).

**R13.** SI `descuentos` de una línea trae más de un valor, ENTONCES el caso
debe salir ERROR en IA3 con motivo «descuento compuesto no representable», sin
sumarlos ni ignorarlos.

**R14.** (P4) El contexto y el envelope deben llevar la `clasificacion` del
documento con la familia que corresponde a la tipología del caso
(`design.md` §6), de modo que sv5 elija el prompt de producción
(`valuation_residuos` para residuos) y sv6 la familia efectiva.

**R15.** En el subproceso de sv5, las líneas de albarán y de contrato deben
pasar por `UnitCategoryPrefilter` de sv5 antes de llegar al LLM y al envelope:
`unidad_categoria` es la de producción, no `unknown`.

**R16.** `fecha_albaran` y `numero_albaran` del contexto deben salir de
`CONDICIONES` (R9 rellena la fecha).

**R17.** (P5) Cada fase IA3, IA4 y E2E del informe debe declarar como «entrada
no reproducida» lo que el banco no da a IA3: el documento del contrato (MD o
PDF, fase 1b) y su cabecera (nombre, proveedor, obra).

## C · Runner y veredicto

**R18.** (P3) SI un caso tiene `contrato_codigo` pero ninguna línea de contrato
en INPUTS, ENTONCES IA3, IA4 y E2E de ese caso deben salir OMITIDO con motivo
«sin líneas de contrato en INPUTS», en las dos corridas, y la corrida con LLM
no debe mandarlo a sv5 (no se paga).

**R19.** CUANDO `--fases` no incluye IA1 ni IA2, la pasada con LLM no debe
invocar sv2 ni exigir sus claves.

**R20.** (P6) Sin `--proveedores`, el proveedor de IA3/IA4 debe ser el de
producción: `IA3_PROVIDER` del entorno o, si falta, `claude` (hoy `gemini`).

**R21.** El informe debe registrar en cada fase IA3, IA4 y E2E el proveedor y
el **modelo** usados (`- Modelo: …`), sin cambiar las líneas parseables
(`MODO:`, `FASES:`, `PROVEEDORES:`, `VEREDICTO:`).

**R22.** (P2) DONDE el estímulo por precio esté activo, en el modo determinista
una fila IA3 con `codigo_producto_contrato` `?` y `precio_source = contrato_db`
debe estimularse con la línea de contrato cuyo `precio_unitario` sea el
`precio_unitario_final` esperado (y, si la partida esperada no es nula, su
misma partida) cuando sea **única**; si no hay o hay varias, `no_match` y un
aviso que diga por qué.

## D · Lo que no cambia

**R23.** El sistema no debe modificar sv5, sv6 ni ningún otro servicio, ni
ninguna ruta de `harness/rutas_sensibles.json`.

**R24.** Los 7 casos RES deben seguir igual: `tests/datos/
afirmado_por_el_humano_RES.json` pasa sin cambios y su resultado determinista
de IA3, IA4 y E2E no empeora en ningún caso.

**R25.** Los tests no deben tocar red ni BBDD: sigrid-api con
`httpx.MockTransport`, el LLM con un doble, el libro en `tmp_path`.

**R26.** El `evals/README.md` debe explicar el importador: qué lee, de dónde,
que es solo lectura, que lo lanza el humano y el orden importar → convertir →
corrida determinista.

## E · Verificación y nueva línea base

**R27.** CUANDO el humano ha importado y regenerado los fixtures, la corrida
determinista debe dar precio no nulo en toda línea IA3 con `precio_source =
contrato_db` cuya cobertura (R10) sea «única».

**R28.** La nueva línea base es una pasada con LLM de IA3, IA4 y E2E sobre los
59 casos con el modelo de producción (`claude-opus-4-8`), lanzada por el
humano (`design.md` §9). Vale si: 0 casos ERROR, el modelo consta en el
informe (R21) y los «obtenido None» son ≤ 20 % de los fallos críticos de IA3
de los casos evaluados (hoy 93 % y 95 %).
