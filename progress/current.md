<!-- progress/current.md -->
# Trabajo en curso

> Podado el 2026-08-26. El relato de la sesión del 25-26 de agosto —los cuatro
> bloques de F-036, sus dos ciclos de review y los hallazgos— está en
> `progress/history.md`. Aquí solo queda lo vivo.

## LO PRIMERO AL ABRIR LA PRÓXIMA SESIÓN

**F-045 · CAPA 1 IMPLEMENTADA** (2026-09-16, rama
`feature/F-045-banco-evals-revision-manual`, 22 commits de tarea). Informe
completo en `progress/impl_F-045.md`, importación en
`progress/import_F-045.md`, mutación en `progress/mutacion_F-045.md`. El banco
pasa de **7 casos** a **59**, de ocho familias y 18 proveedores; 811 tests en
verde, 98,3 % de cobertura de lo cambiado y campaña de mutación completa con
sus 90 supervivientes analizados (**74 con test nuevo, 16 equivalentes**).

**Pasada 1 del review: CHANGES_REQUESTED, ya corregido** (`review_F-045.md`).
Los dos bloqueantes eran justificaciones de equivalencia FALSAS —`sort_keys`
del mapa y la copia de seguridad de R16— y se cierran con test, no con prosa;
los cinco menores también.

**Pasada con LLM del 2026-09-16** (`evals_F-045.md`): ROJO, pero 1295 de los
1456 fallos eran «obtenido None», o sea ruido del banco. **T13 entró** (no
estaba en la capa 1): IA1 e IA2 se comparan ya solo por lo que la corrida VE, y
eso quita 266 fallos de ruido —`caso_id`, `fichero_albaran`, `unidad`,
`descuentos`— y deja los 86 defectos de verdad a la vista. **IA3, IA4 y el E2E
no miden nada** hasta que se decida de dónde salen las líneas de contrato: las
tres vías, medidas, en `progress/impl_F-045_contrato_lineas.md` (recomendada la
B, por `sigrid-api`). Otra pasada con LLM la decide el humano.

**Las dos decisiones del humano, cerradas el 2026-09-16**: la tipología va por
PESTAÑA —y **§3 queda corregida**, era la spec la que estaba mal— y el
incremento por LER **se deduce del contrato**, así que el material impreso va a
IA1 y el incremento a las sintéticas de IA3: son dos líneas, una por fase, y el
ground truth contradictorio de RES-004 desaparece.

**Pasada 2 del review: RECHAZADA y corregida.** La pérdida de datos era de 38
valores afirmados, no de 3: restaurados los 35 que faltaban desde `5132bdc`,
arreglado el método que solo vio tres —ahora la comparación recorre todos los
fixtures campo a campo— y puesto un guardián versionado
(`tests/datos/afirmado_por_el_humano_RES.json`, 496 valores) que falla nombrando
cada pérdida. Y la campaña de mutación del lote: 44 mutantes, 35 muertos, **los
9 supervivientes cerrados con test**.

Libros, mapa y **fixtures ya regenerados** (se esperó a que terminara la pasada
de evals que los estaba leyendo). Repetir importador + conversor no deja ni un
cambio.

Siguen abiertas dos decisiones que no bloquean: `codigo_imputacion` (que sale
`?` en las 114 líneas) y de dónde salen las líneas de contrato para que IA3,
IA4 y el E2E midan algo.

Falta la pasada 2 del reviewer: la feature sigue `in_progress` y NO se marca
`done`.

**Tres cosas que tiene que decidir el humano antes de cerrar:**

1. **`INPUTS.CASOS.tipologia`**: la implementación escribe la **pestaña**, no
   la familia de documento que pide `design.md` §3. Motivo medido:
   `MAPA_TIPO_FAMILIA` de `evals/procesos/{sv5_valoracion,sv6_build}.py` está
   indexado por pestaña, así que escribir la familia deja a TODOS los casos
   —incluidos los 7 RES que ya funcionaban— en `tipo_familia='otro'`, que es
   justo la clasificación equivocada que F-043 vino a arreglar; y esos dos
   ficheros §2 los declara intocables en F-045. La familia no se pierde: va a
   `evals/mapa_casos.json` y agrupada en el informe.
2. **Los incrementos LER de los 7 casos RES**: el Excel los marca
   `EN ALBARAN`, pero el libro escrito a mano los tenía como sintéticas
   esperadas. Hoy RES-004 los espera por los dos caminos a la vez, y eso es
   ground truth contradictorio. Hay que mirar el papel.
3. **Los originales siguen sin copiarse**: los 59 casos salen como
   `fila_sin_fichero`. El plan de renombrado se propone en el informe con la
   estrategia de cada emparejado, y **no se ha renombrado nada**: hay que
   pedirlo con `python -m evals.revision --renombrar` tras revisarlo.

**F-043 y F-036 están CERRADAS** (`done`, 2026-09-14). El relato completo, con
las cuatro verificaciones, los tres defectos que solo salieron probando en real
y las salvedades, está en `progress/history.md`.

**Lo siguiente es F-045** (prioridad 2, `pending`): llevar al banco de evals los
**32 albaranes** que el humano revisó uno a uno, con sus comentarios de defecto,
desde `evals_summary.xlsx` (carpeta `evals` de OneDrive). **El Excel sigue
creciendo**: a 2026-09-14 faltaban por valorar los últimos de hormigón y
residuos, así que se siembra lo cerrado y el resto entra después.

### Spec de F-045 escrita (2026-09-15)

`specs/F-045-banco-evals-revision-manual/` con los tres ficheros (requirements
150/150, design 186/250). Propone un importador nuevo, `evals/revision/`, que
traduce la tabla PLANA de la revisión a los seis libros de `ground_truth/` y
deja `evals/conversor.py` como única puerta a los fixtures. La tabla de reparto
columna a columna es `design.md` §3 y es normativa. Medido el 2026-09-15 sobre
el Excel del humano: 142 filas con datos, 59 códigos de albarán, 10 etiquetas de
familia, 35 filas con comentario de defecto (había crecido desde las ~110).

**Decisiones abiertas que necesita validar el humano antes de implementar:**

1. **La tabla de reparto de `design.md` §3**, y en particular la separación
   extracción/valoración que pediste: lo que el albarán imprime va a IA1/IA2, lo
   que el sistema decide (partida final, precio de contrato o de oferta,
   contrato elegido, obra deducida) va a IA3/IA4 y a `RESULTADO_FINAL`.
2. **D3 · CORREGIDA por el humano el 2026-09-15.** La versión anterior («toda
   celda vacía → `?`») era errónea, y la marca de «validada» que llevaba
   también: un **comentario** vacío significa que eso salió BIEN y hay que
   seguir comprobándolo en cada pasada, así que esos casos se comparan y hoy
   deben salir en VERDE (son los de no regresión: 107 de 142 filas, y 36 de los
   59 albaranes no tienen ni un comentario). El `?` solo lo produce un **valor
   esperado** ausente, y ni siempre: `descuento` vacío = sin descuento y `LER`
   vacío = no aplica a esa familia. Con esa lectura la ceguera real del banco
   son ~10 celdas, no las 107 filas. Está en `design.md` §5 y D3.
3. **D1 · el mapa de familias**: `CONTENEDORES`→`residuos` y
   `CAMION GRUA`→`alquiler_maquinaria` son interpretación nuestra de tus
   etiquetas. Van en fichero de datos para cambiarlas sin tocar código.
4. **D4 · `numero_albaran` y la obra de IA1 quedan sin vigilar** (patrones 9 y
   la mitad de extracción del 2): tu columna `codigo alabran` es la clave del
   documento, no el literal impreso (`0000168` frente a `SS-0000168`).
5. **D6 · el campo `servicios` de la ficha**: F-045 no toca sv2/sv5/sv6, solo
   los vigila.

**Añadido el 2026-09-15 · parte de los originales son PNG, a propósito** («asi
medimos tambien en otro formato»). La spec lo recoge en `design.md` §4 bis: son
TRES caminos de lectura, no dos —PDF con texto, PDF escaneado (JPEG por página)
e imagen suelta realzada por `preparar_imagen_para_ia`, rama de sv2 de julio de
2026 que hoy no mide nadie—, y un fallo que solo sale en el tercero es
información sobre el FORMATO, no un defecto de extracción. Tres consecuencias:
el mismo albarán en PDF y en PNG son DOS casos con el mismo ground truth
(`HOR-012` y `HOR-012-IMG`, hermanados por `gemelo_de`) y no se deduplican; el
formato NO se escribe en ningún libro, se mide en la corrida y el informe agrupa
por él; y **hay un agujero que cerrar en `.gitignore`**, que ignora `*.pdf` pero
no `*.png`, así que hoy un original de proveedor en PNG entraría en git.

**Añadido el 2026-09-15 · el convenio de nombres** que cierra la capa 1: el
código de albarán va al final del nombre del fichero, después del último `_`, o
es el nombre entero si no hay `_` (`PROVEEDOR_SS-0003967.pdf` y
`SS-0003967.png` → `SS-0003967`). Ese es el puente **nombre de fichero → código
del Excel → `caso_id`**, y sin él emparejar 59 albaranes con sus ~142 filas es
trabajo manual. Queda en `design.md` §4 y en R20–R22, con tres cosas: el
renombrado es un script reproducible (T11), no un `mv`; los cuatro casos que la
regla no cubre (dos ficheros al mismo código, código sin fila, fila sin fichero,
nombre vacío) salen listados uno a uno en el informe; y **manda el código del
papel, nunca el persistido** — el precedente es `SS-0801977` leído donde el
papel decía `SS-0001977`.

**Añadido el 2026-09-15 · residuos y el lío de las familias** (`design.md` §5
bis y §5 ter). Los tres criterios de residuos que dio el humano están
**verificados contra el código y NINGUNO existe hoy**: el canon por LER es el
enganche que `residuos_incrementos.py` deja para F-006 (`spec_ready`); el
mínimo facturable de 1 tn no está en ningún sitio; y la red M1 del incremento
por año corta con `!= "hormigon"`, así que ni residuos ni mortero lo generan.
Sus casos nacen ROJOS como defecto conocido y los arreglos son fichas propias.
**Pregunta abierta que cambia el ground truth de 19 albaranes**: el mínimo de 1
tn, ¿alcanza al movimiento de contenedor —que hoy se cuenta en CONTENEDORES,
§10.6 del doc de dominio— o solo a la línea de incremento/canon, que sí se
tarifa por tonelada?

Y hay **tres espacios de nombres que nadie reconciliaba**: las 10 etiquetas del
Excel, las CUATRO familias de documento del catálogo (`combustible` y
`alquiler_maquinaria` son de alcance LÍNEA) y las 7 pestañas de los libros.
Poner `combustible` como familia de documento dejaría ese caso ROJO para
siempre sin que nada esté roto. La tabla de mapeo vive solo en
`vocabulario.json`, y **tres filas quedan pendientes de ti**: CONTENEDORES
(¿residuos o genérico con línea de alquiler?), GASOLEO y CAMION GRUA. La
pestaña Bombeo se queda vacía. Que al catálogo le falten familias de documento
es ficha aparte: hoy deja mal a 2 albaranes de 59.

**Cerrado el 2026-09-15 · las dos decisiones que faltaban.** (1) El mínimo de 1
alcanza SOLO a lo que se pesa —canon y tratamiento: 0,42 tn se valora como 1;
3,10 tn como 3,10—, y el movimiento de contenedor sigue en unidades (1 cambio =
1 UD), así que el ground truth de los 19 albaranes de residuos queda fijado.
(2) CONTENEDORES es familia `residuos`; GASOLEO y CAMION GRUA van con documento
`generico` y la LÍNEA marcada `combustible` / `alquiler_maquinaria`, que es lo
único que el sistema produce hoy (si algún día fueran familia de documento
propia, es ficha del catálogo, no de F-045). Las diez etiquetas del Excel tienen
destino y ninguna cae en «desconocida».

**Corregido el 2026-09-15 · el vocabulario amplía el CATÁLOGO.** GASOLEO no es
genérico con línea marcada, es **`combustible`** (que hoy existe solo con
alcance línea), y GRAVA y FERRETERIA son **familias nuevas**, más **FERRALLA**,
que ni siquiera aparece en el Excel. Eso obliga a tocar
`ruesma_comun/contratos/familias.py`, que es ruta sensible —su texto se inyecta
en el prompt de IA1 y toca F-043—, así que **sale como ficha propia** y NO entra
en F-045. Mientras no exista, los casos de GASOLEO, GRAVA y FERRETERIA nacen
ROJOS a propósito y el informe los agrupa bajo «la familia aún no existe en el
catálogo», sin mezclarlos con defectos reales de clasificación. Volumen medido:
FERRETERIA 11 filas/3 albaranes, GRAVA 2/2, GASOLEO 1/1. Riesgos anotados en esa
ficha: `grava` no se puede validar con dos líneas, `ferralla` llega sin ningún
caso, y **el doc de dominio no documenta ninguna regla de ferralla**, así que la
ficha nace sin insumo de negocio. En el banco esto sí entra: las pestañas
`Grava` y `Ferreteria` se crean en los seis libros y se añaden a `TIPOLOGIAS`
del conversor (T8 bis), con prefijos `GRA-` y `FER-`.

### Lo único que sigue abierto de la spec

1. **Validación del humano** de la tabla de reparto (`design.md` §3) y de la
   política de vacíos por columna (R12): es la PARADA 1 antes de implementar.
2. **D6 · el campo `servicios` de la ficha F-045**: declara sv2/sv5/sv6, pero la
   feature no los toca; hay que anotarlo como «vigilados» o vaciarlo.

Revisada la spec entera tras los cambios de hoy, no queda ninguna
contradicción: se corrigió la última, que la columna `Tipo de albaran` daba a la
vez la pestaña y la familia, y ya no es cierto para GASOLEO ni CAMION GRUA.

Los arreglos salen como fichas propias, priorizadas en `design.md` §7: patrón 1
(partida mal leída) y patrón 3 (líneas deducidas que no se generan) primero;
CIF raro y número de albarán, al final, por tener un solo caso cada uno.

### Pendiente del humano, arrastrado

1. **T24 de F-036**: los 7 albaranes de SALMEDINA contra la BBDD real, SOLO
   LECTURA. Avisos: SS-0003967 dará 90,00 € ó 210,00 € según lo que case IA3;
   los tres que hoy aciertan (120/120/136) GANAN una sintética sin precio y
   pasan a revisión, y eso es lo querido.
2. **El push y el despliegue**: 130+ commits locales sin subir. **F-036 no puede
   mergearse sola** —sus tests viven en la rama de F-043—, y al desplegar **sv3
   va primero**: es quien crea las seis columnas que sv5 y sv4 leen.
3. **Tres mejoras del arnés** propuestas y no aplicadas (las lleva el humano):
   el falso verde de `harness.cobertura --feature`, que `harness.mutacion` no
   muta `in`/`not in`, y que avise cuando el alcance de una feature arrastra el
   de otra.
4. **Un PDF versionado** que incumple la norma:
   `services/albaranes-api/worker_input/0695 - Albaranes 2026.03.09-13-16.pdf`.

### Deuda conocida del banco de evals (entra en F-045)

- **42 de los 103 fallos de T30 son ruido de papeleo** (`caso_id`,
  `fichero_albaran`, `comentario`): se quitan pasando los observables a IA1 e
  IA2 en `evals/runner.py`, como ya hacen IA3 e IA4. El humano lo aprobó el
  2026-09-12 y quedó sin aplicar.
- IA4 sigue con 0 casos.

<!-- fin del bloque nuevo -->

## Lo anterior (histórico de la sesión de F-043)

### LO PRIMERO AL ABRIR LA PRÓXIMA SESIÓN

**Estás en `feature/F-043-clasificacion-por-ia1`**, que sale de la rama de
F-036 (no de `dev`). **56 commits locales, ninguno subido.**

**F-043 está en `spec_ready`, con la spec APROBADA y sus seis dudas resueltas
por el humano** (al final de `specs/F-043-clasificacion-por-ia1/requirements.md`).
El plan de implementación **también está aprobado**. Lo siguiente, sin volver a
preguntarlo:

1. Poner F-043 en `in_progress` (`harness/features.json`) y regenerar el backlog.
2. ~~Lanzar el implementer del **BLOQUE A (T1-T4)**~~ → **HECHO** el 2026-08-26,
   revisado y con los cambios requeridos aplicados. Informes:
   `progress/impl_F-043_bloque_A.md` + `progress/impl_F-043_bloque_A_cr.md`.
3. ~~**BLOQUE B (T5-T12)**~~ → **HECHO** el 2026-08-26. Informe:
   `progress/impl_F-043_bloque_B.md`. Nueve commits (`230fc22` … `3a10fce`),
   `init.sh` verde, 556 passed en la raíz y 139 en sv2, cobertura 98,9 %.
   **`tipologia_resolver` ya no existe**: el `grep` de T10 sale sin
   resultados. **Falta su review.**
4. ~~**BLOQUE C (T13-T17)**~~ → **HECHO** el 2026-08-26. Informe:
   `progress/impl_F-043_bloque_C.md`. Seis commits (`db205a2` … `6dd6844`),
   `init.sh` verde, 556 passed en la raíz y **169 en sv3**, cobertura 98,6 %,
   38 tests nuevos y **17 mutantes inyectados uno a uno, 0 supervivientes**.
5. ~~**BLOQUE D (T18-T23)**~~ → **HECHO** el 2026-08-26. Informe:
   `progress/impl_F-043_bloque_D.md`. Seis commits (`af0846c` … `6f2599a`),
   `init.sh` verde, 27 tests nuevos y **17 mutantes inyectados uno a uno, 0
   supervivientes**. **R26 CONSEGUIDO**: SS-0003967 vale **210,00 EUR en 2
   líneas** con la línea SIN `tipo_familia`, por la clasificación del
   DOCUMENTO. Medido con el builder real, mismo albarán, mismo contrato y
   mismo match, cambiando solo `context.clasificacion`: **720,00 € / 1 línea
   → 210,00 € / 2 líneas**.
6. ~~**BLOQUE E (T24-T27, T29, T33)**~~ → **HECHO** el 2026-08-27. Informe:
   `progress/impl_F-043_bloque_E.md`. Seis commits (`f989563` … `f3fd682`),
   `init.sh` verde, **26 tests nuevos en sv4** (131 → 157), cobertura de
   líneas cambiadas **98,8 %** y **8 mutantes inyectados uno a uno, 0
   supervivientes**. sv4 ya pinta familia, confianza y motivo; el catálogo y
   el contrato son **ruta sensible** (13 en aviso, evidencia = T30); la regla
   14 de `docs/ARCHITECTURE.md` y la nota del §9 del documento de negocio
   dejan escrito que **clasifica IA1, nunca una regla determinista**.

   **La implementación de F-043 está COMPLETA.** Lo siguiente: la **review de
   los bloques B, C, D y E** y, con su APROBADO, lo que queda es del humano —
   T28, T30, T31 y T32.
7. ~~**REVIEW FINAL** (`progress/review_F-043_final.md`)~~ → hecha el
   2026-08-27: **CHANGES_REQUESTED, 4 bloqueantes + 2 menores**. Todos
   **APLICADOS** el mismo día. Informe: `progress/impl_F-043_crf.md`. Lo que
   cambió: **CRF-1** el catálogo de familias no llegaba a IA2 —el task de fase
   1 viajaba SIN renderizar dentro del prompt de fase 2— y de paso se cerró la
   misma fuga de `{obras_activas}`, previa a F-043 (hallazgo 9); **CRF-2** R17
   ya tiene sus `test_f043_r17_*`; **CRF-3** T31 reescrita con la vía real
   (RE-EXTRAER) y el criterio de verde honesto; **CRF-4**
   `azure-apps/albaranes.md` recoge las seis columnas `tipologia*` y su índice
   (commit local `43196b1` **en ese otro repositorio**, sin push); **menores 5
   y 6** aquí abajo y en `requirements.md` (R27 acotado).
   **Decide el humano** si esto se cierra sin más review o si abre un tercer
   ciclo: el arnés admite dos y este era el segundo.

### BLOQUE E · dos cosas que el reviewer tiene que saber

- **Se corrigió la verificación de T27 en `tasks.md`.** Decía
  `python -m harness.cobertura --feature F-043`, y ese módulo no tiene
  `--feature`: argparse lo abreviaba a `--features`, no encontraba el catálogo
  y la puerta salía **`N/A` con exit code 0**. Un falso verde. Ahora usa el
  comando de `init.sh`. La de T29 sí funcionaba y no se tocó.
- **Se partió en dos la verificación de T4**, como pidió la review del bloque
  A: sv2 y sv3 comparten el paquete `infrastructure/sigrid` y en un solo
  proceso de pytest la pasada muere al RECOGER. Comprobados los dos comandos.
- Se tocó `tests/test_f011_r19_r20_declaracion.py` (el guarda del conjunto de
  rutas sensibles): las dos nuevas van en `RUTAS_ANADIDAS_DESPUES`, aparte de
  `RUTAS_DE_LA_SPEC`, que sigue siendo lo que aprobó F-011.

### BLOQUE D · lo que el bloque E y el reviewer tienen que saber

- **sv5 ya lee las seis columnas** y las entrega en `ContextoValoracion.
  clasificacion` y en `context.clasificacion` del sobre hacia sv6.
  `tipologia` NULL → `clasificacion=None`, nunca un `generico` inventado.
- **Las OCHO puertas de familia de sv6** (seis de familia, el detector de
  movimiento y el padre de la sintética) abren ya por
  `familia_efectiva(tipo_familia, clasificacion)`. Sin clasificación no se
  abre ninguna: comportamiento idéntico al de hoy (R27).
- **CAMBIO DE COMPORTAMIENTO CONOCIDO Y QUERIDO (R24).** Se borró
  `_derivar_tipologia_valoracion` de sv5: un documento **anterior** a F-043
  con líneas de residuos ya **no** se valora con `valuation_residuos` sino
  con el genérico, porque sin clasificación no hay familia de documento y
  adivinarla por las líneas es el lazo cerrado que la feature desmonta.
  Consecuencia para **T31**: revalorar SS-0003967 desde sv4 **no** basta —esa
  vía no re-extrae y el merge sigue con las seis columnas a NULL—; hay que
  volver a pasarlo por sv2 (`q-extraccion`) para que IA1 lo clasifique.
- **Lo que F-043 NO arregla y sigue vivo**: el 210,00 € exige además que IA3
  case la base contra el CONTENEDOR. Con el match REAL de SS-0003967 —la
  26481, que es el INCREMENTO— la guarda de F-036 R15 lo anula y el albarán
  sale en **90,00 € a revisión**. Es mejor que los 540,00 € valorados de más
  en silencio, pero no son los 210,00. Arreglar ese match es **T30** (evals
  del prompt), no el bloque D.

### BLOQUE C · qué existe ya (T13-T17), y qué tiene que saber el bloque D

- **La clasificación llega y se persiste.** `albaran_documents_merge` tiene
  seis columnas nuevas —`tipologia`, `tipologia_confianza_pct`,
  `tipologia_motivo`, `tipologia_origen`, `tipologia_mixta`,
  `tipologia_secundarias_json`— con DDL idempotente e índice en `tipologia`.
  **Es lo que T18 tiene que meter en el SELECT de sv5.**
- **Sin clasificación, las seis columnas quedan a NULL.** sv3 NO escribe
  `generico`/0/`ausente` para un documento anterior a la feature: si lo
  hiciera, sv5 leería una clasificación donde no la hay y R27 se rompería.
  El envelope sin bloque se marca con el motivo `clasificacion_ausente`.
- **Había un segundo hueco además de `_sanear_envelope`**, no previsto en
  `tasks.md`: `AlbaranConfidenceService.build_merge_analysis` rehace `data`
  campo a campo y tiraba la clasificación. Arreglado en T15. **Si el bloque D
  toca ese merge, que no lo deshaga.**
- **Motivos nuevos en `review_reasons_json` del documento** (los pinta sv4 en
  T24): `clasificacion_confianza_baja` (umbral `CLASIFICACION_CONFIANZA_
  MINIMA_PCT`, defecto 60), `clasificacion_mixta`, `clasificacion_ausente` y
  `linea_sin_familia_en_albaran_mixto:{n}` con el índice de la línea.
- **sv3 usa `familia_efectiva` del catálogo**, no una copia: es el mismo
  punto que T22 tiene que usar en las seis puertas de sv6 (R20).

### BLOQUE A · pasada 1 revisada y CAMBIOS REQUERIDOS APLICADOS

Review: `progress/review_F-043_bloque_A.md` (CHANGES_REQUESTED, 2 bloqueantes).
Los tres cambios están hechos —`74c80be` CR-1, `d3d195b` CR-2, `2c438b4` CR-3—
y documentados en `progress/impl_F-043_bloque_A_cr.md`. `init.sh` verde,
556 passed, cobertura 98,6 %. **Falta la pasada 2 del reviewer.**

Dos cosas que el bloque D (T22) tiene que saber:

- **`generico` es ahora familia de LÍNEA válida** (entró en el `Literal`
  `TipoFamilia` por decisión del humano del 2026-08-26, con test de coherencia
  contra `familias_linea()`). `familia_efectiva` puede devolver `'generico'`
  por su rama 4; las puertas de sv6 comparan contra `'residuos'` y
  `'hormigon'`, así que **no abre ninguna: mismo efecto que el `None` de hoy**.
- `ClasificacionAlbaran` se importa **siempre** de `ruesma_comun.contratos`
  (el reexport), nunca de `ruesma_comun.contratos.clasificacion`.

### BLOQUE A · qué existe (T1-T4)

Cuatro commits, uno por tarea (`af550a2`, `d5e5994`, `31817bf`, `44707c5`).
Lo que existe ahora y el bloque B ya puede usar:

- `ruesma_comun.contratos.familias` — catálogo único (7 familias: 4 de
  documento, 3 de solo línea), `familias_documento/linea`, `obtener`,
  `render_catalogo_markdown`, `prompt_fase2_de`, `prompt_valoracion_de` y
  `familia_efectiva`.
- `ruesma_comun.contratos.clasificacion.ClasificacionAlbaran`, reexportado en
  `ruesma_comun.contratos`.
- `DocumentoAlbaran.clasificacion` (default `None`) en sv2 y en sv3.

**Dos avisos para quien siga:**

- La verificación de T4 en `tasks.md` (`pytest services/albaranes-api/tests
  services/albaranes-persistencia/tests -k f043_schema`) **no puede funcionar**:
  sv2 y sv3 tienen ambos un paquete real `infrastructure/sigrid`, y en un solo
  proceso de pytest uno tapa al otro (falla al RECOGER
  `test_f002_obras_cache.py`, nada que ver con F-043). Es previo a esta feature.
  Se verificó lanzando las dos suites por separado, que es como lo hace
  `harness/init.sh`. Mismo cuidado en las verificaciones de T13-T17.
- La campaña de mutación con `--feature F-043` **muta también todo F-036**
  (esta rama sale de la de F-036, no de `dev`: 32 ficheros de diff contra
  `dev`). Para el bloque A se acotó con `--ficheros` a los dos módulos nuevos.
  Y muta el ÁRBOL PRINCIPAL: si se corta a medias, `python -m harness.mutacion
  --restaurar` antes de nada.

### BLOQUE B · qué existe ya (T5-T12), y qué tiene que saber el bloque C

- **La clasificación viaja en `data.clasificacion`** del envelope final, con
  los seis campos del contrato y el `origen` sellado (`ia1`/`ia2`/`ausente`).
  `meta.tipologia` sigue ahí, pero solo como espejo: el dato bueno es el de
  `data`. Es justo lo que T13 tiene que ver sobrevivir a `_sanear_envelope`.
- **Confianza 0 = hueco**, y hay dos formas de llegar a ella: la IA no
  clasificó (`origen='ausente'`, motivo `ia_sin_clasificacion`) o se inventó
  una familia (`origen='ia1'`, motivo `familia fuera de catalogo: '…'`). Las
  dos tienen que caer del lado de «a revisión» con el umbral de 60 % de T16.
- `application/services/clasificacion_resolver.py` es el único punto de sv2
  que decide algo sobre la familia, y no decide: normaliza. Sin `ler`, sin
  texto, sin CIF, con dos tests que lo vigilan.
- **El prompt de fase 2 se elige con `prompt_fase2_de(familia)`**: `None`
  significa «genérico configurado». Si alguien da de alta una familia con
  clave de prompt y olvida escribirlo en el YAML, el pipeline avisa por
  `WARNING` en vez de callarse.
- **`config/prompts.yaml` de sv2 es ahora ruta sensible tocada**: `init.sh`
  lista 8 rutas en aviso en vez de 7. Su evidencia es T30.

### El plan aprobado de F-043 · cinco implementers en serie

| # | Tareas | Qué hace |
|---|---|---|
| A | T1-T4 | El **catálogo** en `ruesma_comun` (familias, definiciones, `familia_efectiva`) y el contrato `ClasificacionAlbaran`. Base de todo lo demás |
| B | T5-T12 | **sv2**: fase 1 clasifica, fase 2 confirma, nace `clasificacion_resolver` y **se borra `tipologia_resolver`** |
| C | T13-T17 | **sv3**: que la clasificación sobreviva a `_sanear_envelope`, DDL, persistencia, umbral 60 % y motivos — **HECHO** |
| D | T18-T23 | **sv5 y sv6**: el contexto la lleva, las puertas de familia pasan a `familia_efectiva`, y **T23 prueba SS-0003967 → 210,00 €** — **HECHO** |
| E | T24-T27, T29, T33 | **sv4** la pinta, rutas sensibles, docs, cobertura, tamaños e `init.sh` — **HECHO** |

### Las CUATRO verificaciones MANUAL del humano, con su comando

> **Al 2026-09-11: T28 HECHA. Quedan T30, T31 y T32**, las tres del humano.
> T30 se factura y sigue sin autorizar; T31 depende de re-extraer el albarán
> por sv2; T32 es abrir la ficha en sv4. Con las tres, F-043 se puede cerrar
> y **F-036 se desbloquea** (su T23 se apoya en esta misma campaña).

Estaban solo nombradas aquí y sus comandos vivían en `tasks.md`. Copiados, con
el criterio de verde de cada una. **T31 lleva su detalle largo en `tasks.md`**
(cinco pasos) porque no cabe aquí sin repetirlo mal.

- ~~**T28 · campaña de mutación COMPLETA, sin tope, 0 supervivientes.**~~ →
  **HECHA** el 2026-09-11. Informe:
  `progress/impl_F-043_T28_supervivientes.md`. **No la relances: cuesta dos
  horas y muta el árbol principal.**

  La campaña corrió el 2026-09-10 (`progress/mutacion_F-043.md`, ya
  versionado): 347 mutantes, **184 muertos y 163 supervivientes**, sin
  muestreo, «base rota» = 0, sin «⚠ CAMPAÑA NO VÁLIDA». **Los 163
  supervivientes quedan analizados; sin justificar: CERO.** 96 eran huecos
  reales y se cerraron con tests nuevos (84 del catálogo LER, 8 de sv6, 4 de
  sv4), 7 son equivalentes con su guarda, y 60 se justifican **en bloque**
  —los dos `scripts/diagnose_sigrid_contrato_docs*.py`, con autorización
  expresa del humano del 2026-09-10—, verificado que son ejecutables sueltos
  que ningún servicio importa y que ninguna ruta de producción usa.

  **Los 3 «timeouts» eran ruido de la máquina, no mutantes lentos**: los
  mutantes 6, 7 y 9 de 347, con los 4 workers midiendo líneas base a la vez.
  Reinyectados, los tres **matan la suite de su servicio en menos de 3,5 s**
  frente al timeout de 275 s. Por eso el recuento real es 184/163/0.

  Cuatro commits previos (`9568ac2`, `8f36c77`, `cd35efb`, `805cccb`) más
  `78d1c6e` (las guardas de los seis equivalentes que faltaban: 1 en sv6 y 5
  en sv4, estos últimos sin tocar por nadie hasta ahora) y `b114377`
  (informe + fila en `inventario_mutacion_F-039.md`, que tenía `init.sh` en
  rojo por el guardián de F-039 R2).

  **Sigue abierto el `[~]` de RM1** que dejó la review: el SHA medido en
  `mutacion_F-043_bloque_A.md` no es HEAD. La campaña de T28 sí midió
  `48e3d17`, que tampoco es HEAD ya (hay 3 commits nuevos, todos de tests y
  papeleo: ninguno toca código de producción).
- **T30 · evals con LLM real. SE FACTURA y NO está autorizada** (duda 6: se
  decide al llegar, con número de casos, proveedores y coste delante).
  `python -m evals.runner --con-llm --feature F-043`.
  **Verde**: `progress/evals_F-043.md` con `MODO: completa`,
  `FASES: IA1,IA2,IA3,IA4,E2E` y `VEREDICTO: VERDE`. Hoy daría
  `NO_EVALUABLE`: los seis `evals/fixtures/*_indice.json` están a `casos = 0`.
  Es la **única** red que dice si IA1 clasifica bien y si IA3 casa el
  contenedor, o sea lo que cubre el riesgo aceptado de más abajo.
- **T31 · el caso real SS-0003967, de extremo a extremo.** **Reescrita**: hay
  que **RE-EXTRAER** (`encolar_extraccion.py`), revalorar NO basta, y el verde
  honesto es **90,00 € con `total_lines = 2` y `review_required = true`**, no
  210,00 €. Los cinco pasos ejecutables, el SQL y el «NO es verde si» están en
  `specs/F-043-clasificacion-por-ia1/tasks.md` → T31.
- **T32 · la ficha del revisor en sv4.** Abrir `http://localhost:8004` y entrar
  en la ficha del documento.
  **Verde**: se ven **familia, confianza y motivo** de la clasificación, y un
  albarán con `tipologia_confianza_pct` por debajo de 60 aparece **marcado a
  revisión**, con los motivos nuevos (`clasificacion_confianza_baja`,
  `clasificacion_mixta`, `clasificacion_ausente`) dentro del bloque de motivos
  que ya existía (F-036 R23).

### El riesgo declarado y ACEPTADO por el humano

El bloque B **borra `tipologia_resolver` entero**. Es lo correcto —es la pieza
que crea el lazo donde una regla decide qué puede concluir la IA— pero es lo que
enruta hoy el prompt de fase 2 de **todos** los albaranes, no solo los de
residuos. Si IA1 clasifica peor que el resolver en alguna familia, se nota en
todo el pipeline y **los tests no lo verán**: eso solo lo detectan las evals con
LLM real, que son T30 y siguen sin autorizar. La red que protege este cambio es
la que se dejó para el final. Se dijo, y se aceptó.

---

## F-036 · `blocked` a la espera de F-043

**Todo su código está implementado y aprobado**: bloque A aprobado en su review,
y bloques B, C y D rechazados en la pasada 1 y **aprobados en la pasada 2**.
`init.sh` exit 0, raíz **556 passed**, cobertura de líneas cambiadas 98,2 %.

**Por qué sigue bloqueada.** Toda la maquinaria de residuos de sv6 está cerrada
tras `contexto_linea.tipo_familia == 'residuos'`, y ese campo no llega al merge.
Medido con el builder real, mismo albarán y mismo contrato: **sin el campo
540,00 €, con él 210,00 €**. Eso lo arregla F-043 (su T22/T23).

**Lo que NO se hizo, a propósito**: no se reintrodujo la regla de T11 ni se
abrieron los gates de sv6 al `codigo_ler`. Sería clasificar por LER, prohibido
por el humano el 2026-08-25.

### Para cerrarla, cuando F-043 esté

1. **T23** · `python -m harness.mutacion --feature F-036`, cero supervivientes o
   justificación escrita por superviviente (rigor `critico`). **La lanza el
   humano**: muta el árbol principal.
   **Puede que ya no haga falta lanzarla.** La campaña de T28 de F-043
   (`progress/mutacion_F-043.md`) muta **F-036 entera**, porque esta rama sale
   de la de F-036 y no de `dev`: sus 38 ficheros de alcance incluyen los de
   F-036, y sus 163 supervivientes quedan **todos** analizados —los grupos A,
   B, D y G de `progress/impl_F-043_T28_supervivientes.md` son precisamente
   código de F-036—. **Lo decide el humano**: aceptar esa medición como la
   evidencia de T23, o exigir una campaña propia acotada al diff de F-036.
2. **T24** · BBDD real en SOLO LECTURA, los 7 albaranes de SALMEDINA. **Añadir
   ahí**: comprobar que ninguna línea real escribe el incremento como
   `INCREMENTO 170802` —pegado y sin la palabra `LER`—, grafía que antes casaba y
   que desde `CR-3` devuelve `None`.
3. **Evals** (`progress/evals_F-036.md`). Hoy darían `NO_EVALUABLE`: los seis
   `_indice.json` siguen con `casos = 0`.
4. **Reviewer final** contra `CHECKPOINTS.md`. Tiene que juzgar además los
   **cuatro `CR-10`..`CR-13`**, que se hicieron sin review propia porque el arnés
   admite dos ciclos y ya se habían gastado.
5. Y entonces `features.json` a `done`.

### Dos cosas de F-036 que hay que recordar

- **`ModifierContractMatcher` NO está cableado en producción** (verificado con
  grep por el reviewer): nadie lo instancia ni lee su flag. T19/R20 está bien
  hecho pero **hoy no cambia ninguna valoración**. Cablearlo es F-004.
- **Deuda de entorno**: `pytest` y `coverage` están instalados en
  `services/albaranes-front/.venv`, que desde T25 es el venv declarado de sv4 en
  `harness/servicios.json`. En otra máquina sin ellos, `init.sh` sale en rojo en
  sv4. Documentado en el README de sv4.

---

## Estado del arnés

| Repositorio | Versión | Estado |
|---|---|---|
| `arnes-base` | **1.7.2** | `main` sincronizado con `origin` |
| `albaranes` | **1.7.2** (2026-08-21) | Al día. Aplicado a mano; consta en `harness/ARNES_VERSION.md` |
| `porcentajes`, `postventa-incidencias` | 1.5.2 | sin actualizar |
| `datamart-seg-anual` | 1.5.0 | sin actualizar |
| `partes` | 1.4.0 | sin actualizar; se saltaría **siete** versiones |

### Mejoras del arnés propuestas y NO aplicadas (las levantó el reviewer)

1. **Una ficha en `blocked` apaga una puerta de contenido**: `PUERTA RUTAS
   SENSIBLES` sale `N/A` («sin feature en curso») aunque el diff sí toque rutas
   sensibles. Propuesta: que `harness.rutas_sensibles` acepte `--feature F-XXX`
   explícito, y que `CHECKPOINTS.md` mande cotejar el diff a mano ante ese `N/A`.
2. **`CHECKPOINTS.md` no contempla la review por bloques** de una feature grande:
   obliga a recorrer C1-C5 aunque el bloque revisado no pueda satisfacer C1 ni C5.
3. Si se aceptan, **son genéricas: hay que portarlas a `arnes-base`** en el mismo
   trabajo (regla de propagación).

---

## Pendientes del humano

1. **Actualizar los otros cuatro proyectos** a la 1.7.2 con el instalador.
   `partes` es donde más ficheros aparecerán «distintos»; desde F-035 el
   instalador ya no puede pisar estado.
2. **Verificaciones MANUAL arrastradas**: las 4 de F-002 (liberan el merge de
   F-003, aprobada en su rama desde hace días), y las de F-019 y F-027.
3. **Reconciliar F-003 y F-004 antes de arrancarlas** (su R4 conserva el cálculo
   que F-019 corrigió).
4. **Histórico mal valorado en BBDD**: sin backfill por diseño; se sanea
   revalorando desde sv4. Falta decidir cuáles. **Misma política confirmada para
   F-043** (decisión 5 de su spec).
5. **NADA está desplegado**: producción corre imágenes del 24 de julio, o sea
   **sin F-002, F-019 ni F-027** — y sin nada de F-036.
6. **`evals/fixtures/inputs/` vacío**: mientras lo esté, la puerta de rutas
   sensibles se queda en `aviso` y las evals dan `NO_EVALUABLE`.
7. **Retirar de la F-010 del otro proyecto** las dos reglas del arnés (hoy en la
   ficha de F-038).
8. **`progress/historico/mutacion_F-011.md` sigue invalidada** y
   **`mutacion_F-002.md` en cuarentena** (sellada en su primera pantalla el
   2026-08-25). La decisión de F-002 sigue abierta: relanzarla con la caché
   limpia, o anotar allí que su evidencia no vale.

---

## Notas operativas (valen para cualquier sesión)

- **Los `impl_`, `review_` y `evals_` de features cerradas viven en
  `progress/historico/`** (archivados el 2026-08-25: 29 ficheros, 639 KB). Las
  **campañas de mutación NO se archivan**: F-039 las vigila por ruta fija y
  moverlas pone 8 tests en rojo. El porqué, en `progress/historico/README.md`.
- **Nada en paralelo**: dos suites a la vez tumban el proceso en Windows
  (`0xC0000142`). Y **una campaña de mutación muta el árbol principal**: mientras
  corra, no lanzar `init.sh` ni tests.
- **Un agente con demasiado contexto se cuelga en bucle.** Lanzar uno **nuevo y
  acotado** —diciéndole exactamente qué leer— lo resuelve y sale más barato. Toda
  la sesión del 25-26 de agosto se hizo así, por bloques, sin un solo cuelgue.
- **Un agente que se cuelga no pierde el trabajo commiteado.** Ayuda que
  commiteen por tarea.
- **No ensuciar el árbol mientras un agente trabaja**: C5 exige árbol limpio, y
  además tus cambios pueden colarse en el commit de otro.
- **Los agentes no deben usar scripts que reescriban ficheros versionados**;
  copias en el scratchpad.
- **Cuidado con las rutas de Windows en heredocs de Python**: `\U` de `C:\Users`
  se interpreta como escape unicode y mata el script.
- **La máquina es compartida y se nota**: otra sesión corriendo triplica los
  tiempos y puede invalidar una campaña. Antes de lanzar una, comprueba que no
  hay nada más corriendo.
- **Un comando de verificación guardado en `progress/` puede caducar**: si
  guardas un comando, guarda también de qué depende.
- **El humano ejecuta él mismo** los `push`, los merges y las verificaciones
  MANUAL. Dale el comando listo para **PowerShell**, con `git -C <ruta>`, sin
  `&&` (su PowerShell 5.1 da error de parser) y diciendo cuál es el criterio de
  verde.

---

## Deudas menores que sobreviven (ninguna bloquea)

1. **RM2 solo dispara a 10×** y, con «Tiempo total» > 60 s, tampoco se reejecuta:
   un informe «solo» cinco veces demasiado rápido pasaría. Aire deliberado.
2. **Marcas `[ADAPTAR]` sin resolver** en las specs de F-034 y F-035 (aviso de
   `init.sh`, no bloquea).
3. **`ruff`: 1138 avisos** de deuda previa en el monorepo (+9 del bloque C de
   F-043: 7 `ISC004` de las sentencias DDL nuevas y 2 `UP006`, ambas reglas ya
   incumplidas por esos mismos ficheros; el detalle, en su informe §6). El
   bloque E no añadió ninguno, medido fichero a fichero.
4. **sv1-email e `infra` sin directorio de tests**: nadie comprueba lo suyo.

---

## IA1/IA2 del lote SALMEDINA: HECHO (2026-09-11)

Banco de evals completo en las fases IA1 e IA2 con los siete albaranes de
SALMEDINA. **Indices: IA1 0 -> 7, IA2 0 -> 7.** Informe:
`progress/impl_F-043_evals_ia1_ia2.md`.

Se hizo con la **Opcion A** que decidio el humano: IA1 mide LO IMPRESO. Los
siete PDF no son albaranes comerciales, son el documento de control de residuos
(RD 553/2020) con una rejilla LER preimpresa y el volumen a mano; no imprimen
concepto, ni precio, ni codigo de obra. Lo que el Excel de negocio pone en esas
columnas es la vista ya valorada.

Tres cosas que arrastrar:

1. **`SS-0801977` -> `SS-0001977`** en RES-005: el papel lo imprime asi y el
   numero anterior era una mala lectura del sistema. Corregido en los cuatro
   sitios del banco. `progress/impl_F-043_evals_banco.md` queda **superado en
   ese punto** (sigue citando el numero viejo; no se reescribe el pasado). La
   **BBDD local no se toco** y sigue guardando `SS-0801977`: la divergencia
   queda escrita en el comentario del caso.
2. **IA1 e IA2 daran 35 fallos falsos** (14 + 21) hasta que se les pase su lista
   de `observables` en `evals/runner.py:306`, como ya hacen IA3 e IA4: hoy
   comparan tambien las columnas de papeleo (`caso_id`, `fichero_albaran`). Es
   una linea, pero es diseno del banco y lo decide el humano. El defecto estaba
   tapado por tener los libros vacios.
3. **Sigue abierto** el agujero de `impl_F-043_evals_banco.md` §5: las
   CONDICIONES no se propagan al `contexto_linea` y los importes salen x6. Es lo
   unico que impide el verde de T30.

Verificado: conversor con 0 hallazgos del barrido, runner determinista con
**diff vacio** contra la linea base (la siembra no mueve nada), `init.sh` en
verde, ningun `.xlsx` ni `.pdf` en el indice de git. Cero llamadas a LLM.

Aparte y sin tocar: hay **un PDF preexistente en el indice**,
`services/albaranes-api/worker_input/0695 - Albaranes 2026.03.09-13-16.pdf`,
entrado con la importacion de `albaranes-api` (`df01ef4`).

## 2026-09-12 · el canal de los subprocesos de evals (defecto que bloqueaba T30)

`--con-llm` moria en `json.loads(proceso.stdout)`: PyMuPDF escribe en STDOUT
su aviso de que `fitz` esta deprecado y contaminaba el canal por el que vuelve
el JSON. Arreglado en `evals/procesos/canal.py` por los dos extremos (el hijo
blinda su stdout con `dup2`, el padre lee la carga entre marcas); sv2, sv5 y
sv6 tenian los tres el mismo defecto. Detalle, traza RED y evidencias en
`progress/impl_F-043_evals_runner_fix.md`.

La **pasada de T30 queda desbloqueada**, pero seguira dando ROJO por el punto
3 de arriba (las CONDICIONES sin propagar, importes x6): eso sigue abierto.

## 2026-09-15 · DESPLIEGUE EN CURSO (punto de reanudación)

**sv3 YA está desplegado y al día**: `sv3-persistencia:r20260915-0002`, una sola
revisión, estado `ok`. Es el primer servicio que se actualiza **desde el 24 de
julio**, y el primero construido desde el monorepo. Al arrancar habrá aplicado
su DDL, así que **las seis columnas `tipologia*` deberían existir ya en la BBDD
de producción** — falta confirmarlo (el humano; la consulta está abajo).

**Faltan los otros cinco**: sv1, sv2, sv4, sv5 y sv6, todos con
`r20260724-1632`.

### Lo que se arregló para poder desplegar

1. **El build empaquetaba los repositorios ARCHIVADOS** en vez del monorepo:
   la causa de que nada llegara a producción desde julio. Rama
   `chore/infra-build-desde-el-monorepo`, informe en
   `progress/infra_despliegue_fuente_equivocada.md`.
2. **`00_vars.ps1` no cargaba `00_vars.local.ps1`**: la suscripción iba
   redactada y `az account set` fallaba siempre. Ya carga («[vars] valores
   reales cargados»).
3. **`-Only` no limitaba el build**: construía los seis.
4. **El temporal de build bloqueado tumbaba el despliegue** (2026-09-15):
   Windows retiene `%TEMP%\acrbuild_<svc>` y el `Remove-Item` del `finally`
   abortaba el script DESPUÉS de subir la imagen. Ahora el contexto lleva
   nombre único por ejecución y la limpieza es best-effort. **Sin commitear
   todavía** cuando se escribió esto.

### Al retomar

```powershell
cd C:\Users\pgris\PycharmProjects\albaranes\infra
. .\00_vars.ps1
.\deploy.ps1 -Only sv1,sv2,sv4,sv5,sv6
.\check_deploy.ps1
```

Vigilar: que las rutas impresas sean `albaranes\services\...`; que no queden
**revisiones múltiples** (`fix_revisiones.ps1 -Only <svc>`); y si algo falla
tras el `OK <svc> ->`, la imagen ya está subida: continuar con
`-Tag <el impreso> -SkipBuild`.

**La comprobación que de verdad importa** no es `check_deploy`, sino procesar
un albarán y ver en la ficha del portal la familia, la confianza y el motivo.
Y en la BBDD de producción:

```sql
SELECT column_name FROM information_schema.columns
WHERE table_name = 'albaran_documents_merge' AND column_name LIKE 'tipologia%';
```

Deben salir seis.

---

## F-047 · SPEC ESCRITA (2026-09-16, spec-author) — 2.ª versión

`specs/F-047-evals-ciclo-completo/`: requirements (150 líneas, 40 R), design
(245) y tasks (23 tareas; T19–T22 son MANUAL y exigen el pipeline local).
Rigor `critico`. No se ha tocado una línea de código. Ficha de
`harness/features.json` reescrita con el alcance nuevo y pasada a `spec_ready`.

**La 1.ª versión fue RECHAZADA por el humano**: proponía encadenar los hand-off
en memoria saltándose la persistencia. Sus palabras: «no, debería encadenar el
proceso completo, incluyendo ambas persistencias». Tenía razón y el argumento
está recogido en la spec: dos de los defectos que motivan la ficha —el
`contexto_linea` perdido en el reproceso y la rama de duplicado que no llamaba a
`save()`, con las seis `tipologia*` en NULL— son de persistencia y un ciclo en
memoria no los habría visto.

### El alcance vigente

El banco inyecta por la misma puerta que sv1 (fila en `workflow_runs`, blob
`input/`, `MensajeExtraccion`, reutilizando `ruesma_comun`) y deja que el
pipeline LOCAL lo recorra entero: `q-extraccion` → sv2 → `q-persistencia` → sv3
→ `q-valoracion` → sv6 → HTTP → sv5 → sv6 persiste. Las salidas de cada fase se
leen de Postgres y solo con `SELECT`.

### Hallazgo del análisis que cambia el diseño

**`workflow_runs` NO avanza en el pipeline real.** `ruesma_comun.workflows`
expone `transicionar`, pero el único código que la llama son los tests de humo
del propio paquete: la fila se queda en `email_received` todo el recorrido. Por
eso la terminación se decide por **evidencia persistida** (cinco hitos, de las
filas de `albaran_documents` a `albaran_line_valuations`), con plazo por hito
contado desde el último avance y vigilancia de las colas `-poison`. Que los
workers transicionen es un arreglo del SISTEMA, no del banco: **candidato a
ficha propia**.

### Decisiones abiertas que necesita validar el humano

1. **`INDETERMINADO` degrada la pasada a NO_EVALUABLE, no a ROJO.** Cuando IA1
   rompe el emparejado de líneas no se puede atribuir sin adivinar.
2. **Cuando sv3 no auto-selecciona contrato**, el banco hace el gesto del
   revisor de sv4 (fija el de `INPUTS.CASOS.contrato_codigo` y republica
   `MensajeValoracion`) y declara que ese caso NO midió la selección. La
   alternativa —dejarlo colgar— convertiría en NO_EVALUABLE todos los casos con
   más de un contrato.
3. **El aislamiento va por baja LÓGICA**, la misma vía de sv4, nunca `DELETE`, y
   solo sobre documentos con prefijo `eval/`. `--reproceso` hace lo contrario a
   propósito para ejercitar la rama de duplicado.
4. **El coste y el tiempo**: cada caso recorre seis servicios con dos llamadas
   LLM en sv2 y una o dos en sv5. T19 pasa UN caso, T20 seis, y la de 59 (T22)
   la decide el humano.

### Costuras que el ciclo NO vigila (declaradas en design §9)

sv1 y el buzón M365, sv4 salvo el gesto de contrato, SharePoint real, y el
comportamiento contra Azure de verdad (Azurite no es Azure Queue; la identidad
gestionada no se ejercita).

Siguiente paso: aprobación del humano y, con ella, el implementer sobre
`feature/F-047-evals-ciclo-completo`.
