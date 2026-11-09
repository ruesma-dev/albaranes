<!-- progress/review_F-117.md -->
# F-117 · Review (reviewer)

Revisión completa (pasada 1): `git diff 9c4bf43..f37c85a` (HEAD), rama `feature/F-117-partida-equivalente-en-obra`.

**Veredicto: CHANGES_REQUESTED** — el código, los tests y la campaña están bien. Lo que falta es papeleo de
cierre del líder: C4 (MANUAL en `current.md` sin su comando) y C5 (`tasks.md` T10). Son dos cambios de una línea;
la pasada 2 puede ser incremental y no hace falta tocar código.

**Nivel de rigor:** `critico`, declarado en `harness/features.json`. Exige fase RED, cobertura ≥ 80 % de lo
cambiado, mutación con 0 supervivientes, RM1–RM6 y las MANUAL listadas con su comando exacto.

## Verificación ejecutada por el reviewer

- `bash harness/init.sh` en el worktree, con `PYTHONPATH=<worktree>\services\albaranes-comun` y `ARNES_SIN_CACHE=1`,
  sobre `f37c85a`: **EXIT=0**. raíz 1919, sv1 236, sv2 496, sv3 1608, sv4 2562, sv5 149, **sv6 706**, sv9 1186,
  **comun 1492** (+2 skipped), todo passed. `PUERTA COBERTURA: 100.0% de 57 líneas cambiadas (57/57)` [OK].
  `PUERTA TAMAÑO` [OK]. `PUERTA RUTAS SENSIBLES [evals]` en AVISO (ver C4 ter). `git status` limpio después.
- Mutación, recálculo puro (`harness.alcance` + `harness.mutacion.generar_mutantes`): con base `9c4bf43`
  **y con base `dev`** (los scripts ya no están en la rama) salen los mismos **157 líneas en 6 ficheros y 32
  mutantes** (normalizador 55/19, settings 9/1, composition 1/0, `__init__` 1/0 y 2/0, partidas 89/12). Igual
  que el informe.
- **Campaña no reejecutada: 291,3 s según el informe** (> 60 s). Sí apliqué RM4 sobre una copia de comun en el
  scratchpad (`git archive`, sin tocar el árbol). Reproduje dos mutantes del recálculo, texto exacto:
  - `partidas.py:756` `or _choca_con_no_hoja` → `and _choca_con_no_hoja`: **MUERTO**, 4 fallos (`r8_capitulo_cd02`,
    `r8_no_hoja_por_su_cod`, `r8_no_hoja_con_letra`…).
  - `partidas.py:731` `len(lectura) >= MIN_SEGMENTOS_SUFIJO` → `>`: **MUERTO**, 5 fallos (`r4_con_letra…`,
    `r7_alm_configurable`, `r8_no_hoja_por_su_cod`…).
  Original restaurado: 70 passed.

## Checkpoints

**C1** [x] `init.sh` exit 0. [x] Ficheros base del arnés presentes. **C2** [x] Una sola `in_progress`. [x] Rama de
la feature. [x] `current.md` al día para F-117. [x] Las `done` con su resumen en `history.md` (sin cambios aquí).
**C3** [x] Hexagonal: la regla pura vive en comun `sigrid/partidas.py`; sv6 la aplica en `application/services`
(ya importaba `ruesma_comun.sigrid`); el interruptor va en `config`, cableado en `interface_adapters`. Sin DDL,
colas ni endpoints. [x] Primera línea con la ruta en los 3 tests nuevos (los `.py` modificados ya la traían).
[x] Sin `print`, sin TODO, sin secretos, sin dependencias nuevas. [x] Reglas de ARCHITECTURE: regla 23 ampliada
con la excepción a H1. Las tres trampas: no se toca merge/raw ni schema, y los importes no cambian (R24: 540 €).
**C3 bis** N/A: no toca `docs/referencia/`.
**C4** [x] Todos los requisitos con test trazable y en verde (tabla abajo). [x] Sin red ni BBDD (puertos y
repositorio falsos). **[ ] Las MANUAL no están en `progress/current.md` con su comando exacto.** La línea de
F-117 dice «T8 (despliegue de sv6) es del humano; T9 la mide el líder», sin comando. Los comandos sí están en
`tasks.md` T8/T9 y en `impl_F-117.md` §6, pero el checkpoint pide `current.md` → cambio 1.
**C4 bis**
- [x] `rigor` declarado (`critico`).
- [x] Fase RED con la salida real (`impl_F-117.md` §4): comun 68 failed/1 passed, con causas `AttributeError`
  por la función inexistente. sv6 32 failed + 1 error. Pipeline 5 failed. Los 3 fallos de fixture tras T4 están
  explicados: rama directa con el NETO (regla 13) y IA4 sin línea de contrato. El fixture corregido no relaja
  nada de lo que exige R24.
- [x] Cobertura [OK] 100 % (57/57). [x] Mutación: informe de la herramienta, totales verificados por mi cuenta (arriba). 0 supervivientes, 0
  timeouts, «Sin veredicto (base rota)» = 0, sin cabecera de campaña no válida, línea base medida (8 filas).
- [x] Muertos comprobados. Campaña > 60 s, así que basta recálculo + RM. Además, RM4 con 2 muestras.
- [x] Coste por mutante = 291,3 × 4 ÷ 32 = **36,4 s**: dentro de la línea base (sv6 ~22 s, comun ~39 s) con `-x`.
- [x] RM1: el informe se midió sobre `09d2800`. De ahí a HEAD solo cambian `progress/`, `tasks.md` y el borrado de
  `scripts/medicion_F-117/`, nada del alcance. El alcance de hoy coincide con el medido, línea a línea.
- [x] RM2: `32 × 9,1 = 291,3` y `media × W = 36,4 s` frente a líneas base de 21,5–40,0 s. No hay salto de orden de magnitud.
- [x] RM3: ninguno de los 32 mutantes es equivalente; los repasé uno a uno. Por ejemplo, el
  `self._equivalente or …` lo mata `r13_por_defecto_apagada`, y `MAX_CODS_AMBIGUA = 6` lo mata el parametrizado de R16.
- [x] RM5 N/A (sin supervivientes ni equivalentes declarados). [x] RM6: no se quitó ninguna guarda `None`; `clave is not None` sigue en su sitio. Lo que se quitó son tres
  condiciones de design §3 (D-3 del implementer). El invariante lo comprobé en quien construye el dato, que es la
  misma función: `equivalentes_partida` sale con `()` si `resolver_partida_obra` no da `fuera_de_lista`.
  `_casar_simple` busca en `_indice_normalizado`, que indexa con `normalizar_partida` el cod **y** el código completo
  de cada hoja. Así, una lectura cuyos segmentos coinciden con los de alguna forma de una hoja nunca llega como
  `fuera_de_lista`, salvo que choque con una no hoja, y ese caso ya lo excluye la línea 756. Por eso son
  redundantes «la hoja tiene letra», «la lectura no tiene letra» (`_sin_letra` no deja ninguna) y «la hoja es más
  larga». La docstring de `_equivalente` lo deja escrito y los tests de R3 y R4 lo fijan.
- [x] «Evidencias» con los cuatro números y los workers (4). [x] Ningún N/A sin motivo.

**C4 ter** (rutas sensibles: el diff toca `services/albaran-valoracion-persist/application/services/**`)
- [ ] Falta `progress/evals_F-117.md`. Exigencia declarada: `aviso`. **Dictamen: no bloquea el APPROVED, pero sí
  es condición de cierre (`done`).** Motivo: el arnés lo declara `aviso`, y la pasada es de pago y la lanza el
  humano. Pero F-117 cambia la partida que recibe IA4 (R-2 de design §10, el efecto buscado), y desde F-084 los
  fixtures de IA4 tienen 13 casos, así que la pasada ya no daría NO_EVALUABLE. Antes de `done`, o
  `python -m evals.runner --con-llm --feature F-117` en verde, con las 3 líneas de `exige_lineas`, o la renuncia
  del humano por escrito en `history.md`. Si se ejecuta, el informe tiene que ser posterior a `2aa328a` (último
  commit que toca la ruta sensible) → cambio 1.
- [x] El motivo del `aviso` consta aquí.

**C5**
- **[ ] `tasks.md` T10 sin marcar.** `init.sh` está en verde sobre HEAD (lo verifiqué yo) → cambio 2. T8 y T9 son
  MANUAL posteriores al despliegue y van tras la fusión: N/A justificado, como en F-110 y F-111. Un commit por
  tarea T1–T7 [x]: T7 en dos commits, `09d2800` y `2ce59db`, aceptable.
- [x] Sin temporales ni ficheros sin trackear en el worktree. La *junction* `.venv` de sv4 está anotada para
  retirarla.
- [x] `features.json` dice `in_progress`, que es el estado real.

## Desviaciones del implementer (§3 y §2)

- **D-1 `test_f111_t5_version_0130`, de `== 0.13.0` a `>= 0.13.0`: ACEPTADA.** La spec se contradice: R12 pide
  0.14.0 y design §7 dice que no se toquen los tests de F-111. El implementer siguió el precedente del repositorio
  (F-076, F-098, F-110 y F-111 hicieron lo mismo). La aserción sobre `pyproject` hasta sale más fuerte: ahora
  comprueba que pyproject y `__version__` coinciden. Ninguna otra aserción de F-111 cambia.
- **D-2 la fila de `sv6.md`: ACEPTADA.** Es la tabla de variables del servicio y F-111 metió ahí la suya.
- **D-3 las tres condiciones omitidas en `_equivalente`: ACEPTADA.** Las verifiqué en el origen del dato (RM6).
- **R16, motivo solo en la línea: ACEPTADA.** R16 no pide cabecera, a diferencia de R15. La cabecera lleva
  `partida_fuera_de_lista` como hoy, así que la revisión no se pierde.
- Quitar `scripts/medicion_F-117/` (`f37c85a`, del líder): aceptado, por el precedente de F-111. Condición:
  versionarlos en la chore de cierre **antes de T9**, que los ejecuta (`tasks.md` T9).

## Cobertura requisito → test

| Req | Test(s) (comun `test_f117_equivalentes_partida.py`, sv6 `test_f117_partida_equivalente.py` / `_pipeline.py`) |
|---|---|
| R1–R3 | `test_f117_r1_*` (3), `r2_*` (8: letra, ceros, código completo, segmentos), `r3_*` (2) |
| R4–R6 | `test_f117_r4_*` (5), `r5_*` (2), `r6_*` (3, incluida la ambigua de la 0459) |
| R7–R9 | `test_f117_r7_*` (5), `r8_*` (3, `CD.02` de la 0692), `r9_*` (4) |
| R10–R12 | `r10_resolver_y_casar_siguen_igual` + F-049/F-076/F-098 intactos en verde; `r11_*` (2); `r12_*` (2) |
| R13–R18 | sv6 `r13_*` (4), `r14_r15_anotar_una_equivalente`, `r14_*` (2), `r15_*`, `r16_*` (3), `r17_*`, `r18_*` (comun y sv6) |
| R19–R23 | `r19_*` (3), `r20_*` (2), `r21_*`, `r22_*` (2), `r23_*` (2) |
| R24–R26 | `r24_albaran_de_0719`, `r24_sin_f117_es_lo_de_hoy`, `r25_sufijo_de_0719`, `r26_valoracion_directa[letra/sufijo]` |
| R27 | ARCHITECTURE regla 23 (diff leído) y `azure-apps` `a3cd897` §11.2 (leído: variable, efecto, «pendiente de despliegue») |

## Cambios requeridos (los dos son del líder; ninguno toca código)

1. `progress/current.md`, línea de F-117 (punto de reanudación): listar las MANUAL con su comando exacto.
   - T8 (humano), desde `infra/`: `.\deploy.ps1 -Only sv6` → `.\check_deploy.ps1`, con la revaloración de D7.
   - T9 (líder, solo lectura): `.\scripts\medicion_F-117\run.ps1 m1_fuera_de_lista.py` y `… m2_estrategias.py`,
     con la nota de que los scripts vuelven en la chore de cierre.
   - Evals (humano, de pago, condición de `done`): `python -m evals.runner --con-llm --feature F-117`, o la
     renuncia escrita.
2. `specs/F-117-partida-equivalente-en-obra/tasks.md:15` (T10): marcar `[x]` con la verificación del reviewer
   (`init.sh` exit 0 sobre `f37c85a`, 57/57).

## Observaciones (no bloquean)

- O1. `services/albaran-valoracion-persist/sv6.md:793`: el párrafo de la normalización de F-076 no cita F-117.
  Basta una frase que remita a la regla 23 de ARCHITECTURE. No lo pide R27.
- O2. `partidas.py:756`: la compuesta se detecta con un `/` ASCII, mientras que `normalizar_partida` aplica NFKC
  (`／`). El efecto es inocuo, porque el segmento resultante (`8/X`) no coincide con ninguna hoja y da `()`, pero
  `"/" in normalizar_partida(lectura)` sería más coherente.

## Automejora (propuesta para el humano, no aplicada)

- `harness/rutas_sensibles.json` (`_exigencia`) y `CHECKPOINTS.md` C4 ter dicen que los seis `_indice.json` tienen
  la lista de casos vacía. Hoy cinco tienen casos (IA1 59, IA2 9, IA3 59, IA4 13, final 59; solo `contratos` está
  vacío). Toca decidir si se sube a `bloqueo` o al menos corregir el texto (genérico, portable a `arnes-base`).
- `specs/SPECS.md`: proponer que, cuando una spec sube la versión de comun, `design.md` §7 exceptúe de antemano los
  tests de versión exacta de features anteriores. Esa contradicción se ha repetido en F-076, F-098, F-110, F-111 y F-117.
