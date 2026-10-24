<!-- progress/review_F-104.md -->
Revisión incremental desde afe5b6d (pasada 2). La pasada 1 (completa, `dev...afe5b6d`) queda resumida abajo.

# F-104 · Review (pasadas 1 y 2) · alcance T1–T7 (M1, M-D, M2, T8 y T9 fuera a propósito, D1)

**Veredicto: APPROVED.** La pasada 1 rechazó solo por la evidencia: la campaña manual no se podía reproducir
desde el informe. El delta `afe5b6d..1a66c6b` lo corrige y no toca código: solo `progress/mutacion_F-104.md`
y `progress/current.md`. Como no hay cambio de código, nada de lo aprobado queda invalidado.

**Nivel de rigor:** `critico`, declarado en `features.json`. Exige fase RED, cobertura, mutación con 0
supervivientes y las MANUAL listadas con su comando exacto.

## Pasada 2 (delta)
- `bash harness/init.sh`: **exit 0**. Raíz 1883; sv1 205, sv2 485, sv3 1576, sv4 1833, sv5 96, sv6 473
  (+1 skipped), sv9 1017; comun en verde por caché. Cobertura 100 % (4/4); tamaño `[OK]` (review 100/140).
- **Cambio 1: hecho.** La tabla manual trae una fila por mutante (M01…M17) con fichero:línea, texto exacto
  original → mutado, fallos sin `-x` y los comandos de test. Comparé con el fuente las líneas de M01–M05,
  M07, M09–M12 y M17, y coinciden.
- **Muestra nueva**, sobre una copia limpia en mi scratchpad (`rev104b`, idéntica al worktree según `cmp`),
  sin `-x`, con la base en verde antes de cada una:
  - M05 `clasificador.py:45` `_NO_ADMITIDO`→`_ERROR`: **6/135**;
  - M07 `alta_sigrid_models.py:138` texto = código: **5/50**;
  - M17 `_alta_sigrid.html:127` `{% if a.texto %}`→`{% if a.codigo %}`: **2/50**.

  Las tres cuadran con el informe. Con M02, M09 y M14 de la pasada 1, van **6 de 17 reproducidas**.
- **Cambio 2: hecho.** `current.md` trae `Set-DeployTag; .\deploy.ps1 -Only sv9,sv4`, desde `infra/`.
- El árbol de trabajo queda limpio y en `progress/` no escribí nada salvo este informe.

## Pasada 1 (resumen)
- init.sh exit 0, con los mismos números.
- Recálculo puro (`alcance_de_feature` + `generar_mutantes`): **2 ficheros, 31 líneas, 1 mutante**
  (`alta_sigrid_models.py:373`, `logico`, `or ""` → `and ""`). Coincide con el informe.
- Control sobre los ficheros enteros: 13 y 47 mutantes. El 1 es legítimo: 30 de las líneas son datos.
- **La campaña no se reejecutó**: 566,1 s según el informe (> 60 s). Me quedé en el recálculo más RM1–RM6.
- Reproducidas M02 (10/135), M09 (4/50) y M14 (2/50), sobre copia.

## Checkpoints
- C1 [x] init.sh exit 0 · [x] ficheros del arnés. C2 [x] solo F-104 `in_progress` · [x] rama
  `feature/F-104-codigos-contrato-v83` · [x] current.md describe la sesión activa · [x] sin `done` nuevas.
- C3 [x] hexagonal (datos y `avisos_sigrid` puros en *domain*, la plantilla en *interface*) · [x] primera
  línea con la ruta · [x] sin prints, TODOs, secretos ni dependencias nuevas (el test de R4 lee `infra/*.ps1`
  y solo imprime el nombre del fichero) · [x] trampas: no toca merge/raw, schema ni importes.
- C3 bis N/A (no toca `docs/referencia/`). C4 ter N/A (init.sh: ninguna ruta sensible declarada).
- C4 [x] trazabilidad completa y en verde · [x] sin red ni BBDD · [x] MANUAL: M1/M2/M3 con su comando en
  design §6; M-D en current.md y tasks.md.
- C4 bis [x] rigor declarado · [x] RED con trazas reales de T1–T4 y mutación inversa en las guardas ·
  [x] cobertura `[OK]` al 100 % · [x] totales verificados · [x] más de 60 s: recálculo puro, dicho arriba ·
  [x] coste por mutante 566,1 × 1 ÷ 1 = 566 s · [x] sin «CAMPAÑA NO VÁLIDA», sin veredicto = 0 ·
  [x] RM1: medido en `d3c20f1`, y desde entonces solo cambian `progress/` y `tasks.md` ·
  [x] RM2: media 566,1 = total, base sv4 282,4; cuadra con base + una pasada casi entera de sv4 (`test_f104_*`
  va al final por orden alfabético) · [x] RM3: ninguno de los 17 manuales es equivalente · RM5 N/A (no hay
  equivalentes) · RM6 N/A (no se quitó ninguna guarda; M12 protege `isinstance`) · [x] campaña MANUAL
  reproducible (pasada 2; 6 de 17 filas reproducidas) · [x] 0 supervivientes · [x] «Evidencias» con los workers (1).
- C5 [x] T1–T7 `[x]` con 7 commits `F-104 Tn:`; T8/T9 y las MANUAL abiertas por D1 · [x] árbol limpio ·
  [x] `features.json` coherente.

## Puntos que pidió el líder
1. **Mutación.** 1 mutante automático sobre 31 líneas es correcto: el mutador no toca literales de diccionario
   ni plantillas, y la prueba de control lo confirma. Para `critico` no basta solo, así que la campaña manual
   es la evidencia: 17 mutantes que cubren cada código, texto, campo de `avisos_sigrid`, filtro y rama de la
   plantilla. Desde la pasada 2 se puede reproducir desde el informe.
2. **Panel (D2).** `<li title="codigo">texto · mensaje (línea N)</li>`. El `mensaje` de sigrid-api (porcentaje,
   base y cuota) va entero y escapado (`test_f104_r8_el_mensaje_se_escapa`). Sin texto, igual que antes.
   Los otros 9 avisos de §3.2 (`871cc0c`) no tienen texto en `TEXTOS_MOTIVO_ALTA`: se pintan igual que antes.
3. **Avisos y H25.** El defecto sigue en `producto_sin_historico` (`settings.py:65`); ningún `.ps1` ni
   `.env.example` los nombra (test de R4 y diff). `clasificar` mantiene `CODIGOS_CABECERA.get(…, _ERROR)`
   (`clasificador.py:108`); R3 lo prueba con un código desconocido, con uno a un carácter de distancia y con
   los dos avisos llegados como error.
4. **`d3c20f1`.** Correcto. Añade solo `"branch"` a la ficha de F-104, con el mismo formato que F-073/F-083/
   F-085, y regenera `BACKLOG.md`. Lo usan `alcance.rama_de_feature`, `rigor`, `tamano` y `rutas_sensibles`.
   Sin él, la mutación medía el merge de `chore/F-104-alta`.
5. **`azure-apps` `8f6f243`.** La viñeta está al final de §10 (F-053; §11 empieza justo después). Trae los cinco
   códigos, el retirado hasta la verificación, el orden de despliegue y el enlace a la spec. Sin secretos,
   commit local y sin push. Cumple R12; `sv9.md` también (cabecera v8.3 `871cc0c` y sección nueva).

## Cobertura requisito → test
| R | Tests |
|---|---|
| R1 | `test_f104_r1_*` (tabla, `clasificar` en previa y grabación, motivo y detalle, servicio en simulación y real) |
| R2, R3 | `test_f104_r2_*`; `test_f104_r3_*` (tabla v8.2 + 3, desconocido a `error`, no son de línea); `test_f053_r18_*` |
| R4 | `test_f104_r4_defecto_*`, `test_f104_r4_ni_infra_ni_env_example_*` |
| R5 | `test_f104_r5_avisos_v83_se_guardan_sin_motivo[simulado/revisar/registrado]` + contraste |
| R6 | `test_f104_r6_*` (por `desde_cuerpo`; `filas` no se guarda; `tot` sí, R16) |
| R7 | `test_f104_r7_*`; `test_f077_r27_*` |
| R8 | `test_f104_r8_*` (vista, ignora lo que no es dict, panel, sin texto, escape) |
| R9 | `test_f104_r9_*` (derivados de la vista; panel solo bajo «Avisos de Sigrid») |
| R10 | sv4: `test_f104_r10_*`. sv9: T8, fuera de esta pasada (D1) |
| R11 | revisado en el diff: no toca comparador, cliente, `ruesma_comun`, DDL, `infra` ni `.env.example` |
| R12 / R13–R14 | revisado `sv9.md` y `azure-apps` `8f6f243` / MANUAL tras el despliegue, fuera de esta pasada |

## Cambios requeridos
Ninguno. Los dos de la pasada 1 están resueltos: la tabla manual reproducible (`1a66c6b`) y el comando completo
en `current.md`. Siguiente paso, según D1: F-104 pasa a `blocked` hasta el despliegue de la F-015 de
sigrid-api; después vienen M1, M-D, M2/M3 y T8–T9.

## Automejora (propuesta, no aplicada)
El último punto de mutación de C4 bis dice «si la campaña automática dio **0** mutantes y se sustituyó por una
MANUAL». Propongo que diga «o si la manual **complementa** a una automática que no cubre el alcance». Aquí
salió 1 mutante sobre 31 líneas y la regla no se activaba al pie de la letra, aunque la manual era el 94 % de
la evidencia. Va en `CHECKPOINTS.md` y `reviewer.md`, y es genérico: también en `arnes-base`.
