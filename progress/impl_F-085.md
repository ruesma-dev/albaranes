<!-- progress/impl_F-085.md -->
# F-085 · Informe del implementer — modelos de producción por fase

Rama `feature/F-085-modelos-produccion` (worktree `../albaranes-F-085`), `dev` `17ccef7` fusionado
(`87796bd`). Rigor `critico`. Spec `specs/F-085-modelos-produccion/` (PARADA 1 resuelta, `7566f82`).

## 1. Qué cambió (un commit por tarea)

| Commit | Tarea | Qué |
|---|---|---|
| `87796bd` | — | Fusión de `dev` (conflictos en `features.json`, `BACKLOG.md`, `current.md`: lo de `dev` + lo de F-085) y F-085 a `in_progress`. |
| `5ccf4b3` | T1 + D4 | `infra/create_capps.ps1`: `$GEMINI_MODEL="gemini-4-argon"`, `$OPENAI_MODEL="gpt-6.1-sol"`, `$ANTHROPIC_MODEL` igual; sv5 con secreto `openai-key` (KV `OPENAI-API-KEY`), `ENABLE_OPENAI=true`, `OPENAI_API_KEY=secretref:openai-key`, `OPENAI_MODEL`, `IA3_PROVIDER=openai`, `IA4_PROVIDER=openai`; sv2 con `IA_SEGUNDA_FASE=openai` y sin `WORKER_CON_FASE2`; cabecera «quién usa qué» reescrita. D4: tabla y test R3 de F-083 (§3). |
| `01d28b7` | T2 | `set_models.ps1`: `OPENAI_MODEL` también en sv5, `-Solo sv2|sv5` (`ValidateSet`), ayuda con el aviso de Claude 5.5 / `ANTHROPIC_FORZAR_HERRAMIENTA` (F-086). `check_deploy.ps1 -ConModelos`: las 9 variables de fase. |
| `dcdc114` | T2b | **Ampliación decidida por el líder (2026-10-21)**: bloque de sv2 con las credenciales de sigrid-api, patrón de sv3/sv9 (§4). |
| `303cfb7` | T3 | `settings.py` de sv5: `_ensure_phase_providers_valid` (R8, R9); vacías, como hoy (R10). |
| `df55dbc` | T4 | `app.py`: `construir_proveedores` y `seleccionar_ia4` extraídas de `build_app` sin cambiar la semántica (R13, R14). |
| `1803881` | T5 | `app.py`: `describir_wiring`, `aviso_ia3_todos`, `proveedores_ia3`; `build_app` escribe el WARNING (R11) y la línea INFO (R12). |
| `5938a3a` | — | Spec corregida por **O3** de `progress/review_F-083.md`: P1 y design §7.1 ya no atribuyen el arreglo de `_parse_response` a F-083 T11 (va a F-086); R27 y la nota de §3 de requirements nombran F-086. Mismo número de líneas (design sigue en 250/250). T6, T7 y T12 marcadas «FUERA → F-086». |
| `adbe1d4` | T8 | `docs/ARCHITECTURE.md` (R20: tabla fase → servicio → variable, IA2 siempre, sv5 con OpenAI; sv2 lee sigrid-api), `infra/README_capps.md`, `INSTRUCCIONES_WORKER_sv2.md` y `_sv3.md` (R22). |
| `6f82a46` | T9 | `azure-apps/albaranes.md` §14 «Modelos de IA por fase (F-085)», commit **`0416ce3`** en `azure-apps`, sin push (R21, R24 provisional). |

Ficheros de test nuevos: `tests/test_f085_infra.py` (R1–R6, R22, ampliación),
`services/albaran-valoracion-api/tests/test_f085_settings.py` (R8–R10),
`services/albaran-valoracion-api/tests/test_f085_wiring.py` (R10–R14). Tocados: `tests/test_f083_precios.py`
y `tests/test_f083_comparar_modelos.py` (D4).

Fuera (P1/P3, PARADA 1): **T6, T7, T12 → F-086** (R15–R19, R27). No implementadas. MANUAL del humano:
**T0, T10, T11** (comandos en `progress/current.md`).

## 2. Decisiones de diseño

- **Funciones de wiring en `app.py`, después de `build_app`** (design §3 dice «a nivel de módulo»): así el diff
  de `build_app` es solo el bloque extraído y la mutación no arrastra líneas sin cambio semántico.
- **`proveedores_ia3`** (no estaba en design §3): la línea de R12 tiene que decir a quién llama IA3 de verdad;
  replica el filtro de `ValuationExtractionService.extract` (vacía ⇒ todos). Con IA3 vacía la línea nombra
  todos: `IA3=claude/claude-opus-4-8,openai/gpt-6.1-sol`. Sin proveedores, `ninguno`.
- **`forzar_herramienta` de la línea de wiring = `FORZAR_HERRAMIENTA_CLAUDE = True`**, constante de módulo:
  sv5 no pasa el parámetro hasta F-086 (T6 fuera) y el defecto de comun es forzar. F-086 la sustituirá por
  `settings.anthropic_forzar_herramienta`.
- **R8/R9: se valida normalizado y se guarda tal cual** (`ia3_provider` sigue siendo el texto de la
  variable; servicio y pipeline ya normalizan). El primer error manda (IA3 antes que IA4).
- **R5/R6 se prueban EJECUTANDO los `.ps1`** (design decía «sobre el texto»): `powershell.exe` con un `az`
  falso definido como función global, más un `az.cmd` delante en el `PATH` que hace fallar el test si se
  llega a invocar, y `AZURE_CONFIG_DIR` vacío. Ningún test toca Azure. Sin PowerShell (Linux), se saltan.
- **R4**: formas de clave con longitud mínima (`sk-…{20,}`, `sk-ant-…{20,}`, `AIza…{30,}`) para no confundir
  «task-» o un prefijo citado; las claves de ejemplo del propio test se construyen concatenando.
- **Sustituto de `fastapi` en `test_f085_wiring.py`**: el `.venv` de la raíz (el intérprete de sv5 en
  `harness/servicios.json`) no trae FastAPI ni ningún venv local tiene a la vez FastAPI y los SDK. El módulo
  solo se inyecta si `import fastapi` falla; basta con que `FastAPI()` acepte los decoradores de ruta. En
  `build_app` también se sustituyen BBDD, SharePoint y prompts: nada abre conexión.

## 3. D4 · acoplamiento con F-083 R3 (O1 de `progress/review_F-083.md`)

- **Tabla** `evals/precios_modelos.json`: `referencias` IA1 `gemini-4-argon`, IA2/IA3/IA4 `gpt-6.1-sol`.
  Papeles: Argon y Sol `referencia`; `gemini-3.7-flash`, `gpt-5.4` y `claude-opus-4-8` pasan a `candidato`
  con motivo «… antes de F-085 (vuelta atrás)» (Opus 4.8 tiene que poder pedirse en M2, IA3/IA4); el motivo
  de `gemini-3.8-flash` ya no lo llama «referencia». `validos()` no cambia (tanda 1 + Opus 4.8).
- **Test R3, antes**: `parametrize((fase, variable))` fijo: IA3 e IA4 → `ANTHROPIC_MODEL`. Con
  `create_capps.ps1` ya en el paso 1 y la tabla vieja, solo detectaba IA1 e IA2; IA3/IA4 pasaban porque
  comparaba `claude-opus-4-8` con `claude-opus-4-8`:
  ```
  FAILED tests/test_f083_precios.py::test_f083_r3_la_referencia_es_la_de_produccion[IA1-GEMINI_MODEL]
  FAILED tests/test_f083_precios.py::test_f083_r3_la_referencia_es_la_de_produccion[IA2-OPENAI_MODEL]
  2 failed, 3 passed, 33 deselected in 0.14s
  ```
- **Test R3, después**: `_variable_de_fase(fase)` lee `IA3_PROVIDER`/`IA4_PROVIDER` del bloque de sv5 (sin
  ellas, `claude`, el defecto de sv5) y los traduce a su `*_MODEL`; test nuevo
  `test_f083_r3_ia3_e_ia4_siguen_al_proveedor_de_sv5`. Contra la tabla vieja (RED) detecta las cuatro:
  ```
  E   AssertionError: IA1: la tabla dice gemini-3.7-flash e infra/create_capps.ps1 (GEMINI_MODEL) dice gemini-4-argon
  E   AssertionError: IA2: la tabla dice gpt-5.4 e infra/create_capps.ps1 (OPENAI_MODEL) dice gpt-6.1-sol
  E   AssertionError: IA3: la tabla dice claude-opus-4-8 e infra/create_capps.ps1 (OPENAI_MODEL) dice gpt-6.1-sol
  E   AssertionError: IA4: la tabla dice claude-opus-4-8 e infra/create_capps.ps1 (OPENAI_MODEL) dice gpt-6.1-sol
  4 failed, 2 passed, 33 deselected in 0.20s
  ```
  Con la tabla nueva: `6 passed`.
- **Efecto colateral, resuelto sin tocar ninguna aserción**: 19 tests de `test_f083_comparar_modelos.py`
  usaban la tabla real y daban por hecho las referencias de entonces (p. ej. `plan.referencia ==
  "gemini-3.7-flash"`). Prueban el comparador, no la producción: el fichero define `cargar_tabla()` local que
  carga la tabla versionada y fija `REFERENCIAS_DE_ESTOS_TESTS` (las de antes). `test_f083_r1_papeles_de_la_parada_1`
  pasa a comprobar los papeles nuevos.
- **Para F-083 T13–T15**: el comparador ya añade como referencia el modelo de producción (O1 resuelto).

## 4. Ampliación del líder (2026-10-21): sigrid-api en sv2

Hallazgo del líder en Log Analytics: sv2 arranca desde al menos el 07-10 con «OBRAS_ACTIVAS_ENABLED=true pero
faltan credenciales SIGRID_API_*» e IA1 recibe `obras_activas=NO DISPONIBLE`. En `create_capps.ps1`, bloque de
sv2: secreto `sigrid-key=$(KvRef 'SIGRID-API-FUNCTION-KEY')` y `SIGRID_API_BASE_URL=$SIGRID_BASE_URL`,
`SIGRID_API_FUNCTION_KEY=secretref:sigrid-key`, `SIGRID_API_DATABASE=$SIGRID_DB` (`ruesma` en
`00_capps_vars.ps1`), igual que sv3. Sin URL ni clave en claro (test). sv2 solo hace `sql/read`
(`sigrid_api_obras_client.py`). Documentado en ARCHITECTURE.md (lectores de Sigrid) y en `azure-apps` §14.
**No choca con la spec**: no toca código de sv2 (design §4) ni contratos; añade un consumo de sv2 a sigrid-api
que el código ya tenía previsto. Lo aplica el humano a mano (bloque M-S de `progress/current.md`).

## 5. Fase RED (comando exacto y salida real)

Root: `C:\Users\pgris\PycharmProjects\albaranes\.venv\Scripts\python.exe -m pytest …` desde el worktree. sv5:
`cd services/albaran-valoracion-api` y `PYTHONPATH=<worktree>/services/albaranes-comun`.

- **T1** — `pytest tests/test_f085_infra.py -k "r1 or r2 or r3 or r4" -q --tb=no -rf`, antes de tocar
  `create_capps.ps1` (`-k r2` arrastra también R22):
  ```
  FAILED tests/test_f085_infra.py::test_f085_r1_modelos_del_paso_1[GEMINI_MODEL-gemini-4-argon]
  FAILED tests/test_f085_infra.py::test_f085_r1_modelos_del_paso_1[OPENAI_MODEL-gpt-6.1-sol]
  FAILED tests/test_f085_infra.py::test_f085_r2_sv5_declara_el_secreto_de_openai
  FAILED tests/test_f085_infra.py::test_f085_r2_entorno_de_sv5[IA3_PROVIDER=openai]
  FAILED tests/test_f085_infra.py::test_f085_r3_sv2_fija_las_dos_fases - Assert...
  FAILED tests/test_f085_infra.py::test_f085_r3_nadie_declara_worker_con_fase2
  13 failed, 35 passed, 8 deselected in 0.30s
  ```
  (13 fallos: R1 ×2, R2 ×6, R3 ×2 y R22 ×3; listado completo recortado.) Después: `42 passed`.
- **T2** — `pytest tests/test_f085_infra.py -k "r5 or r6" -q --tb=line -rf`:
  ```
  E   AssertionError: assert {'ca-sv2-extraccion'} == {'ca-sv2-extr...v5-valuation'}
  E   AssertionError: assert ['ca-sv2-extraccion'] == ['ca-sv5-valuation']
  E   Failed: DID NOT RAISE AssertionError
  E   assert 'ANTHROPIC_FORZAR_HERRAMIENTA' in '# set_models.ps1\n# Cambia EN CALIENTE ...
  E   AssertionError: IA_PRIMERA_FASE
  5 failed, 3 passed, 42 deselected in 7.47s
  ```
  (Los 3 verdes caracterizan lo que ya era así: `-Gemini` solo sv2, `-Anthropic` en las dos, `-Solo sv2`.)
- **T2b** — `pytest tests/test_f085_infra.py -k amp -q --tb=line -rf`:
  ```
  E   assert "sigrid-key=$(KvRef 'SIGRID-API-FUNCTION-KEY')" in ["anthropic-key=$(KvRef 'ANTHROPIC-API-KEY')", "openai-key=$(KvRef 'OPENAI-API-KEY')", "gemini-key=$(KvRef 'GEMINI-API-KEY')"]
  E   AssertionError: assert 'SIGRID_API_BASE_URL=$SIGRID_BASE_URL' in ['AZURE_CLIENT_ID=$MI_CLIENTID', ...]
  E   AssertionError: assert [] == ['SIGRID_API_...E=$SIGRID_DB']
  5 failed, 1 passed, 50 deselected in 0.17s
  ```
- **T3** — `pytest tests/test_f085_settings.py -q --tb=no -rf`:
  ```
  FAILED tests/test_f085_settings.py::test_f085_r8_proveedor_desconocido_no_arranca[mistral-IA3_PROVIDER]
  FAILED tests/test_f085_settings.py::test_f085_r8_ia4_se_valida_aunque_ia3_este_vacia
  FAILED tests/test_f085_settings.py::test_f085_r9_proveedor_apagado_no_arranca[openai-ENABLE_OPENAI-IA3_PROVIDER]
  FAILED tests/test_f085_settings.py::test_f085_r9_claude_apagado_no_arranca[IA4_PROVIDER]
  14 failed, 12 passed in 0.76s
  ```
  (Los 12 verdes son R10 y los casos válidos: lo de hoy no cambia.)
- **T4** — `pytest tests/test_f085_wiring.py -q --tb=line -rf`:
  ```
  E   AttributeError: module 'interface_adapters.api.app' has no attribute 'construir_proveedores'
  E   AttributeError: module 'interface_adapters.api.app' has no attribute 'seleccionar_ia4'
  FAILED tests/test_f085_wiring.py::test_f085_r13_ia3_openai_llama_solo_a_openai_y_es_el_primario
  12 failed, 1 passed in 11.44s
  ```
  (El verde: `build_app` ya daba a IA4 solo `openai`; queda como caracterización.)
- **T5** — `pytest tests/test_f085_wiring.py -q --tb=line -k "r11 or r12"`:
  ```
  E   AssertionError: assert '[svc5][wiring] IA3=openai/gpt-6.1-sol IA4=openai/gpt-6.1-sol forzar_herramienta=True' in ['[svc5][wiring] IA call logger INACTIVO (dir=n/a)']
  E   assert (0 == 1)
  11 failed, 13 deselected in 8.01s
  ```
- **T8** — `pytest tests/test_f085_infra.py -k r22 -q --tb=no -rf`:
  ```
  FAILED tests/test_f085_infra.py::test_f085_r22_nadie_dice_que_worker_con_fase2_apaga_la_fase_2[services/albaranes-api/INSTRUCCIONES_WORKER_sv2.md]
  FAILED tests/test_f085_infra.py::test_f085_r22_nadie_dice_que_worker_con_fase2_apaga_la_fase_2[services/albaranes-persistencia/INSTRUCCIONES_WORKER_sv3.md]
  FAILED tests/test_f085_infra.py::test_f085_r22_nadie_dice_que_sv5_solo_usa_claude[infra/README_capps.md]
  3 failed, 3 passed, 56 deselected in 0.13s
  ```

## 6. Resultado real de `bash harness/init.sh` (worktree, HEAD `6f82a46`; repetido sobre `039f58f`, mismo verde)

`ENTORNO LISTO. Puedes trabajar.` (exit 0). Raíz `1638 passed in 308.37s`; sv1 205, sv2 485, sv3 1576, sv4
1774, **sv5 `96 passed in 34.29s`**, sv6 473 (+1 skipped), sv9 673, comun en verde (caché). `[OK] PUERTA
COBERTURA: 100.0% de 44 líneas cambiadas cubiertas (44/44, umbral 80%, nivel critico)`. `[OK] PUERTA TAMAÑO`
(requirements 105/150, design 250/250). Avisos previos, no de F-085: ruff 1360 (deuda), `ruesma_comun` desde
el árbol principal, `[ADAPTAR]` de F-034/F-035, infra sin `comando_tests`. Los commits posteriores
(`a737e7b`, este informe, el inventario) solo tocan `progress/`.

## 7. Verificaciones MANUAL pendientes (humano; comandos en `progress/current.md`)

- **T0 · M0** (solo lectura): el paso 1 en sv2/sv5 coincide con `create_capps.ps1`; pegar aquí la salida y la
  revisión activa. Sin hacer.
- **M-S** (ampliación): sigrid-api en sv2 [ESCRIBE EN PRODUCCIÓN · humano]; VERDE «Obras activas CABLEADAS».
- **P2/P5** (opcional): `--remove-env-vars WORKER_CON_FASE2` e `IA_SEGUNDA_FASE=openai` en sv2.
- **T10 · M4**: desplegar solo sv5 tras APPROVED y fusión, con T0 en verde; VERDE la línea
  `[svc5][wiring] IA3=openai/gpt-6.1-sol IA4=openai/gpt-6.1-sol forzar_herramienta=True`.
- **T11 · M2**: medición con el comparador de F-083 (IA1/IA2 ya; IA3/IA4 con F-084 `done`) y veredicto §6.

## 8. Fuera del alcance y riesgos que quedan

- **F-086**: R15–R19, R27, T6, T7, T12 (Opus 5.5 en IA3, `ANTHROPIC_FORZAR_HERRAMIENTA`, arreglo de
  `_parse_response`). `set_models.ps1` y `create_capps.ps1` avisan de no poner un Claude 5.5 en sv5 antes.
- **Despliegue de sv5 antes que T0**: si Azure no coincidiera (p. ej. `IA3_PROVIDER=openai` sin
  `ENABLE_OPENAI=true`), la imagen nueva no arrancaría (R9). Es lo buscado, pero por eso T0 va antes de T10.
- **El test de R5/R6 depende de `powershell.exe`**: en Windows corre (unos 5 s); en otro sistema se salta y
  R5/R6 quedan sin comprobar ahí.
- **`create_capps.ps1` sigue sin BOM** (como antes; las convenciones piden UTF-8 con BOM para PowerShell). Sus
  textos con tilde ya estaban así; no se cambia en F-085.
- **D4 en F-083**: los tests del comparador ya no dependen de producción; si alguien cambia las
  referencias de la tabla, solo R3 y los papeles de `test_f083_precios.py` lo notan, que es lo pretendido.

## 8 bis. Pasada 2 de la review (solo documental, `progress/review_F-085.md`)

Cambio 1: `description` de F-085 en `features.json` con P1 corregido (O3) y `title` al día; `BACKLOG.md`
regenerado. Cambio 2: `azure-apps` §14 con sigrid-api en sv2 aplicado (rev. `--0000006`, 277 obras), commit
**`81164ab`** sin push; M-S marcada hecha en `current.md`. O1: ARCHITECTURE.md precisa que `WORKER_CON_FASE2`
sigue en Azure (`false`) hasta P2. O5: `dominio_negocio_albaranes.md` (§ cambio de modelos) y `sv5.md` (§5.1,
§8.2 con `IA3_PROVIDER`/`IA4_PROVIDER`, R8/R9 y la línea de wiring; decisión 8). Sin tocar código (O3 de
ruff y O4 quedan como están).

## 9. Evidencias

| Evidencia | Valor medido |
|---|---|
| Tests de F-085 | raíz `tests/test_f085_infra.py` **62 passed** (5,8 s, con PowerShell); sv5 `test_f085_settings.py` **26 passed**, `test_f085_wiring.py` **24 passed** |
| Tests tocados de F-083 (D4) | `test_f083_precios.py` + `test_f083_comparar_modelos.py` + `test_f085_infra.py`: **150 passed** (17,2 s), sin cambiar ninguna aserción del comparador |
| Suites completas (init.sh) | raíz **1638 passed** (308,4 s); sv5 **96 passed** (34,3 s); resto de servicios en verde (§6) |
| Cobertura de las líneas cambiadas | **100,0 %** (44/44, umbral 80 %, `critico`) — línea `PUERTA COBERTURA` de init.sh |
| Mutación | `python -m harness.mutacion --feature F-085` (con `PYTHONPATH=<worktree>/services/albaranes-comun`), campaña **completa**, 4 workers, sobre `a737e7b`: 2 ficheros, 195 líneas de sv5; **20 mutantes, 20 muertos, 0 supervivientes**, 0 timeouts, 0 sin veredicto, 170,0 s → `progress/mutacion_F-085.md`; fila nueva en `progress/inventario_mutacion_F-039.md` (48 informes) |
| Supervivientes | ninguno: no hay análisis que hacer |
| No medido por la herramienta | los `.ps1` de `infra/` (la mutación solo cubre Python): R1–R6 los prueban los tests de texto y la ejecución con `az` falso; la RED de T1/T2/T2b muestra que fallan sin el cambio |
| Tiempo de la suite | raíz 308,4 s y sv5 34,3 s en init.sh; base de mutación de sv5 21,0 s por worker |
