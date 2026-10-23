<!-- progress/impl_F-084.md -->
# F-084 · Informe del implementer — el banco de evals valora de verdad

Rama `feature/F-084-banco-valoracion` (worktree `../albaranes-F-084`), `dev`
`416b55c` fusionado (F-083, F-085, altas hasta F-098). Rigor `critico`.
Servicios tocados: **ninguno** (solo `evals/` y tests). T1–T11, T13, T15 y T16
hechas, y los 3 cambios de la review pasada 1; T12 y T14 las lanzó el humano el
2026-10-23 (comandos en `progress/current.md`).

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
| `evals/comparador.py`, `evals/criticidad.json` | R37 (T16): 0,05 € de tolerancia, en `Decimal`, en los importes y precios valorados (`CAMPOS_CON_TOLERANCIA_EUR`); IA1 exacta; en `criticidad.json`, solo una nota. |
| `evals/modelos.py`, `evals/informe.py` | `ResultadoFase.modelos` y `.documentos`; `- Modelo: …`, `- Documento del contrato: md N · pdf N · ninguno N` y la advertencia de emparejamiento del determinista (R36). Líneas parseables idénticas. |
| `evals/README.md` | Sección de F-084 (R26). `azure-apps/albaranes.md` §8: commit local `a6bc26a`, **sin push**. |
| Tests | `tests/test_f084_{contratos,contexto_valoracion,runner,tolerancia_importes}.py` (202 tests). Ajuste en 2 tests de F-083 y 1 doble de F-048 (D2); los 2 de F-083 sobre el build real aíslan el índice (D4). |

## Decisiones de diseño

- **Descuento en `Decimal`**: el `COALESCE` de sv5 calcula en `numeric`; en
  float 50 × 0,647 × 0,60 da 19,409999…, en `Decimal` 19,41 exacto.
- **`descuentos` del conversor** llega como número, lista (`a;b`) o texto: los
  tres caminos; `?`/vacío = sin descuento; más de un valor = R13.
- **R13 en el runner**: con LLM, IA3 `ERROR` e IA4/E2E `OMITIDO` («no se
  valoró · …»); en el determinista, IA3 y E2E `ERROR` e IA4 `OMITIDO`.
- **R9**: la fecha que falta se escribe para cualquier caso pedido sin
  `fecha_albaran`, no solo los importados (nunca pisa una existente).
- **`preparar_contexto` por costura**: `ejecutar_trabajo(trabajo, fabrica,
  preparar)` sigue sirviendo al test in-process de F-083 (sin sv5 importable);
  el subproceso entra por `valorar_casos`, que pasa `preparar_contexto`. Los
  tests de T7 entran por esa misma puerta en un subproceso con doble de LLM.
- **El índice va con los fixtures** (`<fixtures>/contratos/_indice.json`) y el
  runner lo lee de ahí; `construir_contexto` y `falta_documento` sin índice
  explícito leen el versionado (el comparador de F-083 hereda contexto,
  documento y R33).
- **Informe compartido** `progress/import_F-084.md`, una sección por subcomando.
  Sin escritura en sistemas: sigrid-api solo `sql/read`, BBDD de solo lectura.
- **Costuras por T15**: `LectorSigrid(dormir=…)`, `_sesion_real(crear, abrir)` y
  `_descargador_real(clase)` dejan probar reintentos, techo de espera y el
  montaje real sin conectar; se quitan `future`/`pool_pre_ping` (sesión de un uso).

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

- **D5 (propuesta, sin código):** cómo contar R28; ver «T14». IA4 usa el
  proveedor de IA3, como antes.
- **Emparejamiento como lo describe el humano** (solo IA4, prefiltro de precio
  ±0,02 € y partida, y luego significado): feature aparte que propone el líder.
- R18 no se aplica en el comparador de F-083 (la spec no lo pide); R33 sí.

## T12 (humano) y T13: línea base determinista (`b39cb0e`)

T12, 2026-10-23: `lineas` 18 contratos y 0 fallidos (3159 filas, 52 fechas);
`documentos` 20: md 1, pdf 6 y ninguno 13 (los 13, «no está en
albaran_contratos_merge»: **30 de los 59 casos van a T14 sin documento**); 6
libros y 264 ficheros. T13 versiona `evals/fixtures/inputs/` (60 ficheros), el
índice y `progress/import_F-084.md`. Barrido de lo añadido: sin URL, correo,
GUID, clave, IBAN, NIF de persona ni teléfono; los «IPv4» son partidas; los 7
CIF son de sociedades (O3). La caché sigue ignorada.

- **R27, verde:** 0 OMITIDO por R18; FER-001 `importe_calculado` 19,41 sin
  fallo (le queda `codigo_partida_final`); advertencia de R36 en las tres fases.
- **Determinista** (`python -m evals.runner --feature F-084`, ROJO): IA3 59
  evaluados, VERDE 6, ROJO 53, **394 fallos**; IA4 13 evaluados, VERDE 13, 46
  OMITIDO («sin caso en el libro IA4»); E2E VERDE 6, ROJO 53, **572 fallos**;
  0 ERROR. RES-001..007 igual que antes (RES-007 IA3 4 y E2E 6).
- **Línea base con R37** (`daa6293`): IA3 **386 fallos** (−8), E2E **563** (−9);
  mismos estados por caso (FER-002 IA3 15 → 8, FER-003 6 → 5); 0 de redondeo.
- **«obtenido None»: R36, no el estímulo.** 385 de 394 en IA3 (103 líneas): 77
  con el código de contrato en `?` en el libro y 26 `no_match`; **ninguna** con
  un código presente en las líneas importadas. El estímulo solo empareja lo que
  el libro afirma (P2 = b); el resto lo mide T14.
- **Redondeo → R37 (T16; decisión del humano, opción a):** IA3 7 en FER-002
  (17,59 frente a 17,5932 = 54 × 0,543 × 0,60) y 1 en FER-003 (95,481 frente a
  95,479167); E2E, lo mismo y el total de FER-002 (139,65 frente a 139,66). El
  libro anota el papel en céntimos y sv6 no redondea sin importe declarado: el
  libro no está mal. Ahora el banco tolera 0,05 € ahí; producción no cambia.

## T14 (humano): línea base con LLM, `gpt-6.1-sol` (detalle: `progress/impl_F-084_T14.md`)

Informes del runner fuera de git (precios de proveedor); aquí, solo recuentos.
IA3 59 evaluados, 0 ERROR, ROJO 58 · VERDE 1, **212 fallos**, 137 «obtenido None»;
IA4 13 evaluados (46 OMITIDO), ROJO 13, 27 fallos; E2E ROJO 52 · VERDE 7, **312**.
Modelo en las tres fases; documento md 5 · pdf 24 · ninguno 30. Coste real: no
consta (el runner no mide tokens). Humo: IA3 19, IA4 3, E2E 23. Frente al
determinista: IA3 386 → 212 y líneas sin precio 91 → 8.

- **R28 en ROJO: 137 de 212 = 64,6 %.** 86 son `codigo_partida_final`, que IA3 no
  produce: la pone sv6 desde la partida del albarán, y INPUTS la trae vacía en
  las 110 líneas (E2E tampoco la observa). Sin ellas: 40,5 %. 28 son filas de
  sintéticas con `rol_linea` en `?` en el libro, que no pueden casar. Sin ambas:
  23 de 98 = 23,5 %. **D5** (decide el humano o el reviewer): partida no
  observable en IA3 y la de IA1 a INPUTS para E2E. Criterio sin cambiar.
- **Valoración frente a emparejamiento** (según el código de hoy): IA3 76 de
  valoración y 20 de emparejamiento, IA4 27 de emparejamiento. El banco apenas
  mide el emparejamiento: IA4 solo tiene 13 casos con libro.

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
  Supervivientes pendientes de aceptar por el humano: **ninguno**.
- Las cuatro campañas de F-084 constan en `progress/inventario_mutacion_F-039.md`.

## Evidencias

| Evidencia | Valor |
|---|---|
| Tests ejecutados (`bash harness/init.sh` final, `6cbc716`, tras T16, T13, la review 1 y `dev` `416b55c`) | raíz 1871 passed (331,9 s); sv1 205; sv2 485; sv3 1576; sv4 1774; sv5 96; sv6 473 (+1 skipped); sv9 673; comun en verde |
| Tests de F-084 | 202 (contratos 93 · contexto 49 · runner 31 · tolerancia 29) |
| Cobertura de las líneas cambiadas | `PUERTA COBERTURA: 98.5% de 618 líneas cambiadas cubiertas (609/618, umbral 80%, nivel critico)` |
| Mutación | Remedida de T16 (`progress/mutacion_F-084_r37.md`, `daa6293`): **8 generados, 8 muertos, 0 supervivientes** · remedida de la review 1 (`progress/mutacion_F-084_review1.md`, `57c3c0c`): **10 generados, 10 muertos, 0 supervivientes** · 2.ª campaña completa (`progress/mutacion_F-084.md`, `d4dbe97`): **198 generados, 194 muertos, 4 supervivientes** (equivalentes, analizados) · remedida del fichero afectado (`progress/mutacion_F-084_sv5_documentos.md`, `3ce021f`): **39 generados, 39 muertos, 0 supervivientes**. 1.ª campaña (195, 45 supervivientes) sustituida: ver «Mutación» |
| Tiempo de la suite raíz | 331,9 s (dentro de init.sh, con los 59 casos ya con contrato) |
| `bash harness/init.sh` | `ENTORNO LISTO. Puedes trabajar.` (exit 0; PUERTA TAMAÑO requirements 150/150, design 245/250, impl 220/220) |
