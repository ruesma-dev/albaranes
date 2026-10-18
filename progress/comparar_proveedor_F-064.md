<!-- progress/comparar_proveedor_F-064.md -->
# F-064 · Comparador del proveedor base/rama

Generado por `python -m evals.comparar_proveedor`. **Sin valores**: solo recuentos, caso_id y veredicto.
Los CIF y los nombres están en `evals/salidas/comparar_proveedor/2026-10-18-013938`, que git ignora.

- Fecha: 2026-10-17T23:39:38Z · rama `e0ee65c` · base `544113b` (`544113b`)
- IA1: proveedor `gemini`, modelo `gemini-2.5-flash` · IA2: proveedor `openai`, modelo `gpt-5`
- Variantes: base, rama · repeticiones: 3 · casos: 19 (sin correo, sin lista de obras, sin contexto de Sigrid)

## Recuentos (casos por categoría mayoritaria)

| Mayoría del caso | base IA1 | base IA2 | rama IA1 | rama IA2 | Qué significa |
|---|---|---|---|---|---|
| emisor | 8 | 8 | 9 | 9 | el CIF esperado del emisor (normalizado) |
| cliente | 0 | 0 | 0 | 0 | el CIF de una empresa del cliente: el fallo que corrige F-064 |
| nulo | 10 | 10 | 9 | 9 | sin CIF |
| otro | 1 | 1 | 1 | 1 | un CIF que no es ni el del emisor ni el del cliente |
| error | 0 | 0 | 0 | 0 | la ejecución falló o no hay albarán |
| inestable | 0 | 0 | 0 | 0 | (solo mayoría) empate entre categorías en las repeticiones |
| *ejecuciones con CIF cliente* | 0 | 0 | 0 | 0 | para C1 |

## Casos por categoría mayoritaria

- **base tras IA1** · emisor: FER-001, FER-002, FER-003, COM-001, GEN-004, GEN-010, HOR-012, RES-010 · nulo: HOR-006, HOR-007, HOR-008, HOR-009, HOR-010, HOR-011, MOR-003, ALQ-001, GEN-002, RES-001 · otro: HOR-005
- **base tras IA2** · emisor: FER-001, FER-002, FER-003, COM-001, GEN-004, GEN-010, HOR-012, RES-010 · nulo: HOR-006, HOR-007, HOR-008, HOR-009, HOR-010, HOR-011, MOR-003, ALQ-001, GEN-002, RES-001 · otro: HOR-005
- **rama tras IA1** · emisor: FER-001, FER-002, FER-003, COM-001, GEN-002, GEN-004, GEN-010, HOR-012, RES-010 · nulo: HOR-005, HOR-006, HOR-007, HOR-008, HOR-009, HOR-010, HOR-011, ALQ-001, RES-001 · otro: MOR-003
- **rama tras IA2** · emisor: FER-001, FER-002, FER-003, COM-001, GEN-002, GEN-004, GEN-010, HOR-012, RES-010 · nulo: HOR-005, HOR-006, HOR-007, HOR-008, HOR-009, HOR-010, HOR-011, ALQ-001, RES-001 · otro: MOR-003

## Ejecuciones con error

(ninguno)

## Veredicto

- C1 · OK · ejecuciones con CIF cliente: rama tras IA2 = 0 (debe ser 0); tras IA1 rama = 0, base = 0 (rama ≤ base)
- C2 · OK · tras IA1 rama = 9, base = 8; tras IA2 rama = 9, base = 8 (casos con mayoría emisor, rama ≥ base)
- C3 · OK · casos que pierden la mayoría emisor en la rama: (ninguno)
- AVISO: la base no dio ningún CIF cliente: el banco no reproduce el incidente y C1 no prueba nada (design.md §7: añadir el albarán real).

VEREDICTO: VERDE
