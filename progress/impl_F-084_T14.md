<!-- progress/impl_F-084_T14.md -->
# F-084 · T12–T14, líneas base: cifras y análisis de R28

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

## R28: «obtenido None» en los fallos críticos de IA3 (línea base aceptada: 23,5 %)

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

**D5, aprobada por el humano el 2026-10-23 («sí me vale») → T17.**

1. R38: `IA3.lineas_valoradas.codigo_partida_final` es **no observable en IA3**
   (consta en «Campos no observables» y no cuenta en R28); E2E la sigue midiendo.
2. R39: el banco lleva a `INPUTS.lineas_albaran.codigo_imputacion`, al cargar
   (no en el conversor ni en el libro), la partida de la línea del libro IA1 con
   su mismo número **y su misma descripción**: 56 líneas. De las 58 que se
   esperaban, 2 (FER-002 L4 y L5) no son la misma línea: IA1 numera 4 y 5 las que
   INPUTS numera 7 y 8; por número solo habrían recibido `CI.4.18` donde el final
   espera `P5.36.01`.

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

Sin las 86 partidas ni las 28 filas sin pareja: **23 de 98 = 23,5 %**, por
encima del 20 % original (ahora la línea base). Los 23 son 8 líneas sin precio (con su importe y su precio
final) y una sintética emparejada sin precio: lo que mide el modelo.

**Línea base de R28 aceptada por el humano (D5, 2026-10-23): 23 de 98 = 23,5 %**,
en lugar del 20 %: sin la partida (R38) ni las 28 sintéticas sin pareja, cuyo
arreglo es una **tarea de datos del banco** (afirmar `rol_linea` en el libro IA3),
anotada y no hecha en F-084. Con ellas dentro, lo que el banco mide hoy: **51 de
126 = 40,5 %**. Recontado del texto del informe de T14 (`b4cde93`), sin volver a
pagar. El modelo, `gpt-6.1-sol`, lo confirmó el humano (D1).

**T14 no se puede recomparar sin pagar:** el runner no guarda las respuestas de
sv5 ni los envelopes, solo el informe. Además, con R39 el contexto de IA3 lleva
ya la partida del albarán (como en producción) y T14 se tomó sin ella: una
pasada nueva mediría también ese efecto.

## Anexo · T12 (humano) y T13: línea base determinista (`b39cb0e`)

T12, 2026-10-23: `lineas` 18 contratos y 0 fallidos (3159 filas, 52 fechas);
`documentos` 20: md 1, pdf 6 y ninguno 13 (los 13, «no está en
albaran_contratos_merge»: **30 de los 59 casos van a T14 sin documento**); 6
libros y 264 ficheros. T13 versiona `evals/fixtures/inputs/` (60 ficheros), el
índice y `progress/import_F-084.md`. Barrido de lo añadido: sin URL, correo,
GUID, clave, IBAN, NIF de persona ni teléfono; los «IPv4» son partidas; los 7
CIF son de sociedades (O3). La caché sigue ignorada.

- **R27, verde:** 0 OMITIDO por R18; FER-001 `importe_calculado` 19,41 sin
  fallo (le queda `codigo_partida_final`); advertencia de R36 en las tres fases.
- **Determinista** (`python -m evals.runner --feature F-084`, ROJO): IA3 59
  evaluados, VERDE 6, ROJO 53, **394 fallos**; IA4 13 evaluados, VERDE 13, 46
  OMITIDO («sin caso en el libro IA4»); E2E VERDE 6, ROJO 53, **572 fallos**;
  0 ERROR. RES-001..007 igual que antes (RES-007 IA3 4 y E2E 6).
- **Línea base con R37** (`daa6293`): IA3 **386 fallos** (−8), E2E **563** (−9);
  mismos estados por caso (FER-002 IA3 15 → 8, FER-003 6 → 5); 0 de redondeo.
- **«obtenido None»: R36, no el estímulo.** 385 de 394 en IA3 (103 líneas): 77
  con el código de contrato en `?` en el libro y 26 `no_match`; **ninguna** con
  un código presente en las líneas importadas. El estímulo solo empareja lo que
  el libro afirma (P2 = b); el resto lo mide T14.
- **Redondeo → R37 (T16; decisión del humano, opción a):** IA3 7 en FER-002
  (17,59 frente a 17,5932 = 54 × 0,543 × 0,60) y 1 en FER-003 (95,481 frente a
  95,479167); E2E, lo mismo y el total de FER-002 (139,65 frente a 139,66). El
  libro anota el papel en céntimos y sv6 no redondea sin importe declarado: el
  libro no está mal. Ahora el banco tolera 0,05 € ahí; producción no cambia.
