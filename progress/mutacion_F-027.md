<!-- progress/mutacion_F-027.md -->
# F-027 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-027` el 2026-08-19 00:37.
> **Medida con el arnés 1.5.2, que NO mutaba `is`/`is not`. Re-medida con el 1.6.0 (F-034): 1 mutante en vez de 0, y muerto — ver `progress/mutacion_F-027_remedida.md`.**

## Alcance

Origen del diff: **rama** (`e95549d8880ebdabee45c1ec4fbe20651240428f` .. `feature/F-027-conversion-kg-tn-muerta`).

| Fichero | Líneas en alcance |
|---|---|
| `services/albaran-valoracion-persist/application/services/unit_converter.py` | 24 |
| `services/albaran-valoracion-persist/application/services/valuation_builder.py` | 34 |
| **Total** | **58** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 0 |
| Mutantes evaluados | 0 |
| Muertos | 0 |
| Supervivientes | 0 |
| Timeouts | 0 |
| Tiempo total | 0.0 s |
| Muestreo | no: campaña completa |

## Supervivientes

Ninguno: cada mutación aplicada la cazó al menos un test.


---

# Complemento MANUAL de la campaña (F-027)

> Todo lo de arriba lo escribe `python -m harness.mutacion`. Esto lo
> escribe el implementer, y dice por qué la campaña automática salió en
> **0 mutantes** y qué se hizo en su lugar. Un «0 supervivientes» sobre
> 0 mutantes no demuestra nada: sin este complemento, la puerta de
> mutación de F-027 estaría vacía.

## Por qué la herramienta genera 0 mutantes

`harness/mutacion.py` sabe mutar comparaciones (`==`, `!=`, `<`, `<=`,
`>`, `>=`), aritmética (`+`, `-`, `*`, `//`), operadores lógicos
(`and`/`or`), el `not` unario y las constantes `bool` e `int`.
Comprobado sobre la tabla real del módulo:

```
Operadores de comparacion que la herramienta sabe mutar:
    Eq, NotEq, Lt, LtE, Gt, GtE
ast.Is / ast.IsNot presentes: False False
```

El cambio de producción de F-027 son **cuatro líneas ejecutables** y
ninguna cae en ese catálogo:

| Línea cambiada | Nodo AST | ¿Mutable por la herramienta? |
|---|---|---|
| `if partida_result.derived_line is not None:` | `Compare(IsNot)` | **no** — `ast.IsNot` no está en `COMPARACIONES` |
| `unidad_destino_conversion = (…unidad_medida)` | `Assign` | no |
| `unidad_destino_conversion = unidad_contrato` | `Assign` | no |
| `cantidad=albaran_line.cantidad if albaran_line else None` | `IfExp` | no |

Los 24 renglones en alcance de `unit_converter.py` son **todos
comentario** (T6 no cambió una sola línea ejecutable), así que de ahí no
podía salir ningún mutante tampoco.

**Es un punto ciego de la herramienta, no de la feature**, y es un punto
ciego caro: `is` / `is not` es el operador con el que Python escribe
casi todas sus guardas de ausencia. Ampliar `COMPARACIONES` con
`ast.Is` / `ast.IsNot` sería una mejora del arnés que hay que **portar a
`arnes-base`** (regla de propagación de `CLAUDE.md`), y por eso NO se
hace dentro de F-027: cambiaría la herramienta que mide a todas las
features de todos los proyectos, y eso lo decide el humano. **Queda
propuesto en `progress/current.md`.**

## Campaña manual: 7 mutantes, 7 muertos

Uno por cada mutación posible de las cuatro líneas ejecutables, más las
dos variantes de destino que reproducen el defecto corregido. Cada
mutante se aplicó a una **copia aislada** de sv6 (nunca al árbol real) y
se ejecutó su suite entera, **en serie**.

| Id | Mutación | Qué vigila | Resultado |
|---|---|---|---|
| **M1** | `derived_line is not None` → `is None` | invierte la guarda de la derivada | **MUERTO** (17 fallos) |
| **M2** | `cantidad=… if albaran_line else None` → `cantidad=None` | **restaura el defecto original de F-027** | **MUERTO** (26 fallos) |
| **M3** | `unidad_contrato=unidad_destino_conversion` → `=unidad_albaran` | la otra mitad del ×1000 | **MUERTO** (23 fallos) |
| **M4** | rama `else`: destino `unidad_contrato` → `unidad_albaran` | destino sin derivada | **MUERTO** (9 fallos) |
| **M5** | rama con derivada: destino `derived_line.unidad_medida` → `unidad_albaran` | vuelve al destino de antes de F-027 | **MUERTO** (14 fallos) |
| **M6** | `unidad_albaran=unidad_albaran` → `=None` | borra la unidad de origen | **MUERTO** (3 fallos) |
| **M7** | `if albaran_line else None` → `else 0.0` | la guarda de línea de albarán ausente | **MUERTO** (1 fallo) |

**7 generados · 7 muertos · 0 supervivientes.**

### M7 sobrevivió en la primera pasada, y por eso existe un test más

En la primera vuelta M7 pasó los 109 tests sin que ninguno se inmutara.
El agujero era real y de forma: el test de R8 que había construía una
línea de albarán **con** `cantidad=None`, así que `albaran_line` era un
objeto y la expresión `if albaran_line else None` nunca tomaba su rama
`else`. Nadie probaba el caso de que **no exista contexto de línea**.

Con el mutante vivo, una línea sin contexto de albarán se habría
valorado en **0,00 € con `importe_source='calculated'`** —un importe
inventado con pinta de calculado— en vez de quedarse sin importe y pedir
revisión.

Se añadió
`test_f027_r8_una_linea_sin_contexto_de_albaran_no_inventa_cantidad`
(`tests/test_f027_r1_r2_r11_r13_builder.py`), que arma un envelope con
la línea de IA3 apuntando a un `merge_line_id` ausente de
`context.lineas_albaran`. Con él, M7 muere.

### Cómo reproducirlo

El guion de la campaña manual vive en el scratchpad de la sesión
(`mutacion_manual.py`), fuera del repositorio a propósito: es andamiaje
de verificación, no código del producto. Reconstruirlo es mecánico —
copiar `services/albaran-valoracion-persist` a un directorio temporal,
aplicar una de las siete sustituciones de la tabla y lanzar
`python -m pytest tests -q` desde la copia— y las sustituciones están
escritas arriba con el texto exacto.
