<!-- progress/review_F-038.md -->
Revisión completa (pasada 1) del rango `34dada0..b43d672` — 18 commits, 26
ficheros, 2.459 líneas. **Corrección de rango:** el encargo decía
`a69fd66..b43d672`, pero `a69fd66` es el **primer commit de la rama**, no la
punta de `dev`: `git merge-base dev HEAD` = `34dada0`. Revisado el superconjunto.

# F-038 · Review

**Veredicto: APPROVED**

**Nivel de rigor:** `estandar`, **declarado** en la ficha. Exige fase RED,
cobertura y campaña con supervivientes analizados; no exige cero supervivientes
ni la demostración ejecutable de RM5.

## Verificaciones ejecutadas

- `bash harness/init.sh` → **exit 0**: 389 passed, 8 servicios verdes,
  `PUERTA COBERTURA 95.9%` (164/171), `PUERTA TAMAÑO dentro de los topes
  (requirements 119/120, design 162/200, impl 150/150)`.
- **La puerta nueva frena de verdad** (copia en scratchpad, sin tocar el árbol):
  con `impl_F-038.md` de 151 líneas, `harness.tamano` sale **1** nombrando
  fichero, líneas y tope, y `ko()` suma a `FALLOS` → `exit 1`. Sin bloque
  `tamano` sale **2** con el motivo impreso, que 7 quater vuelca en `warn`.
- **Sin off-by-one:** `contar_lineas` = `splitlines()`; cuenta blancos y la
  última línea sin salto final (probado: 120 líneas sin `\n` = 120, no excede).
  El corte es `> tope`: 150/150 pasa y 151 falla. El informe del implementer
  está en el límite exacto, medido bien.
- **T0 verificado en vivo:** `ejecutor_para` devuelve `ruta='tests'` para los
  cuatro ficheros del alcance e `identidad()` la incluye: la campaña sí juzgó algo.
- **Recálculo independiente:** `harness.alcance` = 205/9/60/195 = **469 líneas**;
  `generar_mutantes` = **55** (tamano 25, mutacion 17, rigor 13). Coincide.
- **Único superviviente muestreado:** `tamano.py:47`, operador `booleano`,
  `frozen=True` → `frozen=False`. Existe como mutante real, mismo texto.
- **Campaña NO reejecutada: 728,5 s (12,1 min) según el informe**, muy por
  encima del umbral de 60 s: recálculo puro + RM1–RM6. RM4 tampoco hizo falta.
- `arnes-base` **no tocado** (limpio, último commit de F-034), D6 respetado; y
  árbol de trabajo limpio antes y después de esta revisión.

## RM1–RM6

- **RM1 [x]** SHA `337a948fe48f7813780e5e5b72994cc3b84dceca`. Los tres commits
  posteriores tocan solo `progress/*` y `tasks.md`: ni un fichero del alcance.
  Medición fresca.
- **RM2 [x]** base 52,1 s, media 36,4 s (728,5/20 cuadra). Que la media quede
  bajo la base es esperable: se corre con `-x` y 19 de 20 murieron abortando
  antes de acabar. Nada parecido al 111 s de F-034.
- **RM3 [x] con salvedad (O1)** Ningún equivalente sale muerto en la campaña de
  registro. El implementer declara por su cuenta que `mutacion.py:1781` salió
  MUERTO en la 1ª campaña y SUPERVIVIENTE en la 2ª sin cambiar código: muerte
  falsa en una campaña **anterior**, ya superada. Ver O1.
- **RM5 N/A justificado por nivel** (`estandar`). La justificación escrita
  **se sostiene**: `frozen` no altera ninguna salida, nadie asigna atributos a un
  `Exceso` ni lo mete en un set; matarlo pediría un test de
  `FrozenInstanceError`, que comprueba el lenguaje, no la feature.
- **RM6 [x]** No se quitó ninguna guarda. Los seis huecos se cerraron
  **añadiendo tests** (T12 1/2 y 2/2), incluido el eco que mata el
  `if max_mutantes is not None` de `mutacion.py:1781`.

## CHECKPOINTS

- **C1 [x]** exit 0; los siete documentos existen.
- **C2 [x]** una sola `in_progress`; rama correcta; `current.md` con la sesión
  activa y la deuda declarada; F-039 dada de alta como ficha.
- **C3 [x]** hexagonal **N/A justificado**: feature de arnés, `services/**` sin
  tocar. Ruta en la primera línea de los 6 ficheros nuevos; sin secretos ni
  prints de debug (los `print` son salida de CLI); los 13 avisos de `ruff` están
  fuera del alcance del diff (deuda previa).
- **C3 bis N/A justificado:** no toca `docs/referencia/`.
- **C4 [x]** trazabilidad R1→R22 completa; sin red ni BBDD; MANUAL pendientes: 0.
- **C4 bis [x]** fase RED con **salida real** de T0, T3, T5 y T6 y error literal
  del resto; cobertura OK; totales verificados; ningún `PENDIENTE`; «Evidencias»
  con los cuatro números.
- **C4 ter [x]** `PUERTA RUTAS SENSIBLES: N/A` — no toca ninguna.
- **C5 [x]** T0–T14 `[x]`, un commit `F-038 Tn:` cada una (P1 es explícitamente
  posterior al merge); árbol limpio; `features.json` coherente.

## Trazabilidad requisito → test

| Req | Test |
|---|---|
| R1–R4 | `test_f038_r1_r4_ejecutor_raiz.py` (10) |
| R5–R9 | `test_f038_r5_r9_muestreo_por_nivel.py` (23) |
| R10–R12 | `test_f038_r10_r12_informe.py` (14) |
| R13–R16 | `test_f038_r13_r16_tamano.py` (21, dos leen `init.sh`) |
| R17–R21 | `test_f038_r17_r21_documentos.py` (15, los 5 documentos) |
| R22 | Sin test: es contenido. Verificada la cabecera «⚠ CAMPAÑA NO VÁLIDA» en `mutacion_F-011.md` y `_F-012.md`, y el criterio de por qué F-034 no se marca. |

## Observaciones (no bloquean) y automejora propuesta

1. **O1 · Hay un test inestable en la suite de la raíz**, según declara el
   propio implementer. Fuera del alcance de F-038 y la campaña de registro vale,
   pero una campaña de mutación vale lo que valga su suite: **propongo ficha**,
   con F-039 como candidata a heredarlo.
2. **O2 · Matizar RM2 en `CHECKPOINTS.md`** (propuesta, no aplicada): «la media
   no puede ser muy inferior a la línea base» marcaría esta misma campaña (36,4
   vs 52,1). Con `-x` un muerto termina antes que la suite limpia; la alarma es
   el salto de **orden de magnitud**.
3. **O3 · Menor:** en un proyecto no-Python 7 quater no imprime nada (igual que
   cobertura) y `CHECKPOINTS.md` promete `N/A` con motivo: deuda previa, a
   corregir en el porte a 1.7.0.

---

# Pasada 2 · revisión INCREMENTAL desde b43d672 (`b43d672..HEAD`, HEAD 7d08de6)

**APPROVED. Cambios requeridos: ninguno.** Lo aprobado hasta `b43d672` queda dado por bueno. Delta: 6 commits, 16 ficheros, **ni una línea de lógica de producción**; T15–T17 `[x]` con su commit `F-038 Tn:`.
`bash harness/init.sh` entero y en verde: **391 passed**, cobertura 95,9 %, `PUERTA TAMAÑO 119/150 · 162/250 · 218/220 · 100/140` — contrastado con `wc -l`, la medición es correcta.
**Sin remedición de mutación:** recalculé el alcance en HEAD y da los mismos 4 ficheros y **469 líneas** que el informe medido en `337a948`; el delta no toca ningún `harness/*.py`, así que RM1 sigue en pie.

**T15 · topes 150/250/220/140 — [x] completo.** `grep` de los cuatro valores viejos en todo el repo: no queda **ningún** punto de cableado con ellos.
Los 9 ficheros están (`rigor.json` con el `$doc` del motivo, `SPECS.md`, los tres agentes, **R13** de `requirements.md`, la tabla de `design.md`, los dos tests).
`CHECKPOINTS.md` no cableaba ninguno: **verificado**. Tampoco `tamano.py`, `rigor.py` ni `init.sh`, así que R13 («nunca cableados en el código») se cumple.

**T16 · RM2 por orden de magnitud — [x].** Sigue cazando F-034 (18 mutantes en 111 s ⇒ media 6,2 s contra una base de ~120 s: 6,2 < 12,0, dispara) y **no** marca la campaña legítima de esta feature (36,4 s contra un umbral de 5,21 s, y 20 × 36,4 = 728 ≈ 728,5 del «Tiempo total»: coherente por las dos vías).
Misma redacción en `CHECKPOINTS.md` y en el agente, con un test que la fija.

**T17 · el flaky de paridad — [x].** (a) El arreglo es **del test**: el diff no toca `mutacion.py` ni `mutacion_paralela.py`.
(b) El filtro **no se ensanchó de más**: sigue comparando alcance, los seis totales, SHA, línea base, muestreo y las fichas de supervivientes; una diferencia real serie/paralelo sigue fallando.
(c) La única fila de reloj que queda fuera del filtro es `| Línea base (s) — …`, y aquí no varía: `_EjecutorFalso` no tiene `linea_base` y ambos informes imprimen `n/d`. Con eso el informe queda **determinista**, no «menos flaky». 3/3 en verde por mi parte, además del init completo.

## F-039 · qué cierra T17 y qué no

- **(a) test inestable de la suite de la raíz: CERRADO por T17.** Es el mismo test, identificado por su nombre, hecho determinista y con el porqué escrito (T5 añadió una fila de reloj y nadie extendió el filtro). Encaja con la prueba de la ficha: la campaña corre con `-x`, así que un fallo intermitente de *cualquier* test se lee como MUERTO — justo el falso MUERTO de `mutacion.py:1781`, que en la 2ª campaña salió SUPERVIVIENTE, su veredicto verdadero. **Retirar de F-039** ese criterio de aceptación.
- **(b) campaña paralela: causa eliminada, falta UNA confirmación.** La ficha dice que la base aborta *porque falla ese test*, y ese test ya no falla. Su «sospecha a verificar» —«el worktree no trae lo que ese test espera en disco»— queda **refutada**: el test se fabrica su propio repo en `tmp_path` y su `Alcance` es un literal, no lee nada del worktree. Falta solo correr `python -m harness.mutacion --feature F-038 --workers 5 --salida <fuera de progress/>` y ver la línea base en verde; no lo hago aquí porque son 5 suites simultáneas y esta sesión lo tiene prohibido. **Reescribir** ese criterio como verificación, no como arreglo.

## Observaciones (no bloquean)

1. El filtro del test es una lista de prefijos escrita a mano: la cuarta fila de reloj que se añada volverá a romperlo. Propuesta para el porte a 1.7.0: derivar la exclusión de una constante junto a `escribir_informe`.
2. RM2 solo dispara a 10× y, con «Tiempo total» > 60 s, tampoco se reejecuta: un informe «solo» 5 veces demasiado rápido pasaría. Aire deliberado, pero queda dicho.
3. `BACKLOG.md`/ficha F-038 y `progress/current.md` siguen citando 120/200/150/100 como decisión original: es rastro, no cableado, pero una línea de «recalibrado el 2026-08-20» en `current.md` al cerrar evita el tropiezo.
