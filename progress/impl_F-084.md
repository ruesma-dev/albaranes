<!-- progress/impl_F-084.md -->
# F-084 · Informe del implementer — el banco de evals valora de verdad

Rama `feature/F-084-banco-valoracion` (worktree `../albaranes-F-084`), `dev`
`416b55c` fusionado (F-083, F-085, altas hasta F-098). Rigor `critico`.
Servicios tocados: **ninguno** (solo `evals/` y tests). T1–T11, T13, T15–T17
hechas, y los 3 cambios de la review pasada 1; T12 y T14 las lanzó el humano el
2026-10-23 (comandos en `progress/current.md`). D5 aprobada por el humano → T17.

## Qué cambió

| Fichero | Cambio |
|---|---|
| `evals/procesos/sv6_build.py` | `lineas_albaran_de` (descuento, precio neto, importe derivado en `Decimal`, `DescuentoCompuesto`) y `clasificacion_de` con `MAPA_FAMILIA_DOCUMENTO`; el envelope estimulado las usa y lleva `clasificacion` (R12–R14). Estímulo de matches sin cambios. |
| `evals/revision/escritura.py` | Clave de `contrato_lineas` = (`caso_id`, `codigo_producto`, `linea_sigrid`) (R11). |
| `evals/contratos.py` (nuevo) | CLI `lineas` (sigrid-api → `INPUTS.xlsx`) y `documentos` (BBDD + SharePoint → caché e índice); `LectorSigrid` con reintentos tenacity; informe `progress/import_F-084.md` (R1–R11, R29–R31, R34). |
| `evals/procesos/sv5_documentos.py` (nuevo) | Subproceso con sv5 en `sys.path`: `_SQL_CONTRATO_HEADER` de sv5 en sesión `default_transaction_read_only=on`, descargador de sv5, MD > PDF, `MAX_PDF_MB` = 40; credenciales por entorno, no por stdin. |
| `evals/procesos/sv5_valoracion.py` | `documento_de` (sha256 contra el índice, R32/R33); `construir_contexto` con cabecera del índice, `lineas_albaran_de`, `clasificacion_de` y documento; subproceso: `Raw*` + `UnitCategoryPrefilter` + `ClasificacionAlbaran`, `preparar_contexto`, MD como `contrato_markdown` / PDF como adjunto, `modelo` en el trabajo y en la salida, `valorar_casos` como puerta del subproceso. |
| `evals/procesos/sv5_modelos.py` | La línea de `preparar_contexto` en su `main` (design §8). |
| `evals/runner.py` | R18 y R13 en las dos corridas y R33 solo en la de LLM (review 1), antes de montar sv5/sv6; R19 (`fases` sin IA1/IA2 ⇒ sin sv2 ni sus claves; las de sv5 se exigen antes de nada); R20 `valoracion_por_defecto`; R17/R21 en las fases. |
| `evals/comparar_modelos.py` (de F-083) | R33 en `casos_de_fase` de IA3 e IA4 vía `sv5_valoracion.falta_documento` (review 1). |
| `evals/procesos/sv6_build.py`, `evals/runner.py`, `evals/comparar_modelos.py` (T17) | R38: `codigo_partida_final` fuera de `OBSERVABLES` de IA3. R39: `con_partidas_de_ia1` y `runner.cargar_inputs`, la única carga de INPUTS del runner y del comparador. |
| `evals/comparador.py`, `evals/criticidad.json` | R37 (T16): 0,05 € de tolerancia, en `Decimal`, en los importes y precios valorados (`CAMPOS_CON_TOLERANCIA_EUR`); IA1 exacta; en `criticidad.json`, solo una nota. |
| `evals/modelos.py`, `evals/informe.py` | `ResultadoFase.modelos` y `.documentos`; `- Modelo: …`, `- Documento del contrato: md N · pdf N · ninguno N` y la advertencia de emparejamiento del determinista (R36). Líneas parseables idénticas. |
| `evals/README.md` | Sección de F-084 (R26). `azure-apps/albaranes.md` §8: commit local `a6bc26a`, **sin push**. |
| Tests | `tests/test_f084_{contratos,contexto_valoracion,runner,tolerancia_importes}.py` (202 tests). Ajuste en 2 tests de F-083 y 1 doble de F-048 (D2); los 2 de F-083 sobre el build real aíslan el índice (D4). |

## Decisiones de diseño

- **Descuento en `Decimal`**, como el `COALESCE` de sv5 en `numeric` (float: 19,409999…).
- **`descuentos`** llega como número, lista (`a;b`) o texto; `?`/vacío = sin descuento; >1 = R13.
- **R13**: con LLM, IA3 `ERROR` e IA4/E2E `OMITIDO`; en el determinista, IA3/E2E `ERROR`.
- **R9**: la fecha que falta se escribe en cualquier caso pedido; nunca pisa una existente.
- **`preparar_contexto` por costura**: `ejecutar_trabajo(trabajo, fabrica, preparar)` sirve
  al test in-process de F-083; el subproceso entra por `valorar_casos` (también los de T7).
- **El índice va con los fixtures** (`<fixtures>/contratos/_indice.json`); sin índice
  explícito se lee el versionado (el comparador de F-083 hereda contexto y R33).
- **Informe compartido** `progress/import_F-084.md`; sigrid-api solo `sql/read`, BBDD solo lectura.
- **Costuras por T15**: `LectorSigrid(dormir=…)`, `_sesion_real(crear, abrir)` y
  `_descargador_real(clase)` prueban reintentos y montaje real sin conectar.

## Desviaciones (justificadas también en `progress/current.md`)

- **D1 · R20/R28/T14 (líder):** el defecto es la referencia IA3 de
  `evals/precios_modelos.json` (`openai`/`gpt-6.1-sol`, atada a `infra/` por R3
  de F-083), no `claude-opus-4-8`. Cumple P6 = (a); ya en la spec (review 1).
- **D2 · R18 frente a tests ajenos:** `test_f083_runner_evaluar_valoracion_
  coincide_con_el_modo_determinista` y `test_f083_bloque_ia3_con_la_ia4_del_libro`
  comparaban en FER-001/GEN-001/HOR-005 (sin líneas: ahora OMITIDO); pasan a
  RES-001/004/006, misma intención. El doble de `construir_contexto` de
  `test_f048_evals_fallos_aislados.py` acepta `**_`. Ninguna expectativa cambia.
- **D4 · R33, opción (a)** (cambio 1 de la review): ver «Review pasada 1».
- **D3 · `dev` `2721e06` fusionado** (banco IA1 corregido): solo cambian claves `IA1.*` de `afirmado_por_el_humano_RES.json`; el guardián de R24 pasa a fijar lo afirmado fuera de IA1 (idéntico a `efd73b7`) y RES-001..007 dan los mismos fallos (RES-007 IA3 4, E2E 6); los ajustes D2 siguen valiendo.

## Fase RED (comando y salida real, antes del código)

Comando base: `PYTHONPATH=<worktree>/services/albaranes-comun python -m pytest <fichero> -k "<filtro>" -q`.

- **T1** (`test_f084_contexto_valoracion.py -k "r12 or r13 or r14"`):
  `E   ImportError: cannot import name 'MAPA_FAMILIA_DOCUMENTO' from 'evals.procesos.sv6_build'`.
  Comportamiento antes del cambio (FER-001 por el subproceso real de sv6):
  `FER-001 importe_calculado (antes de T1): [32.35]` · `clasificacion en context: False`.
- **T2** (`test_f084_contratos.py -k r11`):
  `E       AssertionError: assert ('caso_id', 'codigo_producto') == ('caso_id', '...linea_sigrid')`
  `E       assert [(12, 2)] == [(11, 1), (12, 2)]` → `2 failed, 1 passed`.
- **T3** (`-k "r1 or r5 or r6 or r9 or r10"`):
  `E   ImportError: cannot import name 'contratos' from 'evals'`.
- **T4** (`-k "r2 or r3 or r4 or r7 or r8"`):
  `E       AttributeError: module 'evals.contratos' has no attribute 'main'` → `9 failed, 1 passed, 23 deselected`.
- **T5** (`-k "r29 or r30 or r31 or r34"`):
  `E   ImportError: cannot import name 'sv5_documentos' from 'evals.procesos'`.
- **T6** (`-k "r17 or r32 or r33"`):
  `E       AttributeError: module 'evals.procesos.sv5_valoracion' has no attribute 'documento_de'` ·
  `E       TypeError: construir_contexto() got an unexpected keyword argument 'indice'`.
- **T7** (`-k "r12 or r14 or r15 or r16 or r32 or r20"`):
  `At index 0 diff: {... 'importe_albaran': None, ...} != {... 'importe_albaran': 19.41, ...}` ·
  `E       KeyError: 'clasificacion'` · subproceso: `AttributeError: module 'evals.procesos.sv5_valoracion' has no attribute 'valorar_casos'`.
- **T8** (`test_f084_runner.py -k "r13 or r18 or r19 or r20 or r32 or r33"`):
  `E           AssertionError: assert ('ROJO', '') == ('OMITIDO', '...to en INPUTS')` ·
  `E       TypeError: corrida_completa() got an unexpected keyword argument 'fases'` ·
  `FAILED ...test_f084_r19_por_cli_tampoco - assert 2 in...` (sin GEMINI_API_KEY salía 2) → `16 failed, 1 passed`.
- **T9** (`-k "r17 or r21 or r36"`):
  `E           TypeError: ResultadoFase.__init__() got an unexpected keyword argument 'modelos'` ·
  `E       AssertionError: assert 'NO mide el emparejamiento' in 'IA3 · valoración contra contrato (sv5) — VERDE ...'` → `8 failed, 1 passed`.
- **T11** es un guardián de no regresión (R24): pasa en `efd73b7` y en HEAD por
  construcción; no hay fase RED que mostrar.
- **T16** (`test_f084_tolerancia_importes.py`, antes del código): `E  AttributeError:
  module 'evals.comparador' has no attribute 'TOLERANCIA_IMPORTE_EUR'` · `E  AssertionError:
  assert False` (17,59 frente a 17,5932, ×13) → `16 failed, 13 passed in 2.73s`.

## Verificación (resultado real)

- T1: FER-001 determinista por el subproceso real de sv6 → `importe_calculado` 19,41.
- T2: `pytest tests/ -k f045` → `296 passed` sin tocar expectativas.
- T7 (doble de LLM en subproceso): RES-001 usa `valuation_residuos` y el texto lleva
  descuento, `"unidad_categoria": "count"`, fecha, cabecera y el MD; un PDF va adjunto.
- T11: determinista en `efd73b7` y HEAD, RES-001..007 idénticos (001–006 VERDE; RES-007
  IA3 4 y E2E 6 fallos en los dos, detalle igual).
- Humo del subproceso real de documentos sin red (`contratos: []`, entorno
  falso) → `{'resultados': []}`; `python -m evals.contratos --help` correcto.

## Fuera del alcance / pendiente

- **Tarea de datos del banco (anotada, no hecha):** las 28 filas de sintéticas con
  `rol_linea` en `?` (25 casos) no casan nunca. IA4 usa el proveedor de IA3, como antes.
- **Emparejamiento como lo describe el humano** (solo IA4, prefiltro de precio
  ±0,02 € y partida, y luego significado): feature aparte que propone el líder.
- R18 no se aplica en el comparador de F-083 (la spec no lo pide); R33 sí.

## T12 (humano) y T13: línea base determinista (`b39cb0e`; detalle en `progress/impl_F-084_T14.md`, anexo)

T12 (2026-10-23): `lineas` 18 contratos, 0 fallidos (3159 filas, 52 fechas); `documentos` 20
(md 1, pdf 6, ninguno 13: 30 casos sin documento). T13 versiona fixtures, índice e informe de
importación, con barrido de sensibles. **R27 en verde.** Determinista: IA3 394 fallos, E2E 572;
con R37 (`daa6293`) 386 y 563; los «obtenido None» son el emparejamiento que no mide (R36).

## T14 (humano): línea base con LLM, `gpt-6.1-sol` (detalle: `progress/impl_F-084_T14.md`)

Informes del runner fuera de git (precios de proveedor); aquí, solo recuentos.
IA3 59 evaluados, 0 ERROR, ROJO 58 · VERDE 1, **212 fallos**, 137 «obtenido None»;
IA4 13 evaluados (46 OMITIDO), ROJO 13, 27 fallos; E2E ROJO 52 · VERDE 7, **312**.
Modelo en las tres fases; documento md 5 · pdf 24 · ninguno 30. Coste real: no
consta (el runner no mide tokens). Humo: IA3 19, IA4 3, E2E 23. Frente al
determinista: IA3 386 → 212 y líneas sin precio 91 → 8.

- **R28, tal cual: 137 de 212 = 64,6 %.** 86 son `codigo_partida_final`, que IA3 no
  produce; 28, sintéticas con `rol_linea` en `?` que no pueden casar. D5 aprobada →
  T17; la cifra con el criterio nuevo, en «T17».
- **Valoración frente a emparejamiento** (según el código de hoy): IA3 76 de
  valoración y 20 de emparejamiento, IA4 27 de emparejamiento. El banco apenas
  mide el emparejamiento: IA4 solo tiene 13 casos con libro.

## T17 · D5 del humano: R38 y R39 (`a4d7653`)

- **R39 casa por `num_linea` y descripción.** Solo por número, FER-002 L4 y L5 recibían
  `CI.4.18` donde el final espera `P5.36.01` (en 21 casos IA1 e INPUTS no numeran igual).
  Quedan 56 de 110 líneas con partida; 33 sin línea IA1 de ese número y 19 con `?` en IA1
  siguen sin ella: no se inventa. El contexto de IA3 con LLM lleva ya la partida, como en
  producción; T14 se tomó sin ella.
- **Tests ajenos:** F-011 r13 (la partida torcida sale roja en E2E y no en IA3) y r16 (lo
  crítico torcido pasa a ser el precio); nota en `criticidad.json`; I001 de ruff, previo, corregido.
- **RED** (`python -m pytest tests/test_f084_partida.py -q`, antes del código):

```
E  AssertionError: assert 'codigo_partida_final' not in ('num_linea', 'match_method', 'codigo_producto_contrato', 'codigo_partida_final', ...)
E  AttributeError: module 'evals.procesos.sv6_build' has no attribute 'con_partidas_de_ia1'
E  AttributeError: module 'evals.runner' has no attribute 'cargar_inputs'
E  AssertionError: assert not [Discrepancia(campo='FINAL.lineas[1].partida_final', esperado='CI.4.18', obtenido=None ...)]
E  AssertionError: assert None == 'CI.4.18'
10 failed in 11.80s
```
  La guarda de descripción (`-k "misma_linea or fer_002"`, código sin ella):
  `E  AssertionError: assert ['CI.4.18', 'CI.4.18'] == [None, None]` → `2 failed, 10 deselected in 0.76s`.
  Con el código: `12 passed`; tests de la raíz que tocan `evals`: `1392 passed in 121.37s`.
- **Determinista recontado** (`a4d7653`): IA3 VERDE 8 · ROJO 51, **300 fallos** (386 − 86
  partidas); IA4 13 VERDE; E2E VERDE 7 · ROJO 52, **491** (563), 30 `partida_final`, todas
  «obtenido None» y 0 con partida distinta. FER-001 VERDE; RES-001..006 VERDE, RES-007 igual.
- **R28 con R38, recontado del texto de T14 sin pagar: 51 de 126 = 40,5 %** (ROJO). Sin
  además las 28 sintéticas `?`, que siguen contando: **23 de 98 = 23,5 %**, la cifra que el
  líder propone al humano como línea base en lugar del 20 %; R28 no cambia hasta que decida.
- **T14 no se recompara sin pagar:** el runner no guarda respuestas de sv5 ni envelopes.

## Review pasada 1 (`progress/review_F-084.md`): cambios aplicados

- **1 · R33 (opción a, del líder):** `runner.motivo_sin_lineas` (R18) y
  `sv5_valoracion.falta_documento` (R33); el determinista aplica solo R18; con
  LLM, R18 + R33; el comparador de F-083, R33 en IA3 e IA4 (`92b5e42`). Tres
  tests `test_f084_r33_*` nuevos (uno con los fixtures reales, índice con
  documento y sin caché); los dos de F-083 sobre el build real aíslan el índice (D4).
- **2 · C4:** T12 y T14 con su texto exacto en `progress/current.md` (+ O2, O3).
- **3 · D1 en la spec:** R20, R28, design §9 y T14 a `gpt-6.1-sol`, coherentes con
  `test_f084_r20_*`. **O5:** descripción de F-084 sin el texto anterior a la PARADA 1.

RED (código de `57c3c0c` con `runner.py`, `comparar_modelos.py` y
`sv5_valoracion.py` de antes; `python -m pytest tests/test_f084_runner.py
tests/test_f083_comparar_modelos.py -q -k "r33 or bloque_ia3_con or bloque_ia4_concilia"`):

```
E       assert False
E        +  where False = all(<generator object test_f084_r33_el_determinista_no_lee_el_documento_y_no_omite.<locals>.<genexpr> ...>)
E           AssertionError: IA3
E           assert (['HOR-001', 'HOR-002'], {}) == (['HOR-001'],...le en local'})
E        +  where False = all(<generator object test_f084_r33_el_determinista_de_los_7_res_no_depende_de_la_cache.<locals>.<genexpr> ...>)
FAILED tests/test_f084_runner.py::test_f084_r33_el_determinista_no_lee_el_documento_y_no_omite
FAILED tests/test_f084_runner.py::test_f084_r33_el_comparador_omite_el_caso_sin_documento_local
FAILED tests/test_f084_runner.py::test_f084_r33_el_determinista_de_los_7_res_no_depende_de_la_cache
3 failed, 3 passed, 74 deselected in 7.34s
```

Con el código nuevo: los 4 de R33 y los 2 de F-083, en verde.

## Mutación (T15)

- **1.ª campaña** (`d4b948a`, 195): 45 supervivientes, todos muertos por los
  `test_f084_t15_*` de `d4dbe97` (informe sustituido). **2.ª** (`d4dbe97`, 198):
  4 equivalentes en `sv5_documentos.py`, reescrito en `d0f91b1`.
- **Remedida** de `sv5_documentos.py` entero (`3ce021f`, 39): 0 supervivientes.
- **Remedida de la review 1** (`progress/mutacion_F-084_review1.md`, `57c3c0c`, 41
  líneas): **10 de 10 muertos**, 1 worker (dos intentos con 4 y 2, NO VÁLIDA por carga).
- **Remedida de T16** (`progress/mutacion_F-084_r37.md`, `daa6293`, diff desde
  `5f70189`, `comparador.py`): **8 mutantes, 8 muertos**, 1.828,9 s, 2 workers. Un
  intento anterior dejó 1 superviviente (`round(…, 6)` → `7`): se quitó el redondeo.
- **Remedida de T17** (`progress/mutacion_F-084_r39.md`, `a4d7653`, diff desde `83680ea`, 45
  líneas): **5 mutantes, 5 muertos**, 1.201,3 s, 2 workers. Supervivientes por aceptar: **ninguno**.
- Las cinco campañas de F-084 constan en `progress/inventario_mutacion_F-039.md`.

## Evidencias

| Evidencia | Valor |
|---|---|
| Tests ejecutados (`bash harness/init.sh` final, `52d6f5b`, tras T17) | raíz 1883 passed (272,7 s); sv1 205; sv2 485; sv3 1576; sv4 1774; sv5 96; sv6 473 (+1 skipped); sv9 673; comun en verde |
| Tests de F-084 | 214 (contratos 93 · contexto 49 · runner 31 · tolerancia 29 · partida 12) |
| Cobertura de las líneas cambiadas | `PUERTA COBERTURA: 98.6% de 638 líneas cambiadas cubiertas (629/638, umbral 80%, nivel critico)` |
| Mutación | Remedida de T17 (`progress/mutacion_F-084_r39.md`, `a4d7653`): **5 generados, 5 muertos, 0 supervivientes** · remedida de T16 (`progress/mutacion_F-084_r37.md`, `daa6293`): **8 generados, 8 muertos, 0 supervivientes** · remedida de la review 1 (`progress/mutacion_F-084_review1.md`, `57c3c0c`): **10 generados, 10 muertos, 0 supervivientes** · 2.ª campaña completa (`progress/mutacion_F-084.md`, `d4dbe97`): **198 generados, 194 muertos, 4 supervivientes** (equivalentes, analizados) · remedida del fichero afectado (`progress/mutacion_F-084_sv5_documentos.md`, `3ce021f`): **39 generados, 39 muertos, 0 supervivientes**. 1.ª campaña (195, 45 supervivientes) sustituida: ver «Mutación» |
| Tiempo de la suite raíz | 272,7 s (dentro de init.sh) |
| `bash harness/init.sh` | `ENTORNO LISTO. Puedes trabajar.` (exit 0; PUERTA TAMAÑO requirements 150/150, design 250/250, impl 216/220, review 135/140; ruff 1364 avisos de deuda previa, no bloquea) |
