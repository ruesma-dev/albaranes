# Informe del implementer · F-111 (residuos: contenedores 3/6/9 y partida de gestión de residuos)

- Rama: `feature/F-111-residuos-contenedores-y-partida` (worktree `../albaranes-F-111`).
- Spec: `specs/F-111-residuos-contenedores-y-partida/`. Rigor `critico`.
- Estado: A y B (T0–T12, T14) hechas y aprobadas el 2026-11-03; **parte C (T15–T21) hecha el 2026-11-06**.
  **T13 MANUAL pendiente** (líder, solo lectura, tras desplegar sv5 y sv6 y revalorar).

## Partes A y B (resumen; informe íntegro en `progress/impl_F-111_partes_AB.md`)

- A: tamaño de contenedor 3/6/9 m³ (sv6 `residuos_container_calc.py`, prompt de IA3). B: una línea de residuos
  sin partida no va a almacén; partida del capítulo de gestión de residuos (comun 0.13.0 `candidatas_residuos`,
  sv5 `POST /v1/albaranes/partida-residuos`, sv6 `partida_residuos.py`, matcher `sin_almacen`, pipeline).
- RED de T1–T10, tests, mutación (113/110/3 equivalentes, `progress/mutacion_F-111.md`) y cobertura (99,7 %):
  en el informe íntegro. Review APPROVED (`progress/review_F-111.md`).

## Parte C · primero la partida del contrato (T15–T21)

Regla del humano (2026-11-05): «que mire primero en las líneas del contrato si tiene partida; si es de gestión de
residuos que coja esa, y si no que busque». Decisiones: D1=b, D2=a, D3=a, D-C1=a, interpretación (i) enmendada
(caída al capítulo, R43), (ii) y (iii) aceptadas (`progress/spec_F-111.md` §7).

### C.1 Qué cambió

- **sv6 `application/services/partida_residuos.py`** (único fichero de producción de sv6 tocado):
  - Función pura nueva `partidas_del_contrato(lineas_contrato, lista, alm)` (R37): por cada `codigo_partida`
    legible, `resolver_partida_obra`; vale solo `exacta`/`normalizada` y sin `cod_repetido`; la hoja es la de
    `lista.hojas` con ese cod; sin duplicados, en orden de primera aparición.
  - `asignar` elige el paso UNA vez por documento: paso 1 (del contrato y del capítulo, prefijo
    `partida_residuos_contrato:`), paso 2 (todas las del contrato, `partida_residuos_contrato_hoja:`), paso 3
    (el capítulo, `partida_residuos:`, la parte B tal cual).
  - `_resolver(documento, lineas, conjunto, prefijo, intento)` extraído: 0 ⇒ `sin_capitulo`, 1 ⇒ esa sin IA,
    ≥ 2 ⇒ IA solo entre el conjunto. Devuelve asignadas, pendientes y el motivo de revisión.
  - (R43) Si en el paso 1/2 quedan pendientes (IA `null`, fuera del conjunto, sin respuesta, fallo o sin elector),
    SOLO esas se resuelven contra el capítulo (segunda llamada como mucho, R41), con
    `intento = partida_residuos_contrato_sin_eleccion:<cods del conjunto, hasta 5>`.
  - `ResultadoPartidaResiduos.intento` (defecto `None`); `anotar` lo añade a la línea antes del motivo final,
    nunca a la cabecera ni a revisión.
  - Constantes `PREFIJO_PARTIDA_RESIDUOS_CONTRATO`, `PREFIJO_PARTIDA_RESIDUOS_CONTRATO_HOJA`,
    `MOTIVO_CONTRATO_SIN_ELECCION` (R46). Log con `paso=` (`contrato`/`contrato_hoja`/`capitulo`) y
    `caidas_al_capitulo=`.
  - `alm_codigo_partida` deja de descartarse: `self._alm` va a `partidas_del_contrato` (un `ALM` del contrato
    es `no_aplica`). Docstring del módulo con los tres pasos.
- **sv5 `config/prompts.yaml`** (`partida_residuos_es`, R48): la frase de candidatas pasa a «las partidas hoja de
  la obra (del contrato del proveedor o del capitulo de gestion de residuos)»; reglas y esquema sin tocar. Se
  actualiza también el comentario de cabecera del bloque.
- **`docs/ARCHITECTURE.md`** (R47): punto 16 (excepción de residuos a F-051: la única copia de partida del
  contrato, solo residuos sin lectura y siempre validada contra la obra) y punto 27 (los tres pasos, la caída al
  capítulo y los rastros nuevos).
- **No cambian**: pipeline, composición, settings (mismo `PARTIDA_RESIDUOS_ENABLED`), matcher, builder, comun,
  DDL. `azure-apps/albaranes.md` tampoco (ni endpoint ni contrato nuevos, T19).

### C.2 Tests

- Nuevo sv6 `tests/test_f111_partida_contrato.py` (39 tests recogidos, 33 funciones): las 6 obras medidas en listas sintéticas (0686,
  0669, 0694, 0687, 0459, sin capítulo), descartes de R37 (`ALM`, vacía, no hoja, inexistente, ambigua,
  cod repetido, duplicados, `alm=None`, contrato `None`, `ALM` vía `asignar`), R41 (dos llamadas como mucho, solo las caídas en la segunda), R43
  (5 variantes de «no elige» en 0669 ⇒ IA del capítulo; capítulo de 1; capítulo que también falla ⇒ revisión;
  obra sin capítulo; sin elector; hasta 5 códigos), R44, R45, `anotar` (orden intento ⇒ motivo, cabecera intacta)
  y R46 (constantes y `paso=` en el log).
- Nuevo test de pipeline `test_f111_r38_el_pipeline_toma_la_partida_del_contrato` (paso 1 de punta a punta).
- sv5 `tests/test_f111_partida_residuos.py`: `test_f111_r48_...` (frase nueva, la vieja fuera, reglas de R32).
- **Retocados** (sin relajar aserciones): los helpers `_envelope` de `test_f111_partida_residuos.py` y
  `test_f111_pipeline.py` de sv6 dejan el contrato **sin partidas** (R40) para seguir probando el paso 3: el
  escenario compartido trae `32.01` en el contrato y, con la parte C, esos tests habrían pasado al paso 1. Se
  hace con **copias** (`model_copy`): la primera versión mutaba los DTO de `CONTRATO_SALMEDINA`, compartidos
  por módulo, y rompía un test del matcher que se ejecutaba después (detectado y corregido antes del commit).

### C.3 Decisiones y desviaciones

1. Sin desviaciones de la spec. Detalles no fijados por ella, resueltos así:
   - En el paso 1/2 el conjunto va **en el orden del contrato** (primera aparición); en el paso 3, en el de la
     lista (como B). El intento cita los códigos del conjunto del paso 1/2 en ese orden.
   - Si el conjunto del paso 1 coincide con el capítulo y la IA no elige, la línea vuelve a la IA con el capítulo
     (segunda llamada): es lo que dice R43 literalmente; no se ha optimizado.
   - El motivo de revisión tras una caída cita las candidatas del **capítulo** (los de la parte B), y la línea
     conserva además el intento.
2. Línea base de init.sh al empezar (2026-11-06): todo verde salvo sv6, que salió rojo **solo** porque el fichero
   RED de T15 ya estaba escrito (`ImportError` de `MOTIVO_CONTRATO_SIN_ELECCION`); el resto de suites, verde.

### C.4 Fase RED (trazas reales)

Desde la carpeta del servicio, con `PYTHONPATH=C:\Users\pgris\PycharmProjects\albaranes-F-111\services\albaranes-comun`.

**T15** (antes de cualquier código): `python -m pytest tests/test_f111_partida_contrato.py -q --tb=line -p no:cacheprovider`
```
tests\test_f111_partida_contrato.py:22: in <module>
    from application.services.partida_residuos import (
E   ImportError: cannot import name 'MOTIVO_CONTRATO_SIN_ELECCION' from 'application.services.partida_residuos'
ERROR tests/test_f111_partida_contrato.py
1 error in 6.47s
```
**T17** (con T16 hecho: constantes y `partidas_del_contrato`, `asignar` aún de la parte B), mismo comando:
```
test_f111_partida_contrato.py:211: AssertionError: assert None == '32.01'                       (0686, paso 1)
test_f111_partida_contrato.py:226: AssertionError: assert ['102.08.01',....01', '31.02'] == ['31.01', '102.08.01']  (0669)
test_f111_partida_contrato.py:241: AssertionError: assert '23.01' == 'CI.03A.7'                   (0694, paso 2)
test_f111_partida_contrato.py:282: AssertionError: assert 'partida_resi..._sin_capitulo' == 'partida_resi...hoja:CI.03A.7'
test_f111_partida_contrato.py:301: AssertionError: assert 1 == 2          (×5, R43: no había segunda llamada)
test_f111_partida_contrato.py:350: AssertionError: assert None == 'partida_residuos_contrato_sin_eleccion:31.01,102.08.01'
test_f111_partida_contrato.py:424: AssertionError: assert 'partida_residuos_contrato:32.01' in [..., 'partida_residuos_ia_fallo:32.01,37.06.01']
test_f111_partida_contrato.py:438: AssertionError: assert ['partida_res...,31.01,31.02'] == ['partida_res...siduos:31.02']
INFO ... [partida-residuos] document_id=doc-SS-0000589 obra=0686 candidatas=1 asignadas=1 a_revision=0   (sin paso=)
22 failed, 14 passed in 5.17s
```
Los 14 que pasaban eran los de R37 (T16, `-k "r37 or constantes"`: 7 passed), R40 y R44/R45 (la parte B ya los
cumplía). Tras T17: `tests/test_f111_partida_contrato.py tests/test_f111_partida_residuos.py
tests/test_f111_pipeline.py` ⇒ **90 passed in 7.07s**.

**T18** (sv5): `python -m pytest tests/test_f111_partida_residuos.py -q --tb=line -p no:cacheprovider`
```
tests\test_f111_partida_residuos.py:207: AssertionError: assert 'partidas hoja de la obra (del contrato del proveedor o del capitulo de gestion de residuos)' in 'eres un experto en presupuestos de obra en espana. ...'
FAILED tests/test_f111_partida_residuos.py::test_f111_r48_las_candidatas_son_hojas_de_la_obra_del_contrato_o_del_capitulo
1 failed, 17 passed in 32.59s
```
Tras el cambio del prompt: **18 passed in 40.27s**.

### C.5 Mutación y cobertura (T20)

Informe: `progress/mutacion_F-111_C.md` (fila nueva en `progress/inventario_mutacion_F-039.md`, recuento 67).
Comando: `python -m harness.mutacion --feature F-111 --base 16023b0 --max-mutantes 0 [--workers 1] --salida
progress/mutacion_F-111_C.md` (alcance: el diff de la parte C, solo `partida_residuos.py`, 167 líneas).

- **Herramienta, pasada 1** (`b69192a`, 4 workers): 14 mutantes, 13 muertos, **1 superviviente** (`caidas = 0 → 1`,
  solo visible en el log): hueco real, test nuevo del log.
- **Mutantes a mano** (la herramienta genera pocos en este diff): 28 sobre `partidas_del_contrato`, la elección de
  paso y la caída al capítulo; **4 supervivientes**: 2 equivalentes (filtro de vacías y deduplicado redundantes:
  código eliminado) y 2 huecos (`alm` de `asignar` y `lineas_contrato=None`: tests nuevos). Ronda 2: 25/25 muertos
  más el de `cod_repetido` reformulado (muerto). Tabla en el informe de mutación.
- **Herramienta, pasada 2 (definitiva)** sobre `2e8ea2e`, 1 worker: **13 mutantes, 13 muertos, 0 supervivientes**,
  0 timeouts, 612,3 s.

### C.6 Fuera de alcance y pendiente

- **T13 MANUAL** (líder, solo lectura, tras desplegar y revalorar): las 8 líneas de `design.md` §13 (0686 ⇒
  `partida_residuos_contrato:32.01`, 0694/0697 ⇒ `partida_residuos_contrato_hoja:CI.03A.7`, 0687 ⇒
  `partida_residuos:19.01`) y contar las `partida_residuos_contrato_sin_eleccion`.
- **Despliegue** (humano): **sv5 y sv6** (comun sin cambios). Si sv6 sale antes que sv5, la IA recibe la frase
  vieja en el paso 2: elige igual (las reglas no cambian), solo la descripción de las candidatas es inexacta.
- **Lo ya valorado** cambia solo al revalorar (D7).
- Evals con LLM (`python -m evals.runner --con-llm --feature F-111`) no lanzados (coste): lo decide líder/humano.
- Entorno: *junction* `.venv` de sv4 en el worktree (quitarla con `cmd /c rmdir` antes de `git worktree remove`).
- Nada contra producción, sin `.env`, sin push, sin despliegue.

## Evidencias (parte C)

| Evidencia | Valor |
|---|---|
| `bash harness/init.sh` (T21, 2026-11-06, `PYTHONPATH` a la comun del worktree, `ARNES_SIN_CACHE=1`) | **ENTORNO LISTO**, salida 0 |
| Tests ejecutados (init.sh) | raíz 1919 · sv1 236 · sv2 496 · sv3 1608 · sv4 2562 · **sv5 149** · **sv6 667 (+1 skipped)** · sv9 1186 · comun 1424; todo verde |
| Tests nuevos de la parte C | sv6 +40 (`test_f111_partida_contrato.py` 39, pipeline 1) · sv5 +1 |
| Cobertura de las líneas cambiadas | **100,0 %** (57/57, umbral 80 %, `critico`), línea PUERTA COBERTURA |
| Mutantes generados / supervivientes | herramienta pasada 2: **13 / 0** (pasada 1: 14 / 1, resuelto) · a mano: 28 / 4 ⇒ 2 equivalentes eliminados + 2 tests; ronda 2: 26 / 0 |
| Tiempo de la campaña de mutación | pasada 2: 612,3 s (1 worker) · pasada 1: 357,0 s (4 workers) |
| Tiempo de las suites (init.sh) | sv6 90,6 s · sv5 149,4 s · comun 233,0 s · raíz 2176,6 s · sv4 1426,4 s |
| Avisos no bloqueantes | PUERTA RUTAS SENSIBLES [evals]: `prompts.yaml` de sv5 y `partida_residuos.py` sin `progress/evals_F-111.md`; **no lanzado** (`python -m evals.runner --con-llm --feature F-111` llama a LLM reales con coste): lo decide líder/humano |
