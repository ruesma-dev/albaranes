<!-- progress/review_F-115.md -->
Revisión completa (pasada 1) · `dev...9c5ad7d` (base de rama `ba3542b`)

# F-115 · review

**Veredicto: APPROVED**

Fuera de esta revisión por encargo del líder: T13 (Chrome, líder) y T16 (despliegue sv3 → sv4, humano). Que sigan
`[ ]` en `tasks.md` es lo esperado y no bloquea esta review; sí bloquean el `done`.

## Nivel de rigor

`estandar`, declarado en `harness/features.json`. Exige fase RED con salida real, puerta de cobertura, campaña de
mutación sin supervivientes `PENDIENTE` y sección «Evidencias». RM5 no aplica (solo en `critico`).

## Verificación ejecutada por el reviewer

- `bash harness/init.sh` en el worktree con `PYTHONPATH=<worktree>\services\albaranes-comun` y `ARNES_SIN_CACHE=1`
  (sin eso sale rojo porque sv3/sv4 importan la comun 0.10.0 del árbol principal; es del entorno, no del código):
  **EXIT 0**. Raíz 1919 passed; sv1 236; sv2 496; sv3 1608; sv4 2248; sv5 125; sv6 506 (+1 skipped); sv9 1073;
  comun 1342. `PUERTA COBERTURA [OK] 98,5 %` (134/136); `PUERTA TAMAÑO [OK]`; rutas sensibles N/A (motivo impreso).
- `git status` limpio tras la ejecución.
- Mutación, recálculo independiente (`harness.alcance` + `generar_mutantes`, cálculo puro): 13 ficheros,
  **445 líneas, 54 mutantes**, que coinciden con el informe. Muestra de 20 con la semilla `20260820`: sale el
  superviviente declarado (`busqueda_contratos.py:120`, `comparacion`, `vista is not None` → `vista is None`),
  mismo texto original→mutado.
- **Campaña no reejecutada: 1440,3 s (24 min) según el informe**, por encima del umbral de 60 s; me quedo en el
  recálculo puro y RM1–RM6.

## Checkpoints

**C1** — [x] init.sh exit 0 (con el PYTHONPATH del worktree, motivo arriba) · [x] ficheros del arnés presentes.
**C2** — [x] una sola `in_progress` (F-115) · [x] rama `feature/F-115-cambio-proveedor-reinicia-contrato` ·
[x] `current.md` con la sesión activa · [x] N/A history: la feature aún no es `done`.
**C3** — [x] hexagonal: la excepción nueva vive en `domain/models` sin infraestructura; SQL solo en
`infrastructure/database`; el puerto de sv3 en `domain/ports`; comun es función pura · [x] primera línea con ruta en
los 8 ficheros de código nuevos · [x] sin `print` de depuración (los `console.log` están en el arnés node de los tests),
sin secretos · [x] ARCHITECTURE: regla 26 nueva y regla 25 con R7; límite de servicio respetado (la lógica compartida
en comun y no copiada).
**C3 bis** — N/A: no entra ningún documento de fuera.
**C4** — [x] cada requisito tiene su test (tabla de abajo) · [x] unit tests sin red; BBDD solo en SQLite en memoria y
dobles, como en las features anteriores · [x] verificaciones MANUAL listadas (T0 hecha, T13 y T16 abiertas).
**C4 bis** — [x] `rigor` declarado · [x] RED con salida real para T1, T3, T5, T7, T9 y T11 · [x] cobertura [OK] ·
[x] `progress/mutacion_F-115.md` de la herramienta, sin `PENDIENTE` · [x] muertos: campaña > 60 s, recálculo hecho
· [x] tiempo coherente: 20 × 72,0 s = 1440 s; media 72 s frente a línea base de sv4 170 s y de sv3 15,9 s, con 19/20
muertos y `-x` (caso legítimo de RM2) · [x] sin cabecera «⚠ CAMPAÑA NO VÁLIDA»; «Sin veredicto (base rota)» = 0 ·
[x] **RM1**: SHA medido `ce87998`; desde ahí solo cambia `tests/test_f115_t14_supervivientes.py` (un test, fuera
del alcance de producción) y docs, así que la campaña vale · [x] **RM2** ok · [x] **RM5** N/A (rigor `estandar`) ·
[x] **RM6** N/A: el superviviente se mató con un test nuevo, sin quitar ninguna guarda · [x] N/A campaña manual: no la
hubo · [x] el superviviente lleva su análisis (hueco real, test nuevo, reproducido a mano por el implementer) ·
[x] «Evidencias» con los cuatro números · [x] ningún N/A sin justificar.
**RM3** — en la muestra no hay ningún mutante equivalente que salga muerto: los 19 cambian el comportamiento
observable (p. ej. `strip() and None` deja siempre `None`; `fila[1]` da IndexError; `lector is not None` anula la
retirada).
**C4 ter** — N/A: la puerta de rutas sensibles dice que F-115 no toca ninguna.
**C5** — [x] T0–T12, T14, T15 y T17 marcadas `[x]`, cada una con su commit `F-115 Tn: …`; T13 y T16 abiertas, fuera por
encargo · [x] sin temporales en el árbol del worktree · [x] `features.json` = `in_progress`, que es el estado real.

## Cobertura requisito → test

| R | Test(s) |
|---|---|
| R1 | `comun/tests/test_f115_pertenencia.py` (9 `test_f115_r1_*`, formatos, legado, albarán vacío, reexport) |
| R2–R6 | `sv3/tests/test_f115_seleccion_ajena.py` (`r2_*` ×14, `r3`, `r4_*` sin_datos y error, `r5_*` ×3, `r6_*`; casos a–f de R22) |
| R7 | `sv3/tests/test_f115_disparo_force.py` (5); `test_f075_disparo.py` sigue verde con `force=False` |
| R8 | `test_f115_r8_reenrich_no_toca_lineas_ni_blobs_ni_extraccion` |
| R9–R11, R18, R19 | `sv4/tests/test_f115_guardar_retira_contrato.py` (casos g e i) + `test_f115_t14_supervivientes.py` (R11 «Obra cambiada») |
| R12, R13 | `sv4/tests/test_f115_detalle_y_aprobar.py` (caso h; 409 en API y aviso en el listado) |
| R14, R15 | `sv4/tests/test_f115_js_confirmacion.py` (12, `avisoCambioCabecera` y cancelar restaura) |
| R16 | R8 (las líneas no se tocan) + la suite de F-106 fase B en verde (F-115 no añade conservación propia, como dice la spec) |
| R17 | caso a de R2/R6 (selección NULL) + R7 (publica sin contrato); sv9 sin cambios |
| R20 | suites completas en verde; retoques de tests anteriores justificados en impl §8 (ninguna aserción relajada: versión «≥», fixtures coherentes con R13 y `CABECERA` como manda la ficha) |
| R21 | `docs/ARCHITECTURE.md` reglas 25 y 26; `azure-apps` `7c6081b` (+10 líneas en `albaranes.md`, local) |

## Contraste con el diseño

- Ficheros: los de `design.md` §4–§5, más `busqueda_contratos.py` (R19 exigía normalizar el CIF del rastro;
  desviación 3, justificada) y `review_models.py`/`review_service.py` (`contrato_retirado`, desviación 1). Sin DDL ni
  cambios de mensajes de cola; sv5, sv6, sv9 y sv2 sin tocar. He comprobado que sv6 ya trata `no_contract` (sustituye la
  valoración), así que R7 no necesita tocarlo.
- comun **0.11.0** en `pyproject.toml`, `__init__.py`, README (tabla y entrada de versión con el orden de reconstrucción
  sv3 → sv4) y el test exacto `test_f115_t2_version_0110`.

## Observaciones (no bloquean)

- **O1.** `cambio_de_cabecera` dice «proveedor» cuando no hay rastro con CIF aunque solo haya cambiado la obra
  (`busqueda_contratos.py:120`). Está documentado en el docstring; el efecto es solo el texto del aviso.
- **O2.** `_normObra` de `app.js` no replica `canonizar_codigo_obra` del todo (solo añade el 0 a 3 dígitos). En el peor
  caso pide una confirmación de más; no tiene efecto en los datos.
- **O3.** Por D2, un albarán con contrato y sin CIF u obra pierde la selección en el siguiente PUT o enriquecimiento.
  La T0 no midió ese caso. Es lo que se aprobó; se apunta por si aparece en la T13.
- **O4.** `azure-apps` `7c6081b` está solo en local: publicarlo junto con la T16.

## Cambios requeridos

Ninguno.

## Automejora (propuesta, no aplicada)

- `CHECKPOINTS.md` C1: anotar que, en un worktree cuya feature sube la versión de comun, `init.sh` se ejecuta con
  `PYTHONPATH` a la comun del worktree. Ya ha pasado en F-113, F-114 y F-115, y sin la nota cada reviewer lo vuelve a
  descubrir. Vale para cualquier monorepo con librería compartida instalada en editable, así que iría también a
  `arnes-base`.
