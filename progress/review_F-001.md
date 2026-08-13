<!-- progress/review_F-001.md -->
# F-001 · Informe de review — Test de estructura del monorepo

- Rama revisada: `feature/F-001-test-estructura` (HEAD `564df13`, base común con
  `dev`: `42139da`).
- Modo: `sdd=false` — la mini-spec son los `acceptance` de
  `harness/features.json`; no hay `specs/F-001-*/` ni `tasks.md`.
- Fecha de la review: 2026-08-13.

## Veredicto

**APPROVED**

## Nivel de rigor

Declarado en `harness/features.json`: **`estandar`**. Según
`harness/rigor.json`, ese nivel exige `fase_red: true`, `cobertura: true`,
`mutacion: true` y `supervivientes_maximos: null` (los supervivientes se
documentan y el reviewer juzga; no se exige cero). No se aplica el nivel por
omisión: la feature lo declara explícitamente.

## Qué he ejecutado yo (evidencia de primera mano)

No doy por bueno nada del informe del implementer que no haya reproducido.

| Comprobación | Comando | Resultado real |
|---|---|---|
| Portero del arnés | `bash harness/init.sh` (tal cual, sin pipes) | `ENTORNO LISTO. Puedes trabajar.` — **exit code 0** |
| Suite de la raíz | `.venv/Scripts/python.exe -m pytest tests/ -v -p no:cacheprovider` | **4 passed in 0.02s**, exit 0 |
| Alcance de mutación | `harness.alcance.alcance_de_feature("F-001")` | `0 fichero(s), 0 línea(s) de producción (origen rama, 42139da..feature/F-001-test-estructura)` |
| Generador de mutantes (control) | `harness.mutacion.generar_mutantes` sobre `tests/test_estructura_monorepo.py` | **14 mutantes generables** si el fichero no estuviera excluido |
| Fase RED reproducida | copia del test en un árbol roto del scratchpad | **2 failed, 2 passed**, con los mismos mensajes del informe |
| Diff de la rama | `git diff --name-status dev...HEAD` | 1 fichero de código (`tests/test_estructura_monorepo.py`) + 3 de `progress/` |
| Árbol limpio | `git status --porcelain -uall` | 0 ficheros sin trackear; solo `harness/features.json` modificado (marca de estado del líder) |

## C1 — El arnés está completo y en verde

- [x] `bash harness/init.sh` termina con **exit code 0**. Ejecutado por mí,
      sin pipes ni decoración. Puertas relevantes de su salida:
      `[OK] features.json válido`, `[OK] harness/rigor.json y niveles
      declarados: válidos`, `[OK] compileall: sin errores de sintaxis`,
      `[OK] pytest en verde` (23 passed, 3 skipped en la raíz),
      `[OK] servicio comun: pytest en verde` (19 passed, 3 skipped),
      `[OK] PUERTA COBERTURA: N/A (F-001 no cambia líneas Python de producción
      frente a dev)`, `[OK] Rama actual: feature/F-001-test-estructura`.
      Los `[AVISO]` (ruff/coverage no instalados, servicios sin directorio de
      tests, `infra` sin `comando_tests`) no tumban el portero y no son de esta
      feature.
- [x] Existen `CLAUDE.md`, `harness/features.json`, `specs/SPECS.md`,
      `progress/current.md`, `progress/history.md`, `docs/ARCHITECTURE.md`,
      `docs/CONVENTIONS.md` — verificado uno a uno por el propio `init.sh`.

## C2 — El estado es coherente

- [x] Una sola feature `in_progress`: `11 features, 11 abiertas, en curso:
      ['F-001'], bloqueadas: ninguna`.
- [x] La rama actual es `feature/F-001-test-estructura`, la declarada para
      F-001 en `features.json`. No es `main` ni `dev`.
- [x] `progress/current.md` describe **solo** la sesión de F-001 (bloque de
      cabecera + estado del implementer). Sin restos de sesiones anteriores.
- [x] Ninguna feature está `done` todavía, así que `progress/history.md` en
      plantilla es lo correcto. (Es el líder quien escribirá ahí el resumen de
      F-001 al cerrar; no es trabajo del implementer y no bloquea esta review.)

## C3 — El código respeta arquitectura y convenciones

- [x] Arquitectura hexagonal: la feature **no añade código de producción**.
      `tests/test_estructura_monorepo.py` no importa nada del repositorio (ni
      dominio, ni aplicación, ni infraestructura): solo `ast`, `json` y
      `pathlib`. No hay capa que violar. No aplica ninguna de las tres trampas
      del monorepo (tablas merge, lectores de un cambio de schema, unidades e
      importes): la feature no toca schema, ni SQL, ni importes.
- [x] Primera línea del fichero: `# tests/test_estructura_monorepo.py`, la
      ruta relativa exacta. Además, el propio R1 lo convierte en test.
- [x] Barrido hecho por mí sobre el fichero
      (`print\(|password|secret|token|api_key|connection_string|AccountKey|TODO`):
      **sin coincidencias**. Sin `print()` de debug, sin TODOs, sin secretos.
- [x] Sin dependencias nuevas: `MODULOS_PERMITIDOS` es
      `{__future__, ast, json, pathlib}`, todo biblioteca estándar. No se
      añade nada a ningún `requirements`.
- [x] Convenciones de Ruesma: todo en español (docstrings, mensajes de
      aserción, comentarios) y mensajes de commit en español.
- [x] Python 3.12 con type hints en todas las firmas públicas
      (`-> list[dict]`, `-> bool`, `-> set[str]`, `-> None`).

## C3 bis — Documentos que entran de fuera

**N/A, justificado:** el diff `dev...HEAD` no añade ni modifica ningún fichero
bajo `docs/referencia/` (los cuatro ficheros tocados son
`tests/test_estructura_monorepo.py`, `progress/current.md`,
`progress/impl_F-001.md` y `progress/mutacion_F-001.md`). No hay PDF ni
ofimática en el diff ni en el árbol de trabajo. Este bloque solo aplica a
features que tocan `docs/referencia/`, y esta no lo hace.

## C4 — La verificación es real

- [x] Cada criterio `acceptance` tiene al menos un test trazable con nombre
      `test_f001_rN_*`, y todos pasan (ver tabla de cobertura abajo).
- [x] Los unit tests no tocan red ni BBDD. No es una promesa: R4 lo
      **verifica leyendo el AST** del propio fichero y comparando los imports
      contra una lista blanca de stdlib. Lo he comprobado en el árbol roto:
      añadiendo `import socket`, R4 falla.
- [x] Verificaciones `MANUAL (humano)`: **ninguna**, y así consta en
      `progress/current.md` y en el informe del implementer. Correcto: la
      feature no toca Azure, ni BBDD, ni producción; todos sus criterios son
      automáticos.

### Cobertura: criterio `acceptance` → test que lo cubre

| # | Criterio `acceptance` | Test | Estado |
|---|---|---|---|
| R1 | Existe `tests/test_estructura_monorepo.py` con primera línea de comentario de ruta | `test_f001_r1_el_fichero_declara_su_ruta_en_la_primera_linea` | PASSED |
| R2 | Cada `ruta` de `harness/servicios.json` existe como directorio | `test_f001_r2_cada_ruta_declarada_existe_como_directorio` | PASSED |
| R3 | Cada servicio `python` declarado trae `pyproject.toml` o `main.py` | `test_f001_r3_cada_servicio_python_trae_pyproject_o_main` | PASSED |
| R4 | El test pasa sin red ni BBDD (solo filesystem y json de la stdlib) | `test_f001_r4_el_test_solo_importa_biblioteca_estandar` | PASSED |
| R5 | `bash harness/init.sh` en verde | Sin test automatizado — ver justificación | Verificado a mano: exit 0 |

**R5 sin test automatizado: aceptado.** Un test que ejecutara `init.sh` se
invocaría a sí mismo a través de la sección 7 del portero (recursión, y minutos
de suite por ejecución). La verificación válida de R5 es ejecutar el portero, y
la he ejecutado yo: exit code 0, `ENTORNO LISTO`. El implementer lo justificó
por escrito en su informe, que es lo que exige la regla del N/A.

**Los tests no pasan en vacío.** Lo he comprobado aparte, porque un test que
itera sobre una declaración externa puede salir verde sin mirar nada: los 8
servicios de `harness/servicios.json` existen como directorio, los 7 declarados
`python` traen `main.py` (o `pyproject.toml` en `comun`), e `infra` está
declarado `otro` y por eso R3 lo salta correctamente. Además,
`cargar_servicios` aborta si el fichero no existe o la lista está vacía, que es
justo el guard contra el verde mentiroso.

## C4 bis — El rigor declarado se cumple

- [x] La feature declara `rigor: "estandar"` en `harness/features.json`, valor
      válido según `harness/rigor.json`. No se aplica el nivel por omisión.
- [x] **Fase RED.** El informe trae **dos trazas reales de fallo**, no una
      frase. Y no me he fiado: he reconstruido el árbol roto A en el scratchpad
      (con `servicios.json` declarando `sv-fantasma -> services/no-existe-esta-ruta`
      y `sv-sin-manifiesto`) y he obtenido el mismo resultado que el informe:
      `2 failed, 2 passed`, con los mensajes
      `harness/servicios.json declara rutas que no existen como directorio…` y
      `Servicios declarados como python sin ninguno de ['pyproject.toml', 'main.py']…`.
      La evidencia RED es auténtica.

      Nota sobre la forma de esta RED: la feature *es* un test, así que no hay
      código de producción cuyo fallo previo enseñar. La demostración
      equivalente —y de hecho más exigente— es que los tests fallan cuando lo
      que vigilan se rompe. Entre los dos árboles rotos, los cuatro tests se
      han visto fallar por su motivo propio. Lo acepto como fase RED cumplida.
- [x] **Cobertura: N/A con el motivo impreso por la herramienta.** `init.sh`
      imprime `[OK] PUERTA COBERTURA: N/A (F-001 no cambia líneas Python de
      producción frente a dev)`. El motivo no es «no está instalado coverage»
      (que también, y consta como AVISO aparte): es que el alcance de la
      feature es vacío, cosa que he recalculado yo. La regla del N/A queda
      satisfecha: hay motivo, es de la herramienta, y es verificable.
- [x] **Mutación: totales verificados de forma independiente.** Existe
      `progress/mutacion_F-001.md` con formato de la herramienta y totales
      0/0/0/0/0. Recalculado por mí con cálculo puro (sin ejecutar la suite):
      - `alcance_de_feature("F-001")` →
        `0 fichero(s), 0 línea(s) de producción (origen rama,
        42139da..feature/F-001-test-estructura)`, idénticas refs y origen que el
        informe.
      - El diff crudo trae 4 ficheros (427 líneas) y `es_produccion` devuelve
        `False` para los cuatro: `tests/` y `progress/` están en
        `DIRECTORIOS_EXCLUIDOS` de `harness/alcance.py`. De ahí el 0.
      - **Control contra el informe escrito a mano:** he pedido al generador
        mutantes sobre `tests/test_estructura_monorepo.py` ignorando la
        exclusión y devuelve **14** (por ejemplo `parents[1]` → `parents[2]`,
        `== "python"` → `!= "python"`, `or` → `and`). Es decir: el generador
        funciona y el 0 del informe viene de la exclusión de alcance, no de una
        herramienta muda ni de un informe inventado.
- [x] **Supervivientes: ninguno, y con explicación.** No hay ninguna sección en
      `PENDIENTE`. El informe del implementer no se limita a apuntar el cero:
      explica que no hubo mutantes que matar porque el alcance es vacío, que es
      exactamente la lectura honesta. `estandar` no exige cero supervivientes,
      así que no hace falta justificación aceptada por el humano.
- [x] **Sección «Evidencias» con los cuatro números.** Presente en
      `progress/impl_F-001.md`: tests (4 passed / 23 passed, 3 skipped en la
      raíz / 19 passed, 3 skipped en `comun`), cobertura de lo cambiado (N/A con
      motivo), mutantes y supervivientes (0 y 0), tiempo de la suite (0,02 s el
      fichero; ~97 s la raíz bajo `init.sh`; ~3 min 20 s el portero completo).
- [x] Ningún punto de este bloque marcado N/A sin justificación escrita.

## C5 — La sesión se cerró bien

- **`tasks.md`: N/A, justificado.** F-001 es `sdd=false`: no tiene
  `specs/F-001-*/` y por tanto no hay `tasks.md` que recorrer, tal como
  contempla la nota de cabecera de `CHECKPOINTS.md`. En su lugar valido el
  formato mínimo de commit para features sin spec, `F-XXX: <descripción>`, y se
  cumple en los dos commits de la rama:
  - `8dd31e1 F-001: test de estructura del monorepo (servicios.json contra el arbol real)`
  - `564df13 F-001: informe de implementacion, campana de mutacion y estado de la sesion`
- [x] Sin ficheros temporales ni artefactos sin trackear:
  `git status --porcelain -uall` devuelve **0 entradas `??`**. Los dos árboles
  rotos de la fase RED viven en el scratchpad de sesión, fuera del repositorio
  (lo he confirmado: no aparecen en el árbol de trabajo). Los míos, igual.
- [x] `features.json` refleja el estado real: F-001 en `in_progress`. El cambio
  `pending → in_progress` está en el working tree sin commitear; es la marca de
  estado del líder, no un artefacto del implementer, y le corresponde a él
  consolidarla al cerrar. No bloquea.

## Cambios requeridos

**Ninguno.** La feature se aprueba tal cual.

## Observaciones para el líder (no bloquean el cierre)

Confirmo los dos hallazgos del implementer, que están bien vistos y bien
dejados fuera del alcance de F-001:

1. **La suite de `comun` se ejecuta dos veces en cada `init.sh`.** Al crear
   `tests/` en la raíz se activa la sección 7 del portero, que lanza `pytest`
   sin argumento de ruta; sin `testpaths`, la recolección arrastra
   `services/albaranes-comun/tests/`. Lo he medido en mi propia ejecución: la
   suite «de la raíz» reporta **23 passed, 3 skipped en 106 s** cuando los
   tests de la raíz son 4 y tardan 0,02 s. Luego la sección 7 bis los repite
   con el venv del servicio (19 passed, 3 skipped). Son ~100 s de peaje por
   cada ejecución del portero, y encima los tests de `comun` corren con un
   intérprete que no es el suyo. Arreglo: `testpaths = tests` en un
   `pyproject.toml`/`pytest.ini` de raíz, o pasar `tests` como argumento en la
   sección 7 de `init.sh`. Lo segundo es mejora del arnés genérico y tocaría
   propagarla a `arnes-base`.
2. **`coverage` y `ruff` no están instalados en el venv de la raíz.** Hoy no
   bloquean —el N/A de cobertura viene del alcance vacío, no de la
   herramienta—, pero la primera feature que toque código de producción se
   encontrará la puerta de cobertura sin nada con que medir, y ahí sí sería un
   N/A **no** justificable. Conviene instalarlos antes de F-011/F-002.

## Automejora del protocolo (propuesta, no aplicada)

Para que lo valore el humano:

1. **`CHECKPOINTS.md` § C4 bis, punto de fase RED.** El texto asume que
   siempre hay código de producción cuyo fallo previo se enseña. En una
   feature cuyo entregable *es* un test (como F-001) eso es imposible por
   construcción, y el implementer tuvo que inventarse la forma equivalente:
   romper el entorno observado y enseñar que el test lo caza. Propongo añadir
   una frase al checkpoint: *«Si el entregable de la feature es el propio test,
   la fase RED se demuestra rompiendo deliberadamente lo que el test vigila y
   pegando la traza del fallo»*. Hoy funciona porque el implementer razonó
   bien; escrito, deja de depender de eso.
2. **`.claude/agents/reviewer.md`, verificación de la mutación.** El protocolo
   manda recalcular alcance y número de mutantes, pero cuando el resultado es
   **0 mutantes** ese recálculo no distingue entre «no había nada que mutar» y
   «el generador está roto o el informe es falso»: ambos casos dan 0. Propongo
   añadir la prueba de control que he hecho aquí: *«Si la campaña declara cero
   mutantes, ejecuta `generar_mutantes` sobre los ficheros del diff ignorando
   la exclusión de alcance; si tampoco ahí sale ninguno, el cero es
   sospechoso»*. Es barato (cálculo puro) y es la diferencia entre creerse un
   cero y comprobarlo.

Ambas mejoras son genéricas del arnés: si se aprueban, van a `arnes-base` por
la regla de propagación.
