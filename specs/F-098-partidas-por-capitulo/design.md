<!-- specs/F-098-partidas-por-capitulo/design.md -->
# F-098 · Partidas por capítulo y con su código completo · Diseño (v1, 2026-10-23)

## 1. La idea en cuatro líneas

- **Se guarda el cod de Sigrid** (`99.01.64`), como hoy y como decidió F-076 («el código tal como figura en la
  lista»). **Se enseña el código completo** (`CD.99.01.64`), calculado de la lista. **sv9 manda lo guardado**.
- El capítulo y el código completo se calculan **una vez, en comun**, a partir de las mismas filas de
  `SQL_PARTIDAS_POR_OBRA` (ya trae `ide`, `padide`, `cod`, `res`): ni SQL nueva ni DDL.
- `casar_partida` aprende que el código completo de una hoja es la hoja: `CD.99.01.64` ⇒ `99.01.64` (`completa`).
  Así lo corrigen sv6 al valorar (F-076, sin tocar su código) y sv4 al guardar una fila.
- sv4 hace el selector como partes: chips «Todas / CD / CI / CP / 98 …» (los que tenga la obra) y luego la partida.

Por qué no guardar el completo (P1, descartada): la partida de las líneas de contrato (`ctrpro.paride →
obrparpar.cod`, sv3 y sv4) es el cod; `cambia_origen`, el ✓/⚠, las reglas de sv6 (`casa_con_contrato`) y sigrid-api
(`resolver_partida`, que busca por `cod` con `_clave` = mayúsculas y espacios, y exige que `paride` tenga ese cod)
comparan contra el cod. Guardar `CD.99.01.64` obligaría a traducir en todos esos sitios y en sv9; guardar el cod
deja intacto todo el camino del alta.

## 2. sigrid-api (consultado en `azure-apps/sigrid_api.md` §8.6 y en su `contrato_albaranes.md`)

La línea del alta extendida lleva `partida?` (cod, 1-24) y `paride?` (`obrparpar.ide`, opcional, «va con
`partida`», debe ser imputable de la obra y **con ese código**, si no `paride_no_valido`). Con el cod basta: **no
hace falta cambiar sigrid-api**. Mandar el completo falla (`partida_no_encontrada`, el caso `8c4e026a`). `paride`
resolvería los cod repetidos entre imputables (M3 de F-009: 4.312 pares obra-código) y es la H17 pendiente
(«F-049 conserva el `ide`; F-053 lo manda»): queda **fuera** (P2), con la lista ya trayendo el `ide` para quien lo
haga. Ninguna dependencia con otro proyecto.

## 3. Ficheros a crear

| Ruta | Qué |
|---|---|
| `services/albaranes-comun/tests/test_f098_partidas_capitulo.py` | R1–R13 (filas falsas: árbol de 0686, raíz única, `CD2.07`, ciclo, raíz sin cod) |
| `services/albaranes-front/domain/ports/partidas_obra_port.py` | `PartidasObraPort` (sv4) |
| `services/albaranes-front/domain/services/partidas_ficha.py` | presentación y traducción de partidas en la ficha (§5.2) |
| `services/albaranes-front/tests/test_f098_lista_sv4.py` | R14, R27, R28 (endpoint y caché con lector falso) |
| `services/albaranes-front/tests/test_f098_ficha_partida.py` | R23, R24, R25, R26 (servicio y render de la plantilla) |
| `services/albaranes-front/tests/test_f098_combo_js.py` | R15–R22 con node + `dom_falso.js` |
| `services/albaran-valoracion-persist/tests/test_f098_normaliza_completa.py` | R29 (pipeline con fixture) y R31 |
| `services/albaranes-alta-sigrid/tests/test_f098_partida_cod.py` | R30 |
| `services/albaran-valoracion-persist/scripts/corregir_partidas_f098.py` | R32, **solo con P4 = a** |

## 4. Ficheros a modificar

- `services/albaranes-comun/ruesma_comun/sigrid/partidas.py`: campos nuevos de `PartidaObra` (al final y con
  defecto: `ide`, `capitulo`, `capitulo_descripcion`, `codigo_completo`), `CapituloObra`,
  `ListaPartidasObra.capitulos` / `cod_repetido` / `no_hojas_completos`, `codigo_completo()`, motivo `completa`,
  índice conjunto en `_casar_simple`, guarda de no hoja ampliada, `misma_partida`, `mostrar_partida`,
  `CachePartidasObra.consultar`. Docstring del módulo: F-098.
- `services/albaranes-comun/ruesma_comun/sigrid/__init__.py` (exportar), `pyproject.toml` (0.9.0), README de comun.
- `services/albaranes-front/config/settings.py`: `PARTIDAS_OBRA_TTL_S` (600), `PARTIDAS_OBRA_MAX_OBRAS` (64),
  `PARTIDAS_OBRA_FALLO_TTL_S` (60).
- `services/albaranes-front/infrastructure/sigrid/sigrid_lookup_client.py`: `lector_partidas` público (el
  `_lector_partidas` de hoy); `fetch_partidas_por_obra` pasa a construir `PartidaOption` con los campos nuevos.
- `services/albaranes-front/domain/models/review_models.py`: `PartidaOption` + `ide`, `codigo_completo`,
  `capitulo`, `cod_repetido`; `DocumentDetailPayload.partidas_mostradas: dict[str, str]` (vacío por defecto).
  `coincide_partida` y `cambia_origen` **no cambian**.
- `services/albaranes-front/application/services/review_service.py`: recibe `partidas: PartidasObraPort | None`
  (opcional, como `orchestrator`); `get_document` aplica `presentar_partidas`; `update_line_conciliacion` y
  `dividir_linea` traducen la partida con `traducir_partida` antes del repositorio (obra de
  `get_merge_cif_and_obra`).
- `services/albaranes-front/interface_adapters/web/app.py`: crea la `CachePartidasObra` de sv4 sobre
  `client.lector_partidas` (sin cliente ⇒ `None`), se la pasa a `ReviewService` (hoy se construye antes que el
  cliente: mover el orden) y la usa `GET /api/sigrid/partidas` vía `consultar` (R14). Plantillas: helper
  `partida_mostrada(doc, cod)`.
- `services/albaranes-front/templates/document_detail.html`: casilla de partida (≈789–800: `value` y `placeholder`
  con lo mostrado, `data-partida-cod` = cod), opciones de «Origen ✎» (≈813), `contrato-lines-json` (≈969: `part`
  sigue el cod, `label` con lo mostrado, `partMostrada` nuevo), «Líneas a Sigrid» (≈1033), `data-partida` de
  «Dividir» (≈933, el mostrado) y la nota F-076 del `title` (≈784) con lo mostrado.
- `services/albaranes-front/static/app.js` (§5.3): `partidasDeRespuesta`, `opcionesPartida`, `attachPartidaCombo`
  (chips, tope, `pick`), `partidaValida`, `partidaParaEnviar`, `partidasMalas` y el envío de «Dividir».
- `services/albaranes-front/static/styles.css`: `.combo-chips` y `.chip.on` (como partes `styles.css:875–881`).
- `services/albaran-valoracion-persist/scripts/medir_f076_partidas.py`: clase `completa` (R31).
- `docs/ARCHITECTURE.md` regla 23 (+ «Infra y despliegue»: comun 0.9.0) y `azure-apps/albaranes.md` (R35).

## 5. Clases y funciones

### 5.1 comun (`ruesma_comun.sigrid.partidas`, sin red ni BBDD)

- `codigo_completo(capitulo: str | None, cod: str) -> str` (R3). Comparación con `NFKC + upper + strip`; límite =
  fin, carácter no alfanumérico o cambio letra↔dígito entre el último carácter del capítulo y el siguiente del cod.
  Compone con `.` y el cod tal cual (no se normaliza lo que se enseña).
- `_primer_nivel(by_ide, parent_ides) -> dict[ide, ide_capitulo]` (R2): sube cada cadena hasta la raíz (padre 0,
  nulo o ausente; `visto` contra ciclos); con UNA raíz con hijos, baja un nivel y repite. `_hojas` lo usa para
  rellenar `capitulo`, `capitulo_descripcion` y `codigo_completo`; `ide` sale de la fila.
- `CapituloObra(codigo: str | None, descripcion: str | None, n_hojas: int)`; `ListaPartidasObra.capitulos`
  (propiedad, R4), `cod_repetido(cod) -> bool` (R12) y `no_hojas_completos: tuple[str, ...]` (campo con defecto
  `()`, relleno en `desde_filas` con el completo de cada no hoja que lo tenga distinto).
- `MOTIVO_COMPLETA = "completa"` en `MOTIVOS_PARTIDA` y `MOTIVOS_CASADOS`.
- `_indice_normalizado(lista) -> dict[clave, set[(cod, por)]]` con `por ∈ {"cod", "completo"}`; `_casar_simple`:
  exacta literal primero (R7); luego candidatos de la clave: un cod distinto ⇒ `normalizada` si alguna entrada es
  `por="cod"`, si no `completa`; más de uno ⇒ `ambigua` (R6). Compuestas: cada parte igual (sin cambios en el paso 5).
- `resolver_partida_obra`: `MOTIVO_COMPLETA` ⇒ `RESOLUCION_NORMALIZADA`; `_choca_con_no_hoja` compara también con
  `no_hojas_completos` (R8). sv6 lo recibe sin cambiar una línea.
- `misma_partida(lista, a, b, alm=None) -> bool` (R10): `casar_partida` de las dos; ambas con motivo casado simple
  (no compuesta) y el mismo `codigos_lista[0]`.
- `mostrar_partida(lista: ListaPartidasObra | None, cod: str | None) -> str | None` (R11).
- `CachePartidasObra.consultar(obra) -> tuple[ListaPartidasObra | None, bool]` (R13): el mismo `_lista` con un flag
  de origen; `lista()` sigue devolviendo `_con_hojas(...)` (R5).

### 5.2 sv4

- `domain/ports/partidas_obra_port.py`: `PartidasObraPort(Protocol)` con `lista(obra)` y `consultar(obra)`.
- `domain/services/partidas_ficha.py` (domain, puro):
  - `presentar_partidas(detalle, lista) -> DocumentDetailPayload`: sin lista ⇒ el mismo objeto (R28). Con lista:
    `partidas_mostradas` = {cod: completo} de los cod de la ficha (finales, casadas, líneas de contrato) cuyo
    `mostrar_partida` difiere; y en cada conciliación con `agree_partida is False` y `misma_partida(leída, casada)`
    ⇒ `agree_partida=True`, `aviso_partida=None` y `partida_normalizada_desde` = leída si difiere de lo pintado
    (R24). Nunca toca un `True` ni un `None`. Copia con `model_copy`, no muta.
  - `traducir_partida(lista, valor) -> str | None`: `None`/vacío ⇒ igual; con lista y `resolver_partida_obra`
    `exacta`/`normalizada` ⇒ el cod; si no, igual (R25).
- `ReviewService`: `get_document` ⇒ `presentar_partidas(detalle, self._partidas.lista(obra))` si hay puerto y
  obra (vista merge y aprobados también: la presentación no escribe). `update_line_conciliacion` y `dividir_linea`
  traducen solo si la partida viene y no está vacía; `cambia_origen` recibe ya el cod (R26: lo calcula el
  repositorio con lo que le llega).
- `GET /api/sigrid/partidas`: `consultar` ⇒ `ok=False` si `ok` es falso o la lista es `None`; si no, `items` y
  `capitulos` de R14. El texto de error no lleva la excepción (la caché ya la registró en WARNING).

### 5.3 sv4 · `static/app.js`

- `partidasDeRespuesta(data)` ⇒ `{items, capitulos, error}`; cada item `{code: cod, completo, capitulo, repetido,
  label: completo · desc_agregada [+ « (código repetido en la obra)»], norm}`.
- `opcionesPartida(items, texto, capitulo)`: «Almacén» primero; filtro de capítulo (`null` = Todas) y tokens como
  hoy; devuelve `{shown, resto}` con `shown` ≤ 101 (Almacén + 100) y `resto` = las que no caben (R19).
- `attachPartidaCombo`: barra `.combo-chips` encima de la lista (botones `type=button`, `mousedown` +
  `preventDefault` para no perder el foco, como partes); chip activo = `capituloElegido()` de la ficha (variable de
  módulo + `localStorage["f098.capitulo." + obra]` en `try/catch`) (R15–R17). `pick(it)` pone `input.value =
  it.completo` y `input.dataset.partidaCod = it.code`. «Cargando partidas…» y el error, como hoy.
- `partidaValida(valor, items)`: vacío, o igual a `it.completo` o a `it.code` (R22).
- `codigoParaEnviar(valor, items)`: vacío ⇒ `""`; igual a un `completo` de una sola hoja o a un `code` ⇒ el `code`;
  si no, el valor (lo frena `partidasMalas`). `partidaParaEnviar(inp, items)` compara con `defaultValue` como hoy y,
  si cambió, devuelve `codigoParaEnviar`. Quien la llame sin `items` (fila sin cambios) sigue recibiendo `null`.
- «Dividir»: las partes mandan `codigoParaEnviar` del valor de su combo.
- Fuera: el resto de la tabla, «Guardar» y su recarga (F-096), F-077 punto 4.

## 6. Encaje en la arquitectura

- Hexagonal: la regla (capítulo, completo, casar) es **dominio puro en comun**; sv4 la usa desde `domain/services`
  y la caché entra por un puerto, como en sv6 (`PartidasObraPort`). Ningún servicio copia lógica (regla de límite).
- **Límite de servicio**: no hay responsabilidad nueva. sv4 sigue sin validar la partida contra la obra (solo la
  traduce si casa); sv6 sigue siendo quien la normaliza al valorar; sv9 no cambia.
- **Datos**: sin DDL (regla 4 intacta), sin columnas nuevas (no se inventa `partida_ide`: es P2), sin cambios en
  mensajes. `codigo_partida_final` sigue siendo un cod de la obra (regla 23) y `codigo_partida_albaran` la leída
  (regla 6).
- **Despliegue** (lo hace el humano): comun 0.9.0 ⇒ reconstruir **sv6 y sv4** (sv9 importa comun pero no cambia de
  comportamiento; sv3 y sv2 no usan `sigrid.partidas`). Orden: sv6 → sv4. Requiere que la secuencia pendiente de
  F-076 (T18–T20, `set_partidas_sv6.ps1`) esté hecha o se haga a la vez: sin ella sv6 no normaliza nada.
- **Conflictos de texto previstos**: F-049 (`partidas.py`: su versión es superconjunto; al retomarla conserva lo de
  F-076 y F-098, y su prompt de fase 2 debe dar a IA2 el **código completo**), F-096 y F-077 (`app.js`, misma
  zona de guardado), F-094 (plantilla). Nada de reglas cruzadas.

## 7. Riesgos y alternativas descartadas

- **R-1 · Regla de primer nivel equivocada para otra forma de árbol.** Lo visto: 0686 con 4 raíces. partes dice
  que «la raíz suele ser PRESUPUESTO» (`partida_catalog.py:4`); si una obra tiene UNA raíz real (solo CD), la
  regla de R2 bajaría a sus hijos y perdería el prefijo `CD`. Mitigación: lectura T0 antes de implementar (P6).
- **R-2 · Composición ambigua del completo** (`98` + `985.1`, `CD` + `CD2.07`): fijada por R3 con tests; T0 dice si
  aparece alguna forma más.
- **R-3 · `ambigua` nueva**: una lectura que antes era `normalizada` puede pasar a `ambigua` si su clave coincide
  además con el completo de otra hoja. Es lo correcto (dos hojas posibles) y va a revisión con
  `partida_ambigua_en_obra`; T0 mide si pasa en alguna obra real.
- **R-4 · Ficha más lenta en frío**: la primera ficha de una obra por réplica espera la lista (hoy la espera solo el
  combo). Acotado por `SIGRID_API_TIMEOUT_S` y el fallo recordado 60 s. Alternativa descartada: pintar el completo
  solo en JS al llegar la lista (parpadeo `99.01.64 → CD.99.01.64`, y el ✓/⚠ y «Líneas a Sigrid» quedarían con el
  cod). Si el humano prefiere ficha rápida, P5.
- **R-5 · Datos frescos**: hoy cada carga de ficha relee la lista; con 600 s, una partida nueva en Sigrid tarda
  hasta 10 min en salir en sv4 (P5).
- **R-6 · Cod repetido entre hojas**: elegir cualquiera de las dos guarda el mismo cod y sigrid-api responderá
  `partida_ambigua` (`no_admitido`). Se avisa en la opción (R20); se arregla con `paride` (P2).
- Descartado **guardar el completo** (§1) y **una columna `capitulo`** en la valoración (se desfasaría del árbol y
  no sirve para las líneas de contrato).
- Descartado **quitar prefijos a la lectura** (`CD.99.01.64` ⇒ «el sufijo `99.01.64`»): es elegir por sufijo,
  prohibido (H1). R6 no quita nada: compara con el completo **calculado de la lista**.

## 8. Preguntas para el humano (PARADA 1)

- **P1 · Qué se guarda.** (a) el cod de Sigrid y se enseña el completo — **recomendada** (§1); (b) el completo.
- **P2 · `ide` / `paride`.** (a) fuera: feature aparte (DDL de sv6 `partida_ide`, sv4 y sv6 lo escriben, sv9 manda
  `paride`), decidida con la medida de T0 de cod repetidos — **recomendada**; (b) dentro de F-098 (sube a
  4 servicios con DDL).
- **P3 · El chip.** (a) compartido por la ficha y recordado por obra, «Todas» por defecto — **recomendada**; (b) por
  combo, como partes; (c) que abra en el capítulo de la partida que ya tiene la fila.
- **P4 · Lo ya guardado con prefijo.** (a) script `--aplicar` del humano (R32); (b) medir con R31 y corregirlas a
  mano en la ficha (con F-098 basta reelegir la partida) — **recomendada si son menos de ~20**; (c) revalorar
  (pierde lo manual, F-058).
- **P5 · Caché de sv4.** (a) 600 s y la ficha espera la lista en frío — **recomendada**; (b) otro TTL; (c) solo JS.
- **P6 · Primer nivel.** Confirmar R2 con T0: ¿hay obras con una sola raíz? ¿es «PRESUPUESTO» o un capítulo real?
- **P7 · Bandeja.** `documents_list.html:277` y la búsqueda por partida (`review_repository.py:5343`, `ILIKE` sobre
  el cod) siguen con el cod: fuera de F-098 (U25 de `analisis_usabilidad_front.md`). También fuera: que una
  partida inválida, tecleada o ya guardada, frene «Guardar y aprobar» (F-077 punto 4, U07 del análisis).
- **P8 · Hojas no imputables** (de baja, `tipdes`≠0) siguen en el combo (H4 de F-009; partes las quita): fuera.

## 9. Datos que el líder lee en Sigrid antes de aprobar (T0, solo lectura, `sql/read`)

Por cada obra con albaranes en los últimos 90 días (lista de obras del merge): nº de raíces y su `cod`/`res`;
obras con una sola raíz; por capítulo de primer nivel, hojas cuyo `cod` no empieza por el capítulo (con R3) y tres
ejemplos; pares (obra, cod) repetidos entre hojas; y, en la BBDD `albaranes` (solo lectura), finales que casan solo
por el completo (R31 sin escribir). Base: `SQL_PARTIDAS_POR_OBRA` de comun, una obra por petición.
