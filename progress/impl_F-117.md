<!-- progress/impl_F-117.md -->
# F-117 · Informe del implementer (T1–T7)

Rama `feature/F-117-partida-equivalente-en-obra`, worktree `../albaranes-F-117`, rigor **critico**. PARADA 1
cerrada el 2026-11-09 (D1–D9 = a): R4, R5, R25 (sufijo) y R15 (revisión no bloqueante) dentro. T8 (despliegue,
humano) y T9 (medición, líder) no son mías. Nada contra Azure, BBDD real, Sigrid ni LLM. Sin push.

## 0. Estado y bloqueo de la puerta de cobertura

**T1–T7 hechas; F-117 marcada `blocked` en `harness/features.json`** por lo que sigue.

**`bash harness/init.sh` NO sale en verde, y no por el código de F-117**: todas las suites pasan y solo cae la
PUERTA COBERTURA, porque el diff de la rama contra `dev` incluye los scripts de medición del spec-author
(`scripts/medicion_F-117/{comun_ro,m1_fuera_de_lista,m2_estrategias}.py`, 206 líneas ejecutables, sin tests y
que solo corren contra Azure/PG/Sigrid). Ya estaba en rojo ANTES de T1 (init de partida: `0.0% de 206 líneas`).
La puerta no tiene exclusiones (`harness/cobertura.py`, `alcance.es_produccion` cuenta `scripts/`).

Medida aparte, la cobertura de lo que escribe F-117 (base `9c4bf43`) es **100 %** (§5). No he improvisado
nada (ni tests de los scripts ni sacarlos de la rama): lo decide el líder. Opciones que veo:
(a) sacar `scripts/medicion_F-117/` de la rama y versionarlos al cerrar, como hizo F-111 (`7493a10`);
(b) tests unitarios de las partes puras de los scripts (alcance nuevo);
(c) aceptar la excepción en la review con la medida del §5.

## 1. Ficheros tocados

| Fichero | Cambio |
|---|---|
| `services/albaranes-comun/ruesma_comun/sigrid/partidas.py` | `equivalentes_partida`, `_equivalente`, `_sin_letra`, `RE_SEGMENTO_CON_LETRA`, `MIN_SEGMENTOS_SUFIJO`; docstring del módulo con la excepción a H1 (R11) |
| `services/albaranes-comun/ruesma_comun/sigrid/__init__.py` | exporta `equivalentes_partida` (R12) |
| `services/albaranes-comun/pyproject.toml`, `ruesma_comun/__init__.py` | 0.13.0 ⇒ **0.14.0** (R12) |
| `services/albaranes-comun/tests/test_f117_equivalentes_partida.py` | nuevo, 70 tests (R1–R12, R18) |
| `services/albaranes-comun/tests/test_f111_candidatas_residuos.py` | solo `test_f111_t5_version_0130`: «== 0.13.0» ⇒ «>= 0.13.0» (§3, D-1) |
| `services/albaran-valoracion-persist/application/services/normalizador_partidas.py` | `equivalente=`, `NormalizacionSobre.equivalencias`, prefijos, `_lista_ambigua`, log, `anotar` (R13–R23) |
| `services/albaran-valoracion-persist/config/settings.py` | `PARTIDA_EQUIVALENTE_ENABLED` (defecto `true`) |
| `services/albaran-valoracion-persist/interface_adapters/composition.py` | `equivalente=settings.partida_equivalente_enabled` |
| `services/albaran-valoracion-persist/tests/test_f117_partida_equivalente.py` | nuevo, 33 tests (R13–R23) |
| `services/albaran-valoracion-persist/tests/test_f117_pipeline.py` | nuevo, 5 tests (R24–R26) |
| `docs/ARCHITECTURE.md` | regla 23: «nunca por sufijo» salvo F-117, reglas y motivos (R27) |
| `services/albaran-valoracion-persist/sv6.md` | fila de `PARTIDA_EQUIVALENTE_ENABLED` en la tabla de variables (§3, D-2) |
| `azure-apps/albaranes.md` | §11.2 nuevo (variable y efecto), commit `a3cd897` en `azure-apps`, sin push |
| `specs/.../tasks.md`, `progress/mutacion_F-117.md` | T1–T7 `[x]`; informe de mutación |

Commits (uno por tarea): `f175e82` T1, `ad6e0b9` T2, `ae91419` T3, `2aa328a` T4, `99894ba` T5, `2e51c3d` T6,
`09d2800` y `2ce59db` T7. No tocados (design §7): `run_valuation_pipeline.py`, matcher, builder, residuos,
almacén, sv4, sv5, sv9, `casar_partida`, `resolver_partida_obra`, `normalizar_partida`, `misma_partida`,
`mostrar_partida`. Tests de F-049/F-076/F-098 sin tocar y en verde.

## 2. Decisiones de diseño

- **`equivalentes_partida`** (comun): `resolver_partida_obra(...) != fuera_de_lista` ⇒ `()`; `"/"` en la lectura o
  `_choca_con_no_hoja` ⇒ `()`; luego, por hoja (orden de `lista.hojas`, un cod una vez) y forma (cod y código
  completo), `_equivalente(segmentos_lectura, segmentos_forma)`.
- **Tres condiciones de design §3 no se escriben porque son consecuencia de la precondición** (lectura fuera de
  lista ⇒ ninguna forma de ninguna hoja tiene sus mismos segmentos): «la hoja tiene algún segmento con letra» (sin
  él `_sin_letra(h) == h`), «la lectura no tiene ninguno» (`_sin_letra` no deja ninguno: R3 sale sola) y, en el
  sufijo, «la hoja tiene más segmentos». Escritas, eran tres mutantes equivalentes (rigor critico: 0 supervivientes).
  Lo explica la docstring de `_equivalente`; los tests de R3 y de «la hoja tiene que ser más larga» lo fijan.
- **sv6**: la búsqueda va en el `elif` de `resolucion.cambia` (una exacta/normalizada nunca busca). Con un cod,
  `nuevas[posicion] = cod` (misma copia profunda de F-076: IA4, rama directa y builder lo ven igual). `anotar`:
  con un cod, `codigo_partida_albaran = leída` y el motivo de revisión es `partida_equivalente:<leída>><cod>` en
  lugar de `partida_fuera_de_lista` (mismo camino que lo pone en línea y cabecera con
  `at_least_one_line_requires_review`); con varios, lo de hoy más `partida_equivalente_ambigua:…`.
- **R16, solo en la línea**: la spec dice cabecera para R15 y calla para R16; la ambigua lleva en cabecera
  `partida_fuera_de_lista` como hoy y el detalle de candidatas solo en la línea.
- **Log** (R22): el INFO de siempre añade `equivalentes=<únicas> ambiguas=<con 2 o más>`.
- Por defecto `equivalente=False` en el constructor (los llamantes y tests de F-076/F-111 no cambian); el
  interruptor de `settings` vale `true` y lo pasa `construir_normalizador_partidas`.

## 3. Desviaciones respecto a la spec (justificadas)

- **D-1 · `test_f111_t5_version_0130`**: R12 obliga a 0.14.0 y ese test exigía la exacta 0.13.0; o cambia, o R12
  no se cumple. Se aplica el precedente del repositorio (F-110 con el de F-115, F-111 con el de F-110, F-098 con
  el de F-076): «desde 0.13.0, nunca menos» y paquete = pyproject. Ninguna otra aserción de F-111 tocada.
- **D-2 · `sv6.md`**: no está en design §6, pero es la tabla de variables del servicio y F-111 añadió ahí la suya;
  una fila.
- **D-3 · mutación con `--base 9c4bf43`** en vez de `dev`, por lo mismo del §0 (detalle en `progress/mutacion_F-117.md`).

## 4. Fase RED (trazas reales)

**T1 (comun), antes de T2:**
```
$ cd services/albaranes-comun; PYTHONPATH=<worktree>\services\albaranes-comun
$ python -m pytest tests/test_f117_equivalentes_partida.py -q -p no:cacheprovider
FAILED tests/test_f117_equivalentes_partida.py::test_f117_r9_ni_prefijo - Att...
FAILED tests/test_f117_equivalentes_partida.py::test_f117_r18_siempre_cods_de_la_lista[CI.03.08]
FAILED tests/test_f117_equivalentes_partida.py::test_f117_r11_docstring_del_modulo
FAILED tests/test_f117_equivalentes_partida.py::test_f117_r12_version_0140 - ...
FAILED tests/test_f117_equivalentes_partida.py::test_f117_r12_exportada - Att...
68 failed, 1 passed in 2.01s
```
Causas (`grep "^E  " | sort | uniq -c`):
```
     53 E       AttributeError: module 'ruesma_comun.sigrid.partidas' has no attribute 'equivalentes_partida'
     11 E       AttributeError: module 'ruesma_comun.sigrid.partidas' has no attribute 'RE_SEGMENTO_CON_LETRA'
      1 E       AttributeError: module 'ruesma_comun.sigrid.partidas' has no attribute 'MIN_SEGMENTOS_SUFIJO'
      1 E       AttributeError: module 'ruesma_comun.sigrid' has no attribute 'equivalentes_partida'
      1 E       AssertionError: assert 'equivalentes_partida' in 'Partidas HOJA de una obra en Sigrid y cómo casar ...
      1 E       AssertionError: assert '0.13.0' == '0.14.0'
```
El que pasa es `test_f117_r10_resolver_y_casar_siguen_igual` (R10: fija lo que NO debe cambiar). Tras T2:
`69 passed in 0.17s`.

**T3 (sv6), antes de T4:**
```
$ cd services/albaran-valoracion-persist
$ python -m pytest tests/test_f117_partida_equivalente.py -q -p no:cacheprovider
     22 E       TypeError: NormalizadorPartidas.__init__() got an unexpected keyword argument 'equivalente'
      3 E       AttributeError: <module 'application.services.normalizador_partidas' ...> has no attribute 'equivalentes_partida'
      3 E       AttributeError: 'NormalizadorPartidas' object has no attribute '_equivalente'
      2 E       AttributeError: 'NormalizacionSobre' object has no attribute 'equivalencias'
      1 E       AttributeError: module 'application.services.normalizador_partidas' has no attribute 'PREFIJO_PARTIDA_EQUIVALENTE'
      1 E                   AttributeError: 'Settings' object has no attribute 'partida_equivalente_enabled'
32 failed, 1 error in 2.99s
```
**T5 (pipeline), escrito antes de T4:**
```
$ python -m pytest tests/test_f117_pipeline.py -q -p no:cacheprovider
FAILED tests/test_f117_pipeline.py::test_f117_r24_albaran_de_0719 - TypeError...
FAILED tests/test_f117_pipeline.py::test_f117_r24_sin_f117_es_lo_de_hoy - Typ...
FAILED tests/test_f117_pipeline.py::test_f117_r25_sufijo_de_0719 - TypeError:...
FAILED tests/test_f117_pipeline.py::test_f117_r26_valoracion_directa[letra]
FAILED tests/test_f117_pipeline.py::test_f117_r26_valoracion_directa[sufijo]
5 failed in 1.14s
```
Tras T4, `test_f117_partida_equivalente.py` en verde (33) y el pipeline con 3 fallos **del fixture**, no del
código: sin línea de contrato no se llama a IA4 (`assert None == ['CI.03A.8']`) y en la rama directa el
`precio_neto_albaran` es el NETO de la línea, no el unitario (regla 13; `Obtained: 60.0, Expected: 540.0`).
Corregido el fixture (una línea de contrato de otra partida; neto 540): `5 passed`. `test_f117_r24_sin_f117_es_lo_de_hoy`
(interruptor apagado) fija lo de hoy: `CI.03.08` fuera de lista y 540 €.

## 5. Tests y evidencias

Última `bash harness/init.sh` (sobre `2ce59db` + fila del inventario, con `PYTHONPATH` a la comun del worktree
y `ARNES_SIN_CACHE=1`): **EXIT=1**, `1 comprobaciones fallidas`, la única la de cobertura (§0). Todas las suites en verde:

| Suite | Resultado | Tiempo |
|---|---|---|
| raíz | 1919 passed | 219,4 s |
| sv1 | 236 passed | 16,9 s |
| sv2 | 496 passed, 1 warning | 14,2 s |
| sv3 | 1608 passed | 32,6 s |
| sv4 | 2562 passed, 1 warning | 220,2 s |
| sv5 | 149 passed | 18,6 s |
| sv6 | **706 passed** (668 antes de F-117 + 38 nuevos) | 11,9 s |
| sv9 | 1186 passed | 32,8 s |
| comun | **1492 passed**, 2 skipped (1422 antes + 70 nuevos) | 37,2 s |

La pasada anterior falló además en la raíz (`test_f039_r2_todo_informe_de_mutacion_figura_en_el_inventario`):
faltaba la fila de `mutacion_F-117.md` en `progress/inventario_mutacion_F-039.md`; añadida (recuento 67 ⇒ 68).

### Evidencias

| Evidencia | Valor real |
|---|---|
| Tests nuevos de F-117 | 108 (comun 70, sv6 33 + 5), todos en verde |
| Cobertura líneas cambiadas, puerta de init (base `dev`) | `PUERTA COBERTURA: 21.7% de 263 líneas cambiadas cubiertas (57/263, umbral 80%, nivel critico)` — KO por los 206 de `scripts/medicion_F-117/` (§0) |
| Cobertura de lo de F-117 (`python -m harness.cobertura --base 9c4bf43`) | `PUERTA COBERTURA: 100.0% de 57 líneas cambiadas cubiertas (57/57, umbral 80%, nivel critico)` |
| Mutación (`python -m harness.mutacion --feature F-117 --base 9c4bf43`) | **32 generados, 32 muertos, 0 supervivientes**, 0 timeouts, 291,3 s, 4 workers (`progress/mutacion_F-117.md`) |
| Puerta de tamaño | OK (requirements 83/150, design 163/250, impl dentro del tope) |
| Lint | `ruff check` de los ficheros tocados: `All checks passed!` |

Sin supervivientes, no hay análisis pendiente.

## 6. Verificaciones MANUAL pendientes (no mías)

- **T8 (humano)**: desplegar comun 0.14.0 con sv6: `.\deploy.ps1 -Only sv6` → `.\check_deploy.ps1`; revalorar
  desde sv4 lo que decida por D7 (hoy solo la de 0719 `CI.03.08`).
- **T9 (líder, solo lectura)**: `.\scripts\medicion_F-117\run.ps1 m1_fuera_de_lista.py` y `m2_estrategias.py`.
- **T10**: `bash harness/init.sh` en verde (bloqueado por el §0).
- Antes de `git worktree remove`: quitar la *junction* `services/albaranes-front/.venv` (creada por mí a la del
  árbol principal) con `cmd /c rmdir`.
