# F-052 · Informe del implementer

Rama `feature/F-052-proveedores-truncados`. Rigor **critico**. Spec v2
aprobada por el humano el 2026-09-30.

## Bloque A (T1–T6)

### T1 · `ruesma_comun.sigrid.lectura` (R8, R9, R14)

Ficheros: `services/albaranes-comun/ruesma_comun/sigrid/{__init__,lectura}.py`,
`services/albaranes-comun/tests/test_f052_sigrid_lectura.py` (29 tests).

RED (test escrito antes que el módulo):

```
$ cd services/albaranes-comun; ../../.venv/Scripts/python.exe -m pytest tests/test_f052_sigrid_lectura.py -q
E   ModuleNotFoundError: No module named 'ruesma_comun.sigrid'
ERROR tests/test_f052_sigrid_lectura.py
1 error in 0.22s
```

GREEN: `29 passed in 0.06s`.

### T2 · Doble de sigrid-api + `transport` inyectable

Ficheros: `services/albaranes-persistencia/tests/doble_sigrid_api.py` (el
doble), `tests/test_f052_doble_sigrid_api.py` (11 tests de humo),
`infrastructure/sigrid/sigrid_api_contrato_client.py` (kwarg `transport`).

Decisiones del doble: `truncated = filas >= max_rows` («se alcanzó
`max_rows`», `sigrid_api.md` §6.1), `max_rows` por defecto 200, `OFFSET` sin
`ORDER BY` → 400 `ok=false`, error de la API → 400 `{ok:false, error}` (§2 de
`sigrid_api.md`). Fixture con semilla `20260930`: obra 0691 (2.083 filas, 81
CIF, 84 contratos, SALMEDINA en las filas 1.500–1.504), obra 0668 (B00001200
con 1.200 líneas desordenadas) y 3.543 proveedores globales. La agregada se
calcula en Python con `strip(" ")` (como `LTRIM/RTRIM`), `DISTINCT` y orden.

RED (el doble ya existía; el cliente no aceptaba el transporte):

```
$ ../../.venv/Scripts/python.exe -m pytest tests/test_f052_doble_sigrid_api.py -q
>       return SigridApiContratoClient(
            base_url=_BASE_URL, function_key="clave-de-test", database="ruesma",
            transport=self.transport, **kwargs,
        )
E       TypeError: SigridApiContratoClient.__init__() got an unexpected keyword argument 'transport'
FAILED tests/test_f052_doble_sigrid_api.py::test_f052_doble_cliente_con_transport_inyectado_habla_con_el_doble
1 failed, 10 passed in 0.62s
```

GREEN: `11 passed in 0.28s`; suite de sv3 completa `244 passed in 2.37s`.
`test_f052_doble_sin_transport_usa_httptransport_con_un_reintento` fija que
sin `transport` el cliente crea un `HTTPTransport(retries=1)` por petición,
como antes (pasaba ya en RED: es el «sin cambio de comportamiento»).

### T3 · `_post_sql_read(politica=..., max_rows=None)` y política por consulta (R7–R10)

`_post_sql_read` = `_enviar_sql_read` (HTTP, JSON, `ok`) + `comprobar_truncado`.
`politica` es keyword-only sin valor por defecto; `max_rows=None` usa el del
cliente. Políticas según design §3: `header_and_lines`, `search_proveedores`,
`fetch_proveedor_by_cif`, `proveedores_obra_*`, `contratos_resumen_obra_*` →
`NO_TOLERA`; `rcg_gra_for_ctr_*`, `gra_rep_for_cod_*` → `TOLERA`. Docstring del
falso «tope de 10.000 filas» corregido. Tests: `tests/test_f052_truncado_cliente.py` (13).

RED (`forzar_truncado` del doble; extracto, una línea por test):

```
$ ../../.venv/Scripts/python.exe -m pytest tests/test_f052_truncado_cliente.py -q
E       KeyError: 'politica'
E       TypeError: SigridApiContratoClient._post_sql_read() got an unexpected keyword argument 'politica'   (x4)
E       Failed: DID NOT RAISE SigridRespuestaTruncada   (x5: las 5 consultas NO_TOLERA con truncated=true)
E       assert False   (sin WARNING en rcg_gra_for_ctr_2405748)
E       AssertionError: assert '10.000' not in 'Proveedores...' ... l tope de 10.000 filas del
12 failed, 1 passed in 0.58s
```

GREEN: `13 passed`; sv3 completa `258 passed` (fallan solo los 7 tests de T4,
escritos ya y sin commitear).

### T4 · `_post_sql_read_paginado`, `header_and_lines` y `search_proveedores` paginadas (R11–R13)

`_post_sql_read_paginado` = `con_paginacion` + `leer_paginado`; cada página va
con `max_rows = pagina + 1`. `header_and_lines`: `ORDER BY con_ctr.cod,
ctr.ide, ctrpro.pos, ctrpro.ide`, `pagina_lineas` (1.000) por página.
`search_proveedores`: `ORDER BY prv.cif, prv.raz`; su kwarg `max_rows`
(5.000) pasa a ser el **tamaño de página** (decisión: se conserva el nombre
para no tocar el puerto ni a los llamantes, que no lo pasan; documentado en
el docstring). Kwargs nuevos de `__init__`: `pagina_lineas=1000`,
`max_paginas=20` (D3; `composition.py` no cambia). Tests:
`tests/test_f052_paginacion_cliente.py` (8).

RED — tests escritos **antes de T3**, contra el código original; aquí se ve el
hallazgo del `max_rows` ignorado y la pérdida silenciosa de líneas:

```
$ ../../.venv/Scripts/python.exe -m pytest tests/test_f052_paginacion_cliente.py -q
>       assert [len(c.lines) for c in contratos] == [500, 700]
E       assert [500, 500] == [500, 700]            (200 líneas perdidas sin aviso)
E       TypeError: SigridApiContratoClient.__init__() got an unexpected keyword argument 'pagina_lineas'
E       AssertionError: assert 1000 == 3543        (search_proveedores cortada a 1.000)
>       assert peticion["max_rows"] > 5000
E       assert 1000 > 5000                         (search_proveedores(max_rows=5000) envía 1.000)
E       TypeError: SigridApiContratoClient.__init__() got an unexpected keyword argument 'max_paginas'
7 failed, 1 passed in 0.49s
```

GREEN: `8 passed`; sv3 completa `265 passed in 2.21s`.

### T5 · `fetch_contratos_resumen_por_obra` con la consulta agregada (R2, R3, R5)

`_SQL_RESUMEN_OBRA_AGREGADO` = la SQL de design §4 literal (con los dos
`ORDER BY` internos). Una llamada, `NO_TOLERA`, sin paginar, `max_rows` del
cliente (1.000 ≥ 163). Python: filas ordenadas por `(cif, nombre)` y dedupe
por CIF quedándose la primera (= la primera de la SQL, `ORDER BY p.cif,
p.raz`); `codigos_contratos` = `split('|')` recortado y sin vacíos; `texto`
tal cual (`None` → `""`). **Decisión**: ordenar en Python hace la salida
independiente del orden de llegada (R5) y, con la SQL real, no cambia nada
(ya llega en ese orden). Puerto y resolver sin cambios. Tests:
`tests/test_f052_resumen_obra.py` (13).

RED (contra T4: la consulta por líneas ya no truncaba en silencio, lanzaba):

```
$ ../../.venv/Scripts/python.exe -m pytest tests/test_f052_resumen_obra.py tests/test_f052_equivalencia_familias.py -q
E  ruesma_comun.sigrid.lectura.SigridRespuestaTruncada: sigrid-api devolvió una respuesta truncada [contratos_resumen_obra_0691]: 1000 filas recibidas (se alcanzó max_rows)
E  AssertionError: assert [('B2', 'ZETA...C9/01',), '')] == [('B1', 'SIN ...ON HA-25 P1')]
E    At index 0 diff: ('B2', 'ZETA, S.L.', ('C2/01', 'C1/01'), 'HORMIGON HA-25 BOMBEO GASOLEO A P1') != ('B1', 'SIN TEXTO, S.A.', ('C9/01',), '')
E  assert 0 == 81        (r2: el paso obra + familia no puntúa a nadie)
ERROR application.services.header_resolver_service:header_resolver_service.py:556 [header-resolver] fetch_contratos_resumen_por_obra fallo obra=0691.
FAILED ...test_f052_r3_una_sola_peticion_con_la_consulta_agregada
FAILED ...test_f052_r3_un_resumen_por_cif_codigos_y_texto
FAILED ...test_f052_r2_el_resumen_trae_los_81_con_salmedina_y_su_texto
FAILED ...test_f052_r2_paso_obra_familia_puntua_los_81
FAILED ...test_f052_r5_barajado_mismo_resumen_y_mismo_orden[1|2|3]
FAILED ...test_f052_r4_mismas_familias_por_cif_en_todo_el_fixture[0691|0668]
9 failed, 10 passed in 0.75s
```

GREEN: `19 passed in 0.40s`; sv3 completa `284 passed in 2.36s`.

### T6 · Equivalencia de familias (R4)

`tests/test_f052_equivalencia_familias.py` (7): por cada CIF de las obras 0691
y 0668 del fixture, `familias_de_texto(texto.lower())` del texto agregado que
devuelve el cliente == el del texto por líneas (reconstruido en el test como
el código anterior: campos no vacíos con `strip`, línea a línea); más un test
de que el fixture no es trivial (≥ 60 CIF con familia, ≥ 5 familias) y cuatro
casos dirigidos (duplicados, orden directo/invertido, espacios y vacíos).

RED: escrito antes de T5 y lanzado contra T4 en la misma ejecución que los de
T5 (traza de arriba: `test_f052_r4_mismas_familias_por_cif_en_todo_el_fixture[0691|0668]`
FAILED con `SigridRespuestaTruncada ... [contratos_resumen_obra_0691]: 1000
filas recibidas`). GREEN tras T5: `7 passed in 0.33s`.

Mutante «leer `nombre` en vez de `texto`» (aplicado a mano en el cliente y
revertido con `git checkout`): **muerto**.

```
$ sed -i 's/texto=str(fila.get("texto") or ""),/texto=str(fila.get("nombre") or ""),/' infrastructure/sigrid/sigrid_api_contrato_client.py
$ ../../.venv/Scripts/python.exe -m pytest tests/test_f052_equivalencia_familias.py -q
E       AssertionError: assert {'B10000000':..., set()), ...} == {}
E         Left contains 80 more items:
E         {'B10000000': ({'acero'}, set()), 'B10007919': ({'acero'}, set()), ...
E       AssertionError: assert {'B00001200':...gon'}, set())} == {}
```

### Lo que el Bloque B (T7–T10) tiene que saber de la API nueva

- **Excepciones de `fetch_contratos_resumen_por_obra`**: truncado →
  `ruesma_comun.sigrid.SigridRespuestaTruncada` (`RuntimeError`, con
  `.etiqueta` y `.filas`); `error_xml`, HTTP ≥ 400, `ok=false`, JSON roto →
  `RuntimeError`; transporte → la de httpx. Para R6/R15 todas son
  «consulta fallida»: capturar `Exception`, no solo la de truncado. T8 puede
  distinguir `SigridRespuestaTruncada` para el WARNING con la obra.
- **Candidatos**: la lista ya viene completa (81 en 0691), ordenada por CIF y
  deduplicada; `[]` solo si no hay obra (sin llamar) o si Sigrid no trae
  nadie. N de R18 = `len(resumenes)`. Puerto sin cambios.
- **`fetch_contratos`** pagina (1.000/pág.) y lanza `SigridRespuestaTruncada`
  si pasa de `max_paginas` (20): en T10 esa excepción es rastro `error` (R13, R21).
- **`search_proveedores()`** devuelve la lista global completa (3.543) en una
  llamada; su `max_rows` es ahora el tamaño de página.
- **Doble** (`tests/doble_sigrid_api.py`): `DobleSigridApi(error_xml=True)` para
  R6/R15; `.cliente(**kwargs)` da el cliente real de sv3; `.peticiones` y
  `.peticiones_con(fragmento)` para contar llamadas; constantes
  `CIF_SALMEDINA`, `RAZ_SALMEDINA` (`"SALMEDINA, S.L."`), `CONTRATO_SALMEDINA`.
  El resolver acepta el cliente real (ver `_RepoFake` en `test_f052_resumen_obra.py`).
- R1 (T7) ya sale verde con el cliente de T5: `_mejor_candidato_por_nombre`
  con `"SALMEDINA"` y obra 0691 encuentra B82899550. Su RED tendrá que ser la
  del código anterior a T5 (o la de la firma nueva `(candidato, motivo, n)`).

## Ficheros tocados (Bloque A)

- Nuevos: `services/albaranes-comun/ruesma_comun/sigrid/{__init__,lectura}.py`,
  `services/albaranes-comun/tests/test_f052_sigrid_lectura.py`,
  `services/albaranes-persistencia/tests/{doble_sigrid_api,test_f052_doble_sigrid_api,
  test_f052_truncado_cliente,test_f052_paginacion_cliente,test_f052_resumen_obra,
  test_f052_equivalencia_familias}.py`.
- Modificado: `services/albaranes-persistencia/infrastructure/sigrid/sigrid_api_contrato_client.py`.
- Sin tocar (fuera del Bloque A): resolver, puertos, `composition.py`, sv4, sv2.

## Fuera del alcance / pendiente

- Bloque B (T7–T10), sv4 (T11–T13 bis, T15, T17), T14, T16, T18 y la campaña
  de mutación (T19). MANUAL (humano): T20–T23. `ruesma_comun` sigue en 0.6.0
  (módulo nuevo sin cambio de API existente; el versionado lo decide el líder).
- La SQL agregada solo se ha probado contra el doble: que sigrid-api real la
  acepta y da 81/163 filas lo verifican T20 y T21.

## Evidencias

`bash harness/init.sh` (tal cual, tras el último commit de código): **ENTORNO LISTO**, exit 0.

| Evidencia | Valor medido |
|---|---|
| Tests F-052 nuevos | 29 (comun) + 11 + 13 + 8 + 13 + 7 = **81**, todos en verde |
| Suites | raíz `1067 passed in 197.52s`; sv3 `284 passed in 4.97s`; comun `306 passed in 29.30s` (sv1, sv2, sv4–sv6: caché; comun y sv3 también a mano, una tras otra: 306 y 284 passed) |
| Cobertura líneas cambiadas | `PUERTA COBERTURA: 100.0% de 95 líneas cambiadas cubiertas (95/95, umbral 80%, nivel critico)` |
| Mutación | no lanzada: es T19, fuera del Bloque A. Mutante manual de T6 («`nombre` por `texto`»): muerto |
| Tamaño | `impl 209/220` en la puerta de `init.sh` (antes de esta tabla) |
