<!-- specs/F-052-proveedores-truncados/design.md -->
# F-052 · Diseño técnico

## 1. Encaje y límite de servicio

Ninguna responsabilidad nueva: sv3 resuelve la cabecera, busca contratos y
es dueño del schema; sv4 es el front. Lo compartido (truncado y paginación,
lógica pura) va a `ruesma_comun`. Sigrid: solo lectura vía `/api/sql/read`.

**El corte de 1.000 NO es de sigrid-api** (la instancia `dev` admite 500.000,
`azure-apps/sigrid_api.md` §4.1): es el `max_rows` por defecto del cliente de
sv3. Paginar con `OFFSET/FETCH` es obligatorio (§6.4, corte a 230 s) y Sigrid
es SQL Server 2012: no hay `STRING_AGG`.

## 2. Ficheros

**Crear**
- `services/albaranes-comun/ruesma_comun/sigrid/__init__.py`
- `services/albaranes-comun/ruesma_comun/sigrid/lectura.py` — política,
  excepción, `comprobar_truncado`, `con_paginacion`, `leer_paginado` (§5).
- `services/albaranes-comun/ruesma_comun/sigrid/consultas.py` —
  `SQL_PROVEEDORES_POR_OBRA` (la de sv4, `DISTINCT` + `ORDER BY prv.raz`).
- `services/albaranes-comun/tests/test_f052_sigrid_lectura.py`
- `services/albaranes-persistencia/tests/doble_sigrid_api.py` — el doble (§7).
- `services/albaranes-persistencia/tests/test_f052_{proveedores_obra,
  truncado_cliente,nota_proveedor,rastro_busqueda}.py`
- `services/albaranes-persistencia/scripts/verificar_f052_proveedores_obra.py`
  — verificación MANUAL de solo lectura (R28); `print` permitido (script).
- `services/albaranes-front/application/services/busqueda_contratos.py` —
  `estado_busqueda` (R25).
- `services/albaranes-front/tests/test_f052_{busqueda_contratos,lookup_truncado}.py`

**Modificar (sv3, `services/albaranes-persistencia/`)**
- `infrastructure/sigrid/sigrid_api_contrato_client.py` — `_post_sql_read`
  con `politica` obligatoria y `max_rows` opcional; `_post_sql_read_paginado`;
  las 7 consultas según §3; `fetch_contratos_resumen_por_obra` rehecha (§4);
  `transport` inyectable en `__init__` (solo para el doble; por defecto
  `httpx.HTTPTransport(retries=1)`, igual que hoy); docstring falso del «tope
  de 10.000 filas» corregido.
- `application/services/header_resolver_service.py` —
  `_mejor_candidato_por_nombre` usa `fetch_proveedores_por_obra` y devuelve
  `(candidato | None, motivo)`; `_red_proveedor_por_cif` redacta la nota por
  motivo (§6); `_resolver_por_obra_y_familia` registra WARNING si la consulta
  lanza `SigridRespuestaTruncada` (el degradado ya existe).
- `domain/ports/header_resolver_ports.py` — `fetch_proveedores_por_obra` en
  `ProveedorReverseLookupClient`.
- `domain/ports/contrato_merge_repository_port.py` y
  `infrastructure/database/sqlalchemy_albaran_repository.py` —
  `sellar_busqueda_contratos(document_id, cif, obra, resultado)`.
- `application/services/contrato_enrichment_service.py` — sella el rastro en
  cada salida de `enrich_merge_document` (R19). El re-fetch de sv3
  (`contrato_refetch_service.py`) pasa por aquí: no se toca.
- `infrastructure/database/phase2_ddl.py` — 4 `ALTER ... ADD COLUMN IF NOT
  EXISTS` (§4). `infrastructure/database/orm_models.py` — las 4 columnas en
  `AlbaranDocumentMergeOrm`.
- `config/settings.py` — `SIGRID_API_PAGINA_FILAS` (5000) y
  `SIGRID_API_MAX_PAGINAS` (20); `interface_adapters/composition.py` e
  `interface_adapters/api/app.py` los pasan al cliente (las dos raíces de
  composición que lo instancian).

**Modificar (sv4, `services/albaranes-front/`)**
- `infrastructure/sigrid/sigrid_lookup_client.py` — `_SQL_PROVEEDORES_POR_OBRA`
  sale de `ruesma_comun.sigrid.consultas`; `_post_sql_read` recibe `politica`
  y llama a `comprobar_truncado` (R27).
- `infrastructure/database/orm_models.py` — las 4 columnas (solo lectura
  desde el front; las escribe sv3 y el fallback local).
- `infrastructure/database/review_repository.py` — rellena
  `busqueda_contratos` en el detalle; `sellar_busqueda_contratos` para el
  fallback local.
- `infrastructure/sigrid/local_refetch_client.py` — sella el rastro (R20).
- `domain/models/review_models.py` — `BusquedaContratosVista` (estado, cif,
  obra, fecha, resultado) y campo `busqueda_contratos` en
  `DocumentDetailPayload`.
- `templates/document_detail.html` — bloque de contrato (`:375-401`): mensaje
  según `busqueda_contratos.estado` (R21–R24) y aviso de desfase también sobre
  la lista de contratos (R22).

## 3. Política de truncado de cada consulta del cliente de contratos de sv3

| # | Método / etiqueta | Filas esperadas | Lectura | Política | Por qué |
|---|---|---|---|---|---|
| 1 | `fetch_contratos` / `header_and_lines` | líneas de CIF+obra (máx. hoy 989, obra 0668) | paginada | NO_TOLERA | perder líneas de contrato valora mal en silencio |
| 2 | `search_proveedores` | proveedores emp=1 de todo Sigrid (sin medir) | paginada | NO_TOLERA | su `max_rows=5000` se ignora hoy; un fallback por nombre sobre lista parcial elige mal |
| 3 | `fetch_proveedor_by_cif` | 1 (`TOP 1`) | simple | NO_TOLERA | no puede truncar; se declara igual |
| 4 | `fetch_proveedores_por_obra` | ~100 por obra (0691: 81) | simple, `max_rows=5000` | NO_TOLERA | es la lista de candidatos: parcial = el defecto |
| 5 | `fetch_contratos_resumen_por_obra` (texto de familia) | líneas de la obra (0691: 2.083) | paginada | NO_TOLERA | familia parcial puntúa mal |
| 6 | `_fetch_gra_rep_ide` / `rcg_gra_for_ctr_*` | documentos de un contrato | simple | TOLERA | PDF best-effort; ya captura errores |
| 7 | `_resolve_rep_ide` / `gra_rep_for_cod_*` | 1 por `gra.cod` | simple | TOLERA | usa la primera fila válida |

Paginación: `max_rows = pagina + 1` por página, para que una página llena no
llegue marcada `truncated` (sigrid-api lo marca al alcanzar `max_rows`); si
aun así llega, es un error. Tope: `SIGRID_API_MAX_PAGINAS` × `PAGINA_FILAS`
(100.000 filas) → `SigridRespuestaTruncada`.

## 4. SQL (Sigrid, solo lectura; ningún fichero `.sql`: inline, como todo el repo)

- **Lista de proveedores de la obra** (`ruesma_comun.sigrid.consultas`): la
  actual de sv4 (`DISTINCT prv.cif, prv.raz`, joins `ctr`/`con_ctr`/`con_obr`/
  `prv`, `con_obr.cod = ?`, `con_ctr.emp = 1`, `ORDER BY prv.raz`). sv3 la
  usa en `fetch_proveedores_por_obra` en lugar de su copia sin `ORDER BY`.
- **Texto de familia** (nueva, sv3): mismas columnas y joins que la actual de
  `fetch_contratos_resumen_por_obra` (`:825-840`) + `ORDER BY ctr.ide,
  ctrpro.ide` + `OFFSET ? ROWS FETCH NEXT ? ROWS ONLY`. Sin `DISTINCT`:
  `con_ctr.res` es `text` y SQL Server no lo admite (lo documenta sv4).
- `fetch_contratos_resumen_por_obra` = lista (4) + texto (5): construye un
  `ProveedorObraResumen` **por cada proveedor de la lista**, con el texto que
  le toque (vacío si no tiene líneas). El candidato ya no depende del texto.
- `header_and_lines`: `ORDER BY con_ctr.cod, ctr.ide, ctrpro.pos, ctrpro.ide`
  (desempate estable para paginar; conserva el orden de agrupado actual).
- `search_proveedores`: `ORDER BY prv.cif, prv.raz` (válido con `DISTINCT`).

**DDL (PostgreSQL `albaranes`, sv3 dueño, `phase2_ddl.py`)**, todas nullable:
`contratos_busqueda_cif VARCHAR(64)`, `contratos_busqueda_obra VARCHAR(32)`,
`contratos_busqueda_resultado VARCHAR(16)`, `contratos_busqueda_at_utc
VARCHAR(64)` (el schema guarda las fechas como texto ISO). Lectores: sv4 (ORM
propio, las declara) y nadie más; sv5 no las lee, así que su SQL crudo no se
ve afectado. Se elige columna y no `raw_extraction_json`: ese JSON es la
extracción de la IA, no el estado del enriquecimiento, y sv4 tendría que
parsearlo para pintar un bloque.

## 5. Clases y funciones

**`ruesma_comun.sigrid.lectura`** (puro, sin HTTP ni logging propio salvo el
logger que recibe):
- `class PoliticaTruncado(Enum)`: `TOLERA`, `NO_TOLERA`.
- `class SigridRespuestaTruncada(RuntimeError)`: `etiqueta`, `filas`. Hereda
  de `RuntimeError` para que los `except Exception` actuales la traten como
  fallo de consulta (es lo que se quiere).
- `comprobar_truncado(body: dict, *, politica, etiqueta: str, logger) -> None`.
- `con_paginacion(sql: str) -> str`: añade `OFFSET ? ROWS FETCH NEXT ? ROWS
  ONLY`; `ValueError` sin `ORDER BY`.
- `leer_paginado(leer_pagina: Callable[[int, int], tuple[list, list, bool]],
  *, pagina: int, max_paginas: int, etiqueta: str, politica, logger) ->
  tuple[list[str], list[list]]`: encadena páginas hasta una incompleta.

**sv3 · infrastructure** — `SigridApiContratoClient._post_sql_read(*, sql,
parameters, database, label, politica, max_rows=None)`;
`_post_sql_read_paginado(*, sql, parameters, database, label, politica)`.
**sv3 · application** — `HeaderResolverService._mejor_candidato_por_nombre
(...) -> tuple[tuple[str, str | None] | None, str]` con motivo ∈ {`propuesta`,
`nadie_casa`, `sin_obra`, `sin_nombre`, `consulta_fallida`} y el número de
candidatos para la nota. **sv4 · application** — `estado_busqueda(cif_actual,
obra_actual, rastro) -> BusquedaContratosVista` con estado ∈ {`sin_rastro`,
`vigente`, `desfasada`, `error`, `sin_datos`}; compara CIF en mayúsculas sin
espacios y obra con `normalize_obra_code` de sv4.

## 6. Notas de revisión (R13–R17)

Mismo prefijo `[AVISO] Proveedor` y mismo motivo `proveedor_cif_no_casa:<cif>`.
Solo cambia el texto tras «el CIF leído X no existe en Sigrid»:
`consulta_fallida` → «y no se pudo consultar la lista de proveedores de la
obra Y (fallo al consultar Sigrid): no hay propuesta»; `sin_obra` → «y no hay
obra válida con la que buscar candidatos»; `sin_nombre` → «y no se leyó nombre
de proveedor con el que comparar»; `nadie_casa` → «y ninguno de los N
proveedores con contrato en la obra Y casa con el nombre leído ('…')».

## 7. Tests (sin red ni BBDD)

**Doble de sigrid-api** (`tests/doble_sigrid_api.py`): `httpx.MockTransport`
con un manejador que recibe tablas por SQL reconocida (por un fragmento
distintivo), aplica `max_rows` y los dos últimos parámetros de `OFFSET/FETCH`
cuando la SQL los lleva, y devuelve `{ok, columns, rows, row_count,
truncated}` como el real. Fixture de la obra «0691»: 2.083 filas de 81
proveedores, barajadas con semilla fija, con las 5 de B82899550 **más allá de
la fila 1.000** en el orden de la consulta antigua.

Fase RED obligatoria (rigor crítico), contra el código actual:
- R1: la red por nombre con el cliente real sobre el doble no propone
  B82899550 → hoy falla (propone `None`).
- R2: el paso obra + familia ve 81 candidatos → hoy ve menos de 81.
- R7/R10/R11: `truncated=true` no lanza; `search_proveedores` y
  `fetch_contratos` se quedan en 1.000 → hoy fallan.
- R22 (sv4): `estado_busqueda` no existe → falla por importación; la traza
  válida es la del test de plantilla que hoy pinta el CIF actual.

Nombres `test_f052_rN_*`; el `ORDER BY` se comprueba en la SQL que recibe el
doble y el determinismo (R5) con tres barajados distintos.

## 8. Saneamiento de lo ya procesado (solo lectura; decisión D5)

Detección en dos pasos. Primero, sigrid-api (`sql/read`, solo lectura), las
obras cuya consulta antigua pasa de 1.000 filas:

```sql
SELECT con_obr.cod AS obra, COUNT(*) AS filas
FROM ctr JOIN con AS con_ctr ON ctr.ide = con_ctr.ide
JOIN con AS con_obr ON ctr.obride = con_obr.ide
JOIN prv ON ctr.entide = prv.ide LEFT JOIN ctrpro ON ctrpro.docide = ctr.ide
WHERE con_ctr.emp = 1 GROUP BY con_obr.cod HAVING COUNT(*) > 1000
ORDER BY filas DESC
```

Después, en la BBDD `albaranes` (solo SELECT), los sospechosos:

```sql
SELECT d.id, d.source_filename, d.numero_albaran, d.obra_codigo,
       d.proveedor_cif, d.proveedor_cif_origen, d.approved, d.created_at_utc,
       CASE WHEN d.review_notes ILIKE '%ningun proveedor con contrato en la obra casa%' THEN 'nadie_casa'
            WHEN d.proveedor_cif_origen = 'det_familia_obra' THEN 'familia_obra'
            WHEN d.review_notes ILIKE '%sin CIF: no deducible con seguridad%' THEN 'sin_cif_ambiguo'
       END AS sospecha
FROM albaran_documents_merge d
WHERE d.is_active
  AND ( d.review_notes ILIKE '%ningun proveedor con contrato en la obra casa%'
     OR ( d.obra_codigo = ANY(:obras_grandes)
          AND ( d.proveedor_cif_origen = 'det_familia_obra'
             OR d.review_notes ILIKE '%sin CIF: no deducible con seguridad%')))
ORDER BY sospecha, d.created_at_utc;
```

`:obras_grandes` = la lista del primer paso. Límite conocido: el atajo por
nombre dentro de la obra sella `deterministic`, igual que el fallback global,
y no se distingue; y si el revisor ya editó la nota, el documento no sale.
Saneo propuesto: por documento, en sv4 (corregir proveedor → «Guardar y volver
a buscar» → contrato → revalorar), sin backfill, como decidió el humano en F-043.

## 9. Despliegue

`ruesma_comun` gana un módulo que solo importan sv3 y sv4: sv2, sv5 y sv6 no
cambian de comportamiento y no necesitan reconstruirse por esta feature.
**Orden: sv3 → sv4.** sv3 aplica el DDL al arrancar; un sv4 nuevo contra una
base sin las 4 columnas falla al leer el merge (mismo aviso que F-043). Lo
lanza el humano: `.\deploy.ps1 -Only sv3`, `.\check_deploy.ps1`, `-Only sv4`.
Rollback al revés; las columnas quedan (nullable, inocuas).

## 10. Riesgos

- **El proveedor elegido puede cambiar** en albaranes que hoy «aciertan» por
  azar: con la lista completa, el paso obra + familia ve más candidatos, el
  margen sobre el segundo se estrecha y habrá **menos** deducciones
  `det_familia_obra` y más avisos «no deducible». Es conservador (va a
  revisión, no elige mal), pero subirá la carga del revisor en obras grandes.
- Solo afecta a lo que se procese o re-busque tras desplegar: el resolver no
  toca un CIF ya presente. Más llamadas a sigrid-api (una por página; 0691:
  2 en total), cada una con el `timeout_s` actual de 30 s.
- Truncado en `fetch_contratos` → sin contratos nuevos, rastro `error`, visible (R23).

## 11. Qué NO se toca y fuera de alcance

- El **CIF mal leído por IA1** (B82890580 frente a B82899550): otro problema;
  la red por nombre existe precisamente para cubrirlo.
- `_score_razon_social`, `_match_score`, umbrales y puntos: el matching es
  correcto (score 1,0). sv5 y sv6 no leen nada de lo que cambia.
- `SigridApiObraClient` de sv3 (`search_obras`, `fetch_obra_by_codigo`) y el
  `SigridApiContratoClient` de sv4 (fallback solo-front, copia de
  `header_and_lines` con `max_rows=1000`): mismo patrón, fuera; ver D6.
- `static/app.js`: los dos botones de re-búsqueda se reutilizan (salvo D4-A).
- `familia_detector.py`, `familias.py`, prompts: ninguna ruta sensible.

## 12. Decisiones abiertas (D1–D7, con recomendación: `progress/spec_F-052.md`)
