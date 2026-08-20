<!-- progress/current.md -->
# Trabajo en curso

## Cierre de sesión — 2026-08-20 (sesión del 19 y 20 de agosto)

Sesión larga y casi entera dedicada al **arnés**. Se cierra a propósito para
liberar contexto: lo que queda es trabajo largo y conviene retomarlo limpio.

### Lo primero al abrir la próxima sesión

1. **`git push` de `arnes-base`**: los commits locales de la 1.6.1 en adelante
   —más los de la 1.7.0 cuando se porte F-038— son lo único que impide que todo
   el trabajo del arnés exista fuera de un solo disco.
2. Por orden: **F-036 (residuos, lo único que toca dinero)** → **F-039 (subida
   a prioridad 2: sin una suite estable, ninguna medición del arnés vale)** →
   actualizar los otros cuatro proyectos con el instalador ya seguro.
3. **Decidir qué se hace con `progress/mutacion_F-011.md`** (ver «F-038 · lo que
   queda después del cierre», punto 2).

---

## Estado del arnés

| Repositorio | Versión | Estado |
|---|---|---|
| `arnes-base` | **1.7.0** | F-038 portada e integrada sobre la 1.6.3 (6 commits). **8 commits locales sin subir** (los 2 de la 1.6.3 + los 6 de la 1.7.0) |
| `albaranes` | **1.6.1** sellado, pero con **el código de F-038 dentro** | El sello y el código YA NO COINCIDEN: F-038 se desarrolló aquí y se portó allí, pero **la 1.6.2 y la 1.6.3 nunca llegaron a este repositorio**. En particular **le falta el arreglo del bytecode envenenado**, que es lo que provocaba mutantes «muertos» falsos. Se arregla actualizándolo con el instalador |
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

1. **`git push` de `arnes-base`**: todo lo posterior a la 1.6.0 sigue sin subir.
   Sin push, ese trabajo existe en un solo disco.
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
