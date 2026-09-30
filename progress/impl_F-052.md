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
| T4 `6d9c795` | `_post_sql_read_paginado` (`max_rows = pagina + 1`); `header_and_lines` y `search_proveedores` paginadas; kwargs `pagina_lineas=1000`, `max_paginas=20` (R11–R13) | `test_f052_paginacion_cliente.py` contra el código ORIGINAL: `assert [500, 500] == [500, 700]` (200 líneas perdidas en silencio), `assert 1000 == 3543`, **`assert 1000 > 5000`** (hallazgo: `search_proveedores(max_rows=5000)` enviaba 1.000) — `7 failed, 1 passed` | 8 passed |
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

### Lo que el Bloque B (T7–T10) tiene que saber de la API nueva

- **Excepciones de `fetch_contratos_resumen_por_obra`**: truncado →
  `ruesma_comun.sigrid.SigridRespuestaTruncada` (`RuntimeError`, `.etiqueta`,
  `.filas`); `error_xml`, HTTP ≥ 400, `ok=false`, JSON roto → `RuntimeError`;
  transporte → la de httpx. Para R6/R15 todas son «consulta fallida»: capturar
  `Exception`. T8 puede distinguir `SigridRespuestaTruncada` para el WARNING.
- **Candidatos** completos (81 en 0691), ordenados por CIF y deduplicados; `[]`
  solo sin obra (no llama) o si Sigrid no trae nadie. N de R18 = `len(resumenes)`.
- **`fetch_contratos`** pagina (1.000/pág.) y lanza `SigridRespuestaTruncada`
  al pasar de `max_paginas` (20): en T10, rastro `error` (R13, R21).
- **`search_proveedores()`**: lista global completa (3.543), una llamada.
- **Doble**: `DobleSigridApi(error_xml=True)` para R6/R15; `.cliente(**kw)` da
  el cliente real; `.peticiones` / `.peticiones_con(fragmento)`; constantes
  `CIF_SALMEDINA`, `RAZ_SALMEDINA` (`"SALMEDINA, S.L."`), `CONTRATO_SALMEDINA`.
  El resolver acepta el cliente real (`_RepoFake` en `test_f052_resumen_obra.py`).
- **R1 (T7) ya sale verde** con el cliente de T5 (comprobado: B82899550). Su RED
  irá contra el código anterior a T5 o contra la firma nueva `(candidato, motivo, n)`.
- **Nota para T16 (O1 de la review)**: `HeaderGroundingService`
  (`header_grounding_service.py:328-348`) toma los 200 primeros de
  `search_proveedores()`: antes, de una lista cortada a 1.000 en orden no
  garantizado; ahora, los 200 primeros por CIF de 3.543, y una respuesta
  truncada lanza (antes pasaba). Efecto menor e intencionado por R12:
  anotarlo en `azure-apps/albaranes.md`.

## Ficheros tocados (Bloque A)

- Nuevos: `services/albaranes-comun/ruesma_comun/sigrid/{__init__,lectura}.py`,
  `services/albaranes-comun/tests/test_f052_sigrid_lectura.py`,
  `services/albaranes-persistencia/tests/{doble_sigrid_api,test_f052_doble_sigrid_api,
  test_f052_truncado_cliente,test_f052_paginacion_cliente,test_f052_resumen_obra,
  test_f052_equivalencia_familias}.py`.
- Modificado: `services/albaranes-persistencia/infrastructure/sigrid/sigrid_api_contrato_client.py`.
- Sin tocar: resolver, puertos, `composition.py`, sv4, sv2.

## Fuera del alcance / pendiente

- Bloque B (T7–T10), sv4 (T11–T13 bis, T15, T17), T14, T16, T18 y la campaña
  de mutación (T19). MANUAL (humano): T20–T23. `ruesma_comun` sigue en 0.6.0
  (módulo nuevo, sin cambio de API existente; el versionado lo decide el líder).
- La SQL agregada solo se ha probado contra el doble: que sigrid-api real la
  acepta y da 81/163 filas lo verifican T20 y T21.

## Evidencias

| Evidencia | Valor medido |
|---|---|
| Tests F-052 nuevos | 31 (comun) + 11 + 13 + 8 + 12 + 7 (sv3) = **82**, todos en verde |
| Suites a mano, una tras otra (tras CR-A1/CR-A2) | comun `308 passed in 35.24s`; sv3 `284 passed in 4.94s` |
| `bash harness/init.sh` (tras CR-A1/CR-A2) | ENTORNO LISTO, exit 0; raíz `1067 passed in 253.01s`; sv3 `284 passed in 8.19s`; comun `308 passed in 37.93s`; `PUERTA COBERTURA: 100.0% de 91 líneas cambiadas cubiertas (91/91, umbral 80%, nivel critico)`; tamaño `impl 104/220` |
| Mutación | T19, fuera del Bloque A. Manuales: «`nombre` por `texto`» muerto (T6); la review mató M1 y M3 |
