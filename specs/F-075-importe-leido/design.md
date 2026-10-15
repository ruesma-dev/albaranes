# F-075 · La bandeja y la ficha muestran el importe leído del albarán — diseño

Servicio: **sv4-front** (solo). Rigor `estandar`. Requisitos: `requirements.md`. Preguntas abiertas
y recomendación: `progress/spec_F-075.md` §4. Este diseño implementa las recomendaciones (P1 a
P7); si el humano decide otra cosa en la PARADA 1, se rehace la parte afectada antes de implementar.

## 1. Encaje y límite de servicio

- El dato **ya está persistido y es utilizable**: `albaran_lines_merge.precio_neto` (dueño: sv3,
  lo escribe al guardar el merge; ARCHITECTURE §1 y §13). sv4 lo lee con SQL de solo lectura, igual
  que ya lee el merge y la valoración. **No hace falta que ningún servicio guarde nada nuevo.**
- Todo es presentación de sv4: sin DDL, sin cambio de contratos de cola, sin endpoints nuevos.
  `azure-apps/albaranes.md` no cambia (no varía lo que se expone ni lo que se consume).
- Leer del papel el **total con IVA o la base imponible** sí sería responsabilidad de sv2 (prompt +
  `CabeceraAlbaran`) y sv3 (columnas del merge, DDL, lectores). Queda fuera (P2); si se quiere, es
  una feature aparte de sv2+sv3, y esta columna podría compararse después con esa cifra.

## 2. Ficheros a crear

| Ruta | Qué |
|---|---|
| `services/albaranes-front/domain/services/importe_albaran.py` | Value object y funciones puras (§4). Dominio, sin dependencias. |
| `services/albaranes-front/tests/f075_bbdd.py` | SQLite en memoria (patrón de `f053_sv4_bbdd.py`): 4 documentos tipo (§7). |
| `services/albaranes-front/tests/test_f075_importe_albaran.py` | Dominio: R1–R4. |
| `services/albaranes-front/tests/test_f075_bandeja.py` | Repositorio + plantilla de la bandeja + rutas: R6–R13. |
| `services/albaranes-front/tests/test_f075_ficha.py` | Payload del detalle + plantilla de la ficha: R4, R14–R17. |
| `services/albaranes-front/tests/test_f075_vistas.py` | Obras y Proveedores: R18–R20. |

## 3. Ficheros a modificar

| Ruta | Cambio |
|---|---|
| `domain/models/review_models.py` | `DocumentListItem.importe_albaran: ImporteAlbaran \| None` y `computed_field` `importe_difiere`; `DocumentListFilters`: `min_importe_albaran`, `max_importe_albaran` y `"importe_albaran"` en `validate_sort_by`; `PaginatedDocuments.importe_albaran_pendiente: float = 0.0`; `ObraResumenItem` y `ProveedorResumenItem`: `importe_albaran: float = 0.0`, `sin_importe: int = 0`; `DocumentDetailPayload.importe_albaran: ImporteAlbaran \| None`; `aviso_suma_importes` pasa a usar `difieren` (R4). |
| `infrastructure/database/review_repository.py` | §5: consulta por lotes en `list_documents`, tarjeta, `_apply_sort`, `_apply_filters`, `list_obras_resumen`, `list_proveedores_resumen`, detalle del merge (`suma_leida` e `importe_albaran` desde la misma función). |
| `interface_adapters/web/app.py` | `documents_list`: `min_importe_albaran`/`max_importe_albaran` (`Query`, `_parse_optional_float`); `_filters_from_query`: los dos con `_f`. `_query_string` ya los arrastra (usa `model_dump`). |
| `templates/documents_list.html` | Columna `data-col="importe_albaran"` tras `importe` (cabecera ordenable, filtro mín/máx, celda §6); tarjetas §6; `colspan` de la fila vacía 13/12. |
| `templates/document_detail.html` | Bloque §6 (vista merge) y pie de «Líneas leídas del albarán (IA)». |
| `templates/obras_list.html`, `templates/proveedores_list.html` | Columna «Importe albarán» tras «Importe valorado». |
| `static/styles.css` | `.importe-difiere` (marca ≠), `.importe-parcial` (nota pequeña), `.importe-albaran-bloque`. Sin JS nuevo. |
| `docs/ARCHITECTURE.md` | §13: una frase: «el importe del albarán que pinta sv4 es la suma de `precio_neto` del merge, sin IVA; IA1 no lee totales de cabecera». |
| `services/albaranes-front/sv4.md` | Bandeja, ficha y vistas: la columna nueva y su criterio. |

## 4. Dominio: `domain/services/importe_albaran.py`

```python
class ImporteAlbaran(BaseModel):          # frozen
    total: float | None                   # None si ninguna línea trae importe (R2)
    lineas: int                           # líneas del merge
    lineas_con_importe: int
    # computed: lineas_sin_importe, parcial (0 < con < lineas), sin_importe (con == 0)

def importe_albaran(importes: Iterable[float | None]) -> ImporteAlbaran   # R1–R3, desde Python
def desde_agregado(total, lineas, con_importe) -> ImporteAlbaran | None   # desde la fila SQL (§5)
def difieren(valorado: float | None, albaran: float | None) -> bool        # umbral 0,01 (R8, R4)
def diferencia(valorado: float, albaran: float) -> float                  # valorado − albarán
```

- `importe_albaran` ignora `None`, suma con signo, no redondea; `NaN`/infinito no se espera (el
  merge lo guarda sv3 como `Float`), pero si llegara se trata como «sin importe» y no suma.
- `difieren` reproduce exactamente la regla actual de `aviso_suma_importes`
  (`round(abs(a − b), 2) >= 0.01`), que pasa a llamarla: un solo umbral.
- `desde_agregado` devuelve `None` si `lineas == 0` (el documento no tiene líneas) y normaliza
  `SUM` nulo a `total=None`.

## 5. Consultas (sv4, solo SELECT; SQL portable PostgreSQL/SQLite)

**Bandeja, por lotes** (`list_documents`, junto a las consultas existentes de la página; mismo
`try/except` + `rollback` + log que las demás, R13):

```sql
SELECT l.document_id, COUNT(*) AS lineas, COUNT(l.precio_neto) AS con_importe,
       SUM(l.precio_neto) AS total
FROM albaran_lines_merge l WHERE l.document_id IN :ids GROUP BY l.document_id
```
Usa el índice existente de `albaran_lines_merge.document_id`. Las líneas del merge son una sola
fila por línea (las de cada proveedor IA viven en `albaran_lines`, que no se toca).

**Expresión correlacionada** (helper estático `_expr_importe_albaran()`, la usan orden y filtro):
`select(func.sum(AlbaranLineMergeOrm.precio_neto)).where(AlbaranLineMergeOrm.document_id ==
AlbaranDocumentMergeOrm.id).correlate(AlbaranDocumentMergeOrm).scalar_subquery()`.
- `_apply_sort`: `"importe_albaran"` → esa expresión con `nullslast`, desempate actual. Como
  `get_neighbor_ids` ya usa `_apply_sort`/`_apply_filters`, R9 y R11 salen gratis.
- `_apply_filters`: `expr >= :min` / `expr <= :max`; con nulo la comparación es falsa y el documento
  queda fuera (R10).

**Tarjetas**: la actual pasa de `DISTINCT ON` (solo PostgreSQL) a la forma portable
`v.id = (SELECT MAX(av.id) FROM albaran_valuations av WHERE av.document_id = d.id)`; la nueva:
```sql
SELECT COALESCE(SUM(l.precio_neto), 0) FROM albaran_lines_merge l
JOIN albaran_documents_merge d ON d.id = l.document_id
WHERE d.is_active = TRUE AND d.approved = FALSE
```

**Obras / Proveedores**: el `LEFT JOIN LATERAL (… ORDER BY av.id DESC LIMIT 1)` pasa a
`LEFT JOIN albaran_valuations v ON v.id = (SELECT MAX(av.id) …)` (mismo resultado: `id` es la clave
primaria, así que «el mayor» y «el primero en orden descendente» son la misma fila; R20), y se añade
```sql
LEFT JOIN (SELECT document_id, SUM(precio_neto) AS imp FROM albaran_lines_merge
           GROUP BY document_id) la ON la.document_id = d.id
-- en el SELECT:
COALESCE(SUM(la.imp), 0) AS importe_albaran,
COUNT(*) FILTER (WHERE la.imp IS NULL) AS sin_importe
```
Ambos joins dan como mucho una fila por documento: los recuentos actuales no cambian. `FILTER` ya
se usa en esas consultas y SQLite ≥ 3.30 lo admite.

**Detalle del merge**: `importes_leidos` se sustituye por `importe_albaran([m.precio_neto for m in
merge_lines_payload])`; `suma_leida = importe.total` (R4) e `importe_albaran = importe` en el payload.
Si el documento no tiene líneas, `importe_albaran = None` y el bloque pinta «—».

## 6. Presentación

- **Bandeja**: cabecera «Importe albarán» con subtítulo pequeño «sin IVA · leído», enlace de orden
  (`build_sort_query('importe_albaran')`). Celda: `importe_eur` del total; si `parcial`, debajo
  `<span class="importe-parcial">N de M sin importe</span>`; si `sin_importe` o `None`, «—» con
  `title="El albarán no trae importes"`. Si `item.importe_difiere`, `<span class="importe-difiere"
  title="Valorado X · Albarán Y · Diferencia Z">≠</span>`. Filtro mín/máx con el mismo marcado que
  el de importe valorado.
- **Tarjetas**: «Pendiente valorado» (la de hoy, solo cambia el rótulo) y «Pendiente según albarán».
- **Ficha**: tras el banner de valoración (y también sin él), en vista merge:
  `<div class="importe-albaran-bloque">Importe del albarán (sin IVA, leído): <strong>X</strong>`
  + parcial; con valoración: `· Total valorado Y · Diferencia Z` y la marca si difieren.
  En «Líneas leídas del albarán (IA)», `<tfoot>` con «Total leído (sin IVA)».
- **Obras / Proveedores**: celda `importe_eur(importe_albaran)` y, si `sin_importe`, debajo
  `<div class="muted small">N sin importe</div>`.
- **Columna nueva y orden guardado**: `movableOrder()` (app.js) añade al final las columnas que no
  conoce; quien tenga un orden guardado en `sv4.listCols` verá «Importe albarán» al final de la fila
  hasta que la arrastre. Se acepta (P7): no se toca app.js.

## 7. Tests (sin red ni BBDD real; SQLite en memoria y plantillas reales)

`f075_bbdd.py` construye: **A** «DISCOIN» sin valoración, 2 líneas con `precio_neto` (100,00 y
45,50); **B** con valoración `ok` 145,50 y líneas que suman 145,50 (no difieren); **C** con valoración
200,00 y líneas 120,00 + `NULL` (parcial, difieren); **D** sin líneas con importe (todas `NULL`);
**E** en la papelera. Nombres `test_f075_rN_…`:

- Dominio: suma con signo, `None` ignorados, todo nulo ⇒ `None`, parcial, `difieren` en 0,004 /
  0,005 / 0,01 / ausente; `aviso_suma_importes` usa `difieren` (mismo resultado que hoy).
- Bandeja: `list_documents` devuelve A=145,50 sin valoración, D=`None`, C parcial y `importe_difiere`;
  orden asc/desc con D al final; filtros mín/máx excluyen D; tarjeta nueva = suma de pendientes
  activos (sin E); forzando que falle solo la consulta de §5 (doble de sesión que lanza en ella), la
  bandeja sigue con «—» y tarjeta 0 (R13).
  Render de `documents_list.html` (entorno Jinja de `conftest`, ampliado con `build_sort_query`):
  columna, «—» con su texto, nota de parcial, marca ≠ con su `title`, tarjetas, papelera.
  Rutas con `TestClient` y servicio falso: 422 con `min_importe_albaran=abc`; filtros y orden en
  `current_query`; `_filters_from_query` tolerante.
- Ficha: payload de A sin valoración con bloque; C con diferencia; `suma_leida == importe.total`;
  render con `render_detalle`: bloque, pie de tabla, sin bloque en vista de proveedor.
- Vistas: Obras y Proveedores con importe del albarán y `sin_importe`; `importe_valorado` idéntico al
  de un cálculo de referencia en Python (última valoración por documento, R20).

## 8. Ficheros que NO se tocan

- sv2 (`config/prompts.yaml`, `domain/models/albaran_models.py`): IA1 sigue sin leer totales.
- sv3 (ORM, `phase2_ddl.py`, normalizador): el esquema ya tiene `precio_neto`.
- sv5, sv6, sv9 y `services/albaranes-comun` (incluido `ruesma_comun.importes`: no se recalcula nada).
- `static/app.js` (P7), las rutas de edición y guardado de sv4, `esta_valorado`, el cálculo de
  `suma_filas` y `total_valorado`.
- La columna «Líneas valoradas» de la bandeja (P4).

## 9. Riesgos y decisiones

- **D1 Añadir, no sustituir** (P1): el valorado es lo que va a Sigrid (F-053); quitarlo escondería
  la comparación que el humano quiere ver. Alternativa descartada: una sola columna «Importe» que
  cambie de origen según haya contrato (mezcla dos cifras con el mismo rótulo).
- **D2 Solo `precio_neto`** (P3): completar en sv4 `cantidad × precio` duplicaría en SQL la fórmula
  que vive en `ruesma_comun.importes` (ARCHITECTURE §13) y la IA ya la aplica al leer. Riesgo: una
  línea con precio y sin importe no suma; queda a la vista como «parcial».
- **D3 Sin IVA** (P2): es lo que se lee hoy; se rotula siempre «sin IVA» para que nadie lo compare
  con el total con IVA impreso al pie del albarán.
- **D4 SQL portable**: reescribir `LATERAL`/`DISTINCT ON` permite probar las cifras sobre SQLite.
  Riesgo: cambiar una consulta que hoy funciona; mitigación: test de equivalencia (R20) y misma
  semántica (clave primaria única).
- **D5 Rendimiento**: la página añade una consulta agrupada sobre ≤ 100 documentos (indexada); orden
  y filtro usan subconsulta correlacionada por documento activo (miles de filas): aceptable. Si
  algún día pesa, F-0XX podría guardar el total en el merge (sv3, DDL).
- **D6 Lo que dice el papel no siempre es «leído»**: si el papel no trae el importe de la línea, la
  IA lo calcula con lo leído (prompt de IA1). Se acepta y se explica en el `title` de la cabecera.
- Despliegue: solo sv4, sin orden con otros servicios.
