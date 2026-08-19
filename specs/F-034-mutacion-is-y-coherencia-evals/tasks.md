<!-- specs/F-034-mutacion-is-y-coherencia-evals/tasks.md -->
# F-034 · Tareas

Rama: `feature/F-034-mutacion-is-y-coherencia-evals` (desde `dev`).
Un commit por tarea: `F-034 Tn: descripción`. Sin `push` ni PR.

> **Antes de T5 y T6**: árbol limpio, ninguna otra suite ni campaña corriendo
> en la máquina. Esas dos tareas **mutan ficheros del árbol de trabajo** y en
> Windows el paralelismo tumba el portero (`0xC0000142`).

---

- [ ] **T0: Recoger la decisión D1 del humano** (§3 de `requirements.md`:
      ¿se remide el histórico? A / B / C) y la D2 (1.5.3 vs **1.6.0**) y D3
      (corregir la descripción en `features.json`). Anotar la respuesta literal
      en `progress/impl_F-034.md`.
      **Verificación**: MANUAL (humano). Sin respuesta, T7 no se hace y T10 usa
      la versión que el humano diga; el resto de tareas no dependen de D1.

- [ ] **T1: Medición de partida (el «antes»)**. Con el mutador **sin tocar**,
      cálculo puro sobre los alcances históricos de F-019 y F-027, y pegar los
      totales en `progress/impl_F-034.md`.
      **Verificación**: `python -c` con `harness.alcance.alcance_de_feature` +
      `harness.mutacion.generar_mutantes` (sin ejecutar suite) imprime
      **31** mutantes para F-019 y **0** para F-027, con las referencias fijadas
      de `design.md` §6.

- [ ] **T2: Tests en RED**. Crear `tests/test_mutacion_operadores.py` con los
      nueve casos de `design.md` §5 y pegar en `progress/impl_F-034.md` la
      **salida real** del fallo.
      **Verificación**: `python -m pytest tests/test_mutacion_operadores.py -q`
      falla en R1, R2, R3, R4, R5, R8 y R14, y **pasa** en R6 y R7 (que fijan
      comportamiento actual que no debe cambiar).

- [ ] **T3: `ast.Is` / `ast.IsNot` en `COMPARACIONES`** (`harness/mutacion.py`),
      con el comentario que declara la limitación de R7.
      **Verificación**: los tests de R1, R2, R3, R4, R7 y R8 pasan;
      `python -m pytest tests -q` (raíz) en verde.

- [ ] **T4: Delimitador de palabra en `_localizar`** (`_PARTE_DE_PALABRA`,
      `_es_palabra`, `_delimitado` y búsqueda de la primera coincidencia
      **válida**), aplicado solo a tokens alfabéticos.
      **Verificación**: `python -m pytest tests/test_mutacion_operadores.py -q`
      entero en verde (R5 y R6 incluidos) y `python -m pytest tests -q` en verde
      (no regresión de `not`, `and`, `or`, booleanos y enteros).

- [ ] **T5: Campaña real sobre F-027** (la prueba de que el mutante nuevo cae en
      una guarda de verdad y **muere**), con el comando exacto de `design.md`
      §6 y salida a `progress/mutacion_F-027_remedida.md`.
      **Verificación**: el informe declara **1 mutante generado, 1 muerto, 0
      supervivientes**, y el mutante es
      `valuation_builder.py:1033 … is not None` → `is None`. Si sobrevive:
      **PARAR** y aplicar R11 (test nuevo o justificación escrita); no se sigue
      con T6 hasta cerrarlo.

- [ ] **T6: Campaña real sobre F-019** (`cp` del informe histórico al nombre de
      salida **antes** de lanzarla, para que se repongan los análisis ya
      escritos), con el comando exacto de `design.md` §6.
      **Verificación**: `progress/mutacion_F-019_remedida.md` declara **49
      generados** (31 + 18 nuevos), **46 muertos** y **los 3 supervivientes
      conocidos** con su análisis repuesto. Cualquier superviviente nuevo:
      R11 (test que lo mate o análisis escrito) antes de continuar.

- [ ] **T7 (solo si D1 = opción B o C): re-medición oficial**. Añadir a mano un
      puntero de UNA línea al principio de `progress/mutacion_F-019.md` y
      `progress/mutacion_F-027.md` («re-medida con el arnés X.Y.Z: ver
      `progress/mutacion_F-0XX_remedida.md`»), y las campañas extra que el
      humano haya pedido en la opción C.
      **Verificación**: `git diff` de los dos informes históricos = exactamente
      una línea añadida en cada uno; nada más se toca de ellos.

- [ ] **T8: Coherencia de la puerta de evals**. `CHECKPOINTS.md` línea 185,
      `harness/rutas_sensibles.json` clave `_exigencia`, y `progress/current.md`
      líneas 33 y 64: la condición pasa a los fixtures versionados de
      `evals/fixtures/`, con la aclaración de que los libros `.xlsx` de
      `evals/ground_truth/` existen pero no se versionan.
      **Verificación**: `python -m pytest tests/test_mutacion_operadores.py -q`
      (test de R14) en verde; `python -m harness.rutas_sensibles --validar` sin
      error; y `grep -rn "ground_truth" CHECKPOINTS.md harness/rutas_sensibles.json progress/current.md`
      no devuelve ninguna línea que condicione la puerta a esa ruta.

- [ ] **T9: Rastro de la campaña manual**. Punto nuevo en C4 bis de
      `CHECKPOINTS.md` (R16) y la frase equivalente en el punto 4 de
      `.claude/agents/reviewer.md` (R17).
      **Verificación**: revisión del reviewer; el punto exige fichero, línea,
      **texto exacto original → mutado** y resultado con nº de fallos.

- [ ] **T10: Versión del arnés**. `harness/VERSION` y `harness/ARNES_VERSION.md`
      a la versión de D2 (recomendada: **1.6.0**), con fecha.
      **Verificación**: `bash harness/init.sh` imprime `Arnés v1.6.0` en su
      primera comprobación.

- [ ] **T11: Puertas propias de la feature** (nivel `estandar`): cobertura de
      las líneas cambiadas y **campaña de mutación de F-034**, con los
      supervivientes analizados.
      **Verificación**: `python -m harness.mutacion --feature F-034 --workers 1`
      → `progress/mutacion_F-034.md` sin ningún análisis en `PENDIENTE`; línea
      `PUERTA COBERTURA` de `init.sh` en `[OK]`.

- [ ] **T12: Porte a `arnes-base`** (repositorio
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

- [ ] **T13: Cierre documental**. `progress/impl_F-034.md` con la sección
      **Evidencias** (tests y resultado, cobertura, mutantes/supervivientes,
      tiempo de la suite), la fase RED de T2, el antes/después de T1 vs T5/T6 y
      la corrección del enunciado de `requirements.md` §1; `progress/current.md`
      al día; `harness/features.json` con F-034 en `done` (y la frase corregida
      si D3 = sí); `BACKLOG.md` regenerado por `init.sh`.
      **Verificación**: `bash harness/init.sh` no avisa de `BACKLOG.md`
      desactualizado; `git status` limpio salvo lo commiteado.

- [ ] **T14: Ejecutar `bash harness/init.sh` en verde** (incluye suites y
      puertas), en serie y sin nadie más trabajando en el árbol.
      **Verificación**: salida final sin `[FALLO]`.
