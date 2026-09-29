<!-- progress/review_F-048_bloque_E.md -->
Revisión incremental desde 18dacf8 (review final) hasta 665bd0a: runner, comparador de obra y bloque E (T29–T31)

# F-048 · Review de evals/ desde la review final: runner, comparador y bloque E

- **Veredicto: CHANGES_REQUESTED**
- **Rigor:** `critico` (declarado en `harness/features.json`). Exige fase RED, cobertura ≥ 80 %, mutación
  completa con RM1–RM6 y RM5 (muestra de un equivalente).
- **Alcance mirado:** `git diff 18dacf8..HEAD -- evals/ tests/` (9 ficheros de `evals/`, 6 de `tests/`) y los informes
  `impl_F-048_evals.md`, `impl_F-048_bloque_E.md`, `analisis_evals_F-048.md` y `comparar_obra_F-048.md`.
  Nada contra LLM, Azurite ni Azure. No he leído ningún `.env`.
- **`bash harness/init.sh`:** ENTORNO LISTO, exit 0. `995 passed in 694.40s`. `PUERTA COBERTURA` 97.0 %
  (1313/1354). Rutas sensibles en AVISO: falta `VEREDICTO: VERDE` en `progress/evals_F-048.md` (T40, pendiente).
- Las pruebas se hicieron en un worktree separado dentro del scratchpad, que ya he quitado. `git status` sigue limpio.

## Lo que se comprobó (resumen)

| Comprobación | Resultado |
|---|---|
| RED del runner: `runner.py` y los tres hijos vueltos a `18dacf8` | `23 failed, 8 passed` (el informe da 20/5 sobre 25; con los 6 tests de bordes cuadra) |
| RED del comparador: `modelo_sin_campo` devuelve el modelo sin recortarlo | `2 failed, 2 passed`, idéntico al informe |
| RED del bloque E: M3 (`correo_blob=None` en el mensaje) y sin `evals/correos.py` | `1 failed, 12 passed` e `ImportError: cannot import name 'correos'`, igual que el informe |
| Test de `git archive` (variante `dev` = `dev`) | 4 passed. También pasa **sin `sort_keys`**: el schema es idéntico byte a byte, incluido el orden |
| ¿Cambian dev..HEAD los clientes LLM o el preproceso? | No: `infrastructure/llm/` sin cambios; `retry_policy` cambia, pero el comparador no la usa; `activas` sale igual de `SigridApiObrasClient` |
| T30: `git diff feature/F-047-evals-ciclo-completo 01c4b13 -- evals/inyeccion.py tests/test_f047_r2_r16_inyeccion.py` | 0 bytes |
| T31 frente a sv1 (`intake_cola_adapter.py:73-168`) | Misma puerta: huella en el payload, PDF → `guardar_contexto_correo` → publicar con `correo_blob`; si falla, no publica |
| R38 con un correo metido en la copia (`tests/…/correo.json` anidado + `evals/inputs/correos/GEN-001.json`, `git add -f`) | El test **cae** y los encuentra a los dos |
| Paradas del comparador (sin clave, sin sigrid, sin `dev`, sin obras, sin albarán) | Tests presentes y verdes; todas ocurren antes de `montar_extractor` |
| `progress/comparar_obra_F-048.md` y `analisis_evals_F-048.md` | Sin valores: solo caso_id, campo y recuentos |
| **Centinela en `describir_error`** | **FUGA**: ver bloqueante 1 |

## Bloqueantes

1. **`evals/procesos/errores.py:87`: la `loc` de pydantic cuela texto del LLM en el motivo que se versiona (R31 de F-047).**
   `include_input=False` quita `input_value`, pero no las claves. Con `extra='forbid'` (todo `StrictSchemaModel`
   de sv2) y en los campos `dict`, la `loc` lleva la clave **tal como la escribió el LLM**. Lo reproduje con el
   modelo real: `DocumentoAlbaran.model_validate_json('{"cabecera": {"Hormigones CENTINELA SL": "x"}, ...}')` da
   `ValidationError: extra_forbidden en cabecera.Hormigones CENTINELA SL`. Un modelo con `dict[str, int]` da
   `int_parsing en mapa.CENTINELA-VALOR-7731`. Ese motivo llega al informe de evals (`runner.py:355`) y al stderr.
   **Arreglo:** en `extra_forbidden`, quitar el último elemento de la `loc` («campo no previsto en cabecera»).
   En general, dejar los enteros y los nombres que encajen con `^[a-z_][a-z0-9_]*$`, y cambiar el resto por
   `<clave>`. Test con el centinela **en la clave**, no solo en el valor.
2. **Un caso con ERROR que sale como `OMITIDO` deja pasar la puerta de rutas sensibles con un fallo real dentro.**
   `ResultadoFase.veredicto` (`evals/modelos.py:168-174`) no cuenta los omitidos. Si 1 de 10 casos revienta
   porque IA2 devuelve JSON degenerado con el prompt nuevo, la fase sale VERDE, la pasada escribe
   `VEREDICTO: VERDE` y eso es justo la línea que exige `harness/rutas_sensibles.json:13`. Antes la pasada
   moría sin informe y la puerta seguía sin cumplirse. Ahora se cumple. Un LLM que produce una salida inválida
   con el prompt de la rama es un empeoramiento real, y ahora queda escondido.
   **Arreglo propuesto:** marcar el caso roto (un `error=True` en `ResultadoCaso`, o un estado `ERROR`) cuando
   el motivo nace de `_motivos_de_error`, `_motivo_sv5` con error, `_motivo_sv6` con error o `_ejecutar_aislado`
   (`runner.py:197-215, 305-389`). `ResultadoFase.veredicto` tiene que devolver como mínimo `NO_EVALUABLE`
   (código 2) si hay algún caso con error, y `ROJO` sigue mandando. `_explicacion_veredicto` lista «N casos
   con ERROR: …». Hacen falta tests de que un caso roto no puede dar `VEREDICTO: VERDE` y de que
   `sin caso en el libro` sigue sin afectar al veredicto.
3. **RM1: la campaña de mutación ya no mide lo que se revisa.** `progress/mutacion_F-048.md` midió
   `e7fe2c0` con 175 mutantes. `harness.alcance` cuenta `evals/` como producción, y al recalcular sobre HEAD
   (`generar_mutantes`, cálculo puro) salen **394**. Los 219 de `evals/` no se han evaluado nunca:
   `comparar_obra.py` 93, `inyeccion.py` 33, `sv2_obra.py` 29, `correos.py` 21, `errores.py` 21, `runner.py` 21,
   `sv2_extraccion.py` 1. Los 9 mutantes a mano del bloque E y las 2 roturas del comparador no sustituyen una
   campaña en `critico`. Antes de cerrar F-048 hay que relanzar
   `python -m harness.mutacion --feature F-048`, o que el humano excluya `evals/` del alcance **por escrito**.
   En la campaña, `GestoRevisor` (`inyeccion.py:324-401`, sin test en esta rama) dará supervivientes: hay que
   justificarlos como «código de F-047, su test llega con F-047».
4. **El cableado que falta no está anotado donde F-047 lo vaya a ver.** `anadir_opcion_sin_correo`
   (`inyeccion.py:130`), `correo=correos.cargar_correo(caso_id)` en `ciclo.py` y
   `tests/test_f047_r5_seleccion_contrato.py` solo aparecen en `impl_F-048_bloque_E.md`. No están ni en
   `progress/current.md` ni en `specs/F-047-evals-ciclo-completo/tasks.md`. Sin ese cableado, R41 («el ciclo
   admite…») se cumple solo a nivel de `Inyector`. Hay que anotarlo en los dos sitios para que no se pierda
   al integrar F-047.

## Menores (no bloquean)

1. `evals/correos.py:137-138`: la firma de R38 solo mira `.json` con `asunto` y `cuerpo`. Lo comprobé en la
   copia: un `.eml`, un volcado de Graph (`subject` + `uniqueBody`) o un dict en un `.py` pasan sin que salte.
   Conviene prohibir `.eml` y `.msg` bajo `evals/` y `tests/`, y añadir la firma de Graph.
2. `tests/test_f048_comparar_obra_prompt_dev.py:167-168`: quitar `sort_keys=True`. Sin él también pasa (lo
   comprobé), y así «byte a byte» es literal: a Gemini le importa el orden de las propiedades.
3. `evals/runner.py:316`: si un hijo muere, su stderr completo sale por consola. Es correcto que no vaya al
   informe, pero hay que avisar en `evals/README.md` de que esa salida no se redirige a `progress/`.
4. `correos.cargar_correo` duplica el formato de `leer_captura` de sv2, como ya declara el informe. Si crece,
   el sitio es `ruesma_comun.correo`.
5. Limpieza fuera de F-048: `git worktree list` tiene 28 worktrees huérfanos `%TEMP%/mutacion_F-047_*`.

## Juicios pedidos

- **OMITIDO frente a ERROR:** hoy sí puede esconder un empeoramiento real (bloqueante 2). El aislamiento es
  bueno y hay que mantenerlo: que un caso roto no se lleve por delante la pasada ni el informe. Lo que
  sobra es que el veredicto siga en VERDE.
- **T30 sin `GestoRevisor` ni `test_f047_r5_seleccion_contrato.py`:** es aceptable. Traer ese test obliga a
  traer `lectura_bbdd.py` (623 líneas, la capa del ciclo), y eso es justo lo que el humano descartó. En esta
  rama nadie usa `GestoRevisor`, y su test llega con F-047. Solo pido que conste, y eso entra en el bloqueante 4.
- **`anadir_opcion_sin_correo` sin cablear:** es aceptable, porque el CLI del ciclo no existe en esta rama.
  El test de la opción y el de «con y sin correo en dos pasadas» fijan el contrato. La condición es el
  bloqueante 4.
- **Comparador:** la variante `dev` manda lo mismo que `dev`: instrucciones, `user_text` y schema idénticos
  contra el código de `dev` extraído con `git archive`, y los clientes y el preproceso no cambian entre las
  dos ramas. La clasificación es correcta: el vacío cuenta como null, solo se compara el código, un error
  manda el caso a `con_errores` y `difiere` exige que las dos variantes sean estables.

## Checkpoints

- C1 [x] init.sh en verde · [x] ficheros base.
- C2 [x] una sola `in_progress` · [x] rama correcta · [x] current.md (el contenido se revisó en la final).
  N/A history.md: F-048 aún no está `done`.
- C3 [x] hexagonal: `evals/` está fuera de los servicios e importa sv2 solo dentro de funciones
  (`sv2_obra.py:137,199`) · [x] primera línea con la ruta · [x] sin prints de debug (el `print` a stderr es la
  salida de avance a propósito) · [ ] **R31, sin valores en lo versionado: bloqueante 1**.
- C3 bis N/A: en este delta no entra ningún documento de fuera.
- C4 [x] R38, R40 y R41 con test que existe y pasa · [x] sin red ni BBDD (el test de `dev` solo usa git
  local) · [x] MANUAL listado (T36–T40).
- C4 bis [x] rigor declarado · [x] RED real, reproducida en las tres piezas · [x] cobertura 97.0 % ·
  [ ] **mutación y RM1: bloqueante 3** · RM2 N/A: no hay campaña nueva que medir · RM3, RM5 y RM6: no hay
  equivalentes ni guardas quitadas en este delta · [x] «Evidencias» en los dos informes.
- C4 ter: AVISO por falta de T40. Es la exigencia `aviso` declarada, con su motivo impreso.
- C5 [x] T29–T31 en `[x]` con commits `F-048 Tn:` · [x] árbol limpio. El runner y el comparador son
  encargos sin tarea en `tasks.md`, con commits `F-048:`; están trazados en `impl_F-048_evals.md`.

## Cobertura requisito → test

| R | Test |
|---|---|
| R38 | `test_f048_evals_correos.py::test_f048_r38_*` (5), incluido el del repositorio real, que he comprobado que cae |
| R40 | `test_f048_r40_r41_inyeccion.py::test_f048_r40_*` (9) + `test_f048_evals_correos.py::test_f048_r40_*` (8) |
| R41 | `test_f048_r40_r41_inyeccion.py::test_f048_r41_*` (4) |
| Runner (encargo) | `test_f048_evals_fallos_aislados.py` (31) |
| Comparador (encargo) | `test_f048_comparar_obra.py` (19) + `test_f048_comparar_obra_prompt_dev.py` (4) |

## Automejora (propuesta, no aplicada)

- `CHECKPOINTS.md` C4 bis: añadir «si el delta mete ficheros que `harness.alcance` cuenta como producción,
  el reviewer recalcula el número de mutantes sobre HEAD y lo compara con el del informe». Aquí la diferencia
  era de 175 a 394 y nada la señalaba.
- Reviewer: cuando un cambio sanea mensajes de error, probar el centinela **también en claves y nombres de
  campo**, no solo en valores.
