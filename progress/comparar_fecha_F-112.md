<!-- progress/comparar_fecha_F-112.md -->
# F-112 · Comparador de la fecha base/rama

Generado por `python -m evals.comparar_fecha`. **Sin valores**: solo recuentos, caso_id y veredicto.
Las fechas leídas están en `evals/salidas/comparar_fecha/2026-11-10-013321`, que git ignora.

- Fecha: 2026-11-10T00:33:21Z · rama `4de0676` · base `dev` (`4156c98`)
- IA1: `gemini`, modelo `gemini-4-argon` · IA2: `openai`, modelo `gpt-6.1-sol`
- Juegos: A, B, C, D · variantes: base, rama · repeticiones: 2 · casos: 58 (sin correo, sin lista de obras, sin Sigrid)

## Recuentos (casos por categoría mayoritaria)

### Juego A (19 casos)

| Mayoría del caso | base IA1 | base IA2 | rama IA1 | rama IA2 | Qué significa |
|---|---|---|---|---|---|
| exacta | 11 | 12 | 16 | 17 | la fecha esperada (día, mes y año) |
| referencia | 0 | 0 | 0 | 0 | la referencia de recepción copiada como fecha (y no es la esperada) |
| solo_anio | 2 | 1 | 2 | 1 | día y mes de la esperada con otro año: el fallo que corrige F-112 |
| otra | 3 | 3 | 1 | 1 | otra fecha (o un texto que no es fecha) |
| nula | 1 | 1 | 0 | 0 | sin fecha |
| error | 0 | 0 | 0 | 0 | la ejecución falló o no hay albarán |
| inestable | 2 | 2 | 0 | 0 | (solo mayoría) empate entre categorías en las repeticiones |
| *ejecuciones `referencia`* | 0 | 0 | 0 | 0 | para C4 |

### Juego B (20 casos)

| Mayoría del caso | base IA1 | base IA2 | rama IA1 | rama IA2 | Qué significa |
|---|---|---|---|---|---|
| exacta | 18 | 18 | 20 | 20 | la fecha esperada (día, mes y año) |
| referencia | 0 | 0 | 0 | 0 | la referencia de recepción copiada como fecha (y no es la esperada) |
| solo_anio | 0 | 0 | 0 | 0 | día y mes de la esperada con otro año: el fallo que corrige F-112 |
| otra | 2 | 2 | 0 | 0 | otra fecha (o un texto que no es fecha) |
| nula | 0 | 0 | 0 | 0 | sin fecha |
| error | 0 | 0 | 0 | 0 | la ejecución falló o no hay albarán |
| inestable | 0 | 0 | 0 | 0 | (solo mayoría) empate entre categorías en las repeticiones |
| *ejecuciones `referencia`* | 0 | 0 | 0 | 0 | para C4 |

### Juego C (13 casos)

| Mayoría del caso | base IA1 | base IA2 | rama IA1 | rama IA2 | Qué significa |
|---|---|---|---|---|---|
| exacta | 13 | 13 | 13 | 13 | la fecha esperada (día, mes y año) |
| referencia | 0 | 0 | 0 | 0 | la referencia de recepción copiada como fecha (y no es la esperada) |
| solo_anio | 0 | 0 | 0 | 0 | día y mes de la esperada con otro año: el fallo que corrige F-112 |
| otra | 0 | 0 | 0 | 0 | otra fecha (o un texto que no es fecha) |
| nula | 0 | 0 | 0 | 0 | sin fecha |
| error | 0 | 0 | 0 | 0 | la ejecución falló o no hay albarán |
| inestable | 0 | 0 | 0 | 0 | (solo mayoría) empate entre categorías en las repeticiones |
| *ejecuciones `referencia`* | 0 | 0 | 0 | 0 | para C4 |

### Juego D (6 casos)

| Mayoría del caso | base IA1 | base IA2 | rama IA1 | rama IA2 | Qué significa |
|---|---|---|---|---|---|
| exacta | 2 | 2 | 6 | 6 | la fecha esperada (día, mes y año) |
| referencia | 0 | 0 | 0 | 0 | la referencia de recepción copiada como fecha (y no es la esperada) |
| solo_anio | 0 | 0 | 0 | 0 | día y mes de la esperada con otro año: el fallo que corrige F-112 |
| otra | 0 | 0 | 0 | 0 | otra fecha (o un texto que no es fecha) |
| nula | 4 | 4 | 0 | 0 | sin fecha |
| error | 0 | 0 | 0 | 0 | la ejecución falló o no hay albarán |
| inestable | 0 | 0 | 0 | 0 | (solo mayoría) empate entre categorías en las repeticiones |
| *ejecuciones `referencia`* | 0 | 0 | 0 | 0 | para C4 |

## Casos por categoría mayoritaria

- **A · base tras IA1** · exacta: FEC-001, FEC-004, FEC-006, FEC-007, FEC-010, FEC-014, FEC-015, FEC-016, FEC-017, FEC-018, FEC-019 · solo_anio: FEC-002, FEC-013 · otra: FEC-003, FEC-011, FEC-012 · nula: FEC-009 · inestable: FEC-005, FEC-008
- **A · base tras IA2** · exacta: FEC-001, FEC-004, FEC-005, FEC-006, FEC-007, FEC-010, FEC-014, FEC-015, FEC-016, FEC-017, FEC-018, FEC-019 · solo_anio: FEC-013 · otra: FEC-003, FEC-011, FEC-012 · nula: FEC-009 · inestable: FEC-002, FEC-008
- **A · rama tras IA1** · exacta: FEC-001, FEC-002, FEC-004, FEC-005, FEC-006, FEC-007, FEC-008, FEC-009, FEC-010, FEC-011, FEC-012, FEC-013, FEC-014, FEC-017, FEC-018, FEC-019 · solo_anio: FEC-015, FEC-016 · otra: FEC-003
- **A · rama tras IA2** · exacta: FEC-001, FEC-002, FEC-004, FEC-005, FEC-006, FEC-007, FEC-008, FEC-009, FEC-010, FEC-011, FEC-012, FEC-013, FEC-014, FEC-016, FEC-017, FEC-018, FEC-019 · solo_anio: FEC-015 · otra: FEC-003
- **B · base tras IA1** · exacta: GEN-003, GEN-005, GEN-006, GEN-010, GRA-002, HOR-001, HOR-002, HOR-005, HOR-010, HOR-017, MOR-001, MOR-002, MOR-004, RES-003, RES-004, RES-009, RES-017, RES-018 · otra: FER-001, RES-013
- **B · base tras IA2** · exacta: GEN-003, GEN-005, GEN-006, GEN-010, GRA-002, HOR-001, HOR-002, HOR-005, HOR-010, HOR-017, MOR-001, MOR-002, MOR-004, RES-003, RES-004, RES-009, RES-017, RES-018 · otra: FER-001, RES-013
- **B · rama tras IA1** · exacta: FER-001, GEN-003, GEN-005, GEN-006, GEN-010, GRA-002, HOR-001, HOR-002, HOR-005, HOR-010, HOR-017, MOR-001, MOR-002, MOR-004, RES-003, RES-004, RES-009, RES-013, RES-017, RES-018
- **B · rama tras IA2** · exacta: FER-001, GEN-003, GEN-005, GEN-006, GEN-010, GRA-002, HOR-001, HOR-002, HOR-005, HOR-010, HOR-017, MOR-001, MOR-002, MOR-004, RES-003, RES-004, RES-009, RES-013, RES-017, RES-018
- **C · base tras IA1** · exacta: HOR-006, HOR-007, HOR-008, HOR-009, HOR-010, HOR-011, RES-001, RES-002, RES-003, RES-004, RES-005, RES-006, RES-007
- **C · base tras IA2** · exacta: HOR-006, HOR-007, HOR-008, HOR-009, HOR-010, HOR-011, RES-001, RES-002, RES-003, RES-004, RES-005, RES-006, RES-007
- **C · rama tras IA1** · exacta: HOR-006, HOR-007, HOR-008, HOR-009, HOR-010, HOR-011, RES-001, RES-002, RES-003, RES-004, RES-005, RES-006, RES-007
- **C · rama tras IA2** · exacta: HOR-006, HOR-007, HOR-008, HOR-009, HOR-010, HOR-011, RES-001, RES-002, RES-003, RES-004, RES-005, RES-006, RES-007
- **D · base tras IA1** · exacta: SIN-004, SIN-005 · nula: SIN-001, SIN-002, SIN-003, SIN-006
- **D · base tras IA2** · exacta: SIN-004, SIN-005 · nula: SIN-001, SIN-002, SIN-003, SIN-006
- **D · rama tras IA1** · exacta: SIN-001, SIN-002, SIN-003, SIN-004, SIN-005, SIN-006
- **D · rama tras IA2** · exacta: SIN-001, SIN-002, SIN-003, SIN-004, SIN-005, SIN-006

## Efecto de IA2 (ejecuciones, fecha de IA1 frente a la final)

| Juego | Variante | corrige | estropea | cambia | igual |
|---|---|---|---|---|---|
| A | base | 2 | 0 | 1 | 35 |
| A | rama | 2 | 0 | 0 | 36 |
| B | base | 0 | 0 | 0 | 40 |
| B | rama | 0 | 0 | 0 | 40 |
| C | base | 0 | 0 | 0 | 26 |
| C | rama | 0 | 0 | 0 | 26 |
| D | base | 0 | 0 | 0 | 12 |
| D | rama | 0 | 0 | 0 | 12 |

- `estropea` en base: (ninguno)
- `estropea` en rama: (ninguno)

## Ejecuciones con error

(ninguno)

## Veredicto

- C1 · OK · juego A, casos `anio` con mayoría exacta tras IA2: rama = 13 de 14 (umbral 12), base = 7 (rama ≥ umbral y ≥ base)
- C2 · OK · juego B, casos que pierden la exacta en rama: (ninguno)
- C3 · OK · juego C, exactos en base que pasan a solo_anio o referencia en rama: (ninguno)
- C4 · OK · ejecuciones `referencia` en rama: 0 (debe ser 0)
- C5 · OK · casos con IA2 `estropea` en rama: (ninguno)
- C6 · OK · juego D, sin mayoría exacta en rama: (ninguno)
- C7 · OK · juego A, `antigua` sin mayoría exacta en rama: (ninguno)

VEREDICTO: VERDE
