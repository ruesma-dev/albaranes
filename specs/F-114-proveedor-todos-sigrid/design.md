<!-- specs/F-114-proveedor-todos-sigrid/design.md -->
# F-114 · Diseño (v1)

Servicio único: **sv4**. Sin DDL, sin cambios en `ruesma_comun`, sin escritura en Sigrid. Encaja en la
capa hexagonal de sv4 como un lookup de solo lectura más del `SigridLookupClient` (infrastructure),
servido por un endpoint de `interface_adapters/web/app.py`, como `/api/sigrid/obras`.

## 1. Ficheros a modificar

| Fichero | Qué cambia |
|---|---|
| `services/albaranes-front/infrastructure/sigrid/sigrid_lookup_client.py` | `_SQL_PROVEEDORES_TODOS`, constantes y `buscar_proveedores` (§3) |
| `services/albaranes-front/domain/models/review_models.py` | `ProveedorOption` gana `fichas: int \| None = None`; nuevo `BusquedaProveedores` (§3) |
| `services/albaranes-front/interface_adapters/web/app.py` | endpoint `GET /api/sigrid/proveedores/todos` junto a `sigrid_proveedores` (~l.526) |
| `services/albaranes-front/templates/document_detail.html` | bloque del combo de proveedor (~l.300-313): cabecera con el check (§4) |
| `services/albaranes-front/static/app.js` | `initCombo` con modo global para `kind = "proveedor"` y funciones puras (§5) |
| `services/albaranes-front/static/styles.css` | `.campo-combo` (copia del estilo de `.form-grid label`) y `.check-inline` |
| `docs/ARCHITECTURE.md` | viñeta en la regla 17 (proveedor): la búsqueda global y su definición de «vivo» |
| `services/albaranes-front/sv4.md` | fila del endpoint nuevo en la tabla de endpoints (~l.150-165) |
| `azure-apps/albaranes.md` §8 | una viñeta: sv4 lee `prv` vivos por nombre/CIF, `NO_TOLERA`, TOP 51 (commit local, sin push) |

Ficheros a crear (tests, sin red ni BBDD):
`tests/test_f114_cliente.py` (cliente con `httpx.MockTransport`, patrón `test_f052_lookup_truncado.py`),
`tests/test_f114_endpoint.py` (`build_app` con dobles, patrón `test_f076_partidas_sv4.py` §«El endpoint»),
`tests/test_f114_js.py` (funciones de `app.js` ejecutadas con node, patrón `test_f065_f1_js.py`),
`tests/test_f114_plantilla.py` (texto de la plantilla y del CSS, patrón de `test_f065_f3bis_front.py`).

## 2. Ficheros que NO se tocan

- `fetch_proveedores_por_obra`, `_SQL_PROVEEDORES_POR_OBRA` y `/api/sigrid/proveedores` (R21).
- `review_repository.update_document_y_transicion`: sigue escribiendo solo `proveedor_cif` y
  `proveedor_nombre`; `proveedor_cif_origen` no se toca (D5).
- `review_service._relanzar_busqueda_si_cambia` (F-052 D4-A): el guardado ya relanza la búsqueda.
- sv3 (red de proveedor, refetch), sv5, sv6, sv9, `ruesma_comun`: ver §6.
- Los combos de obra y de líneas de contrato (`.combo-lines`) y `_proposeBest`.

## 3. Cliente y endpoint (infrastructure + interface_adapters)

```sql
-- _SQL_PROVEEDORES_TODOS (todo por parámetro; R15)
SELECT TOP (?)
    v.cif      AS cif,
    MIN(v.raz) AS nombre,
    COUNT(*)   AS fichas
FROM prv AS v
JOIN con AS c ON c.ide = v.ide
WHERE c.tip = ? AND c.emp = ? AND c.fecbaj = ?
  AND v.cif IS NOT NULL AND LTRIM(RTRIM(v.cif)) <> ''
  AND (v.raz COLLATE Latin1_General_CI_AI LIKE ? ESCAPE '!'
       OR REPLACE(REPLACE(UPPER(v.cif), ' ', ''), '-', '') LIKE ? ESCAPE '!')
GROUP BY v.cif
ORDER BY MIN(v.raz), v.cif
```

Parámetros: `[LIMITE + 1, TIP_PROVEEDOR (5), EMPRESA (1), 0, patron_nombre, patron_cif]`.
`prv.raz` es texto de 128 (no `text`): admite `MIN` y `ORDER BY` (trampa de §6.6 de `sigrid_api.md`).
`tip 5` y `fecbaj = 0` son los de `L17_PROVEEDOR_POR_CIF` de sigrid-api: lo que se lista es lo que su
alta sin contrato reconoce. La sintaxis (`TOP (?)`, `COLLATE`, `ESCAPE`) se valida en la T0 (MANUAL).

Constantes del módulo: `MINIMO_BUSQUEDA_PROVEEDOR = 3`, `LIMITE_BUSQUEDA_PROVEEDOR = 50`,
`TIP_PROVEEDOR = 5`, `EMPRESA_RUESMA = 1`.

- `_patron_like(texto: str) -> str` (función del módulo): escapa `!`, `%`, `_`, `[` con `!` (T0: `ESCAPE '\'` da error 506 a través de sigrid-api) y
  envuelve en `%…%` (R16).
- `SigridLookupClient.buscar_proveedores(self, *, texto: str) -> BusquedaProveedores`:
  1. `t = texto.strip()`; si `len(t) < MINIMO` ⇒ `BusquedaProveedores(items=[], mas=False)` sin
     llamar (defensa; el endpoint ya corta, R13).
  2. `patron_nombre = _patron_like(t)`; `patron_cif = _patron_like(t.upper().replace(" ", "").replace("-", ""))`.
  3. `_post_sql_read(..., label="proveedores_todos", politica=PoliticaTruncado.NO_TOLERA)` (R20).
  4. Por fila: `cif = _opt_str`, descarta vacío y `es_cif_propio(cif, _CIFS_PROPIOS)` con
     `_CIFS_PROPIOS = cifs_propios(None)` (R19); agrupa por `normalizar_cif(cif)` sumando `fichas`
     y conservando el primero (ya ordenado por nombre) (R17).
  5. `mas = len(filas_sql) > LIMITE`; devuelve los primeros `LIMITE` (R18). Log INFO con texto,
     número y `mas` (R20).
- `BusquedaProveedores(BaseModel)` en `review_models.py`: `items: list[ProveedorOption]`, `mas: bool`.
- Endpoint (`app.py`, junto a `sigrid_proveedores`):

```python
@app.get("/api/sigrid/proveedores/todos", include_in_schema=False)
def sigrid_proveedores_todos(q: str = Query(default="")) -> JSONResponse:
    # client None ⇒ ok=false (R14); len(q.strip()) < MINIMO ⇒ ok=false sin llamar (R13);
    # excepción ⇒ WARNING + ok=false (R14); si no, {ok, items:[{cif,nombre,fichas}], mas} (R12)
```

## 4. Plantilla (`document_detail.html`)

El `<label class="full-width">` que envuelve al combo pasa a `<div class="full-width campo-combo">`:
dentro de un `<label>`, un checkbox sería su primer control y un clic en el rótulo lo conmutaría.

```html
<div class="full-width campo-combo">
  <div class="campo-combo-cabecera">
    <span id="proveedor_combo_rotulo">Elegir proveedor (con contrato en la obra · Sigrid) — escribe para buscar</span>
    <label class="check-inline"><input type="checkbox" id="proveedor_solo_obra" checked> Solo de la obra</label>
  </div>
  <div class="combo" data-kind="proveedor" ... data-solo-obra-check="proveedor_solo_obra"
       data-endpoint-todos="/api/sigrid/proveedores/todos"> … (igual que hoy) </div>
</div>
```

Desmarcado, el JS cambia el rótulo a «Elegir proveedor (todos los de Sigrid) — escribe al menos 3
letras del nombre o del CIF». Sin `{% if editable %}`, nada de esto se pinta (R1).

## 5. JS (`static/app.js`, dentro de `initCombo`)

Funciones puras al nivel de las de `_norm` (para sacarlas con `_funcion_js` en los tests):

- `textoBusquedaProveedor(valor)` ⇒ texto recortado o `null` si tiene menos de 3 caracteres.
- `urlProveedoresTodos(endpoint, texto)` ⇒ `endpoint + "?q=" + encodeURIComponent(texto)`.
- `etiquetaProveedorGlobal(it)` ⇒ `_comboLabel("proveedor", it.cif, it.nombre)` + (`fichas > 1` ⇒
  ` · N fichas en Sigrid`) (R6).
- `mensajeListaObraVacia(error)` ⇒ texto de R10 (con el error delante si lo hay).

En `initCombo`, solo si `kind === "proveedor"` y existe `data-solo-obra-check`:

- `soloObra()` lee el check. Marcado ⇒ `ensureLoaded`/`applyFilter` de hoy, sin tocar (R2);
  única adición: si la lista llega vacía o el endpoint dice «Falta el codigo de obra», el mensaje
  es `mensajeListaObraVacia` (R10).
- Desmarcado ⇒ los manejadores `focus` e `input` llaman a `buscarGlobal()` en vez de
  `ensureLoaded`: `clearTimeout` + `setTimeout(…, 300)`; `const n = ++secuencia`; `fetch`; si
  `n !== secuencia` se descarta (R4); `items` = respuesta mapeada con `etiquetaProveedorGlobal` y
  `render(items)` sin filtrar (R3); `mas` ⇒ fila final no elegible `.combo-msg` (R5); `title` del
  ítem con varias fichas (R6). Menos de 3 ⇒ `msg(...)` sin `fetch` (R3). Error ⇒ `msg("⚠ …",
  "combo-error")` (R11). `keydown` y `choose` no cambian (R7).
- `change` del check ⇒ `items = []`, `loadedKey = null`, `++secuencia`, `close()`, rótulo
  según el modo, `input.value = combo.dataset.label` (R8). Nada en `localStorage` (R9).
- `_proposeBest` sigue usando `ensureLoaded(true)` (lista de la obra): al cargar el check está
  siempre marcado (R9), así que la propuesta no cambia.

## 6. Aguas abajo de un proveedor sin contrato en la obra (verificado en el código)

1. **Guardar** (`sendSave` ⇒ PUT): sv4 escribe CIF y nombre; el CIF cambia respecto al rastro, así que
   `_relanzar_busqueda_si_cambia` publica la re-búsqueda (`q-persistencia`, `force=True`).
2. **sv3, re-búsqueda** (`contrato_refetch_service`): canoniza el nombre por CIF exacto (`prv.raz`)
   y, sin contratos para CIF + obra, devuelve `no_results` («No se encontró ningún contrato…»),
   que la ficha ya enseña. La red de proveedor (regla 17) **no** corrige: el CIF existe en `prv`. Un
   CIF propio no llega (R19; si llegase, sv3 lo descarta, regla 18).
3. **Botón de buscar contratos**: igual, `no_results`; el combo de contratos sale vacío.
4. **Valoración** (regla 25, F-075): sin contrato seleccionado y con importes, sv3 publica
   `q-valoracion` con `codigo_contrato` nulo y sv6 hace la valoración directa (`no_contract`, sin IA,
   partida impresa o almacén, regla 16); sin importes, `sin_importe_en_albaran` y no se aprueba
   hasta completarla. «Valorar ahora» sin contrato sigue disponible si el albarán trae importes.
5. **Alta en Sigrid (sv9)**: `cod_contrato` = el de la valoración ⇒ nulo; todas las líneas sin
   vincular con producto genérico por familia (`QA9999`/`XA9999`/`MA9999`). sv9 **no** manda
   `sin_contrato` (ese campo es de `sigrid/proforma`, §8.10, no de `sigrid/albaran`). Con la F-015
   desplegada (24-10), sigrid-api toma la identidad del contrato ⇒ del último albarán del CIF en la
   empresa de la obra ⇒ del **único** `prv` vivo con ese CIF; ninguno ⇒ `proveedor_no_encontrado`,
   varios ⇒ `proveedor_ambiguo`, los dos `no_admitido` en sv9 (F-104). **sv9 no necesita cambios.**

## 7. Riesgos

- **R-1 CIF con otra grafía**: L17 compara `v.cif = ?` con el CIF que manda sv9 normalizado (H21).
  Si un `prv.cif` guarda espacios o minúsculas, el alta sin contrato ni albarán previo daría
  `proveedor_no_encontrado` (visible, `no_admitido`). La T0 mide cuántos hay.
- **R-2 Contrato de otro proveedor seleccionado** (D6): sv3 hace *upsert* de contratos y no limpia
  `selected_contrato_codigo` con 0 resultados; si el documento tenía elegido un contrato del
  proveedor anterior, se queda. Es previo a F-114 (pasa igual con «Solo de la obra»); el origen de la
  feature (obra sin contratos) no lo tiene.
- **R-3 `COLLATE` / `TOP (?)`** no aceptados por el validador de sigrid-api: la T0 lo prueba; si
  falla, se para y se re-propone (sin `COLLATE`, o `TOP` literal de una constante).
- **R-4 Rendimiento**: `LIKE '%…%'` recorre `prv` entero; con decenas de miles de filas es
  ~ms en SQL Server. La T0 mide el tiempo; con el debounce y el mínimo, una petición por pausa.

## 8. Decisiones para la PARADA 1 (recomendación en negrita)

**PARADA 1 cerrada por el humano el 2026-10-30**: D1 a D7 aprobadas según la recomendación («apruebo»). D6: el contrato del proveedor anterior va a una feature aparte, F-115, dada de alta el mismo día.

- **D1 Lista completa o búsqueda al escribir.** (a) Lista completa de vivos, cargada al enfocar y
  filtrada en local como hoy: reutiliza todo, pero son N filas por apertura y `render` pinta un `div`
  por fila (con 3.543 proveedores con contrato el 29-09, `prv` entero será mayor). (b) **Búsqueda en
  servidor, mínimo 3 caracteres, 50 resultados**: coste constante sea cual sea `prv`. Recomendada
  (b); (a) solo si la T0 da ≤ 5.000 CIF vivos y el humano prefiere no esperar al servidor.
- **D2 CIF repetido**: **una entrada por CIF con «N fichas en Sigrid»** (sv4 solo guarda el CIF; el
  aviso anticipa `proveedor_ambiguo`). Alternativa: ocultarlos (perdería proveedores reales).
- **D3 Bajas y bloqueos**: **baja = `con.fecbaj ≠ 0`, se excluye** (como sigrid-api). `prvblo`
  (bloqueos por empresa, con `fecbaj` propia) **no se filtra ni se marca** en F-114: su significado
  (pagos, homologación…) no está documentado y sigrid-api no lo mira. La T0 cuenta cuántos hay.
- **D4 Recordar el check**: **no; siempre marcado al cargar**, como pidió el humano (por defecto).
- **D5 Encaje con F-062**: **sin cambios**. Elegir de la lista global es la misma edición manual de
  hoy (solo `prv.cif`); sv3 no la corrige porque el CIF existe, y retira `[CORREGIDO] Proveedor` y su
  motivo en la siguiente pasada (regla 17). `proveedor_cif_origen` no se toca (como hoy).
- **D6 Contrato del proveedor anterior** (R-2): **fuera; feature aparte** (sv3/sv4: al cambiar el CIF,
  desseleccionar el contrato que no es de ese CIF). Ver `progress/spec_F-114.md`.
- **D7 Empresa**: **`emp = 1`**, como todas las lecturas de sv4. Una obra de otra empresa de
  `SIGRID_ALBARAN_EMPRESAS_OBRA` no se contempla (no la hay en el pipeline hoy).
