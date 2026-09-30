<!-- specs/F-052-proveedores-truncados/design.md -->
# F-052 · Diseño técnico (v2, 2026-09-29)

## 1. Encaje y límite de servicio

Ninguna responsabilidad nueva: sv3 resuelve la cabecera, busca contratos y es
dueño del schema; sv4 es el front; lo compartido (comprobar `truncated`,
paginar) va a `ruesma_comun`. Sigrid: solo lectura vía `/api/sql/read`.

**El problema era el grano, no el tamaño de la obra** (v2). La consulta de hoy
trae una fila por línea de contrato (0696: 5.558). Agregada en SQL, una fila
por proveedor, la mayor obra da 163 filas y **0 diferencias de familias** en
las 74 obras de más de 1.000 líneas (`progress/explore_F-052_grano.md` §3).
El corte de 1.000 es el `max_rows` por defecto del cliente de sv3, no de
sigrid-api (`dev` admite 500.000, `azure-apps/sigrid_api.md` §4.1). Sigrid no
tiene `STRING_AGG` (error 195); `WITH` y `FOR XML PATH` sí pasan por sigrid-api.

## 2. Ficheros

**Crear**
- `services/albaranes-comun/ruesma_comun/sigrid/__init__.py`
- `services/albaranes-comun/ruesma_comun/sigrid/lectura.py` — política,
  excepción, `comprobar_truncado`, `con_paginacion`, `leer_paginado` (§5).
- `services/albaranes-comun/tests/test_f052_sigrid_lectura.py`
- `services/albaranes-persistencia/tests/doble_sigrid_api.py` — el doble (§7).
- `services/albaranes-persistencia/tests/test_f052_{resumen_obra,
  equivalencia_familias,truncado_cliente,nota_proveedor,rastro_busqueda}.py`
- `services/albaranes-persistencia/scripts/verificar_f052_proveedores_obra.py`
  (MANUAL, solo lectura: R29, R30). `services/albaranes-front/application/services/busqueda_contratos.py` (R27).
- `services/albaranes-front/tests/test_f052_{busqueda_contratos,lookup_truncado}.py`

**Modificar (sv3, `services/albaranes-persistencia/`)**
- `infrastructure/sigrid/sigrid_api_contrato_client.py` — `_post_sql_read`
  con `politica` obligatoria y `max_rows` opcional; `_post_sql_read_paginado`;
  las 7 consultas según §3; `fetch_contratos_resumen_por_obra` con la consulta
  agregada (§4); `transport` inyectable en `__init__` (solo para el doble; por
  defecto `httpx.HTTPTransport(retries=1)`, igual que hoy); `pagina_lineas`
  (1000) y `max_paginas` (20) como kwargs con valor por defecto (D3);
  docstring falso del «tope de 10.000 filas» corregido.
- `application/services/header_resolver_service.py` —
  `_mejor_candidato_por_nombre` devuelve `(candidato | None, motivo, n)` y
  sigue usando `fetch_contratos_resumen_por_obra`; `_red_proveedor_por_cif`
  redacta la nota por motivo (§6); `_resolver_por_obra_y_familia` registra
  WARNING con la obra si la consulta lanza `SigridRespuestaTruncada` (el
  degradado al fallback global ya existe). El puerto no cambia.
- `domain/ports/contrato_merge_repository_port.py`, `infrastructure/database/
  sqlalchemy_albaran_repository.py` — `sellar_busqueda_contratos(document_id, cif, obra, resultado)`.
- `application/services/contrato_enrichment_service.py` — sella el rastro en
  cada salida de `enrich_merge_document` (R21). El re-fetch de sv3
  (`contrato_refetch_service.py`) pasa por aquí: no se toca.
- `infrastructure/database/phase2_ddl.py` — 4 `ALTER ... ADD COLUMN IF NOT
  EXISTS` (§4). `infrastructure/database/orm_models.py` — las 4 columnas en
  `AlbaranDocumentMergeOrm`.

**Modificar (sv4, `services/albaranes-front/`)**
- `infrastructure/sigrid/sigrid_lookup_client.py` — `_post_sql_read` recibe
  `politica` y llama a `comprobar_truncado` (R28). Su SQL no cambia.
- `infrastructure/database/orm_models.py` — las 4 columnas (las escriben sv3 y
  el fallback local). `review_repository.py` — rellena `busqueda_contratos` en
  el detalle; `sellar_busqueda_contratos` para el fallback local.
- `infrastructure/sigrid/local_refetch_client.py` — sella el rastro (R22).
- `domain/models/review_models.py` — `BusquedaContratosVista` (estado, cif, obra,
  fecha, resultado) y campo `busqueda_contratos` en `DocumentDetailPayload`.
- `templates/document_detail.html` — bloque de contrato (`:375-401`): mensaje
  según `busqueda_contratos.estado` (R23–R26), también con contratos listados.

## 3. Política de cada consulta del cliente de contratos de sv3

| # | Método / etiqueta | Filas (medido) | Lectura | Política | Por qué |
|---|---|---|---|---|---|
| 1 | `fetch_contratos` / `header_and_lines` | líneas CIF+obra (máx. 989, 0668) | paginada, 1.000/pág. | NO_TOLERA | alimenta valoración y UPSERT por `sigrid_ide`: todas o ninguna |
| 2 | `search_proveedores` | 3.543 global (2026-09-29) | paginada, 5.000/pág. | NO_TOLERA | hoy se corta a 1.000 en silencio |
| 3 | `fetch_proveedor_by_cif` | 1 (`TOP 1`) | simple | NO_TOLERA | no puede truncar; se declara igual |
| 4 | `fetch_proveedores_por_obra` (grounding) | ≤ 193 | simple | NO_TOLERA | lista de candidatos de la 2ª IA |
| 5 | `fetch_contratos_resumen_por_obra` | ≤ 163 (agregada) | simple, una llamada | NO_TOLERA | truncado = candidatos parciales |
| 6 | `_fetch_gra_rep_ide` / `rcg_gra_for_ctr_*` | documentos de un contrato | simple | TOLERA | PDF best-effort; ya captura errores |
| 7 | `_resolve_rep_ide` / `gra_rep_for_cod_*` | 1 por `gra.cod` | simple | TOLERA | usa la primera fila válida |

Paginación (solo 1 y 2): `max_rows = página + 1` (sigrid-api marca `truncated`
al alcanzar `max_rows`; si aun así llega, es error); se sigue mientras la página
venga llena; tope `max_paginas` → `SigridRespuestaTruncada` (R13). Caso normal
de `header_and_lines`: una sola llamada, como hoy.

## 4. SQL (Sigrid, solo lectura; inline en el cliente, como todo el repo)

**Consulta agregada** (`_SQL_RESUMEN_OBRA_AGREGADO`, sv3): la de la exploración
§3 más dos `ORDER BY` internos para que texto y códigos sean deterministas (R5;
R30 revalida la medición con ellos):

```sql
WITH base AS (
    SELECT prv.cif AS cif, prv.raz AS raz, con_ctr.cod AS cod_ctr,
           con_ctr.res AS res_ctr, ctrpro.res AS res_lin, con_pro.cod AS cod_pro
    FROM ctr
    JOIN con AS con_ctr ON ctr.ide = con_ctr.ide
    JOIN con AS con_obr ON ctr.obride = con_obr.ide
    JOIN prv ON ctr.entide = prv.ide
    LEFT JOIN ctrpro ON ctrpro.docide = ctr.ide
    LEFT JOIN pro ON ctrpro.proide = pro.ide
    LEFT JOIN con AS con_pro ON pro.ide = con_pro.ide
    WHERE con_obr.cod = ? AND con_ctr.emp = 1
),
txt AS (
    SELECT DISTINCT b.cif, CAST(LTRIM(RTRIM(x.v)) AS NVARCHAR(MAX)) AS v
    FROM base b CROSS APPLY (VALUES (b.res_ctr), (b.res_lin), (b.cod_pro)) AS x(v)
    WHERE x.v IS NOT NULL AND LTRIM(RTRIM(x.v)) <> ''
),
ctrs AS (SELECT DISTINCT cif, cod_ctr FROM base)
SELECT p.cif, p.raz AS nombre,
       STUFF((SELECT '|' + c.cod_ctr FROM ctrs c WHERE c.cif = p.cif ORDER BY c.cod_ctr
              FOR XML PATH(''), TYPE).value('.', 'NVARCHAR(MAX)'), 1, 1, '') AS codigos_contratos,
       STUFF((SELECT ' ' + t.v FROM txt t WHERE t.cif = p.cif ORDER BY t.v
              FOR XML PATH(''), TYPE).value('.', 'NVARCHAR(MAX)'), 1, 1, '') AS texto
FROM (SELECT DISTINCT cif, raz FROM base) AS p
ORDER BY p.cif, p.raz
```

- `TYPE` + `.value(...)` devuelve el texto sin escapar (`&amp;` → `&`); el
  `CAST` resuelve las columnas `text`; `cod_pro` es inocuo y se mantiene.
- Python: dedupe por CIF (primera fila; un CIF con dos `raz` sale dos veces),
  `codigos_contratos` = `split('|')` sin vacíos, `texto` tal cual (`None` →
  `""`). Un proveedor sin líneas sigue siendo candidato.
- **Alternativa documentada, NO se implementa** (si apareciera el error de
  XML): Q1 `DISTINCT` cif + raz + contrato (≤ 193 filas, candidatos completos)
  y Q2 `SELECT DISTINCT prv.cif, ctrpro.res` (~3.000 filas; paginar; truncada
  solo perdería señal de familia). Detalle: exploración §3.

**`header_and_lines`**: `ORDER BY con_ctr.cod, ctr.ide, ctrpro.pos, ctrpro.ide`
+ `OFFSET/FETCH` (`con_paginacion`); `ctr.ide` desempata contratos sin líneas
con igual código. **`search_proveedores`**: `ORDER BY prv.cif, prv.raz`.

**DDL (PostgreSQL `albaranes`, sv3 dueño, `phase2_ddl.py`)**, todas nullable:
`contratos_busqueda_cif VARCHAR(64)`, `contratos_busqueda_obra VARCHAR(32)`,
`contratos_busqueda_resultado VARCHAR(16)`, `contratos_busqueda_at_utc
VARCHAR(64)` (fechas como texto ISO). Solo las lee sv4. Columna y no
`raw_extraction_json`: ese JSON es la extracción de la IA, no el enriquecimiento.

## 5. Clases y funciones

**`ruesma_comun.sigrid.lectura`** (puro, sin HTTP; usa el logger que recibe):
- `class PoliticaTruncado(Enum)`: `TOLERA`, `NO_TOLERA`.
- `class SigridRespuestaTruncada(RuntimeError)`: `etiqueta`, `filas`; los
  `except Exception` actuales la tratan como fallo de consulta (se quiere así).
- `comprobar_truncado(body: dict, *, politica, etiqueta: str, logger) -> None`.
- `con_paginacion(sql: str) -> str`: añade `OFFSET ? ROWS FETCH NEXT ? ROWS
  ONLY`; `ValueError` sin `ORDER BY`.
- `leer_paginado(leer_pagina: Callable[[int, int], tuple[list, list, bool]],
  *, pagina: int, max_paginas: int, etiqueta: str, politica, logger) ->
  tuple[list[str], list[list]]`: encadena páginas hasta una incompleta.

**sv3 · infrastructure** — `SigridApiContratoClient._post_sql_read(*, sql,
parameters, database, label, politica, max_rows=None)`;
`_post_sql_read_paginado(*, sql, parameters, database, label, politica,
pagina)`. **sv3 · application** —
`HeaderResolverService._mejor_candidato_por_nombre(...) ->
tuple[ProveedorObraResumen | None, str, int]` con motivo ∈ {`propuesta`,
`nadie_casa`, `sin_obra`, `sin_nombre`, `consulta_fallida`} y N candidatos.
**sv4 · application** — `estado_busqueda(cif_actual, obra_actual, rastro) ->
BusquedaContratosVista` con estado ∈ {`sin_rastro`, `vigente`, `desfasada`,
`error`, `sin_datos`}; CIF en mayúsculas sin espacios y obra con
`ruesma_comun.obras.normalizar_codigo_obra`, la de sv3 (CR-C1).

## 6. Notas de revisión (R15–R19)

Mismo prefijo `[AVISO] Proveedor` y mismo motivo `proveedor_cif_no_casa:<cif>`.
Solo cambia el texto tras «el CIF leído X no existe en Sigrid»:
`consulta_fallida` → «y no se pudo consultar la lista de proveedores de la
obra Y (fallo al consultar Sigrid): no hay propuesta»; `sin_obra` → «y no hay
obra válida con la que buscar candidatos»; `sin_nombre` → «y no se leyó nombre
de proveedor con el que comparar»; `nadie_casa` → «y ninguno de los N
proveedores con contrato en la obra Y casa con el nombre leído ('…')».

## 7. Tests (sin red ni BBDD)

**Doble de sigrid-api** (`tests/doble_sigrid_api.py`): `httpx.MockTransport`
que reconoce la SQL por un fragmento distintivo y sirve, desde **un único
fixture por líneas**, la consulta antigua, la agregada (calculada en Python con
su semántica: valores recortados, distintos y no vacíos; códigos por `|`) y
`header_and_lines`/`search_proveedores` con `OFFSET/FETCH`. Aplica `max_rows` y
`truncated` como el real; modo `error_xml` (`ok=false`, «FOR XML could not
serialize»). Fixture «0691»: 2.083 filas, 81 proveedores, semilla fija,
B82899550 tras la fila 1.000; con repetidas, espacios y vacíos (R4).

**Equivalencia (R4)**, `test_f052_equivalencia_familias.py`: para cada CIF del
fixture, `familias_de_texto` del texto que devuelve el cliente sobre la vía
agregada == el del texto por líneas (reconstruido en el test igual que el
código de hoy: campos no vacíos concatenados por línea). Más tres casos
dirigidos: duplicados, orden invertido y valores con espacios. Esto fija la
semántica en Python; que la SQL real la cumple lo prueba R30 (MANUAL).

Fase RED obligatoria (rigor crítico), contra el código actual:
- R1: la red por nombre sobre el doble no propone B82899550 (hoy `None`).
- R2/R3: obra + familia ve 81 candidatos en una llamada (hoy menos de 81).
- R6/R15: con `error_xml`, nota «no se pudo consultar» (hoy «ningún … casa»).
- R8/R11/R12: `truncated=true` no lanza; `fetch_contratos` y
  `search_proveedores` se quedan en 1.000.
- R24 (sv4): la traza válida es el test de plantilla, que hoy pinta el CIF actual.

R4 hoy es RED por truncado (los CIF más allá de la fila 1.000 llegan sin texto).
Además, una mutación del cliente (leer `nombre` en vez de `texto`) debe
matarla. Nombres `test_f052_rN_*`; el `ORDER BY` se comprueba en la SQL que
recibe el doble y el determinismo (R5) con tres barajados.

## 8. Saneamiento de lo ya procesado (solo lectura; decisión D5)

Dos pasos de solo lectura. (1) Obras afectadas: las 74 de más de 1.000 líneas
en la consulta antigua; el script de T14 las recalcula con
`--listar-obras-grandes` (sigrid-api, `GROUP BY con_obr.cod HAVING COUNT(*) >
1000`). (2) En la BBDD `albaranes`, el SELECT de sospechosos (`nadie_casa`,
`det_familia_obra` y «sin CIF: no deducible» de esas obras), que vive en
`progress/spec_F-052.md` §Anexo. Límite: el atajo por nombre en la obra sella
`deterministic` y no se distingue del fallback global; si el revisor editó la
nota, el documento no sale. Saneo por documento en sv4, sin backfill (F-043).

## 9. Despliegue

`ruesma_comun` gana un módulo que solo importan sv3 y sv4 (sv2, sv5 y sv6 no se
reconstruyen). **Orden: sv3 → sv4**: sv3 aplica el DDL al arrancar y un sv4
nuevo sin las columnas falla al leer el merge. Lo lanza el humano:
`.\deploy.ps1 -Only sv3`, `.\check_deploy.ps1`, `-Only sv4`. Rollback al revés.

## 10. Riesgos

- **Rendimiento**: la agregada tarda hasta 5 s (0695; la de más filas, 0696,
  3,7 s) frente al `timeout_s` de 30 s y el corte de 230 s del balanceador. Se
  ejecuta una vez por albarán sin CIF o con CIF inexistente. El script manual
  registra el tiempo; si pasara de 15 s, se abre feature para cachear.
- **sigrid-api o su validador dejan de aceptar `WITH` o `FOR XML`**: la
  consulta falla en todas las obras. Efecto acotado y visible (R6): nota
  «no se pudo consultar», fallback global por nombre y `logger.exception`. La
  salida es la alternativa Q1/Q2 de §4. `azure-apps/albaranes.md` lo anota
  como dependencia (T16).
- **Carácter de control no válido en XML** en una descripción: misma
  degradación (R6). No ha ocurrido en las 74 obras. Truncado en
  `fetch_contratos` → sin contratos nuevos, rastro `error` visible (R25).
- **Cambio de deducción** (D7): solo en las 74 obras grandes; en el resto el
  texto da las mismas familias (R4) y la lista ya estaba completa.

## 11. Qué NO se toca y fuera de alcance

- El **CIF mal leído por IA1** (B82890580 frente a B82899550): otro problema.
  `_score_razon_social`, `_match_score`, umbrales, puntos, `familia_detector.py`,
  `familias.py` y prompts; sv5 y sv6 no leen nada de lo que cambia.
- `ProveedorReverseLookupClient` (puerto) y `fetch_proveedores_por_obra` de sv3
  salvo su política (fila 4); `config/settings.py` y raíces de composición (D3).
- `SigridApiObraClient` de sv3 y el `SigridApiContratoClient` de sv4 (fallback solo-front, copia de `header_and_lines` con `max_rows=1000`): ver D6.
- `static/app.js`: los dos botones de re-búsqueda se reutilizan; D4-A aceptada (2026-09-30): «Guardar» relanza la búsqueda si cambian CIF u obra (T13 bis).
  Humano, 2026-10-01: (1) sin rastro, el primer «Guardar» busca una vez (O-C1); (2) una sola normalización de obra, la de sv3, en `ruesma_comun.obras` (CR-C1).

## 12. Decisiones abiertas (D1–D7, con recomendación: `progress/spec_F-052.md` §v2)
