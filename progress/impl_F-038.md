<!-- progress/impl_F-038.md -->
# F-038 · Informe de implementación

Rama `feature/F-038-coste-del-ciclo-sdd`, rigor `estandar`, un commit por tarea
(T0–T14). **Sometido al tope que esta feature establece: 150 líneas.**

## Qué cambió, por tarea

| T | Qué cambió | Ficheros |
|---|---|---|
| T0 | `EjecutorPytest` gana `ruta`, que acota la recolección y entra en `identidad()`; `ejecutor_para` la resuelve a `tests` para lo que no cae en un servicio Python (R1–R4) | `harness/mutacion.py` |
| T1 | `max_mutantes_nivel`, `semilla_nivel`, `topes_tamano`: claves opcionales, valor inválido = ausencia (R5, R13) | `harness/rigor.py` |
| T2 | `nivel_por_defecto` → `estandar`; `estandar` 20 mutantes + semilla `20260820`; `critico` sin tope; bloque `tamano` 120/200/150/100 (R5, R8, R13) | `harness/rigor.json` |
| T3 | `resolver_muestreo` (pura) y `_muestreo_configurado`; el CLI los aplica en serie y en paralelo (R6, R7) | `harness/mutacion.py` |
| T4 | `comprobar_linea_base` devuelve segundos por ejecutor; el informe gana `sha_head`, `segundos_linea_base` y la media por mutante; la campaña paralela los propaga (R10–R12) | `harness/mutacion.py`, `harness/mutacion_paralela.py` |
| T5 | `escribir_informe` imprime SHA, línea base, media por mutante y el muestreo con su nivel (R9–R12) | `harness/mutacion.py` |
| T6 | Nuevo medidor de topes de papeleo, códigos 0/1/2 (R14, R16) | `harness/tamano.py` |
| T7 | Sección **7 quater**: mide SOLO la feature en curso; código 1 → rojo, 2 → N/A con motivo (R15) | `harness/init.sh` |
| T8 | Topes 120/200/150 y «lo que no cabe se resume y se enlaza» (R17) | `specs/SPECS.md`, `spec-author.md`, `implementer.md` |
| T9 | Informe ≤ 100, umbral 5 min → **60 s**, revisión incremental declarando SHA, y RM1–RM6 con RM5 acotada a `critico` (R18–R20) | `.claude/agents/reviewer.md` |
| T10 | C4 bis: 60 s y checkbox de RM1, RM2, RM5 y RM6; ninguna puerta automática nueva (R20, R21) | `CHECKPOINTS.md` |
| T11 | Cabecera «CAMPAÑA NO VÁLIDA» donde se midió con la invocación rota (R22) | `progress/mutacion_F-011.md`, `_F-012.md` |
| T12 | Campaña de mutación + los tests que cerraron sus huecos (3 commits) | `tests/`, `progress/mutacion_F-038.md` |
| T13 | Estado real de F-038 y deuda declarada (F-039, F-011, porte a 1.7.0) en `progress/current.md`; T14, portero en verde | `progress/current.md` |

Tests nuevos (84) en `tests/test_f038_*.py`, uno por bloque de requisitos.

## Decisiones y desviaciones respecto al `design.md`

1. **`_muestreo_configurado` devuelve tres valores, no dos**: tope, semilla y
   **nivel**, porque R9 exige que el informe declare quién fijó la semilla y
   resolverlo aparte obligaría a releer los mismos dos JSON.
2. **Dos añadidos que el design no nombraba y R10–R12 necesitan:**
   `sha_de_head(raiz)` y la propiedad `InformeMutacion.segundos_por_mutante`.
3. **Coherencia de R8 fuera de `rigor.json`:** cinco sitios seguían diciendo que
   quien no declara `rigor` arrastra «el más exigente (`critico`)»
   (`CHECKPOINTS.md`, `rigor.py`, `init.sh`, `features.json`, `implementer.md`).
   Cambiados al `nivel_por_defecto`: dejarlos daba dos respuestas a la misma
   pregunta.
4. **T11 marca dos informes, no uno** (criterio abajo); **T13** cambia de
   contenido (las tres preguntas ya están respondidas en `requirements.md`); y
   **`arnes-base` NO se ha tocado** (D6).

## Fase RED · trazas reales

Las cuatro centrales, pegadas; las demás, con su error literal.

**T0 — R1–R4** · `python -m pytest tests/test_f038_r1_r4_ejecutor_raiz.py -q --tb=line`
```
E   AttributeError: 'EjecutorPytest' object has no attribute 'ruta'   (línea 81)
E   TypeError: EjecutorPytest.__init__() got an unexpected keyword argument 'ruta'
9 failed, 1 passed in 0.78s
```
**T3 — R6, R7** · `python -m pytest tests/test_f038_r5_r9_muestreo_por_nivel.py -q --tb=line`
```
    from harness.mutacion import (
E   ImportError: cannot import name '_muestreo_configurado' from 'harness.mutacion'
1 error in 0.20s
```
**T5 — R9–R12** · `python -m pytest tests/test_f038_r10_r12_informe.py -q --tb=line`
```
E   AssertionError: assert '| Media por mutante evaluado (s) | n/d |' in '<!-- ...vacio.md -->\n# F-...| Muestreo | no: campaña completa |\n...'
E   AssertionError: assert 'Muestreo | sí — 1 de 61 mutantes, semilla `20260820`, nivel `estandar`' in '...1 mutantes, semilla `20260820` |\n...'
5 failed, 9 passed in 0.56s
```
**T6 — R14, R16** · `python -m pytest tests/test_f038_r13_r16_tamano.py -q --tb=line`
```
    from harness.tamano import ETIQUETA, main, medir, slug_de_feature
E   ModuleNotFoundError: No module named 'harness.tamano'
1 error in 0.21s
```
**T1:** `ImportError: cannot import name 'max_mutantes_nivel' from
'harness.rigor'` y `… 'topes_tamano' …` (2 errores de recolección). **T2:**
`assert 'critico' == 'estandar'` y `assert {} == {'requirements': 120, ...}`
(3 failed). **T4:** `ImportError: cannot import name 'sha_de_head' from
'harness.mutacion'`. **T7:** `IndexError: list index out of range` al partir
`init.sh` por `7 quater`, que no existía (2 failed). **T8–T10:** 5, 5 y 3 fallos
`assert … in` (`assert '150' in …`, `assert 'RM1' in bloque`,
`'inferior a 5 minutos' not in texto`).

## T11 · informes revisados y criterio aplicado

Criterio: **alcance entero fuera de `services/`** —luego juzgado con `pytest`
sin ruta— **y sin remedición por rodeo**. Los 10 informes:

- **Marcado `_F-012.md`** (`harness/*.py`, 61 mutantes): remedición = **F-039**.
- **Marcado `_F-011.md`** (`evals/**`, `harness/rutas_sensibles.py`; 305
  mutantes, 133 supervivientes): **sin ficha**, deuda anotada en `current.md`.
- **No marcado `_F-034.md`**, pese a medir `harness/mutacion.py`: ya se remidió
  a mano con la ruta acotada y su cabecera lo documenta; marcarlo sería falso.
- **No marcados** `F-001`, `F-002`, `F-019(+remedida)`, `F-027(+remedida)`,
  `F-035`: alcance de `services/`, con la suite del servicio, siempre acotada.

## Campaña de mutación (T12) → `progress/mutacion_F-038.md`

`python -m harness.mutacion --feature F-038 --timeout 600 --workers 1` (con el
timeout por defecto, 120 s, la suite de la raíz roza el corte bajo carga). Tres
campañas, **los mismos 20 mutantes de 55**: el muestreo es reproducible.

| Campaña | Muertos | Supervivientes | Tiempo |
|---|---|---|---|
| 1ª (`ce352ed`) | 13 | 7 | 940,7 s |
| 2ª (`1ac47f1`) | 18 | 2 | 774,8 s |
| **3ª, la del informe (`337a948`)** | **19** | **1** | **728,5 s** |

Seis supervivientes eran **huecos reales**, cerrados con tests: la frontera `1`
de `resolver_muestreo` y de `topes_tamano`, el slug de una rama con dos barras,
el resumen de `harness.tamano` (nadie comprobaba **qué** decía la puerta en
verde) y el eco `Muestreo: hasta N mutantes`.

**El único superviviente** es `@dataclass(frozen=True) -> frozen=False`
(`harness/tamano.py:47`): **equivalente para el comportamiento observable**
—nadie asigna un atributo de un `Exceso`—, analizado en el informe de la
campaña. Ninguna sección quedó en `PENDIENTE`.

**Hallazgo para el reviewer (RM3):** `mutacion.py:1781` salió MUERTO en la 1ª
campaña y SUPERVIVIENTE en la 2ª **sin que su código cambiara**: su muerte fue
falsa, hay algún test inestable en la suite de la raíz bajo carga.

**La campaña paralela no sirve aquí:** con `--workers 5` la línea base aborta en
el worktree (falla `test_f012_r1_r4_el_informe_paralelo_...`). Es anterior a
esta feature, y la línea base hizo lo que debía: abortar en vez de contar
muertos falsos.

## `bash harness/init.sh` (T14) — verde, exit code 0

```
[OK] pytest en verde (con medición de cobertura)   389 passed in 67.17s
[OK] PUERTA COBERTURA: 95.9% de 171 líneas cambiadas cubiertas (164/171, umbral 80%, nivel estandar)
[OK] PUERTA TAMAÑO: F-038 dentro de los topes (requirements 119/120, design 162/200)
[OK] PUERTA RUTAS SENSIBLES [evals]: N/A (F-038 no toca ninguna ruta sensible declarada)
     niveles: critico, documental, estandar; por defecto estandar; umbral 80%
ENTORNO LISTO. Puedes trabajar.
```

Los 8 servicios en verde (6 por caché; sv1 sin tests e `infra` sin comando, como
antes). Con este informe escrito, PUERTA TAMAÑO añade `impl 150/150`.

## Evidencias

| Evidencia | Valor real |
|---|---|
| Tests ejecutados (raíz) | **389 passed, 0 failed** (305 antes de F-038) |
| Cobertura de lo cambiado | **95,9 %** (164/171, umbral 80 %) |
| Mutantes generados/evaluados/supervivientes | **55 / 20 / 1** (semilla `20260820`) |
| Tiempo de la suite | **67,17 s** con cobertura; **52,1 s** la línea base |

## Qué queda fuera

- **F-039** (remedir F-012), qué hacer con `mutacion_F-011.md` y el **porte a `arnes-base` 1.7.0** (P1) tras el merge. **Verificaciones MANUAL pendientes: 0.**
