<!-- progress/impl_F-084.md -->
# F-084 · Informe del implementer — el banco de evals valora de verdad

Rama `feature/F-084-banco-valoracion` (worktree `../albaranes-F-084`), `dev`
`ac34ad8` fusionado (F-083, F-085, altas F-086..F-090). Rigor `critico`.
Servicios tocados: **ninguno** (solo `evals/` y tests). T1–T11 y T15 hechas;
**T12 y T14 son MANUAL del humano** (comandos al final); T13 espera a T12.

## Qué cambió

| Fichero | Cambio |
|---|---|
| `evals/procesos/sv6_build.py` | `lineas_albaran_de` (descuento, precio neto, importe derivado en `Decimal`, `DescuentoCompuesto`) y `clasificacion_de` con `MAPA_FAMILIA_DOCUMENTO`; el envelope estimulado las usa y lleva `clasificacion` (R12–R14). Estímulo de matches sin cambios. |
| `evals/revision/escritura.py` | Clave de `contrato_lineas` = (`caso_id`, `codigo_producto`, `linea_sigrid`) (R11). |
| `evals/contratos.py` (nuevo) | CLI `lineas` (sigrid-api → `INPUTS.xlsx`) y `documentos` (BBDD + SharePoint → caché e índice); `LectorSigrid` con reintentos tenacity; informe `progress/import_F-084.md` (R1–R11, R29–R31, R34). |
| `evals/procesos/sv5_documentos.py` (nuevo) | Subproceso con sv5 en `sys.path`: `_SQL_CONTRATO_HEADER` de sv5 en sesión `default_transaction_read_only=on`, descargador de sv5, MD > PDF, `MAX_PDF_MB` = 40; credenciales por entorno, no por stdin. |
| `evals/procesos/sv5_valoracion.py` | `documento_de` (sha256 contra el índice, R32/R33); `construir_contexto` con cabecera del índice, `lineas_albaran_de`, `clasificacion_de` y documento; subproceso: `Raw*` + `UnitCategoryPrefilter` + `ClasificacionAlbaran`, `preparar_contexto`, MD como `contrato_markdown` / PDF como adjunto, `modelo` en el trabajo y en la salida, `valorar_casos` como puerta del subproceso. |
| `evals/procesos/sv5_modelos.py` | La línea de `preparar_contexto` en su `main` (design §8). |
| `evals/runner.py` | R18, R33 y R13 en las dos corridas antes de montar sv5/sv6; R19 (`fases` sin IA1/IA2 ⇒ sin sv2 ni sus claves; las de sv5 se exigen antes de nada); R20 `valoracion_por_defecto`; R17/R21 en las fases. |
| `evals/modelos.py`, `evals/informe.py` | `ResultadoFase.modelos` y `.documentos`; `- Modelo: …`, `- Documento del contrato: md N · pdf N · ninguno N` y la advertencia de emparejamiento del determinista (R36). Líneas parseables idénticas. |
| `evals/README.md` | Sección de F-084 (R26). `azure-apps/albaranes.md` §8: commit local `a6bc26a`, **sin push**. |
| Tests | `tests/test_f084_{contratos,contexto_valoracion,runner}.py` (170 tests). Ajuste en 2 tests de F-083 y 1 doble de F-048 (D2). |

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
  runner lo lee de ahí; `construir_contexto` sin índice explícito lee el
  versionado (el comparador de F-083 hereda contexto y documento).
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
- R18 no se aplica en el comparador de F-083 (la spec no lo pide).

## MANUAL del humano: T12 y T14 (PowerShell)

Claves y contraseña solo con `Read-Host -AsSecureString`, nunca en fichero.
Ningún paso escribe en Sigrid, la BBDD ni SharePoint: solo libro, caché e índice locales.

### T12 · Importar contratos, convertir y determinista (solo lee)

Los libros viven en el árbol principal (no versionados): se leen con `--ground-truth`.

```powershell
cd C:\Users\pgris\PycharmProjects\albaranes-F-084
$gt = "C:\Users\pgris\PycharmProjects\albaranes\evals\ground_truth"
$env:PYTHONPATH = "$PWD\services\albaranes-comun"

# 1. Líneas de contrato desde sigrid-api (solo lectura)
$env:SIGRID_API_BASE_URL = "<url de sigrid-api>"
$env:SIGRID_API_DATABASE = "ruesma"
$s = Read-Host -AsSecureString "SIGRID_API_FUNCTION_KEY"
$env:SIGRID_API_FUNCTION_KEY = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($s))
python -m evals.contratos lineas --ground-truth $gt --dry-run
#    VERDE: progress\import_F-084.md sin contratos fallidos (o con motivo aceptado)
python -m evals.contratos lineas --ground-truth $gt

# 2. Cabecera y documento: BBDD albaranes de AZURE (el .env apunta a local) y SharePoint
Push-Location C:\Users\pgris\PycharmProjects\albaranes\infra
. .\00_vars.ps1; . .\00_capps_vars.ps1
Pop-Location
$env:PG_HOST = $PG_HOST; $env:PG_PORT = "5432"; $env:PG_DB = $PG_DB; $env:PG_USER = $PG_ADMIN
foreach ($k in $SP.Keys) { Set-Item "Env:$k" $SP[$k] }
$s = Read-Host -AsSecureString "PG_PASSWORD"
$env:PG_PASSWORD = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($s))
$s = Read-Host -AsSecureString "GRAPH_KEY"
$env:GRAPH_KEY = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($s))
python -m evals.contratos documentos
#    VERDE: evals\fixtures\contratos\_indice.json con un tipo por contrato

# 3. Libros -> fixtures y corrida determinista (sin red)
python -m evals.conversor --ground-truth $gt
python -m evals.runner --feature F-084

Remove-Item Env:SIGRID_API_FUNCTION_KEY, Env:PG_PASSWORD, Env:GRAPH_KEY
```

La sesión de BBDD es de solo lectura aunque el usuario sea el de la app. Si el
barrido del conversor salta con un texto de contrato, se redacta en el libro.
Criterio T12: informe sin contratos fallidos (o motivo aceptado), `tipo` por
contrato en el índice y R27 en `progress\evals_F-084.md`. T13 la hace el
implementer. Tras fusionar en `dev`, copiar la caché (sin ella, R33 omite):

```powershell
Copy-Item -Recurse -Force C:\Users\pgris\PycharmProjects\albaranes-F-084\evals\inputs\contratos C:\Users\pgris\PycharmProjects\albaranes\evals\inputs\
```

### T14 · Línea base con LLM (CUESTA DINERO), después de T13

Con el modelo de producción vigente tras F-085: IA3 e IA4 = `openai`
`gpt-6.1-sol` (desviación D1). Sin `--proveedores`, el runner usa justo eso.

```powershell
cd C:\Users\pgris\PycharmProjects\albaranes-F-084
$env:PYTHONPATH = "$PWD\services\albaranes-comun"
Remove-Item Env:IA3_PROVIDER -ErrorAction SilentlyContinue
$env:OPENAI_MODEL = "gpt-6.1-sol"

# Estimación sin claves ni llamadas (sale con 0)
python -m evals.comparar_modelos --fase IA3 --modelos gpt-6.1-sol --estimar

$s = Read-Host -AsSecureString "OPENAI_API_KEY"
$env:OPENAI_API_KEY = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($s))
# Humo: 3 casos (el informe dice el coste real; con el documento el prompt crece)
python -m evals.runner --con-llm --fases IA3,IA4,E2E --casos ALQ-001,GEN-002,RES-010 --feature F-084-humo
# Los 59
python -m evals.runner --con-llm --fases IA3,IA4,E2E --feature F-084
Remove-Item Env:OPENAI_API_KEY
```

Criterio (R28; puede salir ROJO): 0 casos ERROR, `- Modelo: gpt-6.1-sol` en
IA3, IA4 y E2E de `progress\evals_F-084.md`, y «obtenido None» ≤ 20 % de los
fallos críticos de IA3 de los casos evaluados. La cifra va a este informe como
línea base.

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
  Supervivientes pendientes de aceptar por el humano: **ninguno**.
- Las dos campañas de F-084 constan en `progress/inventario_mutacion_F-039.md`.

## Evidencias

| Evidencia | Valor |
|---|---|
| Tests ejecutados (`bash harness/init.sh` final, `9248c63`, tras fusionar `dev`) | raíz 1839 passed (330,7 s); sv1 205; sv2 485; sv3 1576; sv4 1774; sv5 96; sv6 473 (+1 skipped); sv9 673; comun en verde |
| Tests de F-084 | 170 (contratos 93 · contexto 49 · runner 28) |
| Cobertura de las líneas cambiadas | `PUERTA COBERTURA: 98.5% de 598 líneas cambiadas cubiertas (589/598, umbral 80%, nivel critico)` |
| Mutación | 2.ª campaña completa (`progress/mutacion_F-084.md`, `d4dbe97`): **198 generados, 194 muertos, 4 supervivientes** (equivalentes, analizados) · remedida del fichero afectado (`progress/mutacion_F-084_sv5_documentos.md`, `3ce021f`): **39 generados, 39 muertos, 0 supervivientes**. 1.ª campaña (195, 45 supervivientes) sustituida: ver «Mutación» |
| Tiempo de la suite raíz | 330,7 s (dentro de init.sh) |
| `bash harness/init.sh` | `ENTORNO LISTO. Puedes trabajar.` (exit 0; PUERTA TAMAÑO impl 220/220) |
