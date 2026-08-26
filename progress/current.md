<!-- progress/current.md -->
# Trabajo en curso

## Cierre de sesión — 2026-08-21 (sesión del 20 y 21 de agosto)

Sesión entera dedicada al **arnés**: **F-038, F-039 y F-040 cerradas**, aprobadas,
mergeadas en `dev`, subidas y portadas a `arnes-base`. El detalle de cada una
está en `progress/history.md`; aquí solo queda lo vivo.

La suite del monorepo pasó de **305 a 530 tests**; la de `arnes-base`, de 47 a
**263**.

**Añadido el 21-ago, después de ese cierre**: `albaranes` ya está **actualizado
a la 1.7.2** (rama `arnes/1.7.2`, 531 tests). Se aplicó a mano, no con el
instalador; el porqué y el detalle, en `progress/history.md`.

### Estado de esos cuatro puntos, al 2026-08-25

1. **Merge de `arnes/1.7.2` a `dev`: HECHO y subido.** `origin/dev` está al día.
2. **`progress/mutacion_F-002.md` sigue en cuarentena, pero ya lo dice el propio
   informe**: 108 mutantes en 54,8 s en serie = **0,51 s por mutante**, por
   debajo del segundo que la regla del coste por mutante declara sospechoso por
   construcción. El 25-ago se le puso el sello en su primera pantalla, porque la
   advertencia vivía solo aquí y quien abriera el fichero se creía sus números.
   **La decisión sigue siendo del humano**: relanzar con la caché limpia, o
   anotar allí que su evidencia no vale.
3. **F-036 (residuos): EN CURSO desde el 2026-08-25**, rama
   `feature/F-036-residuos-contenedores-e-incrementos`. Spec aprobada, 27
   requisitos y 25 tareas. Ver la sección de abajo.
4. Después, **F-041** (el quinto defecto de la campaña, `critico`, prioridad 2).

---

## Estado del arnés

| Repositorio | Versión | Estado |
|---|---|---|
| `arnes-base` | **1.7.2** | F-038 (1.7.0), F-039 (1.7.1) y F-040 (1.7.2) portadas y **subidas**: `main` sincronizado con `origin`. Destino: 263 passed, instalador 65 verde |
| `albaranes` | **1.7.2** (2026-08-21) | Al día. El sello vuelve a decir la verdad: entró el **arreglo del bytecode envenenado** (1.6.3) y los criterios que faltaban en `CHECKPOINTS.md` y en el reviewer. Aplicado a mano —el instalador habría duplicado ~190 tests que aquí ya existen con nombre `test_f0XX_*`—; consta en `harness/ARNES_VERSION.md` |
| `porcentajes`, `postventa-incidencias` | 1.5.2 | sin actualizar |
| `datamart-seg-anual` | 1.5.0 | sin actualizar |
| `partes` | 1.4.0 | sin actualizar; se saltaría **siete** versiones |

### El hilo conductor de la sesión, por si sirve de guía

Un solo defecto con **cuatro caras**, todas cerradas: la campaña de mutación
diciendo «todo bien» **sin haber juzgado nada**. La invocación sin ruta que moría
en la recolección (F-038 T0), el flake de las filas de reloj (F-038 T17), la
guarda inalcanzable de `--ficheros ","` (F-039 CR-2) y la campaña con alcance
vacío por `--feature` (F-040 D4).

**La quinta cara sigue viva y tiene ficha: F-041.** `ResultadoSuite.verde` cuenta
`PYTEST_SIN_TESTS = 5` como verde, así que un mutante cuya suite no recogió ni un
test sale SUPERVIVIENTE en vez de «no juzgado». El sesgo es el seguro —solo
produce falsos supervivientes, nunca falsos muertos—, pero **mientras viva,
ninguna campaña de una sola pasada vale como evidencia sin contraste**. Esa regla
ya se aplicó dos veces y ahorró horas de máquina.

---

## Pendientes del humano

1. ~~Merge de `arnes/1.7.2` a `dev` y push.~~ **HECHO el 2026-08-25**, junto con
   el merge de `chore/poda-progress`. `origin/dev` está al día.
2. **Actualizar los otros cuatro proyectos** a la 1.7.2 con el instalador.
   `partes` es donde más ficheros aparecerán «distintos»; desde F-035 el
   instalador ya no puede pisar estado. Ahí sí conviene usarlo: el problema de
   los tests duplicados es exclusivo de `albaranes`, que fue donde nacieron.
3. **Verificaciones MANUAL arrastradas**: las 4 de F-002 (liberan el merge de
   F-003, aprobada en su rama desde hace días), y las de F-019 y F-027.
4. **Reconciliar F-003 y F-004 antes de arrancarlas** (su R4 conserva el cálculo
   que F-019 corrigió).
5. **Histórico mal valorado en BBDD**: sin backfill por diseño; se sanea
   revalorando desde sv4. Falta decidir cuáles.
6. **NADA está desplegado**: producción corre imágenes del 24 de julio, o sea
   **sin F-002, F-019 ni F-027**.
7. **`evals/fixtures/inputs/` vacío**: mientras lo esté, la puerta de rutas
   sensibles se queda en `aviso`.
8. **Retirar de la F-010 del otro proyecto** las dos reglas del arnés (hoy en la
   ficha de F-038).
9. **`progress/mutacion_F-011.md` se queda invalidada** (decisión del 20-ago):
   305 mutantes y 133 supervivientes medidos con la invocación rota, no se
   repiten. Consecuencia: **la puerta de evals de F-011 no tiene hoy ninguna
   medición de mutación válida detrás**.

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

- **Los `impl_`, `review_` y `evals_` de features cerradas viven en `progress/historico/`** (archivados el 2026-08-25: 29 ficheros, 639 KB). Las **campañas de mutación NO se archivan**: F-039 las vigila por ruta fija y moverlas pone 8 tests en rojo (el porqué, en `progress/historico/README.md`).
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

- **La máquina es compartida y se nota.** Dos veces esta sesión otra sesión
  (campañas de `datamart-seg-anual`) triplicó los tiempos: la suite pasó de 51 s
  a 149 s y las campañas se invalidaron solas. La suite **nunca estuvo roja**.
  Antes de lanzar una campaña, comprueba que no hay nada más corriendo.
- **Una campaña paralela ralentiza su propia suite**: ~51 s en reposo, 97,5 s con
  1 worker, 119-121 s con 3. Desde F-040 el timeout se deriva de esa medición, así
  que ya no hace falta pasar `--timeout` a mano; si te hace falta, es un síntoma.
- **Un comando de verificación guardado en `progress/` puede caducar**: el de la
  campaña paralela usaba `--feature F-038`, y al mergear F-038 su diff pasó a ser
  vacío. Si guardas un comando, guarda también de qué depende.

---

## Deudas menores que sobreviven (ninguna bloquea)

1. **RM2 solo dispara a 10×** y, con «Tiempo total» > 60 s, tampoco se reejecuta:
   un informe «solo» cinco veces demasiado rápido pasaría. Aire deliberado.
2. **Marcas `[ADAPTAR]` sin resolver** en las specs de F-034 y F-035 (aviso de
   `init.sh`, no bloquea).
3. **`ruff`: 1108 avisos** de deuda previa en el monorepo.
4. **sv1-email e `infra` sin directorio de tests**: nadie comprueba lo suyo.

---

## F-036 · spec escrita (2026-08-22, spec-author)

Escrita `specs/F-036-residuos-contenedores-e-incrementos/`: **27 requisitos**
EARS y **25 tareas**. `python -m harness.tamano --feature F-036` en verde
(requirements 149/150, design 222/250).

- **T1 = D1** y es su propio commit, como manda la decisión (6). D1 se
  especifica como regla GENERAL de sv4 («si la conversión no es reproducible,
  sv4 conserva lo que escribió sv6»), sin ningún `if residuos`, y el guardián
  de F-019 R24 pasa a compararse SOLO por entradas.
- Sin SQL nuevo: `albaran_line_valuations.review_reasons_json` ya existe; sv4
  pasa a leerla y escribirla.
- `modifier_source='gestion_residuos'` ya está en el `Literal` de sv5, así que
  D3 NO dispara los «5 sitios» de ARCHITECTURE §10.

### Decisiones del humano aplicadas (2026-08-22, segunda pasada)

Las cinco dudas están RESUELTAS y la spec ya las incorpora:

1. **R3** confirmado tal cual: conservar la `cantidad_convertida` de sv6,
   marcar `review_required`, razón
   `front_cantidad_editada_sin_conversion_reproducible`. No se re-encola.
2. **R8** confirmado: la plantilla deja de recalcular el importe en Jinja
   cuando la conversión no es reproducible.
3. **R14** confirmado: el catálogo LER va a `ruesma_comun`; el coste de
   reconstruir las imágenes de sv2, sv3, sv5 y sv6 está aceptado.
4. **R17 CAMBIÓ** («siempre debe crear la sintética; ya pondrá el revisor el
   importe a mano»): con LER válido sv6 emite SIEMPRE la sintética; sin tarifa
   sale sin precio (forma C, alineada con la red M1) y SÍ activa
   `review_required`. Arrastró a R16, a R25 y a las tareas T16, T17, T21, T22
   y T24.
5. **R24** acotado a `proveedor_cif_no_casa`; el resto de motivos sellados por
   sv3 van en ficha aparte.

**Consecuencia declarada en R25 y en el diseño**: SS-0000168, SS-0003935 y
SS-0025146 GANAN una línea sintética sin precio y pasan a `review_required`.
El invariante es su TOTAL (120,00 / 120,00 / 136,00), no su número de líneas
ni su estado de revisión. **No es una regresión**, y está escrito así para que
el reviewer no lo lea como tal.

Tamaños tras la segunda pasada: requirements 146/150, design 228/250.

### Arranque de la implementación (2026-08-25)

Rama `feature/F-036-residuos-contenedores-e-incrementos` creada desde `dev`
(que ya incluye la poda de `progress/`). F-036 pasa a `in_progress`; es la
ÚNICA en curso.

**Las 25 tareas se reparten en cuatro implementers en serie**, no en uno solo:
un agente con demasiado contexto se cuelga en bucle (le pasó al reviewer de
F-034 esta misma semana). Cada tarea, su commit.

| Bloque | Tareas | Servicios |
|---|---|---|
| A | T1-T7 | sv4 (D1: el recálculo que hoy estropea los albaranes, y la trazabilidad) |
| B | T8-T13 | `comun` (catálogo LER), sv3 (scorer del merger), sv5 (tipología y prompts) |
| C | T14-T20 | sv6 (D3: sintéticas por LER, guarda anti-incremento, predicado del matcher) |
| D | T21, T22, T25 | tests de aceptación de SALMEDINA e `init.sh` |

Revisión corta tras el bloque A (es el que mueve los euros) y reviewer completo
contra `CHECKPOINTS.md` al final.

**T23 (campaña de mutación) y T24 (comprobación en la BBDD real) las lanza el
humano**, no un agente: la campaña muta el árbol principal y T24 es lectura
contra Azure.

### Bloque A (T1-T7) IMPLEMENTADO — 2026-08-25

**Hecho y commiteado en la rama** (8 commits, `4caeb0a`..`960e0d1`, ninguno
subido). Informe completo con las trazas de fase RED:
`progress/impl_F-036.md`. Falta la revisión corta del bloque A.

Lo que cambió, en una línea cada cosa: sv4 conserva la `cantidad_convertida`
que no sabe rehacer (se acabó el ×6 de SALMEDINA al guardar), el guardián de
F-019 R24 mira solo las entradas, las decisiones quedan escritas en
`review_reasons_json`, la ficha PINTA por fin esas razones y los motivos del
documento, la plantilla deja de recalcular el importe en Jinja y los
`proveedor_cif_no_casa:<cif>` caducan cuando el revisor corrige el CIF.

- Suite de sv4: **130 passed** (eran 59). `test_f019_r23_r26_recalculo_importe.py`
  en verde **sin tocarlo** (R26).
- `PUERTA COBERTURA: 97,3 % de 113 líneas cambiadas` (umbral 80 %, `critico`).
- **Se instaló `jinja2` en el venv raíz** para que los tests de render de T5/T6
  no se salten. `jinja2>=3.1` ya estaba en el `requirements.txt` de sv4; no se
  tocó ningún manifiesto. Alternativa más limpia, si el humano la prefiere:
  declarar `"venv"` de sv4 en `harness/servicios.json` (ese venv tiene jinja2 y
  FastAPI, pero hoy NO tiene pytest).
- El punto ciego conocido de R7 (`factor=1.0`, cantidad 1, convertida 1) queda
  documentado y **cubierto por un test que fija el comportamiento actual**, sin
  inventar nada para taparlo.

### Bloque A REVISADO — APROBADO (2026-08-25)

`progress/review_F-036_bloque_A.md`. El reviewer verificó por su cuenta la
suite (130 passed, **0 skipped**), la cobertura y que R26 sigue intacto. Los
tres puntos de criterio salen a favor, y deja constancia de que el arreglo
**mejora** el guardián de F-019: sacar `cantidad_convertida` de `sin_cambios`
era justo lo que impedía que la rama «esta fila no se toca» entrara nunca en
una línea de residuos.

**Cuatro cambios requeridos antes de CERRAR F-036** (ninguno bloquea el bloque A):

1. `requirements.md` R4: escribir que la razón se sella solo en las líneas que
   el guardado actualiza.
2. `templates/document_detail.html:623`: `join('&#10;')` no da salto de línea
   —con `autoescape` Jinja escapa el `&`—; separar con `"
"` real y test del
   separador.
3. `review_repository.py:4048`: la docstring nombra `_num_iguales`, que hoy
   vive en `domain.models.review_models.numeros_iguales`.
4. Entorno de los tests de render. **DECIDIDO POR EL HUMANO el 2026-08-25**:
   `conftest.py` pasa a `import jinja2` DURO (un entorno sin jinja2 debe caerse,
   no saltarse 10 tests en silencio) **y** `harness/servicios.json` declara
   `"venv": "services/albaranes-front/.venv"` para sv4; hay que **instalar
   pytest en ese venv**. Se ejecuta en **T25**, con el bloque D.

Los cambios 1-3 se entregan al implementer del bloque B como su tarea T0.

**Pendiente de arnés (propuesta del reviewer, NO aplicada)**: `CHECKPOINTS.md`
no contempla la review por bloques de una feature grande —obliga a recorrer
C1-C5 aunque el bloque no pueda satisfacer C1 ni C5—. Si se acepta, es mejora
genérica y hay que portarla a `arnes-base` en el mismo trabajo.

### Bloque B ENTREGADO — T0 + T8-T13 (2026-08-25)

Informe: **`progress/impl_F-036_bloque_B.md`**. Siete commits, uno por tarea,
ninguno subido. Los cambios 1-3 de la review del bloque A quedan CERRADOS (T0);
el 4 sigue siendo de T25.

- **T8** · el catálogo LER vive ya en `services/albaranes-comun/ruesma_comun/
  ler.py`; en sv2 solo queda la reexportación y hay test que comprueba que no
  hay copia. `tipologia_resolver.py` intacto.
- **T9/T10** · el merger de sv3 puntúa las nueve medidas de residuos Y completa
  al ganador con las que le faltan, sin sobrescribir ni fusionar los narrativos.
- **T11** · sv5 aplica la regla dura LER → residuos antes de mirar
  `tipo_familia`, con el catálogo compartido.
- **T12** · en sv6 el **volumen manda sobre la resta**; los nombres de las
  `reasons` no cambian. **T13** · el prompt `valuation_residuos` documenta ese
  orden nuevo.

Verificado: las **6 suites en verde** (526 passed, 3 skipped, 0 failed), 84
tests nuevos, `PUERTA COBERTURA 97.0 %` (196/202) y `PUERTA TAMAÑO` en verde.
`bash harness/init.sh` NO se ejecutó: es T25.

**Dos cosas para el líder** (detalle en el informe): (a) `texto_contiene_ler`
busca `"ler"` como SUBCADENA —`TORNILLERIA`, `ALQUILER`— y da contexto de
residuos a cualquier 6-dígitos válido; es heredado de sv2 y NO se tocó, pero
T11 lo extiende a sv5: propongo ficha aparte. (b) `harness/features.json` no
declara sv2 ni `comun` entre los servicios de F-036, y T8 los toca por R14.

**Puerta de rutas sensibles en `aviso`**: tres rutas tocadas sin
`progress/evals_F-036.md` (`prompts.yaml` de sv5, `residuos_container_calc.py`,
`tipologia.py` de sv2). No se lanzó `evals.runner --con-llm`: gasta LLM real y
lo decide el humano. El bloque D3 vuelve a tocar `prompts.yaml` (T20), así que
la pasada tiene sentido UNA vez, en T25.

Siguiente: bloque C (T14-T20, sintéticas de LER en sv6).

### Bloque C ENTREGADO — T14-T20 (2026-08-25)

Informe: **`progress/impl_F-036_bloque_C.md`**. Siete commits, uno por tarea,
ninguno subido. D3 cerrado: los incrementos por LER ya se emiten.

- **T14** · `residuos_incrementos.py` (sv6) con `es_linea_incremento_ler`,
  `tarifa_incremento_ler` y `REGLAS_SINTETICAS_RESIDUOS`. Punto de enganche de
  F-006: el recorrido del builder no conoce ninguna regla concreta (test con
  una regla ficticia que se emite sin tocar el builder).
- **T15** · una línea base de residuos casada con un incremento por LER pierde
  el match ENTERO —id, precio y `match_method`— y va a revisión.
- **T16/T17** · el builder inyecta la sintética siempre que haya LER válido,
  con dedupe; sin tarifa sale sin precio, con
  `residuos_ler_sin_tarifa_en_contrato`, y activa revisión.
- **T18** · **el design se equivocaba**: R19 no era «solo un test». La
  sintética heredaba los m³ crudos, no el nº de contenedores → SS-0000589 daba
  426 € en vez de 171. Corregido solo para padres de residuos.
- **T19** · predicado por código LER en `ModifierContractMatcher`.
- **T20** · el prompt `valuation_residuos` dice ya que el incremento por LER lo
  inyecta sv6 de forma determinista, sin ablandar la prohibición a IA3.

Verificado: sv6 **156 passed**, sv5 **34 passed**, 34 tests nuevos,
`PUERTA COBERTURA 97.9 %` (281/287) y `PUERTA TAMAÑO` en verde. `init.sh` NO se
ejecutó: es T25.

**Tres cosas para el líder**: (a) `ModifierContractMatcher` **no está cableado
en producción** —no lo instancia nadie—, así que el predicado de T19 hoy no
afecta a ninguna valoración real; cablearlo es F-004. (b) El hallazgo de
`texto_contiene_ler` sigue abierto y sin tocar. (c) `config/prompts.yaml`
vuelto a tocar: la pasada de evals sigue pendiente para T25.

Siguiente: bloque D (T21-T25, aceptación, mutación y `init.sh`).

## Bloque D de F-036 — CERRADO con un aviso (2026-08-25)

Detalle en `progress/impl_F-036_bloque_D.md`. Cuatro commits locales:
`7ca2ffc` (reversión de T11), `591d9ee` (T21+T22), `766abee` y `492889e`
(las dos partes de T25).

- **T11 REVERTIDA por decisión del humano.** sv5 vuelve a derivar la
  tipología SOLO del `tipo_familia` que puso la IA. R13 marcado RETIRADO en
  la spec; `ruesma_comun.ler` y el `tipologia_resolver` de sv2 intactos.
- **T21/T22** · escenario de aceptación de SALMEDINA, 19 tests, fase RED
  hecha contra `dev` en un worktree (9 failed, 10 passed; los totales daban
  120 donde el administrativo espera 171/210/210).
- **T25** · `bash harness/init.sh` en **verde, exit code 0**. Por el camino
  salió un rojo heredado del bloque C: T15 añadió el motivo
  `residuos_base_casada_con_incremento` sin ampliar el inventario congelado
  de `tests/test_f027_r18_r22_contrato.py`. Arreglado comprobando antes los
  consumidores del string. Además, sv4 declara ya su venv en
  `harness/servicios.json` y `jinja2` se importa duro en su conftest (once
  tests de render se saltaban en silencio con exit code 0).

**LO QUE TIENE QUE DECIDIR EL HUMANO ANTES DE CERRAR LA FEATURE**:
**SS-0003967 no llega a 210,00 € de extremo a extremo**. Toda la maquinaria
de residuos de sv6 está cerrada tras `contexto_linea.tipo_familia ==
'residuos'`, y ese campo NO lo restituyen T9/T10 (por R12 los cinco campos
narrativos no se fusionan) ni, ya, T11. Medido con el builder real: sin
`tipo_familia` el albarán se queda en **540,00**; con él da **210,00**. T24
fallará en ese albarán; los otros cinco no dependen del hueco. Tres salidas
propuestas en §2 del informe, ninguna dentro del alcance de F-036.

Pendiente del humano: **T23** (mutación), **T24** (BBDD real, solo lectura) y
`progress/evals_F-036.md` (la puerta de rutas sensibles avisa; NO se ha
lanzado `python -m evals.runner --con-llm`: gasta LLM real).

## F-036 · BLOQUEADA a la espera de F-043 (decisión del humano, 2026-08-25)

**Estado: `blocked`.** No es un fallo del trabajo: los cuatro bloques están
implementados y en verde (`init.sh` exit 0, 531 tests en la raíz, cobertura
97,8 % de las líneas cambiadas). Lo que falta es una pieza que **no está en el
alcance de F-036** y que el humano ha decidido esperar en vez de rodear.

**Por qué.** Toda la maquinaria de residuos de sv6 está cerrada tras
`contexto_linea.tipo_familia == 'residuos'`: el cálculo de contenedores
(`valuation_builder.py:1165`), la red de sintéticas del LER (`:846`) y la
guarda anti-incremento (`:985`). Ese campo NO llega al merge: T9/T10 restituyen
las nueve MEDIDAS, pero `tipo_familia` es narrativo y por diseño (R12) no se
fusiona. Medido con el builder real, mismo albarán y mismo contrato, cambiando
solo ese campo: **sin `tipo_familia` → 540,00 €; con él → 210,00 €** (el ground
truth). Detalle en `progress/impl_F-036_bloque_D.md` §2.

**Consecuencia concreta**: cinco de los seis albaranes del lote quedan
correctos; **SS-0003967 no**, y **T24 fallará en ese albarán** hasta que F-043
esté hecha.

**Lo que NO se hizo, y a propósito**: no se reintrodujo la regla de T11 ni se
abrieron los gates de sv6 al `codigo_ler`. Sería clasificar por LER, que es
justo lo que el humano prohibió el 2026-08-25.

### Para desbloquearla

1. **F-043** (prioridad 1, `pending`): IA1 clasifica y la clasificación llega
   hasta sv6.
2. Después, **T23** (campaña de mutación, la lanza el humano), **T24**
   (comprobación contra la BBDD real, MANUAL) y el **reviewer final** contra
   `CHECKPOINTS.md`.
3. Pendiente del humano y sin decidir: **`progress/evals_F-036.md`**. La puerta
   de rutas sensibles avisa (no bloquea) de seis rutas tocadas sin evals.
   `python -m evals.runner --con-llm --feature F-036` gasta LLM real.

### Deuda de entorno que nace aquí — RESUELTA

`pytest` y `coverage` están ahora instalados en `services/albaranes-front/.venv`,
que desde T25 es el venv declarado de sv4 en `harness/servicios.json`. **En otra
máquina sin esos paquetes, `init.sh` saldrá en rojo en sv4.** Documentado en el
README de sv4 (commit `5edd058`); se descartó `requirements-dev.txt`.

## 2026-08-25 · ciclo de corrección del RECHAZO de los bloques B/C/D

`progress/review_F-036_bloques_BCD.md` rechazó B/C/D con 2 bloqueantes y 6
cambios. **Los ocho están hechos**, un commit por punto (`2025e08` → `5edd058`).
Informe: **`progress/impl_F-036_correcciones_BCD.md`**.

Lo caro de los dos bloqueantes: la doc de producción seguía describiendo la
regla de T11 (retirada), y **R19 se incumplía por el camino sin contenedores**
—la sintética heredaba los m³ crudos y sacaba 306,00 € de incremento, total
1026,00—. La feature sigue `blocked` por F-043; `features.json` no se tocó y
T11 no se restauró.

### Bloques B, C y D · APROBADOS en la pasada 2 (2026-08-26)

`progress/review_F-036_bloques_BCD_pasada2.md`. La pasada 1 los RECHAZÓ por dos
bloqueantes; el ciclo de corrección (nueve commits `F-036 CR-*`) los cerró y el
reviewer lo verificó **reproduciendo el antes y el después con el builder real**,
sin usar los tests del implementer, y con un worktree desechable en el commit
anterior:

| Escenario | ANTES | AHORA |
|---|---|---|
| Base de residuos SIN contenedores calculables | sintética 6,0 UD, **306,00 €**, total 1026,00, sin revisión | sintética sin cantidad, **sin importe**, total 720,00, **en revisión** |
| 6 m³ / 12 m³ / 3 contenedores | 51 / 102 / 153 € | **idénticos** |

Lo que se aprendió, y vale para cualquier feature: **el mismo defecto puede
volver por otra rama del código**. El bloque C arregló que la sintética heredara
los m³ crudos; la corrección solo actuaba si el padre tenía `cantidad_convertida`,
así que el camino `residuos_sin_volumen_m3` seguía multiplicando por seis. Hoy en
residuos **no hay fallback**: si no se sabe el nº de contenedores, la línea sale
sin cantidad, con `residuos_sintetica_sin_cantidad` y en revisión. No se inventa.

**Confirmado por el reviewer con grep propio**: `ModifierContractMatcher` NO está
cableado en producción —nadie lo instancia ni lee su flag—, así que T19/R20 está
bien hecho pero **hoy no cambia ninguna valoración**. Cablearlo es F-004.

### Cuatro cambios requeridos que quedan vivos (ninguno de euros)

1. `services/albaranes-api/tests/test_f036_r14_ler_reexportado.py:5` sigue
   diciendo que el catálogo se movió «porque sv5 también los necesita (R13)».
   Una línea, y es la última mentira que queda de T11.
2. **La sintética muda**: con `modifier_source` distinto de `gestion_residuos` y
   padre de residuos sin contenedores, la línea sale con cantidad e importe a
   `None`, **sin razón y sin `review_required`**. No hay euros de más, pero es
   justo la línea muda que `RAZON_SIN_CANTIDAD` existe para evitar: la guarda
   está atada a `modifier_source` y no a «el padre es de residuos».
3. `_motivos_de` (`tests/test_f027_r18_r22_contrato.py`) debe **fallar a gritos**
   ante un `reasons.append(<expresión que no sabe resolver>)` en vez de saltárselo
   en silencio. Un analizador que alimenta una congelación y calla lo que no
   entiende es decorado.
4. `claves_dedupe` (`residuos_incrementos.py:146`) sigue llamando a
   `normalizar_ler` sobre texto libre: **el mismo defecto de la fecha leída como
   LER** que se acaba de corregir en `es_linea_incremento_ler`. `ler_creible` lo
   cierra.

**Añadir a T24 cuando se haga**: comprobar que ninguna línea real escribe el
incremento como `INCREMENTO 170802` —pegado y sin la palabra `LER`—, grafía que
antes casaba y que desde CR-3 devuelve `None` (medido por el reviewer).

### Los cuatro cambios requeridos, CERRADOS (2026-08-26, `CR-10`..`CR-13`)

`progress/impl_F-036_cambios_menores.md`. Ya no queda ninguno vivo:

- **CR-10**: la última mentira de T11 (docstring de `test_f036_r14_ler_reexportado`).
- **CR-11**: la sintética sin cantidad se explica por **el PADRE de residuos**, no
  por su `modifier_source`. Ya no hay línea muda.
- **CR-12**: el analizador que alimenta la congelación de motivos **revienta ante
  lo que no sabe leer** en vez de saltárselo. Un portero que calla lo que no
  entiende es decorado.
- **CR-13**: `claves_dedupe` deja de leer una fecha como código LER — el mismo
  defecto que CR-3 había corregido en la función de al lado.

`bash harness/init.sh` **exit 0**; raíz **556 passed** (eran 532), sv6 **185**.

**Estos cuatro NO tienen review propia**: el arnés admite dos ciclos y ya se
usaron (pasada 1 rechazó, pasada 2 aprobó). Los verificará el **reviewer final
de cierre**, junto con T23 y T24, cuando F-043 desbloquee la feature.

---

## F-043 · ARRANCADA (2026-08-26)

Rama `feature/F-043-clasificacion-por-ia1`, creada **desde la rama de F-036** y
no desde `dev`: F-043 toca sv2, sv3, sv5 y sv6, los mismos ficheros que F-036
tiene sin mergear, y dos ramas divergentes sobre ese código darían conflictos de
lógica, no de formato. Se cerrarán y mergearán en cadena.

Siguiente paso: `spec-author`. Y después, **PARADA OBLIGATORIA**: la spec pasa a
`spec_ready` y no se implementa una línea sin que el humano la apruebe.


---

## F-043 · Spec escrita (2026-08-26, spec-author)

`specs/F-043-clasificacion-por-ia1/` con `requirements.md` (34 requisitos EARS
+ 6 dudas), `design.md` y `tasks.md` (33 tareas). Topes de tamaño en verde
(150/150 y 250/250). NO se ha tocado código ni `harness/features.json`.

**Lo que decide la spec**, por si hace falta discutirlo antes de implementar:

1. `tipologia_resolver` se **borra** (con el enum `Tipologia`, las funciones de
   texto hormigón/mortero y el override por CIF). El determinismo queda en un
   `dict` familia → clave de prompt.
2. Si IA1 no clasifica: `generico` + confianza 0 + `origen='ausente'` + motivo
   de revisión. **Nunca** se reconstruye la familia por LER ni por texto.
3. La clasificación es de **DOCUMENTO** y viaja en `data.clasificacion`, no en
   `meta`: hoy `persistence_worker._sanear_envelope` de sv3 **descarta**
   `meta.tipologia`, y ése es el punto exacto donde se tira el dato.
4. Catálogo único en `ruesma_comun/contratos/familias.py` (definición, en qué
   se diferencia, señales, alcance y las dos claves de prompt por familia).
   `generico` tiene definición propia; la duda se expresa bajando la confianza.
5. Las puertas de familia de sv6 pasan a `familia_efectiva(línea, documento)`:
   una línea sin `tipo_familia` hereda la familia del documento **salvo** si el
   albarán es mixto. Eso es lo que devuelve SS-0003967 a 210,00 € y **desbloquea
   F-036** (su T24).

**DECISIONES ABIERTAS QUE NECESITA VALIDAR EL HUMANO** (las 6 dudas del final
de `requirements.md`, y la implementación no debe arrancar sin ellas):

1. ¿El catálogo arranca con solo 4 familias de documento (`generico`,
   `hormigon`, `mortero`, `residuos`), dejando `combustible`,
   `alquiler_maquinaria` y `bombeo` como familias de LÍNEA hasta que tengan
   prompt de fase 2 propio?
2. ¿`tipo_familia='otro'` es «genérico» o «ninguna familia con reglas»? Cambia
   si esa línea hereda o no.
3. Umbral de confianza baja: ¿60 %, y solo marca revisión sin bloquear?
4. Albarán mixto: la spec lo hace VISIBLE pero no re-ejecuta la fase 2 con un
   segundo prompt. ¿De acuerdo en dejarlo para otra feature?
5. ¿Backfill de los albaranes ya persistidos, o solo los nuevos?
6. Evals con LLM real: ¿cuántos casos y con qué proveedores autoriza? Se
   factura y es condición de cierre (ruta sensible).
