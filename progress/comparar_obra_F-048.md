<!-- progress/comparar_obra_F-048.md -->
# F-048 · Comparador de obra dev/rama

Generado por `python -m evals.comparar_obra`. **Sin valores**: solo recuentos y caso_id.
Los códigos de obra están en `evals/salidas/comparar_obra/2026-09-24-160204`, que git ignora.

- Fecha: 2026-09-24T14:02:04Z · rama `64dcbd9` · dev `1807e83`
- IA1 (solo fase 1, sin correo): proveedor `gemini`, modelo `gemini-3.7-flash`
- Variantes: dev, rama · repeticiones: 3 · casos: 10
- Lista de obras activas: 277 obras, una sola consulta a sigrid-api
- Estable = el mismo `obra_codigo` en todas las repeticiones (el nombre no cuenta).

## Recuentos

| Categoría | Nº | Qué significa |
|---|---|---|
| difiere | 1 | dev y rama estables consigo mismas y DISTINTAS entre sí: señal del prompt |
| inestable | 2 | alguna variante cambia de obra entre repeticiones: ruido del LLM |
| identico | 7 | dev y rama estables y con la misma obra |
| con_errores | 0 | alguna repetición falló o no hay albarán: no se puede juzgar |

## Casos por categoría

- **difiere**: RES-015
- **inestable**: RES-005 (rama), RES-011 (dev y rama)
- **identico**: GEN-001, GEN-009, GEN-010, HOR-003, HOR-006, FER-003, RES-012
- **con_errores**: (ninguno)
