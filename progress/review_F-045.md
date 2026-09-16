<!-- progress/review_F-045.md -->
# F-045 · Review de la CAPA 1 (T1–T12, T17, T18, T21)

**Revisión incremental desde `3d01f5f` (pasada 2)** — rama
`feature/F-045-banco-evals-revision-manual`, HEAD `e3ffcbd`. Lo aprobado en la
pasada 1 queda dado por bueno; aquí se revisa el delta `3d01f5f..HEAD` (2
commits: 3 ficheros de producción, 3 de tests y el papeleo) más las puertas
enteras, que se ejecutan siempre.

## Veredicto: APROBADO

Los dos bloqueantes están cerrados **con test, no con prosa**, y lo he
comprobado matando los mutantes yo mismo. La capa 1 queda aprobada; el cierre de
la feature depende de tres decisiones del humano, que enumero al final.

**Nivel de rigor: `critico`** (`harness/features.json`): fase RED, cobertura
≥ 80 %, campaña completa sin muestreo, cero supervivientes injustificados y las
MANUAL listadas con su comando.

## Las puertas, ejecutadas enteras

`bash harness/init.sh` → **exit 0**: **811 tests** en 96,6 s; PUERTA COBERTURA
`[OK] 98,3 % de 922 líneas (906/922)`; **PUERTA RUTAS SENSIBLES [evals]: `N/A`
(F-045 no toca ninguna ruta sensible declarada)** —ya por el motivo correcto,
no por falta de rama—; PUERTA TAMAÑO `impl 219/220`, `review 140/140`. Árbol
limpio salvo el `README.md` del humano, que sigue sin tocarse.

## Los dos bloqueantes: verificados muriendo, no leídos

Reinyecté cada mutante en un **worktree aparte** y corrí la suite acotada
(242 tests, 9,9 s de base):

| Mutante | Antes | Ahora | Test que lo mata |
|---|---|---|---|
| 49 `mapa.py:64` `sort_keys=True→False` | sobrevivía | **MUERE** | `test_f045_r7_el_mapa_se_escribe_byte_a_byte_como_dice_su_docstring` |
| 8 `__main__.py:211` `ejecutar=False→True` | sobrevivía | **MUERE** | `test_f045_r16_la_copia_del_libro_es_el_estado_ANTES_de_la_importacion` |
| 9 `__main__.py:290` `parents=True→False` | «equivalente» | **MUERE** | `test_f045_r14_el_informe_se_deja_aunque_su_carpeta_no_exista` |

**Confirmado el punto que pedía el coordinador**: el mutante 8 vive en la CLI y
**solo** lo mata el test de `test_f045_r14_r18_cli.py`; el de `escritura` es
correcto y necesario (fija que la pasada de comprobación no escribe), pero no
alcanza al `__main__`. Al reinyectar el 8 falla exactamente uno, y es el de la
CLI. Los dos tests son de verdad: el de la CLI provoca un cambio real en el
Excel para que la segunda pasada tenga que escribir, y compara los **bytes** de
`copias/` con los del libro previo; el del mapa fija el **contenido literal**
del JSON, no solo el orden de los casos.

## RM1 · el delta tocó producción, así que lo he vuelto a medir

El informe de mutación sigue declarando `SHA de HEAD medido: 1c3e8d7`, y desde
entonces sí cambió producción (`modelos.py`, `informe.py`, `__main__.py`).
Recalculado hoy: el alcance sube de 2371 a **2406 líneas** y el total sigue en
**266 mutantes** (una línea mutada desapareció al extraerse `_libros`). El
**delta `3d01f5f..HEAD` son 36 líneas y genera exactamente UN mutante nuevo**:
`modelos.py:169 en_seco: bool = False → True`. Lo reinyecté: **MUERE**, con
`test_f045_r14_ninguno_tiene_dos_motivos_y_el_informe_los_separa`. La campaña
no hay que repetirla: el único hueco que abrió el delta está medido y cerrado,
y queda aquí escrito con el comando y el resultado.

## Las 16 equivalencias: comprobadas, y cinco las ejecuté yo

16 equivalentes + 74 con test = 90, ninguno pendiente. Las 16 traen ahora su
línea de comprobación. **Cinco de ellas siguen siendo un razonamiento sobre el
código, no una ejecución** (15, 16, 17 de G2, más 18 y 31), así que las corrí
yo: `localizar_bloques` sobre los **seis libros reales** da **94 bloques y
ninguno** conserva un valor por defecto (G2 en pie); `_ultima_con_datos` tiene
un solo llamador y `0 > 0` y `-1 > 0` son falsos (31); `copia_de_seguridad`
exige que el libro exista, así que `copias` es el único nivel que crea (18).
De las demás reproduje G1 (todas las celdas de una fila comparten `.row`), el
10 (`rsplit(1)[-1] == rsplit(2)[-1]`), el 71 (`max(0,n) == max(1,n)` de 1 a
999) y el 72 (las dos guardas dan lo mismo en `None`, `True`, `False`, `0`,
`7`, `'72,50'`, `''`, `'no es'` y `'1.234,5'`). Y verifiqué que tres declarados
equivalentes **siguen sobreviviendo** (6, 18, 71): coherente, ninguno sale
muerto (RM3).

## Los cinco menores

1. **`tasks.md`**: 20 tareas en `[x]` (T1–T12 con sus bis, T17, T18, T21) y una
   nota de estado; abiertas solo la capa 2 (T13–T16) y las MANUAL T19 y T20.
2. **`branch` en `features.json`**: declarada. `harness.alcance --feature F-045`
   ya resuelve solo, y la puerta de rutas sensibles corre y sale N/A porque de
   verdad no se toca ninguna, no porque no tuviera qué mirar.
3. **«Evidencias»**: trae los **4 workers** y los cuatro números al día (811 tests, 98,3 %, 266/90, 102,9 s).
4. **Desviación de §3 en `codigo_imputacion`**: declarada en el aviso del
   informe de importación, con lo que cuesta (la mitad de EXTRACCIÓN del patrón
   1 queda sin vigilar) y cómo se cierra.
5. **Informe de importación regenerado con pasada REAL**: «Libros comprobados:
   6» y «Libros escritos: (ninguno: ningún libro cambiaba; ver R18)». El
   «ninguno» ya distingue sus dos motivos, que era justo lo que me despistó.

## Checkpoints

- **C1** [x] exit 0 y ficheros obligatorios. **C2** [x] una feature
  `in_progress`, rama correcta, `current.md` al día con la pasada 1 y lo que
  falta; `features.json` sigue en `in_progress`, como debe hasta el cierre.
- **C3** [x] el delta respeta la arquitectura: `informe.py` y `modelos.py`
  siguen sin infraestructura, ruta en la primera línea, sin prints de debug ni
  secretos ni dependencias nuevas.
- **C3 bis** N/A **justificado**: no toca `docs/referencia/`. En la pasada 1
  hice igualmente el barrido de lo versionado (correo, `api[_-]?key`, `secret`,
  `token`, `AccountKey=`, GUID): cero hallazgos, y el delta no añade datos.
- **C4** [x] R1–R18, R20–R22 y R24 con test trazable; 811 verdes. R19 lo
  verifiqué ejecutando el conversor (pasada 1). T19 y T20 (MANUAL) listadas con
  su comando en `current.md`.
- **C4 bis** [x] fase RED con trazas reales, cobertura `[OK]`, totales
  recalculados (2406 líneas, 266 mutantes), RM1 re-medido sobre el delta, RM2
  coherente (media 24,0 s × 4 workers ≈ 96 s frente a línea base 141,6 s), RM3
  sin equivalentes muertos, RM4 usado, **RM5 con muestra reproducida** y RM6 sin
  defensa eliminada: los 74 mueren por tests nuevos, no por quitar guardas.
- **C4 ter** [x] la puerta corre y sale N/A con su motivo correcto. **C5** [x]
  `tasks.md` marcado con commit por tarea, sin temporales, estado real.

## Condiciones de cierre (del humano, no del implementer)

No bloquean este veredicto sobre el código, pero **la feature no se marca
`done` sin ellas**:

1. **Copiar los documentos de entrada**: hoy los 59 casos salen
   `fila_sin_fichero`, uno a uno en el informe, como pide R21.
2. **Validar la tipología por pestaña**: confirmé en la pasada 1 que lo
   implementado es lo acertado —`MAPA_TIPO_FAMILIA` de `sv6_build.py:69` está
   indexado por PESTAÑA— y que **la spec §3 es la que está mal**. Falta que el
   humano lo cierre y se corrija §3, no el código. Con ella va la desviación de
   `codigo_imputacion` (menor 4).
3. **La contradicción de RES-004**: los incrementos LER esperados a la vez como
   impresos y como deducidos. Hay que mirar el papel.

**Recomendación no bloqueante**: que `progress/mutacion_F-045.md` recoja el
re-medido del delta (SHA `e3ffcbd`, 2406 líneas, el mutante nuevo y su
veredicto), para que la evidencia viva junto a la campaña y no solo aquí.

## Registro de la pasada 1 (CHANGES_REQUESTED, 2026-09-16)

Bloqueaban dos justificaciones de equivalencia falsas —`sort_keys` del mapa,
que sí cambiaba el fichero, y `ejecutar=False`, que rompía la copia previa de
R16— más cinco menores. Todo cerrado y verificado arriba. **La lección que deja
y que propongo llevar a `CHECKPOINTS.md`** (propuesta, no aplicada): RM5 debe
exigir que la demostración de equivalencia **pueda fallar** —fragmento
ejecutado con su salida— y que el reviewer elija su muestra entre las que
afirman igualdad de un artefacto en disco, que es donde se escondieron las dos.
