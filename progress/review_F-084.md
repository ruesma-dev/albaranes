<!-- progress/review_F-084.md -->
Revisión incremental desde fbbabd7 (pasada 2) · `git diff fbbabd7..c4bf6f3` · lo aprobado hasta `fbbabd7` queda dado por bueno

# F-084 · Review del reviewer: el banco de evals valora de verdad

## Veredicto

**CHANGES_REQUESTED (RECHAZADO), solo por documentación.** El código, los tests, la mutación y
`init.sh` están en verde y aprobarían. Lo que falla es que la spec, los informes y `current.md`
siguen diciendo «pendiente del humano» en dos decisiones que el humano **ya tomó** (D1 y la línea
base de R28). Con las condiciones 1–4 aplicadas y `init.sh` en verde, es APROBABLE sin otra
revisión de código (no hace falta remedir mutación: no cambia ningún `.py`).

La pasada 1 (APPROVED para lanzar T12, HEAD `fbbabd7`) está en el historial: `git show a2aeaaf:progress/review_F-084.md`.

## Nivel de rigor

`critico` (declarado): fase RED, cobertura ≥ 80 %, mutación completa con 0 supervivientes, RM5.

## Decisiones del humano en vigor (dadas al líder) y dónde deberían constar

| Decisión | En el código | En spec / informes |
|---|---|---|
| R37, tolerancia 0,05 € (opción a) | sí, `comparador.py` (T16) | sí (R37, design §4, §11) |
| D1, el modelo es `gpt-6.1-sol` | sí (R20) | **no**: «pendiente de confirmación» en 5 sitios |
| D5: partida fuera de IA3 (R38), INPUTS con la de IA1 (R39) | sí (T17) | sí (R38, R39, design §4, §11) |
| D5: 28 sintéticas `?` = tarea de datos del banco | — | sí (design §11, impl, current) |
| D5: línea base de R28 aceptada ≈ 23,5 % (23 de 98) | — | **no**: R28 sigue con «≤ 20 %» y «el umbral lo revisa el humano»; impl, T14 y current dicen «no cambia hasta que decida» |

## Lo verificado por el reviewer

- **`bash harness/init.sh`** (worktree, HEAD `c4bf6f3`, ejecutado tal cual): **`ENTORNO LISTO`, exit 0**.
  Raíz 1883 passed (260,3 s); sv1 205, sv2 485, sv3 1576, sv4 1774, sv5 96, sv6 473 (+1 skipped),
  sv9 673, comun en verde (caché); `PUERTA COBERTURA: 98.6% de 638 líneas` `[OK]`; rutas sensibles N/A;
  `PUERTA TAMAÑO`: requirements **150/150**, design **250/250**, impl 216/220. El `.venv` de sv4 existe.
  Antes de lanzarlo esperé unos 60 min a que acabaran las suites de `datamart-seg-anual` y `partes`
  (ninguna de albaranes): corrió sin otra suite a la vez.
- **R23**: `git diff fbbabd7..HEAD -- services/ harness/rutas_sensibles.json` vacío.
- **R6/R11**: los RES solo ganan `linea_sigrid: null` y el `sha256_libro`; líneas y señuelos intactos.
- **T16 (R37)**: `tolera_centimos` por (tabla, campo) con la lista de R37; IA1 fuera; diferencia en
  `Decimal` desde `repr`, `<= 0,05`; `None` y no finitos siguen siendo fallo. Tests de límite (0,05
  entra, 0,06 no), del total de FER-002 y de los campos exactos.
- **T17 (R38, R39)**: `codigo_partida_final` fuera de `OBSERVABLES["lineas_valoradas"]`; E2E sigue
  con `partida_final`. `con_partidas_de_ia1` es pura (copia JSON), INPUTS manda, `?`/`REVISIÓN`/
  `None` no son partida y exige el mismo `num_linea` **y** la descripción `equivalentes` (FER-002 L4/L5,
  test con los fixtures reales). `runner.cargar_inputs` es la única carga en las dos corridas y en
  las dos de `comparar_modelos` (R39 «en el comparador de F-083», con su test). Los ajustes a F-011
  r13/r16 conservan la intención (la partida torcida sale roja en E2E; lo crítico torcido es el precio).
- **Review 1 aplicada** (`92b5e42`): `motivo_sin_lineas` (R18) en las dos corridas, `falta_documento`
  (R33) solo con LLM y en `casos_de_fase` de IA3/IA4; tres `test_f084_r33_*`, uno sin caché.
- **R28, recontado por mí** desde `progress/evals_F-084.md` (local, fuera de git; aquí solo recuentos):
  IA3 212 fallos, 137 «obtenido None», 86 de ellos `codigo_partida_final` (todos None) ⇒ **51/126 =
  40,5 %**; de los 51, 28 son filas de `sinteticas_esperadas` sin pareja ⇒ **23/98 = 23,5 %**
  (8 `precio_source`, 7 `importe_calculado`, 7 `precio_unitario_final`, 1 sintética). Coincide.

## Mutación (C4 bis)

- **Recálculo puro** (`parsear_diff` + `filtrar_produccion` + `generar_mutantes` en cada SHA):
  review 1 `1839b8c..57c3c0c` → **41 líneas, 10 mutantes**; T16 `5f70189..daa6293` → **42, 8**;
  T17 `83680ea..a4d7653` → **45, 5** (los 5 en `sv6_build.py` 276–287; `runner`/`comparar_modelos`
  sin operadores). Los tres coinciden con sus informes; listé cada mutante (operador y texto).
- **Campañas no reejecutadas**: 2.065,1 s, 1.828,9 s y 1.201,3 s según los informes (> 60 s).
- **RM1** [x]: los `.py` de producción solo cambian en esos tres rangos (más `comparador.py` y
  `backlog.py`, que trae la fusión de `dev` y son ajenos); de `a4d7653` a HEAD, ningún `.py`.
- **RM2** [x]: medias 206,5 / 228,6 / 240,3 s con líneas base 448 / 331–333 / 304–310 s: mismo
  orden de magnitud, coherente con `-x` y con el 100 % de muertos. Sin «NO VÁLIDA», sin veredicto = 0.
- **RM3** [x] sin equivalentes. **RM5** N/A: ninguna campaña declara equivalentes ni supervivientes.
  **RM6** [x]: en T16 se quitó un `round(…, 6)` (no es una guarda defensiva: la comparación pasa a
  `Decimal`); en T17 no se quita ninguna guarda.

## Checkpoints

- **C1** [x] init.sh exit 0 · [x] ficheros base.
- **C2** [x] una `in_progress` · [x] rama de la feature · **[ ] `current.md` describe el estado real**
  (D1 y la línea base de R28 constan como pendientes; condición 4) · [x] historia.
- **C3** [x] hexagonal N/A dentro de `evals/` (herramienta, design §6), servicios intactos · [x]
  primera línea con ruta en el código y en los tests nuevos · [x] sin `print` de debug ni secretos · [x]
  importes en `Decimal`.
- **C4** **[ ] trazabilidad de R28**: el requisito no dice el criterio que el humano aceptó, así
  que la cifra de T14 no se puede juzgar contra él (condición 1) · [x] sin red ni BBDD (fixtures,
  `tmp_path`, sv6 por subproceso sin llamadas) · [x] MANUAL T12/T14 con su comando en `current.md`.
- **C4 bis** [x] rigor · [x] RED real de T16 y T17 (salida pegada, incluida la guarda de
  descripción) · [x] cobertura 98,6 % · [x] mutación recalculada · [x] RM1 · [x] RM2 · RM5 N/A ·
  [x] RM6 · [x] sin pendientes · [x] «Evidencias» con los cuatro números · [x] ningún N/A sin motivo.
- **C3 bis** N/A: no toca `docs/referencia/`. **C4 ter** N/A: la puerta no señala rutas sensibles.
- **C5** [x] T1–T17 `[x]` con commits `F-084 Tn:` (T14 `6dd6c88`, T16 `46b60ac`/`daa6293`, T17
  `a4d7653`) · [x] árbol limpio · [x] `features.json` `in_progress`, rama, `servicios = evals`.

## Cobertura: requisito → test (delta de esta pasada)

| Req | Test (o verificación) |
|---|---|
| R33 (review 1) | `tests/test_f084_runner.py::test_f084_r33_*` (4, uno sin caché) y 2 de F-083 |
| R37 | `tests/test_f084_tolerancia_importes.py` (29: límite, total FER-002, campos exactos, `None`) |
| R38 | `tests/test_f084_partida.py::test_f084_r38_*` (2) + F-011 r13 ajustado |
| R39 | `test_f084_partida.py::test_f084_r39_*` (10: INPUTS manda, `?`/`REVISIÓN`, FER-002, `cargar_inputs`, sv5, sv6, comparador) |
| R27 | MANUAL T12 + determinista de T13 (`impl_F-084_T14.md`, anexo) |
| R28 | MANUAL T14: 0 ERROR y `- Modelo: gpt-6.1-sol`, sí; la cifra, contra un criterio que no está escrito (condición 1) |

Lo demás (R1–R26 y R29–R36) quedó cubierto en la pasada 1.

## Cambios requeridos

Solo texto; ningún `.py`. Cuidado con los topes: requirements y design están en **150/150 y 250/250**,
y cada edición debe quedar neutra en número de líneas.

1. **`specs/F-084-banco-valoracion/requirements.md:146-150` (R28).** Quitar «**pendiente de
   confirmación del humano**» (D1 decidido: `gpt-6.1-sol`) y sustituir «≤ 20 % … el umbral lo
   revisa el humano con la cifra de T14» por la línea base aceptada por el humano el 2026-10-23
   (D5): «obtenido None» **23 de 98 = 23,5 %** de los fallos críticos de IA3, contados sin
   `codigo_partida_final` (R38) ni las 28 filas de `sinteticas_esperadas` con `rol_linea` en `?`
   (tarea de datos del banco, fuera de F-084). Que conste también lo que el banco mide hoy con esas
   28 dentro, **51 de 126 = 40,5 %**, y que T14 se tomó antes de R39 (sin la partida en el prompt).
2. **`design.md:215-216` (§9, T14) y `:242-243` (§11, P6):** quitar «pendiente de confirmación
   del humano»; en el punto D5 de §11 (`:247-250`), añadir que el humano acepta el 23,5 % como línea
   base documentada de R28 en lugar del 20 %.
3. **`tasks.md:20` (T14):** quitar «D1, pendiente de confirmación del humano».
4. **Informes y estado:** `progress/impl_F-084.md:159-160` y `progress/impl_F-084_T14.md:82` y
   `:138-139` dejan de decir «el líder propone … R28 no cambia hasta que decida»: el humano ha aceptado
   el 23,5 %. Pasar al estado decidido `progress/current.md:4` («propuesta del líder como línea base»),
   `:7` («queda pendiente de confirmación del humano»), `:58` («pendiente de confirmación») y `:78`
   (criterio «≤ 20 %»). Después, `bash harness/init.sh` en verde (PUERTA TAMAÑO incluida).

## Observaciones (no bloquean)

- **O6.** `dev` está en `84653d2` (altas de F-099–F-102) y la rama fusionó `416b55c`: antes de
  integrar, fusionar `dev` y repetir `init.sh`.
- **O7.** T13 versiona en `evals/fixtures/inputs/` las 3159 líneas de contrato de Sigrid con sus
  precios. Es lo que piden T13 y el `.gitignore` («entran los fixtures JSON ya barridos») y lo lanzó
  el humano, pero son precios de proveedor en git, cuando los informes del runner se sacaron de git
  justo por eso. Conviene que el humano lo tenga presente.
- **O8.** La línea base de R28 se recontó del texto de T14, que no llevaba la partida (R39) en el
  contexto de IA3: la próxima pasada con LLM medirá también ese efecto, y su cifra no es comparable
  una a una con el 23,5 %.

## Automejora (propuesta, no aplicada)

`leader.md` / `CHECKPOINTS.md` C2: «cuando el humano decide en el chat algo que la spec deja
"pendiente del humano", el líder lo traslada a la spec y a `current.md` **antes** de pedir la
revisión final». Aquí la decisión le llegó al reviewer por el encargo, no por la spec.
