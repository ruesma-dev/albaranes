<!-- progress/impl_F-084_T14.md -->
# F-084 · T14, línea base con LLM: cifras y análisis de R28

Detalle enlazado desde `progress/impl_F-084.md`. Solo recuentos: los informes del
runner (`progress/evals_F-084.md` y `progress/evals_F-084-humo.md`) imprimen
«esperado X, obtenido Y» con precios e importes de proveedor y **no se versionan**
(`.gitignore`, desde el 18-sep-2026). Se regeneran con los comandos de T14
(`progress/current.md`).

## La pasada (humano, 2026-10-23, en el worktree, HEAD `b4cde93`)

`python -m evals.runner --con-llm --fases IA3,IA4,E2E --feature F-084`, sin
`--proveedores`: `openai` `gpt-6.1-sol` (R20, D1). Unos 15 minutos, ROJO, exit 1.

| Fase | Evaluados | Omitidos | ERROR | Estados | Fallos críticos | «obtenido None» | Avisos |
|---|---|---|---|---|---|---|---|
| IA3 | 59 | 0 | 0 | ROJO 58 · VERDE 1 | 212 | 137 | 54 |
| IA4 | 13 | 46 (sin caso en el libro IA4) | 0 | ROJO 13 | 27 | 27 | 0 |
| E2E | 59 | 0 | 0 | ROJO 52 · VERDE 7 | 312 | 164 | 0 |

- `- Modelo: gpt-6.1-sol` en las tres fases; `- Documento del contrato: md 5 ·
  pdf 24 · ninguno 30` (los 30 son los 13 contratos que no están en
  `albaran_contratos_merge`).
- **Coste real: no consta.** El runner no mide tokens (el medidor es del
  comparador de F-083); la estimación de `comparar_modelos --estimar` es la única
  cifra de coste.
- **Humo** (`progress/evals_F-084-humo.md`, ALQ-001, GEN-002, RES-010): IA3 19
  fallos (3 · 11 · 5), IA4 1 evaluado con 3, E2E 23 (6 · 11 · 6); 0 ERROR; md 0 ·
  pdf 1 · ninguno 2. ALQ-001 y GEN-002 dan en IA3 los mismos fallos que en la
  pasada de 59 casos.

## Frente al determinista (`daa6293`, con R37)

| Fase | Determinista | Con LLM | Diferencia |
|---|---|---|---|
| IA3, fallos críticos | 386 | 212 | −174 |
| IA3, líneas sin precio (`precio_source` None) | 91 | 8 | −83 |
| IA3, `importe_calculado` / `precio_unitario_final` None | 90 / 90 | 7 / 7 | −83 / −83 |
| IA3, `codigo_partida_final` None | 86 | 86 | 0 |
| IA3, `sinteticas_esperadas` sin pareja | 28 | 28 | 0 |
| IA4 | 13 VERDE, 0 fallos | 13 ROJO, 27 fallos | el determinista concilia con el libro |
| E2E, fallos críticos | 563 | 312 | −251 |

El emparejamiento que el determinista no mide (R36) es justo lo que cambia: de
91 líneas sin precio a 8. Lo que no cambia (partida y sintéticas) no depende
del modelo.

## Valoración frente a emparejamiento (aclaración del humano, 2026-10-23)

**Diseño que describe el humano:** casar líneas es solo cosa de IA4; IA3 valora.
IA4, con las líneas ya valoradas, filtra las líneas del contrato en Sigrid con el
mismo precio unitario (±0,02 €) y el mismo código de partida, y entre esas casa
por el significado de la descripción.

**Lo que hace hoy el código** (visto por el líder): IA3 (`valuation_es`) también
empareja, porque emite `codigo_producto_contrato` y `match_method`; IA4
(`conciliacion_es`, `services/albaran-valoracion-api/prompts.yaml` 1135-1237)
solo concilia en lote las líneas que quedan sin match, por concepto, sin
prefiltro de precio ni de partida. Atribución según el código de hoy:

| Fallos críticos | Campos | Fase hoy | Fallos | Líneas |
|---|---|---|---|---|
| Valoración | `importe_calculado` 33, `precio_unitario_final` 25, `precio_source` 18 | IA3 | 76 | 36 |
| Emparejamiento | `match_method` 13, `codigo_producto_contrato` 7 | IA3 (por diseño, IA4) | 20 | 13 |
| Emparejamiento | `conciliacion.precio_unitario_esperado` 20 (None), filas de `conciliacion` sin pareja 7 | IA4 | 27 | — |
| No observable aquí | `codigo_partida_final` 86 | sv6, desde el albarán | 86 | 86 |
| Libro sin clave | `sinteticas_esperadas` 28 filas (+2 campos) | — | 30 | — |

- 5 de las 36 líneas con fallo de valoración tienen también un fallo de
  emparejamiento (14 de los 76 fallos): ahí el precio falla porque la línea casó
  mal. En las otras 31, 8 son líneas sin precio, y en muchas el libro deja el
  emparejamiento en `?`, así que su causa puede ser también el emparejamiento
  sin que el banco lo vea.
- **El banco apenas mide el emparejamiento:** IA4 solo tiene libro en 13 casos
  (46 OMITIDO, «sin caso en el libro IA4»), y en IA3 el libro deja en `?` el
  código de contrato de 77 líneas.
- **Diferencia con el diseño:** hoy el emparejamiento se reparte entre IA3 (casi
  todo) e IA4 (las que quedan), y ninguno filtra por precio ±0,02 € ni por
  partida. Medido así, los fallos de emparejamiento de IA3 cuentan como de IA3.
  **No se resuelve en F-084**: el líder propone al humano una feature aparte.

## R28: «obtenido None» ≤ 20 % de los fallos críticos de IA3

**Tal cual: 137 de 212 = 64,6 % → R28 en ROJO** (0 ERROR y modelo en el
informe, sí). Desglose de los 137: `codigo_partida_final` 86, filas de
`sinteticas_esperadas` sin pareja 28, `precio_source` 8, `importe_calculado` 7,
`precio_unitario_final` 7 y `sinteticas_esperadas.precio_unitario` 1.

### `codigo_partida_final` no es observable en este banco (confirmado)

- **IA3 no la produce.** sv5 empareja línea y precio; la partida la pone sv6
  (`services/albaran-valoracion-persist/application/services/partida_matcher.py`)
  desde la **partida del albarán** (`codigo_imputacion`, que lee IA1): ALM ⇒
  sin partida; albarán sin partida ⇒ sin partida (almacén, F-051) o
  `no_action`; con partida ⇒ la del albarán o la de la línea de contrato con
  esa partida. sv6 no la deduce de otra cosa.
- **INPUTS no trae la partida del albarán:** `codigo_imputacion` vacío en las
  **110** líneas de `lineas_albaran`. De las 86: en 58 el libro IA1 sí la
  afirma, en 25 el libro IA1 no tiene esa línea y en 3 la deja en `?`.
- Por eso salen las mismas 86 en el determinista y con LLM, y las mismas 86
  `partida_final` en E2E. **E2E tampoco la observa** con estos INPUTS: no es un
  fallo de sv6, que hace lo que debe con un albarán sin partida.

**Propuesta (D5, no aplicada; decide el humano o el reviewer).**

1. Contar `IA3.lineas_valoradas.codigo_partida_final` como **no observable en
   IA3** (como los de R26), porque esa fase no la produce. Se queda en E2E.
2. Para que E2E la mida de verdad, llevar a `INPUTS.lineas_albaran.codigo_imputacion`
   la partida que afirma el libro IA1 (58 de las 86 líneas), por el conversor o
   en el libro. Es un cambio de datos del banco, fuera de esta feature.

Sin esas 86: **51 de 126 = 40,5 %**.

### Las 28 `sinteticas_esperadas` sin pareja

El comparador empareja las sintéticas por (`num_linea_base`, `rol_linea`). En
28 filas el libro deja `rol_linea` (y `modifier_source`) en `?`, así que la
clave lleva `@@NO_COMPARAR@@` y **ninguna fila obtenida puede casar**: salen como
«fila del ground truth que el sistema no ha producido», con cualquier modelo,
también en el determinista. El sistema sí produce sintéticas: los 54 avisos de
IA3 son filas `[+]` sobrantes (`incremento_year`, por ejemplo, con la misma
cantidad que la esperada). Es una carencia del libro, no del modelo: o el
humano afirma `rol_linea` en esas 28 filas, o el comparador las empareja sin
esa clave. Las 2 filas `1/GESTION_RESIDUOS` sí casan y fallan de verdad
(cantidad y precio).

Sin las 86 partidas ni las 28 filas sin pareja: **23 de 98 = 23,5 %**, aún por
encima del 20 %. Los 23 son 8 líneas sin precio (con su importe y su precio
final) y una sintética emparejada sin precio: lo que mide el modelo.

**Criterio sin cambiar.** Contar distinto cambia el veredicto y lo que mide el
banco, no solo la contabilidad del informe: queda como desviación D5 para que
lo decida el humano o el reviewer, sin código.
