<!-- progress/mutacion_F-003.md -->
# F-003 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-003` el 2026-08-15 13:31.

## Alcance

Origen del diff: **rama** (`c9bd5df571e750da532d212181ab80b44d26057e` .. `feature/F-003-valorados-match-estricto`).

| Fichero | Líneas en alcance |
|---|---|
| `services/albaran-valoracion-api/application/pipelines/value_albaran_pipeline.py` | 17 |
| `services/albaran-valoracion-api/application/services/unit_category_prefilter.py` | 2 |
| `services/albaran-valoracion-api/domain/models/valuation_context.py` | 13 |
| `services/albaran-valoracion-api/domain/ports/valuation_context_repository.py` | 18 |
| `services/albaran-valoracion-api/infrastructure/database/sqlalchemy_valuation_context_repository.py` | 59 |
| `services/albaran-valoracion-persist/application/services/atributo_sustantivo_guard.py` | 229 |
| `services/albaran-valoracion-persist/application/services/guard_aritmetico.py` | 191 |
| `services/albaran-valoracion-persist/application/services/valuation_builder.py` | 139 |
| `services/albaran-valoracion-persist/config/settings.py` | 23 |
| `services/albaran-valoracion-persist/domain/models/valuation_envelope.py` | 27 |
| `services/albaran-valoracion-persist/interface_adapters/api/app.py` | 6 |
| `services/albaran-valoracion-persist/interface_adapters/composition.py` | 6 |
| `services/albaranes-api/domain/models/albaran_models.py` | 23 |
| `services/albaranes-persistencia/application/services/albaran_confidence_service.py` | 66 |
| `services/albaranes-persistencia/application/services/descuento_cascada.py` | 75 |
| `services/albaranes-persistencia/domain/models/extraction_models.py` | 22 |
| `services/albaranes-persistencia/infrastructure/database/orm_models.py` | 22 |
| `services/albaranes-persistencia/infrastructure/database/schema_contribution.py` | 18 |
| `services/albaranes-persistencia/infrastructure/database/sqlalchemy_albaran_repository.py` | 41 |
| **Total** | **997** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 87 |
| Mutantes evaluados | 87 |
| Muertos | 84 |
| Supervivientes | 3 |
| Timeouts | 0 |
| Tiempo total | 32.3 s |
| Muestreo | no: campaña completa |

## Supervivientes

Cada superviviente es una línea que ningún test comprueba de verdad, o una mutación equivalente. Distinguirlo es trabajo del implementer: ningún análisis puede quedarse sin completar al cerrar la feature.

### 1. `services/albaran-valoracion-persist/application/services/atributo_sustantivo_guard.py:180` [logico]

- Original: `if albaran_line is None or contrato_line is None:`
- Mutado:   `if albaran_line is None and contrato_line is None:`

#### Análisis (implementer, 2026-08-15)

> **Por qué ningún test lo caza:** porque el mutante NO cambia el
> comportamiento. La guarda es defensiva y redundante: si se entra al
> cuerpo con una de las dos líneas a `None`, las lecturas siguientes son
> `getattr(x, "descripcion", None)`, que devuelven `None`;
> `extraer_tokens_dimension(None)` da el conjunto vacío, no hay
> conflictos y la línea se salta igual. La única diferencia sería un
> ciclo de CPU.
> **Decisión: mutante EQUIVALENTE.** Hay dos tests que fijan el
> comportamiento observable (`..._sin_la_linea_de_contrato_no_se_toca_nada`
> y `..._sin_la_linea_de_albaran_no_se_toca_nada`): pasan con el original
> y con el mutante, que es exactamente lo que significa equivalente. La
> guarda se conserva por legibilidad: dice en voz alta que sin las dos
> descripciones no hay nada que comparar.

### 2. `services/albaran-valoracion-persist/application/services/guard_aritmetico.py:94` [comparacion]

- Original: `if descuento < 0.0 or descuento > 100.0:`
- Mutado:   `if descuento <= 0.0 or descuento > 100.0:`

#### Análisis (implementer, 2026-08-15)

> **Por qué ningún test lo caza:** el cuerpo de la rama es
> `descuento = 0.0`. Con `descuento == 0.0`, entrar en la rama (mutante)
> o no entrar (original) deja exactamente el mismo valor, así que ningún
> test puede distinguirlos: no hay observación posible.
> **Decisión: mutante EQUIVALENTE.** Los dos extremos que SÍ importan
> están cubiertos: un descuento fuera de rango se ignora
> (`..._un_descuento_fuera_de_rango_se_ignora`) y el 100 % sí se aplica
> (`..._un_descuento_del_cien_por_cien_si_se_aplica`), que era el borde
> peligroso de la comparación.

### 3. `services/albaranes-persistencia/infrastructure/database/sqlalchemy_albaran_repository.py:89` [booleano]

- Original: `return json.dumps(valores, ensure_ascii=False)`
- Mutado:   `return json.dumps(valores, ensure_ascii=True)`

#### Análisis (implementer, 2026-08-15)

> **Por qué ningún test lo caza:** `valores` es una lista de NÚMEROS
> (porcentajes de descuento). `ensure_ascii` solo cambia el volcado
> cuando hay caracteres no ASCII en el JSON, y en una lista de floats no
> puede haberlos: la cadena resultante es idéntica byte a byte.
> **Decisión: mutante EQUIVALENTE.** El test
> `test_f003_r3_la_fila_guarda_los_descuentos_como_json` comprueba lo que
> importa —que la fila guarda `[5.0, 2.0]` y se puede releer— y pasa con
> las dos variantes. `ensure_ascii=False` se mantiene por coherencia con
> el resto de volcados del repositorio.


## Veredicto del implementer

**87 mutantes, 84 muertos, 3 supervivientes, 0 timeouts (32,3 s).**

La primera pasada dejó **21 supervivientes**. **18 eran huecos reales** y
se cazaron escribiendo los tests que faltaban (no borrando mutantes): la
marca de IVA leída como texto, la red sin línea de albarán o sin línea de
contrato, la razón de la IA conservada y recortada a 500 caracteres, el
redondeo de los motivos a 2 decimales, los límites INCLUSIVOS de las tres
tolerancias, el descuento fuera de rango y el del 100 %, una línea del
lote sin contexto, una línea limpia que no debe ir a revisión y los
descuadres MODERADOS de coherencia (los astronómicos pasaban con
cualquier tolerancia, que era justo el punto ciego).

Dos de esos huecos apuntaban a código, no a tests, y se corrigieron: un
importe leído de 0 cuenta como AUSENTE (misma convención que
`ImporteCalculator` y `PriceReconciler`: una celda vacía no manda una
línea a revisión) y se retiró del comparador la rama `0 contra 0`, que ya
cubría el `1e-9` del denominador.

Los **3 supervivientes restantes están analizados uno a uno arriba y los
tres son EQUIVALENTES**: ninguno cambia el comportamiento observable.
Ninguna sección queda en PENDIENTE.
