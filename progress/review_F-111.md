<!-- progress/review_F-111.md -->
Revisión incremental desde 16023b0 (pasada 2, parte C) · `0b51d6b..e7c1f23` (código desde `0b51d6b^`)

# F-111 · review

**Partes A y B:** APPROVED (pasada 1, `dev...178a29c`). El informe íntegro está en
`progress/review_F-111_partes_AB.md`: se movió ahí para no pasar del tope de 140 líneas. Lo ya aprobado no se ha
vuelto a leer. La suite entera pasó otra vez y no hay regresiones.

## Parte C · primero la partida del contrato (T15–T21)

**Veredicto: APPROVED**

### Nivel de rigor

`critico`, declarado en `harness/features.json`. Exige RED con salida real, puerta de cobertura y mutación con cero
supervivientes. RM5 solo se aplica si hay equivalentes declarados que sigan en el código (aquí no hay).

### Verificación ejecutada por el reviewer

- `bash harness/init.sh` en el worktree con `PYTHONPATH=<worktree>\services\albaranes-comun` y `ARNES_SIN_CACHE=1`:
  **exit 0, «ENTORNO LISTO»**. Todo passed:
  - raíz 1919, sv1 236, sv2 496, sv3 1608 y sv4 2562;
  - **sv5 149**, **sv6 667 (+1 skipped)**, sv9 1186 y comun 1424.

  Puertas: COBERTURA [OK] 100,0 % (57/57), TAMAÑO [OK], RUTAS SENSIBLES en AVISO (C4 ter). `git status` limpio.
- **Recálculo independiente de la mutación** (`alcance_de_feature("F-111", base="16023b0")` + `generar_mutantes`,
  cálculo puro, script en el scratchpad): un fichero (`partida_residuos.py`), **167 líneas, 13 mutantes**. Coincide
  con el informe. La campaña no se reejecutó: 612,3 s según el informe, por encima del umbral de 60 s.
- **RM4, la tercera vía**: copié sv6 al scratchpad y reapliqué 3 de los 13 mutantes reales. Contra
  `test_f111_partida_contrato.py`, los tres mueren y el original pasa (39 passed):
  - `:248` `caidas = 0→1`: 3 failed. Es el superviviente de la pasada 1, y ahora sí lo caza un test.
  - `:249` `and→or`: 4 failed.
  - `:382` `is not None→is None`: 2 failed.
- **RM3**: repasé los 13 en busca de un equivalente marcado como muerto. No hay ninguno: los 13 cambian algo
  observable (el resultado, el número de llamadas o el log que miran los tests). El `-` del log a `+` cambia
  `a_revision=0` a `=2`.
- **Diff leído entero** (código, prompt, ARCHITECTURE, tests nuevos y retocados) y `b69192a..2e8ea2e` (qué quitó T20).

### Los cuatro puntos del encargo

1. **La excepción a F-051 está acotada.**
   - `_objetivo` no cambia: solo entran las líneas de familia `residuos` sin lectura. `ALM` cuenta como lectura y las
     de otra familia no entran. Lo cubre R45.
   - La partida del contrato solo llega a través de `partidas_del_contrato`. Esa función pasa por
     `resolver_partida_obra` y solo acepta `exacta` o `normalizada` sin `cod_repetido`, que son por construcción hojas
     de `lista.hojas`: `casar_partida` usa `lista.codigos` y `_indice_normalizado` sale de las hojas. Por eso el
     `next(...)` no puede lanzar `StopIteration`.
   - Sin lista, `MOTIVO_SIN_LISTA` sale antes de leer el contrato (R44). Ningún otro fichero de producción de sv6
     cambia: ni matcher, ni builder, ni pipeline.
2. **El prompt de sv5 solo cambia la frase de candidatas.** El `system` cambia únicamente la frase de candidatas. Las
   reglas, `task`, `schema_hint` y el esquema quedan igual. El otro cambio está en el comentario YAML de cabecera, que
   no llega al modelo. El test R48 comprueba que la frase nueva está, que la vieja ya no y que se mantienen las reglas
   de R32.
3. **Los tests retocados no relajan ninguna aserción.**
   - En los dos `_envelope` de sv6 (`test_f111_partida_residuos.py` y `test_f111_pipeline.py`) solo se vacía el
     `codigo_partida` del contrato, con `model_copy`, para que sigan probando el paso 3 (R40). No se borra ni se
     cambia ningún `assert`.
   - `test_f111_partida_contrato.py` tras la RED: `env`→`_`, el log se endurece (`caidas_al_capitulo=0`) y 3 tests más.
4. **El informe de mutación es real.**
   - Se generó con la herramienta, y los totales coinciden con mi recálculo.
   - RM1: midió `2e8ea2e`. Entre `2e8ea2e` y `e7c1f23` solo cambian `progress/` y `tasks.md`, nada del alcance.
   - RM2: 13 × 47,1 = 612,3 s, cuadra; media 47,1 s frente a base 45,0 s. Sin «⚠ CAMPAÑA NO VÁLIDA»; sin veredicto 0.

### Checkpoints

**C1** [x] init.sh exit 0 · [x] ficheros del arnés. **C2** [x] única `in_progress` · [x] rama `feature/F-111-…` · [x] `current.md`.
**C3**
- [x] Hexagonal: la lógica nueva va en `application`, es pura y no tiene I/O. Usa solo puertos ya existentes y
  funciones de comun. Comun no cambia.
- [x] Primera línea con la ruta. Sin `print`, `TODO` ni secretos. Sin dependencias nuevas.
- [x] Dominio: partida del contrato siempre validada contra la obra; rastros sin revisión (D4); intento en la línea y
  nunca en cabecera; `codigo_partida_albaran` vuelve a la lectura vacía. Todo con test.
- [x] R47: `ARCHITECTURE.md` recoge los tres pasos, la caída al capítulo y la excepción a F-051 (punto 16).

**C3 bis** N/A: la parte C no toca `docs/referencia/`.
**C4**
- [x] Cada requisito de la parte C tiene test (tabla abajo) y todos pasan.
- [x] Sin red ni BBDD: elector y puertos falsos, y listas sintéticas.
- [x] MANUAL listada: T13 sigue `[ ]` en `tasks.md`, ampliada con las líneas de la parte C.

**C4 bis**
- [x] `critico` · [x] RED real de T15 (`ImportError`), T17 (22 failed) y T18 (1 failed), §C.4 · [x] cobertura 100 %.
- [x] `mutacion_F-111_C.md` de la herramienta y recalculado · [x] >60 s: recálculo + RM1–RM6 + RM4 · [x] 47 s/mutante.
- [x] RM1 · [x] RM2.
- N/A RM5: no queda ningún equivalente en el código. Los 2 de la ronda manual eran código redundante y se
  eliminaron.
- [x] RM6. Las dos comprobaciones que quitó T20 no eran defensa:
  - el filtro de vacías: `casar_partida` devuelve `sin_partida` con `None` o vacío y `resolver_partida_obra` lo pasa
    a `no_aplica` (`partidas.py:583`, `:669`);
  - `codigo in vistas`: el dict ya deduplica, conserva la primera inserción y guarda la misma hoja.
- N/A campaña manual sustitutiva: la automática dio 13 y la tabla manual es un complemento (ver O-C2).
- [x] Ningún superviviente `PENDIENTE` · [x] «Evidencias» con los cuatro números.

**C4 ter** [x] con motivo escrito (exigencia `aviso`). La puerta señala `prompts.yaml` de sv5 y `partida_residuos.py`
sin `progress/evals_F-111.md`. No bloquea:
- el cambio del prompt es una frase descriptiva, sin reglas nuevas, y tiene test de texto;
- la pasada `--con-llm` cuesta dinero y la decide el humano;
- se mantiene el D8 = (a) de la PARADA 1.

**C5** [x] T15–T21 `[x]`, con commits `F-111 Tn:` · [x] sin temporales sin trackear · [x] `features.json` sigue en
`in_progress`, que es el estado real (T13 está pendiente).

### Cobertura requisito → test (sv6 `test_f111_partida_contrato.py` salvo que se indique)

| Req. | Test(s) |
|---|---|
| R37 | `r37_*` (8): descartes, orden, normalizada, no hoja, ambigua, cod repetido, `alm=None`, contrato `None`, `ALM` vía `asignar` |
| R38 | `r38_0686_*` (sin IA), `r38_0669_*` (la IA recibe solo `31.01` y `102.08.01`); pipeline `test_f111_r38_el_pipeline_toma_la_partida_del_contrato` |
| R39 | `r39_0694_*`, `r39_varias_*`, `r39_sin_capitulo_*` |
| R40 | `r40_0687`, `r40_0459`, `r40_sin_capitulo_*`; además la parte B entera (`test_f111_partida_residuos.py`, contrato sin partidas) |
| R41 | `r41_solo_las_que_caen_*`, `r41_con_todas_elegidas_una_sola_llamada`, más el número de llamadas en `r43_*` |
| R42 | `r42_anotar_contrato_sin_revision_y_lectura_de_vuelta`, y los prefijos en `r38`/`r39` |
| R43 | `r43_*` (9): 5 variantes de «no elige», capítulo de una, el capítulo también falla, IA caída, obra sin capítulo, sin elector, 5 códigos, `anotar` |
| R44, R45 | `r44_*`, `r45_con_lectura_y_apagado_no_se_toca` |
| R46 | `r46_constantes_congeladas`, `r46_el_log_dice_el_paso` (×3), `r46_el_log_cuenta_las_caidas_al_capitulo` |
| R47 | lectura de `docs/ARCHITECTURE.md` (puntos 16 y 27) |
| R48 | sv5 `test_f111_r48_las_candidatas_son_hojas_de_la_obra_del_contrato_o_del_capitulo` |

### Condiciones para el `done` (no son cambios al código)

1. La C1 de A/B (el humano acepta por escrito los 3 equivalentes) ya consta como aceptada en `7493a10`.
2. **T13** (MANUAL, después de desplegar **sv5 y sv6** y de revalorar). Hay que comprobar las 8 líneas de `design.md`
   §13 y contar cuántas `partida_residuos_contrato_sin_eleccion` salen.

### Observaciones (no bloquean)

- **O-C1 · R42 «misma herencia de las sintéticas (R24)».** Ningún test de la parte C cubre las sintéticas LER con una
  partida del contrato. No hace falta para aprobar: el código que copia la partida al sobre (`nuevas` → `copia`) es
  común a los tres pasos, y el test R24 de la parte B lo ejercita.
- **O-C2 · El anexo de mutantes a mano no se puede reproducir.** Está en `mutantes_c.py`, en el scratchpad de la
  sesión, y las filas no traen el texto exacto original → mutado. No cuenta como evidencia (la automática basta),
  pero conviene versionarlo o escribir ese texto.
- **O-C3 · Coste.** En el peor caso, el paso 1 con 2 o más partidas en el capítulo y la IA en `null` hace dos llamadas
  de pago con conjuntos que se solapan. Es lo que dice R43 y está acotado a dos.
- **Automejora (propuesta, no aplicada).** `harness/rigor.json` tamano.review: el tope de 140 es por fichero. Una
  feature que se reabre por partes lo agota con la primera review. Propuesta: que `harness/tamano.py` acepte un
  `review_F-XXX_<parte>.md` aparte, o documentar en `CHECKPOINTS.md` el patrón de mover la review anterior a un
  fichero hermano, como se ha hecho aquí.
