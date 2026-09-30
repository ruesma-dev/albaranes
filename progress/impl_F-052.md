# F-052 · Informe del implementer

Rama `feature/F-052-proveedores-truncados`. Rigor **critico**. Spec v2
aprobada por el humano el 2026-09-30.

## Bloque A (T1–T6) · resumen

Trazas RED condensadas a su línea clave; la traza completa se reproduce con
el test indicado sobre el commit anterior al de la tarea (el reviewer
reprodujo las de T4 y T5/T6, `progress/review_F-052_bloqueA.md`).

| Tarea (commit) | Qué | RED (comando: `pytest <fichero> -q` en su servicio) | GREEN |
|---|---|---|---|
| T1 `5588131` | `ruesma_comun/sigrid/{__init__,lectura}.py`: `PoliticaTruncado`, `SigridRespuestaTruncada(etiqueta, filas)`, `comprobar_truncado`, `con_paginacion`, `leer_paginado` (R8, R9, R14) | `test_f052_sigrid_lectura.py`: `ModuleNotFoundError: No module named 'ruesma_comun.sigrid'` — `1 error` | 29 passed |
| T2 `dcf9292` | Doble `tests/doble_sigrid_api.py` + kwarg `transport` del cliente | `test_f052_doble_sigrid_api.py`: `TypeError: SigridApiContratoClient.__init__() got an unexpected keyword argument 'transport'` — `1 failed, 10 passed` | 11 passed |
| T3 `cd17ae9` | `_post_sql_read(politica, max_rows=None)` = `_enviar_sql_read` + `comprobar_truncado`; política de las 7 consultas (design §3); docstring del falso tope corregido (R7–R10) | `test_f052_truncado_cliente.py`: `unexpected keyword argument 'politica'`, `DID NOT RAISE SigridRespuestaTruncada` ×5, `assert '10.000' not in ...` — `12 failed, 1 passed` | 13 passed |
| T4 `6d9c795` | `_post_sql_read_paginado` (`max_rows = pagina + 1`); `header_and_lines` y `search_proveedores` paginadas; kwargs `pagina_lineas=1000`, `max_paginas=20` (R11–R13) | `test_f052_paginacion_cliente.py` contra el cliente de T2 (`dcf9292`, ya con `transport`; O6): `assert [500, 500] == [500, 700]` (200 líneas perdidas en silencio), `assert 1000 == 3543`, **`assert 1000 > 5000`** (hallazgo: `search_proveedores(max_rows=5000)` enviaba 1.000) — `7 failed, 1 passed` | 8 passed |
| T5 `69883cb` | `fetch_contratos_resumen_por_obra` con `_SQL_RESUMEN_OBRA_AGREGADO` (design §4 literal), una llamada, `NO_TOLERA` (R2, R3, R5) | `test_f052_resumen_obra.py` contra T4: `SigridRespuestaTruncada ... [contratos_resumen_obra_0691]: 1000 filas recibidas`, `assert 0 == 81` — `9 failed, 10 passed` (junto con T6) | 12 passed |
| T6 `fe717bd` | `test_f052_equivalencia_familias.py`: familias por CIF del texto agregado == texto por líneas (0691, 0668) + 4 casos dirigidos (R4) | los 2 `r4_mismas_familias[0691\|0668]` FAILED en la misma ejecución que T5 | 7 passed |

Mutante manual de T6 «leer `nombre` en vez de `texto`» (`sed` sobre el
cliente, revertido con `git checkout`): **muerto** —
`AssertionError: assert {'B10000000':..., set()), ...} == {}` (80 CIF difieren).

### Decisiones de diseño

- Doble: `truncated = filas >= max_rows` («se alcanzó», `sigrid_api.md` §6.1),
  `max_rows` por defecto 200, `OFFSET` sin `ORDER BY` → 400; semilla
  `20260930`; SALMEDINA en las filas 1.500–1.504 de la consulta antigua.
- `search_proveedores(max_rows=5000)`: el kwarg pasa a ser el **tamaño de
  página** (el puerto y los llamantes no lo pasan; documentado en el docstring).
- Resumen de la obra: filas ordenadas en Python por `(cif, nombre)` y dedupe
  por CIF quedándose la primera (= la de la SQL, `ORDER BY p.cif, p.raz`);
  salida independiente del orden de llegada (R5). Ver O4 de la review
  (collation frente a punto de código: solo afecta al nombre mostrado).
- `ruff` limpio en los ficheros nuevos (`221e34d`).

### Correcciones de review (CR-A1, CR-A2)

- **CR-A1** `2caa1c9`: `test_f052_r5_mismo_ganador_y_misma_nota_con_tres_barajados`
  fija por caso el resultado esperado (`(B82899550, "deterministic")`; nota con
  «Candidatos con contrato en la obra 0691»; `(B10000000, "deterministic")`) y
  comprueba una sola petición (la agregada) y ningún `search_proveedores`.
  RED contra el cliente de T4 (`git show 6d9c795:...` temporal, revertido):
  `AssertionError: assert (None, 'deterministic') == ('B82899550', 'deterministic')`,
  `... == ('B10000000', 'deterministic')` — `3 failed, 9 deselected`.
- **CR-A2** `1a18615`: `leer_paginado` lanza `RuntimeError` (etiqueta, nº de
  página y recuentos, sin datos) si una página trae más filas que las pedidas,
  con cualquier política. Test
  `test_f052_r14_leer_paginado_pagina_con_filas_de_mas_lanza[TOLERA|NO_TOLERA]`
  con una fuente de `tamano + 1`. RED: `Failed: DID NOT RAISE RuntimeError` —
  `2 failed, 29 passed`. GREEN: `31 passed`.

### Lo que usan los bloques siguientes de la API del Bloque A

- `fetch_contratos_resumen_por_obra`: truncado → `SigridRespuestaTruncada`
  (`RuntimeError`, `.etiqueta`, `.filas`); `error_xml`, HTTP ≥ 400, `ok=false`
  → `RuntimeError`; candidatos completos, ordenados por CIF y deduplicados.
- `fetch_contratos` pagina (1.000/pág.) y lanza `SigridRespuestaTruncada` al
  pasar de `max_paginas` (20). `search_proveedores()`: lista global completa.
- Doble: `DobleSigridApi(error_xml=True | forzar_truncado=True | barajar=n)`,
  `.cliente(**kw)`, `.peticiones_con(fragmento)`, `CIF_SALMEDINA`, `RAZ_SALMEDINA`.
- **Para T16 (O1 de la review)**: `HeaderGroundingService`
  (`header_grounding_service.py:328-348`) toma los 200 primeros de
  `search_proveedores()`: antes de una lista cortada a 1.000 sin orden, ahora
  los 200 primeros por CIF de 3.543, y un truncado lanza. Anotarlo en
  `azure-apps/albaranes.md`.

## Bloque B (T7–T10) · sv3

RED de cada tarea: el fichero de test nuevo contra el commit anterior, con
`cd services/albaranes-persistencia; python -m pytest <fichero> -q`. Sin red ni BBDD.

| Tarea (commit) | Qué | RED | GREEN |
|---|---|---|---|
| T7 `8085dd4` | `_mejor_candidato_por_nombre` → `(candidato, motivo, n)`; `_red_proveedor_por_cif` redacta la nota de design §6 por motivo (R1, R5, R15–R19) | `test_f052_nota_proveedor.py` contra `f766178`: **`19 failed, 9 passed`** | 28 passed |
| T8 `f7e86ef` | `_resolver_por_obra_y_familia`: `SigridRespuestaTruncada` → WARNING con obra, etiqueta y filas; el resto sigue con `logger.exception`; ambos degradan al fallback global (R6) | `-k r6_familia` contra `8085dd4`: **`1 failed, 3 passed`** | 4 passed |
| T9 `1df8ef5` | 4 `ALTER ... ADD COLUMN IF NOT EXISTS contratos_busqueda_*` en `phase2_ddl.py`, ORM del merge, constantes de resultado en `contrato_models.py`, `sellar_busqueda_contratos` en puerto y repositorio (R20) | `test_f052_rastro_busqueda.py` contra `f7e86ef`: **`13 failed, 2 passed`** | 15 passed |
| T10 `fed1bfa` | `enrich_merge_document` sella el rastro en cada salida, best-effort (R21, R13) | mismo fichero contra `1df8ef5`: **`24 failed, 17 passed`** | 41 passed |

Trazas RED (extracto literal de la salida):

- **T7**: `E       TypeError: cannot unpack non-iterable ProveedorObraResumen object`;
  `E       assert 'no se pudo consultar la lista de proveedores de la obra 0691 (fallo al consultar Sigrid): no hay propuesta' in "[AVISO] Proveedor el CIF leido B82890580 no existe en Sigrid y ningun proveedor con contrato en la obra casa con el nombre leido ('SALMEDINA'). Revisa el proveedor en el portal."`
  (con `error_xml`: la mentira de R15); `E       AssertionError: assert None == (None, 'sin_obra', 0)`;
  `E       assert 'ninguno de los 3 proveedores con contrato en la obra 0691' in "[AVISO] ... ningun proveedor con contrato en la obra casa con el nombre leido ('TRANSPORTES MACOTRAN')..."`.
  Los 9 que pasaban: R1 de punta a punta y R5 ×3 (verdes desde T5, O5) y R19 ×5
  (prefijo y motivo no cambian: son de no regresión).
- **T7 · R1 contra el cliente anterior a T5** (O5; `git show 6d9c795:.../sigrid_api_contrato_client.py`
  sobre el árbol, revertido con `git checkout`): `test_f052_r1_la_red_por_nombre_propone_salmedina_con_el_cliente_real`
  → `E       assert 'PROPUESTA: B82899550 — SALMEDINA, S.L.' in "[AVISO] Proveedor el CIF leido B82890580 no existe en Sigrid y ningun proveedor con contrato en la obra casa con el nombre leido ('SALMEDINA')..."` — `1 failed`.
  Con ese cliente la consulta antigua lanzaba `SigridRespuestaTruncada` (1.000 filas) y la
  nota decía «ningún casa»: el bug de SS-0026122 y la mentira de R15 a la vez.
- **T8**: `test_f052_r6_familia_truncado_warning_con_la_obra_y_fallback` →
  `E       ValueError: not enough values to unpack (expected 1, got 0)` en
  `[aviso] = _registros_de_la_obra(caplog, logging.WARNING)` (antes solo ERROR). Los 3
  que pasaban fijan el degradado que ya existía (error_xml → `search_proveedores`).
- **T9**: `E           AssertionError: falta el ALTER de contratos_busqueda_cif`;
  `E       assert 0 == 4`; `E           AssertionError: el ORM no declara contratos_busqueda_cif`;
  `E       AttributeError: type object 'ContratoMergeRepository' has no attribute 'sellar_busqueda_contratos'`;
  `AttributeError: 'SqlAlchemyAlbaranRepository' object has no attribute 'sellar_busqueda_contratos'` ×9.
  Los 2 que pasaban eran vacíos sin columnas (exportación de `schema_contribution` y
  «la tabla raw no lleva el rastro»); con T9 dejan de serlo.
- **T10**: `E       AssertionError: assert [] == [('doc-f052-r... 'sin_datos')]`,
  `... == [('doc-f052-r...91', 'error')]`, `... == [('doc-f052-r...', 'ninguno')]`,
  `... == [('doc-f052-r...encontrados')]` ×4 y R13 de punta a punta con el cliente real
  (1.200 líneas, páginas de 500, tope 2): `E       AssertionError: assert [] == [('doc-f052-r...68', 'error')]`.
  De los 17 que pasaban, 15 son de T9 y 2 vacíos sin sellado (servicio desactivado;
  repositorio sin el método).

### Decisiones del Bloque B

- **Textos de la nota**: cabeza intacta (`[AVISO] Proveedor el CIF leido X no existe en
  Sigrid`, sin tilde, como hoy) y cola literal de design §6 (con tildes), cerrada con
  «. Revisa el proveedor en el portal.». La propuesta no cambia.
- **Sin obra y sin nombre a la vez → `sin_obra`**: sin obra no hay lista que comparar
  (`test_f052_r16_sin_obra_ni_nombre_manda_la_obra`). `nadie_casa` con 0 proveedores
  dice «ninguno de los 0»: N es el número real (R18), aunque la frase sea tosca.
- **Constantes**: `MOTIVO_*` en el resolver; `BUSQUEDA_*` y
  `RESULTADOS_BUSQUEDA_CONTRATOS` en `domain/models/contrato_models.py`. El
  repositorio rechaza un resultado desconocido con `ValueError` antes de tocar la BBDD.
- **Rastro**: CIF y obra normalizados (`None` si faltan o no validan); la fecha la pone
  el repositorio (`datetime.now(timezone.utc).isoformat()`), el puerto no la recibe.
- **Dos salidas que la spec no enumera** (R21 dice «cuando termina»): (a) `replace_contratos`
  falla tras una consulta correcta → rastro **`error`**: el documento se queda sin
  contratos y ni `encontrados` ni `ninguno` serían verdad
  (`test_f052_r21_fallo_guardando_los_contratos_sella_error`); (b) servicio
  desactivado (`enabled=False`) → **sin sellado**: no hubo búsqueda. Si el líder o el
  humano prefieren otra cosa, es una línea en cada caso.
- `ruff`: sin avisos nuevos salvo 4 `ISC004` en las 4 sentencias del DDL, con el
  mismo estilo que el resto de `_PHASE2_DDL` (deuda previa del fichero).

Mutantes manuales del Bloque B (sobre el código commiteado, revertidos con
`git checkout`), con `test_f052_rastro_busqueda.py` + `test_f052_nota_proveedor.py`
(73 tests): **7 de 7 muertos** — `ninguno`→`encontrados` (1 fallo), quitar el sello
del `replace` fallido (3), `n=0` en `nadie_casa` (4), sin rama propia para el
truncado (1), `sin_nombre` antes que `sin_obra` (1), caché sella `ninguno` (1),
repositorio sin validar el resultado (4).

## Ficheros tocados

- Bloque A: nuevos `services/albaranes-comun/ruesma_comun/sigrid/{__init__,lectura}.py`
  y su test; en sv3 `tests/{doble_sigrid_api,test_f052_doble_sigrid_api,
  test_f052_truncado_cliente,test_f052_paginacion_cliente,test_f052_resumen_obra,
  test_f052_equivalencia_familias}.py`; modificado `infrastructure/sigrid/sigrid_api_contrato_client.py`.
- Bloque B (sv3, `services/albaranes-persistencia/`): modificados
  `application/services/{header_resolver_service,contrato_enrichment_service}.py`,
  `domain/models/contrato_models.py`, `domain/ports/contrato_merge_repository_port.py`,
  `infrastructure/database/{phase2_ddl,orm_models,sqlalchemy_albaran_repository}.py`;
  nuevos `tests/test_f052_{nota_proveedor,rastro_busqueda}.py`.
- Sin tocar: sv4 (Bloque C), `docs/` y `azure-apps` (Bloque D), `composition.py`, sv2.

## Fuera del alcance / pendiente

- sv4 (T11–T13 bis, T15, T17), T14, T16, T18 y la campaña de mutación (T19).
  MANUAL (humano): T20–T23; la escritura real del rastro en PG se ve en T22.
  `ruesma_comun` sigue en 0.6.0 (el versionado lo decide el líder).
- La SQL agregada solo se ha probado contra el doble: T20 y T21 lo verifican.
- **Para T16/T18 (dato del líder, leído en Azure el 2026-09-30)**: sigrid-api tiene
  `MAX_ALLOWED_ROWS=500000`; el tope de 1.000 lo ponía el propio cliente de sv3
  (`max_rows`), no la pasarela. Corregir «1.000 filas por petición» donde aparezca. Hoy
  aparece en `PycharmProjects/CLAUDE.md:27`, `azure-apps/datamart_seg_anual.md:117`,
  `azure-apps/remesas.md:283,495` y `azure-apps/postventa_incidencias.md` (varias): de
  esos, solo `albaranes.md` es nuestro; el resto se avisa a sus dueños (regla de
  propiedad de `azure-apps`).
- Para T16 además: el rastro son 4 columnas nuevas de `albaran_documents_merge`
  (dueño sv3, lector sv4) y el orden de despliegue sv3 → sv4.
- `progress/current.md` arrastra sesiones anteriores (C2 de la review): lo poda el líder.

## Evidencias

| Evidencia | Valor medido |
|---|---|
| Tests F-052 nuevos | Bloque A **82** (31 comun + 51 sv3); Bloque B **73** (32 `nota_proveedor` + 41 `rastro_busqueda`); total **155**, todos en verde |
| Suites a mano tras T10, una tras otra | comun `308 passed in 38.50s`; sv3 `357 passed in 6.07s` (284 → 357) |
| `bash harness/init.sh` tras T10 (antes del commit de estilo) | ENTORNO LISTO, exit 0; raíz `1067 passed in 327.10s`; sv3 `357 passed in 10.62s`; comun en caché (sin cambios); `PUERTA COBERTURA: 100.0% de 148 líneas cambiadas cubiertas (148/148, umbral 80%, nivel critico)`; tamaño `impl 175/220` |
| `bash harness/init.sh` final (tras ordenar imports según el `ruff` de la raíz) | ENTORNO LISTO, exit 0; raíz `1067 passed in 256.71s`; sv3 `357 passed in 8.99s`; `PUERTA COBERTURA: 100.0% de 148 líneas cambiadas cubiertas (148/148, umbral 80%, nivel critico)`; tamaño `impl 179/220`; ruff 1167 avisos (1163 al empezar: los +4 son los `ISC004` del DDL) |
| Tiempo de la suite | sv3 3,8–10,6 s; comun 38,5 s; raíz 327 s |
| Mutación | Campaña: T19 (fuera del bloque). Manuales: Bloque A 1 + 2 de la review, Bloque B **7/7 muertos** |
