<!-- progress/mutacion_F-038.md -->
# F-038 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-038` el 2026-08-20 14:35.

## Alcance

Origen del diff: **rama** (`34dada0a3d3973357c43f41893413485b4ae7d57` .. `feature/F-038-coste-del-ciclo-sdd`).

| Fichero | Líneas en alcance |
|---|---|
| `harness/mutacion.py` | 205 |
| `harness/mutacion_paralela.py` | 9 |
| `harness/rigor.py` | 60 |
| `harness/tamano.py` | 195 |
| **Total** | **469** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 55 |
| Mutantes evaluados | 20 |
| Muertos | 19 |
| Supervivientes | 1 |
| Timeouts | 0 |
| Sin veredicto (base rota) | 0 |
| Tiempo total | 728.5 s |
| SHA de HEAD medido | `337a948fe48f7813780e5e5b72994cc3b84dceca` |
| Línea base (s) — `.` | 52.1 |
| Media por mutante evaluado (s) | 36.4 |
| Muestreo | sí — 20 de 55 mutantes, semilla `20260820`, nivel `estandar` |

## Supervivientes

Cada superviviente es una línea que ningún test comprueba de verdad, o una mutación equivalente. Distinguirlo es trabajo del implementer: ningún análisis puede quedarse sin completar al cerrar la feature.

### 1. `harness/tamano.py:47` [booleano]

- Original: `@dataclass(frozen=True)`
- Mutado:   `@dataclass(frozen=False)`

#### Análisis (completado por el implementer)

> **Por qué ningún test lo caza:** `frozen` no cambia ni un resultado de
> `harness.tamano`. `Exceso` se construye en `medir()` y se lee en `main()`
> para imprimir `exceso.descripcion()`; **nadie le asigna un atributo nunca**,
> ni dentro del arnés ni en los tests. `frozen=False` solo retira una
> prohibición que nadie estaba infringiendo, así que ninguna entrada distingue
> las dos versiones a través del comportamiento observable de la herramienta.
>
> **Decisión: mutante equivalente para el comportamiento, justificado.**
> Matarlo exigiría un test del tipo
> `with pytest.raises(dataclasses.FrozenInstanceError): exceso.tope = 1`, que
> comprueba una garantía del lenguaje, no una regla de esta feature. El
> `frozen=True` se mantiene por la misma razón que en `Mutante`, `_Candidato` y
> `Aplicado` de `harness/mutacion.py`: un valor que viaja entre funciones no
> debe poder cambiar por el camino. La única diferencia observable sería la
> hashabilidad, y nada mete un `Exceso` en un conjunto ni en una clave de
> diccionario.
>
> Es el mismo mutante que sobrevivió en las tres campañas de esta feature (ver
> `progress/impl_F-038.md`, sección de mutación).

