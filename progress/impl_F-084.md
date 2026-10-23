<!-- progress/impl_F-084.md -->
# F-084 · Informe del implementer — el banco de evals valora de verdad

Rama `feature/F-084-banco-valoracion` (worktree `../albaranes-F-084`), `dev`
`416b55c` fusionado (F-083, F-085, altas hasta F-098). Rigor `critico`.
Servicios tocados: **ninguno** (solo `evals/` y tests). T1–T11 y T15 hechas, y
los 3 cambios de la review pasada 1; **T12 y T14 son MANUAL del humano**
(comandos en `progress/current.md`); T13 espera a T12.

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
| `evals/modelos.py`, `evals/informe.py` | `ResultadoFase.modelos` y `.documentos`; `- Modelo: …`, `- Documento del contrato: md N · pdf N · ninguno N` y la advertencia de emparejamiento del determinista (R36). Líneas parseables idénticas. |
| `evals/README.md` | Sección de F-084 (R26). `azure-apps/albaranes.md` §8: commit local `a6bc26a`, **sin push**. |
| Tests | `tests/test_f084_{contratos,contexto_valoracion,runner}.py` (173 tests). Ajuste en 2 tests de F-083 y 1 doble de F-048 (D2); los 2 de F-083 sobre el build real aíslan el índice (D4). |

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

- **D1 · R20/R28/T14 (instrucción del líder):** el defecto no es `claude` ni
  `claude-opus-4-8` sino la referencia de IA3 de `evals/precios_modelos.json`
  (`openai` / `gpt-6.1-sol`, la que R3 de F-083 ata a `infra/create_capps.ps1`
  tras F-085). `IA3_PROVIDER` y la variable de modelo del proveedor mandan si
  están. Cumple P6 = (a); solo cambia el literal anterior a F-085. T14 se lanza
  con `gpt-6.1-sol`. No es contradicción no trivial: no se ha bloqueado.
- **D2 · R18 frente a tests ajenos:** `test_f083_runner_evaluar_valoracion_
  coincide_con_el_modo_determinista` y `test_f083_bloque_ia3_con_la_ia4_del_libro`
  comparaban en FER-001/GEN-001/HOR-005 (sin líneas: ahora OMITIDO); pasan a
  RES-001/004/006, misma intención. El doble de `construir_contexto` de
  `test_f048_evals_fallos_aislados.py` acepta `**_`. Ninguna expectativa cambia.
- **D4 · R33, opción (a)** (cambio 1 de la review): ver «Review pasada 1».
- **Hasta T12 el determinista omite 52 casos** (R18, lo pedido). **D3 · `dev` `2721e06` fusionado** (banco IA1 corregido): solo cambian claves `IA1.*` de `afirmado_por_el_humano_RES.json`; el guardián de R24 pasa a fijar lo afirmado fuera de IA1 (idéntico a `efd73b7`) y RES-001..007 dan los mismos fallos (RES-007 IA3 4, E2E 6); los ajustes D2 siguen valiendo.

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

## Verificación (resultado real)

- T1: FER-001 determinista por el subproceso real de sv6 → `importe_calculado` 19,41.
- T2: `pytest tests/ -k f045` → `296 passed` sin tocar expectativas.
- T7 (doble de LLM en subproceso): RES-001 usa `valuation_residuos` y el texto lleva
  descuento, `"unidad_categoria": "count"`, fecha, cabecera y el MD; un PDF va adjunto.
- T11: determinista en `efd73b7` y HEAD, RES-001..007 idénticos (001–006 VERDE; RES-007
  IA3 4 y E2E 6 fallos en los dos, detalle igual). Totales: base ROJO 106 · OMITIDO 46 ·
  VERDE 25; HEAD ROJO 2 · OMITIDO 163 · VERDE 12 (los OMITIDO nuevos son R18 hasta T12).
- Humo del subproceso real de documentos sin red (`contratos: []`, entorno
  falso) → `{'resultados': []}`; `python -m evals.contratos --help` correcto.

## Fuera del alcance / pendiente

- **T12 y T14**: MANUAL del humano (comandos abajo). **T13** (versionar los
  fixtures regenerados y el índice, y comprobar R27) la hace el implementer
  después de T12. R27 y R28 quedan sin verificar hasta entonces.
- IA4 usa el mismo proveedor que IA3 (`IA4_PROVIDER` aparte: fuera, como antes).
- R18 no se aplica en el comparador de F-083 (la spec no lo pide); R33 sí.

## MANUAL del humano: T12 y T14

Comandos exactos de PowerShell en `progress/current.md` (bloque «F-084 · MANUAL
del humano»), con `az login` como requisito (O2), el script del líder fuera del
repo como forma cómoda de T12 y el repaso de `cif_proveedor`/`nombre_proveedor`
del índice antes de T13 (O3). Claves y contraseña solo con
`Read-Host -AsSecureString`; nada escribe en Sigrid, la BBDD ni SharePoint.

- **T12** (gratis, solo lee): `evals.contratos lineas --dry-run` → `lineas` →
  `documentos` → conversor → determinista. Criterio: informe sin contratos
  fallidos (o motivo aceptado), `tipo` por contrato en el índice y R27.
- **T14** (de pago, tras T13): `openai` `gpt-6.1-sol` (D1, **pendiente de
  confirmación del humano**); estimación, humo de 3 casos y los 59. Criterio
  R28: 0 ERROR, `- Modelo: gpt-6.1-sol` en IA3/IA4/E2E y «obtenido None»
  ≤ 20 % de los fallos críticos de IA3. La cifra vuelve aquí como línea base.

## Review pasada 1 (`progress/review_F-084.md`): cambios aplicados

- **1 · R33 (opción a, del líder):** `runner.motivo_sin_lineas` (R18) y
  `sv5_valoracion.falta_documento` (R33, mismos defectos que
  `construir_contexto`); el determinista aplica solo R18 y ya no lee el
  índice; la corrida con LLM, R18 + R33; el comparador de F-083, R33 en IA3 e
  IA4. Spec: R33 y design §4/§6/§11. `92b5e42`.
  Tests nuevos: `test_f084_r33_el_determinista_no_lee_el_documento_y_no_omite`,
  `test_f084_r33_el_comparador_omite_el_caso_sin_documento_local` y
  `test_f084_r33_el_determinista_de_los_7_res_no_depende_de_la_cache` (copia de
  los fixtures reales + índice con documento para CTSU24/0228 y CTSU24/0402, sin
  caché: los 7 RES sin OMITIDO y sin empeorar). Los dos tests de F-083 sobre el
  build real llevan `sin_documentos` (índice aislado): miden la equivalencia con
  el determinista, que no lee el documento (D4).
- **2 · C4:** T12 y T14 con su texto exacto en `progress/current.md` (+ O2, O3).
- **3 · D1 en la spec:** R20, R28, design §9 y T14 a `openai` `gpt-6.1-sol`,
  coherentes con `test_f084_r20_*`; el modelo de la línea base, pendiente de
  confirmación del humano. **O5:** descripción de F-084 sin el texto anterior a
  la PARADA 1. `57c3c0c`.

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

- **1.ª campaña** (`d4b948a`, 195): 150 muertos, **45 supervivientes**, todos
  con test nuevo `test_f084_t15_*` en `d4dbe97` (reintentos y techo de espera de
  `LectorSigrid`, `ok=true`, R10 a 4 decimales, sin cambios = sin copia,
  `asegurar_columna`, secciones e índice del informe, MD vacío, tope del PDF,
  sesión/descargador/subproceso reales, hueco en `descuentos`); el `ensure_ascii`
  del `contexto_linea_json` era equivalente y se quitó. Su informe se sustituyó.
- **2.ª campaña** (`d4dbe97`, 198): 4 supervivientes en dos líneas de
  `sv5_documentos.py`, equivalentes (análisis escrito en el informe); el código
  se reescribe en `d0f91b1` para que dejen de serlo.
- **Remedida** de `sv5_documentos.py` entero (`3ce021f`, 39): 0 supervivientes.
- **Remedida de la review 1** (`progress/mutacion_F-084_review1.md`, `57c3c0c`,
  diff desde `1839b8c`: 41 líneas, 3 ficheros): **10 mutantes, 10 muertos**,
  2.065,1 s, 1 worker (con 4 y con 2 la línea base agotó los 600 s por suites
  de otros proyectos en la máquina: dos intentos NO VÁLIDA, no versionados).
  Supervivientes pendientes de aceptar por el humano: **ninguno**.
- Las tres campañas de F-084 constan en `progress/inventario_mutacion_F-039.md`.

## Evidencias

| Evidencia | Valor |
|---|---|
| Tests ejecutados (`bash harness/init.sh` final, `ad02d1c`, tras la review 1 y `dev` `416b55c`) | raíz 1842 passed (376,3 s); sv1 205; sv2 485; sv3 1576; sv4 1774; sv5 96; sv6 473 (+1 skipped); sv9 673; comun en verde |
| Tests de F-084 | 173 (contratos 93 · contexto 49 · runner 31) |
| Cobertura de las líneas cambiadas | `PUERTA COBERTURA: 98.5% de 606 líneas cambiadas cubiertas (597/606, umbral 80%, nivel critico)` |
| Mutación | Remedida de la review 1 (`progress/mutacion_F-084_review1.md`, `57c3c0c`): **10 generados, 10 muertos, 0 supervivientes** · 2.ª campaña completa (`progress/mutacion_F-084.md`, `d4dbe97`): **198 generados, 194 muertos, 4 supervivientes** (equivalentes, analizados) · remedida del fichero afectado (`progress/mutacion_F-084_sv5_documentos.md`, `3ce021f`): **39 generados, 39 muertos, 0 supervivientes**. 1.ª campaña (195, 45 supervivientes) sustituida: ver «Mutación» |
| Tiempo de la suite raíz | 376,3 s (dentro de init.sh, con suites de otros proyectos en la máquina) |
| `bash harness/init.sh` | `ENTORNO LISTO. Puedes trabajar.` (exit 0; PUERTA TAMAÑO requirements 150/150, design 238/250, impl 201/220) |
