<!-- progress/impl_F-036_bloque_B.md -->
# F-036 · Implementación del BLOQUE B (T0 + T8-T13)

Rama `feature/F-036-residuos-contenedores-e-incrementos`. Rigor `critico`:
fase RED obligatoria, traza real pegada. Un commit por tarea, sin push.
El bloque A (T1-T7, sv4) ya estaba implementado y APROBADO; aquí solo se
tocó sv4 para lo que pedía T0.

**Fuera de alcance de este bloque, a propósito:** T14-T20 (bloque D3,
sintéticas de LER en sv6), T21-T22 (aceptación SALMEDINA), T23 (campaña de
mutación), T24 (verificación MANUAL contra BBDD real) y T25 (`init.sh`
completo). No se ejecutó `bash harness/init.sh`: es T25.

## Commits

| Commit | Tarea |
|---|---|
| `717aa93` | T0 · cierre de los cambios pedidos en la review del bloque A |
| `119f170` | T8 · el catálogo LER se muda a `ruesma_comun.ler` (R14) |
| `33d6b33` | T9 · las nueve medidas de residuos puntúan (R9, R10) |
| `18c05a5` | T10 · el ganador se completa con las medidas que le faltan (R11, R12) |
| `e4e3122` | T11 · regla dura LER → residuos en la tipología de sv5 (R13) |
| `0de37ba` | T12 · el volumen manda sobre la resta (R22) |
| `8956c5c` | T13 · el prompt `valuation_residuos` documenta el orden nuevo (R22) |

## Ficheros tocados

**Producción** (el diff exacto, en los commits de la tabla)

- **nuevo** `services/albaranes-comun/ruesma_comun/ler.py` — catálogo LER
  (2014/955/UE), `es_ler_valido`, `normalizar_ler`, `texto_contiene_ler`.
- `services/albaranes-api/domain/models/tipologia.py` — pierde el catálogo,
  queda la reexportación. `tipologia_resolver.py` NO se tocó.
- `.../albaranes-persistencia/application/services/contexto_linea_merger.py`
  — `_CAMPOS_RESIDUOS`, `_tiene_valor`, `_score_contexto` ampliado,
  `_completar_campos_objetivos` nueva, docstring del módulo reescrita.
- `.../albaran-valoracion-api/application/services/valuation_extraction_service.py`
  — `_hay_ler_en_linea` nueva; la regla dura delante de `tipo_familia`.
- `.../albaran-valoracion-persist/application/services/residuos_container_calc.py`
  — prioridades 2 y 3 intercambiadas, docstring y comentarios al orden nuevo.
- `.../albaran-valoracion-api/config/prompts.yaml` — bloque
  `valuation_residuos`, orden de prioridades.
- sv4, solo T0: `templates/document_detail.html` (separador del tooltip) y
  `infrastructure/database/review_repository.py` (docstring de
  `_num_iguales`).

**Tests nuevos** — `test_f036_r14_ler.py` en `comun` (18),
`test_f036_r14_ler_reexportado.py` en sv2 (2),
`test_f036_r9_r12_contexto_merger.py` en sv3 (29),
`test_f036_r13_tipologia_ler.py` (16) y
`test_f036_r22_prompt_residuos_orden.py` (4) en sv5,
`test_f036_r22_contenedores_prioridades.py` en sv6 (14), y +1 en
`test_f036_r23_r24_trazabilidad.py` de sv4 (el separador, T0).

**Papeleo**: `specs/.../requirements.md` (R4) y `specs/.../tasks.md` (T7-bis
y las casillas T8-T13).

## Decisiones de diseño

1. **T8 movió también `normalizar_ler`**, no solo las dos funciones que
   nombra el diseño: comparte `_LER_REGEX` y `es_ler_valido` con ellas, y
   dejarla en sv2 obligaba a duplicar la regex — lo que R14 prohíbe.
2. **El test de identidad de la reexportación vive en sv2**, no en `comun`:
   el paquete `domain` de sv2 solo es importable desde su propio `conftest`.
   En `comun` queda el contrato de comportamiento y un test que lee el fuente
   de sv2 y comprueba que el catálogo ya no está ahí.
3. **`_tiene_valor` trata `False` y `0` como DATO** (solo `None` y las
   cadenas en blanco son hueco). `carga_incompleta=False` significa «la carga
   iba completa»: si contara como hueco, el relleno de R11 lo pisaría con el
   `True` de otro proveedor. Hay test de las dos caras.
4. **`_completar_campos_objetivos` devuelve el propio ganador si no hay nada
   que rellenar**, sin copiar y sin log: el caso mayoritario no paga nada y
   la traza solo aparece cuando de verdad se completó algo.
5. **En T11 el texto que se escanea es `codigo` + `descripcion` +
   `descripcion_extendida`.** sv2 usa `codigo` + `concepto`; en sv5 la
   descripción extendida existe y es donde suele venir el LER de una línea de
   residuos. El validador compartido ya exige catálogo + (grafía con espacios
   o palabra de contexto), así que ampliar el texto no relaja la regla. **Es
   una interpretación de «su texto contiene un LER» del diseño: si el
   reviewer la quiere estricta, se recorta en una línea.**
6. **T12 anida la resta dentro del `if m3 is None or m3 <= 0`** en vez de
   reordenar dos bloques sueltos: así el único camino que llega a
   `residuos_sin_volumen_m3` es «ni volumen ni resta utilizables», que es
   literalmente lo que dice R22.
7. **Los nombres de las `reasons` no cambiaron** (T12), con test que fija
   `residuos_tamano_defecto_6m3`, `residuos_volumen_implausible…` y
   `residuos_sin_volumen_m3`: `valuation_builder.py:1147-1155` los inspecciona
   por prefijo y sv4 los pinta.

## Fase RED · trazas reales

### T0 · el separador del tooltip

`cd services/albaranes-front && python -m pytest tests/test_f036_r23_r24_trazabilidad.py -q --tb=short -k tooltip`

```
F                                                                        [100%]
_______ test_f036_r23_el_tooltip_separa_las_razones_con_salto_de_linea ________
tests\test_f036_r23_r24_trazabilidad.py:258: in test_f036_r23_el_tooltip_...
    assert "residuos_contenedores\nresiduos_sin_volumen_m3" in html
E   assert 'residuos_contenedores\nresiduos_sin_volumen_m3' in '<!-- templates/document_detail.html -->\n...'
1 failed, 29 deselected in 1.21s
```

Verde tras el cambio: `1 passed, 29 deselected in 0.72s`.

### T8 · el catálogo LER en `comun`

`cd services/albaranes-comun && python -m pytest tests/test_f036_r14_ler.py -q --tb=short`

```
tests\test_f036_r14_ler.py:17: in <module>
    from ruesma_comun.ler import (
E   ModuleNotFoundError: No module named 'ruesma_comun.ler'
ERROR tests/test_f036_r14_ler.py
!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
1 error in 0.22s
```

`cd services/albaranes-api && python -m pytest tests/test_f036_r14_ler_reexportado.py -q --tb=short`

```
F.                                                                       [100%]
__________ test_f036_r14_sv2_reexporta_la_misma_funcion_no_una_copia __________
tests\test_f036_r14_ler_reexportado.py:25: in test_f036_r14_sv2_reexporta_la_misma_funcion_no_una_copia
    from ruesma_comun import ler as ler_comun
E   ImportError: cannot import name 'ler' from 'ruesma_comun'
1 failed, 1 passed in 0.16s
```

### T9 · las nueve medidas puntúan

Primera ejecución del fichero, antes de existir `_CAMPOS_RESIDUOS`:

```
tests\test_f036_r9_r12_contexto_merger.py:19: in <module>
    from application.services.contexto_linea_merger import (
E   ImportError: cannot import name '_CAMPOS_RESIDUOS' from
    'application.services.contexto_linea_merger'
1 error in 0.91s
```

### T10 · el relleno de las medidas

Con T9 ya en verde, `python -m pytest tests/test_f036_r9_r12_contexto_merger.py -q --tb=short -k "r11 or r12"`:

```
................F..FF.F......                                            [100%]
tests\test_f036_r9_r12_contexto_merger.py:156: in test_f036_r11_el_ganador_pobre_conserva_los_m3_del_rico
    assert elegido.codigo_ler == "170504"
E   AssertionError: assert None == '170504'
tests\test_f036_r9_r12_contexto_merger.py:205: in test_f036_r11_manda_el_candidato_de_mayor_score
    assert elegido.volumen_m3 == 6.0
E   AssertionError: assert None == 6.0
tests\test_f036_r9_r12_contexto_merger.py:215: in test_f036_r11_completar_no_muta_al_ganador
    assert elegido is not ganador
E   AssertionError: assert ContextoLinea(...) is not ContextoLinea(...)
tests\test_f036_r9_r12_contexto_merger.py:244: in test_f036_r11_queda_en_el_log_que_se_completo_y_desde_quien
    assert "codigo_ler" in traza
E   AssertionError: assert 'codigo_ler' in ''
4 failed, 25 passed in 0.48s
```

### T11 · la regla dura de LER en sv5

`cd services/albaran-valoracion-api && python -m pytest tests/test_f036_r13_tipologia_ler.py -q --tb=line`

```
E   AssertionError: assert 'hormigon' == 'residuos'   (el_ler_gana_a_la_familia_hormigon)
E   AssertionError: assert 'generico' == 'residuos'   (el_ler_tambien_se_busca_en_el_texto)
E   AssertionError: assert 'generico' == 'residuos'   (el_ler_en_la_descripcion_extendida)
FAILED ::test_f036_r13_un_codigo_ler_en_el_contexto_basta
FAILED ::test_f036_r13_basta_con_que_UNA_linea_traiga_ler
FAILED ::test_f036_r13_el_ler_gana_a_la_familia_hormigon
FAILED ::test_f036_r13_el_ler_tambien_se_busca_en_el_texto_de_la_linea
FAILED ::test_f036_r13_el_ler_en_la_descripcion_extendida_tambien_cuenta
5 failed, 11 passed in 0.75s
```

### T12 · el volumen manda sobre la resta

`cd services/albaran-valoracion-persist && python -m pytest tests/test_f036_r22_contenedores_prioridades.py -q --tb=short`

```
.FF..........F                                                           [100%]
____________ test_f036_r22_prioridad_2_el_volumen_gana_a_la_resta _____________
E   AssertionError: assert 1 == 2
E    +  where 1 = ResultadoContenedores(num_contenedores=1, volumen_m3=12.0,
        contenedor_m3=None, reasons=['residuos_contenedores_resta=1 (llevadas 2 - retiradas 1)']).num_contenedores
___________ test_f036_r22_el_volumen_gana_aunque_la_resta_diera_mas ___________
E   AssertionError: assert 8 == 1
_______ test_f036_r22_la_docstring_del_modulo_documenta_el_orden_nuevo ________
E   AssertionError: la docstring sigue poniendo la resta antes que el volumen
E   assert 674 < 517
3 failed, 11 passed in 0.15s
```

### T13 · el orden en el prompt

`cd services/albaran-valoracion-api && python -m pytest tests/test_f036_r22_prompt_residuos_orden.py -q --tb=short`

```
.FF.                                                                     [100%]
_________ test_f036_r22_el_prompt_pone_el_volumen_antes_que_la_resta __________
E   AssertionError: el prompt no describe el orden de R22: explicitos -> volumen -> resta
E   assert 866 < 822
_________ test_f036_r22_el_prompt_numera_el_volumen_como_prioridad_2 __________
E   assert '2) ceil(volumen_m3' in 'eres un experto valorador de obra...'
2 failed, 2 passed in 0.24s
```

## Verificación · resultado literal

Suites completas, cada una con `cd` a su ruta y el intérprete que resuelve
`python -m harness.servicios --shell` (los siete servicios comparten `.venv`
de la raíz). Ninguna en paralelo.

| Servicio | Resultado |
|---|---|
| `comun` | `64 passed, 3 skipped in 109.23s` |
| sv2-api | `58 passed in 1.12s` |
| sv3-persistencia | `117 passed in 1.95s` |
| sv4-front | `131 passed in 2.59s` |
| sv5-valoracion-api | `31 passed in 1.26s` |
| sv6-valoracion-persist | `125 passed in 1.59s` |

`python -m harness.tamano --feature F-036`:

```
PUERTA TAMAÑO: F-036 dentro de los topes
(requirements 149/150, design 228/250, impl 220/220)
```

`python -m harness.rutas_sensibles --puerta --base dev`:

```
PUERTA RUTAS SENSIBLES [evals]: aviso: falta la evidencia de 3 ruta(s)
sensible(s) tocada(s):
  - services/albaran-valoracion-api/config/prompts.yaml
  - services/albaran-valoracion-persist/application/services/residuos_container_calc.py
  - services/albaranes-api/domain/models/tipologia.py
  Sin cumplir: no existe progress/evals_F-036.md
  Lánzalo con: python -m evals.runner --con-llm --feature F-036
```

**No bloquea** (exigencia `aviso` en `harness/rutas_sensibles.json`) y **no se
lanzó**: `--con-llm` gasta LLM real y esa decisión es del humano. El bloque D3
volverá a tocar `prompts.yaml` (T20) y `valuation_builder.py`, así que la
pasada tiene sentido UNA vez, al final. **Queda anotado para T25.**

`bash harness/init.sh` NO se ejecutó: es T25, del bloque D.

## Evidencias

| Evidencia | Valor |
|---|---|
| Tests ejecutados (6 suites) | **526 passed, 3 skipped, 0 failed** |
| Tests NUEVOS de este bloque | **84** (18 comun + 2 sv2 + 29 sv3 + 20 sv5 + 14 sv6 + 1 sv4) |
| Cobertura de las líneas cambiadas | **97,0 %** (196/202, umbral 80 %) |
| Mutantes generados / supervivientes | **no medido en este bloque** — la campaña es T23 |
| Tiempo de ejecución de las suites | 109,23 s (`comun`) + 8,51 s (los otros cinco) |

`python -m harness.cobertura --base dev`, con el `coverage.json` de cada
servicio regenerado antes (`coverage run -m pytest` + `coverage json`):

```
PUERTA COBERTURA: 97.0% de 202 líneas cambiadas cubiertas
(196/202, umbral 80%, nivel critico)
```

Mide el diff completo de la rama contra `dev`, o sea bloque A + bloque B.

**Mutación (T23).** No se lanzó aquí: `python -m harness.mutacion --feature
F-036` mide el diff COMPLETO de la rama, así que correrla ahora daría un
informe que el bloque C invalidaría a la primera línea. Con rigor `critico`
el umbral es CERO supervivientes y cada uno exige test o justificación
escrita; eso se hace una vez, con la feature entera, en T23. **No es una
sección `PENDIENTE` disfrazada: es la tarea T23 y está sin marcar.**

## Hallazgos y dudas para el líder

1. **`texto_contiene_ler` busca `"ler"` como SUBCADENA.** Palabras corrientes
   la contienen —`TORNILLERIA`, `ALQUILER`, `TALLER`— y dan «contexto de
   residuos» a cualquier número de 6 dígitos que sea capítulo/subcapítulo
   válido. Lo descubrí porque mi primer test de T11 usaba `"TORNILLERIA"` y
   clasificaba `residuos`. Es comportamiento **heredado de sv2 desde jul
   2026**, no algo que F-036 introduzca, pero T11 lo extiende a sv5. **No lo
   toqué**: cambiarlo altera el enrutado de la fase 2 de sv2, es ruta
   sensible y necesita decisión del humano + evals. Queda un comentario en el
   test que lo documenta. **Propongo ficha aparte** (exigir `\bler\b` o
   palabra completa).
2. **`harness/features.json` declara para F-036 los servicios sv3, sv4, sv5 y
   sv6, pero T8 toca sv2 y `comun`.** R14 lo manda explícitamente, así que no
   es una salida de alcance, sino metadato desactualizado. **No toqué
   `features.json`** (instrucción del líder): lo decide él.
3. **Coste operativo de T8 confirmado**: `ruesma_comun` va horneado en cada
   imagen, así que al desplegar hay que reconstruir sv2, sv3, sv5 y sv6.
   Aceptado por el humano (decisión R14). No queda copia del catálogo en sv2:
   hay un test que lee el fuente y lo comprueba.
4. **`ruff` sigue avisando de deuda previa** en los ficheros tocados (`UP006`,
   `UP037`, `UP045`, `ISC004`, `RUF046`) y del `I001` de import-sorting que
   afecta a TODOS los tests de servicio del repo (los preexistentes también).
   No se arregló: es deuda ajena a esta feature y la puerta de lint no
   bloquea. Lo mío queda sin avisos NUEVOS salvo ese `I001` compartido, que
   he mantenido igual que los ficheros vecinos a propósito.
5. **`coverage.json` de los seis servicios quedó regenerado.** Están en
   `.gitignore` (`services/*/coverage.json`): no entran en ningún commit.
