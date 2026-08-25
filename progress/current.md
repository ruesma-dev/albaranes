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

Siguiente: bloque B (T8-T13, `comun` + sv3 + sv5 + el orden de prioridades de sv6).
