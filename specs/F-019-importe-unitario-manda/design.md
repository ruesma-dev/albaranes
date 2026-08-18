<!-- specs/F-019-importe-unitario-manda/design.md -->
# F-019 · Importe de línea: manda el unitario leído · Diseño

Servicios tocados: **sv5** (`albaran-valoracion-api`, un SELECT) y **sv6**
(`albaran-valoracion-persist`, el `PriceReconciler`). **sv2 NO se toca**
(decisión D1). Sin cambios de schema, sin migración, sin dependencias nuevas.

## Contexto del código real (leído y ejecutado, no supuesto)

### La cadena causal, reproducida

El fallo se reprodujo ejecutando el código real del repositorio con los
números del albarán (venv de la raíz, sin BBDD):

```
PriceReconciler(tolerance_pct=2.0).reconcile(
    precio_1a=4000.0, precio_albaran_declarado=0.543,
    cantidad_albaran=108.0, importe_albaran=3800.52, descuento_pct=40.0)
→ final_price=58.65  source='albaran_calculated'
  reasons=['unitario_declarado_vs_derivado_mismatch:0.543!=58.65',
           'albaran_importe_manda_derivado']

# con el importe correcto (35.19) el MISMO código ya devuelve:
→ final_price=0.543  source='albaran_declared'
  reasons=['albaran_importe_manda_declarado_coincide']
```

Y el SELECT de sv5, ejecutado tal cual contra SQLite en memoria con la fila
real, devuelve `importe_albaran = 3800.5199999999995` para
`cantidad=108, precio=0.543, descuento=40, precio_neto=35.19`.

**Conclusión medida: el defecto que produce el número malo es UNO — el SELECT
de sv5. La precedencia de sv6 solo lo amplifica.** Por eso el diseño tiene un
fix (T2) y un endurecimiento (T4), y no al revés.

### Quién más lee `precio_neto` (y ya lo lee bien)

Evidencia de que el sistema entero, salvo sv5, entiende `precio_neto` como
importe de línea — es sv5 quien tenía la premisa falsa, no el prompt:

| Sitio | Qué hace |
|---|---|
| `services/albaranes-api/config/prompts.yaml:75` (IA1 activo) | «si figura, léelo; si no, calcula `cantidad*precio*(1 - descuento/100)`» |
| `services/albaranes-api/config/prompts/svc2_prompt_albaran_factura_es.yaml:82` (V3, no cargado) | «importe final de la línea tras descuento» |
| `services/albaranes-api/sv2.md:291` | «Total línea» |
| `albaran_confidence_service._is_line_net_consistent` (sv3) | compara `precio_neto` contra `cantidad × precio × (1 − dto/100)` |
| `review_repository.py:3725` (sv4) | `eff_importe = line.precio_neto` |
| `static/app.js:1744-1747` (sv4) | «`precio_neto` como nombre de campo para el importe de la línea» |
| `azure_document_intelligence_client.py:212` / `google_document_ai_client.py` | `precio_neto ← Amount / LineAmount / TotalPrice` |

El comentario «FIX (jun 2026)» del SELECT de sv5 afirma lo contrario
(«`precio_neto` (unitario NETO)»). Es la premisa falsa que hay que borrar.

### El bug de junio que el FIX quiso arreglar sigue arreglado

El comentario de sv5 dice que el problema original era la línea base de
hormigón apareciendo con importe 0/vacío. Eso NO lo causaba el alias
`precio_neto AS importe_albaran`: lo causaba que en hormigón `precio_neto`
viene **NULL** (el albarán no imprime precios). Lo arregla la cascada del
«FIX 2 (jul 2026)», que se conserva entera. El `cantidad *` de fuera del
`COALESCE` es puro daño colateral.

### El importe inflado también contamina a la IA3

`value_albaran_pipeline._albaran_line_to_dict` vuelca `importe_albaran` al
prompt de IA3. Es decir, la IA de valoración está viendo hoy importes ×
cantidad. Corregir el SELECT también sanea la entrada del LLM **sin tocar
ningún prompt**.

## sv5 — el SELECT

### Ficheros a modificar

**`services/albaran-valoracion-api/infrastructure/database/sqlalchemy_valuation_context_repository.py`**

1. `_SQL_ALBARAN_LINES` — la expresión de `importe_albaran` pasa de

```sql
(cantidad * COALESCE(
    precio_neto,
    precio * (1 - COALESCE(descuento, 0) / 100.0)
)) AS importe_albaran,
```

a

```sql
COALESCE(
    precio_neto,
    cantidad * precio * (1 - COALESCE(descuento, 0) / 100.0)
) AS importe_albaran,
```

   El `cantidad *` se mueve DENTRO de la segunda rama del `COALESCE`. Un solo
   movimiento de paréntesis: la rama del importe leído deja de multiplicarse
   (R4, R7) y la rama derivada mantiene su fórmula exacta (R5). Sin
   `precio_neto` ni `precio` sigue saliendo NULL (R6).

2. El bloque de comentarios (líneas ~55-125) se reescribe: fuera la afirmación
   «`precio_neto` es el precio unitario NETO», dentro la semántica de R1 con
   el motivo (F-019, prueba local del 2026-08-18) y el nombre de los otros
   consumidores que ya la respetan. **El comentario que mintió es parte del
   bug**: se corrige con la misma seriedad que el código.

### Matriz de comportamiento del cambio (por qué el riesgo está acotado)

| `precio_neto` | `precio` | `cantidad` | Antes | Ahora | ¿Cambia? |
|---|---|---|---|---|---|
| 35,19 | 0,543 | 108 | 3.800,52 | **35,19** | **SÍ (el bug)** |
| NULL | 0,543 | 108 | 58,64 (=108×0,543×0,6) | 58,64 | no |
| NULL | NULL | 108 | NULL | NULL | no |
| 35,19 | 0,543 | NULL | NULL | **35,19** | **SÍ (mejora, R7)** |
| 35,19 | NULL | 108 | 3.800,52 | **35,19** | **SÍ (el bug)** |

**El único caso que cambia de número es aquel en el que `precio_neto` NO es
NULL** — exactamente el caso roto. Todo lo demás es idéntico byte a byte, lo
que es el argumento central de que esto no rompe hormigón, residuos ni
albaranes sin valorar.

### Cómo se prueba el SQL sin BBDD

`_SQL_ALBARAN_LINES` es un `sqlalchemy.text()` con SQL estándar (`COALESCE`,
aritmética, `ORDER BY`). **Comprobado durante la redacción de esta spec**: se
ejecuta sin cambios contra `create_engine("sqlite://")` creando
`albaran_lines_merge` al vuelo, y reproduce tanto el 3.800,52 como el NULL del
hormigón. Los tests de R4-R7 usan esa fixture: sin red, sin PostgreSQL, sin
contenedor. (Si el implementer encontrara una incompatibilidad, el fallback es
un test de contenido del SQL — más débil: se documenta como desviación.)

## sv6 — la precedencia

### Ficheros a modificar

**`services/albaran-valoracion-persist/application/services/price_reconciler.py`**

`PriceReconciler.reconcile` (capa **application**; clase pura, sin IO). La
firma NO cambia. Cambia el orden de los bloques y el contenido del docstring:

```
Prioridad NUEVA (regla del humano, 2026-08-18):

  1. UNITARIO declarado (≠0) → MANDA. source='albaran_declared'.
     Si además el importe leído es derivable:
       - coincide (PRICE_TOLERANCE_PCT) → agreement='neither',
         reason 'albaran_unitario_manda_derivado_coincide'
       - discrepa → agreement='mismatch', reason
         'unitario_declarado_vs_derivado_mismatch:<d>!=<x>'   [R10]
     El final_price es el declarado en AMBOS casos.

  2. IMPORTE leído derivable SIN unitario declarado → despeje:
     unitario = importe / (cantidad × (1 − dto/100)).
     source='albaran_calculated', reason 'albaran_importe_manda_derivado'.

  3. FALLBACK contrato — la cadena clásica 1a/1b, SIN TOCAR.        [R11]
```

Helpers `_no_cero`, `_derivar_bruto` y `_match`: **sin cambios**. Los motivos
`line_already_valued`, `importe_albaran_cero_ignorado`,
`precio_declarado_cero_ignorado`, `importe_leido_sin_cantidad_no_derivable`,
`descuento_100_no_derivable`, `only_1a_available`, `only_1b_available`,
`no_price_available` y `price_1a_vs_1b_mismatch`: **se conservan tal cual**
(R13, R14, R11).

Motivos afectados:

| Motivo | Antes | Ahora |
|---|---|---|
| `albaran_importe_manda_declarado_coincide` | importe manda, declarado coincide | **se retira**, lo sustituye el siguiente |
| `albaran_unitario_manda_derivado_coincide` | — | **nuevo**: manda el declarado y el derivado lo confirma |
| `unitario_declarado_vs_derivado_mismatch:<d>!=<x>` | aviso mudo; ganaba el derivado | se mantiene el texto; ahora gana el **declarado** y va a revisión |
| `albaran_unitario_declarado_manda` | prioridad 2 (sin importe) | se mantiene, mismo significado |
| `albaran_importe_manda_derivado` | prioridad 1 | queda solo para el despeje sin unitario (R9) |

Nadie fuera de sv6 consume estos strings (comprobado con `grep` en todo el
monorepo: solo aparecen en el propio fichero y en `sv6.md`), así que retirar
uno y añadir otro no rompe lectores.

### Cómo llega el mismatch a revisión (R10)

`ValuationBuilder._build_line` ya calcula
`review_required = ... or reconciliation.agreement == "mismatch" or ...`.
Devolviendo `agreement="mismatch"` en el caso de R10, la línea va a revisión
**sin tocar `valuation_builder.py`**. Es el motivo de elegir esa vía (D3).

### Lo que NO se toca en sv6

- **`ImporteCalculator`**: el importe declarado sigue mandando sobre el
  calculado (`docs/referencia/dominio_negocio_albaranes.md` §10.4
  «transcribir, no recomponer»). Con el importe efectivo ya correcto, el
  declarado y el calculado coinciden en los casos de Feymaco. Endurecer ese
  contraste es el **guard aritmético R6 de F-003**, no de aquí.
- **`ValuationBuilder`**: ni el orden de pasos, ni el descuento heredado por
  las sintéticas, ni la cantidad efectiva.
- **`UnitCategoryGuard`**, conversor de unidades, `PartidaMatcher`,
  matching de sv5 contra el contrato.

## Ficheros que NO se tocan (colindantes que tentarían)

| Fichero | Por qué no |
|---|---|
| `services/albaranes-api/config/prompts.yaml` | D1: su definición de `precio_neto` es la CORRECTA; cambiarla es F-003 R1 |
| `services/albaranes-api/domain/models/albaran_models.py` | el campo `importe` propio es F-003 R2 |
| `services/albaranes-persistencia/**` | ninguna columna nueva; el merge no cambia |
| `services/albaranes-front/**` | sv4 ya trata `precio_neto` como importe; nada que corregir |
| `services/albaran-valoracion-api/config/prompts*.yaml` | no mencionan el campo; el saneado les llega por el dato |
| `application/services/importe_calculator.py` | ver arriba |
| `services/albaranes-comun/**` | el contrato de mensajes no cambia |

## SQL

No hay ficheros `.sql` (convención del repo: DDL inline en Python). Esta
feature **no crea ni altera schema**: solo cambia una expresión de un `SELECT`
de solo lectura en sv5, que es el consumidor. No hay lectores nuevos que
listar (`docs/ARCHITECTURE.md` regla 3).

## Documentación normativa a actualizar (R3)

- **`docs/ARCHITECTURE.md`**, §«Semántica de dominio imprescindible»: regla
  nueva —`precio_neto` de una línea de albarán es el IMPORTE de la línea tras
  descuento; el unitario bruto es `precio`; la fórmula canónica es
  `importe = cantidad × precio × (1 − dto/100)` y **el unitario leído manda**;
  el importe solo se despeja cuando faltan los campos.
- **`services/albaran-valoracion-api/sv5.md`**: la línea que describe la
  propagación de `descuento` / `precio_neto` al DTO.
- **`services/albaran-valoracion-persist/sv6.md`** §6.1: la tabla de
  precedencia del `PriceReconciler` (hoy describe el orden viejo) y §6.4, que
  además está **desactualizada desde jul 2026** (dice «no coincide → se usa el
  calculado», cuando el código usa el declarado). Se corrige de paso: es
  documentación del servicio que estamos tocando.
- **`progress/current.md`**: lista de decisiones abiertas y el pendiente de
  re-valorar documentos antiguos (R20).

## Riesgos y decisiones

### D1 — sv2 no se toca; la semántica se fija con un test de contrato

*Alternativa descartada*: emitir en IA1 un campo con nombre no ambiguo
(`importe_linea`) en esta feature. Se descarta por tres razones: (a) **ya está
especificado en F-003** (R1 y R2 de `specs/F-003-valorados-match-estricto/`),
que además añade la columna en sv3 y el `importe_leido` en sv5 — hacerlo aquí
duplicaría diseño y colisionaría al implementar; (b) tocar
`config/prompts.yaml` dispara la puerta de rutas sensibles con una pasada de
evals que hoy sale `NO_EVALUABLE` (ground truth vacío), añadiendo peaje sin
evidencia; (c) el prompt **no está mal**: su definición coincide con sv3 y
sv4. El equivocado era el consumidor.

Lo que sí se hace es dejar la semántica **atada con un test** (R2): si alguien
cambia esa regla del prompt, el test del monorepo falla y obliga a reconciliar
sv5/sv6 en el mismo trabajo. Convierte una convención tácita en un contrato
ejecutable, que es lo que faltaba en junio de 2026.

### D2 — Corregir el SELECT bastaría; la precedencia se cambia igualmente

Con el importe efectivo correcto, el reconciliador actual ya devuelve 0,543
(medido). Aun así se invierte la prioridad porque: (a) es la regla explícita
del humano (2026-08-18); (b) deja el sistema robusto ante documentos donde el
importe impreso y el unitario no cuadren (redondeos del proveedor, descuentos
en cascada, OCR de una cifra); (c) sin ella, cualquier futura recaída en el
importe volvería a fabricar un unitario inventado en silencio.

### D3 — El mismatch viaja por `agreement="mismatch"`

*Alternativa descartada*: añadir una condición nueva en
`ValuationBuilder._build_line` (`or "unitario_declarado_vs_derivado_mismatch"
in reasons`). Se descarta porque obliga a tocar un fichero de 1.500 líneas
para expresar algo que el modelo ya sabe decir. **Riesgo asumido y anotado**:
`precio_unitario_agreement="mismatch"` pasa a poder aparecer en líneas con
`source="albaran_declared"`, donde hasta hoy solo salía en las de contrato. El
significado literal («las fuentes de precio no concuerdan») se sostiene, y
`sv6.md` §6.1 lo documenta.

### D4 — Ni migración ni reescritura de histórico

Las valoraciones son un replace transaccional por documento y el contexto se
relee del merge (que no cambia): re-valorar corrige. No se escribe ningún
script de backfill (R19/R20). **Queda como decisión del humano** qué
documentos ya valorados se reprocesan y cuándo; el mecanismo (botón de
revalorar de sv4 → `q-valoracion`) ya existe.

### R5 — Riesgo residual conocido, fuera de alcance

El prompt de IA1 permite que `descuento` sea «un número» y el V3 dice
«porcentaje **o importe** de descuento». Si un albarán trajera el descuento
como importe en euros, la fórmula canónica se rompería para esa línea. **No se
aborda aquí**: es F-003 R2/R3 (`descuentos` como lista de porcentajes y
cascada determinista en sv3). Queda anotado para que el reviewer no lo lea
como olvido.

### Solape con F-003 (spec_ready) — a reconciliar antes de implementar F-003

F-003 R4 dice literalmente que sv5 debe exponer «el `importe_albaran` efectivo
(el leído si existe; si no, **la derivación actual `cantidad × precio_neto`**
como fallback)». **Esa frase queda obsoleta con F-019**: la derivación actual
es el bug. Cuando F-003 se implemente, su R4 debe leerse con la fórmula de
R4/R5 de esta spec. Igual con F-003 R6: su guard aritmético es la evolución
del mismatch de R10, no un duplicado. **Acción para el humano**: anotarlo en
F-003 al arrancarla (queda en `progress/current.md`).

## Límite de microservicio

La feature respeta el reparto vigente: sv5 construye el contexto de valoración
(y ahí vivía la derivación errónea), sv6 decide precio e importe finales. No
aparece responsabilidad nueva, no se mueve lógica entre servicios y no se
duplica nada que debiera estar en `albaranes-comun`: la fórmula canónica se
aplica en **un** sitio por servicio y el resto la consume ya calculada. No
procede proponer servicio nuevo.

## Decisiones abiertas que necesita validar el humano

1. **D3**: ¿se acepta que `precio_unitario_agreement="mismatch"` aparezca en
   líneas cuyo precio viene del albarán? (Alternativa: condición explícita en
   el builder.)
2. **R20**: ¿se reprocesan los albaranes ya valorados con importes inflados?
   ¿Cuáles y cuándo? (Fuera del código de esta feature.)
3. **F-003**: confirmar que su R4/R6 se reescriben contra esta spec cuando se
   arranque, en vez de restaurar la derivación vieja.
