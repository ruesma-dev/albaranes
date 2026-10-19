<!-- progress/review_F-075.md -->
Revisión incremental desde 8eed0c7 (pasada 2) · `8eed0c7..e853d4f`; la pasada 1 fue completa (`bee817d..8eed0c7`)

# F-075 · review

**Veredicto: APPROVED, con el CIERRE CONDICIONADO a las condiciones de §3.**

- **Pasada 1** (completa, sobre `8eed0c7`): CHANGES_REQUESTED por tres huecos. R10 no funcionaba en pantalla («Valorar
  ahora» salía desactivado sin contrato), R11 no tenía test trazable y las MANUAL no estaban en `current.md`. Hubo
  además cuatro observaciones, O1–O4. Todo lo demás quedó verificado y aprobado: integración con F-078, F-076, F-077,
  F-053 y F-064; DDL; manifiestos; mutación recalculada y RM4.
- **Pasada 2**: resuelve los tres cambios, más O1, O2 y O4. Lo aprobado hasta `8eed0c7` se da por bueno. El delta no
  toca ninguna firma pública, no mueve ficheros y no cambia el alcance medido (§1).

**Rigor:** `critico`, declarado. Exige RED, cobertura ≥ 80 %, 0 supervivientes, RM1–RM6 y las MANUAL con su comando.
C4 ter aplica por las rutas sensibles.

## 1. Verificación ejecutada en esta pasada

- **`bash harness/init.sh`** con `PYTHONPATH=<worktree>/services/albaranes-comun` y `ARNES_SIN_CACHE=1`. Hacen falta
  los dos: el editable del venv es el del árbol principal, y la caché de suites anula la cobertura (§6). Resultado:
  **ENTORNO LISTO, exit 0**.
  - raíz 1328, sv1 205, sv2 485, sv3 1540, sv4 1774, sv5 46, sv6 473 (+1 skip), sv9 673, comun 859 (+3 skip):
    **0 fallos**;
  - **COBERTURA [OK] 98,1 %** (464/473);
  - TAMAÑO OK;
  - RUTAS SENSIBLES en aviso (falta T17).

  Coincide con «Pasada 2» de `impl_F-075.md`. Ha corrido una sola suite a la vez, y el árbol queda limpio en `e853d4f`.
- **Delta de producción**: `pie_guard_service.py:92,107-114,139` (O2, O4) y `app.js` (R10).
  - `generar_mutantes` sobre esas líneas devuelve **0 mutantes**. En la prueba de control (el mismo fichero, sin
    acotar el alcance) salen 5. El cero es legítimo: la llamada nueva no tiene operadores ni constantes mutables.
  - `app.js` no es Python.
  - **La campaña no cambia**: 175 generados, 171 muertos, 4 desaparecidos, 0 supervivientes. RM1–RM6 siguen como en
    la pasada 1.
- **R11, demostrado con una rotura**. En una copia hecha con `git archive` en el scratchpad, hice que
  `anotar_valorado_distinto` tocara `total_valorado`, y `test_f075_r11_r12_con_sinteticas_solo_se_anade_el_motivo` cae
  (1 failed). Es la fase RED de un test de caracterización (C4 bis).

## 2. El delta, punto por punto

1. **R10** (`bb7fea3`, `8d81c47`) [x].
   - `puedeValorar(codigo, traeImportes)` decide el estado inicial (`app.js:2715`) y el de «Sin contrato»
     (`app.js:2761-2762`). `avisoSinContrato` dice «se valora con los importes del albarán».
   - Ya no queda ningún `disabled = !current`.
   - `test_f075_r10_js_*`: dos de ellos ejecutan las funciones con `node`, y el tercero fija los dos bloques. Hay RED
     real («3 failed, 2 passed»).
   - DISCOIN y el backfill uno a uno (v2-P6) ya se pueden hacer desde la ficha.
2. **R11** (`f617037`) [x].
   - En sv6: mismas líneas, total y motivos que `ValuationBuilder` + `completar_registros`. Con sintéticas, R12 solo
     añade su motivo al final.
   - En sv3: con contrato y líneas publica su código, traiga o no importes, y sin leerlos.
3. **MANUAL en `current.md`** (`5b3024f`) [x].
   - T0 (SOLO LECTURA), T17 y T18 con su comando exacto para PowerShell.
   - [ESCRIBE EN PRODUCCIÓN · humano] en cada `deploy.ps1`, en «Valorar ahora» y en «Aprobar».
   - Cada paso con su VERDE.
   - T18 sigue el orden **sv5 → sv6 → sv3 → sv4 → sv2** (O1), con su motivo. Lo he comprobado: sv5 y sv6 no dependen
     de la DDL, y sv2 va detrás de sv3 por `StrictSchemaModel`.
   - Este orden se aparta de la spec §10: **tiene que aceptarlo el humano**.
4. **O2** (`04c52fc`) [x].
   - Ahora se retira el prefijo `pie_no_cuadra:` antes de marcar, y queda un solo motivo vivo. Hay test (orden
     `retirar → marcar`, los motivos ajenos intactos) y su RED.
   - Son dos transacciones: si fallara la segunda, el motivo se perdería hasta la siguiente pasada. Es aceptable porque
     es best-effort (R18) y `review_required` no baja.
5. **O4** (`6376564`) [x]: vuelve el comentario «best-effort (R18)».
6. **O3** (línea directa con importe y sin cantidad) queda **fuera**, a decisión del humano.
   - Cómo se nota: esa línea se aprueba y luego sv9 la deja `no_admitido`, visible en el panel de F-053.

## 3. Condiciones de cierre (no se marca `done` sin ellas)

1. **El humano acepta el orden de T18** (sv5 → sv6 → sv3 → sv4 → sv2) o vuelve al de la spec.
2. **T17** (humano, en el worktree y antes de fusionar): `progress/evals_F-075.md` con:
   - `MODO: completa` y `FASES: IA1,IA2,IA3,IA4,E2E`;
   - IA1 ≤ 154 e IA2 ≤ 4 fallos críticos;
   - el pie en «Campos no medidos»;
   - IA3, IA4 y E2E iguales a la pasada determinista.

   Debe ser posterior al último commit que toque `prompts.yaml` o `albaran_models.py`. Si sale peor, el bloque del pie
   se revisa antes de fusionar.
3. Fusionar en `dev` y pasar `init.sh` en verde **en el árbol principal**, ya sin `PYTHONPATH`. Quitar la *junction*
   `.venv` de sv4 antes de `git worktree remove`.
4. **T18** (humano), con su comprobación en pantalla. T0 es opcional.
5. El humano decide qué hacer con O3: feature nueva o aceptarla tal cual.

## 4. Checkpoints, tras la pasada 2

- **C1/C2** [x] `init.sh` exit 0 · [x] ficheros base · [x] una `in_progress` · [x] rama · [x] `current.md` · [x] `done`⇒`history` aún no aplica.
- **C3**
  - [x] Arquitectura hexagonal.
  - [x] Primera línea con la ruta.
  - [x] Sin `print`, sin TODO, sin secretos.
  - [x] **Ninguna dependencia nueva**: no cambia ningún `requirements.txt` ni ningún `infra/manifests/*`; `StrEnum`
    viene de Python 3.12 y `pydantic` de comun.
  - [x] Las tres trampas: todo sobre el merge; DDL idempotente en las dos tablas, con sus lectores; las sintéticas,
    resueltas en R12.
- **C3 bis** N/A: no se toca `docs/referencia/`.
- **C4** [x] R1–R27 y R5 bis tienen cada uno al menos un `test_f075_rN_*`, todos en verde (§5) · [x] sin red ni BBDD
  real · [x] MANUAL en `current.md`.
- **C4 bis**
  - [x] Rigor declarado. [x] Fase RED: las 15 trazas de la pasada 1, más R10 y O2, más la rotura de R11 (§1).
  - [x] Cobertura del 98,1 %.
  - [x] Mutación recalculada: 175 en `d33f009` y 171 en HEAD (solo faltan los 4 desaparecidos, no aparece ninguno
    nuevo). El delta añade 0, con 5 en el control.
  - [x] La campaña duró 5586,7 s, más de 60 s: **no la reejecuto**. Me quedo con el recálculo puro más RM4: en la
    pasada 1 reproduje #86, #152 y #47.
  - [x] Coste por mutante 127,7 s; sin «CAMPAÑA NO VÁLIDA»; «Sin veredicto» = 0.
  - [x] RM1: lo cambiado desde `d33f009` no crea ningún mutante sin juzgar.
  - [x] RM2: 31,9 s × 4 frente a líneas base de 16 a 331 s, con 153 de 175 muertos con `-x`.
  - [x] RM3: ningún muerto equivalente.
  - [x] RM5 N/A (ningún equivalente declarado); RM6: no se quitó ninguna guarda.
  - [x] Los 22 están analizados en `mutacion_F-075.md`.
  - [x] Evidencias completas, con los 4 workers.
  - [x] Ningún N/A sin motivo escrito.
- **C4 ter** (`aviso`) [ ] falta `evals_F-075.md` en modo completo. **Motivo: T17 la paga y la lanza el humano.** El
  comando y el criterio están revisados (§3.2). No bloquea el APPROVED; sí el cierre.
- **C5** [x] T1–T16 y T19 en `[x]`, cada una con su commit; T0, T17 y T18 son MANUAL del humano · [x] sin temporales
  versionados · [x] `features.json` coherente.

## 5. Cobertura requisito → test

| Requisitos | Tests |
|---|---|
| R1, R2, R6 (unitario) | comun `test_f075_importes.py` |
| R3, R4, R11 (sv3) | sv3 `test_f075_disparo.py` |
| R5 bis | sv5 `test_f075_no_contract.py` |
| R5–R9, R11, R12 | sv6 `test_f075_valoracion_directa.py` |
| R13, R14 | sv2 `test_f075_pie_ia1.py` |
| R15–R18 | sv3 `test_f075_pie.py` |
| R9, R10, R23, R24 | sv4 `test_f075_ficha.py` |
| R19–R22, R25 | sv4 `test_f075_bandeja.py`, `test_f075_vistas.py` |
| R26 | sv9 `test_f075_alta_directa.py` |
| R27 | raíz `tests/test_f075_evals.py` |

## 6. Automejora del arnés (pendiente del humano; genérica ⇒ `arnes-base`)

- **P1** la caché de suites no aporta cobertura (KO 31,7 % en una rama al 98,1 %): guardar su `coverage.json` o desactivarla con la puerta.
- **P2** en un worktree que cambia comun, `init.sh` tal cual da rojo: que el aviso diga qué `PYTHONPATH` exportar, o lo fije.
