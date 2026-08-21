<!-- progress/current.md -->
# Trabajo en curso

## Cierre de sesión — 2026-08-20 (sesión del 19 y 20 de agosto)

Sesión larga y casi entera dedicada al **arnés**. Se cierra a propósito para
liberar contexto: lo que queda es trabajo largo y conviene retomarlo limpio.

### Lo primero al abrir la próxima sesión

1. **`git push`: HECHO el 2026-08-20.** `arnes-base` subió sus 8 commits
   (`9e2ced7..c6d4979`, la 1.6.3 y la 1.7.0 completas) y `albaranes` sus 72 de
   `dev` (`73b00d7..82f3e20`). Ya no hay trabajo del arnés en un solo disco.
   `main` de `albaranes` NO se tocó y no se creó ningún PR.
2. Por orden: **F-036 (residuos, lo único que toca dinero)** → **F-039 (subida
   a prioridad 2: sin una suite estable, ninguna medición del arnés vale)** →
   actualizar los otros cuatro proyectos con el instalador ya seguro.
3. **Decidir qué se hace con `progress/mutacion_F-011.md`** (ver «F-038 · lo que
   queda después del cierre», punto 2).

---

## Estado del arnés

| Repositorio | Versión | Estado |
|---|---|---|
| `arnes-base` | **1.7.1** | 1.7.0 (F-038) pusheada el 20-ago. La **1.7.1 (F-039)** son 2 commits locales **sin subir**: `--ficheros` con su guarda de alcance vacío y `lineas_comparables`. Destino: 153 passed, instalador 65 verde |
| `albaranes` | **1.6.1** sellado, pero con **el código de F-038 y F-039 dentro** | El sello y el código YA NO COINCIDEN: F-038 se desarrolló aquí y se portó allí, pero **la 1.6.2 y la 1.6.3 nunca llegaron a este repositorio**. En particular **le falta el arreglo del bytecode envenenado**, que es lo que provocaba mutantes «muertos» falsos. Se arregla actualizándolo con el instalador |
| `porcentajes`, `postventa-incidencias` | 1.5.2 | sin actualizar |
| `datamart-seg-anual` | 1.5.0 | sin actualizar |
| `partes` | 1.4.0 | sin actualizar |

**F-035 esta cerrada, asi que el instalador ya es seguro**: los cuatro
proyectos atrasados se pueden actualizar cuando el humano quiera.

### F-034 · el mutador muta `is` / `is not` — CERRADA (done, en `dev`)

APPROVED en **tercera** pasada. `x is None` es LA guarda de ausencia en Python y
el mutador no la conocía: las campañas de F-019 y F-027 —los dos defectos más
caros del proyecto, ambos en una guarda `is`— se midieron ciegas justo ahí.

Las dos primeras pasadas rechazaron con razón:

- **1ª**: culpa del líder, no del implementer. Propagó el arnés 1.6.0 **dentro
  de la rama** después de medir las puertas, y la rama pasó a tener 1.057 líneas
  donde el informe declaraba 56. **Lección: la propagación del arnés va en su
  rama `chore/` y DESPUÉS del merge, nunca dentro de la rama de una feature.**
- **2ª**: la campaña de mutación **mentía**. Declaraba 18/1/0 en 111 s y al
  reejecutarla salía 9/8/2 en 63 min. El reviewer lo demostró sin ejecutar nada:
  dos mutantes declarados MUERTOS eran semánticamente idénticos al original.
  De sus 8 supervivientes, **cuatro eran huecos reales** en `_es_palabra`,
  `_delimitado` y `_localizar` — la función que decide si una mutación de `is`
  cae en el sitio correcto. Sin esa insistencia, la feature habría cerrado con
  esos cuatro agujeros dentro.

Causa probable de los falsos muertos: **bytecode rancio**. CPython reutiliza el
`.pyc` cuando el fuente conserva tamaño y mtime truncado a segundos, cosa que
dos mutantes consecutivos cumplen a menudo. Lo arregla la 1.6.0.

### F-035 · el instalador no pisa estado del proyecto — CERRADA (done)

**APPROVED en segunda pasada**, rama `feature/F-035-instalador-no-pisa-estado`.
**El código vive en `arnes-base`** (versión **1.6.2**, commits `1e67231`..
`9e2ced7`), no aquí; esta rama sostiene spec, informe y rastro.

Origen: el 19-ago el instalador pisó en este repositorio `harness/features.json`
(34 features → 1), `docs/ARCHITECTURE.md` (183 → 37 líneas), `progress/
current.md` e `history.md`. Se recuperó porque nada estaba commiteado.

Entregado y verificado: `politica_ficheros.json` con tres categorías, backup
previo con manifiesto, precondiciones con `-IgnorarPrecondiciones`, normalización
de fin de línea, y `tests_instalador/prueba_instalador.ps1` con **47
comprobaciones en verde**, incluido P1 (el incidente: «features.json sobrevive a
`-Modo actualizar -Forzar`»).

**Review: CHANGES_REQUESTED** (`progress/review_F-035.md`). Estado de los CR:

| CR | Qué | Estado |
|---|---|---|
| CR-1 | El mutante que anula el atajo del arnés puro sobrevive a las 47 comprobaciones (R11/R12 sin caso sin `-Forzar`) | **hecho** (`efdfbe7`) |
| CR-2 | El comentario de P4 miente y R15 no lo ejercita nadie | **hecho** (`d64be41`) |
| CR-3 | `Join-Path` fuera del `try` en `New-DirectorioBackup`: traza cruda y `exit 1` en vez de `exit 4` | **hecho** (`d937012`, sube a 1.6.2) |
| CR-4 | C5 documental: tareas, estado, rama, `current.md` | **hecho** (líder, `c86b488` y `b1f7924`) |

**Encargo extra: HECHO** (`9e2ced7`). Portar a `arnes-base` **tres tests de `test_mutacion_operadores.py`** que
solo existen aquí (12 tests en `albaranes`, 9 en `arnes-base`). Son los que
cierran los cuatro huecos de F-034, y se quedaron atrás porque el porte a la
1.6.0 se hizo antes de escribirlos. Sin ellos `arnes-base` lleva `_es_palabra` y
`_delimitado` **sin la red que los protege**. Va en commit APARTE de los CR.

**Verificación MANUAL T16: HECHA por el humano el 20-ago.** Salida:
`Nuevos 0 | Ya iguales 11 | Iguales salvo finales de línea 11 | Actualizados 0 |
Conservados 9 | Protegidos 4`. Los **4 protegidos son exactamente los cuatro
ficheros que el incidente destruyó**. Y los 11 «iguales salvo finales de línea»
son la decisión D4 pagando: once diffs falsos que antes empujaban a pulsar
«Todos».

**Cerrada**: suite del instalador **65 comprobaciones en verde** (eran 47) y
suite Python de `arnes-base` 46 passed (eran 43). Lo que cierra el rechazo no
es ese número sino que **el reviewer volvió a aplicar el mutante MR1 y lo vio
morir**, sobre una copia del scratchpad y comprobando antes que el literal
aparecía exactamente una vez.

**Deuda conocida anotada por el reviewer**, no bloqueante: R20, R26 (constancia
en el manifiesto), R27, R28 y R21/R33 quedan parciales en la suite del
instalador, para cuando vuelva a tocarse.

### F-038 · bajar el coste en tokens del ciclo SDD — CERRADA (done)

**APPROVED en dos pasadas**, rama `feature/F-038-coste-del-ciclo-sdd`. Detalle:
`progress/impl_F-038.md` (218 líneas) y `progress/review_F-038.md` (130).

Entregado: **T0** —`ejecutor_para` acota la suite de la raíz a `tests`, sin lo
cual **no se podía medir mutación sobre `harness/`** y las campañas daban falsos
verdes—, muestreo por nivel de rigor (`estandar` = 20 mutantes, semilla
`20260820`), `nivel_por_defecto` de `critico` a `estandar`, el informe de
mutación imprimiendo **SHA de HEAD, línea base y media por mutante**, la puerta
de tamaño (`harness/tamano.py` + sección 7 quater de `init.sh`), umbral de
reejecución de 5 min a 60 s, revisión incremental por defecto y las seis reglas
RM1–RM6 repartidas entre `reviewer.md` y C4 bis.

**Los topes se recalibraron el mismo día**, antes de cerrar: `120/200/150/100` →
**`150/250/220/140`** (requirements / design / impl / review). Motivo: la mediana
histórica es ~484 líneas en informes de implementer y ~475 en los de review, así
que los originales recortaban un ~70 % y **tanto el implementer como el reviewer
entregaron clavados en el límite** (150/150 y 100/100). Los nuevos recortan un
~55 %: el ahorro se mantiene y queda aire para lo que nadie debe resumir, las
trazas de fase RED y el análisis de supervivientes. Cualquier cita de los
números viejos en documentos anteriores a esa fecha es rastro, no configuración.

**El ahorro ya se cobró dentro de la propia feature**: el reviewer NO reejecutó
la campaña de mutación en ninguna de las dos pasadas. Le bastó leer el SHA y los
tiempos que ahora se imprimen. Y la segunda pasada, siendo incremental, cupo en
30 líneas.

**Hallazgo de T17**: el flaky que se creía ajeno era de esta feature. T5 añadió
al informe la fila de reloj `Media por mutante evaluado (s)` y el test de
paridad serie/paralelo no extendió su filtro; bajo carga la serie redondeaba a
0.0 y la paralela a 0.1. Como la campaña corre con `-x`, **un fallo intermitente
de cualquier test se lee como MUERTO**: ése era el falso muerto de
`mutacion.py:1781`. Arreglado en el test, sin tocar lógica.


## Pendientes del humano

1. ~~`git push` de `arnes-base`~~ **HECHO el 2026-08-20**, junto con el de
   `dev` de `albaranes`. Pendiente de decidir por el humano: si `dev` se lleva a
   `main` y cuándo.
2. **Actualizar los otros cuatro proyectos** (F-035 ya cerró). `partes` está
   en 1.4.0 y se saltaría cuatro versiones: es el escenario donde más ficheros
   aparecen «distintos». Con el instalador nuevo ya no puede pisar estado.
3. **Retirar de la F-010 del otro proyecto** las dos reglas del arnés y apuntar
   a F-038.
4. **Verificaciones MANUAL arrastradas**: las 4 de F-002 (liberan el merge de
   F-003, implementada y aprobada en su rama desde hace días), y las de F-019 y
   F-027.
5. **Reconciliar F-003 y F-004 antes de arrancarlas** (su R4 conserva el cálculo
   que F-019 corrigió).
6. **Histórico mal valorado en BBDD**: sin backfill por diseño; se sanea
   revalorando desde sv4. Falta decidir cuáles.
7. **NADA está desplegado**: producción corre imágenes del 24 de julio, o sea
   **sin F-002, F-019 ni F-027**.
8. **`evals/fixtures/inputs/` vacío**: mientras lo esté, la puerta de rutas
   sensibles se queda en `aviso`.

---

## LO QUE TOCA DINERO, y sigue sin integrar: residuos (F-036)

Informe completo en `progress/revision_residuos_salmedina_20260819.md`. Es lo
único de toda la lista que vale euros, y por eso **debería ir antes que F-038 y
que actualizar los otros proyectos**.

Siete albaranes de SALMEDINA, contrastados contra el Excel del administrativo,
con obra y contrato ya puestos a mano por el humano:

| Albarán | Sistema | Ground truth | |
|---|---|---|---|
| SS-0000168, SS-0003935 | 120,00 € | 120,00 € | correctos |
| SS-0025146 | 136,00 € | 136,00 € | correcto |
| SS-0000589 | 120,00 € | **171,00 €** | falta el incremento LER |
| SS-0026122 | 272,00 € | **260,00 €** | tarifa de 9 m³, y de OFERTA (F-017) |
| SS-0003967 | **540,00 €** | **210,00 €** | ×2,6 |
| SS-0801977 | **720,00 €** | **210,00 €** | ×3,4 |

**Causas, ya diagnosticadas:**

1. **El enrutado del prompt de fase 2 falla**: el SS-0003967 recibió
   `albaran_revision_fase2_es` (genérico) en vez de `..._residuos`. Sin
   `tipo_familia` ni `volumen_m3`, la regla de contenedores ni se invoca y el
   importe sale multiplicado por la capacidad del contenedor.
2. **El scorer del merge de contexto tira los campos de residuos**:
   `contexto_linea_merger._score_contexto()` puntúa **solo cinco campos** —los
   originales del modelo— e ignora `codigo_ler`, `volumen_m3`, `peso_toneladas`,
   `contenedores`, `contenedores_entregados`, `contenedores_retirados`,
   `carga_incompleta` y `exceso_declarado_min`. Un contexto que solo traiga
   datos de residuos puntúa **0 y se descarta entero**. Es la explicación más
   plausible del SS-0801977 (falta confirmarla en BBDD).
3. **Los incrementos por LER no se emiten nunca**, aunque están cargados en
   `contrato_lines`.
4. **Efecto perverso**: en el SS-0003967 el matcher eligió como línea principal
   el propio INCREMENTO LER (match exacto por el código LER en su descripción)
   en vez del contenedor.

**DECISIÓN DEL HUMANO, 2026-08-19, pendiente de implementar**: en
`calcular_contenedores_residuos`, **el volumen manda sobre la resta
entrada/salida**. Orden nuevo: (1) contenedores explícitos, (2)
`ceil(volumen_m3 / tamaño)`, (3) resta entregados − retirados. Hoy la resta es
la 2 y el volumen la 3. Hay que tocar `residuos_container_calc.py` (y su
docstring), el prompt de sv5 (`config/prompts.yaml` ~1024, que documenta el
orden viejo) y los tests de la prioridad 2. **Asunción por confirmar**: los
contenedores explícitos siguen siendo prioridad 1.

**Lo que sí está bien**: la regla de contenedores existe y es correcta —lee el
tamaño del contrato (6 por defecto, admite 8), redondea al entero superior—, y
IA2 extrae `volumen_m3` y `peso_toneladas` bien en 6 de 7. Ojo con **F-024**: al
extraer `unidad_medida`, los casos que hoy aciertan pueden pasar a valorar ×6.

**Sin trazabilidad**: las razones de `calcular_contenedores_residuos` no se ven
en sv4. El revisor no puede saber si la regla se aplicó ni con qué tamaño; los
720 € malos se le presentan igual que los 120 € buenos. Y los motivos de
revisión **no se recalculan**: el SS-0801977 sigue mostrando
`proveedor_cif_no_casa` con el CIF viejo después de corregirlo.

Altas relacionadas: **F-036** (los dos defectos, rigor `critico`), **F-037**
(guardado inmediato al seleccionar contrato, pedido por el humano).

---

## Notas operativas (valen para cualquier sesión)

- **Nada en paralelo**: dos suites a la vez tumban el proceso en Windows
  (`0xC0000142`). Y **una campaña de mutación muta el árbol principal**: mientras
  corra, no lanzar `init.sh` ni tests. Desde la 1.6.0 hay centinela que lo avisa.
- **Un agente que se cuelga no pierde el trabajo commiteado.** Esta sesión tuvo
  tres cuelgues (dos de watchdog, uno `ECONNRESET`) y en los tres bastó
  reanudar. Ayuda que commiteen por tarea.
- **Un agente con demasiado contexto se cuelga en bucle**: el reviewer de F-034
  murió dos veces seguidas sin escribir nada. Lanzar uno **nuevo y acotado**
  —diciéndole exactamente qué leer— lo resolvió y costó 101k en vez de 173k.
- **No ensuciar el árbol mientras un reviewer trabaja**: C5 exige árbol limpio.
  Pasó dos veces esta sesión, y una costó una pasada entera.
- **Los agentes no deben usar scripts que reescriban ficheros versionados**;
  copias en el scratchpad. Un artefacto de finales de línea provocó un cuelgue.
- **Cuidado con las rutas de Windows en heredocs de Python**: `\U` de
  `C:\Users` se interpreta como escape unicode y mata el script.

## F-038 · lo que queda después del cierre

1. **Porte a `arnes-base` como 1.7.0: HECHO** el 2026-08-20, informe en
   `progress/impl_F-038_porte_1.7.0.md`. Seis commits locales, suite del destino
   **134 passed** (eran 47 con 1 fallo previo), prueba del instalador **65
   comprobaciones en verde**, y `ruff` igual antes y después (40 avisos). No fue
   copiar: de los 19 hunks de `mutacion.py`, 19 aplicaron, y el único rechazo
   fue en `CHECKPOINTS.md`, justo donde la 1.6.3 había escrito. **Ahí había una
   contradicción real** —la 1.6.3 declara sospechoso un coste «muy por debajo
   del tiempo de la suite» y RM2 dice que con `-x` eso es normal—, resuelta
   dejando a la 1.6.3 la señal dura (por debajo de un segundo, síntoma del
   bytecode envenenado) y delegando en RM2 el resto; a cambio RM2 gana el matiz
   de que en campaña paralela «Tiempo total» es tiempo de reloj y hay que
   multiplicarlo por los workers. **Pendiente de la revisión del humano**
   (verificación MANUAL de P1) y de `git push`, que no hacen los agentes.
2. **`progress/mutacion_F-011.md` se queda INVALIDADA — decidido por el humano
   el 2026-08-20.** Todo su alcance (`evals/**`, `harness/rutas_sensibles.py`)
   cae fuera de `services/`, así que sus **305 mutantes y 133 supervivientes**
   se midieron con la invocación rota. Es la campaña más cara del repositorio y
   **no se va a repetir**: se queda con la cabecera «CAMPAÑA NO VÁLIDA» y sin
   ficha. Consecuencia que hay que tener presente: **la puerta de evals de F-011
   no tiene hoy ninguna medición de mutación válida que la respalde**; si alguna
   vez se toca ese código, la campaña se hace entonces y desde cero. No se cita
   ese informe como evidencia de nada. `mutacion_F-034.md` NO se marcó: ya está
   remedido a mano con la ruta acotada y lo dice en su cabecera.
3. **Deuda menor heredada por F-039** (observación 1 del reviewer): el filtro de
   filas de reloj del test de paridad es una lista de prefijos escrita a mano, y
   la cuarta fila de reloj que se añada volverá a romperlo. Propuesta: derivarlo
   de una constante junto a `escribir_informe`.
4. **RM2 solo dispara a 10×** y, con «Tiempo total» > 60 s, tampoco se reejecuta:
   un informe «solo» cinco veces demasiado rápido pasaría. Aire deliberado, pero
   queda dicho.

---

## F-039 · estabilizar la suite y medir la maquinaria de HOY — CERRADA (done)

**APPROVED en segunda pasada** (CHANGES_REQUESTED en la primera, dos CR).
Detalle: `progress/impl_F-039.md` (220), `progress/review_F-039.md` (140),
`progress/mutacion_maquinaria_paralela_F-039.md` (233) y
`progress/inventario_mutacion_F-039.md`.

**Decisión del humano que cambió el diseño**: NO se remidió el árbol de agosto
de F-012. `mutacion.py` había crecido +1.346 líneas desde entonces, así que
aquella medición habría sido arqueología. Se midió **la maquinaria tal como es
hoy** —`mutacion.py`, `mutacion_paralela.py` y `rigor.py` enteros, 2.742
líneas—: 417 mutantes generados, 20 muestreados (`estandar`, semilla
`20260820`), **13 muertos y 7 supervivientes**. Los siete están en el código que
corre, no en el de agosto.

**Entregado**: `FILAS_DE_RELOJ` + `lineas_comparables()` —con la guarda R5, que
hace **fallar el test** si alguien añade una fila de reloj sin declararla, para
que el flake de F-038 T5 no se repita—, el flag `--ficheros` con
`alcance_de_ficheros()`, el inventario de las 13 campañas con su portero, y las
cabeceras de invalidez de `mutacion_F-011.md` y `mutacion_F-012.md`.

**Los dos CR del reviewer, ambos reales**:

- **CR-1**: R18 se quedó sin test. Quien repitiera la campaña habría borrado en
  silencio la cabecera manual —el comando de reproducción y el aviso de que mide
  otro código—, porque `escribir_informe` conserva los análisis pero no la
  cabecera.
- **CR-2**: la guarda de alcance vacío **era inalcanzable desde el CLI**.
  `--ficheros ","` terminaba en **exit 0 escribiendo un informe de 0 mutantes**:
  una campaña que no mide nada, reportada como éxito. Es el mismo falso verde
  que persiguen F-038 y esta feature, entrando por una puerta nueva. Hoy sale
  con código 2 y sin escribir informe, verificado también con `",,,"` y `" "`.

**Verificación final**: `init.sh` exit 0, **420 passed**, cobertura **100 %**
(32/32). La campaña de la feature se reejecutó tras CR-2 porque el alcance
cambió (134 → 140 líneas): 13 mutantes, **13 muertos, 0 supervivientes**.

**Cómo se revisó, que es parte del valor**: el reviewer no reejecutó ninguna
campaña —838 s y 482 s, muy por encima del umbral de 60 s—. Reprodujo el
muestreo con la semilla, comprobó los 7 supervivientes uno a uno, reejecutó los
33 mutantes **sobre copia en el scratchpad** (veredictos idénticos) y degradó la
cabecera **cinco veces** para comprobar que el test de CR-1 muerde. Eso es la
tercera vía de RM4 funcionando.

### 1. Verificaciones MANUAL que quedan para el humano (T5, T6)

La campaña **paralela** sigue sin verificar: `--workers 5` lanza cinco suites
simultáneas y en esta máquina dos ya tumban el proceso (`0xC0000142`). El
comando exacto, el criterio de verde y el descenso 5 → 3 → 2 están preparados
para copiar y pegar en **`progress/verificacion_paralela_F-039.md`**, con su
tabla de resultados esperando la salida real.

Esto **no bloquea** la campaña del bloque D: se midió en serie (`--workers 1`),
que es como se ha medido siempre en este repositorio.

### 2. Huecos de test detectados — la lista es para decidir, no está abierta

R20: **no se ha abierto ficha y no se ha tocado `harness/features.json`**. Son
**6 huecos reales** de la campaña sobre la maquinaria de mutación de hoy
(7 supervivientes, de los que 1 es equivalente justificado). Agrupados por
causa, con el análisis completo de cada uno en
`progress/mutacion_maquinaria_paralela_F-039.md`:

| Grupo | Qué no se prueba | Supervivientes | Gravedad |
|---|---|---|---|
| **A · El CLI de `harness.mutacion` no se ejercita de punta a punta** | `main` con un centinela sucio en disco (arrancaría la campaña **encima del mutante viejo**) y el código de salida de `--restaurar` | `mutacion.py:1807`, `mutacion.py:1688` | **Alta** el primero: mediría un mutante y lo llamaría «el código» |
| **B · El informe solo se escribe por su camino feliz** | La sección `## Timeouts` (y con ella la de `base_rota`), y el mensaje de `_base_rota_al_final`, que **no tiene ni un test** | `mutacion.py:1539`, `mutacion.py:1282` | Media: `lineas -= [...]` es un `TypeError` en cuanto hay un timeout |
| **D · Las validaciones de `rigor.py` comprueban el tipo, no el rango** | Un `timeout_por_mutante_s` entero pero `<= 0` pasa la validación; con `timeout=0` **toda** la campaña sale «timeout» | `rigor.py:118` | Media |
| **E · La limpieza de worktrees solo se prueba cuando `git worktree remove` funciona** | El respaldo `rmtree` + `prune` para cuando la retirada falla (el caso Windows para el que existe) | `mutacion_paralela.py:257` | Baja |

(El grupo C es el único **mutante equivalente**: `mutacion.py:1348`, en
`analisis_escritos`. No hay test que escribir; la justificación está escrita.)

**Decide el humano**: si se abre trabajo, con qué prioridad y qué grupos
entran. Los cuatro grupos caben en un solo fichero de tests nuevo.

### 3. Hallazgo del arnés que NO se ha tocado (para decidir también)

`_base_rota_al_final` (`harness/mutacion.py:1274`) **no distingue una línea
base que EXPIRA de una que falla**. Con `expirado=True` el código es `-1` y el
informe estampa «La línea base estaba VERDE al empezar y **ROJA** al terminar
(código -1)», que manda a buscar un test caído que no existe.
`comprobar_linea_base` sí lo distingue, y su mensaje —«LÍNEA BASE SIN TERMINAR
… agotó los N s de timeout»— es el que hacía falta.

**Pasó de verdad hoy**: dos pasadas de la campaña de T11 se invalidaron así
mientras la suite estaba **verde** (409 passed) pero tres veces más lenta. No
se arregla aquí por dos motivos: excede los requisitos de F-039, y `mutacion.py`
es justo el código que esta feature está midiendo. Es genérico del arnés, así
que si se abre, se abre para `arnes-base` también.

### 3 bis. TERCER falso verde de la misma familia, hallado el 2026-08-21

**Una campaña con alcance vacío por la vía `--feature` sale con código 0 y
escribe su informe.** Lo destapó el humano al ejecutar la verificación T5:

```
F-038: 0 fichero(s), 0 línea(s) de producción (origen rama, ef5808c..feature/F-038-...)
Sin líneas de producción en el alcance: nada que mutar.
0 mutantes evaluados, 0 muertos, 0 supervivientes ... en 0.0 s
Informe: ...erificacion_paralela_F-039.md
```

Causa inmediata: F-038 ya está mergeada en `dev`, así que el diff de su rama
contra el merge-base es vacío y el comando preparado en
`verificacion_paralela_F-039.md` **caducó al mergear**. Ese comando era correcto
cuando se escribió.

Pero lo que importa es lo otro: **es el mismo defecto que el CR-2 de F-039**
—`--ficheros ","` salía con exit 0 y un informe de 0 mutantes—, por una vía que
nadie tapó. Van **tres veces hoy** el mismo modo de fallo: la invocación sin
ruta (F-038 T0), el flake de las filas de reloj (F-038 T17) y la guarda
inalcanzable (F-039 CR-2). Todos dicen «todo bien» sin haber juzgado nada.

Propuesta, pendiente de que el humano decida: que una campaña con **cero
mutantes generados** aborte con código distinto de 0 y **sin escribir informe**,
igual que hace hoy `--ficheros` tras CR-2. `CHECKPOINTS.md` ya manda mirar con
lupa las campañas de cero mutantes; hoy la herramienta no ayuda a verlo.

**Consecuencia inmediata**: la verificación T5/T6 del paralelo **sigue
pendiente**. Comando que sí la ejercita, con alcance explícito:
`python -m harness.mutacion --feature F-039 --ficheros harness/rigor.py --workers 5 --max-mutantes 1 --salida "$env:TEMPerificacion_paralela_F-039.md"`.

### 3 ter. Primera ejecución real del paralelo (2026-08-21) — lo verificado y lo que falla

`--feature F-039 --ficheros harness/rigor.py --workers 5 --max-mutantes 1`:

**Verificado (R9 parcial, R12 completo):**

- **El paralelo arranca**: `[base] .: en verde (97.5 s)` — la línea base se
  ejecutó DENTRO del worktree y pasó. **Sin `0xC0000142`**: la máquina aguanta
  el montaje paralelo.
- **R12 se cumple incluso con la campaña inválida**: `git status --porcelain`
  vacío y `git worktree list` con una sola línea. La limpieza funciona por el
  camino malo, que es donde importa.
- **Falta lo esencial de R9**: con `--max-mutantes 1` solo se usó UN worker. Los
  cinco simultáneos siguen sin probarse. Hacen falta ≥ N mutantes para ejercitar
  N worktrees.

**Defecto A · el timeout de 120 s no sirve en campaña paralela.** La suite tarda
~51 s en reposo y **97,5 s solo por el arranque paralelo**; el
`timeout_por_mutante_s` de `rigor.json` es 120. Expiraron el mutante y la línea
base de cierre (97,5 + 120 + 120 ≈ 337,7 s de total). **Propuesta**: que el
timeout efectivo escale con el número de workers, igual que la 1.6.3 hizo con el
coste por mutante de `CHECKPOINTS.md` (`f1b250e`). Hoy el arnés reconoce el
factor de workers al JUZGAR el coste, pero no al CONCEDER el tiempo.

**Defecto B · `_base_rota_al_final` mintió en su primera ejecución real.** El
mensaje fue: «La base se rompió durante la campaña… **Arregla la suite y repite
la campaña**». La suite estaba impecable: la línea base **expiró** (código -1),
no falló. Es el hallazgo §3 de F-039, y deja de ser teórico: **mandó al humano a
arreglar algo que no estaba roto**. Sube de prioridad.

### 4. Aviso de convivencia (costó ~40 minutos de máquina)

Mientras corría la campaña de F-039, otra sesión lanzó **campañas de mutación
en paralelo de `datamart-seg-anual`** en esta misma máquina (21:49 y 22:06).
Una campaña de mutación necesita la máquina **para ella sola**: la de aquí pasó
de 51 s a 149 s de línea base y el arnés invalidó sus propios números, con
razón. **Dos campañas de mutación a la vez, en cualquier par de proyectos, se
estropean mutuamente.**

---

## F-040 · spec escrita (2026-08-21, spec-author)

`specs/F-040-campana-dimensionada-y-honesta/` — requirements (114/150), design
(176/250), tasks (26 tareas + 1 posterior al merge). Rama
`feature/F-040-campana-dimensionada-y-honesta`. Nada implementado.

**Decisión de diseño de D1**: el timeout por mutante NO se multiplica por los
workers (el dato de campo lo desmiente: de 1 a 3 workers la suite crece un 25 %,
no un 300 %) ni se mide la suite aparte (cuesta una suite extra y mediría en
reposo). Se **deriva de la línea base que la campaña ya corre dentro de cada
worktree**, que ya incluye la contención real: `max(suelo, ceil(peor_base × 2))`.
La línea base recibe su propio timeout holgado, `suelo × 5`, porque se paga una
vez por worker y no una por mutante. `rigor.json` no gana ningún número de esta
máquina: cambia el mecanismo. **D2**: `TOPE_WORKERS` 16 → 4 y
`min(max(1, (núcleos-2)//2), 4)`. **D4**: guarda única en `main` (embudo), no una
cuarta guarda en `alcance.py`; código de salida 3, sin informe.

**Dos premisas de la ficha resultaron falsas al comprobarlas** (sección 0 del
design): la sección `## Timeouts` NO lanza `TypeError` —solo duplica
`fichero:linea`—, y `timeout_mutacion` SÍ rechaza enteros `<= 0`; lo que se cuela
es un **booleano** (`true` → 1 s) y un `--timeout` negativo sin validar. Tampoco
`CHECKPOINTS.md` reconocía el factor de workers: no aparece ni «worker» ni
«paralel». De ahí sale R27.

### Necesita validación del humano (4 preguntas abiertas en requirements.md)

1. ¿`MARGEN = 2` y `FACTOR_HOLGURA_BASE = 5` en el código, o declarados en
   `rigor.json`?
2. Con el timeout ya derivado, ¿sigue en pie no declarar `mutacion.workers`?
3. ¿`TOPE_WORKERS = 4` o 3, el único punto con medición real en verde?
4. R23 cambia el significado de `--timeout 0` (hoy cae en silencio al
   configurado) y pasa a salir con código 2. ¿Se acepta?

**Riesgo anotado en el design**: si al implementar aparece un **quinto** defecto
de esta maquinaria, se anota en `progress/impl_F-040.md` y se propone al humano;
no entra en F-040 sin preguntar. El porte a `arnes-base` 1.7.2 va **después** del
merge en `dev`, nunca dentro de la rama.
