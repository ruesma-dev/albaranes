<!-- progress/review_F-085.md -->
Revisión completa (pasada 1) · `dev...HEAD` con HEAD `969063c` (merge-base `17ccef7`)

# F-085 · Review del reviewer: modelos de producción por fase

**Veredicto: CHANGES_REQUESTED.** Los dos cambios pedidos son solo documentales. Código, tests,
infra y mutación están bien. El O3 de F-083 se corrigió en la spec, pero sigue igual en la ficha
de la feature (`features.json` y `BACKLOG.md`). `azure-apps` §14 da por pendiente algo que ya
está en producción.

**Rigor:** `critico`, declarado en `features.json`. Exige fase RED, cobertura ≥ 80 % de lo
cambiado, mutación completa con 0 supervivientes y las MANUAL con su comando exacto.

## Verificación ejecutada por el reviewer

- **`bash harness/init.sh`** en el worktree: ENTORNO LISTO (exit 0).
  - Suites: raíz 1638, sv1 205, sv2 485, sv3 1576, sv4 1774, **sv5 96**, sv6 473 (+1 skip) y
    sv9 673.
  - Puertas: COBERTURA `[OK]` 100,0 % (44/44) · RUTAS SENSIBLES N/A · TAMAÑO `[OK]`.
- **Mutación, recálculo puro.** `alcance_de_feature`: rama `17ccef7..feature/…`.
  - `settings.py` 38 líneas + `app.py` 157 = 195 líneas. `generar_mutantes`: 3 + 17 = 20.
  - Cuadra con el informe.
- **Mutación, campaña reejecutada entera.** El «Tiempo total» (170 s) pasa de 60 s y el protocolo
  no la pide, pero era barata y la máquina estaba libre.
  - Sobre `969063c`, 4 workers, salida en el scratchpad: 20 mutantes, 20 muertos,
    0 supervivientes, 0 timeouts, 0 sin veredicto, 397 s.
  - Totales idénticos a `progress/mutacion_F-085.md`. `git status` quedó limpio.
- **RM1.** Midió sobre `a737e7b`; de ahí a HEAD solo cambian `progress/` y una casilla de
  `tasks.md`. Mismo alcance.
- **RM2.** Base 21 s; media 8,5 s × 4 workers ≈ 34 s por mutante. Coherente: los tests que matan
  van al final (`test_f085_*`) y `-x` apenas recorta. Mi campaña da el mismo patrón (base 64 s,
  19,9 × 4 ≈ 80 s).
- **RM3.** Ninguno de los 20 es equivalente: cada uno cambia algo que un test compara.
  - `or ""` → `and ""`: vacía la api_key o el filtro.
  - `<= 1` → `< 1` / `<= 2`: cambia el aviso.
  - `[0]` → `[1]`: IndexError.
- **RM5 / RM6:** N/A. No hay equivalentes declarados ni guardas quitadas.
- **D4 / O1 de F-083.** Antes, R3 mapeaba IA3/IA4 → `ANTHROPIC_MODEL` fijo. Ahora lee
  `IA3_PROVIDER`/`IA4_PROVIDER` del bloque de sv5.
  - Ejecuté `_variable_de_fase`: contra la tabla de `dev` falla en las cuatro fases; contra la
    nueva pasa en las cuatro (IA3/IA4 → `OPENAI_MODEL`).
  - Las referencias pasan a Argon/Sol y los modelos de antes quedan como `candidato`.
- **T2b, contra lo desplegado** (`az containerapp show`, solo lectura, URL y suscripción
  redactadas en la salida).
  - `ca-sv2-extraccion--0000006`: `SIGRID_API_BASE_URL`, `SIGRID_API_DATABASE=ruesma` y
    `SIGRID_API_FUNCTION_KEY` → `sigrid-key`.
  - `sigrid-key` apunta al KV `…/SIGRID-API-FUNCTION-KEY` con `id-albaranes-dev`, igual que en
    `ca-sv3-persistencia`.
  - `create_capps.ps1` declara lo mismo con el patrón de sv9 (`KvRef`, `$SIGRID_BASE_URL`,
    `$SIGRID_DB`). Los alias cuadran con `albaranes-api/config/settings.py:211-216`.
- **M0, leído por el reviewer** (T0 sigue siendo del humano). Coincide con `create_capps.ps1`
  (R7); con esto la imagen nueva arranca y su línea de wiring sale
  `IA3=openai/gpt-6.1-sol IA4=openai/gpt-6.1-sol`.
  - sv2: Argon y Sol, `IA_PRIMERA_FASE=gemini`. Siguen `WORKER_CON_FASE2=false` y sin
    `IA_SEGUNDA_FASE`: P2/P5, opcionales y pendientes.
  - sv5 `--0000005`: `ENABLE_OPENAI=true`, `IA3/IA4_PROVIDER=openai`, `OPENAI_MODEL=gpt-6.1-sol`,
    `OPENAI_API_KEY` → `openai-key`, y el secreto existe.
- **Barrido de secretos** en el diff de la rama y en `azure-apps` `0416ce3` (sin push).
  - Patrones: GUID, IPv4, `sk-`, `AIza`, `azurewebsites`, `vault.azure`, `/subscriptions/`,
    `password=`, `AccountKey`, `tenant`.
  - Solo aparecen los patrones del propio test R4, construidos por concatenación. Ni URL, ni ID,
    ni clave.

## Checkpoints

- **C1** [x] init.sh exit 0 · [x] ficheros base presentes.
- **C2** [x] una sola `in_progress` · [x] rama de la feature · [x] `current.md`, según la práctica
  del repo (F-083 `blocked` con sus MANUAL) · [x] historia de las `done`.
- **C3** [x] hexagonal (wiring en `interface_adapters`, validación en `config`, dominio intacto)
  · [x] primera línea con la ruta · [x] sin print, secretos ni dependencias nuevas · [x] trampas
  de dominio N/A: ni SQL, ni merge, ni importes.
- **C3 bis** N/A: no toca `docs/referencia/`.
- **C4** [x] trazabilidad (tabla de abajo) · [x] sin red ni BBDD (dobles de los SDK, `az` falso
  con `az.cmd` trampa, `AZURE_CONFIG_DIR` vacío) · [x] MANUAL T0, M-S, P2/P5, T10 y T11 en
  `current.md` con su comando exacto.
- **C4 bis**
  - [x] rigor · [x] RED real (T1, T2, T2b, T3, T4, T5, T8 y D4) · [x] cobertura
  - [x] mutación verificada por tres vías · [x] muertos comprobados (campaña repetida)
  - [x] coste por mutante · [x] sin «NO VÁLIDA» · [x] RM1 · [x] RM2
  - RM5/RM6 N/A (motivo arriba) · manual N/A (la automática dio 20)
  - [x] sin supervivientes · [x] «Evidencias» con los workers · [x] ningún N/A sin motivo
- **C4 ter** N/A: la puerta no señala rutas sensibles.
- **C5**
  - [x] `tasks.md`: T1–T5, T2b, T8, T9 y T13 en `[x]`, cada una con su commit `F-085 Tn:`.
    T0, T10 y T11 son MANUAL del humano, pendientes como en F-083. T6, T7 y T12, FUERA → F-086
    (P3).
  - [x] no hay ficheros temporales.
  - **[ ] `features.json` no refleja el estado real** (cambio 1).

## Cobertura: requisito → test

| Req | Test (o verificación) |
|---|---|
| R1–R3 | `tests/test_f085_infra.py::test_f085_r1_*`, `test_f085_r2_*` (secreto, entorno ×9, secretref↔secreto), `test_f085_r3_*` |
| R4 | `test_f085_r4_*`: secretref, la clave en claro, el barrido de los ficheros de F-085, las formas y los falsos positivos |
| R5, R6 | `test_f085_r5_*` y `test_f085_r6_*`: EJECUTAN los `.ps1` con el `az` falso (`-Solo`, ValidateSet, ayuda) |
| R7 | MANUAL T0. El reviewer lo leyó y coincide |
| R8–R10 | `services/albaran-valoracion-api/tests/test_f085_settings.py::test_f085_r8_*` / `r9_*` / `r10_*` y `test_f085_wiring.py::test_f085_r10_*` |
| R11, R12 | `test_f085_wiring.py::test_f085_r11_*` y `r12_*`: función pura y `build_app` con caplog |
| R13, R14 | `test_f085_r13_*` (IA4 solo openai, IA3 primario openai, `build_app`) y `test_f085_r14_*` |
| R15–R19, R27 | FUERA → F-086 (PARADA 1, P1/P3) |
| R20, R21 | Revisión: `docs/ARCHITECTURE.md` «APIs LLM» y `azure-apps/albaranes.md` §14 (ver el cambio 2) |
| R22 | `test_f085_r22_*` (×6) |
| R23–R26 | MANUAL T11 del humano. R24 provisional en `current.md` y en `azure-apps` [x] |

## Cambios requeridos

1. **O3 sigue sin corregir en la ficha de la feature.**
   - `harness/features.json:1012`, `description` de F-085, dice «P1 = (a) el parseo de respaldo
     de Claude lo arregla F-083 T11». Se replica en `BACKLOG.md:144`.
   - Hay que reescribirlo como en design §9: «P1 = (a): fuera de F-085; F-083 T11 solo añadió
     `forzar_herramienta`; el arreglo de `_parse_response` va a F-086». Después se regenera
     `BACKLOG.md` con `init.sh`.
   - Recomendado en el mismo commit: el `title` aún dice «IA3 claude-opus-5-5». Ponerlo al día,
     p. ej. «… IA3 e IA4 gpt-6.1-sol (Opus 5.5 en IA3 → F-086)».
2. **`azure-apps/albaranes.md` §14 se quedó atrás** (regla de `azure-apps`).
   - La viñeta «sv2 consume sigrid-api» dice «Lo aplica el humano a mano».
   - Ya está aplicado: el reviewer lo leyó en `ca-sv2-extraccion--0000006` y el líder vio en el
     log «Obras activas CABLEADAS», 277 obras. El recuadro inicial aún cita sv2 `--0000004`.
   - Hay que anotar «aplicado el 2026-10-21 (rev. `--0000006`), verificado en el log», en un
     commit nuevo en `azure-apps`, sin push.
   - En el mismo trabajo, marcar M-S como hecha en el bloque de F-085 de `progress/current.md`.

## Observaciones (no bloquean)

- **O1.** `docs/ARCHITECTURE.md:779` dice que `WORKER_CON_FASE2` «se quitó». Se quitó de
  `create_capps.ps1`, pero en Azure sigue (`false`) hasta P2. Conviene precisarlo.
- **O2.** sv5 desplegado lleva `GEMINI_MODEL=gemini-3.7-flash`, que `create_capps.ps1` no
  declara. Es inocuo (Gemini está apagado), pero saldrá en `-ConModelos`; puede retirarse en el
  `update` de P2.
- **O3.** Dos avisos nuevos de ruff, menores y dentro de la deuda de 1360:
  `settings.py:326` UP037 (mismo estilo que los validadores de al lado) y
  `test_f085_settings.py:7` I001.
- **O4.** `test_f085_wiring.py` mete un `fastapi` sustituto en `sys.modules` al importarse. Un
  test futuro de sv5 con `importorskip("fastapi")` vería el sustituto y no se saltaría.
- **O5.** Textos viejos fuera de R22, candidatos para F-086 o para una ficha documental:
  - `docs/referencia/dominio_negocio_albaranes.md:451` dice «sv5: solo Claude».
  - `services/albaran-valoracion-api/sv5.md` no cuenta R8/R9 ni la línea de wiring.

**Pasada 2:** incremental desde `969063c` y solo documental. Basta con `init.sh` en verde; si el
delta no toca `settings.py` ni `app.py`, no hace falta campaña nueva.

**Automejora (propuesta, no aplicada)** para `CHECKPOINTS.md` C5: «`features.json` refleja el
estado real, **incluida la `description`** cuando una review posterior corrige una decisión de
la PARADA 1».
