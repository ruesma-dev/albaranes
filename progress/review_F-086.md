<!-- progress/review_F-086.md -->
Revisión completa (pasada 1) · parte A (T1–T8) · `dev...b696285`

# F-086 · Review de la parte A (código)

**Veredicto: APPROVED** (solo parte A). B (medición de pago) y C (producción, incluida
`$ANTHROPIC_MODEL_SV5` de T12) quedan fuera por mandato del líder y no se han juzgado. Tras esto,
F-086 → `blocked` a la espera de F-100 en `dev` (D1 = a).

**Rigor:** `critico`, declarado en `features.json`. Exige fase RED, cobertura ≥ 80 % de lo cambiado,
mutación completa con 0 supervivientes, RM1–RM6 y MANUAL con su comando.

## init.sh (ejecutado dos veces, en serie y nunca dos suites a la vez)

1. **Tal cual:** exit 1, con **un único KO**: sv5 `test_f086_r12_el_servicio_no_transforma_el_valueerror`
   (`1 failed, 123 passed`). Es por el entorno: sv5 importa `ruesma_comun` del árbol principal, sin T1,
   y el mensaje no trae `(stop_reason=refusal)`. Raíz 1919, sv1 205, sv2 485, sv3 1576, sv4 1933,
   sv6 480+1s, sv9 1026, comun en verde (caché); cobertura 100 % (27/27).
2. **Con `PYTHONPATH=C:\Users\pgris\PycharmProjects\albaranes-F-086\services\albaranes-comun` y
   `ARNES_SIN_CACHE=1`:** **exit 0, «ENTORNO LISTO»**. Raíz 1919, sv1 205, sv2 485, sv3 1576,
   sv4 1933, **sv5 125**, sv6 480+1s, sv9 1026, **comun 1077+3s**. `PUERTA COBERTURA: 100.0% de 27
   líneas (critico)`. Tamaño en tope. Es el mismo criterio que se aceptó en F-098.

## Puntos pedidos por el líder

1. **`_parse_response` (comun).**
   - **R4:** el diff de comun no toca `messages.create` ni `__init__`: solo la llamada a
     `_parse_response` (añade `model`) y el respaldo. Con `true` o sin la variable, sv5 pasa
     `forzar_herramienta=True`, que es el defecto de comun. Los tests r4 comparan el dict exacto de
     `messages.create` y el `true` explícito frente a sin variable; F-083 R38 sigue intacto.
   - **Camino sin `tool_use`:** texto unido, cerca quitada, `dict` exigido,
     `model_validate(sanear_para_modelo(...))`. Cualquier fallo da `ValueError(... (stop_reason=X).)`
     `from exc`. El WARNING lleva solo el modelo y el `stop_reason` (r9 lo comprueba con
     `SECRETO-77`). El camino `tool_use` no cambia (r11). sv5 responde 400 con el mismo `detail` y
     `__cause__` (r12, con el `ValueError` real).
   - **Riesgo aceptado (design §8):** sv2 también acepta JSON de texto válido en su próxima imagen.
2. **Tests intermitentes.** `test_f083_claude_forzar_herramienta.py::_Logger.log_call` y
   `test_f086_forzar.py::_peticion` solo hacen `pop("duration_ms")`, sin defecto: si falta, falla.
   Ninguna otra aserción del fichero de F-083 cambia (diff de 4 líneas).
3. **Mutación.** Comprobaciones:
   - **Recálculo puro** en `b696285`: 5 ficheros, 112 líneas, **4 mutantes**. Coincide. Son
     `is not None→is None` (`sv5_valoracion.py:326`), `not` (`:338`), `True→False`
     (`settings.py:84`) y `not isinstance` (`comun :333`).
   - **RM1:** SHA medido `53baed8…`. `git diff 53baed8 HEAD -- services evals` está vacío; solo
     cambió el papeleo.
   - **RM2:** 4 × 223,6 ≈ 894,3 s, con 1 worker. La media es coherente con bases de 313, 20 y 167 s.
   - **Reejecución:** campaña no reejecutada, porque el informe declara 894 s (> 60 s).
   - **Mutantes a mano:** la tabla manual es reproducible (fichero, línea, texto exacto y fallidos).
     **Reproducidas 4 filas al pie de la letra** sobre una copia (`git archive` en el scratchpad),
     sin `-x` y con la comun de la copia. Primero la base: 31, 53 y 60 passed. Resultados:
     **M3** 1 failed, **M5** 10 failed, **M12** 2 failed, **M22** 1 failed. Coinciden los cuatro.
     Copia restaurada y verificada con `cmp`; el worktree no se tocó.
   - **RM3:** ningún mutante muerto es equivalente. M22 sí cambia la conducta: `"   "` sin `strip`
     hace fallar `int`.
   - **RM5:** N/A, no hay supervivientes.
   - **RM6:** N/A, no se quitó ninguna guarda.
4. **Desviaciones (a)–(e)**, aceptadas:
   - **(a)** `test_f085_wiring.py` gana `"forzar_herramienta": True` en su dict exacto. Lo exige R3
     (pasar el valor siempre) y el resto del fichero está intacto.
   - **(b)** En `test_f083_fases.py`, la fixture carga la herramienta real de sv5 y borra las dos
     variables. Solo la expectativa de sv5 añade `tool_description` (R13). sv2 conserva el dict exacto
     (R15, comprobado también en `test_f086_r15`).
   - **(c)** `README_capps.md`: es correcto que se corrija.
   - **(d)** El *junction* de `.venv` de sv4 no está versionado. Hay que quitarlo antes de
     `git worktree remove`.
   - **(e)** Ver el punto 2.
5. **Puerta de rutas sensibles:** `[AVISO]` por 2 rutas, sin `progress/evals_F-086.md`. El motivo
   consta: D4 = (a), y la justificación de design §9 está en `impl_F-086.md` (T7). La exigencia es
   `aviso` y el runner usa `gpt-6.1-sol`, así que no ejercita lo cambiado.
6. **`azure-apps` `b9b6564`** (local, rama `master`, sin push): añade en §14 la viñeta de
   `ANTHROPIC_FORZAR_HERRAMIENTA` (defecto `true`, sin fijar en Azure, sin desplegar) y la fecha al
   pie. Cumple R17.

## Checkpoints

- **C1** [x] init.sh exit 0, en la segunda forma; el rojo de la primera es solo de entorno.
  [x] Ficheros base presentes.
- **C2** [x] Una sola feature `in_progress` (F-086). [x] Rama `feature/F-086-opus-ia3`.
  [x] `current.md` coherente. [x] Las `done` siguen igual.
- **C3** [x] Hexagonal: las constantes viven en `infrastructure/llm` y la configuración en `config`;
  el dominio no se toca. [x] Primera línea con la ruta en los 13 `.py`. [x] Sin `print`, TODO,
  secretos ni dependencias nuevas. [x] Trampas de dominio: N/A, sin SQL, schema ni importes.
- **C3 bis** N/A: no toca `docs/referencia/`.
- **C4** [x] Cada requisito de A tiene su test (tabla). [x] Los dobles sustituyen al SDK, sin red ni
  BBDD. [x] MANUAL: la parte A no tiene ninguno. M1–M6 (T9–T13) son de B y C y su comando exacto
  está en design §6. **Observación:** al pasar a `blocked`, el líder debe llevarlos a `current.md`.
- **C4 bis** [x] rigor. [x] RED con trazas reales de T1–T6 (R7 es una guarda que nace en verde,
  justificado). [x] cobertura. [x] mutación verificada. [x] muertos (> 60 s). [x] coste por mutante
  ≥ 1 s. [x] sin «CAMPAÑA NO VÁLIDA», con 0 sin veredicto. [x] RM1. [x] RM2. [x] RM5 y RM6 N/A
  (motivo arriba). [x] tabla manual reproducida. [x] 0 supervivientes. [x] «Evidencias» completa,
  con 1 worker.
- **C4 ter** [x] aviso con su motivo (punto 5).
- **C5** [x] T1–T7 en `[x]` con su commit. T8 cierra con esta review y T9–T14 están fuera de
  alcance. [x] Sin restos, árbol limpio. [x] `features.json` real.

## Cobertura requisito → test

| Req. | Test | Req. | Test |
|---|---|---|---|
| R1 | `test_f086_r1_*` (sv5) | R9 | `test_f086_r9_*` |
| R2 | `test_f086_r2_valor_no_booleano_no_arranca` | R10 | `test_f086_r10_*` |
| R3 | `test_f086_r3_*` + `test_f085_r14_*` | R11 | `test_f086_r11_*` |
| R4 | `test_f086_r4_*` + `test_f083_r38_*` | R12 | `test_f086_r12_*` (servicio y API 400) |
| R5 | `test_f086_r5_false_pide_auto` | R13 | `test_f086_r13_*` (raíz) |
| R6 | `test_f086_r6_build_app_escribe_el_valor_leido` | R14 | `test_f086_r14_*` |
| R7 | `test_f086_r7_*` (textos) | R15 | `test_f086_r15_*` + `test_f083_runner_fabricas_*` |
| R8 | `test_f086_r8_*` (comun) | R16 | `test_f086_r16_*`; R17: el reviewer, en `b9b6564` |

R18–R27 son de B y C, fuera de esta pasada.

## Cambios requeridos

Ninguno.

**Para el líder:** marcar T8 `[x]`, poner F-086 en `blocked` (motivo D1, F-100) con M1–M6 en
`current.md`, y quitar el *junction* antes de retirar el worktree.
