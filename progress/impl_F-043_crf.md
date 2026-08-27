<!-- progress/impl_F-043_crf.md -->
# F-043 · CAMBIOS REQUERIDOS de la review final — informe del implementer

Rama `feature/F-043-clasificacion-por-ia1`, rigor `critico`. Encargo:
`progress/review_F-043_final.md` (CHANGES_REQUESTED, 4 bloqueantes + 2 menores).
**Los seis, aplicados.** Sin tareas nuevas y sin `git push` en ningún repo.
Commits: `57ffe7c` CRF-1 · `fa46264` CRF-2 · `ba16dbc` CRF-3 · `c7a82db` CRF-5 ·
`65ca6d0` imports — y **`43196b1` en OTRO repo**, `…/azure-apps` (CRF-4).

## 1 · Qué cambió, CR a CR

| CR | Fichero | Qué |
|---|---|---|
| 1 | `…albaranes-api/application/services/albaran_extraction_service.py` + `tests/test_f043_prompt_fase2.py` (**nuevo**, 5 tests) | el task de fase 1 se renderiza en UN sitio por el que pasan las dos fases; el genérico de marcadores colgantes y las dos fugas concretas |
| 2 | `…albaranes-api/tests/test_f043_r17_documento_y_linea.py` (**nuevo**, 6 tests) | R17, sus dos mitades |
| 3 | `specs/F-043-…/tasks.md` | T31 reescrita: cinco pasos y criterio de verde honesto |
| 4 | `azure-apps/albaranes.md` | las seis columnas `tipologia*` y su índice |
| 5 | `progress/current.md` y `specs/F-043-…/requirements.md` | las cuatro MANUAL con su comando y su verde; R27 acotado por R24 |

**Cero cambios de comportamiento fuera de CRF-1**, y ninguna regla determinista
nueva: CRF-1 sustituye marcadores en un prompt, no decide sobre la familia. La
prohibición del humano sigue intacta.

## 2 · CRF-1 (BLOQUEANTE) · el catálogo no llegaba a IA2

`review_phase_2` metía el task de fase 1 **en crudo** dentro de
`{prompt_fase_1}` vía `_build_instructions(prompt_fase_1_spec)`; el renderizado
vivía dentro de `extract_phase_1`, así que **solo** la fase 1 lo veía.

### 2.1 · Fase RED — la traza, tal cual

Test escrito ANTES del arreglo. Comando exacto:

```
$ cd services/albaranes-api && python -m pytest tests/test_f043_prompt_fase2.py -q --tb=line

F                                                                        [100%]
E   AssertionError: albaran_revision_fase2_es deja marcadores sin sustituir: ['{catalogo_familias}', '{obras_activas}']
    assert not ['{catalogo_familias}', '{obras_activas}']
…tests/test_f043_prompt_fase2.py:138: AssertionError
FAILED …::test_f043_r16_las_instructions_de_fase2_no_llevan_marcadores_colgantes
1 failed in 0.72s
```

Con los cinco del fichero: **`5 failed in 0.75s`** — el genérico de arriba, los
dos de catálogo (`…el_catalogo_de_familias_llega_entero_a_fase2`,
`…fase2_ve_las_cuatro_familias_de_documento_con_su_texto`) y los dos de obras
(`test_f002_r1_…`, `test_f002_r2_…`). **El genérico es el que importa**: no
comprueba *un* marcador sino que no queda **ninguno**, así que atrapa el que aún
no existe. Regex `\{[a-z][a-z0-9_]*\}`: los ejemplos JSON llevan llaves, pero
con comillas dentro, y no casan.

### 2.2 · GREEN — el arreglo

El renderizado del task de fase 1 se saca a `_render_task_fase_1(task)`, que
sustituye `{obras_activas}` **y** `{catalogo_familias}`, y lo llaman las DOS
fases. Se **retira** `_build_instructions`: su único llamante era el origen de
la fuga, y una función que compone un prompt a medio renderizar solo puede
volver a usarse mal. `grep` en los seis servicios: cero usos restantes en sv2;
la copia de sv5 es otro servicio y su `prompts.yaml` no tiene esos marcadores.
Resultado: `tests/test_f043_prompt_fase2.py` → **5 passed in 0.77s**; la suite
de sv2 entera → **150 passed in 2.85s** (139 antes).

### 2.3 · La medida de `{obras_activas}` (hallazgo 9): **SÍ queda arreglado**

Los CUATRO prompts de fase 2, con el `prompts.yaml` REAL y dos obras de fixture.
El «ANTES» no es memoria: se midió reinyectando el código anterior y revirtiendo.

| prompt de fase 2 | chars ANTES | colgantes ANTES | chars AHORA | colgantes AHORA | catálogo | obras |
|---|---:|---:|---:|---:|:--:|:--:|
| `albaran_revision_fase2_es`       | 15 945 | 2 | 19 368 | **0** | SÍ | SÍ |
| `albaran_revision_fase2_hormigon` | 17 690 | 2 | 21 113 | **0** | SÍ | SÍ |
| `albaran_revision_fase2_mortero`  | 15 324 | 2 | 18 747 | **0** | SÍ | SÍ |
| `albaran_revision_fase2_residuos` | 18 760 | 2 | 22 183 | **0** | SÍ | SÍ |

Los 2 colgantes de «ANTES» son, en los cuatro,
`['{catalogo_familias}', '{obras_activas}']`. Ahora entran **3 102 caracteres**
de catálogo más el bloque de obras. La fuga de `{obras_activas}`, **previa a
F-043** (viene de F-002), queda cerrada por el mismo arreglo y con sus dos tests
propios: ni a medias ni como trabajo aparte.

### 2.4 · Mutación de lo cambiado — inyectada, no en campaña

`harness.mutacion.generar_mutantes` sobre las **67 líneas añadidas** en
`albaran_extraction_service.py` devuelve **0 mutantes**: el código añadido no
tiene ningún operador de los que muta (comparaciones, aritmética, booleanos,
`not`, enteros). Lo que sí tiene es `in`, y **`ast.In`/`ast.NotIn` no están en
su tabla `COMPARACIONES`** (propuesta en §5). Así que **tres mutantes a mano**,
uno a uno y revertidos:

| # | Mutante | Resultado |
|---|---|---|
| 1 | `review_phase_2` vuelve a embeber `prompt_fase_1_spec.task` sin renderizar (el bug exacto) | **5 failed**, los cinco de fase 2 |
| 2 | `_render_task_fase_1` devuelve `task` sin `_render_catalogo_familias` | **7 failed** (4 de fase 1 + 3 de fase 2) |
| 3 | `if "{obras_activas}" in task:` → `not in` | **9 failed** (6 de F-002 + 3 de fase 2) |

Cero supervivientes. Tras revertir: `150 passed in 2.25s`.

## 3 · CRF-2 (BLOQUEANTE) · R17 con test trazable

`tests/test_f043_r17_documento_y_linea.py`, 6 tests, las **dos mitades**:

- **La clasificación es del DOCUMENTO**: `clasificacion` está en
  `DocumentoAlbaran.model_fields` y **no** en `LineaAlbaran`; una línea que la
  traiga no valida (`extra='forbid'`); y el **JSON Schema** que ve el LLM la
  ofrece solo a nivel documento, que es lo que gobierna dónde la rellena la IA.
- **La fase 2 SIGUE rellenando `contexto_linea.tipo_familia`**: el campo sigue
  declarado, las dos cosas conviven en un `documento_revisado` real (una línea
  con `tipo_familia='residuos'` y otra de portes sin familia propia), y los
  **prompts de familia** siguen mandando rellenarlo por texto.

**Aquí NO hay fase RED, y se dice por qué**: R17 no era código que faltara sino
la prueba que faltaba. Un RED artificial habría exigido romper producción para
enseñar el rojo. En su lugar, **tres inyecciones** revertidas que miden que el
test tiene dientes:

| # | Inyección | Resultado |
|---|---|---|
| 1 | `clasificacion` declarada TAMBIÉN en `LineaAlbaran` | **2 failed** (`…la_linea_no_declara_clasificacion_propia`, `…el_json_schema_pone_la_clasificacion_solo_en_el_documento`) |
| 2 | `LineaAlbaran` pierde `contexto_linea` | **2 failed** (`…la_linea_conserva_su_tipo_familia`, `…fase2_devuelve_las_dos_cosas_a_la_vez`) |
| 3 | `prompts.yaml`: `tipo_familia` → `tipo_de_familia` | **1 failed** (`…los_prompts_de_fase2_siguen_pidiendo_el_contexto_de_linea`) |

`grep test_f043_r17` daba **0** nombres y ahora da **6**.

## 4 · CRF-3, CRF-4 y CRF-5

**CRF-3 · T31.** Reescrita con la vía REAL en cinco pasos ejecutables desde
PowerShell tal cual, con los scripts que **ya existen** en sv2 (`seed_input.py`
y `encolar_extraccion.py`; verificado que el publicador importa y construye el
`MensajeExtraccion` — no se publicó nada, Azurite no está levantado). Arregla
las dos cosas: (a) hay que **re-extraer**, porque revalorar publica
`q-valoracion` y deja las seis columnas a NULL; (b) el verde honesto es
**`total_lines = 2`, `review_required = true` y `total_valorado = 90.00`**, no
210,00 €. **No se ablanda**: se dice que 90,00 € es el número con el match real
de IA3, por qué sigue siendo un avance (de 540,00 € de más *en silencio* a
90,00 € de menos *pidiendo revisión*), que los 210,00 € dependen de **T30**, y
qué **NO** es verde: `tipologia` a NULL o `total_lines = 1` con 540/720. El SQL
usa columnas comprobadas contra el DDL real de sv3 y sv6.

**CRF-4 · `azure-apps/albaranes.md`.** Bullet «Añadidas por sv3 (F-043, ALTER
idempotente)» junto al de sv4, con las **seis columnas y sus tipos exactos**
(`VARCHAR(32)`, `DOUBLE PRECISION`, `TEXT`, `VARCHAR(16)`, `BOOLEAN`, `TEXT`),
el índice `ix_albaran_documents_merge_tipologia`, el porqué de que todas sean
nullable y el aviso de lectores acoplados (sv5 SQL crudo, sv4 ORM, DDL de sv3).
Los tipos salen de `phase2_ddl.py`, no de memoria. **Commit local `43196b1` ahí,
sin push.** Barrido de secretos sobre su diff (`password|secret|token|api_key|
Bearer|AccountKey|subscription|tenant|pwd=|sk-`, IPv4, GUID, correos): **sin
coincidencias**.

**CRF-5 · menores.** (5) Las cuatro MANUAL —T28, T30, T31, T32— ya no están solo
nombradas en `current.md`: llevan comando y criterio de verde, más los avisos
dispersos (que `--feature F-043` arrastra F-036 entera, que T30 se factura y hoy
daría `NO_EVALUABLE`, los tres motivos nuevos de sv4 por su nombre); el detalle
largo de T31 se **enlaza** a `tasks.md` en vez de duplicarse mal. (6) R27
acotado: «…deben comportarse como hoy, **SALVO la elección del prompt de
valoración, que R24 retira**: se usa el genérico configurado». **El código NO se
toca**: la contradicción era de la spec y la decisión ya estaba tomada y
probada. `requirements.md` estaba clavado en 150/150, así que el aire salió de
comprimir su cabecera sin perder contenido; y de paso se corrigió la
consecuencia para T31 de la decisión 5 («revalorarlo a mano»), justo lo que la
review demostró que no basta.

## 5 · Fuera de alcance, y lo que propongo sin implementar

- **Observaciones 7 y 8 de la review**: no son encargo mío y **no las he
  tocado**. La 8 (orden de despliegue: sv3 antes que sv5/sv4) sí queda escrita
  **en `azure-apps/albaranes.md`**, que existe para decir qué se rompe si cambia
  una tabla compartida; **no** he tocado la regla 14 de `docs/ARCHITECTURE.md`,
  que es lo que proponía la review y sigue pendiente del humano.
- **Automejora del arnés, propuesta y NO aplicada**: `harness/mutacion.py` no
  muta `in`/`not in` (faltan `ast.In`/`ast.NotIn` en `COMPARACIONES`). Por eso
  este cambio da **0 mutantes** pese a tener una condición que, invertida, rompe
  nueve tests. Es genérica: habría que portarla a `arnes-base` en el mismo
  trabajo, así que no la hago por mi cuenta.
- **T28, T30, T31 y T32 siguen sin hacer**: son del humano. **T28 hay que
  rehacerla** tras estos commits (el árbol cambió) y cierra el `[~]` de RM1.
  `progress/review_F-043_final.md` estaba sin versionar: entra con este informe.

## 6 · Evidencias

| Evidencia | Valor |
|---|---|
| **Tests ejecutados** — raíz | **556 passed**, 0 failed (`bash harness/init.sh`) |
| **Tests ejecutados** — sv2 | **150 passed** (139 antes: **+11** de esta ronda) |
| sv3 · sv4 · sv5 · sv6 · comun | 169 · 157 · 43 · 212 · 118+3skip — **sin tocar**; `init.sh` los sirvió por caché (árbol sin cambios) |
| **Cobertura de líneas cambiadas** | **98,9 %** — 604/611, umbral 80 %, nivel `critico` (línea `PUERTA COBERTURA`) |
| **Mutantes generados** (67 líneas añadidas) | **0** — la herramienta no muta `in`/`not in`; ver §2.4 |
| **Mutantes inyectados a mano** | **6** (3 en CRF-1, 3 en CRF-2), **0 supervivientes**, todos revertidos |
| **Tiempo de la suite** | raíz **142,52 s**; sv2 **8,32 s** en `init.sh` (2,25 s en frío) |
| **`ruff`** | **1138**, los mismos de antes: **cero avisos nuevos** (nota abajo) |
| **Tamaño del papeleo** | `PUERTA TAMAÑO [OK]` — requirements 150/150, design 250/250 |

> **Nota sobre `ruff`.** Una corrida intermedia de `init.sh` marcó **1140**: eran
> 2 `I001` de mis ficheros nuevos. Corregidos en `65ca6d0`, y el portero final
> vuelve a imprimir **1138**. sv2 trata `application`/`domain` como first-party
> y la raíz no, así que gana la raíz — la config que cuenta el portero y la que
> ya seguía `test_f043_schema_sv2_documento.py` (bloque A).

**La mutación completa sigue siendo T28**, del humano: no se lanzó aquí a
propósito (es cara y muta el árbol). Lo de arriba es inyección dirigida.

## 7 · `bash harness/init.sh` — resultado real

Corrida FINAL, con todo commiteado y el árbol limpio:
```
ENTORNO LISTO. Puedes trabajar.        [exited with code 0]
[AVISO] ruff: 1138 avisos (deuda previa, no bloquea)
[OK] pytest en verde (con medición de cobertura)   556 passed in 142.52s
[OK] servicio sv2-api: pytest en verde (caché: árbol sin cambios desde el último verde)
[OK] PUERTA COBERTURA: 98.9% de 611 líneas cambiadas cubiertas (604/611, umbral 80%, critico)
[OK] PUERTA TAMAÑO: F-043 dentro de los topes (requirements 150/150, design 250/250)
[AVISO] PUERTA RUTAS SENSIBLES [evals]: falta la evidencia de 13 ruta(s) sensible(s)  → es T30
[OK] Rama actual: feature/F-043-clasificacion-por-ia1
```

sv2 sale por caché **en esta última** porque su árbol no cambió desde el verde
anterior; sus **150 passed in 8.32 s** los midió la corrida previa (2,25 s fuera
del portero). Los avisos son los de siempre: rutas sensibles (evidencia =
**T30**), F-036 `blocked`, sv1 sin tests, `infra` sin comando de tests y
`[ADAPTAR]` en dos specs ajenas.
