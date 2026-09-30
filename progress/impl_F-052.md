# F-052 · Informe del implementer

Rama `feature/F-052-proveedores-truncados`. Rigor **critico**. Spec v2 aprobada
por el humano el 2026-09-30. Condensado el 2026-09-30 para caber en el tope: las
trazas completas de A y B se reproducen con el test indicado sobre el commit
anterior al de la tarea (el reviewer lo hizo: `progress/review_F-052_bloque{A,B}.md`).

## Bloque A (T1–T6) · `ruesma_comun` y cliente de sv3 · APROBADO

| Tarea (commit) | Qué | RED (`pytest <fichero> -q` en su servicio) | GREEN |
|---|---|---|---|
| T1 `5588131` | `ruesma_comun/sigrid/lectura.py`: `PoliticaTruncado`, `SigridRespuestaTruncada(etiqueta, filas)`, `comprobar_truncado`, `con_paginacion`, `leer_paginado` (R8, R9, R14) | `ModuleNotFoundError: No module named 'ruesma_comun.sigrid'` — `1 error` | 29 passed |
| T2 `dcf9292` | Doble `tests/doble_sigrid_api.py` + kwarg `transport` | `TypeError: ...__init__() got an unexpected keyword argument 'transport'` — `1 failed, 10 passed` | 11 passed |
| T3 `cd17ae9` | `_post_sql_read(politica, max_rows=None)`; política de las 7 consultas; docstring del falso tope (R7–R10) | `unexpected keyword argument 'politica'`, `DID NOT RAISE SigridRespuestaTruncada` ×5 — `12 failed, 1 passed` | 13 passed |
| T4 `6d9c795` | `_post_sql_read_paginado`; `header_and_lines` y `search_proveedores` paginadas (R11–R13) | `assert [500, 500] == [500, 700]`, `assert 1000 == 3543`, `assert 1000 > 5000` — `7 failed, 1 passed` | 8 passed |
| T5 `69883cb` | `fetch_contratos_resumen_por_obra` con la agregada, una llamada, `NO_TOLERA` (R2, R3, R5) | `SigridRespuestaTruncada ... 1000 filas recibidas`, `assert 0 == 81` — `9 failed, 10 passed` (con T6) | 12 passed |
| T6 `fe717bd` | Equivalencia de familias texto agregado == texto por líneas (R4) | `r4_mismas_familias[0691\|0668]` FAILED con T5 | 7 passed |

CR-A1 `2caa1c9` (R5 fija el ganador por barajado; RED `assert (None, 'deterministic') ==
('B82899550', 'deterministic')` — `3 failed`) y CR-A2 `1a18615` (`leer_paginado` lanza si
una página trae filas de más; RED `DID NOT RAISE RuntimeError` — `2 failed, 29 passed`).
Mutante «leer `nombre` en vez de `texto`»: muerto (80 CIF difieren).

Decisiones A: doble con `truncated = filas >= max_rows`; `search_proveedores(max_rows=5000)` = tamaño de página; resumen ordenado por `(cif, nombre)` y deduplicado por CIF (R5).

## Bloque B (T7–T10) · sv3 · APROBADO

| Tarea (commit) | Qué | RED (fichero nuevo contra el commit anterior) | GREEN |
|---|---|---|---|
| T7 `8085dd4` | `_mejor_candidato_por_nombre` → `(candidato, motivo, n)`; nota de design §6 por motivo (R1, R5, R15–R19) | `test_f052_nota_proveedor.py` contra `f766178`: `19 failed, 9 passed` | 28 passed |
| T8 `f7e86ef` | Obra + familia: truncado → WARNING con obra; resto `logger.exception`; ambos degradan (R6) | `-k r6_familia` contra `8085dd4`: `1 failed, 3 passed` | 4 passed |
| T9 `1df8ef5` | DDL idempotente de `contratos_busqueda_*`, ORM, `sellar_busqueda_contratos` (R20) | `test_f052_rastro_busqueda.py` contra `f7e86ef`: `13 failed, 2 passed` | 15 passed |
| T10 `fed1bfa` | `enrich_merge_document` sella el rastro en cada salida, best-effort (R21, R13) | mismo fichero contra `1df8ef5`: `24 failed, 17 passed` | 41 passed |

- **T7**: `TypeError: cannot unpack non-iterable ProveedorObraResumen object`; con `error_xml`,
  `assert 'no se pudo consultar la lista de proveedores de la obra 0691 (fallo al consultar
  Sigrid): no hay propuesta' in "[AVISO] Proveedor el CIF leido B82890580 no existe en Sigrid y
  ningun proveedor con contrato en la obra casa con el nombre leido ('SALMEDINA')..."`;
  `AssertionError: assert None == (None, 'sin_obra', 0)`.
- **T7 · R1 contra el cliente anterior a T5 (O5, corregido por O-B3)**: árbol con el cliente
  de `6d9c795` y el **resolver de `f766178`** → `1 failed`, nota «ningún proveedor ... casa»
  (el bug de SS-0026122 y la mentira de R15 a la vez). Con el **resolver de T7** (`8085dd4`)
  y ese mismo cliente también falla, pero la nota ya dice «**no se pudo consultar** la lista
  de proveedores de la obra 0691» (reproducido por el reviewer): R15 no depende de T5.
- **T8**: `ValueError: not enough values to unpack (expected 1, got 0)` (no había WARNING).
- **T9**: `AssertionError: falta el ALTER de contratos_busqueda_cif`; `'SqlAlchemyAlbaranRepository'
  object has no attribute 'sellar_busqueda_contratos'` ×9.
- **T10**: `assert [] == [('doc-f052-r... 'sin_datos')]`, `... 'error')]`, `... 'ninguno')]`,
  `... 'encontrados')]` ×4; R13 de punta a punta (1.200 líneas, tope 2): `assert [] == [(... 'error')]`.

Decisiones B: nota con cabeza intacta y cola literal de design §6; sin obra y sin nombre a la
vez → `sin_obra`; constantes `BUSQUEDA_*` en `domain/models/contrato_models.py`; el repositorio
rechaza un resultado desconocido con `ValueError` y pone la fecha UTC. **Extensiones de R21
(O-B2, a decidir en el cierre)**: (a) `replace_contratos` falla tras una consulta correcta →
rastro **`error`** (ni `encontrados` ni `ninguno` serían verdad); (b) servicio desactivado
(`enabled=False`) → **sin sello** (no hubo búsqueda). El Bloque C aplica (a) también al
fallback local de sv4. `ruff`: +4 `ISC004` en el DDL, mismo estilo que `_PHASE2_DDL`.
Mutantes manuales B: **7/7 muertos** (+2 del reviewer).

## Bloque C (T11–T13 bis, T15, T17) · sv4

Orden: **T12 antes que T11** (la vista que devuelve `estado_busqueda` la necesita el
repositorio de T11). RED: fichero nuevo contra el commit anterior, con
`cd services/albaranes-front; .venv/Scripts/python.exe -m pytest <fichero> -q`.

| Tarea (commit) | Qué | RED | GREEN |
|---|---|---|---|
| T12 `8fa6a5b` | `application/services/busqueda_contratos.py::estado_busqueda` (5 estados; CIF sin espacios y en mayúsculas, obra con `normalize_obra_code`); `BusquedaContratosVista`, `RastroBusquedaContratos` y literales `BUSQUEDA_*` en `review_models.py` (R27) | `test_f052_busqueda_contratos.py` contra `fb7cf75`: `1 error` | 21 passed |
| T11 `d1cf760` | ORM con las 4 columnas (longitudes de sv3), `busqueda_contratos` en `DocumentDetailPayload`, el repositorio lo rellena en `_build_merge_detail` | `test_f052_rastro_detalle.py` contra `8fa6a5b`: `6 failed` | 6 passed |
| T13 `4840421` | `document_detail.html`: mensaje por estado (R23–R26), también con contratos listados si está desfasado, falló o no se buscó; un solo juego de botones | `test_f052_bloque_contrato.py` contra `d1cf760`: `9 failed, 2 passed` | 11 passed |
| T13 bis `d954765` | D4-A: `ReviewService.save_document_y_buscar_si_cambia`, `debe_relanzar_busqueda`, `aviso_de_guardado`; PUT `?buscar_si_cambia=1`; «buscando…» + sondeo en `app.js` | `test_f052_d4a_guardar_relanza.py` contra `4840421`: `1 error` | 27 passed |
| T15 `3ec5cb4` | `LocalContratoRefetchClient` sella el rastro (R21) + `sellar_busqueda_contratos` en el repositorio de sv4 (R22) | `test_f052_refetch_local_rastro.py` contra `d954765`: `17 failed, 2 passed` | 19 passed |
| T17 `b8a9064` | `SigridLookupClient._post_sql_read(politica=...)` + `comprobar_truncado`; proveedores `NO_TOLERA`, resto `TOLERA` (R28) | `test_f052_lookup_truncado.py` contra `3ec5cb4`: `5 failed, 5 passed` | 10 passed |

Trazas RED (extracto literal):

- **T12**: `E   ModuleNotFoundError: No module named 'application.services.busqueda_contratos'`.
- **T11**: `E           AssertionError: el ORM de sv4 no declara contratos_busqueda_cif`;
  `E       KeyError: 'busqueda_contratos'`; `E       sqlite3.OperationalError: table
  albaran_documents_merge has no column named contratos_busqueda_cif`.
- **T13** (la traza de design §7 para R24: hoy pinta el CIF actual): con rastro `B82890580`
  y CIF actual `B82899550`, la plantilla anterior decía «No se encontró ningún contrato en el
  ERP para la combinación CIF B82899550 + obra 0691. Este albarán queda sin contrato» →
  `E       AssertionError: assert 'todavía no se han buscado' in '  Contrato asociado  0 contratos
  encontrados ...'`; `E       AssertionError: R23 exige la fecha de la búsqueda`;
  `E       AssertionError: assert 'falló' in ...` ×2; `assert 'no consta' in ...` ×2;
  `assert 'no se buscaron contratos' in ...`. Los 2 que pasaban son de no regresión (vigente
  con contratos no pinta aviso; un solo juego de botones).
- **T13 bis**: `E   ImportError: cannot import name 'debe_relanzar_busqueda' from
  'application.services.busqueda_contratos'`. Con el servicio ya escrito y la plantilla sin
  tocar: `E       assert 'id="busqueda-buscando"' in '<section class="contrato-section"> ...'`
  — `1 failed, 21 passed`. Los 5 casos de `test_f052_d4a_aviso_de_guardado` se escribieron
  junto al helper (sin RED propia; los caza el mutante M8). El test O-B4 fija un
  comportamiento que ya existía (el deshacer no cambia): es de caracterización.
- **T15**: `E       AssertionError: assert [] == [('f052-doc-0... 'sin_datos')]` ×4,
  `... 'error')]` ×3, `... 'ninguno')]` ×2, `... 'encontrados')]` ×2,
  `E           AttributeError: 'AlbaranReviewRepository' object has no attribute
  'sellar_busqueda_contratos'` ×2, best-effort sin log ×4. Pasaban: documento inexistente
  no sella (no regresión) y repositorio sin el método (vacío hasta T15).
- **T17**: `E       Failed: DID NOT RAISE SigridRespuestaTruncada` (proveedores);
  `E       AssertionError: []` ×3 (obras, contratos, partidas sin WARNING);
  `E       Failed: DID NOT RAISE TypeError` (`politica` no era obligatoria). Pasaban los 4 «sin
  truncado» y «la SQL y el `max_rows` no cambian» (no regresión, D2).

### Decisiones del Bloque C

- **Estados** (`estado_busqueda`): sin resultado o resultado desconocido → `sin_rastro`
  (nunca se afirma que no hay contrato); CIF u obra distintos → `desfasada`, **manda sobre el
  resultado** (los datos de hoy no se buscaron, aunque la búsqueda vieja fallara); si
  coinciden, `error`, `sin_datos` o `vigente`. CIF normalizado como lo sella sv3
  (`strip().upper().replace(" ", "")`); los literales de resultado se atan a los de sv3 con un
  test que lee su `contrato_models.py` (sv4 no puede importar sv3).
- **Plantilla**: el aviso sale sin contratos y, con contratos, en `desfasada`, `error` y
  `sin_datos`. Caso no enumerado por R23: `vigente` + `encontrados` pero 0 contratos listados
  (contrato compartido reasignado por el UPSERT de sv3) → «encontró contratos, pero ahora no
  figura ninguno asociado; vuelve a buscar». La fecha pasa por `fecha_hora_local`.
- **D4-A (T13 bis)**: la lógica vive en `ReviewService` (testeable sin FastAPI); el endpoint
  solo la cablea. Relanza con `desfasada` (y sin rastro desde O-C1, abajo). **No relanza**
  al **aprobar** (aprobar no es «Guardar») ni en los PUT sin `?buscar_si_cambia=1`. Solo `sendSave(false)` lo
  manda (botón «Guardar» y el autoguardado al elegir obra/proveedor en el combo); «Guardar y
  volver a buscar», elegir contrato y «Valorar ahora» no, para no publicar dos veces en
  `q-persistencia` (sv3 podría valorar dos veces). Un fallo al relanzar no deshace el
  guardado: outcome `sigrid_error` con mensaje. «Buscando…» solo si el outcome es `queued`
  (`?buscando=1`); el JS sondea `GET /api/documents/{id}` cada 3 s hasta que el estado cambia
  y recarga sin el parámetro (tope 60 s y aviso).
- **O-B4**: el deshacer restaura la fila entera: CIF, obra y rastro vuelven juntos y el
  siguiente «Guardar» sin cambios no busca (`test_f052_d4a_ob4_*`, SQLite). Límite previo: no
  restaura `albaran_contratos_merge` (los contratos nuevos siguen listados).
- **T15**: mismas salidas que sv3, con la extensión (a) de R21 (`replace` fallido sella `error`
  y re-lanza). `ContratoRefetchService` de sv4: no cableado, deuda previa (solo cambia su import).
- **T17**: sin seam nuevo en el cliente; el test cambia `httpx.HTTPTransport` con `monkeypatch`.
  Un truncado de proveedores llega al endpoint como excepción → `ok=false` (ya existía).

Mutantes manuales del Bloque C (sobre HEAD, revertidos con `git checkout`; los 6 ficheros
nuevos, 94 tests): **12/12 muertos** — M1 comparar solo el CIF, M2 CIF sin quitar espacios,
M3 relanzar también con `error`, M4 aprobar relanza, M5 el local sella siempre `ninguno`,
M6 proveedores `TOLERA`, M7 el desfase pinta el CIF actual, M8 «buscando» con cualquier
outcome, M9 sin rastro = vigente, M10 `replace` fallido sin sello, M11 sin aviso de error
con contratos listados, M12 el repositorio no valida el resultado.

## Correcciones de review (CR-C1, CR-C2, O-C1) · decisiones del humano del 2026-10-01

| Cambio (commit) | Qué | RED | GREEN |
|---|---|---|---|
| CR-C1 `a7abcff` (+ `e8c62ab` imports) | `ruesma_comun/obras/{__init__,codigo}.py::normalizar_codigo_obra` con la semántica de sv3; sv3 (5 servicios) y sv4 (`busqueda_contratos`, `LocalContratoRefetchClient`, `ContratoRefetchService` muerto) la importan; borradas las dos copias `obra_code_normalizer.py`; `sv3.md`, `sv4.md`, design §5 y T12 al día | sv4 `-k cr_c1` contra `9c43f79`: `9 failed, 6 passed`; comun `test_f052_obras_codigo.py`: `1 error` | sv4 15, comun 15 |
| O-C1 `f034384` | `debe_relanzar_busqueda`: también `sin_rastro`; aviso con «Buscando…» también con contratos listados (`bc_buscando`, `data-estado-inicial`); el JS espera a que cambie el estado inicial; mensaje «Buscando contratos con el CIF y la obra guardados…» | `test_f052_d4a_guardar_relanza.py` contra `e8c62ab`: `7 failed, 25 passed` | 32 passed |
| CR-C2 `9d0c258` | T22 con los dos casos (con rastro / sin rastro) y las dos decisiones en design §11 (250/250) | documental | — |

- **CR-C1 RED**: `E       AssertionError: assert 'desfasada' == 'sin_datos'` ×4 (`12`, `7`,
  `1234`, `1001`); `E       AssertionError: assert (['f052-doc-00...00-000026122'] == []` ×2
  (cada «Guardar» relanzaba); `E       AssertionError: assert 'no_results' == 'skipped_missing_data'`
  ×2 (el local consultaba Sigrid con `0012`/`1234`); `copia local de la normalización:
  ...albaranes-front/application/services/obra_code_normalizer.py`. Comun:
  `E   ModuleNotFoundError: No module named 'ruesma_comun.obras'`. Pasaban `12345`, `abc`, `""`
  y las 3 obras válidas (iguales en las dos copias).
- **O-C1 RED**: `E       AssertionError: assert [] == ['f052-doc-00...00-000026122']` ×3 (sin
  rastro no buscaba); `where False = debe_relanzar_busqueda(BusquedaContratosVista(estado='sin_rastro', ...))`;
  `assert 'id="busqueda-buscando"' in ...` ×2; diff del mensaje de guardado.
- **Sin bucle** (`test_f052_oc1_sin_rastro_y_obra_invalida_busca_una_vez_y_no_en_bucle`): sin
  rastro y obra `12` → 1 búsqueda; sv3 sella `sin_datos` (obra `None`); dos «Guardar» más → 0.
  Riesgo residual: si sv3 no sella nada (servicio con `enabled=False` o excepción antes del
  sello, O-B1), cada «Guardar» de un documento sin rastro vuelve a publicar.
- **sv3 sin cambio de comportamiento**: el cuerpo de la función es el de sv3 tal cual; `357
  passed` antes y después. Los scripts `scripts/diagnose_*.py` de sv3 llevan su propia copia
  (scripts sueltos, no importan el módulo): no se tocan. `normalizar_codigo` de F-048 es otra
  cosa (forma de comparación sin ceros): test que las distingue.
- **Pendiente para el líder**: R31 (requirements, 150/150) sigue diciendo «guardar debe mostrar
  el aviso de R24»; T22 ya describe el flujo real. `ruesma_comun` gana `obras/`: sv3 y sv4 deben
  reconstruirse juntos (ya era el orden sv3 → sv4).
- Mutantes manuales de las correcciones: **5/5 muertos** (4 dígitos sin exigir `0`, `zfill` de
  1–3 dígitos, sin rastro no relanza, «buscando» solo con desfase, aviso sin `bc_buscando`).

## Ficheros tocados

- A: `services/albaranes-comun/ruesma_comun/sigrid/{__init__,lectura}.py` y su test; sv3
  `infrastructure/sigrid/sigrid_api_contrato_client.py` y `tests/{doble_sigrid_api,
  test_f052_doble_sigrid_api,test_f052_truncado_cliente,test_f052_paginacion_cliente,
  test_f052_resumen_obra,test_f052_equivalencia_familias}.py`.
- B (sv3): `application/services/{header_resolver_service,contrato_enrichment_service}.py`,
  `domain/models/contrato_models.py`, `domain/ports/contrato_merge_repository_port.py`,
  `infrastructure/database/{phase2_ddl,orm_models,sqlalchemy_albaran_repository}.py`,
  `tests/test_f052_{nota_proveedor,rastro_busqueda}.py`.
- C (sv4, `services/albaranes-front/`): nuevo `application/services/busqueda_contratos.py`;
  modificados `application/services/review_service.py`, `domain/models/review_models.py`,
  `infrastructure/database/{orm_models,review_repository}.py`,
  `infrastructure/sigrid/{local_refetch_client,sigrid_lookup_client}.py`,
  `interface_adapters/web/app.py`, `templates/document_detail.html`, `static/{app.js,styles.css}`;
  tests nuevos `tests/test_f052_{busqueda_contratos,rastro_detalle,bloque_contrato,
  d4a_guardar_relanza,refetch_local_rastro,lookup_truncado}.py`.
- Correcciones: nuevo `ruesma_comun/obras/` y `tests/test_f052_obras_codigo.py`; sv3
  `application/services/{contrato_enrichment,contrato_refetch,header_grounding,header_resolver,
  obra_enrichment}_service.py` (solo el import), `sv3.md`, `sv4.md`, spec (design, tasks).

## Fuera del alcance / pendiente

- Bloque D: T14 (script de verificación), T16 (`azure-apps/albaranes.md`), T18
  (`docs/ARCHITECTURE.md`); T19 (campaña de mutación). `ruesma_comun` sigue en 0.6.0.
- **Sin test automático** (sv4 no tiene tests de FastAPI ni de JS): el cableado del PUT
  (`buscar_si_cambia`, `redirect_url` con `buscando=1`, `busqueda_relanzada`), el parámetro
  `buscando` de la ficha y el sondeo de `app.js` (`node --check` OK). Se ven en **T22 (MANUAL,
  humano)**, reescrita en CR-C2 con los casos con rastro y sin rastro.
- La SQL agregada solo se ha probado contra el doble: T20 y T21 (MANUAL) lo verifican.
- **Para T16/T18**: sigrid-api tiene `MAX_ALLOWED_ROWS=500000`; el 1.000 era el `max_rows` del
  cliente de sv3. Corregir «1.000 filas por petición» en `albaranes.md`; avisar a los dueños de
  `PycharmProjects/CLAUDE.md:27`, `azure-apps/{datamart_seg_anual,remesas,postventa_incidencias}.md`.
  Además: 4 columnas `contratos_busqueda_*` (dueño sv3, lector y escritor del fallback sv4),
  orden de despliegue sv3 → sv4, `HeaderGroundingService` toma los 200 primeros por CIF de
  3.543 (O1 de la review A) y el lookup de sv4 lanza si los proveedores de la obra truncan.

## Evidencias

| Evidencia | Valor medido |
|---|---|
| Tests F-052 nuevos | A **82**, B **73**, C **94**, correcciones **+33** (comun 15, sv4 18); total **282**, en verde |
| Suites a mano tras las correcciones, una tras otra | comun `323 passed in 17.43s`; sv3 `357 passed in 2.84s`; sv4 `359 passed in 10.05s` |
| `bash harness/init.sh` final (`1d2bcb6`) | ENTORNO LISTO, exit 0; raíz `1067 passed in 207.46s`; sv4 `341 passed in 21.12s`; resto en caché; `PUERTA COBERTURA: 98.0% de 252 líneas cambiadas cubiertas (247/252, umbral 80%, nivel critico)` (las 5 sin cubrir, cableado de `app.py`: ver «pendiente»); tamaño `impl 195/220`; ruff 1166 (1167 al empezar el bloque) |
| Tiempo de la suite | sv4 6–17 s; sv3 3,8–10,6 s; comun 38,5 s; raíz 257–327 s |
| Mutación | Campaña: T19 (fuera). Manuales: A 1 (+2 review), B **7/7**, C **12/12** muertos |
