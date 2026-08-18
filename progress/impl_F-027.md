<!-- progress/impl_F-027.md -->
# F-027 · Error de ×1000 en el importe: la red KG→TN de `UnitConverter` es código muerto · Informe de implementación

- **Rama**: `feature/F-027-conversion-kg-tn-muerta`, base `dev` (`e95549d`, con
  F-019 ya mergeada, que es lo que la spec asumía en su §5).
- **Rigor**: `critico`.
- **Servicio tocado**: sv6 (`services/albaran-valoracion-persist`) y solo sv6.
- **Tareas**: T1-T9 y T11 cerradas con un commit cada una. **T10 es MANUAL y
  la ejecuta el humano** (guion completo al final de este informe).
- `bash harness/init.sh` → **ENTORNO LISTO**. Cobertura de las líneas
  cambiadas **100 % (4/4, umbral 80 %)**.

---

## 1. Qué cambió, en una frase

El `ValuationBuilder` llamaba al conversor de unidades **con la cantidad
puesta a `None`** siempre que el guard de categoría decía que no, y convertía
hacia **la unidad del albarán** cuando había línea de contrato derivada. Lo
primero mataba la red de plausibilidad de toneladas; lo segundo daba factor 1
contra un precio por tonelada. Ahora se convierte **siempre con la cantidad
real** y **hacia la unidad de la línea que pone el precio**.

Son **cuatro líneas ejecutables** en un solo fichero de producción.

## 2. Ficheros tocados

| Fichero | Qué |
|---|---|
| `services/albaran-valoracion-persist/application/services/valuation_builder.py` | **el cambio**: paso «4. Unit conversion». 4 líneas ejecutables + comentario |
| `services/albaran-valoracion-persist/application/services/unit_converter.py` | **solo comentario** (24 renglones; `git diff` confirma 0 líneas ejecutables) |
| `services/albaran-valoracion-persist/sv6.md` | §5.2 y §6.3 (que no documentaba la red de toneladas pese a existir desde jul 2026) |
| `docs/ARCHITECTURE.md` | regla 8 de «Semántica de dominio» |
| `services/albaran-valoracion-persist/tests/f027_escenarios.py` | módulo de apoyo (sin prefijo `test_`) |
| `services/albaran-valoracion-persist/tests/test_f027_*.py` | 4 ficheros, 57 tests |
| `tests/test_f027_r18_r22_contrato.py` | 9 tests de contrato en la suite raíz |
| `harness/features.json`, `BACKLOG.md`, `specs/.../tasks.md` | estado de la feature |
| `progress/mutacion_F-027.md`, `progress/evals_F-027.md` | puertas |

**No se tocó** nada de sv1-sv5, ni `partida_matcher.py` (F-031), ni ningún
`prompts*.yaml` (F-024), ni `config/unit_registry.yaml`, ni la firma pública
de `convert()`. Lo vigila un test: `test_f027_r23_r24_la_feature_no_toca_ni_el_matcher_ni_ningun_prompt`,
que mide los ficheros de los commits `F-027 …` sobre `git`.

## 3. El cambio, tal cual

```python
# ANTES
if category_match and partida_result.derived_line is not None:
    unidad_contrato_para_conversion = unidad_albaran
else:
    unidad_contrato_para_conversion = unidad_contrato

if category_match:
    converted = self._converter.convert(
        cantidad=albaran_line.cantidad if albaran_line else None, ...)
else:
    converted = self._converter.convert(
        cantidad=None, ...)          # ← el defecto

# DESPUÉS
if partida_result.derived_line is not None:
    unidad_destino_conversion = (
        partida_result.derived_line.unidad_medida
    )
else:
    unidad_destino_conversion = unidad_contrato

converted = self._converter.convert(
    cantidad=albaran_line.cantidad if albaran_line else None,
    unidad_albaran=unidad_albaran,
    unidad_contrato=unidad_destino_conversion,
)
```

## 4. Decisiones de diseño

### 4.1 Se convierte siempre; `category_match=False` solo marca revisión (D1, D2)

El argumento que decide, y que está medido: **el conversor ya se niega a
cruzar categorías incompatibles**. `convert(108, 'UD', 'M3')` devuelve `None`
con `unit_category_mismatch_in_conversion` por su cuenta. Cegarlo pasándole
`cantidad=None` no protegía de nada; lo único que conseguía era matar las
redes que solo viven en el caso `unknown` —la de toneladas entre ellas—.

Consecuencia deliberada (**D2**): cuando IA3 declara `unidad_category_match =
false` pero las unidades son convertibles de verdad (KG → TN), ahora se
convierte. Convertir bien y marcar revisión domina estrictamente a valorar mal
y marcar revisión. Fijado con test propio
(`test_f027_d2_se_convierte_aunque_ia3_declare_desacuerdo_de_categoria`), y la
línea sigue saliendo con `review_required = true`.

### 4.2 La unidad de destino es la de quien pone el precio (R6, R7)

`PartidaMatcher._build_derived` inicializa la unidad de la derivada con la del
albarán y la **pisa con la de la línea de contrato casada por la IA siempre
que exista**, que es el caso normal. Por tanto la derivada lleva la unidad
**y el precio** del contrato: es ella quien multiplica, y ella fija el
destino. El nombre viejo (`unidad_contrato_para_conversion`) mentía.

Compatibilidad: cuando no hay línea de contrato de referencia,
`derived_line.unidad_medida == unidad_albaran`, que es **exactamente** el caso
para el que se escribió la expresión vieja. El cambio es un superconjunto
correcto, no una inversión — con test
(`test_f027_r6_derivada_sin_linea_de_contrato_se_comporta_igual_que_antes`).

### 4.3 El umbral de 1000 se conserva, con su riesgo escrito (D3)

Un albarán legítimo con ≥ 1000 unidades reales contra un contrato en TN se
dividiría por 1000. Riesgo aceptado y acotado: el caso siempre sale
`ambiguous → review_required`, así que **ningún importe reinterpretado llega
mudo al revisor**, y los dos umbrales son parámetros del constructor de
`UnitConverter` (ajustarlos no exige tocar código). Fijado con test propio
(`test_f027_d3_mil_unidades_legitimas_contra_un_contrato_en_tn_se_dividen`)
para que se lea como decisión y no como efecto colateral.

### 4.4 Lo que esta feature NO arregla (D4, R23)

Tras F-027 el 58826 queda en **468,76 €**, no en los 390,99 € del
administrativo. Los 77,77 € que faltan son el **precio** de contrato
equivocado (15,43 €/TN de caliza en vez de 12,87 de grava), que es **F-031**.
Los tests fijan **los dos** números —con 15,43 y con 12,87— precisamente para
que la prueba local pueda distinguir qué feature produjo cada euro.

## 5. Desviaciones respecto a la spec

**Una, y menor**: la spec (T4) proponía fijar en R14 «el mismo importe que
hoy» junto a los metadatos de conversión en el mismo test. Se han separado en
dos tests, porque no son la misma afirmación: el **importe** debe estar verde
**antes y después** (esa es toda su función como guardián de regresión),
mientras que `cantidad_convertida` y `factor_conversion` **sí cambian** de
`None` a `(cantidad, 1.0)`. Juntos, el guardián de regresión habría estado
rojo antes del cambio y no habría demostrado nada.

Nada más. El alcance, los ficheros y los números son los de la spec aprobada.

## 6. Fase RED — las trazas reales

### 6.1 T2 · el defecto, a través del builder (los requisitos centrales)

Comando, desde `services/albaran-valoracion-persist`:

```
python -m pytest tests/test_f027_r1_r2_r11_r13_builder.py -q
```

```
_________________ test_f027_r11_el_58826_no_vale_468763_euros _________________

    def test_f027_r11_el_58826_no_vale_468763_euros():
        """R11: 30.380 kg a 15,43 EUR/TN son 468,76 EUR, no 468.763,40."""
        _, linea = valorar(_mahorsa("58826", 30380.0))

>       assert linea.importe_calculado != pytest.approx(IMPORTE_MEDIDO_MAL_58826)
E       assert 468763.4 != 468763.4 ± 0.468763
E        +  where 468763.4 = LineValuationRecord(merge_line_id=621, ...).importe_calculado

tests\test_f027_r1_r2_r11_r13_builder.py:137: AssertionError
_____ test_f027_r10_una_linea_con_cantidad_no_puede_decir_que_no_la_tiene _____

        assert linea.cantidad_albaran == pytest.approx(30380.0)
>       assert "no_quantity_in_albaran" not in linea.review_reasons
E       AssertionError: assert 'no_quantity_in_albaran' not in
        ['unit_category_partially_unknown', 'only_1a_available',
         'ia_match_partida_missing_derived', 'no_quantity_in_albaran',
         'importe_using_albaran_quantity_fallback']

tests\test_f027_r1_r2_r11_r13_builder.py:124: AssertionError
=========================== short test summary info ===========================
FAILED ...::test_f027_r1_el_builder_convierte_aunque_el_guard_diga_que_no
FAILED ...::test_f027_r10_una_linea_con_cantidad_no_puede_decir_que_no_la_tiene
FAILED ...::test_f027_r11_el_58826_no_vale_468763_euros
FAILED ...::test_f027_r11_el_58826_con_el_precio_correcto_da_el_numero_del_gt
FAILED ...::test_f027_r12_el_58878_no_vale_462282_euros
FAILED ...::test_f027_r12_el_58878_con_el_precio_correcto_da_38559
FAILED ...::test_f027_r13_el_total_del_documento_esta_en_centenas_de_euros[58826-30380.0-468763.4]
FAILED ...::test_f027_r13_el_total_del_documento_esta_en_centenas_de_euros[58878-29960.0-462282.8]
FAILED ...::test_f027_d2_se_convierte_aunque_ia3_declare_desacuerdo_de_categoria
FAILED ...::test_f027_d3_mil_unidades_legitimas_contra_un_contrato_en_tn_se_dividen
FAILED ...::test_f027_r4_desde_el_builder_la_cantidad_implausible_solo_se_avisa
11 failed, 3 passed in 1.12s
```

### 6.2 T3 · la segunda mitad del ×1000 (R6, R7)

```
python -m pytest tests/test_f027_r6_r7_unidad_destino.py -q
```

```
    def test_f027_r7_con_kg_leido_el_importe_ya_no_es_de_cientos_de_miles():
        """R7: 30.380 KG a 15,43 EUR/TN son 468,76 EUR."""
        cabecera, linea = valorar(_mahorsa_con_unidad_kg())

>       assert linea.importe_calculado != pytest.approx(IMPORTE_MEDIDO_MAL)
E       assert 468763.4 != 468763.4 ± 0.468763

tests\test_f027_r6_r7_unidad_destino.py:109: AssertionError
______ test_f027_r7_la_cantidad_cruda_se_conserva_junto_a_la_convertida _______

        assert linea.cantidad_albaran == pytest.approx(30380.0)
>       assert linea.cantidad_convertida == pytest.approx(30.38)
E       assert 30380.0 == 30.38 ± 3.0e-05
E         Obtained: 30380.0
E         Expected: 30.38 ± 3.0e-05

tests\test_f027_r6_r7_unidad_destino.py:119: AssertionError
=========================== short test summary info ===========================
FAILED ...::test_f027_r6_se_convierte_hacia_la_unidad_de_la_derivada
FAILED ...::test_f027_r7_con_kg_leido_el_importe_ya_no_es_de_cientos_de_miles
FAILED ...::test_f027_r7_la_cantidad_cruda_se_conserva_junto_a_la_convertida
3 failed, 3 passed in 0.99s
```

### 6.3 T4 · la tabla de motivos y el rastro numérico (R19, R20)

```
python -m pytest tests/test_f027_r14_r20_no_regresion.py -q
...
FAILED ...::test_f027_r19_cada_estado_emite_su_motivo_y_solo_el_suyo[se convirtio aplicando la red de plausibilidad-...]
FAILED ...::test_f027_r19_cada_estado_emite_su_motivo_y_solo_el_suyo[magnitud sospechosa pero no se toco-...]
FAILED ...::test_f027_r19_cada_estado_emite_su_motivo_y_solo_el_suyo[no se pudo convertir: categorias incompatibles-...]
FAILED ...::test_f027_r20_la_reinterpretacion_deja_las_tres_columnas_coherentes
8 failed, 10 passed in 1.07s
```

Los **10 que pasan** son los guardianes de no-regresión (R14 importes, R15
Feymaco, R16 VODALAND, R17): verdes **antes y después**, que es su función.

### 6.4 T1 · el conversor aislado (fase RED por rotura deliberada)

Los tests de T1 pasan en verde desde el primer momento porque la lógica del
conversor ya era correcta: el entregable de esa tarea **es el test**. Según
CHECKPOINTS.md C4 bis, la fase RED se demuestra rompiendo lo que el test
vigila **en una copia aislada, nunca en el árbol real**. Se copió el servicio
al scratchpad de la sesión y se puso `_TN_UMBRAL_CONVERTIR = 100000.0`:

```
python -m pytest tests/test_f027_r3_r9_conversor.py -q      # sobre la COPIA

>       assert resultado.cantidad_convertida == pytest.approx(esperada), albaran
E       AssertionError: 58826
E       assert 30380.0 == 30.38 ± 3.0e-05
E         Obtained: 30380.0
E         Expected: 30.38 ± 3.0e-05

tests\test_f027_r3_r9_conversor.py:63: AssertionError
...
E       AssertionError: []           ← el warning de R21 tampoco se emite
=========================== short test summary info ===========================
FAILED ...::test_f027_r3_cantidad_sin_unidad_contra_tn_se_reinterpreta_como_kg[58826-30380.0-30.38]
FAILED ...::test_f027_r3_cantidad_sin_unidad_contra_tn_se_reinterpreta_como_kg[58878-29960.0-29.96]
FAILED ...::test_f027_r3_el_umbral_de_1000_es_inclusivo
FAILED ...::test_f027_r3_la_red_reconoce_los_literales_de_tonelada[TN]  (y tn, Tn., t, TM, Ton)
FAILED ...::test_f027_r21_la_reinterpretacion_deja_traza_en_el_log
10 failed, 8 passed in 0.54s
```

### 6.5 T7 · el guardián de los límites, verificado NO vacuo

Mismo método, sobre copias aisladas de los dos ficheros: umbral a `5000.0` y
un motivo nuevo inyectado en el builder (justo el
`conversion_skipped_unit_category_mismatch` que proponía F-025).

```
== R18 umbral, sobre la copia rota ==
   FALLA como debe: leido 5000.0 != 1000.0
== R22 inventario de motivos, sobre la copia rota ==
   FALLA como debe. Diferencia simetrica:
   ['conversion_skipped_unit_category_mismatch', 'ia_no_match']
```

## 7. Los números, antes y después (medidos con el código real, sin BBDD ni red)

| Escenario | Antes | Después |
|---|---|---|
| **58826** · 30.380 sin unidad, contrato TN a 15,43 | **468.763,40 €** | **468,76 €** (30,38 TN · factor 0,001) |
| **58878** · 29.960 sin unidad, contrato TN a 15,43 | **462.282,80 €** | **462,28 €** (29,96 TN) |
| 58826 con el precio correcto (12,87 €/TN) | 390.990,60 € | **390,99 €** ← el del administrativo |
| 58878 con el precio correcto | 385.585,20 € | **385,59 €** |
| **58826 con `KG` leído** (lo que abre F-024) | **468.763,40 €** *y sin ir a revisión* | **468,76 €** |
| Hormigón 224964 · 4 m³ a 99,90 | 399,60 € | **399,60 €** |
| Hormigón 225137 · 9 m³ a 99,90 | 899,10 € | **899,10 €** |
| Hormigón 1167 · 8 m³ a 99,90 | 799,20 € | **799,20 €** |
| Mortero 1229 · 3 m³ a 70,00 | 210,00 € | **210,00 €** |
| Feymaco 2.137.569 (total documento) | 139,66 € | **139,66 €** |
| Feymaco 2.139.643 (total documento) | 19,41 € | **19,41 €** |
| VODALAND A261584 · 377 ud a 9,00 | 3.393,00 € | **3.393,00 €** |
| `UD` contra contrato `M3` (108 ud) | 12.841,20 € (fallback crudo) | **12.841,20 €** (mismo importe, motivo distinto y cierto) |
| Línea sin cantidad | sin importe | **sin importe** |

Lo que cambia además del euro: el **motivo**. Donde antes salía
`no_quantity_in_albaran` en líneas que sí tenían cantidad (hallazgo H-2, objeto
de F-025), ahora sale el motivo cierto de cada caso.

## 8. Verificaciones MANUAL pendientes — **T10, las ejecuta el humano**

Prueba local de extremo a extremo con Azurite + PostgreSQL local
(`infra/docs/levantar-pipeline-local.md`), con los PDFs del lote
`alvaro_17082026`.

**1 · Reprocesar `Mahorsa_58826.pdf`.**

```sql
SELECT l.cantidad_albaran, l.cantidad_convertida, l.factor_conversion,
       l.precio_unitario_final, l.importe_calculado, l.review_reasons_json
  FROM albaran_line_valuations l
  JOIN albaran_valuations v ON v.id = l.valuation_id
 WHERE v.document_id = (SELECT id FROM albaran_documents_merge
                         WHERE numero_albaran = '58826');
```

Debe salir: `cantidad_albaran = 30380`, `cantidad_convertida = 30.38`,
`factor_conversion = 0.001`, `review_reasons_json` **con**
`cantidad_sin_unidad_reinterpretada_kg_a_tn` y **sin**
`no_quantity_in_albaran` (R10).

```sql
SELECT total_valorado FROM albaran_valuations
 WHERE document_id = (SELECT id FROM albaran_documents_merge
                       WHERE numero_albaran = '58826');
```

Debe estar en **centenas de euros**: **468,76 €** con el precio que hoy elige
IA3. **NO saldrán los 390,99 € del administrativo**: los 77,77 € que faltan
son el precio de contrato equivocado, que es **F-031** y queda fuera a
propósito (decisión D4 de la spec).

**2 · Ídem con `Mahorsa_58878.pdf`**: 29.960 → **29,96 TN**, total **462,28 €**
(el del administrativo, 385,59 €, llegará con F-031).

**3 · El warning que nunca se había emitido** (R21). En
`services/albaran-valoracion-persist/logs/`:

```
[unit-converter] cantidad 30380.0 sin unidad con contrato en TN:
                 reinterpretada como KG -> 30.38 TN
```

Su **ausencia** en los logs del 2026-08-18 es, en sí misma, la prueba de que
la red estaba muerta. Si tras esta feature sigue sin aparecer, algo no llegó a
ejecutarse.

**4 · Un hormigón del mismo lote** (224964 o 1167): su importe debe ser
**idéntico** al de la corrida del 2026-08-18 — 475,60 € y 871,20 € de total de
documento (R14).

**5 · Abrir el 58826 en sv4 y guardar sin cambiar nada** (R27): el importe no
debe moverse. sv4 usa `cantidad_convertida` con fallback a `cantidad_albaran`
(`review_repository.py`), así que el 30,38 que escribe sv6 debe ser también el
que use el front. Es el paso que destapó el fallo de F-019, y por eso se
repite aquí.

**6 · Histórico (R26)**: los 468.763,40 € del 58826 y los 462.282,80 € del
58878 **siguen persistidos** hasta que se re-valoren. No hay script de
backfill (decisión cerrada al aprobar la spec): se sanean revalorando desde
sv4 → `q-valoracion`. Qué documentos y cuándo lo decide el humano.

---

# Evidencias

| Evidencia | Valor |
|---|---|
| **Tests ejecutados y resultado** | **635 tests, 635 passed, 0 failed**. Raíz 262 · sv2 56 · sv3 88 · sv4 59 · sv5 11 · **sv6 110** · comun 49. De ellos, **66 son de F-027** (57 en sv6, 9 en la suite raíz) |
| **Cobertura de las líneas cambiadas** | **100,0 % (4/4)**, umbral 80 %, nivel `critico`. Línea `PUERTA COBERTURA` de `bash harness/init.sh` |
| **Mutantes generados y supervivientes** | Campaña automática: **0 mutantes** (punto ciego de la herramienta, ver abajo). Campaña **manual**: **7 generados, 7 muertos, 0 supervivientes**. Detalle en `progress/mutacion_F-027.md` |
| **Tiempo de ejecución de la suite** | **58,5 s** en total, medido suite a suite: raíz 36,6 s · comun 16,0 s · sv3 2,4 s · sv2 1,2 s · sv4 1,1 s · **sv6 0,7 s** · sv5 0,6 s |

## La campaña de mutación merece leerse entera

`python -m harness.mutacion --feature F-027` devuelve **0 mutantes**. Eso no
es un aprobado: es una medición vacía, y presentarla como «0 supervivientes»
sería vender una puerta que no se ha cruzado.

**La causa es un punto ciego de la herramienta**, verificado sobre su propia
tabla de operadores: `harness/mutacion.py` muta `==`, `!=`, `<`, `<=`, `>`,
`>=`, `+`, `-`, `*`, `//`, `and`, `or`, `not` y las constantes `bool`/`int`,
y **`ast.Is` / `ast.IsNot` no están en `COMPARACIONES`**. Las cuatro líneas
ejecutables de F-027 son un `is not None`, dos asignaciones y una expresión
condicional: ninguna cae en ese catálogo. Los 24 renglones en alcance de
`unit_converter.py` son todos comentario.

**Es caro**: `is` / `is not` es el operador con el que Python escribe casi
todas sus guardas de ausencia. Ampliar la tabla sería una mejora del arnés que
hay que **portar a `arnes-base`** (regla de propagación de `CLAUDE.md`), y por
eso **no se ha hecho dentro de F-027**: cambiaría la herramienta que mide a
todas las features de todos los proyectos, y eso lo decide el humano. Queda
propuesto en `progress/current.md`.

En su lugar se hizo la campaña **a mano**: 7 mutantes, uno por cada mutación
posible de esas cuatro líneas, cada uno aplicado a una **copia aislada** de
sv6 y evaluado con su suite entera, **en serie**. **7 muertos, 0
supervivientes.**

**Y encontró un agujero real.** El mutante M7 —`if albaran_line else None` →
`else 0.0`— **sobrevivió a los 109 tests** en la primera pasada. El test de R8
que había construía la línea de albarán **con** contexto y `cantidad=None`, de
modo que `albaran_line` era un objeto y la rama `else` no se ejercitaba nunca.
Con ese mutante vivo, una línea sin contexto de albarán se habría valorado en
**0,00 € con `importe_source='calculated'`** — un importe inventado con pinta
de calculado. Se añadió
`test_f027_r8_una_linea_sin_contexto_de_albaran_no_inventa_cantidad` y M7
muere. Es el mejor argumento a favor de tapar el punto ciego de la
herramienta: si el operador `is not` se hubiera mutado desde el principio, ese
hueco habría salido solo.

## Puerta de rutas sensibles (R25, C4 ter)

El diff toca **2 rutas sensibles** declaradas en `harness/rutas_sensibles.json`
(`unit_converter.py` y `valuation_builder.py`, motivo «redes deterministas de
sv6»), así que la puerta exige la pasada completa de evals.

**La pasada declarada no se pudo ejecutar.** Salida literal de
`python -m evals.runner --con-llm --feature F-027`:

```
no se puede lanzar la pasada completa: faltan en el entorno
GEMINI_API_KEY, OPENAI_API_KEY. No se ha consumido ningún caso.
```

Son secretos y no viven en el repositorio. **La variante determinista sí
corrió** y demuestra que la causa de fondo es otra y anterior:
`evals/fixtures/inputs/` solo contiene `_indice.json`, es decir **0 casos**,
así que la pasada completa daría `NO_EVALUABLE` igual. Informe en
`progress/evals_F-027.md`, veredicto `NO_EVALUABLE`.

Exigencia declarada: **`aviso`** (decisión D5 de F-011), de modo que no
bloquea el cierre pero **no se marca N/A a secas**: el motivo queda escrito
aquí y el reviewer lo recoge en C4 ter. Es el mismo estado en que quedó F-019.

## Coordinación con las features vecinas

- **F-025** (`no_quantity_in_albaran` como falsa alarma) **pierde su caso
  principal**: proponía emitir `conversion_skipped_unit_category_mismatch` en
  la rama `else` que F-027 elimina. Al no haber ya conversión omitida a
  propósito, el motivo vuelve a significar lo que dice, y esta feature no
  renombra ni añade ningún string (R22, con test). **Su alcance debe
  reevaluarlo el humano antes de arrancarla.**
- **F-024** (la unidad que IA1 no extrae) queda **preparada, no resuelta**: el
  escenario que activa —albarán con `KG` leído contra contrato en `TN`— es
  justo el que R6/R7 arreglan aquí, así que cuando IA1 empiece a extraer la
  unidad, esos albaranes ya no producirán el ×1000. La revisión razonada de
  plausibilidad de IA2 que pidió el humano **sigue siendo necesaria** (R24):
  IA2 detecta arriba, sv6 protege abajo, y que la red de sv6 funcione no
  legitima que el dato siga llegando mal desde la extracción.
- **F-031** (elección de línea de contrato) queda **intacta a propósito**
  (R23): el precio 15,43 €/TN sobrevive a esta feature, y los tests fijan los
  importes con los dos precios para que se pueda separar qué feature produjo
  qué euro.
- **F-026** (guard de partida antes de derivar) no se roza: F-027 solo **lee**
  `derived_line.unidad_medida`.
