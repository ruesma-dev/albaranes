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
