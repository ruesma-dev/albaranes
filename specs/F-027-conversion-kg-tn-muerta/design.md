<!-- specs/F-027-conversion-kg-tn-muerta/design.md -->
# F-027 · La red KG→TN de `UnitConverter` es código muerto · Diseño

Servicio tocado: **sv6** (`services/albaran-valoracion-persist`) y solo sv6.
Sin cambios de schema, sin migración, sin dependencias nuevas, sin tocar
prompts ni ningún fichero de otro servicio.

El cambio de producción son **dos expresiones** del paso 4 de
`ValuationBuilder._build_line`. `unit_converter.py` no cambia de
comportamiento: solo se le añade documentación.

---

## 1. El código real, leído y ejecutado

### 1.1 La rama que mata la red (`valuation_builder.py:1008-1025`, tal cual está en `dev`)

```python
# 4. Unit conversion
if category_match and partida_result.derived_line is not None:
    unidad_contrato_para_conversion = unidad_albaran
else:
    unidad_contrato_para_conversion = unidad_contrato

if category_match:
    converted = self._converter.convert(
        cantidad=albaran_line.cantidad if albaran_line else None,
        unidad_albaran=unidad_albaran,
        unidad_contrato=unidad_contrato_para_conversion,
    )
else:
    converted = self._converter.convert(
        cantidad=None,                      # ← el defecto
        unidad_albaran=unidad_albaran,
        unidad_contrato=unidad_contrato_para_conversion,
    )
```

Y la primera guarda del conversor (`unit_converter.py:64-70`) sale por
`no_quantity_in_albaran` **antes** de llegar a la red de plausibilidad de
toneladas (`unit_converter.py:83-113`, escrita en jul 2026 justo para esto).

### 1.2 Comportamiento real del conversor, medido (matriz completa)

Ejecutado sobre `dev` con `YamlUnitRegistry(config/unit_registry.yaml)`:

| cantidad | u. albarán | u. destino | resultado | motivo |
|---|---|---|---|---|
| 8,0 | *(None)* | `M3` | 8,0 · f=1,0 | `no_albaran_unit_assumed_same` |
| 4,0 | `M3` | `M3` | 4,0 · f=1,0 | — |
| 108,0 | `UD` | `UD` | 108,0 · f=1,0 | — |
| **30380,0** | *(None)* | **`TN`** | **30,38 · f=0,001 · ambiguous** | **`cantidad_sin_unidad_reinterpretada_kg_a_tn`** |
| 500,0 | *(None)* | `TN` | 500,0 · f=1,0 · ambiguous | `cantidad_tn_implausible_revisar` |
| 12,0 | *(None)* | `TN` | 12,0 · f=1,0 | `no_albaran_unit_assumed_same` |
| 108,0 | `UD` | `M3` | **`None`** | `category_mismatch:count!=volume` + `unit_category_mismatch_in_conversion` |
| 30380,0 | `KG` | `TN` | 30,38 · f=0,001 | — |
| 5,0 | *(None)* | *(None)* | 5,0 · f=1,0 | `no_contract_unit_assumed_same` |
| 5,0 | `SACO` | `UD` | 5,0 · f=1,0 · ambiguous | `ambiguous_unit_conversion` |
| *(None)* | *(None)* | `TN` | `None` | `no_quantity_in_albaran` |

**La fila decisiva es `UD → M3`**: el conversor **ya se niega** a cruzar
categorías incompatibles y devuelve `None` por su cuenta. Es decir, la rama
`else` del builder no aporta ninguna protección que el conversor no tenga: lo
único que consigue es cegar el caso `unknown`, que es precisamente donde vive
la red de plausibilidad. Ese es el argumento que decide el diseño (§4, D1).

### 1.3 La segunda mitad del mismo ×1000 (R6, R7)

`PartidaMatcher._build_derived` (`partida_matcher.py:257-281`) construye la
línea derivada así:

```python
unidad: str | None = unidad_albaran
if ia_line is not None:
    unidad = ia_line.unidad_medida or unidad     # ← la del CONTRATO
```

Es decir: cuando la IA casó una línea de contrato (el caso normal, y el del
58826), la derivada se queda con la **unidad y el precio del contrato**. Pero
el builder, cuando hay derivada, convierte a `unidad_albaran`:

```
albarán 'KG' + contrato 'TN' + partida cruzada
  → guard: mass == mass → category_match = True
  → derived_line existe  → destino = unidad_albaran = 'KG'
  → convert(30380, 'KG', 'KG') = 30380 · factor 1
  → 30380 × 15,43 €/TN  = 468.763,40 €
```

Es el mismo error de tres órdenes de magnitud, **vivo hoy y sin necesidad de
que la IA falle**. Además es el escenario que **F-024 activa**: en cuanto IA1
empiece a extraer «KG», los albaranes de MAHORSA entrarán por aquí. Arreglar
una mitad y dejar la otra sería cerrar F-027 y reabrirla con F-024.

---

## 2. Ficheros a modificar

### 2.1 `services/albaran-valoracion-persist/application/services/valuation_builder.py`

Capa **application**. Único cambio de producción. El bloque «4. Unit
conversion» queda:

```python
# 4. Unit conversion
# (ago 2026 · F-027) CONVERTIR PRIMERO, DECIDIR REVISIÓN DESPUÉS.
# Antes, con category_match=False, aquí se llamaba al conversor con
# cantidad=None a propósito: eso mataba la red de plausibilidad de
# toneladas (30.380 kg sin unidad contra un contrato en TN se valoraban
# como 30.380 TN → 468.763 €). No protegía de nada: el conversor YA
# devuelve None cuando las categorías son incompatibles de verdad
# (UD→M3). category_match=False marca revisión (paso 5), no anula la
# cantidad.
# La unidad de DESTINO es la de la línea que pone el precio: la derivada
# si la hay —que suele llevar la unidad del contrato, no la del
# albarán—, si no la del contrato.
if partida_result.derived_line is not None:
    unidad_destino_conversion = partida_result.derived_line.unidad_medida
else:
    unidad_destino_conversion = unidad_contrato

converted = self._converter.convert(
    cantidad=albaran_line.cantidad if albaran_line else None,
    unidad_albaran=unidad_albaran,
    unidad_contrato=unidad_destino_conversion,
)
```

Tres cambios, ninguno de más:

1. **Desaparece el `if category_match: … else: cantidad=None`**: una sola
   llamada, siempre con la cantidad real (R1). Cuando no hay línea de albarán
   la cantidad sigue siendo `None` y la guarda de R8 hace su trabajo.
2. **`unidad_contrato_para_conversion` → `unidad_destino_conversion`**, y su
   valor pasa a ser `derived_line.unidad_medida` en vez de `unidad_albaran`
   (R6). El nombre viejo mentía: la unidad de destino no siempre es la del
   contrato.
3. **La condición pierde el `category_match and`**: la unidad de destino no
   depende de si el guard aprobó o no; depende de qué línea pone el precio.

**Compatibilidad de (2)**: `_build_derived` inicializa `unidad = unidad_albaran`
y solo la pisa si la línea de contrato casada trae unidad. Por tanto
`derived_line.unidad_medida == unidad_albaran` **exactamente en el caso para el
que se escribió la línea vieja** (derivada sin línea de contrato de referencia).
El cambio es un superconjunto correcto, no una inversión.

**Lo que NO se toca de este fichero**: el orden de los cinco pasos, el bloque
4.bis de residuos, la regla «movimiento de residuos sin cantidad vale 1», el
cálculo de `review_required` (que ya incluye `not category_match` y
`converted.ambiguous`), la construcción de `nueva_derived`, las tres pasadas
(base / complementarias / sintéticas) y las redes M1 / código de hormigón.

### 2.2 `services/albaran-valoracion-persist/application/services/unit_converter.py`

**Sin cambio funcional.** Se amplía el comentario de cabecera de la red de
plausibilidad (líneas 21-33) con dos frases: (a) que la red vivió muerta entre
jul y ago 2026 porque el builder la llamaba con `cantidad=None`, con el caso
real 58826/58878 y sus euros; (b) que la guarda de `cantidad is None` es la
primera **a propósito** y solo debe disparar cuando la cantidad falta de
verdad. Es documentación de un defecto que costó 468.372 € de error: se escribe
donde se lee.

`_TN_UMBRAL_CONVERTIR`, `_TN_UMBRAL_AVISAR`, `_UNIDADES_TONELADA`,
`_es_tonelada` y la firma de `convert` **no se tocan** (R18). Los dos umbrales
ya son parámetros de constructor, así que si el humano quisiera ajustarlos no
haría falta tocar código.

### 2.3 `services/albaran-valoracion-persist/sv6.md`

Documentación del servicio tocado. Dos secciones:

- **§5.2** (paso 4 de la línea): el conversor se llama SIEMPRE con la cantidad
  real; `category_match` no gobierna la conversión, gobierna la revisión.
  Nombre nuevo `unidad_destino_conversion` y de dónde sale.
- **§6.3** (`UnitConverter`): la lista de casos **no menciona hoy la red de
  plausibilidad de TN**, que existe desde jul 2026. Se añaden sus dos niveles
  (≥1000 reinterpreta y ≥100 avisa) y la tabla de motivos de R19.

### 2.4 `docs/ARCHITECTURE.md`

§«Semántica de dominio imprescindible», regla 8. Hoy dice «No comparar
cantidades ni precios de unidades distintas sin pasar por el conversor». Se
completa con la segunda mitad, que es la que faltaba y costó el defecto:
**pasar por el conversor significa pasarle la cantidad**; un desacuerdo de
categoría marca revisión, nunca anula la cantidad; y la unidad de destino es la
de la línea que pone el precio.

### 2.5 `progress/current.md`

Decisiones abiertas y verificaciones MANUAL, según el protocolo del arnés.

---

## 3. Ficheros que NO se tocan (los colindantes que tentarían)

| Fichero | Por qué no |
|---|---|
| `application/services/unit_category_guard.py` | Se comporta bien: clasifica y avisa. El defecto no es que dijera `False`, es lo que el builder hacía con ese `False`. (Lo mismo concluye F-025.) |
| `config/unit_registry.yaml` | R18. Además es ruta sensible por sí misma; no hay motivo para tocarla. |
| `application/services/partida_matcher.py` | **F-031**. Aquí solo se LEE `derived_line.unidad_medida`; la elección de línea de contrato no se roza (R23). |
| `application/services/price_reconciler.py` | **F-019** lo está reescribiendo. F-027 no lo mira. |
| `application/services/importe_calculator.py` | Su cascada `convertida → albarán` es correcta y es la red de último recurso; se conserva entera (R5). **F-019** también lo toca. |
| `services/albaranes-api/config/prompts*.yaml` | **F-024** (R24). Tocarlo dispararía la puerta de evals sobre prompts sin necesidad. |
| `services/albaranes-front/**` | sv4 ya usa `cantidad_convertida` con fallback (R27): no hay nada que corregir, solo que verificar. |
| `services/albaranes-comun/**` | El contrato de mensajes no cambia. |
| Cualquier fichero de sv1, sv2, sv3, sv5 | La feature es de sv6. |

---

## 4. Riesgos y decisiones

### D1 — Se elige **convertir siempre** (opción A), no un guard previo de TN (opción B)

Las tres opciones estudiadas:

| | Qué hace | Veredicto |
|---|---|---|
| **A. Convertir primero, decidir revisión después** | Una sola llamada a `convert()` con la cantidad real; `category_match=False` solo marca revisión. | **ELEGIDA** |
| **B. Guard previo e independiente de plausibilidad TN** | Sacar el bloque `>=1000 → /1000` a un componente nuevo que corre antes del guard de categoría. | Descartada |
| **C. Pasar `category_match` como parámetro a `convert()`** | El conversor decide qué redes aplica según el desacuerdo. | Descartada |

**Por qué A.** El defecto no es «falta una comprobación de toneladas»: es que
el builder **ciega deliberadamente al componente que sabe de unidades**. Con la
rama `else` viva, TODAS las redes internas del conversor mueren en el caso
`unknown`, no solo la de TN: también `no_albaran_unit_assumed_same`,
`no_contract_unit_assumed_same` y la conversión real por registro cuando la IA
se equivocó al declarar el desacuerdo. A arregla la clase entera de defectos;
B arregla un síntoma. Y A **quita** código (cinco líneas y una rama), que es la
forma más barata de no volver a tener el problema: menos superficie, menos
mutantes, menos que mantener.

**Por qué no B.** (a) Parte la semántica de unidades en dos sitios —el registro
de unidades y su fachada están en `UnitConverter`, que es donde el equipo va a
buscar—, contra la regla de `CLAUDE.md` de no duplicar lógica compartida.
(b) Deja intactas las otras redes muertas: el mismo bug reaparecería con
`M3`/`L`, o con `KG` real contra `TN` cuando la IA declara desacuerdo.
(c) Añade un componente a un servicio ya denso (5 servicios compuestos por el
builder), cuando la corrección correcta es borrar una rama.

**Por qué no C.** El conversor tendría que conocer la semántica del guard,
ampliando su contrato público (R18 lo prohíbe) para expresar algo que ya sabe
decir por sí mismo: cuando las categorías son incompatibles de verdad,
`convert()` ya devuelve `None` (fila `UD → M3` de §1.2). C paga complejidad por
una protección redundante.

### D2 — Riesgo asumido: la conversión también se aplicará cuando la IA declaró desacuerdo

Con A, si la IA devuelve `unidad_category_match=false` (guard caso 1) pero las
unidades son realmente convertibles (`KG` → `TN`), el sistema pasará a
convertir en vez de usar la cantidad cruda. **Es deliberado y es mejor**:
convertir bien y marcar revisión (R2 mantiene el `review_required`) domina
estrictamente a valorar mal y marcar revisión. Pero es un cambio de número en
un caso que hoy no se cubre, así que se fija con test propio y se anota aquí
para que el reviewer no lo lea como efecto colateral no visto.

### D3 — Riesgo asumido: el umbral de 1000 puede reinterpretar un albarán legítimo

Si existiera un albarán con `>= 1000` unidades reales contra un contrato en TN
y sin unidad impresa, la cantidad se dividiría por 1000. El comentario de
jul 2026 argumenta que no existe («un camión lleva 25-30 TN; ningún albarán
real trae >= 1000 TN») y el caso siempre queda `ambiguous=True` →
`review_required=true`, así que **ningún importe reinterpretado llega al
revisor sin bandera**. Riesgo aceptado; escape sin tocar código: los dos
umbrales son parámetros del constructor de `UnitConverter`.

### D4 — La feature no arregla el precio, y eso se dice en la spec

Tras F-027 el 58826 queda en **468,76 €**, no en los 390,99 € del ground
truth: los 77,77 € restantes son la línea de contrato equivocada (15,43 €/TN
caliza en vez de 12,87 €/TN grava), que es **F-031**. Prometer 390,99 € aquí
sería vender un arreglo que esta feature no hace. Los requisitos R11 y R12
fijan **los dos** números para que el reviewer y la prueba local puedan
distinguir qué feature produjo cada euro.

### D5 — Ni migración ni backfill

Igual que F-019 D4: la valoración es un replace transaccional por documento y
el contexto se relee del merge, que no cambia. Re-valorar corrige. Qué
documentos históricos se reprocesan y cuándo es decisión del humano (R26).

---

## 5. Solape con F-019 (en round trip) — **el implementer parte de `dev` con F-019 mergeada**

F-019 está tocando, en su rama, ficheros que F-027 necesita. El solape es real
y hay que declararlo:

| Fichero | F-019 | F-027 | Conflicto |
|---|---|---|---|
| `application/services/price_reconciler.py` | reescribe la precedencia | no lo toca | ninguno |
| `application/services/importe_calculator.py` | ajusta redondeo/fórmula | no lo toca (lo consume) | **de número**: los tests de F-027 encadenan `convert` + `compute`; si F-019 cambia el redondeo, los importes esperados deben calcularse contra la versión mergeada |
| `application/services/valuation_builder.py` | `_build_header` (redondeo del total, F-019 R26) | paso 4 de `_build_line` | **textual leve**: funciones distintas del mismo fichero. Git lo resuelve, pero rebasar sobre F-019 evita ruido |
| `services/albaranes-front/.../review_repository.py` | fórmula canónica del importe (R23-R26) | **no lo toca**, solo verifica R27 | ninguno de código; sí de expectativa: el test de R27, si se escribiera, debe ir contra la versión de F-019 |
| `services/albaran-valoracion-persist/tests/` | **la crea** (F-019 T3, con su `conftest.py`) | la reutiliza | **de infraestructura**: ver §6 |
| `services/albaranes-comun/` | F-019 prevé mover ahí la fórmula del importe | no la usa directamente | ninguno hoy; si la fórmula acaba en `ruesma_comun`, F-027 la consume ya movida |

**Decisión**: F-027 se implementa **sobre `dev` con F-019 ya mergeada**. Si el
humano quisiera adelantarla, el implementer debe (a) crear él la suite de sv6
con su `conftest.py` y (b) recalcular los importes esperados de R11-R16 contra
el `ImporteCalculator` de `dev`, dejándolo escrito en `progress/impl_F-027.md`.
No es una preferencia de comodidad: los números de los tests dependen del
redondeo que F-019 está fijando.

---

## 6. Cómo se prueba, sin red y sin BBDD

Los cinco colaboradores de `ValuationBuilder` entran por constructor
(`valuation_builder.py:365-378`), así que la prueba es composición pura:

```python
registry  = YamlUnitRegistry(RAIZ_SV6 / "config" / "unit_registry.yaml")
builder   = ValuationBuilder(
    unit_category_guard=UnitCategoryGuard(registry),
    price_reconciler=PriceReconciler(tolerance_pct=2.0),
    partida_matcher=PartidaMatcher(...),
    unit_converter=UnitConverter(registry),
    importe_calculator=ImporteCalculator(tolerance_pct=5.0),
)
header, lines = builder.build(envelope=..., existing_document_already_valued=False)
```

El `ValuationEnvelope` se construye a mano con `AlbaranLineContextDto`
(`merge_line_id`, `line_index`, `cantidad`, `unidad_medida`,
`codigo_partida_albaran`) y `ContratoLineContextDto` (`contrato_line_id`,
`codigo_contrato`, `unidad_medida`, `precio_unitario`, `codigo_partida`). El
único fichero que se lee del disco es `config/unit_registry.yaml`, que es dato
versionado del propio servicio: **sin red, sin PostgreSQL, sin LLM**.

**Ubicación**: `services/albaran-valoracion-persist/tests/`, la suite que crea
F-019 (T3) con su `conftest.py` anclando `sys.path` al servicio —patrón de
`services/albaranes-api/tests/conftest.py`—. Ojo con la trampa que F-019 ya
documentó: **sv5 y sv6 no pueden compartir invocación de pytest**, porque ambos
tienen paquetes `application`/`domain`/`infrastructure` de primer nivel y
colisionan en `sys.modules`. La sección 7 bis de `init.sh` los ejecuta por
separado, cada uno con `cd` a su ruta, así que no hay nada que configurar.

---

## 7. Límite de microservicio

La feature no mueve responsabilidades: sv6 sigue siendo el dueño de las redes
deterministas de valoración y de la conversión de unidades, y el cambio ocurre
íntegramente dentro de su capa `application`. No aparece lógica que debiera
vivir en `services/albaranes-comun` (la conversión de unidades es propia de la
valoración, y hoy nadie más la necesita) ni responsabilidad que justifique un
servicio nuevo. **No procede** proponer extracción.

Lo que sí cruza frontera es una **capa que falta aguas arriba** —la revisión
razonada de plausibilidad de IA2 (R24)—, y por eso se especifica en F-024
(sv2), no aquí. Es el reparto correcto: la extracción valida lo que lee, la
valoración se protege de lo que le llega.

---

## 8. SQL y schema

Ninguno. No hay ficheros `.sql` en el repositorio (convención de
`docs/CONVENTIONS.md`: DDL inline en Python) y esta feature no crea ni altera
tablas ni columnas. Las columnas implicadas —`albaran_line_valuations`:
`cantidad_albaran`, `cantidad_convertida`, `factor_conversion`,
`unidad_category_match`, `review_reasons_json`, `importe_calculado`; y
`albaran_valuations.total_valorado`— **ya existen y no cambian de tipo ni de
nombre**, así que `docs/ARCHITECTURE.md` regla 3 (listar lectores ante un
cambio de schema) no se activa. Lo que cambia es el **valor** que se escribe en
`cantidad_convertida` y `factor_conversion`, y su lector conocido es sv4
(`review_repository.py`), contemplado en R27.

---

## 9. Decisiones abiertas que necesita validar el humano

1. **D2** — ¿se acepta convertir también cuando IA3 declaró
   `unidad_category_match=false` pero las unidades son convertibles de verdad?
   (Alternativa: seguir respetando ciegamente el juicio de la IA y valorar con
   la cantidad cruda, que es lo que hoy produce el ×1000.)
2. **D3** — ¿se confirma el umbral de 1000 para reinterpretar KG→TN, con la
   justificación de que ningún albarán real trae ≥ 1000 TN?
3. **F-025** — al desaparecer la rama que pasaba `cantidad=None`, el motivo
   falso `no_quantity_in_albaran` deja de emitirse solo. ¿F-025 se reduce a
   verificar que ningún lector dependía del string, o se cierra? **Decisión del
   humano antes de arrancarla** (R22).
4. **R26** — ¿se re-valoran los documentos ya persistidos con importes
   inflados (58826 con 468.763,40 € y 58878 con 462.282,80 € en la BBDD
   local)? ¿Cuáles y cuándo? La feature no trae script de backfill.
5. **Orden de implementación** — se asume `dev` con **F-019 mergeada** (§5).
   Confirmar, o aceptar el sobrecoste descrito de adelantarla.
