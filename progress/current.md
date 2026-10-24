<!-- progress/current.md -->
# Trabajo en curso

**F-069 · `blocked` (2026-10-24): review APPROVED (pasada 2), fusionada en `dev` (`904d790`, init.sh en verde) y DESPLEGADA por el líder a petición expresa del humano** — usuario y empleado de Sigrid de quien aprueba (Lista → correo/`emp.traele` → Respaldo / `empide` nulo). Despliegue 2026-10-24: `set_alta_sigrid.ps1` (Lista vacía en sv9; DESDE, ESPERA y RESPALDO sin cambios; `ALTA_SIGRID_COMMIT` = true, sin tocar) → sv9 `r20261024-0845` (una revisión activa; log: `modo=real`, «Lista de equivalencias: 0 Entradas», escuchando `q-feedback`) → sv4 `r20261024-0848` (una revisión activa, arranque limpio). Rama `feature/F-069-usuario-empleado-sigrid`, worktree `../albaranes-F-069`. Informe `progress/impl_F-069.md`, review `progress/review_F-069.md`, medición T5 `progress/medicion_F-069.md`. `azure-apps` `3119ae3` local, sin push.

- **Espera 1 · T17 (líder, solo lectura):** tras la primera alta real de un aprobador, `dca.empide` del AC nuevo = el de su correo (odomingo 1363636, tortiz 677761, lgarcia 922352, privillas 1203626) y el panel enseña «Empleado de Sigrid» y los avisos.
- **Superviviente equivalente ACEPTADO por el humano (2026-10-24)** (`sys.path.insert(1, …)` en `scripts/medir_empleados_f069.py:46`, demostración en `progress/mutacion_F-069.md`). Ya no es espera.
- **E5 DECIDIDO por el humano (2026-10-24): no se corrige, se dejan así.** 65 de las 68 altas ya escritas llevan 2425207; no se pide nada a sigrid-api por esto (F-103 §3.d sale de la petición).

**F-103 · `blocked` (2026-10-24, decisión del humano): parada hasta que sigrid-api termine su F-015 v2**, donde estas decisiones ya están tomadas y en implementación. Spec v1 en la rama `feature/F-103-alta-sin-facturacion-heredada` (worktree `../albaranes-F-103`, `563d264`, *junction* `.venv` de sv4), sin PARADA 1: D1–D7 en su `design.md` §8 quedan sin decidir aquí. El borrador `progress/propuestas_a_sigrid_api_F-103.md` (en esa rama) NO se envía. Al retomarla: quitar §3.d (E5 decidido: no se corrige el `empide`), corregir 68/46 (mismo universo; el 68 incluye las altas del 24-10), y que F-069 ya está desplegada hace imprescindible no filtrar la limpieza por `empide = 2425207` (§3.b).

**F-084 · CERRADA (`done`, 2026-10-23).** El banco de evals valora de verdad. Review APROBADA en la pasada 3; línea base de R28 del 23,5 % aceptada por el humano (D5). Resumen en `history.md`; detalle en `progress/impl_F-084.md`, `progress/impl_F-084_T14.md` y `progress/review_F-084.md`. Pendiente anotado: afirmar `rol_linea` en las 28 líneas sintéticas `?` del libro IA3 (tarea de datos del banco).

**F-092 · `blocked` (2026-10-22, al darla de alta): gestión de almacén.** Bloqueada por la regla LÍMITE DE SERVICIO antes de la spec: el humano decide qué es (vista de lo que entró a almacén desde albaranes o gestión de existencias con salidas a partida/obra), si va en este monorepo como servicio nuevo o en un proyecto aparte, y si escribe en Sigrid. Ficha en `harness/features.json`.

**F-085 · `blocked` (2026-10-21): review APPROVED (pasada 2), fusionada en `dev`; implementación hecha (T1–T5, T2b, T8, T9); T0, T10 y T11 son MANUAL del humano; T6, T7 y T12 FUERA → F-086** — modelos de producción por fase. Spec en `specs/F-085-modelos-produccion/` (corregida por O3 de la review de F-083). Rama `feature/F-085-modelos-produccion`, worktree `../albaranes-F-085` (*junction* `.venv` de sv4: quitarla con `cmd /c rmdir` antes de `git worktree remove`), `dev` (`17ccef7`) fusionado. Rigor `critico`. Informe: `progress/impl_F-085.md`; mutación: `progress/mutacion_F-085.md`; `azure-apps` `0416ce3` sin push.

- **Punto de partida:** el paso 1 que el humano aplicó a mano el 2026-10-20 (sv2 `ca-sv2-extraccion--0000004`: `GEMINI_MODEL=gemini-4-argon`, `OPENAI_MODEL=gpt-6.1-sol`; sv5 `ca-sv5-valuation--0000005`: secreto `openai-key` → KV `OPENAI-API-KEY`, `ENABLE_OPENAI=true`, `IA3_PROVIDER=openai`, `IA4_PROVIDER=openai`, `OPENAI_MODEL=gpt-6.1-sol`). `infra/create_capps.ps1` lo deja igual. IA3/IA4 **provisionales** hasta medir con el banco de F-084 (R24).
- **Ampliación del líder (2026-10-21, T2b):** sv2 con las credenciales de sigrid-api en `create_capps.ps1` (secreto `sigrid-key` → KV `SIGRID-API-FUNCTION-KEY`, `SIGRID_API_BASE_URL`, `SIGRID_API_FUNCTION_KEY`, `SIGRID_API_DATABASE`): sv2 arrancaba sin ellas e IA1 recibía `obras_activas=NO DISPONIBLE`. **M-S HECHA**: aplicado por el humano el 2026-10-21 (`ca-sv2-extraccion--0000006`), verificado en el log («Obras activas CABLEADAS», 277 obras); `azure-apps` `81164ab`.
- **D4 (O1 de `progress/review_F-083.md`), hecho aquí:** `evals/precios_modelos.json` con referencias IA1 `gemini-4-argon` e IA2–IA4 `gpt-6.1-sol` (los de antes, candidatos de vuelta atrás); el test R3 de F-083 lee `IA3_PROVIDER`/`IA4_PROVIDER` de sv5; los tests del comparador fijan sus propias referencias. Consecuencia para las MANUAL T13–T15 de F-083: la referencia que añade el comparador ya es la de producción (O1 resuelto).
- **Desviaciones (justificadas en el informe):** los tests de `build_app` importan `app.py` con un sustituto de `fastapi` (el `.venv` de la raíz no lo trae); `forzar_herramienta` de la línea de wiring es la constante `FORZAR_HERRAMIENTA_CLAUDE = True` hasta F-086.

#### F-085 · MANUAL del humano, comandos para PowerShell

Todo desde `C:\Users\pgris\PycharmProjects\albaranes\infra`. Lo marcado **[ESCRIBE EN PRODUCCIÓN · humano]** necesita el sí expreso del humano; ningún agente lo lanza. Si un paso no da su VERDE, para ahí.

```powershell
cd C:\Users\pgris\PycharmProjects\albaranes\infra
. .\00_vars.ps1
. .\00_capps_vars.ps1
```

**T0 · M0, solo lectura** (el paso 1 coincide con `create_capps.ps1`, R7):

```powershell
az containerapp show -n ca-sv2-extraccion -g $RG --query "properties.template.containers[0].env[?ends_with(name,'_MODEL') || starts_with(name,'IA_') || starts_with(name,'SIGRID_') || name=='WORKER_CON_FASE2'].{n:name,v:value,s:secretRef}" -o table
az containerapp show -n ca-sv5-valuation -g $RG --query "properties.template.containers[0].env[?ends_with(name,'_MODEL') || starts_with(name,'IA') || starts_with(name,'ENABLE_') || name=='OPENAI_API_KEY'].{n:name,v:value,s:secretRef}" -o table
az containerapp show -n ca-sv5-valuation -g $RG --query "properties.configuration.secrets[].name" -o tsv
az containerapp revision list -n ca-sv5-valuation -g $RG --query "[?properties.active].name" -o tsv
```

VERDE: sv2 `GEMINI_MODEL=gemini-4-argon`, `OPENAI_MODEL=gpt-6.1-sol`; sv5 `ENABLE_OPENAI=true`, `IA3_PROVIDER=openai`, `IA4_PROVIDER=openai`, `OPENAI_MODEL=gpt-6.1-sol`, `OPENAI_API_KEY` con `s=openai-key`, y `openai-key` en los secretos. Pegar la salida y la revisión activa en `progress/impl_F-085.md` (T0).

**M-S · sigrid-api en sv2 (ampliación) — HECHA el 2026-10-21** (rev. `--0000006`, «Obras activas CABLEADAS», 277 obras). Comandos que se usaron, como referencia:

```powershell
az containerapp secret set -n ca-sv2-extraccion -g $RG --secrets "sigrid-key=keyvaultref:$KV_URI/secrets/SIGRID-API-FUNCTION-KEY,identityref:$MI_ID"
az containerapp update -n ca-sv2-extraccion -g $RG --set-env-vars "SIGRID_API_BASE_URL=$SIGRID_BASE_URL" SIGRID_API_FUNCTION_KEY=secretref:sigrid-key "SIGRID_API_DATABASE=$SIGRID_DB"
az containerapp logs show -n ca-sv2-extraccion -g $RG --tail 300 | Select-String "Obras activas|faltan credenciales"
```

VERDE: «Obras activas CABLEADAS» y ningún «faltan credenciales SIGRID_API_*» en la revisión nueva (sv2 escala a cero: puede hacer falta un albarán para ver el log). Vuelta atrás: `--remove-env-vars SIGRID_API_BASE_URL SIGRID_API_FUNCTION_KEY SIGRID_API_DATABASE`.

**P2/P5 en sv2 (opcional, sin efecto en el comportamiento) — [ESCRIBE EN PRODUCCIÓN · humano]:**

```powershell
az containerapp update -n ca-sv2-extraccion -g $RG --remove-env-vars WORKER_CON_FASE2
az containerapp update -n ca-sv2-extraccion -g $RG --set-env-vars IA_SEGUNDA_FASE=openai
```

**T10 · M4, desplegar solo sv5 — [ESCRIBE EN PRODUCCIÓN · humano].** Tras APPROVED, fusión en `dev` e `init.sh` en verde en el árbol principal; **antes, T0 en verde** (con R8/R9, sv5 no arranca con una combinación incoherente).

```powershell
az containerapp show -n ca-sv5-valuation -g $RG --query "properties.template.containers[0].image" -o tsv
Set-DeployTag
.\deploy.ps1 -Only sv5
.\check_deploy.ps1 -ConModelos
az containerapp logs show -n ca-sv5-valuation -g $RG --tail 300 | Select-String "wiring|proveedor=|IA4 proveedor|HTTPException|Traceback"
```

VERDE: sv5 en el tag nuevo y `[svc5][wiring] IA3=openai/gpt-6.1-sol IA4=openai/gpt-6.1-sol forzar_herramienta=True`, sin WARNING de «IA3 llamará a TODOS», sin `Traceback`. Vuelta atrás: `az containerapp update -n ca-sv5-valuation -g $RG --image <la imagen apuntada>`. Después, M1 de design §5 (Log Analytics: modelos servidos y volumen de 30 días).

**T11 · M2, medición (cuesta dinero; humano):** con F-083 T13–T15, comandos en design §5 M2 y en el bloque de F-083 de abajo. IA1 e IA2 ya; IA3 e IA4 solo con F-084 `done`. Veredicto de design §6 por fase (consolidar o M3) y coste mensual con Argon a 4/20, anotados aquí.

**F-083 · `blocked` (2026-10-21): review APPROVED (pasada 2), fusionada en `dev`; espera las MANUAL T13–T15 del humano (pago). O6 de la review (campo de uso opcional ausente = 0 sin `uso_incompleto`) ACEPTADO por el humano el 2026-10-21. Antes: PARADA 1 resuelta el 2026-10-19 (tanda 1 de 8 modelos, P5 = (a)); T1–T12 y T16 hechas, review pasada 1 CHANGES_REQUESTED solo documental (aplicada); pendientes T13–T15 del humano, que antes debe decidir O1 y O2** — comparar modelos de IA por fase (IA1–IA4) con acierto y coste por albarán. Spec en `specs/F-083-comparar-modelos/`; inventario de modelos con precio, fuente y fecha en `progress/spec_F-083.md`. Rama `feature/F-083-comparar-modelos`, worktree `../albaranes-F-083` (creado desde `dev` `7facc86`; *junction* `.venv` de sv4 puesta: quitarla con `cmd /c rmdir` antes de `git worktree remove`). Rigor `critico`. Toca `evals/` y, solo con P5 = (a), un parámetro opcional del cliente de Claude en comun; ningún servicio cambia en producción.

Estado del implementer (2026-10-21): **T1–T12 y T16 hechas** (un commit por tarea); fase RED, decisiones, riesgos y evidencias en `progress/impl_F-083.md`. `bash harness/init.sh` en verde en el worktree (cobertura de lo cambiado 99,4 %). **T16, mutación VÁLIDA**: la campaña completa del reviewer sobre `96a59a3`, 3 workers, **366 mutantes, 366 muertos, 0 supervivientes**, 0 timeouts, 21.907 s (`progress/mutacion_F-083.md`, con su fila en el inventario de F-039). Las dos campañas anteriores del implementer quedaron «NO VÁLIDA» por la base de cierre con la máquina cargada (`progress/impl_F-083_mutacion.md`). Desviaciones (justificadas en el informe): T9 y T10 antes que T8; `procesar` y `lanzar` viven en `medidor.py`, compartidos por los dos subprocesos. T13–T15 son MANUAL del humano, comandos abajo.

#### F-083 · MANUAL T13–T15 (humano), comandos para PowerShell

**Cuesta dinero: solo el humano.** Todo en el worktree, sobre la rama (trae la comun con `forzar_herramienta`). `--estimar` no pide claves ni llama a nada: hacerlo siempre antes. Las claves se piden con `Read-Host -AsSecureString` y se borran al final. Nada escribe en producción: solo llamadas a las API de los tres proveedores.

Preparación de la consola (una vez):

```powershell
cd C:\Users\pgris\PycharmProjects\albaranes-F-083
if (-not (Test-Path .\evals\inputs)) { Copy-Item -Recurse C:\Users\pgris\PycharmProjects\albaranes\evals\inputs .\evals\inputs }
$env:PYTHONPATH = "C:\Users\pgris\PycharmProjects\albaranes-F-083\services\albaranes-comun"
$py = "C:\Users\pgris\PycharmProjects\albaranes\.venv\Scripts\python.exe"
$m = "gemini-3.7-flash,gemini-4-argon,claude-opus-5-5,gpt-5.4,gpt-5.5,gpt-6.1-sol,gpt-6-luna,gpt-5.6-luna"
$s = Read-Host "ANTHROPIC_API_KEY" -AsSecureString
$env:ANTHROPIC_API_KEY = [Runtime.InteropServices.Marshal]::PtrToStringBSTR([Runtime.InteropServices.Marshal]::SecureStringToBSTR($s))
$s = Read-Host "GEMINI_API_KEY" -AsSecureString
$env:GEMINI_API_KEY = [Runtime.InteropServices.Marshal]::PtrToStringBSTR([Runtime.InteropServices.Marshal]::SecureStringToBSTR($s))
$s = Read-Host "OPENAI_API_KEY" -AsSecureString
$env:OPENAI_API_KEY = [Runtime.InteropServices.Marshal]::PtrToStringBSTR([Runtime.InteropServices.Marshal]::SecureStringToBSTR($s))
```

**Antes de T13, lo decide el humano (review de F-083, `progress/review_F-083.md`):**

- **O1 · Producción ya no usa las referencias de la tabla.** Según el líder, desde el 20-10 producción usa `gemini-4-argon` en IA1 y `gpt-6.1-sol` en IA2–IA4. La tabla sigue a `infra/create_capps.ps1` (IA1 `gemini-3.7-flash`, IA2 `gpt-5.4`, IA3/IA4 `claude-opus-4-8`), así que R3 pasa hoy, pero T13–T15 compararían contra modelos retirados y prepararían IA2 con 3.7-flash e IA4 con Opus 4.8. **Recomendación: F-085 antes de pagar T13**; después, quien se fusione segunda ajusta `referencias` y `papel` de la tabla y hace que R3 lea el proveedor de sv5 (`IA3_PROVIDER`/`IA4_PROVIDER`).
- **O2 · No pagar IA3 ni IA4 hasta F-084.** El banco de IA3/IA4 no discrimina (52 de los 59 casos de INPUTS sin líneas de contrato, R-1 del informe): con los mismos fallos en todos los modelos, R33 podría decir «cambiar» al más barato sin que el banco lo sostenga.

**T13 · humo** (≈ 2–4 USD). Dice qué modelos fallan por formato (PDF en las Luna, `max_tokens` con pensamiento, Opus 5.5 con `tool_choice` auto), qué modelo sirve Google a `gemini-3.7-flash` y deja tokens medidos para la estimación siguiente.

```powershell
& $py -m evals.comparar_modelos --fase IA1 --modelos $m --casos GEN-001,HOR-001 --estimar
& $py -m evals.comparar_modelos --fase IA1 --modelos $m --casos GEN-001,HOR-001
& $py -m evals.comparar_modelos --fase IA3 --modelos $m --casos GEN-001 --estimar
& $py -m evals.comparar_modelos --fase IA3 --modelos $m --casos GEN-001
```

VERDE: dos secciones nuevas en `progress/comparar_modelos_F-083.md`, con la columna «Modelo servido» y «Parada» rellenas, y sus líneas `GASTO:`. Si un modelo sale con todo `ERROR`, el líder lo revisa y decide si pasa a `excluido` en la tabla.

**T14 · tanda 1**: las cuatro fases, una invocación por fase, siempre `--estimar` antes. Estimación sin medir (×1,5, 2026-10-20): IA1 ≈ 37 USD, IA2 ≈ 8, IA3 ≈ 64, IA4 ≈ 9 (≈ 118 en total). Tras el humo bajan: usan los tokens medidos. **IA3 necesita `--tope-usd 70`** (con 60 para antes de gastar, código 2).

```powershell
& $py -m evals.comparar_modelos --fase IA1 --modelos $m --estimar
& $py -m evals.comparar_modelos --fase IA1 --modelos $m --tope-usd 60
& $py -m evals.comparar_modelos --fase IA2 --modelos $m --estimar
& $py -m evals.comparar_modelos --fase IA2 --modelos $m
& $py -m evals.comparar_modelos --fase IA3 --modelos $m --estimar
& $py -m evals.comparar_modelos --fase IA3 --modelos $m --tope-usd 70
& $py -m evals.comparar_modelos --fase IA4 --modelos $m --estimar
& $py -m evals.comparar_modelos --fase IA4 --modelos $m
```

**IA3 e IA4, no hasta F-084 (O2)**: 52 de los 59 casos de INPUTS no traen líneas de contrato y hoy esas dos fases apenas miden el modelo (R-1 de `progress/impl_F-083.md`). Lo mismo vale para el humo de IA3 de T13.

VERDE: una sección por fase con su recomendación (marcada «provisional (1 repetición)») y la suma de `GASTO:` dentro de los 200 USD de P3.

**T15 · finalistas**: por fase, la referencia y los dos primeros de la banda de T14, con 3 repeticiones. Ejemplo para IA1 (cambiar `<a>,<b>` por los de la banda):

```powershell
& $py -m evals.comparar_modelos --fase IA1 --modelos <a>,<b> --repeticiones 3 --estimar
& $py -m evals.comparar_modelos --fase IA1 --modelos <a>,<b> --repeticiones 3 --tope-usd 60
```

VERDE: recomendación sin marca de provisional por fase; es la base de la feature que cambie el modelo de producción.

Al terminar, siempre:

```powershell
Remove-Item env:ANTHROPIC_API_KEY, env:GEMINI_API_KEY, env:OPENAI_API_KEY, env:PYTHONPATH
Remove-Variable s, py, m
```

Códigos de salida: 0 hecho, 1 ningún candidato dio resultado, 2 parada antes de gastar, 3 cortado por `--tope-usd` (el informe se escribe con lo hecho). Tras cada corrida, versionar `progress/comparar_modelos_F-083.md` (no lleva valores); `evals/salidas/` no se versiona.

Hallazgos que el humano debe conocer:
- `gemini-3.7-flash` (IA1 en producción según `infra/create_capps.ps1`; ver O1) está descontinuado y Google lo redirige a `gemini-3.8-flash` (página oficial del modelo, 2026-10-12). Renombrarlo en `infra/` queda fuera.
- La línea base de F-075 (IA1 141, IA2 2, IA3/IA4/E2E 408/27/537) probablemente se midió con los defectos del runner (`gemini-2.5-flash`, `gpt-5`, e IA3/IA4 con gemini), no con los modelos de producción: el informe no registra el modelo.
- El cliente de Claude fuerza la herramienta, y `claude-opus-5-5`, `claude-sonnet-5-5` y `claude-fable-5-1` lo rechazan con 400.
- «Luna» es la gama Luna de OpenAI: existen `gpt-6-luna` y `gpt-5.6-luna`. No existe `gpt-6.1-luna`.

Las llamadas de pago son T13–T15, MANUAL del humano, con los comandos de design §8. Ningún agente gasta.

**F-080 · CERRADA (`done`, 2026-10-20).** Desplegada en sv3 (`r20261019-1114`); validación: su suite (36 tests) y el log de sv3 del Bloque E del plan de pruebas. Resumen en `history.md`.

**F-075 · CERRADA (`done`, 2026-10-21).** Desplegada (sv5 → sv6 → sv3 → sv4 → sv2, r20261019); B1–B4 en verde el 2026-10-20 (dfdc8aab: valoración directa y alta `simulado`). El pie (B5) se observará en el próximo albarán que lo traiga. Resumen en `history.md`.

**F-073 · CERRADA (`done`, 2026-10-21).** Desplegada en sv3 (r20261019-0952, y con F-080 en r20261019-1114); paso 0 en verde el 2026-10-20 (54b82479, dedf011a, 53337da7 → FEYMACO, CTSU24/0466). El log del próximo albarán sin CIF se observa sin bloquear. Resumen en `history.md`.

**F-077 · PUNTO 4 EN ROJO (2026-10-22 22:22 local, líder en Chrome, con el sí del humano):** en `d550baa3` (ANFERSA 0692, elegida porque sv9 la frena por `fecha_no_plausible`) se desbloqueó la línea 788 (POST `/lines/788/desbloquear`, autorizado), se escribió `zzzz` en su partida (el combo mostraba «Cargando partidas…») y se pulsó «Guardar y aprobar» (con `alert`/`confirm` redirigidos a una lista en la página para no bloquear la extensión). RESULTADO: **ningún aviso**, ningún PATCH de fila, **PUT de aprobación 200** y recarga «Documento guardado y aprobado»: la fila con `zzzz` NO se trató como fila pendiente, así que la validación de partidas no saltó. Daño: ninguno en Sigrid (sv9 → `revisar`, `fecha_no_plausible`, intento 4); en BBDD el albarán quedó `approved=true` (por residuos@ruesma.es, la sesión del navegador), la línea 788 con CD2.14 (el `zzzz` no se guardó) y desbloqueada. Punto 5 aceptado por el humano con la evidencia de uso real (19 aprobaciones de Óscar Domingo con filas guardadas, registradas en Sigrid). F-077 sigue `blocked`: hay que reproducir en local (¿la fila solo cuenta como pendiente tras el evento `change`/la carga de la lista?) y arreglar antes de cerrarla.

**F-077 · `blocked` (2026-10-17): review APPROVED (pasada 2), fusionada en `dev`; espera la MANUAL T14, que hace el
líder en el navegador tras desplegar sv4 (abajo)** — rama
`feature/F-077-guardar-y-aprobar` (worktree `../albaranes-F-077`), `dev` fusionado. Spec v2 en
`specs/F-077-guardar-y-aprobar/` (con las notas de implementación aceptadas en review); informe:
`progress/impl_F-077.md`; review: `progress/review_F-077.md`; mutación: `progress/mutacion_F-077.md`. Solo sv4, rigor
`estandar`. *Junction* `.venv` de sv4 en el worktree (quitarla con `cmd /c rmdir` antes de `git worktree remove`).
**T14 (líder, 2026-10-18, sv4 `r20261018-1741`):** punto 1 VERDE (panel rojo «No admitido», «Línea 2: La línea no
tiene descripción», title `falta_descripcion`, fila 386; 385/386 sin ⚠). Punto 2 VERDE tras F-078 T14 («Simulado (no
grabado)», sin el motivo). Punto 3 VERDE en lo negativo: 12 de 12 albaranes con filas Contrato (son todos los de la BBDD),
ningún ⚠ en Nueva ni en Contrato coincidentes; no hay hoy ningún caso positivo (Contrato con lectura distinta) que mirar.
Pendientes: punto 4 (`zzzz`, ficha que elija el humano) y punto 5 (solo si hay una corrección real).

#### F-077 · MANUAL T14 (la hace el LÍDER en el navegador, con el humano)

**Cuándo y dónde encaja.** Tras el APPROVED, la fusión en `dev` y `init.sh` en verde en el árbol principal. sv4 desde
`dev` lleva F-078 y F-076: mientras su **secuencia combinada** (bloque «F-076 · MANUAL») siga pendiente, F-077 se
despliega en su **paso 4** (`deploy.ps1 -Only sv4`, lo lanza el humano) y esta T14 va **justo después**; el punto 1
va siempre **antes del paso 6** (F-078 T14), que deja `86c13097` en `simulado`. Nunca sv4 suelto antes del paso 3. Si
la secuencia ya está hecha, el humano despliega sv4 con `. .\00_vars.ps1`, `. .\00_capps_vars.ps1`,
`.\deploy.ps1 -Only sv4` y `.\check_deploy.ps1` (en `infra\`; VERDE: sv4 en el tag nuevo).

Precondición: sv4 con `ALTA_SIGRID_DESDE_UTC` puesta y `ALTA_SIGRID_COMMIT=false`. **Acciones marcadas
[ESCRIBE EN PRODUCCIÓN]: cada una necesita el sí expreso del humano en el chat, para esa acción, antes de pulsar.**
El resto solo abre fichas y mira (sin escribir nada).

1. **Solo lectura, ANTES del paso 6.** Abrir la ficha de `86c13097-98f8-4e4b-91af-6a378c28d9cf`. VERDE: el panel
   «Alta en Sigrid» sale **en rojo** con «Error en el alta en Sigrid: No admitido» y, en su lista de motivos,
   **«Línea N: La línea no tiene descripción»**, con N la posición de la fila 386 en la tabla de líneas de la ficha
   (al pasar el ratón, `falta_descripcion`); las filas 385 y 386 (manuales) sin ⚠ de partida. Si el panel dice en su
   lugar «Sigrid no ha respondido en 5 minutos…», se comprueba en solo lectura `SET default_transaction_read_only =
   on; SELECT m.approved_at_utc, a.approved_at_utc, a.estado FROM albaran_documents_merge m JOIN albaran_altas_sigrid
   a ON a.document_id = m.id WHERE m.id = '86c13097-98f8-4e4b-91af-6a378c28d9cf';`: si los dos instantes difieren, se
   reaprobó sin respuesta de sv9 (el panel es correcto, pero el punto no se puede verificar: se avisa al humano).
2. **Solo lectura, tras el paso 6** (F-078 T14, autorizado en su bloque). Reabrir `86c13097`. VERDE: panel sin
   rojo (no `error`) con «Estado: Simulado (no grabado)» y sin el motivo «La línea no tiene descripción».
3. **⚠ de partida (solo lectura).** En fichas que el humano indique (o las ya abiertas): ⚠ solo en filas «Contrato»
   cuya partida leída no coincide, con tooltip «… · No coincide con la partida leída en el albarán (X)»; en «Nueva»,
   manuales o partes de un reparto, ningún ⚠. VERDE: así en todas las vistas.
4. **Partida no válida (no escribe nada si sale verde).** En una ficha pendiente que elija el humano: escribir `zzzz`
   en la partida de una fila y pulsar «Guardar y aprobar». VERDE: aviso «Hay partidas no válidas (en rojo)…», casilla
   en rojo y, en F12 → Red, **ninguna** petición PATCH ni PUT. Después, recargar sin guardar (la fila vuelve como
   estaba y el albarán sigue pendiente). Si saliera alguna petición, es el defecto: parar y avisar.
5. **[ESCRIBE EN PRODUCCIÓN] «Guardar y aprobar» con filas cambiadas.** Solo si el humano tiene un albarán pendiente
   que **necesite de verdad** corregir una o más filas: la ficha y los valores los elige él (nada inventado: con
   `COMMIT=false` sale `simulado`, pero un «Solicitar alta» posterior con `COMMIT=true` mandaría esos valores a
   Sigrid). Escribe en producción: (a) el **PATCH de cada fila** cambiada (`…/conciliacion/campos?bloquear=1`: la
   guarda y la bloquea), (b) el **PUT de aprobación** de la cabecera y (c) la **publicación en `q-feedback`** del alta
   para sv9. Con el sí expreso del humano para esas tres, cambiar las filas **sin** pulsar su «Guardar» y pulsar
   «Guardar y aprobar» (aceptar la confirmación de la suma si sale). VERDE: la **misma ficha se recarga aprobada**
   (solo lectura, con el mensaje de guardado) con las filas guardadas con los valores nuevos; el panel dice «Alta en
   curso…» sin estado viejo ni botones, F12 → Red enseña `/alta-sigrid/fase` cada 3 s, y en segundos la ficha se
   recarga sola con el resultado de sv9 (lo esperable con `COMMIT=false`: «Estado: Simulado (no grabado)»; si sale
   `no_admitido`/`revisar`/`error`, en rojo y con sus motivos en texto). **Si no hay ninguna corrección real
   pendiente, este punto no se hace:** «guardar las filas antes de aprobar» queda cubierto por
   `tests/test_f077_guardar_y_aprobar_js.py` (23 tests con node) y se anota así.

Con el verde de 1–4 (y el de 5 o su «no aplica» anotado), el líder lo anota en `progress/impl_F-077.md` (§6) y
F-077 pasa a `done`.

**F-076 · `blocked` (2026-10-17): review APPROVED (pasada 2), fusionada en `dev`; espera las MANUAL T18–T20 (secuencia combinada con F-078, abajo)** — rama `feature/F-076-normalizar-partidas`
(worktree `../albaranes-F-076`), `dev` fusionado (F-078 incluida). T1–T17 y T5b hechas; T18–T20 son MANUAL del humano
(abajo). Informe: `progress/impl_F-076.md`; mutación: `progress/mutacion_F-076.md`. `azure-apps` `8a6f63c` (sin
push). *Junction* `.venv` de sv4 en el worktree (quitarla con `cmd /c rmdir` antes de `git worktree remove`).

#### F-076 · MANUAL del humano (T18–T20), comandos para PowerShell

Cuándo: tras el APPROVED del reviewer, la fusión de `feature/F-076-normalizar-partidas` en `dev` y `init.sh` en
verde en el árbol principal.

**Secuencia combinada F-078 + F-076 (úsala mientras las MANUAL T12–T14 de F-078 sigan pendientes).** El despliegue
de sv6 y sv4 de F-076 lleva también F-078 (está en `dev`), así que va todo en este orden, en UNA consola de
PowerShell 5.1 (cada paso con su `cd`; sin `&&`). Si un paso no da su VERDE, para ahí.

> **Conexión a producción (corregido el 2026-10-17).** El `.env` de sv6 apunta a `localhost` (la BBDD local): los
> scripts `rellenar_filas_f078` y `medir_f076_partidas` leen la de Azure solo si la consola lleva las `PG_*` de Azure,
> que mandan sobre el `.env` (pydantic-settings). La contraseña sale de Key Vault a la variable, nunca a un fichero, y
> se borra al terminar. Pega estas dos funciones al abrir la consola y llama a `Usar-PgAzure` antes de cada script
> (los pasos ya lo hacen) y a `Quitar-PgAzure` al acabar. Sin ellas, el script lee (y con `--aplicar`, escribiría) la
> BBDD local: así salió la primera T12 del 17-10 (46 filas, ids 973–1052).

```powershell
function Usar-PgAzure {
  $env:PG_HOST = "psql-albaranes-rs9k2.postgres.database.azure.com"
  $env:PG_USER = "ruesmaadmin"
  $env:PGSSLMODE = "require"
  $env:PG_PASSWORD = az keyvault secret show --vault-name kv-albaranes-rs9k2 --name PG-PASSWORD --query value -o tsv
}
function Quitar-PgAzure { Remove-Item env:PG_HOST, env:PG_USER, env:PG_PASSWORD, env:PGSSLMODE -ErrorAction SilentlyContinue }
```

```powershell
# 1. sv6 local: tenacity (F-076) y lectura de F-078 T12 (solo lectura, BBDD de Azure)
cd C:\Users\pgris\PycharmProjects\albaranes\services\albaran-valoracion-persist
.\.venv\Scripts\python.exe -m pip install "tenacity>=8.2"
Usar-PgAzure
.\.venv\Scripts\python.exe -m scripts.rellenar_filas_f078
Quitar-PgAzure
#    VERDE: ids entre 362 y 545 (Azure) y cuadra con la medición del líder del 17-10 (102 filas revisadas, 94 que
#    cambiarían: 91 descripcion_linea, 27 unidad_albaran, 21 cantidad_convertida, 385 y 386 dentro; 0
#    unidad_contrato, 0 precio). Frente a spec §3 (93/7/6), lo de más son vinculadas a las que se pone la unidad del
#    contrato y sin vincular con la convertida = cantidad (factor 1): no cambia lo que manda sv9. Ids ≥ 900 ⇒ local.

# 2. variables de F-076 en sv6 y despliegue de sv6
cd C:\Users\pgris\PycharmProjects\albaranes\infra
. .\00_vars.ps1
. .\00_capps_vars.ps1
.\set_partidas_sv6.ps1
.\deploy.ps1 -Only sv6
#    VERDE: set_partidas_sv6.ps1 dice OK en las 8 variables y en «secreto sigrid-key» y termina en «Ajustes de
#    F-076 aplicados a ca-sv6-valorador»; deploy.ps1 termina sin error.

# 3. relleno de F-078 con --aplicar (autorización expresa del humano) y su relectura
cd C:\Users\pgris\PycharmProjects\albaranes\services\albaran-valoracion-persist
Usar-PgAzure
.\.venv\Scripts\python.exe -m scripts.rellenar_filas_f078 --aplicar
.\.venv\Scripts\python.exe -m scripts.rellenar_filas_f078
Quitar-PgAzure
#    VERDE: la primera acaba en «Escritas N filas. Releído: 0 pendientes.» (si no, ROLLBACK y código 2);
#    la segunda, en «Filas que cambiarían: 0».

# 4. despliegue de sv4 y comprobación
cd C:\Users\pgris\PycharmProjects\albaranes\infra
.\deploy.ps1 -Only sv4
.\check_deploy.ps1
#    VERDE: check_deploy con sv6 y sv4 en el tag nuevo.
#    Si F-077 ya está en dev, este sv4 la lleva: su T14 (bloque «F-077 · MANUAL T14») va justo después, y su
#    punto 1 (86c13097 en no_admitido, solo lectura) siempre antes del paso 6.

# 5. relectura de F-078 tras sv4 (cierra la ventana entre el relleno y sv4)
cd C:\Users\pgris\PycharmProjects\albaranes\services\albaran-valoracion-persist
Usar-PgAzure
.\.venv\Scripts\python.exe -m scripts.rellenar_filas_f078
Quitar-PgAzure
#    VERDE: «Filas que cambiarían: 0». Si da más: repite el paso 3 (misma autorización) y este.
```

6. **F-078 T14** (con F-077 desplegada, después de su punto 1 de T14): «Solicitar alta en Sigrid» en `86c13097-98f8-4e4b-91af-6a378c28d9cf` desde la ficha y, en solo
   lectura, `SET default_transaction_read_only = on; SELECT estado, historial_json FROM albaran_altas_sigrid WHERE
   document_id = '86c13097-98f8-4e4b-91af-6a378c28d9cf';`. VERDE: ya no termina en `no_admitido` con
   `falta_descripcion` (con `ALTA_SIGRID_COMMIT=false`, `simulado`). Comprobación en la ficha, la del bloque de F-078.
7. **F-076 T19** (abajo, tal cual) y, tras la primera revaloración, la comprobación del log de T18 (abajo). VERDE: los
   de cada uno.

Con eso cierran F-078 (T12–T14) y F-076 (T18–T19); queda T20.

**T18 · si F-078 ya está cerrada: variables de sv6 → sv6 → sv4** (misma consola; con F-078 pendiente, usa la
secuencia combinada de arriba en su lugar):

```powershell
cd C:\Users\pgris\PycharmProjects\albaranes\infra
. .\00_vars.ps1
. .\00_capps_vars.ps1
.\set_partidas_sv6.ps1
.\deploy.ps1 -Only sv6
.\deploy.ps1 -Only sv4
.\check_deploy.ps1
```

VERDE si `set_partidas_sv6.ps1` dice `OK` en las 8 variables (7 valores + `SIGRID_API_FUNCTION_KEY` con
`secretref:'sigrid-key'`) y en `secreto sigrid-key`, y termina en «Ajustes de F-076 aplicados a ca-sv6-valorador»;
`check_deploy.ps1` con sv6 y sv4 en el tag nuevo. Tras la primera valoración (T19), el log de sv6 no debe decir
`partidas_obra_no_disponibles`:

```powershell
az containerapp logs show -n ca-sv6-valorador -g $RG --tail 300 | Select-String "partidas-obra|partidas_obra_no_disponibles"
```

Debe salir `[partidas-obra] obra=… hojas=… segundos=…` y ninguna línea con `partidas_obra_no_disponibles`. Vuelta
atrás sin redesplegar: `az containerapp update -n ca-sv6-valorador -g $RG --set-env-vars PARTIDAS_OBRA_NORMALIZAR_ENABLED=false`.

**T19 · revalorar los pendientes y medir (solo lectura).** *Antes, el paso 0 de F-073 (`54b82479` y los otros dos merges con «Elegir proveedor» → FEYMACO).* En la ficha de sv4 de cada uno, «Valorar ahora»:
`2792cf3b`, `53337da7`, `54b82479`, `dedf011a` (0694); `41ab0dc1` (0711); `09643c2b`, `89e463a7`, `bef66bce`,
`f96c6dbe` (0720); `ca609aee` (0723); `25c5d647` (0724). **`355449d9` NO se revalora** (6 filas guardadas: se
perderían, F-058): su partida se corrige a mano en la ficha (`CI.04.18` ⇒ `CI.4.18`, `CI.03A.02` ⇒ `CI.03A.2`).
Después, la medición (sv6 del árbol principal; PostgreSQL de **Azure** con `Usar-PgAzure` —el `.env` de sv6 apunta a
local—, en solo lectura; las tres `SIGRID_API_*` se toman del `.env` de sv3 SOLO para esta consola, sin imprimirlas):

```powershell
cd C:\Users\pgris\PycharmProjects\albaranes\services\albaran-valoracion-persist
.\.venv\Scripts\python.exe -m pip install "tenacity>=8.2"
Get-Content ..\albaranes-persistencia\.env | Where-Object { $_ -match '^(SIGRID_API_(BASE_URL|FUNCTION_KEY|DATABASE))=(.*)$' } | ForEach-Object { Set-Item -Path "env:$($Matches[1])" -Value $Matches[3].Trim('"') }
Usar-PgAzure
.\.venv\Scripts\python.exe -m scripts.medir_f076_partidas
Quitar-PgAzure
Remove-Item env:SIGRID_API_BASE_URL, env:SIGRID_API_FUNCTION_KEY, env:SIGRID_API_DATABASE
```

VERDE si «normalizable sin normalizar» da **0** en pendientes y las 6 sin candidata de `progress/spec_F-076.md`
§2.2 cuentan en «fuera de lista» con el motivo `partida_fuera_de_lista` (pendientes). Los aprobados antes de DESDE
(12 líneas `CI.4.18`) pueden seguir en «normalizable sin normalizar / aprobado»: sv9 los ignora (R6 de F-053).

**T20**: `bash harness/init.sh` en verde en el árbol principal tras T18–T19; con eso, F-076 `done`.

> **Notas para quien fusione después de F-076:**
> - **F-077** (mismas líneas de `review_repository.py`, `review_models.py` y `document_detail.html`): el
>   `agree_partida` de F-077 ya no es literal: lo da `coincide_partida` (clave de comun) en los dos sitios. El `title`
>   de la casilla de partida debe quedar «descripción ⏎ [nota F-076] ⏎ [aviso F-077]»: la descripción de la partida;
>   si ✓ normalizada, «Normalizada: X → Y» (F-076, `_nota_normalizada`); si ⚠, el aviso de F-077 («No coincide con
>   la partida leída en el albarán (X)»). Las dos notas no coinciden nunca (✓ y ⚠ se excluyen). Hoy F-076 une
>   descripción y nota con « · » (design §5.4); quien fusione F-077 compone el `_title_partida` de la plantilla con
>   el separador que elija para los tres y ajusta R22 de F-077 («el cálculo de `agree_partida` no cambia» ya no es
>   cierto).
> - **F-075**: su `ValoracionDirectaBuilder` recibe ya el sobre normalizado (el pipeline rebinda `envelope` antes de
>   la rama `no_contract`); debe llamar a `NormalizadorPartidas.anotar(header, lines, normalizacion)` tras
>   `completar_registros` (F-078) en su rama.
> - **F-049**: `ruesma_comun/sigrid/partidas.py` (add/add): se queda el suyo conservando `resolver_partida_obra`,
>   `CachePartidasObra`, la guarda de no hoja y `leer_partidas_obra` con F-070; comun pasa a 0.9.0; sv4 ya hace su R11.

**F-078 · CERRADA (`done`, 2026-10-20).** Desplegada en sv6 (`r20261019-0949`) y sv4 (`r20261019-0955`); MANUAL T12–T14 en verde el 2026-10-18. Resumen en `history.md`.

**F-064 · `blocked` (2026-10-18): review O1 APPROVED, T9 y T10 del humano en VERDE; solo queda la MANUAL T12.**
**T12 en marcha:** sv2 desplegado por el humano el 2026-10-18 (`r20261018-1420`, revisión única tras `fix_revisiones`); la
vigilancia de `proveedor_cif_propio:` cuenta desde `2026-10-18T12:22:00Z` hasta el 2026-10-25 (la consulta la hace el líder, solo lectura).
Rama `feature/F-064-proveedor-en-prompts`, worktree `../albaranes-F-064` (*junction* `services\albaranes-front\.venv`:
quitarla con `cmd /c rmdir` ANTES de `git worktree remove`). T9 (comparador, `progress/comparar_proveedor_F-064.md`):
C1/C2/C3 OK, emisor base 8 → rama 9, CIF cliente 0/0; AVISO: el banco no reproduce el incidente (propuesta al humano:
añadir el albarán real de F-063, `progress/impl_F-064.md` §9). T10 (`progress/evals_F-064.md`, fuera de git): IA1 152
(≤ 154), IA2 2 (≤ 4). Siguiente: fusionar en `dev` (ya lleva `dev` fusionado, 2026-10-18), `init.sh` en el árbol principal y **T12: desplegar SOLO sv2 y
vigilar `proveedor_cif_propio:` en merges nuevos una semana** (comandos en `progress/impl_F-064.md` §6). Con T12 en
verde, pasa a `done`.

**F-072 · CERRADA (`done`, 2026-10-16).** MANUAL T16 en verde. Resumen en `history.md`.

**Siguiente (orden del humano, 2026-10-18):** F-075 → F-071 → F-074 (la última, decisión del humano). Mientras, los
despliegues pendientes de F-078, F-076, F-077 y F-073. Después: F-080, F-079, F-081, F-058, F-059, F-049. Specs de F-076, F-077 y F-078 APROBADAS en sus ramas. Escritura en Sigrid apagada (`COMMIT=false`)
hasta desplegar F-078, F-076 y F-077.

> **Nota para quien fusione después de F-078:**
> - **F-075**: su `ValoracionDirectaBuilder` persiste por otra rama del pipeline de sv6; debe llamar a
>   `completar_registros` antes de cada `replace_valuation` con líneas (lo exige
>   `test_f078_pipeline_todo_replace_valuation_con_lineas_va_tras_completar_registros`).
> - **F-077**: su R11 (validación del PUT de «Guardar y aprobar») incluye ahora la R17 de F-078 («Líneas sin
>   descripción: …»), y la fila 13 de `tests/f065_bbdd.py` lleva `descripcion_linea = 'PORTES'`.
> - **Conflictos de texto**: F-076 en `run_valuation_pipeline.py` (sv6); F-075 y F-077 en `review_repository.py`, y
>   F-077 también en `document_detail.html` (sv4). Sin interacción de reglas (`progress/spec_F-078.md` §5).

**F-070 · CERRADA (`done`, 2026-10-15).** Desplegada en sv3, sv4 y sv9 (r20261015-0947) y verificada en pantalla por el
humano (T13). Los merges antiguos con obra de 3 cifras los corrigió el humano a mano en la BBDD. Resumen en `history.md`.

**F-053 · CERRADA (`done`, 2026-10-16).** Alta en Sigrid de lo aprobado (sv9). Código APROBADO (v8, pasada 2) y en
`dev` con `init.sh` en verde; T51 y T29 hechas por el humano en Azure: primera grabación real `AC26/29714` (A27239,
obra 0678) correcta en Sigrid e idempotencia en verde. **sv9 vuelve a SIMULACIÓN** (`ALTA_SIGRID_COMMIT=false`,
revisión `--0000003`) por orden del humano hasta que estén desplegadas F-078, F-076 y F-077; reabrir solo con su
autorización. Resumen en `history.md`.

**F-065 · CERRADA (`done`, 2026-10-13)**: fases 1, 2, 3 y 3 bis (pasadas 1–5) APROBADAS, en `dev` (`53515de`) con
`init.sh` en verde (raíz 1083, sv4 1287) y sv4 desplegado (`r20261013-1836`). MANUAL T19, T27 y T35 hechas por el
humano (T19 punto 6, obra sin partidas, solo con tests). Resumen en `progress/history.md`. Lo aplazado: **F-068**
(F7 con el foco fuera de la fila abre el diálogo de Edge; O8/O9 de la review). Guía de uso para los administrativos:
borrador en el Outlook del humano (2026-10-13). Siguiente: F-053 (usuario del alta = correo de quien usa la app,
respaldo el del humano; T0b/T0c autorizadas; O1 = botón de reintento; 10 equivalentes aceptados) y revisar con el
humano F-066, F-067, F-058, F-059 y X4.

**F-063 · `done` (2026-10-08)**, fusionada en `dev` con `init.sh` en verde. Pendiente del humano: desplegar solo sv3; en los merges `b1d3e179` y `401d9c00`, «Elegir proveedor» FEYMACO a mano. Comandos de la MANUAL T8 en `progress/impl_F-063.md` §7.

**F-062 · `done` (2026-10-08)**, fusionada en `dev` (`d052106`) con `init.sh` en verde. Pendiente del humano: despliegue de solo sv3 y vigilancia T12 (comandos abajo).

> Podado el 2026-10-01 al cerrar F-052 (C2 de `progress/review_F-052.md`). El `current.md` anterior, íntegro, está
> en `progress/historico/current_2026-10-01_cierre_F-052.md`; el resumen de F-052, en `progress/history.md`.
> Aquí solo queda lo vivo. Lo que manda sobre el estado de cada feature es `harness/features.json`.

### F-062 · MANUAL del humano (comandos exactos, PowerShell)

**T0b (opcional, recomendable antes de desplegar) · Anexo A.1 de `progress/spec_F-062.md`, SOLO LECTURA.** El
script del líder `diag_f062.py` abre la sesión con `default_transaction_read_only=on`, comprueba que
`SHOW transaction_read_only` da `on` antes de consultar (si no, aborta), no imprime credenciales ni precios y
lanza A.1, A.2 y A.3 seguidas. Con el venv de sv3 del árbol principal (trae `psycopg`) y el mismo `.env` con los
`PG_*` de la BBDD `albaranes` de Azure que usaste para `diag_proveedor.py` (6.1–6.3):
```powershell
& "C:\Users\pgris\PycharmProjects\albaranes\services\albaranes-persistencia\.venv\Scripts\python.exe" "C:\Users\pgris\AppData\Local\Temp\claude\C--Users-pgris-PycharmProjects-albaranes\f36c80f5-0cba-463e-95e9-161d51e3f583\scratchpad\diag_f062.py" "<ruta del .env con los PG_* de Azure>"
```
Si el scratchpad ya no existe, el SQL íntegro está en el Anexo de `progress/spec_F-062.md`. Criterio: en
`==== A.1`, ningún `otro_proveedor` en un documento que la regla de R3–R4 habría dado por candidato claro (eso
sería una corrección equivocada). Anotar el resultado en `progress/spec_F-062.md` §2; si sale alguno, volver a
la spec antes de desplegar.

**T12 (tras fusionar en `dev` y con `init.sh` en verde en el árbol principal) · desplegar SOLO sv3:**
```powershell
cd C:\Users\pgris\PycharmProjects\albaranes\infra
. .\00_vars.ps1
.\deploy.ps1 -Only sv3
.\check_deploy.ps1
```
Criterio: `check_deploy.ps1` muestra sv3 con la revisión y el tag recién construidos, réplicas arriba, y el resto
de apps sin cambios. Después, **unos días de vigilancia con la consulta A.3** (solo lectura, mismo script y mismo
comando que T0b: su bloque `==== A.3 correcciones F-062` lista cada merge activo con `proveedor_cif_corregido`).
Revisar en sv4 cada documento listado: CIF aplicado = proveedor real y `contratos_busqueda_resultado` =
`encontrados`. Un caso mal aplicado ⇒ `RED_PROVEEDOR_CORRECCION_ENABLED=false` en la Container App de sv3 (la
decide y la aplica el humano) y volver a la spec. No bloquea el `done`.

**F-051 · CERRADA (`done`, 2026-10-09): T22–T24 hechas por el humano (`progress/impl_F-051.md` §6 bis).** Antes: `blocked` (2026-10-06) y FUSIONADA en `dev`. Implementación APROBADA por el reviewer (pasada 2) e `init.sh`
en verde. **T21 hecha** (evals con LLM, 2026-10-06 11:07 UTC, informe local `progress/evals_F-051.md`): frente a F-048,
IA3 417→397 fallos, E2E 545→522, partida final 102→85; IA1 e IA4 iguales; los 4 casos que empeoran son variación del
modelo o recuento (GEN-005, RES-009, MOR-004). **Bloqueo:** T22, T23 y T24 (pruebas manuales en local y navegador)
aplazadas por decisión del humano «hasta que terminemos la escritura» (F-053); se fusiona en `dev` para que F-053 use
la regla de almacén. Pasa a `done` cuando el humano haga T22–T24. No desplegar sv6/sv4/sv2 con F-051 hasta entonces
salvo decisión expresa del humano.

**F-051 · implementación (histórico: `in_progress` del 2026-10-05 al 2026-10-06)** en la rama `feature/F-051-almacen-por-linea`
(worktree `../albaranes-F-051`, con `dev` fusionado el 2026-10-05, que trae F-054): almacén por línea, spec v4
aprobada por el humano en la PARADA 1 («si», 2026-10-05). Informe de spec en `progress/spec_F-051.md` §v4; el del
implementer, en `progress/impl_F-051.md` (la tarea en curso, en «F-051 · estado de la implementación», abajo).
**Todas las decisiones cerradas por el humano, sin preguntas abiertas.** D1 rehecha: «en el visor cuando una línea
no tenga partida que sea almacén» ⇒ almacén = partida final vacía, tenga o no marca (`partida_action` solo
trazabilidad); desaparece el estado «sin partida»; vaciar la partida en sv4 = elegir almacén (sin derivada, la fila
Sigrid sigue Sigrid); la confianza ya no resta por partida vacía. D2: cualquier familia; revisión no bloqueante en
destinadas. D3, D4, D5 (se pierde al revalorar ⇒ **F-058**) y D7 (**F-007 a `pending`**) confirmadas.
**Para otras ramas (no tocadas desde aquí)**: F-053 debe dar de alta como almacén toda partida final vacía
(desaparece `linea_sin_partida`); F-049 bloque C (T31): «Sin partida → almacén» = partida final vacía sin mirar la
marca (cierra su O4). Ambas cosas en `specs/F-051-almacen-por-linea/design.md`, «Contrato con F-053 y con F-049».
**Fichas nuevas en esta rama** (`pending`): **F-058** revalorar no pierde partidas ni almacén a mano (p2, `critico`),
**F-059** etiquetas legibles de motivos de revisión en sv4 (p3, `estandar`), **F-060** tipología de líneas
acopiables (p2, `critico`; decidir junto con la nueva spec de F-007 o fusionarlas).

### F-051 · estado de la implementación

- **T1–T20 y T25 hechas** (2026-10-05); informe en `progress/impl_F-051.md`. **T21–T24 son del humano**
  (evals con LLM y MANUAL; comandos en el informe, §6).
- **Review pasada 1: CHANGES_REQUESTED** (`progress/review_F-051.md`). **Pasada 2 hecha** (2026-10-05), informe en
  `progress/impl_F-051_pasada2.md`: H1 (el banco de evals compone sv6 con almacén y familias destinadas + test que
  recorre todos los puntos de composición), H2 (guardar solo envía la partida si cambió), H3 (test de R12 que
  ejecuta el JS con node), H4 (`azure-apps/albaranes.md`, commit en azure-apps), H5 (dictamen: R20 vale en
  cualquier fila Sigrid), H6 (quitar la junction con `cmd /c rmdir`, nunca `Remove-Item`), O2 (el aviso «pasará a
  NUEVA» no salta con la partida de la casada) y la **decisión del humano**: fuera de almacén el input pinta la
  partida FINAL. Falta la review de la pasada 2.
- **Para el humano**: ¿los ✓/⚠ de partida deben comparar con la final pintada o con la de la casada (hoy, la de la
  casada)? O1 se queda como está (decisión del humano).
- **T21 (previa) hecha** (2026-10-05, opción a del humano): RES-001…007 esperan almacén (`null`) en la línea 1, y
  (2.ª tanda, decisión del humano) las 12 líneas con el literal `ALMACEN`/`almacen` también. Libros
  `IA3_valoracion.xlsx` y `RESULTADO_FINAL.xlsx` del árbol principal ya corregidos (copia previa
  `*.20261005-1759.xlsx`) y fixtures regenerados desde ellos: sincronizados. Evals deterministas: 1025 → 972
  entradas FALLO/AVISO, ninguna nueva. Detalle y comandos de T21/T23: `progress/impl_F-051_t21_previa.md`.
- Entorno del worktree: *junction* `services/albaranes-front/.venv` → venv de sv4 del árbol principal (ignorada
  por git). Se quita con `cmd /c rmdir services\albaranes-front\.venv` ANTES de `git worktree remove`.

**F-054 · CERRADA (`done`, 2026-10-02)**, review de cierre APROBADA: sv1 ingiere los PDF **e imágenes** de correos
adjuntos (`message/rfc822`). Fusionada en `dev` (`639afbb`). Pendiente del humano: despliegue de sv1 y la
verificación MANUAL T12 (sección «F-054 · lo que queda» al final). Resumen en `progress/history.md`.

## LO PRIMERO AL ABRIR LA PRÓXIMA SESIÓN

- **F-053 `in_progress`**, fases 1 y 2 implementadas (bloque de arriba, `progress/impl_F-053_fase2.md`). Es la única
  `in_progress`. Siguiente: review de la fase 2; luego fusionar en `dev` e `init.sh` en el árbol principal.
- **F-051 · CERRADA (`done`, 2026-10-09)** tras T22–T24. Despliegue (lo pide el humano): sv6 → sv4 → sv2, junto con F-053.
- **F-054 · CERRADA (`done`, 2026-10-02)** y fusionada en `dev`. Pendiente del humano: `.\deploy.ps1 -Only sv1` +
  `.\check_deploy.ps1` desde `infra/` y la **T12 MANUAL** (procedimiento al final). La T12 no bloquea el `done`.
- **F-052 · CERRADA (`done`, 2026-10-01)**, fusionada en `dev` y desplegada (sección de abajo).
- **F-055** (IA2 elige el proveedor entre los de la obra): `pending`, prioridad 1. Depende de F-052.
- **Fichas nuevas del cierre de F-052** (`pending`, prioridad 2): **F-056** re-búsqueda doble en sv4 y **F-057**
  truncado sin comprobar en los clientes colindantes de sv4 y sv3.
- Crédito de OpenAI: resuelto. Los 3 albaranes del 2026-09-30 se procesaron hacia las 14:07 (nada en poison).

F-051 (con F-058, F-059, F-060 y el cambio de F-007) está en `dev`. F-053 y F-061 (familia `medios_auxiliares`, de
la P1 de F-053) están registradas en la rama de F-053.

## F-052 · cerrada, fusionada y desplegada (2026-10-01)

- Merge a `dev` por el humano (`a7a53ef`, subido a `origin/dev`). Despliegue del humano: sv3 `r20261001-1654`
  (DDL `contratos_busqueda_*` OK en producción, comprobado en Log Analytics) → sv4 `r20261001-1657` (100 % del
  tráfico; la revisión vieja seguía activa: `fix_revisiones.ps1 -Only sv4`).
- **T23 cerrada por el humano (2026-10-01)**: «hemos estado probando, no hace migrar nada de albaranes antiguos.
  da t23 por cerrada». Sin saneamiento de históricos (D5): si aparece alguno, se corrige a mano en sv4 con «Solo
  volver a buscar» o cambiando el CIF y guardando. Comando y SELECT de sospechosos, por si se necesitan: T23 en
  `specs/F-052-proveedores-truncados/tasks.md` y `progress/spec_F-052.md` §Anexo.

### 3. Observaciones de la review de cierre que siguen vivas

- **Re-búsqueda doble en sv4 → ficha F-056** (O-C2 + mejora menor de T22 + O-C8). La mejora de T22, tal como la
  anotó el humano: un «Guardar» pulsado mientras la ficha está en «Buscando…» relanza otra búsqueda, porque el
  rastro aún tiene el CIF/obra de antes. Inocuo (sv3 y sv6 reemplazan), pero es trabajo doble. Arreglo barato:
  mientras busca, sv4 no relanza si CIF y obra son los mismos con los que lanzó la búsqueda en curso. O-C2: el
  autoguardado del combo (obra y luego proveedor) publica dos re-búsquedas. O-C8: «Solo volver a buscar» con CIF y
  obra vacíos publica un mensaje que sv3 descarta sin sellar.
- **Truncado sin comprobar en los clientes colindantes → ficha F-057** (O-C4 + D6, que decía «ficha aparte» y no
  existía): `header_and_lines` de sv4 (`max_rows=1000`, sin `comprobar_truncado`) y `SigridApiObraClient` de sv3.
- **O-B2 · enseñar al humano** (nunca la aceptó por escrito): extensiones de R21, `replace_contratos` fallido →
  rastro `error`; `enabled=False` → sin sello. Consta en `history.md` como decisión.
- **El «1.000» ajeno, para el humano (otros dueños)**: `PycharmProjects/CLAUDE.md` dice que sigrid-api sirve «como
  máximo 1.000 filas por petición» y otros documentos de `azure-apps` lo repiten. El 1.000 era el `max_rows` del
  cliente; sigrid-api admite 500.000 (`docs/ARCHITECTURE.md` «Acceso a datos»).

### 4. PENDIENTE · portar a `arnes-base` (regla de propagación)

`harness/mutacion.py` cuenta a veces como VIVO un mutante muerto. 3 casos en F-052, sin causa encontrada: en
paralelo (4 workers, `07f89cf`) `sigrid_api_contrato_client.py:1081` y `verificar_f052_proveedores_obra.py:331`;
en serie (`dcca978`) `ruesma_comun/obras/codigo.py:39`. Los tres mueren reevaluados aislados con
`ejecutar_campania` en un worktree limpio (mismo intérprete y comando, `.pyc` purgado). Siempre en la dirección
conservadora. Abrir feature de arnés para reproducir y corregir, y portarla a `arnes-base`. Relacionada: F-041.

Propuesta de automejora de la review de cierre (no aplicada): que `init.sh` avise si `current.md` cita como vivo
(`in_progress`/`blocked`) un ID que `features.json` tiene `done`. Genérica: si se aplica, va también a `arnes-base`.

## Arrastre heredado (anterior a F-052; sin verificar desde su fecha)

Resumido del `current.md` anterior; el detalle, en el archivo de `historico/`. Antes de actuar, comprobar que sigue
vigente.

- **F-047** (`spec_ready`, aparcada el 2026-09-24): al retomarla, cablear `anadir_opcion_sin_correo` en el CLI del
  ciclo, pasar `correo=correos.cargar_correo(caso_id)` desde `ciclo.py` y traer
  `tests/test_f047_r5_seleccion_contrato.py`; nota al final de `specs/F-047-evals-ciclo-completo/tasks.md`. Faltan
  además los 130 supervivientes de `progress/mutacion_F-047.md`, T24–T26 y limpiar 28 worktrees huérfanos.
- **F-048**: confirmar que su despliegue (sv3 → sv2 → sv1 → sv4) está hecho; si no, va junto con el de F-052.
- **Pendientes del humano** (2026-09-24 y anteriores): meter un albarán por producción; decidir si se versionan los
  libros de `evals/ground_truth/`; MANUAL arrastradas de F-002 (liberan el merge de F-003), F-019 y F-027;
  reconciliar F-003 y F-004 antes de arrancarlas; histórico mal valorado en BBDD (sin backfill, se sanea
  revalorando desde sv4); actualizar los otros proyectos al arnés vigente; `mutacion_F-011.md` invalidada y
  `mutacion_F-002.md` en cuarentena (en `historico/`); un PDF versionado que incumple la norma
  (`services/albaranes-api/worker_input/0695 - Albaranes 2026.03.09-13-16.pdf`).
- **Mejoras del arnés propuestas y no aplicadas** (genéricas, irían a `arnes-base`): la caché de `init.sh` no se
  invalida cuando cambia `comun`; `PUERTA RUTAS SENSIBLES` sale `N/A` con la ficha en `blocked`; `CHECKPOINTS.md`
  no contempla la review por bloques; falso verde de `harness.cobertura --feature`; `harness.mutacion` no muta
  `in`/`not in`; avisar cuando el alcance de una feature arrastra el de otra.
- **Deudas menores**: RM2 solo dispara a 10×; marcas `[ADAPTAR]` en las specs de F-034 y F-035; ~1166 avisos de
  `ruff`; sv1-email e `infra` sin tests.

## Notas operativas (valen para cualquier sesión)

- **Los `impl_`, `review_` y `evals_` de features cerradas viven en `progress/historico/`**. Las **campañas de
  mutación NO se archivan**: F-039 las vigila por ruta fija y moverlas pone 8 tests en rojo. El porqué, en
  `progress/historico/README.md`.
- **Nada en paralelo**: dos suites a la vez tumban el proceso en Windows (`0xC0000142`). Y **una campaña de
  mutación muta el árbol principal**: mientras corra, no lanzar `init.sh` ni tests.
- **Un agente con demasiado contexto se cuelga en bucle.** Lanzar uno **nuevo y acotado** —diciéndole exactamente
  qué leer— lo resuelve y sale más barato. Un agente que se cuelga no pierde el trabajo commiteado: commit por tarea.
- **No ensuciar el árbol mientras un agente trabaja**: C5 exige árbol limpio, y tus cambios pueden colarse en el
  commit de otro.
- **Los agentes no deben usar scripts que reescriban ficheros versionados**; copias en el scratchpad.
- **Cuidado con las rutas de Windows en heredocs de Python**: `\U` de `C:\Users` se interpreta como escape unicode.
- **La máquina es compartida y se nota**: otra sesión corriendo triplica los tiempos y puede invalidar una campaña.
- **Un comando de verificación guardado en `progress/` puede caducar**: guarda también de qué depende.
- **El humano ejecuta él mismo** los `push`, los merges y las verificaciones MANUAL. Dale el comando listo para
  **PowerShell**, con `git -C <ruta>`, sin `&&` (su PowerShell 5.1 da error de parser) y con el criterio de verde.

## F-054 · lo que queda (cerrada el 2026-10-02)

- Informes archivados: `progress/historico/impl_F-054.md` y `progress/historico/review_F-054.md`; la campaña
  sigue en `progress/mutacion_F-054.md` (19/20 muertos, 1 equivalente). Resumen y decisiones en `history.md`.
- Al humano: merge de `feature/F-054-correo-adjunto-encadenado` a `dev`; luego, desde `infra/`,
  `.\deploy.ps1 -Only sv1` y `.\check_deploy.ps1`; después la T12 de abajo.
- Log de R23 nuevo en sv1: `sin adjuntos elegibles: ni directos ni correos adjuntos (total=N) → Errores` (sigue
  conteniendo «sin adjuntos elegibles», el texto que busca la T12 en los logs viejos).
- Al leer los logs de la T12 (O1 de la review): unos bytes basura no vacíos en un correo adjunto se leen como
  `text/plain` y salen como WARNING «sin ningun documento interior valido», no como ERROR «ilegible»; el
  destino es el mismo.

### PENDIENTE DEL HUMANO · verificación MANUAL de F-054 (T12, tras merge a `dev` y despliegue de sv1)

No bloquea el `done`. Procedimiento (design §10 y `tasks.md` T12):

1. Desde `infra/`: `.\deploy.ps1 -Only sv1` y `.\check_deploy.ps1`.
2. En Outlook, carpeta `Errores` del buzón de albaranes: localizar los correos cuyo único adjunto es un correo
   (icono de sobre; en los logs viejos de sv1: «sin adjuntos elegibles»).
3. Mover **uno** a la carpeta origen y **marcarlo como no leído** (el filtro de sv1 es `isRead eq false`).
4. Esperar un ciclo de polling y comprobar en los logs de la Container App de sv1: la línea INFO
   `att=<id> documentos interiores: N PDF y M imagen(es)`, el `intake encolado` de cada página y
   `movido a Procesados`; y el albarán en el front (sv4).
5. Si cuadra, repetir con el resto por tandas pequeñas.
6. Los mixtos que están en `Procesados` con el interior perdido **no** se mueven en bloque (re-ingerirían los
   PDF directos con otra `correlation_key`): uno a uno, si el humano lo decide.
7. Anotar aquí el resultado.
