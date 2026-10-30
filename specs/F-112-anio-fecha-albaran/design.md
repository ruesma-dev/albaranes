# F-112 · El año del albarán se lee con la fecha del correo como referencia · Diseño (v1.1)

Servicio: **sv2**. Sin DDL, sin cambios en `ruesma_comun`, sin cambios de contrato entre servicios. Medición de
partida y detalle de la lectura en `progress/spec_F-112.md`. Decisiones abiertas (PARADA 1) en §9.

**Enmienda v1.1 (2026-10-30).** El humano: «añade que ia2 revisara tambien la fecha. el problema vendra cuando
estemos en un cambio de año (diciembre o enero)». Efecto: IA2 revisa la fecha en una sección propia de sus cuatro
prompts (§4.2, sustituye a la regla de checklist de la v1); la Regla del año (requirements, glosario) entra en los dos
bloques; el comparador mide aparte el efecto de IA2 y gana el juego D sintético (§7); riesgo nuevo en §9. D7 = 416
llamadas (decidida); D8 la cierra el líder leyendo los 19 en Blob.

## 1. Qué pasa hoy (leído en el código y en producción, solo lectura)

- **IA1 es la que lee mal el año e IA2 lo confirma.** En los 19 documentos activos con la fecha a más de un año de su
  correo, la fecha de IA1 (`raw_extraction_json → debug.phase_2.debug.phase_1_json.data.cabecera.fecha`) es la misma
  que la final. IA2 sí toca la fecha en otros casos (21 de 158), pero ninguno de estos.
- **El prompt de IA1 que se carga es `albaran_factura_es` de `config/prompts.yaml`** (`PROMPT_KEY_FASE1`, sin
  `PROMPTS_YAML_PATH` en `infra/`). `config/prompts/svc2_prompt_albaran_factura_es.yaml` **no lo carga nadie** (ya lo
  dicen `progress/spec_F-051.md` y `spec_F-064.md`): no se toca. Su regla de cabecera es solo «fecha: la del albarán».
- **La recepción ya llega a sv2.** sv1 guarda `recibido_utc` en el blob lateral del correo desde F-048 (`bf9d983`,
  2026-09-23) y el worker lee ese `ContextoCorreo` para las dos fases. sv2 no lo usa. `raw_context_json` y
  `email_received_datetime` son columnas de sv3: sv2 no las lee ni las necesita.
- **IA2 recibe el task de fase 1 entero** (`{prompt_fase_1}`, renderizado por `_render_task_fase_1` con el mismo
  correo) y la checklist (`{revision_rules}`) en los cuatro `albaran_revision_fase2_*`. Un marcador en fase 1 y una
  regla en la checklist llegan a las dos IAs sin tocar los cuatro prompts de fase 2.

## 2. Ficheros a crear

| Ruta | Qué |
|---|---|
| `services/albaranes-api/application/services/fecha_recepcion.py` | Puro, sin I/O (mismo patrón que `empresas_cliente.py`): `MARCADOR_FECHA_RECEPCION`, `MARCADOR_REVISION_FECHA`, `fecha_recepcion_de`, `render_fecha_recepcion`, `render_revision_fecha`, `NOTA_SIN_RECEPCION`, `NOTA_REVISION_SIN_RECEPCION`; la Regla del año vive en UNA constante que usan los dos render |
| `services/albaranes-api/tests/test_f112_fecha_recepcion.py` | R1–R5 |
| `services/albaranes-api/tests/test_f112_render_prompt.py` | R6–R11 (servicio con cliente LLM falso) |
| `services/albaranes-api/tests/test_f112_worker.py` | R12–R14 (pipeline y worker con fakes) |
| `services/albaranes-api/tests/test_f112_prompt_yaml.py` | R15–R18 (YAML reales) |
| `evals/sinteticos_fecha.py` | Genera las imágenes JPG de SIN-001…005 con Pillow (texto fijo, sin aleatoriedad) y `evals/casos_fecha_sinteticos.json` (R27) |
| `tests/test_f112_sinteticos_fecha.py` | R27 (determinismo: dos generaciones, mismos bytes; casos y fechas esperadas) |
| `evals/procesos/sv2_fecha.py` | Las dos fases de un caso con `fecha_recepcion`, devolviendo solo `cabecera.fecha` (reutiliza `sv2_proveedor.montar_servicio`, `ficheros_de_base`, `ficheros_de_rama` y `sv2_extraccion._adjuntos`) |
| `evals/comparar_fecha.py` | CLI del comparador (R19–R24), forma de `evals/comparar_proveedor.py` |
| `evals/casos_fecha.json` | Juego A: `{"version": 1, "casos": []}` versionado; lo rellena M1 (§7.1) |
| `tests/test_f112_comparar_fecha.py` | R19, R21–R24, R29 sin red (extractor falso) |
| `tests/test_f112_rutas_sensibles.py` | R25 |

## 3. Ficheros a modificar

- `services/albaranes-api/application/services/albaran_extraction_service.py`
  - `_render_task_fase_1(task, correo, fecha_recepcion=None)`: tras empresas del cliente y **antes** de
    `_render_contexto_correo` (R7), `task.replace(MARCADOR_FECHA_RECEPCION, render_fecha_recepcion(fecha))` solo si el
    marcador está (R6, R8: sin marcador no se añade nada, como `{empresas_cliente}` en F-064).
  - `extract_phase_1(..., fecha_recepcion: date | None = None)` y `review_phase_2(..., fecha_recepcion=None)`: la pasan a
    `_render_task_fase_1` (R9). Las dos líneas de log ganan `fecha_recepcion=%s` (fecha ISO o `NO`, R10).
  - `_MARCADORES_FASE_2` gana `revision_fecha`; en `review_phase_2`, `valores["{revision_fecha}"] =
    render_revision_fecha(fecha_recepcion)` dentro de la pasada única (R17). Lo insertado no se recorre otra vez.
- `services/albaranes-api/application/pipelines/extract_albaran_pipeline.py`: campo `fecha_recepcion: date | None =
  None` en las dos requests y paso tal cual (R12).
- `services/albaranes-api/interface_adapters/worker/extraction_worker.py`: tras `_leer_correo`,
  `fecha = fecha_recepcion_de(correo)` una vez; la misma a las dos requests (R13, R14).
- `services/albaranes-api/config/prompts.yaml`: regla de `fecha` y marcador en `albaran_factura_es` (§4.1).
- `services/albaranes-api/config/prompts.yaml`, los cuatro `albaran_revision_fase2_*`: sección «Fecha del albarán
  (revisión obligatoria)» con `{revision_fecha}`, después de la checklist y antes del grounding (§4.2).
- `revision_rules.yaml` **no** se toca (en la v1 llevaba la regla; la v1.1 la sustituye por la sección propia).
- `harness/rutas_sensibles.json`: `fecha_recepcion.py` en la verificación `evals` (R25). Es declaración del proyecto,
  no del arnés genérico: no se porta a `arnes-base`.
- `docs/ARCHITECTURE.md` (regla 26), `services/albaranes-api/sv2.md` (marcador), `evals/README.md` (comparador) (R26).

## 4. Textos

### 4.1 `albaran_factura_es` · «Reglas para la cabecera»

Sustituye a `- fecha: la del albarán.`:

```
- fecha: la del albarán (emisión o servicio), no la de un pedido, contrato o autorización. El día y el mes se
  leen SIEMPRE del papel. El AÑO se contrasta con la fecha de recepción del correo de abajo.

  {fecha_recepcion}
```

`render_fecha_recepcion(date(2026, 10, 28))` (R3; texto fijo, solo la fecha es variable):

```
FECHA DE RECEPCIÓN DEL CORREO: 2026-10-28. Es el día en que este albarán llegó al buzón, NO la fecha del
albarán. Úsala SOLO para leer el AÑO de cabecera.fecha. {REGLA_DEL_ANIO}
El día y el mes salen SIEMPRE del papel. Si el papel no trae fecha, cabecera.fecha es null: NUNCA copies esta
fecha como fecha del albarán.
```

`REGLA_DEL_ANIO` (constante única, va en los dos bloques y con cualquier fecha, R28):

```
La fecha de un albarán es IGUAL o algo ANTERIOR a la de recepción (días o semanas), nunca muy posterior. NO es
«el año del correo»: es el año que deja el día y el mes del papel en la recepción o poco antes. Si el día y el
mes del papel caen DESPUÉS del día y el mes de la recepción, el año es el ANTERIOR al de la recepción
(28-12 con correo del 03-01 ⇒ el año anterior; 02-01 con correo del 05-01 ⇒ el mismo año). Si el papel trae un
año legible y plausible (la fecha queda entre un año antes de la recepción y pocos días después), ese año
manda: no inventes otro. Si el año que lees no es plausible, vuelve a mirarlo: casi siempre es una cifra mal
leída (la última, sobre todo); si aun así el papel dice sin ninguna duda ese año, devuélvelo tal cual.
```

`NOTA_SIN_RECEPCION` (R4): `(Sin fecha de recepción del correo en esta ejecución: lee la fecha solo del papel, como
siempre.)`

Seguridad (R5): el bloque solo lleva `date.isoformat()` de la fecha validada; ningún otro carácter de `recibido_utc`
(que viene de Graph, no del texto del correo) llega al prompt.

### 4.2 Fase 2 · sección «Fecha del albarán (revisión obligatoria)» con `{revision_fecha}`

En los cuatro `albaran_revision_fase2_*`, tras «CHECKLIST DE REGLAS DE REVISIÓN». `render_revision_fecha(fecha)`:

```
FECHA DE RECEPCIÓN DEL CORREO: 2026-10-28. Revisa SIEMPRE cabecera.fecha de la fase 1 contra el documento y
contra esta fecha, sea cual sea la familia y aunque nada más cambie. {REGLA_DEL_ANIO}
Si la fecha de fase 1 no cumple esa regla y el papel admite el año correcto, corrige SOLO el año (día y mes, los
del papel) y añade un razonamiento con campo "cabecera.fecha" y patron_aplicado "anio_fecha_recepcion". Si la
fase 1 leyó mal el día o el mes, corrígelos con lo que diga el papel. Si el papel trae un año legible y
plausible, no lo toques. Nunca pongas la fecha de recepción como fecha del albarán.
```

Ejemplo para el YAML (fijo, no lo pinta el código): recepción 2026-10-28, fase 1 `2020-10-17`, papel «17/10/26» con
el 6 mal cerrado ⇒ `2026-10-17`. `NOTA_REVISION_SIN_RECEPCION`: `(Sin fecha de recepción del correo: revisa
cabecera.fecha solo contra el papel, como siempre.)`

## 5. Clases y funciones (capa)

```python
# application/services/fecha_recepcion.py  (application, puro)
MARCADOR_FECHA_RECEPCION = "{fecha_recepcion}"
NOTA_SIN_RECEPCION: str
def fecha_recepcion_de(correo: ContextoCorreo | None) -> date | None   # date.fromisoformat(recibido_utc[:10])
def render_fecha_recepcion(fecha: date | None) -> str
```

`ContextoCorreo` se importa solo bajo `TYPE_CHECKING` (como en el servicio). Ni el dominio ni la infraestructura
cambian: no hay campo nuevo en `DocumentoAlbaran` ni en `RevisionAlbaranFase2` (la duda del año la recoge el
razonamiento de IA2 y, aguas abajo, la red de sv3).

## 6. Qué NO se toca

- `ruesma_comun` (`ContextoCorreo` ya trae `recibido_utc`; el bloque del correo y su advertencia de DATO no cambian).
- sv1 (ya envía la recepción), sv3 (`fecha_guard_service.py` sigue marcando `fecha_albaran_fuera_de_rango`), sv9
  (`fecha_no_plausible`), sv4 (la corrección a mano es F-108).
- Del resto de los cuatro prompts de fase 2, todo salvo la sección nueva; `revision_rules.yaml`; los schemas de
  `domain/models/` y `config/prompts/svc2_prompt_albaran_factura_es.yaml` (no cargado).
- La API HTTP de sv2 (`/v1/albaranes/extract`): no recibe correo, va sin referencia (Nota sin recepción).
- `evals/runner.py` y `evals/procesos/sv2_extraccion.py`: la pasada completa sigue midiendo sin referencia; con
  referencia mide el comparador.
- `azure-apps/`: sv2 no cambia lo que expone ni lo que consume (el blob del correo ya lo leía).
- Los números de albarán mal leídos (fuera por la ficha).
- LÍMITE DE SERVICIO: todo es lectura de sv2; no hay responsabilidad nueva.

## 7. Medición antes/después (`evals/comparar_fecha.py`)

El banco sí cubre la cabecera: 59 casos de IA1 con `fecha` esperada, campo crítico (`*fecha*` en `criticidad.json`).
Pero ninguno trae correo ni fecha de recepción, y ninguno tiene el fallo de producción (años: 26 de 2026, 20 de 2025, 12
de 2024, 1 de 2023). Por eso tres juegos:

| Juego | Casos | Referencia | Qué mide |
|---|---|---|---|
| A | los de producción con el año mal (§7.1) | la recepción real | que la referencia arregla el fallo (C1) |
| B | los 59 del banco | esperada + 7 días (135 de 158 en producción llegan en ≤ 30 días) | que no rompe lo que funciona (C2) |
| C | los 13 del banco anteriores a 2025 | esperada + 730 días | que un año antiguo impreso de verdad no se pisa (C3) |
| D | 5 sintéticos de cambio de año (R27) | la de cada caso | diciembre con correo de enero, enero con enero, diciembre con diciembre, año legible y año de dos cifras (C6) |

- **Variantes**: `base` = YAML de `--base` (sin marcador ni regla ⇒ el prompt de hoy byte a byte, R8) y `rama`.
- **Umbral de C1** (D6): en A, casos con mayoría `exacta` tras IA2 en rama ≥ 80 % y ≥ base. C4 (ninguna ejecución
  `referencia`) vigila que la IA no copie la recepción.
- **Efecto de IA2, aparte** (R21, R29): por ejecución, fecha de IA1 frente a la final (`corrige`, `estropea`, `cambia`,
  `igual`). C5 exige 0 `estropea` en rama; la tabla dice cuánto aporta la revisión obligatoria frente a base.
- **Juego D**: imágenes JPG de un albarán mínimo (emisor ficticio «PROVEEDOR SINTÉTICO, S.L.», una línea, la fecha
  como único dato variable), generadas con Pillow por `evals/sinteticos_fecha.py`; su tipología, `generico`.
- **Coste** (D7 decidida): 2 llamadas por caso, variante y repetición; A = 19, B = 20 (semilla fija), C = 13, 2
  repeticiones: **416**. D suma 5 × 2 × 2 × 2 = 40.
- **Modelos**: los del entorno (`GEMINI_MODEL`, `OPENAI_MODEL`), que deben ser los de producción (F-085).

### 7.1 Montaje del juego A (M1)

1. Líder, solo lectura (sesión con `default_transaction_read_only=on`, clave de Key Vault en variable de proceso):
   lista de los documentos activos de `albaran_documents_merge` con `|fecha − email_received_datetime| > 365` días, con
   su `id`, tipología y recepción, en `evals/inputs/fecha/origen.json` (**ignorado por git**).
2. Líder, solo lectura en Blob (permiso del humano, 2026-10-30): descarga cada PDF a
   `evals/inputs/albaranes/FEC-NNN.pdf` y lee en el papel la fecha verdadera; con eso cierra D8.
3. Humano o líder: `evals/casos_fecha.json` con `caso_id`, `tipologia`, `fecha_esperada`, `recibido` (solo fechas y
   tipología; sin proveedor ni número de albarán). Se versiona.

Los 3 de los 19 sin el patrón «día y mes bien, año mal» (dos de un transportista de residuos y uno de un gestor de
residuos) pueden ser **otra fecha del papel** (autorización, contrato) y no un año mal leído: el humano lo dirá en el
paso 2 (D8, la cierra el líder).

## 8. Después del despliegue (M4, solo lectura)

A las dos semanas, sobre los documentos dados de alta después del despliegue de sv2:

```sql
SHOW transaction_read_only;  -- debe decir on
SELECT count(*) AS comparables,
       count(*) FILTER (WHERE abs(left(fecha,10)::date - left(email_received_datetime,10)::date) > 365) AS lejos
  FROM albaran_documents_merge
 WHERE is_active AND fecha ~ '^\d{4}-\d{2}-\d{2}' AND email_received_datetime ~ '^\d{4}-\d{2}-\d{2}'
   AND created_at_utc >= '<fecha del despliegue>';
```

Línea base: 19 de 158 (12 %), 17 de 155 en octubre. Además, cuántos razonamientos de IA2 llevan
`patron_aplicado = anio_fecha_recepcion` (en `raw_extraction_json`) y en cuántos documentos la fecha de IA1
(`debug.phase_2.debug.phase_1_json`) difiere de la final (línea base: 21 de 158). En enero de 2027 se repite la
medición solo sobre albaranes con fecha de diciembre y correo de enero (el riesgo de §9). Despliegue: solo sv2 (`.\deploy.ps1 -Only sv2`,
lo lanza el humano); sin orden con otros servicios porque no cambia ningún contrato.

**PARADA 1 (parcial) del humano, 2026-10-30:** D7 = 416 llamadas («mejor 416 lecturas»); para el juego A, permiso de lectura en Blob al líder, que leerá las fechas verdaderas de los 19 en el papel (D8 se cierra con esa lectura). D1–D6 y D9: propuestas las recomendadas, pendientes de su confirmación explícita.

## 9. Riesgos y decisiones (PARADA 1)

Estado a 2026-10-30: **D7 decidida (416)**; **D8 la cierra el líder** con la lectura en Blob; D1–D6 y D9 siguen como
propuestas recomendadas, **pendientes de confirmar por el humano**.

- **Riesgo del cambio de año** (enmienda v1.1). Una referencia leída como «el año del correo» convierte un albarán del
  28-12 que llega el 03-01 en uno de 11 meses después: justo el error que se quiere quitar, pero al revés y en
  diciembre-enero. Mitigación: la Regla del año (igual o anterior; día y mes posteriores ⇒ año anterior), el mismo
  texto en IA1 e IA2 y con cualquier fecha (R28), el juego D (C6) y la repetición de M4 en enero. Riesgo residual: un
  albarán con fecha unos días POSTERIOR al correo (fechado por adelantado) con un año dudoso puede pasar al año
  anterior; sv3 lo marca a revisión (> 365 días) y F-108 lo corrige a mano.
- **D1 · Dónde entra la referencia.** (a) Marcador en el task de IA1 + sección propia de revisión obligatoria en los
  prompts de IA2 (v1.1; IA2 recibe además el bloque de fase 1 dentro de `{prompt_fase_1}`). (b) Solo IA1. (c) Solo
  IA2. **Recomendada (a)**: el error nace en IA1 y hoy IA2 no lo ve; en estos 19 IA2 no corrigió ninguno.
- **D2 · Qué fecha.** (a) La parte de fecha de `recibido_utc` en UTC, como la red de sv3. (b) Hora de Madrid. **(a)**:
  para leer un año, unas horas no importan, y las dos redes miran lo mismo.
- **D3 · Sin correo.** (a) Sin referencia (Nota sin recepción). (b) Hoy como referencia, como hace sv3. **(a)**: una
  reextracción manual de un documento viejo con «hoy» empujaría el año hacia el que no es.
- **D4 · Albarán con una fecha antigua impresa de verdad.** La IA la devuelve tal cual («si el papel dice sin ninguna
  duda otro año»); sv3 lo marca a revisión, sv9 no da de alta y la ficha (F-108) permite corregirla. No se añade
  campo nuevo al schema. Alternativa descartada: un `fecha_dudosa` de la IA, que toca schemas de sv2, sv3 y sv4 para
  lo que ya hace la red de sv3. El riesgo contrario —la IA pisa un año legible con el de la referencia— lo mide C3.
- **D5 · Sin marcador no se añade nada** (como `{empresas_cliente}`, no como `{obras_activas}`): permite medir la
  variante `base` con el código nuevo. Riesgo: un YAML desplegado sin marcador va sin referencia; lo vigila R15.
- **D6 · Umbral de C1**: 80 % de A con mayoría `exacta` tras IA2. Alternativa: «mejor que base» sin umbral.
- **D7 · Tamaño de la medición**: **decidida el 2026-10-30, 416** (B a 20 casos), «mejor 416 lecturas».
- **D8 · Los 3 casos de residuos sin patrón de año** (la cierra el líder con la lectura en Blob): si el papel muestra que la IA tomó otra fecha (autorización del
  gestor, contrato), (a) basta la aclaración «emisión o servicio, no pedido, contrato o autorización» de §4.1, que ya
  va incluida; (b) se sacan del juego A y se abre ficha propia.
- **D9 · Versionar `evals/casos_fecha.json`**: solo fechas y tipología, sin datos del proveedor. Alternativa: dejarlo en
  `evals/inputs/` (ignorado), y entonces el reviewer no puede reproducir el juego A.
- **Riesgo**: el bloque de recepción alarga el prompt de IA1 unas 120 palabras (coste despreciable frente a la lista
  de obras). **Riesgo**: si sv1 no pudo leer el correo (fallo de Graph), no hay blob y ese documento va sin referencia,
  como hoy.
- **Alternativa descartada**: corregir el año en código (p. ej. con el de la recepción cuando día y mes encajan).
  Contradice la decisión del humano: la fecha la lee la IA.
