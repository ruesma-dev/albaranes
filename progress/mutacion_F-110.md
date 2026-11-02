<!-- progress/mutacion_F-110.md -->
# F-110 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-110` el 2026-11-01 13:57.

## Alcance

Origen del diff: **rama** (`108cabcc2ef5ea08429e1c1e5810041559bdd8ec` .. `feature/F-110-descuento-linea-sigrid`).

| Fichero | Líneas en alcance |
|---|---|
| `services/albaranes-alta-sigrid/config/settings.py` | 11 |
| `services/albaranes-alta-sigrid/domain/models/alta_models.py` | 4 |
| `services/albaranes-alta-sigrid/domain/services/comparador_previa.py` | 41 |
| `services/albaranes-alta-sigrid/domain/services/validador_alta.py` | 71 |
| `services/albaranes-alta-sigrid/interface_adapters/composition.py` | 1 |
| `services/albaranes-alta-sigrid/main_worker.py` | 4 |
| `services/albaranes-alta-sigrid/scripts/listar_altas_descuadradas_f106.py` | 44 |
| `services/albaranes-comun/ruesma_comun/__init__.py` | 1 |
| `services/albaranes-comun/ruesma_comun/alta_sigrid.py` | 131 |
| `services/albaranes-front/config/settings.py` | 11 |
| `services/albaranes-front/domain/models/alta_sigrid_models.py` | 44 |
| `services/albaranes-front/domain/models/review_models.py` | 25 |
| `services/albaranes-front/infrastructure/database/review_repository.py` | 12 |
| `services/albaranes-front/interface_adapters/web/app.py` | 2 |
| **Total** | **402** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 108 |
| Mutantes evaluados | 108 |
| Muertos | 90 |
| Supervivientes | 18 |
| Timeouts | 0 |
| Sin veredicto (base rota) | 0 |
| Tiempo total | 4145.6 s |
| SHA de HEAD medido | `2b733f677f435ab706e8828b6f500f5803ff126c` |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-110_kzv0m2wf/wk_0/services/albaranes-alta-sigrid` | 114.9 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-110_kzv0m2wf/wk_0/services/albaranes-comun` | 130.6 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-110_kzv0m2wf/wk_0/services/albaranes-front` | 384.4 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-110_kzv0m2wf/wk_1/services/albaranes-alta-sigrid` | 114.1 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-110_kzv0m2wf/wk_1/services/albaranes-comun` | 129.4 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-110_kzv0m2wf/wk_1/services/albaranes-front` | 391.7 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-110_kzv0m2wf/wk_2/services/albaranes-alta-sigrid` | 114.7 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-110_kzv0m2wf/wk_2/services/albaranes-comun` | 131.3 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-110_kzv0m2wf/wk_2/services/albaranes-front` | 390.3 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-110_kzv0m2wf/wk_3/services/albaranes-alta-sigrid` | 115.5 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-110_kzv0m2wf/wk_3/services/albaranes-comun` | 131.4 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-110_kzv0m2wf/wk_3/services/albaranes-front` | 390.8 |
| Media por mutante evaluado (s) | 38.4 |
| Timeout efectivo por mutante (s) | 784 — derivado de la línea base × 2.0 |
| Suelo configurado (s) | 120 |
| Workers | 4 |
| Muestreo | no: campaña completa |

## Supervivientes

Cada superviviente es una línea que ningún test comprueba de verdad, o una mutación equivalente. Distinguirlo es trabajo del implementer: ningún análisis puede quedarse sin completar al cerrar la feature.

### 1. `services/albaranes-alta-sigrid/domain/services/validador_alta.py:283` [comparacion]

- Original: `cantidad_valida = cantidad is not None and abs(cantidad) > _EPSILON`
- Mutado:   `cantidad_valida = cantidad is not None and abs(cantidad) >= _EPSILON`

#### Análisis

> Por qué ningún test lo caza: Ningún test ponía la cantidad justo en `_EPSILON`: con ella F-106 ya da `cantidad_no_valida` y el mutante añadía un segundo `linea_no_cuadra` «no se puede despejar».
> Decisión: Hueco real ⇒ test nuevo `test_f110_t16_cantidad_en_el_epsilon_no_mira_r8` (sv9, `test_f110_peticion.py`).

### 2. `services/albaranes-alta-sigrid/domain/services/validador_alta.py:343` [entero]

- Original: `f"{_numero_es(round(valor, 2))} %"`
- Mutado:   `f"{_numero_es(round(valor, 3))} %"`

#### Análisis

> Por qué ningún test lo caza: El único caso no despejable era d = 100 exacto, que se escribe igual a 2 y a 3 decimales.
> Decisión: Hueco real ⇒ test nuevo `test_f110_t16_detalle_no_despejable_con_el_dto_a_dos_decimales` (d 99,996 ⇒ «100 %»).

### 3. `services/albaranes-alta-sigrid/scripts/listar_altas_descuadradas_f106.py:98` [booleano]

- Original: `dto_difiere: bool = False`
- Mutado:   `dto_difiere: bool = True`

#### Análisis

> Por qué ningún test lo caza: Todos los tests construían `Descuadre` por `comparar_alta`, que siempre pasa `dto_difiere`.
> Decisión: Hueco real (el defecto es contrato del CSV para los descuadres de F-106) ⇒ `test_f110_t16_descuadre_nace_sin_dto_difiere`.

### 4. `services/albaranes-alta-sigrid/scripts/listar_altas_descuadradas_f106.py:137` [logico]

- Original: `if estado != "aplicable" or valor is None:`
- Mutado:   `if estado != "aplicable" and valor is None:`

#### Análisis

> Por qué ningún test lo caza: Con d no aplicable los tests usaban 150 o nulo, y 7 frente a 150 difiere igual; faltaba un d «cero» con valor 0,0 y un `dto` 0 enviado.
> Decisión: Hueco real ⇒ `test_f110_t16_dto_cero_con_d_cero_sale`.

### 5. `services/albaranes-alta-sigrid/scripts/listar_altas_descuadradas_f106.py:139` [entero]

- Original: `return round(abs(dto_env - round(valor, 2)), 6) > TOLERANCIA_DTO`
- Mutado:   `return round(abs(dto_env - round(valor, 3)), 6) > TOLERANCIA_DTO`

#### Análisis

> Por qué ningún test lo caza: El d de 3 decimales del test (7,456) quedaba a 0,004 tanto de 7,46 como de sí mismo.
> Decisión: Hueco real ⇒ `test_f110_t16_dto_se_compara_con_d_a_dos_decimales` (d 7,444, `dto` 7,449: 0,009 frente a 0,005).

### 6. `services/albaranes-alta-sigrid/scripts/listar_altas_descuadradas_f106.py:139` [entero]

- Original: `return round(abs(dto_env - round(valor, 2)), 6) > TOLERANCIA_DTO`
- Mutado:   `return round(abs(dto_env - round(valor, 2)), 7) > TOLERANCIA_DTO`

#### Análisis

> Por qué ningún test lo caza: `round(x, 6)` frente a `round(x, 7)` solo limpia el ruido binario (~1e-15) de la resta; con `dto` y d de 2–3 decimales el resultado comparado con 0,005 es el mismo con 6 o 7 decimales.
> Decisión: Mutante equivalente: no hay entrada de 2–3 decimales cuya diferencia cambie de lado del 0,005 entre 6 y 7 decimales (comprobado en el borde 7 frente a 7,005 / 6,995, que ya cubre `test_f110_r19_borde_del_dto`).

### 7. `services/albaranes-alta-sigrid/scripts/listar_altas_descuadradas_f106.py:170` [entero]

- Original: `factor = 1 - dto_env / 100`
- Mutado:   `factor = 2 - dto_env / 100`

#### Análisis

> Por qué ningún test lo caza: Los tests de precio distinto movían el importe muy por encima de 0,02 €: el factor no decidía.
> Decisión: Hueco real ⇒ `test_f110_t16_el_precio_distinto_pesa_sobre_el_importe_descontado` (10 × 1 −50 %: 0,0199 € pasa; con /101, 0,0201 € no).

### 8. `services/albaranes-alta-sigrid/scripts/listar_altas_descuadradas_f106.py:170` [aritmetico]

- Original: `factor = 1 - dto_env / 100`
- Mutado:   `factor = 1 + dto_env / 100`

#### Análisis

> Por qué ningún test lo caza: Igual que el 7.
> Decisión: Hueco real ⇒ lo mata el mismo test (factor 1,5 ⇒ 0,0597 €).

### 9. `services/albaranes-alta-sigrid/scripts/listar_altas_descuadradas_f106.py:170` [entero]

- Original: `factor = 1 - dto_env / 100`
- Mutado:   `factor = 1 - dto_env / 101`

#### Análisis

> Por qué ningún test lo caza: Igual que el 7.
> Decisión: Hueco real ⇒ lo mata el mismo test (factor 1,5).

### 10. `services/albaranes-comun/ruesma_comun/alta_sigrid.py:183` [entero]

- Original: `return 2`
- Mutado:   `return 3`

#### Análisis

> Por qué ningún test lo caza: Ningún test medía `len` de una `LineaASigrid` con `dto`; el desempaquetado usa `__iter__`, no `__len__`.
> Decisión: Hueco real (es la desviación 1: se ve como la tupla de dos de F-106) ⇒ `test_f110_t16_se_ve_como_la_tupla_de_dos_de_f106`.

### 11. `services/albaranes-comun/ruesma_comun/alta_sigrid.py:228` [logico]

- Original: `if valor is None or isinstance(valor, bool):`
- Mutado:   `if valor is None and isinstance(valor, bool):`

#### Análisis

> Por qué ningún test lo caza: Sin el filtro de booleano, `True` pasa a ser P = 1,0; los tests no tenían un `True` como precio que cuadrase al céntimo con P = 1.
> Decisión: Hueco real ⇒ `test_f110_t16_precio_booleano_no_es_p` (30 × «True» −7 % con I 27,904: se despeja 1,000143).

### 12. `services/albaranes-comun/ruesma_comun/alta_sigrid.py:244` [entero]

- Original: `return dto if dto > 0 else None`
- Mutado:   `return dto if dto > 1 else None`

#### Análisis

> Por qué ningún test lo caza: Ningún caso tenía 0 < `dto` ≤ 1.
> Decisión: Hueco real ⇒ `test_f110_t16_dto_por_debajo_de_uno_se_envia` (d 0,5).

### 13. `services/albaranes-comun/ruesma_comun/alta_sigrid.py:255` [booleano]

- Original: `con_descuento: bool = False,`
- Mutado:   `con_descuento: bool = True,`

#### Análisis

> Por qué ningún test lo caza: Todos los tests pasaban `con_descuento` explícito; el defecto apagado (lo de F-106) no se miraba.
> Decisión: Hueco real ⇒ `test_f110_t16_sin_con_descuento_es_lo_de_f106`.

### 14. `services/albaranes-comun/ruesma_comun/alta_sigrid.py:293` [entero]

- Original: `precio_p = round(precio_num, 6)`
- Mutado:   `precio_p = round(precio_num, 7)`

#### Análisis

> Por qué ningún test lo caza: Todos los P de los tests tenían ≤ 6 decimales.
> Decisión: Hueco real ⇒ `test_f110_t16_p_va_a_seis_decimales` (0,6451234 ⇒ 0,645123).

### 15. `services/albaranes-front/domain/models/alta_sigrid_models.py:183` [entero]

- Original: `dto is None or round(abs(dto_sigrid - dto), 6) > TOLERANCIA_DTO`
- Mutado:   `dto is None or round(abs(dto_sigrid - dto), 7) > TOLERANCIA_DTO`

#### Análisis

> Por qué ningún test lo caza: Como el 6: `round(…, 6)` frente a `round(…, 7)` de la diferencia de dos `dto` de 2 decimales solo quita ruido binario.
> Decisión: Mutante equivalente (mismo razonamiento que el 6; el borde 0,005 lo fija `test_f110_panel.py`).

### 16. `services/albaranes-front/domain/models/review_models.py:983` [comparacion]

- Original: `return abs(dto_sigrid - d_ficha) > TOLERANCIA_PRECIO_SIGRID`
- Mutado:   `return abs(dto_sigrid - d_ficha) >= TOLERANCIA_PRECIO_SIGRID`

#### Análisis

> Por qué ningún test lo caza: `>` frente a `>=` con 1e-6 solo cambia si la diferencia en coma flotante es exactamente 1e-6. Búsqueda exhaustiva de x = 0,001…99,999 (paso 0,001) con `(x + 1e-6) - x == 1e-6`: ninguna.
> Decisión: Mutante equivalente para `dto` y d reales (0–100 con ≤ 3 decimales).

### 17. `services/albaranes-front/domain/models/review_models.py:2051` [booleano]

- Original: `alta_enviar_dto: bool = False`
- Mutado:   `alta_enviar_dto: bool = True`

#### Análisis

> Por qué ningún test lo caza: Los tests de la plantilla pasaban siempre `alta_enviar_dto`; el defecto no se miraba.
> Decisión: Hueco real (R14: nace apagada) ⇒ `test_f110_t16_la_ficha_nace_sin_data_alta_dto`.

### 18. `services/albaranes-front/infrastructure/database/review_repository.py:1815` [booleano]

- Original: `con_descuento: bool = False,`
- Mutado:   `con_descuento: bool = True,`

#### Análisis

> Por qué ningún test lo caza: `_marcar_cuadre` se llama siempre con `con_descuento` explícito desde el repositorio.
> Decisión: Hueco real (R14) ⇒ `test_f110_t16_marcar_cuadre_nace_sin_descuento`.


## Cierre (implementer)

- 15 de los 18 supervivientes eran huecos reales, cubiertos por 13 tests nuevos `test_f110_t16_*` (el 7, el 8 y el 9 los mata el mismo). Cada mutante se reaplicó a mano
  sobre el fichero y su test nuevo falla (`1 failed`); el original pasa.
- 3 equivalentes justificados (6, 15, 16). Puntuación efectiva: 105 / 108 muertos o cazados (97,2 %), 3 equivalentes.
