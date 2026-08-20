<!-- specs/F-034-mutacion-is-y-coherencia-evals/tasks.md -->
# F-034 · Tareas

Rama: `feature/F-034-mutacion-is-y-coherencia-evals` (desde `dev`).
Un commit por tarea: `F-034 Tn: descripción`. Sin `push` ni PR.

> **Antes de T5 y T6**: árbol limpio, ninguna otra suite ni campaña corriendo
> en la máquina. Esas dos tareas **mutan ficheros del árbol de trabajo** y en
> Windows el paralelismo tumba el portero (`0xC0000142`).

---

- [x] **T0: Recoger la decisión D1 del humano** (§3 de `requirements.md`:
      ¿se remide el histórico? A / B / C) y la D2 (1.5.3 vs **1.6.0**) y D3
      (corregir la descripción en `features.json`). Anotar la respuesta literal
      en `progress/impl_F-034.md`.
      **Verificación**: MANUAL (humano). Sin respuesta, T7 no se hace y T10 usa
      la versión que el humano diga; el resto de tareas no dependen de D1.

- [x] **T1: Medición de partida (el «antes»)**. Con el mutador **sin tocar**,
      cálculo puro sobre los alcances históricos de F-019 y F-027, y pegar los
      totales en `progress/impl_F-034.md`.
      **Verificación**: `python -c` con `harness.alcance.alcance_de_feature` +
      `harness.mutacion.generar_mutantes` (sin ejecutar suite) imprime
      **31** mutantes para F-019 y **0** para F-027, con las referencias fijadas
      de `design.md` §6.

- [x] **T2: Tests en RED**. Crear `tests/test_mutacion_operadores.py` con los
      nueve casos de `design.md` §5 y pegar en `progress/impl_F-034.md` la
      **salida real** del fallo.
      **Verificación**: `python -m pytest tests/test_mutacion_operadores.py -q`
      falla en R1, R2, R3, R4, R5, R8 y R14, y **pasa** en R6 y R7 (que fijan
      comportamiento actual que no debe cambiar).

- [x] **T3: `ast.Is` / `ast.IsNot` en `COMPARACIONES`** (`harness/mutacion.py`),
      con el comentario que declara la limitación de R7.
      **Verificación**: los tests de R1, R2, R3, R4, R7 y R8 pasan;
      `python -m pytest tests -q` (raíz) en verde.

- [x] **T4: Delimitador de palabra en `_localizar`** (`_PARTE_DE_PALABRA`,
      `_es_palabra`, `_delimitado` y búsqueda de la primera coincidencia
      **válida**), aplicado solo a tokens alfabéticos.
      **Verificación**: `python -m pytest tests/test_mutacion_operadores.py -q`
      entero en verde (R5 y R6 incluidos) y `python -m pytest tests -q` en verde
      (no regresión de `not`, `and`, `or`, booleanos y enteros).

- [x] **T5: Campaña real sobre F-027** (la prueba de que el mutante nuevo cae en
      una guarda de verdad y **muere**), con el comando exacto de `design.md`
      §6 y salida a `progress/mutacion_F-027_remedida.md`.
      **Verificación**: el informe declara **1 mutante generado, 1 muerto, 0
      supervivientes**, y el mutante es
      `valuation_builder.py:1033 … is not None` → `is None`. Si sobrevive:
      **PARAR** y aplicar R11 (test nuevo o justificación escrita); no se sigue
      con T6 hasta cerrarlo.

- [x] **T6: Campaña real sobre F-019** (`cp` del informe histórico al nombre de
      salida **antes** de lanzarla, para que se repongan los análisis ya
      escritos), con el comando exacto de `design.md` §6.
      **Verificación**: `progress/mutacion_F-019_remedida.md` declara **49
      generados** (31 + 18 nuevos), **46 muertos** y **los 3 supervivientes
      conocidos** con su análisis repuesto. Cualquier superviviente nuevo:
      R11 (test que lo mate o análisis escrito) antes de continuar.

- [x] **T7 (solo si D1 = opción B o C): re-medición oficial**. Añadir a mano un
      puntero de UNA línea al principio de `progress/mutacion_F-019.md` y
      `progress/mutacion_F-027.md` («re-medida con el arnés X.Y.Z: ver
      `progress/mutacion_F-0XX_remedida.md`»), y las campañas extra que el
      humano haya pedido en la opción C.
      **Verificación**: `git diff` de los dos informes históricos = exactamente
      una línea añadida en cada uno; nada más se toca de ellos.

- [x] **T8: Coherencia de la puerta de evals**. `CHECKPOINTS.md` línea 185,
      `harness/rutas_sensibles.json` clave `_exigencia`, y `progress/current.md`
      líneas 33 y 64: la condición pasa a los fixtures versionados de
      `evals/fixtures/`, con la aclaración de que los libros `.xlsx` de
      `evals/ground_truth/` existen pero no se versionan.
      **Verificación**: `python -m pytest tests/test_mutacion_operadores.py -q`
      (test de R14) en verde; `python -m harness.rutas_sensibles --validar` sin
      error; y `grep -rn "ground_truth" CHECKPOINTS.md harness/rutas_sensibles.json progress/current.md`
      no devuelve ninguna línea que condicione la puerta a esa ruta.

- [x] **T9: Rastro de la campaña manual**. Punto nuevo en C4 bis de
      `CHECKPOINTS.md` (R16) y la frase equivalente en el punto 4 de
      `.claude/agents/reviewer.md` (R17).
      **Verificación**: revisión del reviewer; el punto exige fichero, línea,
      **texto exacto original → mutado** y resultado con nº de fallos.

- [x] **T10: Versión del arnés**. `harness/VERSION` y `harness/ARNES_VERSION.md`
      a la versión de D2 (recomendada: **1.6.0**), con fecha.
      **Verificación**: `bash harness/init.sh` imprime `Arnés v1.6.0` en su
      primera comprobación.

- [x] **T11: Puertas propias de la feature** (nivel `estandar`): cobertura de
      las líneas cambiadas y **campaña de mutación de F-034**, con los
      supervivientes analizados.
      **Verificación**: `python -m harness.mutacion --feature F-034 --workers 1`
      → `progress/mutacion_F-034.md` sin ningún análisis en `PENDIENTE`; línea
      `PUERTA COBERTURA` de `init.sh` en `[OK]`.

- [x] **T12: Porte a `arnes-base`** (repositorio
      `C:\Users\pgris\PycharmProjects\arnes-base`, commit propio allí, sin
      `push`): `harness/mutacion.py`, `tests/test_mutacion_operadores.py`, el
      punto nuevo de C4 bis en `CHECKPOINTS.md`, la frase de
      `.claude/agents/reviewer.md`, `harness/VERSION` y la sección nueva de
      `GUIA_INSTALACION.md` con el aviso de R20 (los informes de mutación
      anteriores dejan de ser comparables; una campaña verde puede pasar a
      roja).
      **Verificación**: en `arnes-base`,
      `diff <(tr -d '\r' < arnes-base/harness/mutacion.py) <(tr -d '\r' < ../albaranes/harness/mutacion.py)`
      vacío, ídem para el test; `python -m pytest arnes-base/tests -q` en verde;
      `git -C ../arnes-base log --oneline -1` muestra el commit de la versión.

      **CÓMO SE RESOLVIÓ** (estaba `[~]` BLOQUEADO; ver `progress/impl_F-034.md`
      §T12 para el bloqueo original y §T15 para el desenlace). El bloqueo era
      real: había otro trabajo en vuelo y sin commitear sobre el mismo
      `harness/mutacion.py` de `arnes-base`. Lo resolvió el **humano**, no el
      implementer, decidiendo incorporar los dos encargos a la **misma versión**:
      la **1.6.0 de `arnes-base`** lleva las cuatro piezas del encargo de
      «mutación fiable» **y** el porte de `is`/`is not` de F-034. Commits allí,
      ya **pusheados** a `origin/main` (verificado con
      `git -C C:/Users/pgris/PycharmProjects/arnes-base log --oneline` y
      `git branch -r --contains 89a9ba9`):

      | Commit | Qué trae |
      |---|---|
      | `860902e` | 1.6.0 (1/4): la campaña de mutación deja de poder contar muertos falsos |
      | `b7dce9d` | 1.6.0 (2/4): la prueba de verdad, y dos defectos más que ha destapado |
      | `febb51d` | 1.6.0 (3/4): **el mutador muta `is` / `is not` (porte de F-034)** |
      | `3ceb95b` | 1.6.0 (4/4): entrega — `VERSION`, entrada en la guía y el §5 ampliado |
      | `89a9ba9` | 1.6.0: `ruff` ordena los imports de los tres tests de mutación |

      Comprobado en `arnes-base` (solo lectura, hay otro agente trabajando ahí):
      `arnes-base/harness/VERSION` → `ARNES_VERSION=1.6.0`, y
      `grep -c "ast.Is" arnes-base/harness/mutacion.py` → **2** (las dos entradas
      de `COMPARACIONES` que añade F-034). El porte está dentro.

      **Desviación aceptada respecto a la letra de T12**: `mutacion.py` **no**
      viaja byte a byte, porque en `arnes-base` convive con el encargo de línea
      base, y `test_mutacion_operadores.py` tampoco (allí el test de R14 se
      generalizó, porque `evals/fixtures/` es de `albaranes`). El reviewer ya
      verificó ambas cosas y las calificó de «adaptación correcta y mejor que la
      copia literal». Lo que R18–R21 exigen —que el mutador de `arnes-base` mute
      `is`/`is not`, en su versión, con su aviso en la guía— está cumplido.

      **La propagación de vuelta a `albaranes` NO forma parte de esta tarea.**
      Se intentó en el commit `e97f9b9` y **se ha revertido** (`163846b`) porque
      metía ~1.000 líneas de producción ajenas en el alcance de F-034 después de
      medir las puertas. Se rehará tras el merge de F-034, en su propia rama
      `chore/`. Ver la nota de §T15 del informe.

- [x] **T13: Cierre documental**. `progress/impl_F-034.md` con la sección
      **Evidencias** (tests y resultado, cobertura, mutantes/supervivientes,
      tiempo de la suite), la fase RED de T2, el antes/después de T1 vs T5/T6 y
      la corrección del enunciado de `requirements.md` §1; `progress/current.md`
      al día; `harness/features.json` con F-034 en `done` (y la frase corregida
      si D3 = sí); `BACKLOG.md` regenerado por `init.sh`.
      **Verificación**: `bash harness/init.sh` no avisa de `BACKLOG.md`
      desactualizado; `git status` limpio salvo lo commiteado.

- [x] **T14: Ejecutar `bash harness/init.sh` en verde** (incluye suites y
      puertas), en serie y sin nadie más trabajando en el árbol.
      **Verificación**: salida final sin `[FALLO]`.
