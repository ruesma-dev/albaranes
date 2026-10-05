<!-- progress/review_F-051_pasada2.md -->
Revisión incremental desde 1cef691 (pasada 2): delta `1cef691..541bfe7` + commit `02b647a` de `azure-apps`.

# F-051 · Almacén por línea · Review, pasada 2

**Veredicto: APPROVED** (2026-10-05). **Rigor `critico`** (declarado en `features.json`): fase RED, cobertura
≥ 80 %, mutación completa con 0 supervivientes sin justificar. Las cuatro puertas se cumplen y los seis hallazgos
de la pasada 1 están cerrados con código, test y control negativo que yo mismo he vuelto a aplicar.

Lo aprobado en la pasada 1, salvo H1–H6, se da por bueno: no lo he vuelto a leer. El delta no cambia firmas
públicas ni mueve ficheros. Sí amplía el alcance de mutación (entra `evals/procesos/sv6_build.py`), y por eso
he vuelto a verificar la campaña entera (ver C4 bis).

**Condición de cierre (para el líder):** T21–T24 siguen siendo del humano. `init.sh` avisa de
`RUTAS SENSIBLES [evals]` porque falta `progress/evals_F-051.md`. Este APPROVED cubre el trabajo del
implementer. No autoriza el `done` mientras T21–T24 no estén hechas o el humano no las dispense por escrito.

## Entorno (resultado real)

`bash harness/init.sh` en el worktree, tal cual, sobre `541bfe7`: **EXIT=0, «ENTORNO LISTO. Puedes trabajar.»**,
ningún `[KO]`.
- Raíz: `1083 passed in 163.65s`. Las siete suites de servicio salieron `[OK]` desde la caché. sv4 es el único
  servicio que cambia en el delta, así que la relancé yo sola (intérprete de su venv, `PYTHONPATH` a la comun
  del worktree): **458 passed, 0 skipped** en 13,3 s. Los tests con node se ejecutaron, no se saltaron
  (node v24.14.1).
- `PUERTA COBERTURA: 98.5% de 130 líneas cambiadas cubiertas (128/130, umbral 80%, nivel critico)`.
- `PUERTA TAMAÑO` dentro.
- Avisos: `RUTAS SENSIBLES [evals]` (T21), ruff 1181 (deuda previa), infra sin tests y `[ADAPTAR]` de
  F-034/F-035 (ajenos). Son los mismos de la pasada 1.

## Hallazgos de la pasada 1

- **H1 · cerrado.** `sv6_build.py:62-63,589-595` pasa `almacen_sin_partida` y
  `familias_destinadas_de_csv(FAMILIAS_DESTINADAS)`. `tests/test_f051_puntos_de_composicion.py` va más allá de
  lo pedido:
  - descubre con `ast` todos los puntos de composición;
  - exige que cada punto pase todos los parámetros de los dos constructores y con el valor que le toca;
  - compara las cinco constantes del banco con los valores por defecto de `Settings`;
  - ejecuta el build real del banco (subproceso, sin red, BBDD ni LLM) y comprueba que una línea sin partida
    sale `almacen_sin_partida` con el motivo de familia destinada.

  Además adopta la automejora que propuse.
- **H2 · cerrado.** La partida solo se envía si el revisor la cambió. `partidaParaEnviar` compara con
  `defaultValue`: vaciada ⇒ `""`, sin tocar ⇒ `null`. Los dos guardados usan un único `_conciliaBody`, y el
  backend trata `None` como «no viene» (`review_repository.py:1828-1832`).
- **H3 · cerrado.** El test de R12 ejecuta con node el JS real, extraído de `app.js`. Otro test exige que los
  dos guardados usen `_conciliaBody` y que nadie más escriba `body[field] =`.
- **H4 · cerrado.** `azure-apps/albaranes.md:163-171` (`02b647a`) lista los siete valores de `partida_action`.
  Lo contrasté con el código: `existing_matched`, `new_line_created`, `alm_new_line_created`,
  `inherited_from_base_line`, `no_action`, `almacen_sin_partida` y `almacen_elegido`. También explica que
  `alm_acopio` es un `origen` y que «`codigo_partida_final` vacío = almacén». El árbol de `azure-apps` está
  limpio.
- **H5 · cerrado.** Hay dictamen en `impl_F-051.md` §2.7 y test guarda
  `test_f051_h5_fuera_de_almacen_poner_la_de_la_casada_sigue_sigrid`. El implementer lo comprobó en negativo
  (`and False` ⇒ 2 failed).
- **H6 · cerrado.** `impl_F-051.md` §2.6 y `current.md` dicen ahora `cmd /c rmdir`, «antes de
  `git worktree remove`» y «NUNCA `Remove-Item`».

## Decisiones del humano

- **(a) Fuera de almacén se pinta la partida final.** Cumple. `review_repository.py:1418-1427` pinta la final
  cuando difiere de la de la casada, y en ese caso no pinta la descripción de la casada. La de la casada se
  guarda en `codigo_partida_casada`. Toda entrada del mapa tiene su `vline`, así que `final` nunca es `None`
  fuera de almacén. Los avisos ✓/⚠ siguen comparando con el contrato a través de `_partida_del_contrato`, y en
  almacén no hay aviso, como antes. El test `p2_el_input_de_la_ficha_lleva_la_partida_final` recorre el camino
  completo, del mapa real al `value` del input, que es justo lo que usa H2.
- **(c) O2 corregido.** `cambiaIdentidad` no avisa si el revisor vacía la partida ni si pone la de la casada.
  `data-partida-casada` solo se pinta en filas `assigned`. Es coherente con el backend: la excepción de R20
  exige `matched_id`, y el JS y Python recortan espacios igual.

## Controles negativos re-aplicados por mí

Script en el scratchpad: cada control aplica una sustitución, lanza la suite y restaura el fichero byte a byte.
Al terminar, `git status` limpio.

| Control | Resultado |
|---|---|
| H1 · `sv6_build.py` sin `almacen_sin_partida=` | 3 failed (no pasa el parámetro · vale None · build real `existing_matched`) |
| H1 · `composition.py` de sv6 sin `familias_destinadas=` | 2 failed (no pasa · vale None) |
| H2/H3 · `v \|\| null` dentro de `_conciliaBody` | 2 failed (`'03.02' is None`; `{None} == {''}`) |
| H2 · enviar siempre (sin comparar con `defaultValue`) | 2 failed (`{'03.02'} == {None}`) |
| H2 · copia propia con `v \|\| null` en «Guardar» de la fila | 1 failed (`'_conciliaBody(tr)' in …`) |
| (a) · `elif` de la partida final → `elif False:` | 2 failed (`'03.02' == '07.07'`; `value="07.07"`) |
| O2 · sin la excepción de la casada en `cambiaIdentidad` | 1 failed |

Incidente propio, sin efecto en el resultado: la primera versión del script restauró dos ficheros con LF en
vez de CRLF. `git diff` no mostraba ningún cambio de contenido. Los devolví con `git checkout --`, reescribí el
script para trabajar en bytes y repetí todos los controles.

## Checkpoints

- **C1** [x] init.sh EXIT 0 · [x] ficheros base.
- **C2** [x] solo F-051 `in_progress` · [x] rama de la feature · [x] `current.md` coherente con la pasada 2.
- **C3** [x] hexagonal: `_partida_del_contrato` es un helper de infraestructura y `ConciliacionDisplay` gana
  un campo de presentación · [x] primera línea con ruta · [x] sin prints ni secretos en el delta ·
  [x] reglas de dominio (H1 y H2 resueltos) · [x] trampas: sin DDL, importes intactos.
- **C3 bis** N/A: en el delta no entra ningún documento de fuera. El commit de `azure-apps` no lleva IDs, IPs
  ni secretos.
- **C4** [x] cada requisito y cada hallazgo tiene test, y pasan · [x] sin red ni BBDD (sqlite, sesión simulada;
  node y el subproceso del banco son locales) · [x] verificación real: los controles de arriba ·
  [x] T21–T24 anotadas en `current.md`.
  - Cambio en tests de otra feature, motivado: `test_f011_r13`/`r14` reciben `codigo_imputacion`. Su objeto no
    es la partida, y con H1 una línea sin partida va correctamente a almacén.
- **C4 bis**
  - [x] Rigor declarado.
  - [x] Fase RED con trazas reales por punto (`impl_F-051_pasada2.md` §2).
  - [x] Cobertura 98,5 %.
  - [x] Mutación, recalculada por mí con `alcance_de_feature` + `generar_mutantes` (puro): **14 ficheros,
    503 líneas, 61 mutantes**, igual que el informe. Comprobé que existen tal cual, con su operador y su
    texto, los mutantes nuevos `sv6_build.py:62` (`True→False`), `review_repository.py:164` (`==→!=`) y
    `:1425` (`!=→==`, `or→and`).
  - [x] Campaña **no reejecutada: 909,4 s según el informe** (> 60 s); me quedo en el recálculo y RM1–RM6.
  - [x] Sin «NO VÁLIDA» y 0 sin veredicto.
  - [x] RM1: medida en `53a17ae`; hasta HEAD solo cambia `progress/`.
  - [x] RM2: 909,4 / 61 = 14,9 s, que es la media declarada. Las líneas base son de 247 s en la raíz y
    9–40 s en sv6/sv4, con 4 workers y `-x`: coherente, sin salto de orden de magnitud.
  - RM3: ningún mutante de la lista es equivalente. Los aritméticos sobre cadenas dan `TypeError` y los demás
    cambian salidas que se observan.
  - [x] RM5 N/A: 0 supervivientes y 0 equivalentes.
  - [x] RM6: el delta no quita ninguna guarda.
  - [x] Sección «Evidencias» con sus cuatro números.
- **tasks.md**: sin cambios en la pasada (T1–T20 y T25 `[x]`; T21–T24, del humano). Los commits van como
  `F-051 (review): …`, uno por punto.

## Cobertura de la pasada: hallazgo → test

| Punto | Test |
|---|---|
| H1 | `tests/test_f051_puntos_de_composicion.py` (16) |
| H2 | `test_f051_h2_guardar_solo_envia_la_partida_si_el_revisor_la_cambio` |
| H3 / R12 | `test_f051_r12_guardar_la_fila_envia_la_partida_vaciada` (node), `r12_los_dos_guardados_…` |
| (a) | `test_f051_p2_*` (5) |
| O2 | `test_f051_o2_*` (4) |
| H5 | `test_f051_h5_fuera_de_almacen_poner_la_de_la_casada_sigue_sigrid` |

## Cambios requeridos

Ninguno.

## Para el humano (no bloquean)

1. **⚠ de partida junto a la final pintada.** Tras (a), una fila que hereda `07.07` (R7) y casa con una línea
   de `03.02` pinta `07.07` con ⚠, aunque `07.07` coincida con lo leído del albarán: el aviso compara con el
   contrato. Ya lo plantea el implementer (`impl_F-051_pasada2.md` §7). Es una línea en
   `_partida_del_contrato`, y conviene mirarlo en T24.
2. **Ground truth RES-001…006.** Espera la partida del contrato en una línea sin partida, que es la regla
   anterior a F-051: con H1 salen 24 discrepancias en evals deterministas. Hay que decidirlo antes de T21.
3. **Tests de JS con node.** Si node falta, se saltan con motivo, y en esa máquina `v || null` dentro de
   `_conciliaBody` dejaría de vigilarse; el test estructural sigue vigilando las copias. Aquí node está
   instalado.

**Automejora (propuesta):** en `reviewer.md`, regla de controles negativos: «restaura en bytes (`git checkout
--` o copia binaria), nunca leyendo y reescribiendo en texto»; en Windows eso cambia los finales de línea.
