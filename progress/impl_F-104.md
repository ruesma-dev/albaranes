<!-- progress/impl_F-104.md -->
# F-104 · Informe del implementer (pasada 1: T1–T7)

Rama `feature/F-104-codigos-contrato-v83` (worktree `../albaranes-F-104`), `dev` (`ba516a7`) fusionado al empezar.
Rigor `critico`. PARADA 1 cerrada por el humano el 2026-10-24: **D1 = 1, D2 = 1** (anotado en `design.md` §8).
Alcance de esta pasada: **T1–T7**. M1, M-D, M2 y T8–T9 quedan para después del despliegue de la F-015 de sigrid-api.

## Qué cambió

| Fichero | Cambio |
|---|---|
| `services/albaranes-alta-sigrid/domain/services/clasificador.py` | +3 entradas `no_admitido` en `CODIGOS_CABECERA` (`proveedor_no_encontrado`, `proveedor_ambiguo`, `retencion_no_soportada`); `proveedor_sin_albaran_previo` intacto con su comentario «retirado en la v8.3»; docstring v8.3 `871cc0c` |
| `services/albaranes-alta-sigrid/tests/test_f053_clasificador.py` | `TABLA_CABECERA` + los tres; docstring v8.3 (único test previo que cambia, design §3.1) |
| `services/albaranes-alta-sigrid/tests/test_f104_contrato_v83.py` | NUEVO: R1–R6 (50 tests) |
| `services/albaranes-alta-sigrid/sv9.md` | cabecera v8.3 `871cc0c`; sección «Códigos del contrato v8.3 (F-104)» |
| `services/albaranes-front/domain/models/alta_sigrid_models.py` | +5 textos en `TEXTOS_MOTIVO_ALTA` (literal de design §3.2); `computed_field` `AltaSigridVista.avisos_sigrid` |
| `services/albaranes-front/templates/_alta_sigrid.html` | «Avisos de Sigrid» itera `avisos_sigrid`: con texto, `<li title="codigo">texto · mensaje (línea N)</li>`; sin texto, la línea de antes |
| `services/albaranes-front/tests/test_f104_textos_avisos.py` | NUEVO: R7–R10 (25 tests) |
| `azure-apps/albaranes.md` §10 | viñeta «Códigos del contrato v8.3 (F-104)»; commit local `8f6f243` en `azure-apps` (master), sin push |
| `specs/F-104-…/design.md` §8, `tasks.md`, `harness/features.json`, `BACKLOG.md`, `progress/current.md` | D1/D2 decididas; F-104 `in_progress`; T1–T7 `[x]` |

Commits: `44c0556` (PARADA 1 + `in_progress`), `f04c04c` T1, `74a8669` T2, `3e5fcc8` T3, `e00cd3e` T4, `a77c123` T5,
`d3c20f1` (rama declarada en `features.json`, ver abajo), `22413cf` T6, T7 en el commit de este informe.

## Decisiones de diseño (sin desviaciones de la spec)

- **`branch` de F-104 en `harness/features.json`**: faltaba; sin él la mutación tomaba el merge de `chore/F-104-alta`
  como alcance (vacío, salió con código 3) y las puertas de cobertura/tamaño de `init.sh` daban N/A. Añadido (`d3c20f1`).

- **R5 con la configuración real por defecto**: los tests de R5 construyen el servicio con
  `Settings(...).avisos_bloqueantes` (no con un `frozenset` a mano), para atar R4 y R5: si alguien añade un Aviso
  v8.3 al defecto, caen los dos. Un test de contraste (`test_f104_r5_si_alguien_los_configura_bloquean`) demuestra que
  el «no bloquear» sale de la configuración y no del código.
- **R6** se prueba pasando el 200 por `RespuestaAlta.desde_cuerpo` (el mismo camino que el cliente real) con
  `totales.tot`, `retenciones`, `n_retenciones` y `filas.dcarec`, en `simulado`, `revisar` y `registrado`, y comparando
  estado, motivos, `cod` y `con_ide` con el mismo 200 sin esos campos.
- **R4** lee como texto `infra/*.ps1` (todos los que haya en el árbol, también los `*.local.ps1` no versionados si
  existen) y `.env.example`; el mensaje de fallo nombra solo el fichero, nunca su contenido.
- **`avisos_sigrid`** ignora lo que no sea `dict` (como `avisos_resolucion`). Como `avisos` lo valida pydantic, el caso
  solo es alcanzable sin validar: se prueba con `model_construct`. `mensaje`/`referencia_linea` ausentes = `None`.
- **Orden T1 → T3**: entre T1 y T3 el test F-077 R27 de sv4 estuvo en rojo (lee `clasificador.py` como texto y
  los tres códigos aún no tenían texto). Es la RED de T3; en el commit de T3 vuelve a verde.

## Fase RED (trazas reales)

**T1 · R1** (antes de tocar `clasificador.py`), desde `services/albaranes-alta-sigrid`:
```
$ python -m pytest tests/test_f104_contrato_v83.py -q --tb=line -k "f104_r1 or f104_r2 or f104_r3"
E   AssertionError: assert <EstadoAlta.ERROR: 'error'> is <EstadoAlta.NO_ADMITIDO: 'no_admitido'>
tests\test_f104_contrato_v83.py:144: AssertionError: assert <EstadoAlta.ERROR: 'error'> is <EstadoAlta.NO_ADMITIDO: 'no_admitido'>
tests\test_f104_contrato_v83.py:192: AssertionError: assert {'obra_no_enc...mitido'>, ...} == {'obra_no_enc...mitido'>, ...}
      Right contains 3 more items: {'proveedor_ambiguo': ..., 'proveedor_no_encontrado': ..., 'retencion_no_soportada': ...}
FAILED tests/test_f104_contrato_v83.py::test_f104_r1_errores_v83_en_la_tabla_como_no_admitido[proveedor_no_encontrado]  (KeyError)
19 failed, 16 passed in 1.54s
```
Tras el cambio: `pytest -k "f104_r1 or f104_r2 or f104_r3 or f053_clasificador"` → `120 passed, 882 deselected`.

**T1 · R2 y R3** (guardas que nacen en verde ⇒ RED por mutación inversa: quitar `proveedor_sin_albaran_previo` de
la tabla y `CODIGOS_CABECERA.get(error.codigo, _NO_ADMITIDO)`; restaurado después):
```
$ python -m pytest tests/test_f104_contrato_v83.py -q --tb=line -k "f104_r2 or f104_r3"
tests\test_f104_contrato_v83.py:184: KeyError: 'proveedor_sin_albaran_previo'                      (x2)
tests\test_f104_contrato_v83.py:200: AssertionError: assert <EstadoAlta.NO_ADMITIDO: 'no_admitido'> is <EstadoAlta.ERROR: 'error'>  (x8)
tests\test_f104_contrato_v83.py:192: AssertionError: assert {'obra_no_enc...mitido'>, ...} == ...
11 failed, 3 passed, 21 deselected in 1.35s
```

**T2 · R4–R6** (sin cambios de producción ⇒ RED por mutación inversa, restaurada: defecto
`producto_sin_historico,retencion_del_contrato`; `# p. ej. cabecera_sin_dato` en `.env.example`; el comparador
añade `importe_distinto` si hay `totales.tot`):
```
$ python -m pytest tests/test_f104_contrato_v83.py -q --tb=line -k "f104_r4 or f104_r5 or f104_r6"
test_f104_contrato_v83.py:216: AssertionError: assert frozenset({'p...el_contrato'}) == frozenset({'p...n_historico'})
test_f104_contrato_v83.py:226: AssertionError: .env.example nombra cabecera_sin_dato
test_f104_contrato_v83.py:249: AssertionError: assert <EstadoAlta.REVISAR: 'revisar'> is <EstadoAlta.SIMULADO: 'simulado'>
test_f104_contrato_v83.py:252: AssertionError: assert 'aviso_bloqueante' not in ['importe_distinto', 'aviso_bloqueante']
test_f104_contrato_v83.py:301: AssertionError: assert <EstadoAlta.REVISAR: 'revisar'> is <EstadoAlta.REGISTRADO: 'registrado'>
test_f104_contrato_v83.py:302: AssertionError: assert (<EstadoAlta....], None, None) == (<EstadoAlta....], None, None)
8 failed, 7 passed, 35 deselected in 1.61s
```
y, sola, la mutación «`desde_cuerpo` arrastra `filas` dentro de `totales`»:
```
$ python -m pytest tests/test_f104_contrato_v83.py -q --tb=line -k f104_r6
test_f104_contrato_v83.py:305: assert 'dcarec' not in '{"estado": ...p": 6.0}]}}}'     (x3)
3 failed, 6 passed, 41 deselected in 1.59s
```

**T3 · R7** (antes de los textos), desde `services/albaranes-front`:
```
$ .venv/Scripts/python.exe -m pytest -q --tb=line -k "f104_r7 or f104_r10 or f077_r27"
tests/test_f077_motivos_alta.py:266: AssertionError: assert ['proveedor_a...no_soportada'] == []
tests/test_f104_textos_avisos.py:40: KeyError: 'proveedor_no_encontrado'   (y los otros cuatro códigos)
tests/test_f104_textos_avisos.py:46: KeyError: 'retencion_del_contrato'    (y los otros cuatro)
tests/test_f104_textos_avisos.py:53: AssertionError: assert [{'codigo': '..._encontrado'}] == [{'codigo': '... de la obra'}]
13 failed, 3 passed, 1805 deselected, 1 warning in 7.22s
```
Tras el cambio: `16 passed`. **R10** (guarda) por mutación inversa (quitar el texto del retirado):
```
tests/test_f077_motivos_alta.py:266: AssertionError: assert ['proveedor_s...baran_previo'] == []
tests/test_f104_textos_avisos.py:60: KeyError: 'proveedor_sin_albaran_previo'
2 failed, 2 passed, 1817 deselected, 1 warning in 6.56s
```

**T4 · R8–R9** (antes de `avisos_sigrid` y de la plantilla):
```
$ .venv/Scripts/python.exe -m pytest tests/test_f104_textos_avisos.py -q --tb=line -k "f104_r8 or f104_r9"
E   AttributeError: 'AltaSigridVista' object has no attribute 'avisos_sigrid'          (x3)
tests/test_f104_textos_avisos.py:127: assert ['<li><code>r...ea 900)</li>'] == ['<li title="...ea 900)</li>']
tests/test_f104_textos_avisos.py:177: assert 0 == 1                                    (x2)
6 failed, 6 passed, 13 deselected in 4.44s
```
Tras el cambio: `25 passed`; `-k "f104_r8 or f104_r9 or f077 or f053_t20 or f053_t21 or f069_panel"` → `374 passed`.
Los 6 que pasaban en RED son guardas de «como hoy» (aviso sin texto, escape, R9 en la vista), que ya se cumplían.

## Mutación (T6)

`python -m harness.mutacion --feature F-104 --max-mutantes 0 --workers 1` (en serie: nunca dos suites a la vez) →
alcance 31 líneas en 2 ficheros, **1 mutante generado, 1 muerto, 0 supervivientes**, 566,1 s (línea base sv4 282,4 s).
El mutador no muta entradas de diccionario ni plantillas (30 de las 31 líneas son datos), así que se complementó con
**17 mutantes a mano** sobre `CODIGOS_CABECERA`, `TEXTOS_MOTIVO_ALTA`, `avisos_sigrid` y `_alta_sigrid.html`:
**17 muertos, 0 supervivientes**. Tabla y análisis en `progress/mutacion_F-104.md`.

## `bash harness/init.sh` (T7)

Primera pasada en rojo por **un** test de la raíz (`test_f039_r2_…`: el informe `progress/mutacion_F-104.md` no
tenía fila en `progress/inventario_mutacion_F-039.md`); añadida la fila (55 informes). Pasada final: ver «Evidencias».

## MANUAL pendientes (no son de esta pasada)

- **M1** (líder, solo lectura, antes de desplegar): `ALTA_SIGRID_AVISOS_BLOQUEANTES` de `ca-sv9-alta-sigrid` sin
  Avisos v8.3 (design §6). **M-D** (humano): `Set-DeployTag; .\deploy.ps1 -Only sv9,sv4`, antes o a la vez que la
  F-015 de sigrid-api. **M2/M3** (líder, tras F-015): SQL de design §6 y panel de un alta con `retencion_del_contrato`.
- **T8–T9** (tras M2 en verde): retirar `proveedor_sin_albaran_previo` de sv9 (el texto de sv4 se queda).
- Tras APPROVED de T1–T7, F-104 pasa a `blocked` («espera al despliegue de F-015 de sigrid-api»), D1.

## Fuera de alcance (R11, sin tocar)

Petición a sigrid-api, `comparador_previa.py`, `ruesma_comun`, DDL, `infra/*.ps1`, `.env.example`, `settings.py`,
`totales.tot` en el panel, la rama y la spec de F-103, el repositorio de sigrid-api.

## Evidencias

| Evidencia | Valor real |
|---|---|
| Tests de F-104 | sv9 `test_f104_contrato_v83.py` 50 passed; sv4 `test_f104_textos_avisos.py` 25 passed |
| Suites (`bash harness/init.sh`) | sv9 **1017 passed** (75,7 s); sv4 **1833 passed** (321,2 s); raíz, sv1–sv3, sv5, sv6, comun en verde |
| Cobertura de líneas cambiadas | `PUERTA COBERTURA: 100.0% de 4 líneas cambiadas cubiertas (4/4, umbral 80%, nivel critico)` |
| Mutación (herramienta, sin tope) | 1 generado, 1 muerto, **0 supervivientes**, 566,1 s |
| Mutación a mano (datos y plantilla) | 17 generados, 17 muertos, **0 supervivientes** |
| `init.sh` final | **verde, exit 0** (raíz 1883 passed con cobertura; 0 comprobaciones fallidas; tamaño impl 150/220) |
