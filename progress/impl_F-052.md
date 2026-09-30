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
