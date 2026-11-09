<!-- progress/impl_F-112.md -->
# F-112 · Informe del implementer (T1–T8)

Rama `feature/F-112-anio-fecha-albaran`, worktree `../albaranes-F-112` (lleva `dev` en `852fa93`), rigor
**estandar**. Spec v1.3 con PARADA 1 cerrada (D1, D3–D6, D9 = a; D2 = b, día en Europe/Madrid; D7 = 416).
T9–T13 no son mías. Nada contra Azure, BBDD, Blob, Sigrid ni LLM reales. Sin push.

## 0. Estado

**T1–T8 hechas** (un commit por tarea). `bash harness/init.sh` (con `ARNES_SIN_CACHE=1` y `PYTHONPATH` a la
comun del worktree) **en verde, EXIT=0**: PUERTA COBERTURA 99,8 % (545/546). La puerta de rutas sensibles da
el AVISO esperado (falta `progress/evals_F-112.md`: es T11, del humano, de pago). Ningún fichero ajeno a F-112
en la puerta de cobertura: la spec no trajo scripts de medición.

La spec casa con el código actual (tras el `dev` de 297 commits): sv2 tiene `_render_task_fase_1`,
`_MARCADORES_FASE_2` con pasada única, `{empresas_cliente}` antes del correo y los cuatro prompts de fase 2
con `{prompt_fase_1}`/`{revision_rules}`/`{sigrid_context}`, tal como describe design §1. Lo único que no
casaba es la numeración de la regla de ARCHITECTURE (§3, D-1).

## 1. Ficheros tocados

| Fichero | Cambio |
|---|---|
| `services/albaranes-api/application/services/fecha_recepcion.py` | **nuevo** (T1): marcadores, `ZONA_RECEPCION`, `REGLA_DEL_ANIO` (una constante), `fecha_recepcion_de`, `render_fecha_recepcion`, `render_revision_fecha`, `NOTA_SIN_RECEPCION`, `NOTA_REVISION_SIN_RECEPCION` |
| `infra/manifests/sv2/requirements.txt` | `tzdata>=2024.1` (R30) |
| `services/albaranes-api/application/services/albaran_extraction_service.py` | `_render_task_fase_1(..., fecha_recepcion=None)` (antes del correo, sin marcador nada); `fecha_recepcion` en `extract_phase_1` y `review_phase_2`; `revision_fecha` en `_MARCADORES_FASE_2` y en la pasada única; `fecha_recepcion=` en los dos logs (`_resumen_fecha`) |
| `services/albaranes-api/application/pipelines/extract_albaran_pipeline.py` | campo `fecha_recepcion` en las dos requests y paso al servicio (R12) |
| `services/albaranes-api/interface_adapters/worker/extraction_worker.py` | `fecha_recepcion_de(correo)` una vez tras `_leer_correo`, la misma a las dos fases (R13, R14) |
| `services/albaranes-api/config/prompts.yaml` | regla de `fecha` + `{fecha_recepcion}` en `albaran_factura_es` (§4.1); sección «Fecha del albarán (revisión obligatoria)» con `{revision_fecha}` y el ejemplo fijo en los cuatro `albaran_revision_fase2_*`, tras la checklist y antes del grounding (§4.2). `revision_rules.yaml` sin tocar |
| `harness/rutas_sensibles.json` | `fecha_recepcion.py` en la verificación `evals` (R25) |
| `evals/procesos/sv2_fecha.py` | **nuevo**: `fecha_de`, `dos_fases(..., referencia)`, `montar_extractor` (reutiliza `sv2_proveedor`) |
| `evals/comparar_fecha.py` | **nuevo**: juegos A–D, clasificación, mayoría, efecto de IA2, veredicto C1–C7, paradas, `--solo-validar`, informes |
| `evals/casos_fecha.json` | **nuevo**, `{"version": 1, "casos": []}` (lo rellena T9) |
| `evals/sinteticos_fecha.py`, `evals/casos_fecha_sinteticos.json` | **nuevos** (T6b): SIN-001…006 y su JSON versionado |
| `docs/ARCHITECTURE.md` (regla **28**), `services/albaranes-api/sv2.md` (§10.9), `evals/README.md` («Comparar la fecha») | T7 (R26) |
| Tests nuevos | sv2: `test_f112_fecha_recepcion.py` (34), `test_f112_render_prompt.py` (15), `test_f112_worker.py` (11), `test_f112_prompt_yaml.py` (30); raíz: `test_f112_rutas_sensibles.py` (3), `test_f112_comparar_fecha.py` (82), `test_f112_sinteticos_fecha.py` (7) |
| Tests viejos tocados | `test_f064_prompt_ia1_proveedor.py` (ancla, §3 D-2); `test_f011_r19_r20_declaracion.py` (+1 ruta declarada, §3 D-3) |
| `progress/current.md`, `specs/.../tasks.md` | estado; T1–T8 `[x]` |

Commits: `e14700b` T1, `c7ee6ac` T2, `a0c0b93` T3, `096e725` T4, `248bcd3` T5, `2b21698` T6, `7b8d348` T6b,
`823ba87` T7, `618c46c` complemento de T5 + current.md. T8 = este informe y el init en verde.
`azure-apps/` no se toca: sv2 no cambia lo que expone ni lo que consume (design §6).

## 2. Decisiones de diseño

- **`fecha_recepcion_de`**: `getattr(correo, "recibido_utc")`; no-texto o vacío ⇒ `None`; 10 caracteres ⇒
  `date.fromisoformat` (fecha sola, tal cual); si no, `datetime.fromisoformat` (acepta `Z` en 3.12), sin zona ⇒
  UTC, `.astimezone(ZoneInfo("Europe/Madrid")).date()`. Cualquier `ValueError` ⇒ `None`.
- **Textos**: los de design §4.1/§4.2 con los saltos de línea de presentación unidos en frases; un `\n` antes
  de «El día y el mes…» / «Si la fecha de fase 1…». La Regla del año va por f-string desde la constante del
  módulo (un test cambia la constante y ve el cambio en los dos bloques).
- **Log**: `fecha_recepcion=` va **antes** de `correo=`: `test_f048_r14` exige que la línea de fase 2 acabe en
  `correo=NO`.
- **YAML de fase 2**: la sección lleva una frase fija («NO es una regla más de la checklist: hazla SIEMPRE, sea
  cual sea la familia») y el ejemplo de §4.2 (2020-10-17 ⇒ 2026-10-17, «17/10/26»).
- **Comparador** (lo que la spec deja abierto):
  - A y D sacan la referencia con `fecha_recepcion_de` de sv2 **cargando el fichero por ruta**
    (`importlib`): meter sv2 en `sys.path` chocaría con los `application` de sv3/sv6 en la suite de la raíz.
    En A el campo es `recibido` (design §7.1), fecha o fecha-hora.
  - B: muestra de 20 sobre los casos de `fixtures/IA1` con fecha válida, `random.Random(20261030)`; el banco
    real da B = 20 y C = 13 (lo fija un test). Clave de resultados `juego/caso_id` (un caso puede estar en B y C).
  - Variante `base` con `sin_pie=False`: F-112 no cambia el schema y `dev` ya trae el pie de F-075 (en
    `comparar_proveedor` la base era anterior a F-075).
  - C2 y C3 se miden **tras IA2** (la fecha final), como C1, C6 y C7. C4 cuenta las dos fases.
  - Efecto de IA2: si alguna fase falla, la ejecución no entra en la tabla (`None`).
  - VERDE exige además los **cuatro juegos**: con un subconjunto, `NO APLICA` (C1/C6 no se podrían juzgar).
    C1 sin ningún `anio` y C6 sin ningún D son KO (evita un VERDE vacío mientras `casos_fecha.json` esté vacío).
  - `--solo-validar` comprueba también el `git show` de la base si la variante la incluye (con
    `--variante rama`, T9, no).
  - Mensajes de parada: posición del caso y campo, nunca valores ni `caso_id` (R23).

## 3. Desviaciones respecto a la spec (justificadas)

- **D-1 · Regla 28, no 26.** R26/T7 dicen «regla 26», pero en `dev` la 26 ya es de F-115 y la 27 de F-111
  (entraron después de la spec). Se añade como **28**, el contenido es el de R26. Si el líder prefiere otra
  numeración es renombrar una línea.
- **D-2 · Ancla de `test_f064_prompt_ia1_proveedor`.** R16 cambia «- fecha: la del albarán.» por la regla
  nueva; tres anclas de ese test buscaban el literal con punto. Pasan a «- fecha: la del albarán» (prefijo
  común); ninguna aserción relajada. Sin el cambio caían 6 tests (comprobado con `git stash`).
- **D-3 · `test_f011_r19` declara la ruta nueva.** Ese test fija la lista de rutas sensibles; T5 añade una y
  la lista gana `fecha_recepcion.py` (igual que hizo F-064 con `empresas_cliente.py`). Se me pasó en T5 y lo
  cazó el primer `init.sh`: commit aparte «F-112: …complemento de T5».
- **D-4 · Papel de los sintéticos sin tildes** («PROVEEDOR SINTETICO, S.L.», «ALBARAN»): la fuente por defecto
  de Pillow no tiene tildes y pintaba cajas. La fecha, único dato variable, no cambia. Pillow está en el
  `.venv` como dependencia transitiva (reportlab, pdfplumber); no se declara en ningún manifiesto (la spec no
  lo pide).
- **D-5 · R5 «texto añadido detrás de la fecha».** Con D2 = b el parseo es estricto: `2026-10-28T07:12:00Z`
  da la misma fecha que `2026-10-28` (test), y un `recibido_utc` con texto basura detrás no es ISO válido ⇒
  `None` ⇒ Nota sin recepción (R2). En ningún caso llega al prompt un carácter de `recibido_utc` que no sea la
  fecha validada (test con inyección). Leo la frase de R5 como heredada de la v1.0 (fecha UTC = 10 primeros
  caracteres); el reviewer dirá si quiere otra lectura.
- **D-6 · Orden RED en T6/T6b.** En T6 y T6b escribí el módulo antes que los tests. La traza RED de §4 se
  obtuvo apartando el módulo y lanzando los tests (fallan al importar); la fuerza de esos tests la mide la
  mutación (§5), no esa traza. En T1–T5 el test fue primero.

## 4. Fase RED (comandos y salida real)

Entorno: `PYTHONPATH=C:\Users\pgris\PycharmProjects\albaranes-F-112\services\albaranes-comun`, intérprete del
`.venv` raíz, `-q -p no:cacheprovider`.

**T1** `python -m pytest services/albaranes-api/tests/test_f112_fecha_recepcion.py`
```
E   ImportError: cannot import name 'fecha_recepcion' from 'application.services' (unknown location)
ERROR services/albaranes-api/tests/test_f112_fecha_recepcion.py
1 error in 0.34s
```
Verde: `34 passed in 0.57s`.

**T2** `python -m pytest services/albaranes-api/tests/test_f112_render_prompt.py` (15 failed in 1.33s; errores
agrupados con `sort | uniq -c`):
```
  5 E  TypeError: AlbaranExtractionService._render_task_fase_1() takes 3 positional arguments but 4 were given
  4 E  TypeError: AlbaranExtractionService.extract_phase_1() got an unexpected keyword argument 'fecha_recepcion'
  5 E  TypeError: AlbaranExtractionService.review_phase_2() got an unexpected keyword argument 'fecha_recepcion'
  1 E  AssertionError: assert '(Sin fecha de recepción del correo en esta ejecución: lee la fecha solo del
       papel, como siempre.)' in '## Cabecera\n\n- fecha: del papel.\n\n  {fecha_recepcion}\n\n## Correo...'
```
Verde: suite de sv2 `545 passed`.

**T3** `python -m pytest services/albaranes-api/tests/test_f112_worker.py` (11 failed in 1.42s):
```
  6 E  AttributeError: 'ExtractAlbaranRequest' object has no attribute 'fecha_recepcion'
  2 E  TypeError: ExtractAlbaranRequest.__init__() got an unexpected keyword argument 'fecha_recepcion'
  2 E  KeyError: 'fecha_recepcion'
  1 E  AttributeError: <module 'interface_adapters.worker.extraction_worker' ...> has no attribute 'fecha_recepcion_de'
```
Verde: suite de sv2 `556 passed`.

**T4** `python -m pytest services/albaranes-api/tests/test_f112_prompt_yaml.py` → `25 failed, 5 passed in 1.76s`:
```
E       AssertionError: assert 0 == 1
E        +  where 0 = <built-in method count of str ...>('{fecha_recepcion}')
E       ValueError: substring not found
E       AssertionError: assert 0 == 1
E        +  where 0 = <built-in method count of str ...>('{revision_fecha}')
FAILED ...test_f112_r17_ia2_recibe_los_dos_bloques_sin_marcadores[sin_fecha-albaran_revision_fase2_mortero]
```
(uno de los 25 era un fallo del propio test, `reglas["rules"]` en vez de `reglas["reglas"]`, corregido.)
Verde: suite de sv2 `586 passed`.

**T5** `python -m pytest tests/test_f112_rutas_sensibles.py` → `2 failed, 1 passed in 0.24s`:
```
E       assert False
E        +  where False = any(<generator object test_f112_r25_la_puerta_de_evals_cubre_el_fichero...>)
E       AssertionError: []
```
Verde: `8 passed` (con `test_f064_r18`) y `python -m harness.rutas_sensibles --validar` rc=0 (23 rutas).

**T6** (módulos apartados, ver D-6) `python -m pytest tests/test_f112_comparar_fecha.py`:
```
E   ImportError: cannot import name 'comparar_fecha' from 'evals' (...\evals\__init__.py)
1 error in 0.58s
```
Verde: `82 passed in 2.31s`. **T6b** igual: `ImportError: cannot import name 'sinteticos_fecha'` ⇒ `7 passed`.

## 5. Verificación y Evidencias

- **`bash harness/init.sh`** (worktree, `ARNES_SIN_CACHE=1`, `PYTHONPATH` a la comun del worktree): **EXIT=0**.
  Suites: raíz `2011 passed in 302.28s`; sv1 `236 passed`; sv2 `586 passed, 1 warning in 21.84s`; y el resto
  de servicios en verde (1608, 2562, 149, 706, 1186, 1492 passed + 2 skipped). ruff: 1525 avisos, los mismos
  que antes de T1 (deuda previa).
- El primer `init.sh` tras T7 dio KO por `test_f011_r19` (D-3) y, con la suite raíz cortada en ese fallo, la
  cobertura cayó a 33,7 %; corregido, 99,8 %.
- Verificaciones de `tasks.md`: T2 `-k "f048 or f064 or f043"` → 438 passed; T3 y T4 dentro de la suite de sv2;
  T5 `--validar` rc=0; T7 `python -m harness.tamano --feature F-112` → dentro de los topes.

| Evidencia | Valor |
|---|---|
| Tests ejecutados (init) | raíz 2011 + sv1 236 + sv2 586 + 1608 + 2562 + 149 + 706 + 1186 + 1492 (2 skipped), 0 fallos |
| Tests nuevos de F-112 | 182 (sv2 90, raíz 92) |
| Cobertura de líneas cambiadas | **99,8 %** (545/546; la que falta, `_valor` con resultado vacío en el detalle del comparador) |
| Mutación (muestreada, 20, semilla 20260820) | **20 generados, 20 muertos, 0 supervivientes**, 0 timeouts (4663 s, `--workers 2`; con 4 la línea base pasaba de 600 s). Sin supervivientes que analizar; detalle en `progress/mutacion_F-112.md` |
| Tiempo de la suite | raíz 302 s; sv2 21,8 s |

## 6. Pendiente (no es mío)

- **T9** (líder): PDF a `evals/inputs/albaranes/FEC-NNN.pdf` y los 19 en `evals/casos_fecha.json`
  (`caso_id`, `tipologia`, `clase`, `fecha_esperada`, `recibido`); el humano confirma el `dudoso`. Verificación:
  `python -m evals.comparar_fecha --variante rama --juegos A --repeticiones 1 --solo-validar` (sin claves de
  proveedor el comando para con 2: comprueba las claves también, R23).
- **T10/T11** (humano, de pago): `python -m evals.sinteticos_fecha`, luego `python -m evals.comparar_fecha
  --variante ambas --repeticiones 2` (416 + 48 llamadas) y `python -m evals.runner --con-llm --feature F-112`.
- **T12** despliegue de sv2 (lleva `tzdata` nuevo en el manifiesto); **T13** medición a las dos semanas.
- Worktree: *junction* `services/albaranes-front/.venv` → la del árbol principal (init.sh daba KO sin ella);
  quitarla con `cmd /c rmdir` antes de `git worktree remove`.
