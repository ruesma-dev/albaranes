<!-- progress/impl_F-001.md -->
# F-001 · Informe de implementación — Test de estructura del monorepo

- Rama: `feature/F-001-test-estructura` (base común con `dev`: `42139da`).
- Modo: `sdd=false` — la mini-spec son los `acceptance` de
  `harness/features.json`. Nivel de rigor declarado: **estandar** (exige fase
  RED, cobertura de líneas cambiadas y campaña de mutación).
- Fecha: 2026-08-13.
- Commits de la rama:
  - `8dd31e1` — `F-001: test de estructura del monorepo (servicios.json contra
    el arbol real)`.
  - (este informe y `progress/current.md`, en el commit siguiente).

## Qué cambió

Un único fichero nuevo, más el directorio que lo contiene:

| Fichero | Estado | Qué hace |
|---|---|---|
| `tests/test_estructura_monorepo.py` | nuevo (116 líneas) | 4 tests que validan `harness/servicios.json` contra el árbol real |

No se ha tocado ningún otro fichero del repositorio: ni servicios, ni
`harness/`, ni manifiestos, ni `.env`. La carpeta `tests/` de la raíz no
existía y se crea con esta feature (`init.sh` la echaba en falta con el aviso
«No existe tests/ todavía — créala en la primera feature»).

## Trazabilidad: un test por criterio `acceptance`

| # | Criterio `acceptance` | Test |
|---|---|---|
| R1 | Existe `tests/test_estructura_monorepo.py` con primera línea de comentario de ruta | `test_f001_r1_el_fichero_declara_su_ruta_en_la_primera_linea` |
| R2 | Cada `ruta` de `harness/servicios.json` existe como directorio del repo | `test_f001_r2_cada_ruta_declarada_existe_como_directorio` |
| R3 | Cada servicio `python` declarado contiene `pyproject.toml` o `main.py` | `test_f001_r3_cada_servicio_python_trae_pyproject_o_main` |
| R4 | El test pasa sin red ni BBDD (solo filesystem y json de la stdlib) | `test_f001_r4_el_test_solo_importa_biblioteca_estandar` |
| R5 | `bash harness/init.sh` en verde | Sin test automatizado — ver justificación abajo |

**R5 no tiene test propio y es deliberado, no un hueco.** La sección 7 de
`init.sh` ejecuta la suite de la raíz; un test que invocara `init.sh` se
llamaría a sí mismo (recursión y minutos de suite por cada ejecución). La
verificación de R5 es la ejecución real del portero, con su salida pegada más
abajo: `ENTORNO LISTO. Puedes trabajar.`, exit code 0.

## Decisiones de diseño

1. **La raíz del repo se deduce del propio fichero** (`Path(__file__).resolve()
   .parents[1]`), sin variables de entorno ni parámetros. Esto convierte el
   módulo en portable: copiado a otro árbol, valida ese otro árbol — que es
   exactamente lo que ha permitido montar la fase RED sin tocar el
   `harness/servicios.json` real (ver abajo).
2. **Los fallos se acumulan en una lista y se afirman de golpe** en vez de un
   `assert` por servicio: con 8 servicios declarados, ver «faltan estas tres
   rutas» vale más que ver solo la primera, sobre todo porque `init.sh` lanza
   pytest con `-x`.
3. **R4 se verifica leyendo el AST del propio fichero** (`ast.parse` + `walk`
   sobre `Import`/`ImportFrom`) y comparando contra una lista blanca
   (`MODULOS_PERMITIDOS = {__future__, ast, json, pathlib}`). Es la única forma
   de que «sin red ni BBDD» sea una afirmación comprobable y no un comentario:
   el día que alguien añada `import requests` o `import psycopg`, el test lo
   dice. La alternativa (interceptar sockets en runtime) exigiría plugins, y el
   criterio pide stdlib pura.
4. **`cargar_servicios` falla si el fichero no existe o la lista está vacía.**
   Sin ese guard, un `servicios.json` vacío o renombrado haría pasar R2 y R3
   *en vacío*: cero servicios, cero fallos, verde mentiroso. Es el riesgo real
   de un test que itera sobre una declaración externa.
5. **Sin `tests/__init__.py`** y sin `conftest.py`: no hacen falta (el módulo no
   importa nada del repositorio) y `__init__.py` habría cambiado el modo de
   importación de pytest para toda la raíz.
6. **`lenguaje` se compara normalizado** (`.strip().lower()`) para que un
   `"Python"` en la declaración no deje al servicio sin comprobar en silencio.

## Fase RED (nivel `estandar`)

La feature es *ella misma* un test: no hay código de producción cuyo fallo
previo se pueda enseñar. La demostración equivalente —y más exigente— es que el
test **falla de verdad cuando lo que vigila está roto**, no solo que pasa hoy.
Se han montado dos árboles rotos en el directorio de scratchpad, con una copia
del fichero entregado, **sin tocar en ningún momento el `harness/` real**.

### RED A — declaración desalineada del árbol (R2 y R3)

Árbol temporal con un `harness/servicios.json` que declara una ruta inexistente
y un servicio `python` sin `pyproject.toml` ni `main.py`.

Comando exacto (desde el árbol temporal):

```
/c/Users/pgris/PycharmProjects/albaranes/.venv/Scripts/python.exe -m pytest tests/test_estructura_monorepo.py -q --tb=short -p no:cacheprovider
```

Salida real:

```
.FF.                                                                     [100%]
================================== FAILURES ===================================
___________ test_f001_r2_cada_ruta_declarada_existe_como_directorio ___________
tests\test_estructura_monorepo.py:87: in test_f001_r2_cada_ruta_declarada_existe_como_directorio
    assert not inexistentes, (
E   AssertionError: harness/servicios.json declara rutas que no existen como directorio del repositorio: ['sv-fantasma -> services/no-existe-esta-ruta']
E   assert not ['sv-fantasma -> services/no-existe-esta-ruta']
___________ test_f001_r3_cada_servicio_python_trae_pyproject_o_main ___________
tests\test_estructura_monorepo.py:104: in test_f001_r3_cada_servicio_python_trae_pyproject_o_main
    assert not sin_manifiesto, (
E   AssertionError: Servicios declarados como python sin ninguno de ['pyproject.toml', 'main.py']: ['sv-fantasma -> services/no-existe-esta-ruta', 'sv-sin-manifiesto -> services/servicio-sin-manifiesto']
E   assert not ['sv-fantasma -> services/no-existe-esta-ruta', 'sv-sin-manifiesto -> services/servicio-sin-manifiesto']
=========================== short test summary info ===========================
FAILED tests/test_estructura_monorepo.py::test_f001_r2_cada_ruta_declarada_existe_como_directorio
FAILED tests/test_estructura_monorepo.py::test_f001_r3_cada_servicio_python_trae_pyproject_o_main
2 failed, 2 passed in 0.10s
```

### RED B — fichero degradado: sin cabecera de ruta y con red (R1 y R4)

Mismo montaje, con un `servicios.json` coherente (para aislar R1 y R4) y una
copia del fichero a la que se le quita la cabecera de ruta y se le añade
`import socket`.

Comando exacto: el mismo de arriba, en el segundo árbol temporal.

Salida real:

```
F..F                                                                     [100%]
================================== FAILURES ===================================
_________ test_f001_r1_el_fichero_declara_su_ruta_en_la_primera_linea _________
tests\test_estructura_monorepo.py:76: in test_f001_r1_el_fichero_declara_su_ruta_en_la_primera_linea
    assert primera_linea == CABECERA_ESPERADA, (
E   AssertionError: La primera línea debe ser '# tests/test_estructura_monorepo.py' (docs/CONVENTIONS.md), y es '# fichero sin su cabecera de ruta relativa'
E   assert '# fichero si...ruta relativa' == '# tests/test...a_monorepo.py'
E     
E     - # tests/test_estructura_monorepo.py
E     + # fichero sin su cabecera de ruta relativa
____________ test_f001_r4_el_test_solo_importa_biblioteca_estandar ____________
tests\test_estructura_monorepo.py:115: in test_f001_r4_el_test_solo_importa_biblioteca_estandar
    assert not prohibidos, (
E   AssertionError: Este test debe funcionar solo con filesystem y json de la biblioteca estándar; importa además: ['socket']
E   assert not ['socket']
=========================== short test summary info ===========================
FAILED tests/test_estructura_monorepo.py::test_f001_r4_el_test_solo_importa_biblioteca_estandar
FAILED tests/test_estructura_monorepo.py::test_f001_r1_el_fichero_declara_su_ruta_en_la_primera_linea
2 failed, 2 passed in 0.08s
```

Entre los dos árboles, **los cuatro tests se han visto fallar por su motivo
propio**. Después, contra el repo real:

```
$ .venv/Scripts/python.exe -m pytest tests/test_estructura_monorepo.py -q --tb=short -p no:cacheprovider
....                                                                     [100%]
4 passed in 0.02s
```

Los dos árboles temporales viven en el scratchpad de la sesión, fuera del
repositorio; no quedan artefactos sin trackear.

## Verificación: `bash harness/init.sh`

Ejecutado tal cual, sin pipes. Exit code 0. Salida relevante:

```
[OK] Arnés v1.3.0 (2026-08-10)
[OK] Python: Python 3.12.7
     11 features, 11 abiertas, en curso: ['F-001'], bloqueadas: ninguna
[OK] features.json válido
[OK] harness/rigor.json y niveles declarados: válidos
[OK] compileall: sin errores de sintaxis
[AVISO] ruff no instalado: pip install -r requirements-dev.txt
[AVISO] coverage no instalado: pip install -r requirements-dev.txt
sss.......................                                               [100%]
23 passed, 3 skipped in 96.87s (0:01:36)
[OK] pytest en verde
[OK] harness/servicios.json válido
[AVISO] servicio sv1-email … sv6-valoracion-persist: sin directorio de tests
sss...................                                                   [100%]
19 passed, 3 skipped in 100.39s (0:01:40)
[OK] servicio comun (services/albaranes-comun): pytest en verde
[AVISO] servicio infra (infra): lenguaje 'otro' y sin comando_tests
[OK] PUERTA COBERTURA: N/A (F-001 no cambia líneas Python de producción frente a dev)
[OK] Rama actual: feature/F-001-test-estructura
----------------------------------------
ENTORNO LISTO. Puedes trabajar.
```

## Hallazgos para el líder (no corregidos: fuera del alcance de F-001)

1. **La suite de `comun` se ejecuta ahora dos veces por cada `init.sh`.** Al
   crear `tests/` en la raíz se activa la sección 7 de `init.sh`, que lanza
   `pytest` desde la raíz **sin argumento de ruta**; sin `testpaths`
   configurado, pytest recolecta todo el árbol y arrastra
   `services/albaranes-comun/tests/` (de ahí los 23 tests de la raíz = mis 4 +
   los 19 de `comun`). Luego la sección 7 bis los vuelve a ejecutar con el venv
   del servicio. Coste medido: **~97 s extra por ejecución del portero**, y los
   tests de `comun` corriendo con el intérprete de la raíz, que no es el suyo
   (hoy pasan, pero es una coincidencia que no debería sostener el arnés).
   Arreglo natural: acotar la recolección de la raíz (`testpaths = tests` en un
   `pyproject.toml`/`pytest.ini` de raíz, o pasar `tests` como argumento en la
   sección 7 de `init.sh`). Ambas cosas caen **fuera de los ficheros que esta
   feature tiene permitido tocar** (`tests/` y `progress/`), y la segunda es
   una mejora del arnés genérico que tocaría propagar a `arnes-base`.
2. **`coverage` y `ruff` no están instalados en el venv de la raíz.** No
   bloquean hoy (la puerta de cobertura sale N/A por otro motivo, ver
   Evidencias), pero la primera feature que toque código de producción se
   encontrará la puerta de cobertura sin datos con los que medir.
3. Seis de los ocho servicios declarados **no tienen directorio de tests**;
   `init.sh` lo avisa uno por uno. F-001 no lo cambia: solo comprueba que las
   rutas y los manifiestos declarados existen.

## Verificaciones MANUAL (humano) pendientes

**Ninguna.** Todo lo que exigen los `acceptance` de F-001 es automático y se ha
ejecutado: los 4 tests y el portero completo. La feature no toca Azure, ni
BBDD, ni sistemas de producción.

## Fuera de alcance (lo que esta feature NO hace)

- No valida el resto de campos de `servicios.json` (`comando_tests`, venv de
  cada servicio): de eso ya se ocupa `harness/servicios.py --validar`, que
  `init.sh` ejecuta en la sección 7 bis.
- No comprueba el sentido inverso (un directorio de servicio en el árbol que
  nadie declare en `servicios.json`). Es un hueco real y consciente: hoy no
  hay forma de distinguir un servicio sin declarar de una carpeta cualquiera
  bajo `services/`. Si interesa, es otra feature.
- No añade tests a ningún servicio ni toca su código.

## Evidencias

| Evidencia | Valor real |
|---|---|
| **Tests ejecutados y resultado** | Fichero de la feature: **4 pasados, 0 fallos** (`4 passed in 0.02s`). Suite de la raíz completa dentro de `init.sh`: **23 pasados, 3 saltados, 0 fallos**. Suite del servicio `comun`: **19 pasados, 3 saltados, 0 fallos**. Veredicto del portero: `ENTORNO LISTO`, exit code 0 |
| **Cobertura de las líneas cambiadas** | **N/A**, con el motivo impreso por `bash harness/init.sh`: `[OK] PUERTA COBERTURA: N/A (F-001 no cambia líneas Python de producción frente a dev)`. El único fichero de la feature vive en `tests/`, y `harness/alcance.py` excluye por diseño `tests`, `specs`, `progress` y `docs` del código de producción medible (`DIRECTORIOS_EXCLUIDOS`). Nota adicional: `coverage` tampoco está instalado en el venv de la raíz, pero no es la causa del N/A — el alcance ya es vacío |
| **Mutantes generados y supervivientes** | **0 mutantes generados, 0 evaluados, 0 muertos, 0 supervivientes, 0 timeouts** en 0,0 s. Informe generado por la herramienta en `progress/mutacion_F-001.md`. Alcance recalculable: `F-001: 0 fichero(s), 0 línea(s) de producción (origen rama, 42139da..feature/F-001-test-estructura)` |
| **Tiempo de ejecución de la suite** | Fichero de la feature aislado: **0,02 s**. Suite de la raíz bajo `init.sh`: **96,87 s** (dominada por los tests de humo de `comun` que arrastra la recolección, ver Hallazgo 1). Suite del servicio `comun`: **100,39 s**. Portero completo: ~3 min 20 s |

### Análisis de supervivientes

**No hay supervivientes que analizar, y conviene decir por qué en vez de
apuntar un cero tranquilizador**: la campaña generó **cero mutantes** porque el
alcance de mutación de F-001 es vacío. `harness/alcance.py` excluye `tests/`
del código de producción, y F-001 no añade otra cosa. No es que las mutaciones
se hayan muerto todas: es que no había nada que mutar. La campaña se lanzó
igualmente y su informe está en `progress/mutacion_F-001.md` con sus totales
reales, verificables con `python -m harness.alcance` / `python -m
harness.mutacion --feature F-001`.

La señal que la mutación no puede dar aquí la da la **fase RED**: los dos
árboles rotos son, en la práctica, mutaciones del entorno que estos tests
observan (una ruta que desaparece, un manifiesto que falta, una cabecera que se
pierde, un import de red que se cuela), y **los cuatro tests las cazaron**, con
la traza pegada más arriba.
