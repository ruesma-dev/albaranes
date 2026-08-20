<!-- progress/current.md -->
# Trabajo en curso

## Cierre de sesión — 2026-08-20 (sesión del 19 y 20 de agosto)

Sesión larga y casi entera dedicada al **arnés**. Se cierra a propósito para
liberar contexto: lo que queda es trabajo largo y conviene retomarlo limpio.

### Lo primero al abrir la próxima sesión

1. **`git push` de `arnes-base`**: 16 commits locales. Es lo único que impide
   que todo el trabajo del arnés exista fuera de un solo disco.
2. Por orden: **F-036 (residuos, lo único que toca dinero)** → **F-038** →
   actualizar los otros cuatro proyectos con el instalador ya seguro.

---

## Estado del arnés

| Repositorio | Versión | Estado |
|---|---|---|
| `arnes-base` | **1.6.2** | 1.6.0 pusheada; de la 1.6.1 en adelante, **16 commits locales SIN SUBIR** |
| `albaranes` | **1.6.1** | código y sello coinciden, mergeado en `dev` |
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

### F-038 · bajar el coste en tokens del ciclo SDD — `pending`, SIN SPEC

Prioridad 3. Medición que la motiva: los subagentes de esta sesión gastaron
**~712.000 tokens** y `progress/` acumula 12.250 líneas. **La campaña de
mutación NO gasta tokens** (es Python y pytest: gasta CPU); el coste está en el
papeleo y en las repeticiones. Cada línea de spec se paga TRES veces: la escribe
el spec-author, la lee el implementer, la relee el reviewer.

Alcance aprobado por el humano, **cuatro palancas**:

1. **Topes de tamaño**: `requirements.md` ≤ 120 líneas, `design.md` ≤ 200,
   informe de implementer ≤ 150, review ≤ 100. La de más ahorro (40-50 %).
2. **Coste de mutación por nivel** en `harness/rigor.json`: `nivel_por_defecto`
   de `critico` a `estandar`, y `max_mutantes` por nivel (20 con semilla fija en
   estándar, sin tope en crítico). `mutacion.py` ya acepta `--max-mutantes` y
   `--semilla`: falta leerlos del nivel.
3. **Umbral de reejecución del reviewer** de 5 min a **60 s**.
4. **Reviewer incremental** por defecto: en la pasada N, solo
   `git diff <último-aprobado>..HEAD`, y decirlo en el informe.

**FUERA por decisión expresa**: modelo por rol (el humano quiere **Opus 5
siempre**). Fuera también, para otro trabajo: informes por delta, y la regla de
fijar en un test el número de aceptación antes de implementar.

**Además, PENDIENTE DE AÑADIR A LA FICHA** (acordado con el humano, no escrito
todavía en `features.json`): **seis reglas** que salen de los reviews de esta
sesión. Cuatro del reviewer de F-034 y dos de otra sesión:

| # | Regla | Efecto en tokens |
|---|---|---|
| 1 | El informe de mutación declara el **SHA de HEAD** contra el que se midió, y el reviewer comprueba que el alcance coincide | **ahorra mucho** (habría evitado el 1er rechazo de F-034, ~200k) |
| 2 | **Coherencia interna del tiempo**: si `tiempo/mutantes` es mucho menor que lo que tarda la suite, se rechaza el informe | **ahorra mucho** (habría cazado el 2º, ~350k) |
| 3 | Un mutante **equivalente no puede salir muerto**; un solo caso invalida la campaña. Como criterio de revisión, no puerta automática | ahorra |
| 4 | Tercera vía de verificación: **reejecutar contra el subconjunto de tests** del módulo mutado, en copia del scratchpad (568 s en vez de 18 min, y no muta el árbol) | ahorra |
| 5 | Un superviviente declarado «equivalente» trae **demostración ejecutable**; el reviewer **reproduce una muestra**, no todas | ⚠ la única que aumenta: **adoptarla ACOTADA** |
| 6 | Quitar código defensivo para matar un mutante obliga a **verificar el invariante en quien construye el dato** | neutra, y muy oportuna |

La 6 es especialmente pertinente ahora: con F-034, el mutador ataca las guardas
`x is None`, y la salida fácil es **borrar la guarda**. Sin esa regla, F-034
empuja a quitar justo las defensas que evitaron F-019 y F-027.

**Aviso de coordinación**: las reglas 5 y 6 salieron de otra sesión, que las
apuntó en **su** F-010 (que en `albaranes` es otra feature distinta: Easy Auth).
Deben viajar por una sola vía o divergirán, que es lo que pasó cuando
`arnes-base` era una carpeta suelta.

**Sugerencia al arrancar**: que F-038 **cumpla sus propios topes** de tamaño.

---

## Pendientes del humano

1. **`git push` de `arnes-base`**: 14 commits locales (todo lo posterior a la
   1.6.0). Sin push, ese trabajo existe en un solo disco.
2. **Actualizar los otros cuatro proyectos** cuando F-035 cierre. `partes` está
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

## F-038 · spec escrita (spec-author, 2026-08-20)

Escrita `specs/F-038-coste-del-ciclo-sdd/` (requirements 118 líneas, design
162, tasks 15 tareas + 1 posterior al merge). La spec cumple los topes que la
propia feature establece.

Decisiones tomadas en el design: D1 `ejecutor_para` con ruta `tests` en vez de
`testpaths` en la raíz; D3 los topes de tamaño NO son retroactivos (la puerta
mide solo la feature en curso, las 12 specs viejas quedan amnistiadas); D4
ninguna de las seis reglas de mutación es puerta automática de `init.sh` (RM1,
RM2, RM5 y RM6 pasan a checkbox de C4 bis; RM3 y RM4 a criterio del reviewer);
D5 remedir F-012 NO entra, solo se estampa el aviso de invalidez; D6 el porte a
`arnes-base` 1.7.0 va después del merge en `dev`.

Las tres preguntas abiertas las **respondió el humano el 2026-08-20** y están
escritas en `requirements.md` («Decisiones del humano»): semilla `20260820`
fija; remedir F-012 NO entra aquí (se abre como **F-039**); y
`nivel_por_defecto: estandar` se acepta sin revisar fichas, porque las 38
features del backlog ya declaran rigor (30 `estandar`, 8 `critico`).

## F-038 · implementada (implementer, 2026-08-20)

T0–T14 hechas, un commit por tarea en `feature/F-038-coste-del-ciclo-sdd`.
Detalle, trazas de fase RED y evidencias: **`progress/impl_F-038.md`**.
Pendiente el APPROVED del reviewer; la feature sigue `in_progress`.

Lo que queda declarado como deuda, fuera de esta rama:

1. **F-039 — remedir `progress/mutacion_F-012.md`.** Sus 61 mutantes se
   midieron con la invocación rota; el informe ya lleva la cabecera «CAMPAÑA NO
   VÁLIDA» (T11) para que nadie los cite como evidencia. Con T0 hecho, esa
   campaña ya se puede ejecutar.
2. **`progress/mutacion_F-011.md` lleva la misma cabecera** y **no** tiene
   ficha de remedición: todo su alcance (`evals/**`, `harness/rutas_sensibles.py`)
   cae fuera de `services/`. Son 305 mutantes y 133 supervivientes, la campaña
   más cara del repositorio: decide el humano si se abre otra F-0XX o se deja
   invalidada. `progress/mutacion_F-034.md` NO se marcó: ya está remedido a
   mano con la ruta acotada y lo documenta en su cabecera.
3. **Porte a `arnes-base` como 1.7.0** (P1 de `tasks.md`): va **después** del
   merge en `dev`, nunca dentro de esta rama. Su entrada en
   `GUIA_INSTALACION.md` debe avisar de que `nivel_por_defecto` pasa a
   `estandar` y de que las campañas de ese nivel quedan **muestreadas a 20
   mutantes**: sus números no son comparables con los de versiones anteriores.
