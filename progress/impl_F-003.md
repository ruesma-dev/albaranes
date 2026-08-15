<!-- progress/impl_F-003.md -->
# F-003 · Tanda 2 — Albaranes valorados, match estricto y coherencia · Informe de implementación

- Rama: `feature/F-003-valorados-match-estricto` (14 commits, uno por tarea
  más el de cierre de la campaña de mutación).
- Nivel de rigor: **estandar** (`harness/features.json`) → exige fase RED,
  cobertura del diff y campaña de mutación.
- Spec: `specs/F-003-valorados-match-estricto/` (R1–R15, design, tasks).
- **REGLA DURA RESPETADA: SIN DESPLIEGUE.** Cero `az`, cero `deploy.ps1`,
  cero `build_images.ps1`, cero secrets, cero Azure. Ningún test toca red,
  BBDD ni LLM.
- Trabajo hecho en un **worktree aislado** (`wt-f003`) para no tocar el árbol
  principal mientras el humano ejecutaba servicios en local. El árbol
  principal no se ha modificado.

## Qué cambió

La feature cierra el ciclo del importe impreso: **hasta ahora el importe de
línea no existía en el pipeline**. sv2 lo metía en `precio_neto` por orden
expresa del prompt («si no figura, calcula `cantidad*precio*(1 -
descuento/100)`») y sv5 lo volvía a multiplicar por la cantidad. Con 120,55 l
a 1,5877 €, los 191,40 € impresos se convertían en 23.073,60 €. Ahora el
importe se **transcribe**, se **persiste** y se **contrasta**.

### sv2 (`services/albaranes-api`) — transcribir, no recomponer

| Fichero | Qué hace ahora |
|---|---|
| `domain/models/albaran_models.py` | `LineaAlbaran` += `importe` (importe de línea impreso) y `descuentos` (lista, en el orden de las columnas). `CabeceraAlbaran` += `importe_total` e `importe_total_incluye_iva`. Todos opcionales: las extracciones anteriores siguen validando (R2). |
| `config/prompts.yaml` (**ruta sensible**) | **Desaparece** la instrucción de calcular `precio_neto` —la causa raíz del ×120—. Bloque nuevo «Albaranes que vienen valorados: transcribir, no recomponer»: cada valor por su etiqueta de columna, PROHIBIDO derivar unos de otros, null si no figura, y el ejemplo del ×120 explicado al modelo. `precio` solo de la columna de precio unitario; `precio_neto` solo si figura impreso; `descuentos` sin combinar. En cabecera, `importe_total` con la regla del IVA (R1). |

### sv3 (`services/albaranes-persistencia`) — persistir lo leído

| Fichero | Qué hace ahora |
|---|---|
| `domain/models/extraction_models.py` | Declara los cuatro campos nuevos. **Sin esto el envelope de sv2 rebotaría ENTERO**: los modelos de sv3 son `extra='forbid'`. El design no lo listaba; es la primera pieza sin la cual la feature no arranca. |
| `infrastructure/database/orm_models.py` | `_LineColumnsMixin` += `importe` (Float) y `descuentos_json` (Text); `_DocumentColumnsMixin` += `importe_total` (Float) e `importe_total_incluye_iva` (Boolean). Aplican a raw y merge a la vez. |
| `infrastructure/database/sqlalchemy_albaran_repository.py` | `ADD COLUMN IF NOT EXISTS` de las 4 columnas (raw + merge); mapeo extracción→ORM de los campos nuevos; `_dump_descuentos` (transcripción fiel; sin descuentos, NULL, nunca `[]`). |
| `infrastructure/database/schema_contribution.py` | Los mismos ALTER en la vista exportable del schema, que debe mantener paridad con el DDL vivo. |
| `application/services/descuento_cascada.py` (nuevo) | `descuento_efectivo` (`(1 − Π(1 − dᵢ/100)) × 100`, 4 decimales) y `resolver_descuento`: transcribir manda sobre calcular — solo se deriva con MÁS de una columna y sin descuento único leído (R3). |
| `application/services/albaran_confidence_service.py` | El merge de 3 proveedores propaga `importe`, `descuentos` y el total de cabecera. Van **fuera** de `_LINE_CONFIGS`/`_HEADER_CONFIGS` a propósito: son transcripción, no un campo puntuado; meterlos en el scoring movería los pesos de confianza de todo el histórico. La marca de IVA viaja con SU total (un total base con la marca del otro proveedor sería mentira). |

DDL: 4 columnas NUEVAS, ningún rename. **Lector acoplado avisado: sv5 hace
`SELECT importe` con SQL crudo** → orden de arranque sv3 antes que sv5 (ver
la nota de despliegue).

### sv5 (`services/albaran-valoracion-api`) — el contexto deja de recomponer

| Fichero | Qué hace ahora |
|---|---|
| `infrastructure/database/sqlalchemy_valuation_context_repository.py` | SELECT de líneas: `importe AS importe_leido` y `COALESCE(importe, <derivación de siempre>) AS importe_albaran` — lo transcrito manda y la derivación queda SOLO como fallback de las filas anteriores a F-003, que tendrán `importe` NULL para siempre. SELECT de cabecera: `importe_total` e `importe_total_incluye_iva`. `_opt_bool` distingue `False` («es base: exige cuadre») de `None` («no consta: solo avisa»). |
| `domain/ports/valuation_context_repository.py`, `domain/models/valuation_context.py`, `application/services/unit_category_prefilter.py`, `application/pipelines/value_albaran_pipeline.py` | Propagación de `importe_leido` por línea y del total al `meta` del envelope, por la misma vía que `fecha_albaran` — **en los dos puntos** donde se construye el meta, incluida la rama `no_contract` (R4). |
| `config/prompts.yaml` (**ruta sensible**) | `valuation_es`: la sección «No cases productos diferentes» gana la regla general de ATRIBUTO SUSTANTIVO (dimensión, modelo/referencia, tipo/material, formato de venta), los tres casos de referencia y la máxima «mejor línea nueva sin precio a revisión que un precio equivocado con apariencia de bueno». `conciliacion_es`: REGLA DURA DE ATRIBUTO SUSTANTIVO, al nivel de la regla dura de años (R9, R10). En ambos, la excepción tipográfica queda **explícita**: D-300 = D300 = DN300 = ø300, 0,5 = 0.5 = 0,50. |

### sv6 (`services/albaran-valoracion-persist`) — las redes deterministas

| Fichero | Qué hace ahora |
|---|---|
| `application/services/guard_aritmetico.py` (nuevo) | `verificar_linea` (R6): `precio × cantidad × (1 − dto) ≈ importe_leido`; si no cuadra, motivo `guard_aritmetico_linea:<calc>!=<leído>`. `verificar_total` (R7): con total BASE el descuadre exige revisión; con total CON IVA o sin marca, solo aviso `guard_aritmetico_total_con_iva`. `importe_efectivo_linea_unica` (R8, caso ORE OIL). Tolerancia: `IMPORTE_TOLERANCE_PCT`, la misma del `ImporteCalculator` — no se inventa umbral. |
| `application/services/atributo_sustantivo_guard.py` (nuevo) | `extraer_tokens_dimension` normaliza número + unidad a la unidad base de su categoría (longitud, superficie, volumen, masa, diámetro) y `sanear_matches_atributo_sustantivo` anula el match cuando ambas descripciones traen la MISMA magnitud con valores distintos. Se anulan los DOS precios (D6). Excluye hormigón, mortero y sintéticas (R11). |
| `application/services/valuation_builder.py` | (1) En `build()`, tras el saneo de años y antes de las pasadas: red de atributo sustantivo y caso ORE OIL, con un canal nuevo de motivos por línea. (2) En `_build_line`: el descuento solo entra en el importe si el precio final sale del albarán (R5) y el guard de línea fuerza revisión (R6). (3) `_build_header` pasa a método de instancia y aplica el guard de total sobre la suma de las líneas `from_albaran` (R7). `_build_synthetic_line` **no cambia**: la herencia del descuento del padre queda intacta (P1/D4). |
| `domain/models/valuation_envelope.py` | `importe_leido` por línea, `importe_total_albaran` e `importe_total_incluye_iva` en el meta. `extra='ignore'`: los sobres YA EN COLA validan y se valoran igual (R14). |
| `config/settings.py` + los DOS composition roots | `GUARD_ARITMETICO_ENABLED` y `RED_ATRIBUTO_SUSTANTIVO_ENABLED`, activos por defecto, cableados en `composition.py` (worker) **y** en `api/app.py` (HTTP): dejar uno sin cablear habría dado comportamientos distintos según la puerta de entrada (R13). |

`ruesma_comun`, sv1 y sv4 **no se han tocado**.

## Fase RED (obligatoria en nivel `estandar`)

Los tests se escribieron ANTES del código en las siete tareas con lógica.
Salidas reales de los fallos:

**T1 — schema de sv2** (`cd services/albaranes-api && python -m pytest tests/test_f003_schema_extraccion.py -q`):

```
E       cabecera.importe_total
E         Extra inputs are not permitted [type=extra_forbidden, input_value=191.4, input_type=float]
E       cabecera.importe_total_incluye_iva
E         Extra inputs are not permitted [type=extra_forbidden, input_value=False, input_type=bool]
E       lineas.0.descuentos
E         Extra inputs are not permitted [type=extra_forbidden, input_value=[0.0], input_type=list]
E       lineas.0.importe
E         Extra inputs are not permitted [type=extra_forbidden, input_value=191.4, input_type=float]
9 failed, 2 passed in 0.93s
```

**T2 — prompt de IA1** (`python -m pytest tests/test_f003_prompt_transcripcion.py -q`):

```
FAILED tests/test_f003_prompt_transcripcion.py::test_f003_r1_el_prompt_ya_no_manda_calcular_el_precio_neto
FAILED tests/test_f003_prompt_transcripcion.py::test_f003_r1_el_prompt_prohibe_derivar_unos_valores_de_otros
FAILED tests/test_f003_prompt_transcripcion.py::test_f003_r1_el_prompt_tiene_el_bloque_de_albaranes_valorados
FAILED tests/test_f003_prompt_transcripcion.py::test_f003_r1_importe_se_lee_de_la_columna_de_importe_de_linea
FAILED tests/test_f003_prompt_transcripcion.py::test_f003_r1_descuentos_se_transcriben_todos_y_en_orden
FAILED tests/test_f003_prompt_transcripcion.py::test_f003_r1_la_cabecera_pide_el_total_del_albaran
FAILED tests/test_f003_prompt_transcripcion.py::test_f003_r1_el_total_con_iva_se_transcribe_y_se_marca
10 failed, 2 passed in 0.31s
```

**T3 — sv3** (`cd services/albaranes-persistencia && python -m pytest tests/test_f003_descuento_cascada.py tests/test_f003_mapeo_campos_leidos.py -q`):

```
tests\test_f003_descuento_cascada.py:17: in <module>
    from application.services.descuento_cascada import (
E   ModuleNotFoundError: No module named 'application.services.descuento_cascada'
```

y, con el módulo ya creado, el resto del mapeo todavía sin tocar:

```
FAILED tests/test_f003_mapeo_campos_leidos.py::test_f003_r3_el_envelope_con_campos_nuevos_valida_en_sv3
FAILED tests/test_f003_mapeo_campos_leidos.py::test_f003_r3_el_ddl_anade_la_columna[albaran_lines-importe-DOUBLE PRECISION]
FAILED tests/test_f003_mapeo_campos_leidos.py::test_f003_r3_el_merge_conserva_el_importe_leido
FAILED tests/test_f003_mapeo_campos_leidos.py::test_f003_r3_la_fila_deriva_el_descuento_efectivo_en_cascada
FAILED tests/test_f003_mapeo_campos_leidos.py::test_f003_r3_el_importe_leido_manda_en_la_coherencia
24 failed, 2 passed in 1.65s
```

**T4 — contexto de sv5** (`cd services/albaran-valoracion-api && python -m pytest tests -q`):

```
E       TypeError: ValuationContextRaw.__init__() got an unexpected keyword argument 'importe_total_albaran'
FAILED tests/test_f003_contexto_importe.py::test_f003_r4_el_select_de_lineas_lee_la_columna_importe
FAILED tests/test_f003_contexto_importe.py::test_f003_r4_el_importe_efectivo_prefiere_el_leido
FAILED tests/test_f003_contexto_importe.py::test_f003_r4_la_fila_con_importe_leido_lo_expone
FAILED tests/test_f003_contexto_importe.py::test_f003_r4_el_meta_lleva_el_total_del_albaran
11 failed, 1 passed in 1.10s
```

**T5 — DTOs y flags de sv6** (`cd services/albaran-valoracion-persist && python -m pytest tests -q`):

```
>       assert builder._guard_aritmetico_enabled is True
E       AttributeError: 'ValuationBuilder' object has no attribute '_guard_aritmetico_enabled'
FAILED tests/test_f003_sobres_antiguos.py::test_f003_r14_la_linea_de_contexto_valida_sin_importe_leido
FAILED tests/test_f003_sobres_antiguos.py::test_f003_r14_el_meta_valida_sin_el_total_del_albaran
FAILED tests/test_f003_sobres_antiguos.py::test_f003_r13_los_flags_vienen_activos_por_defecto
8 failed, 3 passed in 0.73s
```

(los 3 que ya pasaban son la línea base de regresión: el builder valoraba
sobres antiguos sin error antes y después.)

**T6 — descuento y precio de contrato** (`python -m pytest tests/test_f003_dto_no_contrato.py -q`):

```
        assert record.precio_unitario_source == "pdf_inference"
>       assert record.importe_calculado == pytest.approx(100.0)
E       assert 80.0 == 100.0 ± 1.0e-04
E         Obtained: 80.0
E         Expected: 100.0 ± 1.0e-04
FAILED tests/test_f003_dto_no_contrato.py::test_f003_r5_precio_de_contrato_no_recibe_el_descuento
FAILED tests/test_f003_dto_no_contrato.py::test_f003_r5_queda_el_motivo_de_auditoria
FAILED tests/test_f003_dto_no_contrato.py::test_f003_r5_el_precio_inferido_del_pdf_tampoco_recibe_descuento
3 failed, 5 passed in 0.55s
```

Ese `80.0` es exactamente el bug: el descuento del albarán aplicado sobre un
precio de contrato.

**T7 — guard aritmético** (`python -m pytest tests/test_f003_guard_aritmetico.py -q`):

```
tests\test_f003_guard_aritmetico.py:21: in <module>
    from application.services.guard_aritmetico import (
E   ModuleNotFoundError: No module named 'application.services.guard_aritmetico'
```

**T8 — red de atributo sustantivo** (`python -m pytest tests/test_f003_atributo_sustantivo.py -q`):

```
tests\test_f003_atributo_sustantivo.py:19: in <module>
    from application.services.atributo_sustantivo_guard import (
E   ModuleNotFoundError: No module named 'application.services.atributo_sustantivo_guard'
```

**T9 — prompts de IA3/IA4** (`cd services/albaran-valoracion-api && python -m pytest tests/test_f003_prompts_match_estricto.py -q`):

```
FAILED tests/test_f003_prompts_match_estricto.py::test_f003_r9_ia3_tiene_la_regla_de_atributo_sustantivo
FAILED tests/test_f003_prompts_match_estricto.py::test_f003_r9_ia3_trae_el_caso_de_los_ladrillos
FAILED tests/test_f003_prompts_match_estricto.py::test_f003_r9_ia3_conserva_la_excepcion_tipografica
FAILED tests/test_f003_prompts_match_estricto.py::test_f003_r10_ia4_tiene_la_regla_dura_de_atributo
FAILED tests/test_f003_prompts_match_estricto.py::test_f003_r10_ia4_trae_los_casos_de_referencia
9 failed, 5 passed in 0.22s
```

## Decisiones de diseño y desviaciones (todas justificadas)

1. **`_is_line_net_consistent` de sv3 comparaba peras con manzanas
   (desviación).** El design no la mencionaba, pero medía
   `cantidad × precio × (1 − dto)` contra `precio_neto`, que es un precio
   **UNITARIO**. Esa comparación solo tenía sentido mientras el prompt
   ORDENABA meter el importe total en `precio_neto` — o sea, mientras durase
   el bug que esta feature elimina. Dejarla habría marcado como incoherente
   cada línea con precio neto impreso de verdad. Ahora contrasta contra el
   `importe` leído si existe, y unitario contra unitario si no.
2. **Los modelos de extracción de sv3 (desviación de alcance).** El design
   listaba ORM, DDL y servicios, pero no `extraction_models.py`. Son
   `extra='forbid'`: sin declarar los campos, el primer envelope de sv2 con
   `importe` habría rebotado entero y la feature habría roto el pipeline en
   vez de arreglarlo.
3. **Los campos transcritos NO entran en el scoring de confianza.** Añadir
   `importe` a `_LINE_CONFIGS` habría cambiado los pesos y, con ellos, los
   porcentajes de confianza de todas las líneas. Se propagan con el mismo
   orden de precedencia por proveedor, pero fuera del cálculo.
4. **Un importe leído de 0 cuenta como AUSENTE** (lo destapó la mutación).
   Es la convención que ya seguían `ImporteCalculator`
   (`importe_declarado_cero_ignorado`) y `PriceReconciler` (`_no_cero`): una
   celda vacía que el OCR devuelve como cero no puede mandar una línea a
   revisión.
5. **R12: el `origen` de la derivada depende de si el albarán trae partida.**
   El requisito nombra `nueva_no_match`, pero el mecanismo que ya existía
   produce `no_ia_match` cuando la línea del albarán trae partida impresa (la
   derivada se crea en ESA partida) y `nueva_no_match` cuando no la trae. Los
   dos caminos acaban donde pide §10.5 —línea nueva, sin precio, a revisión—
   y **ambos tienen test**. No se ha tocado el `partida_matcher` para forzar
   un literal.
6. **La tolerancia del guard es `IMPORTE_TOLERANCE_PCT`**, la misma que ya
   usaba el `ImporteCalculator` para comparar esos mismos importes. El
   builder la recibe por constructor; no hay umbral nuevo que calibrar.
7. **`_build_header` pasa de `@staticmethod` a método de instancia**: el
   guard de total necesita el flag y la tolerancia. Cambio mecánico, única
   llamada ya era `self._build_header(...)`.

## Tests: qué se comprueba

- **sv2, 79 tests** (+23 de F-003): schema con los campos nuevos y
  retrocompatibilidad, y las reglas R1 leídas del `prompts.yaml` **real**
  (incluida la comprobación de que la fórmula del ×120 ha desaparecido).
- **sv3, 135 tests** (+47): cascada de descuentos, mapeo a fila ORM en raw y
  merge, DDL idempotente de las 4 columnas, merge de 3 proveedores y
  coherencia de línea con la semántica nueva.
- **sv5, 44 tests** (nuevos, directorio creado): SQL del contexto, fila→DTO,
  marca de IVA, propagación al meta en las dos ramas del envelope, y los
  prompts de IA3/IA4 leídos del YAML real.
- **sv6, 88 tests** (nuevos, directorio creado): caso ×120, ORE OIL, guard de
  total con y sin IVA, sintéticas que no suman, R5 con sus regresiones,
  herencia del descuento del padre, red de atributo sustantivo con sus
  exclusiones y sus falsos positivos, los dos flags y los sobres antiguos.
- Ninguno toca red, BBDD ni LLM.

## Evidencias

| Evidencia | Valor |
|---|---|
| **Tests ejecutados** | **242** raíz + **79** sv2 + **135** sv3 + **44** sv5 + **88** sv6 + comun (19 + 3 skips) — **todos en verde, 0 fallos** |
| **Tiempo de las suites** | raíz 26,8 s · sv2 1,3 s · sv3 4,2 s · sv5 2,2 s · sv6 2,2 s |
| **Cobertura de líneas cambiadas** | **96,6 %** (259/268), umbral 80 % → `PUERTA COBERTURA` en verde |
| **Mutación** | **87 mutantes, 84 muertos, 3 supervivientes, 0 timeouts, 32,3 s** (`python -m harness.mutacion --feature F-003 --workers 8`) → `progress/mutacion_F-003.md` |
| **Supervivientes analizados** | 3/3, los tres **equivalentes**; ninguna sección en PENDIENTE |
| **Puerta de rutas sensibles** | AVISO (esperado, ver abajo) |
| `bash harness/init.sh` | **ENTORNO LISTO** |

### Campaña de mutación: de 21 supervivientes a 3

La primera pasada dejó **21**. **18 eran huecos reales** y se cazaron
escribiendo los tests que faltaban: la marca de IVA leída como texto
(`'false'` no puede degradarse a `None`), la red sin línea de albarán o sin
línea de contrato, la razón de la IA conservada y recortada a 500 caracteres,
el redondeo de los motivos a 2 decimales (los lee un humano en el portal),
los límites **inclusivos** de las tres tolerancias, el descuento fuera de
rango y el del 100 %, una línea del lote sin contexto, una línea limpia que
NO debe ir a revisión, y los descuadres **moderados** de coherencia — los
astronómicos pasaban con cualquier tolerancia, que era justo el punto ciego.

Dos de esos huecos apuntaban a código y no a tests, y se corrigieron
(decisión 4 de arriba, y la retirada de la rama `0 contra 0` del comparador,
redundante con el `1e-9` del denominador).

Los **3 supervivientes restantes están analizados uno a uno** en
`progress/mutacion_F-003.md` y **los tres son equivalentes**: una guarda
defensiva cuyo cuerpo tolera `None` igualmente, una comparación cuyo cuerpo
asigna el mismo valor que ya tenía, y `ensure_ascii` sobre una lista de
números (donde no puede haber un carácter no ASCII).

### Puerta de rutas sensibles: AVISO (salida esperada)

Esta feature toca **8 rutas sensibles** (los dos `prompts.yaml`, los schemas
de sv2/sv5, el envelope y las tres redes de sv6). La puerta pide la pasada
completa de evals. Salida real de
`python -m evals.runner --con-llm --feature F-003`:

```
no se puede lanzar la pasada completa: faltan en el entorno GEMINI_API_KEY, OPENAI_API_KEY. No se ha consumido ningún caso.
```

(el arnés corre con `REQUIERE_ENV=0`, sin `.env` global). En modo
determinista sí genera informe:

```
NO_EVALUABLE · informe en progress/evals_F-003.md
VEREDICTO: NO_EVALUABLE
Motivo: no hay ningún caso en evals/fixtures/inputs/
```

Es **la salida esperada** mientras los libros de `evals/ground_truth/` estén
vacíos (decisión D5 de F-011): la puerta está declarada en `aviso` justo por
esto y **no bloquea**. Igual que en F-002.

## Nota de despliegue (nada de esto se ha ejecutado)

**Cuatro imágenes a reconstruir: sv2, sv3, sv5 y sv6.**

**ORDEN OBLIGATORIO: sv3 → sv5 → sv6.** sv5 empieza a hacer `SELECT importe`,
`importe_total` e `importe_total_incluye_iva` con SQL crudo sobre tablas
cuyas columnas crea sv3 al arrancar. Arrancar sv5 antes que sv3 lo rompe en
runtime, sin aviso de compilación (regla 3 de `docs/ARCHITECTURE.md`). En
local sv3 arranca primero de todos modos.

Variables nuevas: ninguna obligatoria. Los dos flags de sv6
(`GUARD_ARITMETICO_ENABLED`, `RED_ATRIBUTO_SUSTANTIVO_ENABLED`) vienen
activos por defecto; solo hay que declararlos si se quiere apagar alguno.
**Ningún secreto nuevo.** `azure-apps/albaranes.md` no cambia: no varía nada
de lo que este proyecto expone o consume hacia otros.

Datos históricos: las filas anteriores tendrán `importe` e `importe_total`
NULL para siempre. Los guards no actúan sobre ellas y la valoración se
comporta como antes. No se re-extrae nada retroactivamente.

## Verificaciones MANUAL del humano (T13) — todas en LOCAL

Pipeline local con Azurite (`infra/docs/levantar-pipeline-local.md`) y PG
local. Arrancar **sv3 primero**.

1. **Las columnas nuevas existen.** Tras arrancar sv3:
   ```sql
   \d albaran_lines_merge
   \d albaran_documents_merge
   ```
   Esperado: `importe` (double precision) y `descuentos_json` (text) en las
   líneas; `importe_total` (double precision) e `importe_total_incluye_iva`
   (boolean) en los documentos. Comprobar también las tablas raw
   (`albaran_lines`, `albaran_documents`) y **volver a arrancar sv3** para
   confirmar que el DDL es idempotente.

2. **Caso ×120.** Reprocesar el albarán de gasóleo (120,55 l a 1,5877 € con
   importe impreso 191,40 €):
   ```sql
   SELECT cantidad, precio, descuento, descuentos_json, precio_neto, importe
   FROM albaran_lines_merge WHERE document_id = '<id>';
   ```
   Esperado: `importe` = 191,40 · `precio_neto` **NULL** (ya no se calcula).
   Y en la valoración:
   ```sql
   SELECT importe_calculado, importe_source, review_required, review_reasons_json
   FROM albaran_line_valuations WHERE ...;
   ```
   Esperado: **191,40**, `importe_source='declared_albaran'`, y **en ningún
   caso 23.073,60**. Este es el punto que motivó la feature.

3. **Caso ORE OIL.** Albarán de una sola línea sin importe de línea impreso y
   con total (base) en la cabecera. Esperado: el importe de la línea = total
   del documento, con `importe_desde_total_documento` en los motivos.

4. **Total con IVA.** Un albarán cuyo único total impreso lleve IVA. Esperado:
   `importe_total_incluye_iva = true` en la cabecera y, si la suma no cuadra,
   `guard_aritmetico_total_con_iva:...` como **aviso** — la valoración NO
   debe quedar en revisión solo por eso.

5. **CETOSA / elemento base 0,5 mm.** Albarán con un producto cuyo espesor o
   modelo no coincide con la línea de contrato. Esperado: línea **NUEVA sin
   precio**, `match_method='no_match'`, `review_required=true` y el motivo
   `atributo_sustantivo_mismatch:...`. Contraprueba: un albarán que sí casa
   (D-300 contra D300) debe seguir casando con su precio.

6. **Descuento contra precio de contrato (R5).** Una línea con descuento en
   el albarán y sin precio propio, casada con contrato. Esperado: importe =
   `cantidad × precio_contrato` **sin** aplicar el descuento, y el motivo
   `descuento_albaran_no_aplicado_a_precio_contrato`. Contraprueba: con
   precio del albarán, el descuento SÍ se aplica.

Pegar los resultados en este mismo fichero.

## Qué queda fuera / qué falta

- **Fuera de alcance por la spec**: `ruesma_comun` (tocarlo obliga a
  reconstruir 4 imágenes), sv1, sv4 (mostrar `importe` e `importe_total` en el
  portal es feature futura si el humano la quiere), `price_reconciler.py` e
  `importe_calculator.py` (su precedencia «lo leído manda» ya era la que G3
  exige), `partida_matcher.py`, la copia muerta
  `config/prompts/svc5_prompt_valuation_es.yaml` (hay test de que no se toca)
  y el prompt de fase 2 de sv2 (hereda la fase 1 por placeholder).
- **Límite consciente de la red R11 (D5)**: solo detecta atributos
  **numéricos con unidad**. Los modelos y nombres no numéricos (ladrillos
  CETOSA, «BOLSA DE CUÑAS») dependen del prompt y, si falla, del revisor. Una
  red de similitud textual daría falsos positivos (D-300 vs D300). Los evals
  de F-011 medirán si el prompt basta.
- **Falta (del humano)**: las 6 verificaciones MANUAL de arriba; el
  despliegue con el orden sv3 → sv5 → sv6; y **rellenar los casos de esta
  feature en los libros de `evals/ground_truth/`** (R15): ×120 y ORE OIL en
  `IA1_extraccion.xlsx` (con `importe`, `descuentos` e `importe_total`),
  CETOSA / elemento base 0,5 mm / bolsa de cuñas en `IA3_valoracion.xlsx` e
  `IA4_conciliacion.xlsx` (esperado: **no casar**), y sus entradas en
  `INPUTS.xlsx`. Sin casos, el runner no puede dar más que NO_EVALUABLE.
- **Hallazgo lateral 1**: el `.gitignore` de sv6 ignora `*.example`, así que
  su `.env.example` con los flags nuevos **está en disco pero no entra en
  git** — mismo descuido que F-002 encontró en sv2. No lo he cambiado por mi
  cuenta.
- **Hallazgo lateral 2**: los clientes OCR opcionales de sv2
  (`azure_document_intelligence_client.py`, `google_document_ai_client.py`,
  ambos **desactivados por defecto**) mapean `LineAmount`/`TotalPrice` a
  `precio_neto`, que es la MISMA confusión importe/unitario que causó el
  ×120. No están en el alcance de la spec y no se han tocado; si alguna vez
  se activan, hay que mapearlos a `importe` antes.
