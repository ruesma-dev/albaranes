<!-- progress/impl_F-104.md -->
# F-104 · Informe del implementer (T1–T7, 2026-10-24; T8–T9, 2026-10-27/28)

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

## MANUAL (líder, solo lectura)

- **M1** (24-10, repetida el 28-10): `ca-sv9-alta-sigrid` sin `ALTA_SIGRID_AVISOS_BLOQUEANTES` (manda el defecto). Verde.
- **M-D** (humano, 24-10): sv9 `r20261024-1838`, sv4 `r20261024-1841`; el 28-10 sv9 sigue en `r20261024-1838`.
- **M2** (28-10, SQL de design §6 con `:desde` = `2026-10-24T18:21:18Z`, PostgreSQL de Azure en solo lectura):
  `registrado` 17 altas y `ya_en_sigrid` 1; en ambas `retirado` 0, `errores_v83` 0, `con_retencion` 0, `sin_dato` 0,
  `aviso_v83_bloqueo` 0. **Verde.** `con_retencion` = 0: aún no ha pasado un albarán con retención (no es rojo, §6);
  el panel **M3** se repite cuando pase. La T8 se escribió el 27-10, antes de anotar este recuento.

## T8 · retirada de `proveedor_sin_albaran_previo` (2026-10-27, R10, D1)

Con la F-015 de sigrid-api desplegada (`60db955`). Antes, `git merge dev`: avance rápido
(`dev` ya contenía la rama), sin conflictos.

- `domain/services/clasificador.py`: fuera la línea del Código retirado y su comentario (−2 líneas). Si llegase, va
  a `error` por H25. sv4 **sin cambios**: `TEXTOS_MOTIVO_ALTA` conserva su texto (altas antiguas).
- `tests/test_f104_contrato_v83.py`: R2 pasa a R10 (`test_f104_r10_el_retirado_ya_no_esta_en_la_tabla`,
  `…_se_clasifica_error[previa/grabación]`, `…_previa_rechazada_por_el_retirado_es_error[simulación/real]`);
  `TABLA_CABECERA_V82` sin el retirado y el test de R3 renombrado a `…_v82_sin_el_retirado_mas_los_tres_errores`.
- `tests/test_f053_clasificador.py`: `TABLA_CABECERA` sin el retirado (docstring y comentario).
- `tests/test_f053_servicio_previa.py`: el caso parametrizado de R18 usa `proveedor_no_encontrado` → `no_admitido`.
- `sv9.md` y §10 de `azure-apps/albaranes.md` dicen «retirado»; la viñeta de §10 ya no pone «sin desplegar»
  (sv9 y sv4 desplegados el 2026-10-24). `azure-apps` `ac1f414`, local, sin push.

**RED** (con la línea aún en `CODIGOS_CABECERA`), desde `services/albaranes-alta-sigrid`:
`python -m pytest -q --tb=line -k "f104_r10 or f104_r3_la_tabla or f053_r18_la_tabla"` (PYTHONPATH = `ruesma_comun`)
```
tests	est_f053_clasificador.py:70: AssertionError: assert {'obra_no_enc...mitido'>, ...} == {'obra_no_enc...mitido'>, ...}
tests	est_f104_contrato_v83.py:184: AssertionError: assert 'proveedor_sin_albaran_previo' not in mappingproxy({...})
tests	est_f104_contrato_v83.py:190: AssertionError: assert <EstadoAlta.NO_ADMITIDO: 'no_admitido'> is <EstadoAlta.ERROR: 'error'>
tests	est_f104_contrato_v83.py:198: AssertionError: assert <EstadoAlta.NO_ADMITIDO: 'no_admitido'> is <EstadoAlta.ERROR: 'error'>
tests	est_f104_contrato_v83.py:206: AssertionError: assert {'obra_no_enc...mitido'>, ...} == {'obra_no_enc...mitido'>, ...}
      Left contains 1 more item: {'proveedor_sin_albaran_previo': <EstadoAlta.NO_ADMITIDO: 'no_admitido'>}
7 failed, 1020 deselected in 15.48s
```
La verificación de la T8 en RED: `-k "f104 or f053_clasificador or f053_r18"` → `7 failed, 145 passed`.

**GREEN** (verificación de la T8, sin suite completa: F-100 tiene su campaña de mutación en marcha):

- `pytest services/albaranes-alta-sigrid -k "f104 or f053_clasificador or f053_r18"` → **152 passed**, 875
  deselected, 12,61 s.
- `pytest services/albaranes-front -k "f104 or f077_r27"` → **28 passed**, 1905 deselected, 36,09 s (con el
  `.venv` de sv4; R10 de sv4 y F-077 R27 en verde: un código de sv4 con texto y sin clasificador no rompe R27).

El RED equivale al mutante a mano M18 «volver a poner la línea» (muerto por 7 tests).

**Mutación de la T8** (2026-10-28, `clasificador.py` entero, en serie; el diff de la T8 ahí es solo un borrado):
`python -m harness.mutacion --feature F-104 --ficheros services/albaranes-alta-sigrid/domain/services/clasificador.py
--max-mutantes 0 --workers 1 --salida <scratchpad>` sobre `4a81091` → **13 generados, 13 muertos, 0 supervivientes**,
218,7 s (base sv9 70,9 s). Detalle en `progress/mutacion_F-104.md` § T8. T8 `[x]`.

## T9 · `bash harness/init.sh` (2026-10-28)

Antes, `git merge dev` (`7af0762`: F-069 `done`, F-107 en el backlog): merge sin conflictos; F-104 sigue `blocked`
con su `branch`; `BACKLOG.md` sin cambios tras `init.sh`. `bash harness/init.sh` **tal cual** en el worktree, sin
`PYTHONPATH` ni `ARNES_SIN_CACHE` (no hizo falta la variante de entorno): **verde, exit 0**, «ENTORNO LISTO».
Raíz 1919 passed (625,9 s, con cobertura); sv1 205; sv2 485; sv3 1576; sv4 1933 (399,6 s); sv5 125; sv6 480 (+1
skipped); sv9 **1027 passed** (83,0 s); comun 1077 (+3 skipped). `PUERTA COBERTURA: N/A (F-104 no cambia líneas
Python de producción frente a dev)`: la T8 solo borra líneas. `PUERTA TAMAÑO`: impl 192/220. T9 `[x]`.

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
| `init.sh` final (T7) | **verde, exit 0** (raíz 1883 passed con cobertura; 0 comprobaciones fallidas; tamaño impl 150/220) |
| Mutación T8 (`clasificador.py` entero) | 13 generados, 13 muertos, **0 supervivientes**, 218,7 s |
| `init.sh` T9 (tal cual, tras merge de `dev`) | **verde, exit 0**; sv9 1027 passed (83,0 s), sv4 1933 passed (399,6 s), raíz 1919 passed (625,9 s); cobertura N/A (solo borrados) |
