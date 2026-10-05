<!-- progress/impl_F-051_pasada2.md -->
# F-051 · Almacén por línea · Pasada 2 (cambios de la review)

Fecha: 2026-10-05. Worktree `albaranes-F-051`, rama `feature/F-051-almacen-por-linea`.
Encargo: `progress/review_F-051.md` (CHANGES_REQUESTED, pasada 1), H1–H6 + O2, y la
**decisión del humano** que llegó durante la pasada: fuera de almacén el input de partida
pinta la partida FINAL. Rigor `critico`. El informe de la pasada 1 sigue en
`progress/impl_F-051.md` (allí van H5 y H6, en su §2).

## 1. Qué cambió (un commit por punto)

| Punto | Commit | Qué |
|---|---|---|
| H1 | `30ee98a` | `evals/procesos/sv6_build.py`: `ALMACEN_SIN_PARTIDA = True` y `FAMILIAS_DESTINADAS` (los defaults de `Settings`), pasados a `PartidaMatcher` y `ValuationBuilder`. Test nuevo `tests/test_f051_puntos_de_composicion.py` (automejora del reviewer) |
| Decisión | `0e87486` | sv4: el mapa de conciliación pinta `codigo_partida_final` fuera de almacén; la de la casada pasa a `ConciliacionDisplay.codigo_partida_casada` |
| H2 | `1f2ba66` | `static/app.js`: la partida solo viaja si cambió respecto a `defaultValue` (vaciada ⇒ `""`, sin tocar ⇒ `null`). Los dos guardados comparten `_conciliaBody` (antes, dos copias) |
| H3 | `d10bf77` | El test de R12 en JS se ejecuta con node; otro exige que los dos guardados usen `_conciliaBody` |
| O2 | `5a608a3` | `data-partida-casada` en el input de las filas Sigrid; regla del aviso en `cambiaIdentidad` |
| Docs | `7bc7144` | `docs/ARCHITECTURE.md` regla 16: partida final pintada, guardado condicionado, O2 |
| H5 | `53a17ae` | Test guarda de la excepción de R20 fuera de almacén (dictamen en `impl_F-051.md` §2.7) |
| H4 | `02b647a` (azure-apps) | `albaranes.md`: vocabulario real de `partida_action` y «`codigo_partida_final` vacío = almacén» |
| H6 | (papeleo) | `impl_F-051.md` §2.6: `cmd /c rmdir`, nunca `Remove-Item` |

**H1, más allá de lo pedido.** El test recorre los puntos de composición de verdad: los
descubre con `ast` por todo el repositorio (fuera de `tests/` y venvs) y exige que sean
exactamente worker, API y banco; que cada uno pase **todos** los parámetros del constructor
de `ValuationBuilder` y `PartidaMatcher` (vale para la próxima feature que añada uno), con el
valor que le toca; que las cinco constantes replicadas del banco igualen los defaults de
`Settings` (leídos con `ast`), y que el build real del banco (subproceso, sin red/BBDD/LLM)
mande a almacén una línea sin partida con el motivo de familia destinada.

**Decisión del humano, detalle.** Si la final coincide con la de la casada, nada cambia
(también la descripción). Si difiere, se pinta la final y **no** la descripción de la casada
(es de otra partida). Los avisos ✓/⚠ de partida (`agree_partida`) **siguen comparando con la
del contrato** (la casada), como antes (helper `_partida_del_contrato`); en almacén, sin aviso.
El `value` inicial del input, que usa H2, es por tanto la partida final (test que encadena
mapa real → plantilla).

## 2. Fase RED (trazas reales)

```
H1 · python -m pytest tests/test_f051_puntos_de_composicion.py -q --tb=line   (raíz, antes del arreglo)
6 failed, 10 passed
evals/procesos/sv6_build.py: ValuationBuilder(...) no pasa ['familias_destinadas']
evals/procesos/sv6_build.py: PartidaMatcher(almacen_sin_partida=...) vale None   (assert None == 'ALMACEN_SIN_PARTIDA')
evals: ALMACEN_SIN_PARTIDA se ha separado de Settings.almacen_sin_partida_enabled   (assert None == True)
evals: FAMILIAS_DESTINADAS se ha separado de Settings.familias_destinadas
AssertionError: assert 'existing_matched' == 'almacen_sin_partida'   (build real del banco)
(+ PartidaMatcher no pasa ['almacen_sin_partida'])
```
(Los 10 verdes: descubrimiento de puntos y worker/API, que ya estaban bien.)
```
Decisión · cd services/albaranes-front && python -m pytest tests/test_f051_almacen_front.py -k p2 -q --tb=line
3 failed, 2 passed
test_f051_almacen_front.py:1125: AssertionError: assert '03.02' == '07.07'
AttributeError: 'ConciliacionDisplay' object has no attribute 'codigo_partida_casada'
assert 'value="07.07"' in '<input ... js-partida-combo ... value="03.02" placeholder="—" ... title="Cimentación">'
H2 · python -m pytest tests/test_f051_almacen_front.py -k h2 -q --tb=short   (node sobre el _conciliaBody de entonces)
E   AssertionError: assert '03.02' is None        (fila sin tocar: mandaba la partida)
H3 · los dos tests nuevos contra el app.js anterior a H2 (git show 0e87486:.../app.js)
2 failed: assert '_conciliaBody(tr)' in 'saveBtn.addEventListener("click", ...'  y  partidaParaEnviar no existía
O2 · python -m pytest tests/test_f051_almacen_front.py -k o2 -q --tb=line
3 failed, 1 passed
assert 'data-partida-casada="03.02"' in '<input ... js-partida-combo partida-almacen" ...>'
ValueError: substring not found              (cambiaIdentidad no existía)
assert None                                  (el confirm no usaba la regla)
```
(Verdes de la decisión: «si la final es la de la casada, nada cambia» y «los ✓/⚠ siguen
comparando con el contrato», guardas de regresión. Verde de O2: la fila Nueva sin atributo.)

## 3. Controles negativos (H3 y H5; todo restaurado, árbol limpio)

Sobre el código final, `-k "r12_guardar_la_fila or r12_los_dos"`:

| Control aplicado a `app.js` | Resultado |
|---|---|
| A · «Guardar» de la fila con su copia propia `v \|\| null` | 1 failed: `assert '_conciliaBody(tr)' in 'saveBtn.addEventListener...'` |
| B · «Guardar todas» con su copia propia `v \|\| null` | 1 failed: `assert '_conciliaBody(tr)' in 'saveAllLinesBtn.addEventListener...'` |
| C · `v \|\| null` dentro de `_conciliaBody` (el control del reviewer) | 1 failed: `assert {'codigo_partida': None} == {'codigo_partida': ''}` |
| D · enviar siempre (sin comparar con `defaultValue`) | 1 failed: `assert {'codigo_partida': '03.02'} == {'codigo_partida': None}` |

H5: con `and _txt(new_codigo_partida) == _txt(partida_casada)` → `and False` en
`update_line_conciliacion`, **2 failed** (`assert None == 501`): el de R20 en almacén y el
nuevo fuera de almacén.

## 4. Verificación

Suites una tras otra (nunca dos a la vez), intérprete de `init.sh` y `PYTHONPATH` a la comun del
worktree. Durante la pasada: sv4 completa **457 passed** (27,5 s) antes de la campaña; raíz, los
ficheros de evals que lanzan el subproceso de sv6 (F-011 R9/R10/R13/R14/R17, F-043, F-045, F-048):
**150 passed** tras ajustar los fixtures de F-011.

`bash harness/init.sh` (tal cual, en el worktree, al final, tras la campaña): **EXIT=0, «ENTORNO
LISTO»**, ningún `[KO]`. Raíz **1083 passed** (195,6 s); sv4 **458 passed** (35,7 s, relanzada);
sv1, sv2, sv3, sv5, sv6 y comun `[OK]` desde la caché de `init.sh` (sus árboles no cambian en esta
pasada: H1 toca `evals/`, que corre en la raíz). `PUERTA COBERTURA: 98.5% de 130 líneas cambiadas
cubiertas (128/130, umbral 80%, nivel critico)`. `PUERTA TAMAÑO` dentro (impl 218/220). Avisos, los
de la pasada 1: `RUTAS SENSIBLES [evals]` (falta `progress/evals_F-051.md`: T21, del humano), ruff
1181 (deuda previa), infra sin tests, `[ADAPTAR]` de F-034/F-035 (ajenos).

**Mutación** (H1 entra en una ruta mutada): campaña completa re-ejecutada sobre `53a17ae`,
`python -m harness.mutacion --feature F-051` → `progress/mutacion_F-051.md`. Alcance 503 líneas
en 14 ficheros (entra `evals/procesos/sv6_build.py`), **61 mutantes, 61 muertos, 0
supervivientes, 0 timeouts, 0 sin veredicto**, 909,4 s, 4 workers. Una primera tanda se paró a
propósito (para añadir el test de H5 antes de medir): su centinela se retiró con
`--restaurar` y sus worktrees temporales se borraron. Lo que va después de `53a17ae` es solo
`progress/`.

## 5. Evals deterministas (sin LLM, solo informativo)

`python -m evals.runner --informes <scratchpad>` (modo determinista: ninguna llamada LLM ni
de red), antes y después de H1. Ya era **ROJO** antes (deuda previa del ground truth). H1
añade **24 discrepancias, todas en RES-001…RES-006** y de un solo tipo: la línea de residuos
sin partida en el albarán sale con partida `None` (almacén) donde el ground truth espera la
del contrato `CI.03A.7` (IA3 `codigo_partida_final`, FINAL `partida_final`, y la sintética de
gestión de residuos que la hereda). Es exactamente R1 de F-051: el ground truth de esos seis
casos describe la regla anterior. **No he tocado el ground truth**: decide el humano en T21
(actualizar esos libros o aceptar la diferencia).

Efecto colateral en la suite de la raíz: `test_f011_r13_determinista.py` y
`test_f011_r14_e2e_real.py` (F-011) tenían una línea **sin partida** que esperaba la del
contrato; con H1 cayeron 3 tests. Su objeto no es la partida (redes de sv6 y forma del
envelope), así que el fixture pasa a llevar `codigo_imputacion` igual a la del contrato
(comentado en el propio test). **Cambio en tests de otra feature**, en el commit de H1.

## 6. Decisiones

1. Los ✓/⚠ de partida comparan con la del contrato (no con la final pintada): es lo que
   documenta el modelo y no se pidió cambiarlo. Consecuencia visible: una fila cuya final
   difiere de la casada (herencia R7) puede enseñar ⚠ junto a una partida que coincide con
   el albarán. Ver §7.
2. `data-partida-casada` solo en filas Sigrid (`kind == 'assigned'`): la excepción de R20 en
   el backend exige `matched_contrato_line_id`.
3. Los tests de JS se ejecutan con **node** (`shutil.which("node")`; si falta, `skip` con
   motivo). Ninguna dependencia nueva en manifiestos. Los tests estructurales que vigilan que
   los dos guardados usen la misma función no necesitan node.
4. La opción «➕ Nueva — derivar a …» del selector usa `c.codigo_partida` y ahora enseña la
   final. Solo es texto; no lo he cambiado.

## 7. Para el humano

- **⚠ de partida** (decisión 1): ¿comparar con la final pintada en vez de con la casada? Es
  un cambio de una línea en `_partida_del_contrato`.
- **Ground truth RES-001…006** (§5) antes de la pasada T21.
- O1 se queda como está (elegir línea de contrato en una línea en almacén la mantiene en almacén).
- T21–T24 siguen pendientes (`impl_F-051.md` §6). En T24 mirar además: guardar sin tocar no
  mueve la partida; poner la de la casada no avisa «pasará a NUEVA».

## Evidencias

| Evidencia | Valor medido |
|---|---|
| Tests nuevos o reescritos en la pasada | raíz 16 (1067 → 1083) (`test_f051_puntos_de_composicion.py`); sv4 13 (5 decisión, 1 H2, 2 H3 —uno sustituye al test débil—, 4 O2, 1 H5): 446 → 458 (13 nuevos, 1 borrado) |
| Tests ejecutados (`init.sh`) | raíz 1083 · sv4 458 · sv1/sv2/sv3/sv5/sv6/comun en verde (caché) — 0 fallos |
| Cobertura de líneas cambiadas | **98,5 %** (128/130, umbral 80 %) — `PUERTA COBERTURA` |
| Mutantes | 61 generados, 61 muertos, **0 supervivientes** (completa, `53a17ae`, 909,4 s) |
| Tiempo de las suites | raíz 195,6 s · sv4 35,7 s (en `init.sh`) |
| Evals deterministas (informativo) | +24 discrepancias, todas en RES-001…006 (§5); LLM: T21, del humano |
