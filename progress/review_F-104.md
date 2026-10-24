<!-- progress/review_F-104.md -->
Revisión completa (pasada 1), `dev...afe5b6d`, alcance T1–T7 (M1, M-D, M2, T8 y T9 fuera a propósito, D1).

# F-104 · Review (pasada 1)

**Veredicto: CHANGES_REQUESTED (REJECTED).** El código, los tests y la documentación están bien y los
reproduje. Lo que falla es la evidencia: la campaña manual (17 de los 18 mutantes) no se puede reproducir con
lo que dice el informe (C4 bis, último punto de mutación). Se arregla en el papel, sin tocar código.

**Nivel de rigor:** `critico`, declarado en `features.json`. Exige fase RED, cobertura, mutación con 0
supervivientes y las MANUAL listadas con su comando exacto.

## Verificación ejecutada por el reviewer
- `bash harness/init.sh` en el worktree: **exit 0**. Raíz 1883 passed; sv9 1017; sv4 1833; sv1 205, sv2 485,
  sv3 1576, sv5 96, sv6 473 (+1 skipped); comun en verde por caché. `PUERTA COBERTURA: 100.0% de 4 líneas
  cambiadas (4/4)`, tamaño `[OK]`, rutas sensibles N/A (no toca ninguna).
- Recálculo puro (`alcance_de_feature` + `generar_mutantes`): **2 ficheros y 31 líneas** (clasificador 7,
  alta_sigrid_models 24), **1 mutante**: `alta_sigrid_models.py:373`, operador `logico`,
  `a.get("codigo") or ""` → `a.get("codigo") and ""`. Coincide con el informe. Prueba de control sobre los
  ficheros enteros: 13 y 47 mutantes, así que el generador funciona y el 1 es legítimo (30 líneas son datos).
- **La campaña no se reejecutó**: 566,1 s según el informe (> 60 s). Me quedo en el recálculo más RM1–RM6.
- Tres filas de la campaña manual reproducidas al pie de la letra, sobre una **copia** en mi scratchpad (RM4),
  sin `-x`, con la base en verde antes de cada una: M02 `clasificador.py:48` `_NO_ADMITIDO`→`_REVISAR`:
  **10 failed**/135. M09 `alta_sigrid_models.py:374` `a.get("mensaje")`→`a.get("detalle")`: **4 failed**/50.
  M14 `_alta_sigrid.html:128` sin `{% if a.mensaje %} · …{% endif %}`: **2 failed**/50. Las tres muertas.
  El texto exacto lo saqué de `mutantes_manuales.py` del scratchpad de la sesión, **no del informe**.

## Checkpoints
- C1 [x] init.sh exit 0 · [x] ficheros del arnés.
- C2 [x] solo F-104 `in_progress` · [x] rama `feature/F-104-codigos-contrato-v83` · [x] current.md describe la
  sesión activa (F-104 arriba, F-069 `blocked` vigente) · [x] sin `done` nuevas.
- C3 [x] hexagonal: los datos en *domain* (sv9 y sv4); `avisos_sigrid` es puro; la plantilla en *interface* ·
  [x] primera línea con la ruta en los 2 tests nuevos · [x] sin prints, TODOs, secretos ni dependencias nuevas
  (el test de R4 lee `infra/*.ps1` y solo imprime el nombre del fichero) · [x] trampas: no toca merge/raw,
  schema ni importes.
- C3 bis N/A: no toca `docs/referencia/`.
- C4 [x] trazabilidad completa (tabla abajo), todo verde · [x] sin red ni BBDD (fakes de F-053, `Settings`
  con monkeypatch) · [x] MANUAL: M1/M2/M3 en design §6 con su comando; M-D en current.md y tasks.md.
- C4 bis
  - [x] rigor declarado.
  - [x] fase RED con trazas reales de T1–T4; las guardas (R2, R3, R4–R6, R10) con mutación inversa anotada.
  - [x] cobertura `[OK]` al 100 %.
  - [x] informe de la herramienta con totales verificados.
  - [x] más de 60 s: recálculo puro, dicho arriba.
  - [x] coste por mutante = 566,1 × 1 ÷ 1 = 566 s (> 1 s).
  - [x] sin «CAMPAÑA NO VÁLIDA»; sin veredicto = 0.
  - [x] RM1: medido sobre `d3c20f1`, y desde entonces solo cambian `progress/` y `tasks.md`; el alcance es el
    mismo.
  - [x] RM2: media 566,1 = total; base sv4 282,4. Cuadra con base + una pasada casi entera de sv4 (el test que
    caza el mutante, `test_f104_*`, va al final por orden alfabético). No hay salto de orden de magnitud.
  - [x] RM3: ningún muerto es equivalente (revisados los 17 del script uno a uno).
  - RM5 N/A: no hay equivalentes declarados.
  - RM6 N/A: no se quitó ninguna guarda; el filtro `isinstance` se queda y M12 lo protege.
  - **[ ] campaña MANUAL reproducible**: ver el cambio 1.
  - [x] 0 supervivientes · [x] «Evidencias» con los números y los workers (1).
- C4 ter N/A: init.sh dice que no toca ninguna ruta sensible declarada.
- C5 [x] T1–T7 `[x]` con commit `F-104 Tn:` (7); T8/T9 y las MANUAL abiertas, como corresponde a D1 ·
  [x] árbol limpio · [x] `features.json` coherente (`in_progress`; pasará a `blocked` tras la aprobación).

## Puntos que pidió el líder
1. **Mutación.** 1 mutante automático sobre 31 líneas es correcto: el mutador no toca literales de diccionario
   ni plantillas, y la prueba de control lo confirma. Para `critico` no basta solo, así que la campaña manual
   es la evidencia que sostiene la feature. Lo que contiene es bueno: 17 mutantes que cubren cada código, cada
   texto, cada campo de `avisos_sigrid`, el filtro y las ramas de la plantilla. Pero tiene que poder repetirse
   desde el informe (cambio 1).
2. **Panel (D2).** `<li title="codigo">texto · mensaje (línea N)</li>`. El `mensaje` de sigrid-api (porcentaje,
   base y cuota) va entero y escapado (`test_f104_r8_el_mensaje_se_escapa`). Sin texto, igual que antes.
   Ninguno de los otros 9 avisos de §3.2 de `871cc0c` tiene texto en `TEXTOS_MOTIVO_ALTA`, así que su
   pintado no cambia.
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
| R2 | `test_f104_r2_el_retirado_sigue_en_no_admitido` |
| R3 | `test_f104_r3_*` (tabla v8.2 + 3, desconocido a `error`, no son de línea); `test_f053_r18_*` |
| R4 | `test_f104_r4_defecto_*`, `test_f104_r4_ni_infra_ni_env_example_*` |
| R5 | `test_f104_r5_avisos_v83_se_guardan_sin_motivo[simulado/revisar/registrado]` + contraste |
| R6 | `test_f104_r6_*` (por `desde_cuerpo`; `filas` no se guarda; `tot` sí, R16) |
| R7 | `test_f104_r7_*`; `test_f077_r27_*` |
| R8 | `test_f104_r8_*` (vista, ignora lo que no es dict, panel, sin texto, escape) |
| R9 | `test_f104_r9_*` (derivados de la vista; panel solo bajo «Avisos de Sigrid») |
| R10 | sv4: `test_f104_r10_*`. sv9: T8, fuera de esta pasada (D1) |
| R11 | revisado en el diff: no toca comparador, cliente, `ruesma_comun`, DDL, `infra` ni `.env.example` |
| R12 | revisado: `sv9.md` y `azure-apps` `8f6f243` |
| R13, R14 | MANUAL (M1, M2/M3), después del despliegue: fuera de esta pasada |

## Cambios requeridos
1. **`progress/mutacion_F-104.md`, tabla de la campaña manual**: **una fila por mutante (M01…M17)**, sin
   agrupar (hoy van juntas M01–M03, M06–M07, M09–M11 y M14–M16). En cada fila:
   - el fichero y la **línea**;
   - el **texto exacto original → mutado** (el par `viejo`/`nuevo` del script; si es multilínea, la primera
     línea y «…»);
   - el **número de fallos**, medido **sin `-x`**, sobre los mismos ficheros de test que el script.
     Referencia de mis tres: M02 10, M09 4, M14 2.

   Motivo: la única fuente que hoy lo permite es `mutantes_manuales.py`, que vive en un scratchpad efímero,
   fuera del repositorio. Cuando se borre, la campaña deja de poder repetirse y se queda en «un párrafo»
   (C4 bis). Puedes añadir la lista de pares del script como bloque de código; el script no hace falta
   versionarlo.
2. Recomendado, no bloquea: en la línea de despliegue de `progress/current.md`, poner el comando completo,
   `Set-DeployTag; .\deploy.ps1 -Only sv9,sv4`, como en tasks.md M-D.

Con el cambio 1 hecho, la pasada 2 es incremental desde `afe5b6d` y solo mira el informe de mutación.

## Automejora (propuesta, no aplicada)
El último punto de mutación de C4 bis dice «si la campaña automática dio **0** mutantes y se sustituyó por una
MANUAL». Propongo que diga «o si la manual **complementa** a una automática que no cubre el alcance». Aquí
salió 1 mutante sobre 31 líneas: la regla no se activaba al pie de la letra, aunque la manual era el 94 % de
la evidencia. El sitio del cambio es `CHECKPOINTS.md` y `.claude/agents/reviewer.md`, y es genérico: va
también a `arnes-base`.
