# F-052 · Informe del implementer

Rama `feature/F-052-proveedores-truncados`. Rigor **critico**. Spec v2 aprobada
por el humano el 2026-09-30. Condensado el 2026-10-01 para caber en el tope: las trazas
RED literales y las decisiones completas de A, B y C siguen en
`git show ce6bbd4:progress/impl_F-052.md` (y se reproducen con el test indicado sobre el
commit anterior al de la tarea, como hicieron los reviewers).

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

Decisiones A: doble con `truncated = filas >= max_rows`; `search_proveedores(max_rows=5000)` = tamaño de página (desde T14 bis, `PAGINA_MAXIMA`); resumen ordenado por `(cif, nombre)` y deduplicado por CIF (R5).

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
- **T7 · R1 contra el cliente anterior a T5 (O-B3)**: cliente de `6d9c795` + resolver de
  `f766178` → `1 failed`, nota «ningún proveedor ... casa» (el bug de SS-0026122); con el
  resolver de T7, la nota ya dice «no se pudo consultar»: R15 no depende de T5.
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

## Bloque C (T11–T13 bis, T15, T17) · sv4 · APROBADO

RED: fichero nuevo contra el commit anterior, `.venv/Scripts/python.exe -m pytest <fichero> -q`
en sv4. Orden **T12 antes que T11** (el repositorio de T11 necesita la vista de T12).

| Tarea (commit) | Qué | RED | GREEN |
|---|---|---|---|
| T12 `8fa6a5b` | `estado_busqueda` (5 estados), `BusquedaContratosVista`, `RastroBusquedaContratos` (R27) | `ModuleNotFoundError: No module named 'application.services.busqueda_contratos'` — `1 error` | 21 passed |
| T11 `d1cf760` | ORM con las 4 columnas, `busqueda_contratos` en el detalle | `el ORM de sv4 no declara contratos_busqueda_cif`, `KeyError: 'busqueda_contratos'` — `6 failed` | 6 passed |
| T13 `4840421` | Plantilla: mensaje por estado (R23–R26), también con contratos listados | `assert 'todavía no se han buscado' in ...` (pintaba el CIF actual), `R23 exige la fecha` — `9 failed, 2 passed` | 11 passed |
| T13 bis `d954765` | D4-A: «Guardar» relanza si cambian CIF u obra; «buscando…» + sondeo en `app.js` | `ImportError: cannot import name 'debe_relanzar_busqueda'` — `1 error` | 27 passed |
| T15 `3ec5cb4` | `LocalContratoRefetchClient` sella el rastro (R21, R22) | `assert [] == [('f052-doc-0... 'sin_datos')]` ×4, `no attribute 'sellar_busqueda_contratos'` — `17 failed, 2 passed` | 19 passed |
| T17 `b8a9064` | Lookup de sv4 con `politica` obligatoria; proveedores `NO_TOLERA` (R28) | `DID NOT RAISE SigridRespuestaTruncada`, `DID NOT RAISE TypeError` — `5 failed, 5 passed` | 10 passed |

Decisiones C (detalle en `ce6bbd4`): `desfasada` manda sobre el resultado; resultado
desconocido → `sin_rastro`; CIF normalizado como lo sella sv3; aviso también con contratos
listados si está desfasado, falló o no se buscó; D4-A vive en `ReviewService`, no relanza al
aprobar ni en PUT sin `?buscar_si_cambia=1`; «buscando…» solo con outcome `queued`, sondeo
3 s y tope 60 s; O-B4 caracterizado; T15 con la extensión (a) de R21. Mutantes manuales C:
**12/12 muertos**.

## Correcciones de review del Bloque C (2026-10-01) · APROBADAS

| Cambio (commit) | Qué | RED | GREEN |
|---|---|---|---|
| CR-C1 `a7abcff` `e8c62ab` | `ruesma_comun.obras.normalizar_codigo_obra` (semántica de sv3); sv3 y sv4 la importan | sv4 `-k cr_c1`: `assert 'desfasada' == 'sin_datos'` ×4 — `9 failed, 6 passed`; comun `No module named 'ruesma_comun.obras'` | 15 + 15 |
| O-C1 `f034384` | Sin rastro, el primer «Guardar» busca una vez | `assert [] == ['f052-doc-00...']` ×3 — `7 failed, 25 passed` | 32 passed |
| CR-C2 `9d0c258` | T22 con y sin rastro; design §11 | documental | — |
| CR-C3 `6d593b3` `3be4ecb` | Sin CIF ni obra no relanza; solo-front: `merge_existe` | `ContratoRefetchOutcome(status='queued'...) is None` ×6 — `6 failed, 4 passed`; `KeyError` — `2 failed, 22 passed` | 10 + 24 |
| O-C6 `cc13df2` | R31 alineado con D4-A y remitido a T22 | documental | — |

Mutantes manuales de las correcciones: **10/10 muertos**. sv3 sin cambio de comportamiento
(357 antes y después de CR-C1).

## Bloque D (T14, T14 bis, T18, T16, versión) · 2026-10-01

| Tarea (commit) | Qué | RED | GREEN |
|---|---|---|---|
| T14 `36713de` `2c6a3f7` | `scripts/verificar_f052_proveedores_obra.py` (R29, R30, design §8) + tests contra el doble | `test_f052_script_verificacion.py`: `ImportError: cannot import name 'verificar_f052_proveedores_obra' from 'scripts'` — `1 error` | 35 passed |
| T14 bis `f25be76` | Página por defecto 499.999 y `max_rows` ≤ 500.000 (decisión del humano) | comun: `ImportError: cannot import name 'PAGINA_MAXIMA' from 'ruesma_comun.sigrid'` — `3 failed, 31 passed`; sv3 `test_f052_paginacion_cliente.py`: `assert [0, 5000] == [0, 499999]`, `ValueError: too many values to unpack (expected 1)` (2 peticiones), `assert [1000, 1000, 1000] == [500000, 500000, 500000]`, `DID NOT RAISE ValueError` ×5 — `8 failed, 8 passed` | 34 + 16 |
| T18 `ed6068a` | `docs/ARCHITECTURE.md` «Acceso a datos» | documental | — |
| T16 `141f9aa` (azure-apps) + `b8fb4c2` | `azure-apps/albaranes.md` §3 y §8 nuevo | documental | — |
| 0.7.0 `a7e8732` | `ruesma_comun` 0.7.0 (`pyproject.toml`, `__version__`, README) | `assert '0.6.0' == '0.7.0'` — `1 failed` | 1 passed |

**T14 · el script** (solo lectura; `python -m compileall` OK; NO ejecutado contra sigrid-api).
Construye `SigridApiContratoClient` como `composition.py`, desde `config.settings.Settings`
(el `.env` de sv3); si el `.env` no valida, dice qué campos sin enseñar valores. Le inyecta
`TransporteQueMide` (el seam `transport` de T2): un `HTTPTransport(retries=1)` nuevo por
petición, como el cliente, que anota filas, `truncated`, bytes y segundos sin tocar nada.
Modos: `--obra X [--cif --nombre --repeticiones N]` (R29: la agregada N veces por el método
público `fetch_contratos_resumen_por_obra`, CIF dentro, score con `_score_razon_social` y el
criterio de `_mejor_candidato_por_nombre`, umbral `HEADER_RESOLVER_MIN_SCORE`, y
`fetch_contratos` con sus peticiones `header_and_lines`); `--comparar-familias --obra A
--obra B` (R30: agregada frente a la consulta por líneas de antes de F-052 sin tope, familias
por CIF con `familias_de_texto`, CIF de más/de menos frente a `fetch_proveedores_por_obra`);
`--listar-obras-grandes` (design §8, `HAVING COUNT(*) > 1000`; imprime la lista para el
SELECT de T23). Termina con `RESULTADO …: OK` (0) o `FALLA` + motivos (1); argumentos u obra
inválidos: 2, sin consultar. Obras normalizadas con `normalizar_codigo_obra` (`691` → `0691`).
Errores redactados (clave y URL → `***`); `configurar_logs()` silencia el INFO del cliente
(escribe la URL) solo al ejecutarlo como script. Usa dos privados del cliente
(`_post_sql_read`, `_database`) para sus dos SQL propias: aceptable en un script de
diagnóstico del mismo servicio. El doble gana la consulta de obras grandes. R29 «< 15 s»:
15,00 s ya falla (test de frontera).

**T14 bis · tamaño de página** (decisión del humano, 2026-10-01). `ruesma_comun.sigrid` gana
`MAX_FILAS_POR_PETICION = 500_000` y `PAGINA_MAXIMA = 499_999`; `leer_paginado` rechaza
`pagina > PAGINA_MAXIMA` antes de pedir nada. sv3: `pagina_lineas` y `search_proveedores`
por defecto `PAGINA_MAXIMA` (una petición: máx. medido 989 líneas y 3.543 proveedores);
`max_rows` del cliente por defecto 500.000 (las lecturas simples —agregada ≤ 163, proveedores
de la obra ≤ 193, TOP 1, documentos— pierden el precipicio de 1.000; `NO_TOLERA` sigue
detrás). `__init__` rechaza `max_rows` o `pagina_lineas` fuera de rango y `_enviar_sql_read`
cualquier `max_rows` > 500.000. `truncated` y el tope de 20 páginas, intactos. Los 230 s: cada
lectura sigue acotada por `timeout_s` (30 s, `SIGRID_API_TIMEOUT_S`), no por las filas. No era
configurable por settings (D3) y sigue sin serlo: `composition.py` y `app.py` no pasan ni
`max_rows` ni página, así que heredan los nuevos valores por defecto. Tests: el de 1.200 líneas en dos páginas pasa
a `pagina_lineas=1000` explícito; nuevos: 1.200 líneas en UNA petición, `max_rows` 500.000 en
las lecturas simples, límites justos admitidos y fuera de rango rechazados sin petición.
Design §2/§3 actualizado en sitio (250/250); `tasks.md` gana T14 bis. Fuera (D6, O-C4): el
`SigridApiContratoClient` de sv4 (1.000) y `SigridApiObraClient` de sv3.

**T18**: «Acceso a datos» dice 500.000 (leído el 2026-09-30), que el 1.000 era el `max_rows`
del cliente (y no 10.000), las tres reglas (`truncated` nunca en silencio, agregar en SQL antes
que paginar, paginar con `ruesma_comun.sigrid`) y que `sigrid/` + `obras/` solo los importan
sv3 y sv4 (sv3 → sv4). `sv3.md` y `sv4.md` no citan el 1.000: sin cambios.
**T16** (azure-apps, solo commit local): §3 con las 4 columnas (dueño sv3, lector sv4, escritor
del solo-front) y orden sv3 → sv4 (O-C3); §8 nuevo: `truncated` comprobado y políticas,
1.000 = `max_rows` del cliente, agregada con dependencia de `WITH` + `FOR XML PATH`, paginadas
con página de 499.999, grounding con los 200 primeros por CIF (O1), `ruesma_comun` 0.7.0
obliga a reconstruir sv3 y sv4 juntos (O-C7). Ningún otro documento de azure-apps tocado.

Mutantes manuales D (revertidos; sv3 suite completa, comun su fichero): **17/17 muertos** tras
endurecer 2 tests (`2c6a3f7`: sobrevivían «R30 sin contar CIF distintos» y «propuesta sin
umbral»). Script: frontera de 15 s, `>=` en el empate, `de_mas` vacío, sin `strip`, CIF
dentro, redactar sin efecto, sin fallo con 0 contratos, `truncated` ignorado. Página: valores
por defecto a 1.000/5.000, sin guarda de `max_rows`, sin guarda de página en sv3 y en comun,
`PAGINA_MAXIMA` igual al tope.

## Ficheros tocados

- A y B: `git show --stat` de los commits de sus tablas.
- C y correcciones: sv4 `application/services/{busqueda_contratos,review_service}.py`,
  `domain/models/review_models.py`, `infrastructure/database/{orm_models,review_repository}.py`,
  `infrastructure/sigrid/{local_refetch_client,sigrid_lookup_client}.py`,
  `interface_adapters/web/app.py`, `templates/document_detail.html`, `static/{app.js,styles.css}`;
  `ruesma_comun/obras/`; 6 tests nuevos de sv4 y 1 de comun.
- D: nuevos `services/albaranes-persistencia/scripts/verificar_f052_proveedores_obra.py` y
  `tests/test_f052_script_verificacion.py`; modificados `tests/doble_sigrid_api.py`,
  `tests/test_f052_paginacion_cliente.py`, `infrastructure/sigrid/sigrid_api_contrato_client.py`,
  `ruesma_comun/sigrid/{__init__,lectura}.py`, `ruesma_comun/__init__.py`, `pyproject.toml`,
  `README.md` y `tests/test_f052_sigrid_lectura.py` de comun, `docs/ARCHITECTURE.md`, spec
  (design §2/§3, tasks); fuera del repo, `azure-apps/albaranes.md`.

## Fuera del alcance / pendiente

- **T19** (campaña de mutación completa; crítico: 0 supervivientes sin justificar). Incluirá el
  script de T14, que cuenta como producción (`scripts/` no está excluido del alcance).
- **MANUAL (humano)**: T20 (R29) y T21 (R30) con el script, solo lectura; T22 (R31, pipeline
  local; cubre el cableado de D4-A, sin tests de FastAPI ni de JS); T23 tras desplegar sv3 → sv4.
- La SQL agregada y la de obras grandes solo se han probado contra el doble (T20, T21, T23).
- **Para el líder** (fuera de mi alcance): `PycharmProjects/CLAUDE.md` («como máximo 1.000 filas
  por petición») y `azure-apps/{sigrid_api,datamart_seg_anual,remesas,postventa_incidencias}.md`
  si repiten el 1.000 son de otros dueños. Siguen abiertas O-C4 (copia de `header_and_lines` de
  sv4 con `max_rows=1000`, D6), O-C5 y O-B2 (extensiones de R21, a decidir en el cierre).
  Despliegue: `ruesma_comun` 0.7.0 va en sv3 y sv4, orden sv3 → sv4 (lo lanza el humano).

## Evidencias

| Evidencia | Valor medido |
|---|---|
| Tests F-052 nuevos | A **82**, B **73**, C **94**, correcciones **+46**, D **+47** (sv3 35 del script y 8 de paginación, comun 4); total **342**, en verde |
| Suites a mano tras el Bloque D, una tras otra | sv3 `400 passed in 8.78s`; comun `327 passed in 38.29s`; sv4 `372 passed in 18.19s` (sin cambios en sv4; comun cambió) |
| `bash harness/init.sh` final | tras `ebd6905`: ENTORNO LISTO, exit 0; raíz `1067 passed in 378.14s`; sv3 `400 passed in 16.92s`; comun `327 passed in 62.80s`; sv4 en verde (caché); `PUERTA COBERTURA: 97.5% de 601 líneas cambiadas cubiertas (586/601, umbral 80%, nivel critico)` (las 11 de antes + 4 del script que solo corren al ejecutarlo: inserción en `sys.path`, import de `Settings` y el bloque `__main__`); tamaño `impl 192/220`; ruff 1166 (los 16 avisos nuevos del Bloque D, corregidos en `ebd6905`) |
| Tiempo de la suite | sv3 8,5–23 s; comun 38–85 s; sv4 18 s; raíz 257–458 s |
| Mutación | Campaña: T19 (fuera). Manuales: A 1 (+2 review), B **7/7**, C **12/12**, correcciones **10/10**, D **17/17** muertos |
