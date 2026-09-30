<!-- progress/impl_F-048_evals.md -->
# F-048 · Runner de evals y comparador de obra — texto íntegro

Movido tal cual desde `progress/impl_F-048.md` el 2026-09-24 (bloque E) para respetar el tope de 220
líneas. Allí queda su resumen.

## Runner de evals: fallos aislados por caso — 2026-09-24

Encargo del líder (aprobado por el humano el 24-sep) tras la pasada `--con-llm` muerta a los 50 min sin
informe: IA2 devolvió JSON degenerado en UN caso, `json_invalid`, el hijo de sv2 salió con 1 y
`corrida_completa` no capturaba el `RuntimeError`. Solo `evals/` y `tests/`: producción intacta.
**Commits**: `77b4bc2` (código + tests) · `3470648` (tests de bordes). **No se lanzó ninguna pasada con LLM.**
- **Hijos** (`sv2_extraccion`, `sv5_valoracion`, `sv6_build`: los tres tenían el mismo agujero): el bucle pasa
  a `procesar_casos(...)`, con cada caso (y en sv2 cada proveedor) en su `try`. El error va al resultado del
  caso como `error: {fase, tipo, motivo}` (sv2: `preproceso`/`IA1`/`IA2`; sv5: `IA3`/`IA4`; sv6: `build`) y
  el bucle sigue; lo que IA1 ya devolvió se conserva si falla IA2. Avance por stderr: `sv2_extraccion: caso
  X, proveedor Y: ok` / `: error en IA2 · <motivo>`. El `main` de los tres ya no imprime `str(error)`.
- **`evals/procesos/errores.py`** (nuevo): `describir_error` da la FORMA, nunca el texto: pydantic →
  `errors(include_input=False, …)`, tipo + `loc` + línea/columna sacadas de `msg` (máx. 3 y «(+N más)»);
  `JSONDecodeError` → posición; SDK → `HTTP <código>`; resto → solo el tipo. Tope 200 caracteres.
- **Padre** (`runner.py`): **decisión**: no hay estado `ERROR`; el caso sale `OMITIDO` con motivo
  `ERROR en IA2 · ValidationError: json_invalid (línea 1, columna N)` (si falla IA1, IA2 dice «no se
  evaluó: falló IA1»). Consecuencia a sabiendas: un caso roto no pone la fase en ROJO, pero cuenta en
  «omitidos» y lleva su motivo. Si un subproceso entero muere (`_ejecutar_aislado`), sus fases quedan
  NO_EVALUABLE con motivo y el informe se escribe; el stderr del hijo va a la consola, NO al informe.
  Un caso que sv5 no valora sale omitido en IA3, IA4 y E2E y no va a sv6; sin build de sv6, IA3 y E2E
  omitidos, IA4 se evalúa igual (antes, sin resultado de sv6 se saltaban IA3 e IA4 en silencio).

**RED** (`python -m pytest tests/test_f048_evals_fallos_aislados.py -q --tb=line -p no:cacheprovider`, test antes del código):
```
1ª (errores.py aún no existía)  E ModuleNotFoundError: No module named 'evals.procesos.errores'  -> 1 error
2ª E AttributeError: module 'evals.procesos.sv2_extraccion' has no attribute 'procesar_casos'  (sv2, sv5, sv6)
   E RuntimeError: el subproceso de sv2 falló con código 1:
    CENTINELA-VALOR-DEL-ALBARAN-7731   (el fallo real)
   E KeyError: 'envelope'   (runner.py:357, un caso roto de sv5)
   E RuntimeError: el subproceso de sv6 falló con código 1: ... data.lineas  Input should be a valid list
     [type=list_type, input_value='CENTINELA-VALOR-DEL-ALBARAN-7731', ...]   (sv6 real: tumba todo Y filtra el valor)
   20 failed, 5 passed in 5.38s          -> 25 passed in 2.19s;  con los bordes: 31 passed in 2.93s
```
**MANUAL (líder)**: relanzar T40. **Fuera**: stderr del hijo en vivo (sale por consola si muere); estado `ERROR` propio.

| Evidencia (runner de evals) | Valor real |
|---|---|
| Tests ejecutados | 31 nuevos; raíz `896 passed in 214.73s` en `bash harness/init.sh` (ENTORNO LISTO) |
| Cobertura de las líneas cambiadas | 99.7 % (872/875), `PUERTA COBERTURA` de la feature |
| Mutación | no relanzada: T34 es anterior a este cambio; nueva campaña a decisión del líder (nivel `critico`) |
| Tiempo de la suite | raíz 214.73 s; el fichero nuevo 2.93 s |

## Comparador de obra dev/rama — 2026-09-24
Encargo del líder (aprobado por el humano el 24-sep) tras `progress/analisis_evals_F-048.md`: medir si cambia la
obra que lee IA1. Solo `evals/` y `tests/`. **Commits** `a264c36` (código + tests) · `8b37675` (test de dev). **No se lanzó contra LLM.**
- `evals/comparar_obra.py`: CLI, corrida aislada por caso (`describir_error`, se sigue), clasificación e informes.
  `evals/procesos/sv2_obra.py`: montaje de sv2 (YAML de `dev` con `git show`, `ObrasFijas`, consulta con el
  `SigridApiObrasClient` de sv2 y su corte `cod_min`). Solo fase 1, sin correo, `IA_PRIMERA_FASE` (gemini).
- **Decisión 1 (ajuste del diseño): schema.** Los clientes mandan el JSON Schema del modelo al proveedor
  (`response_json_schema` en gemini) y el de la rama lleva `lectura_correo`, que `dev` no conoce: la variante `dev`
  usa el schema SIN ese campo (`modelo_sin_campo`). El test extrae `dev` con `git archive` y compara lo que llega al
  cliente LLM (`instructions`, `user_text`, schema): **idéntico byte a byte**. Confirma la decisión 2 de C1.
- **Decisión 2**: en proceso (solo usa sv2: el proceso del CLI ya es el intérprete dedicado) y con los clientes LLM
  del runner (`_especificacion`, sin la `retry_policy` de producción): lo que lee el LLM no cambia.
- **Decisión 3**: UNA consulta de obras, congelada en `ObrasFijas` para las dos variantes y todas las repeticiones.
  El cliente de sv2 es best-effort (devuelve `None`): lista `None` o vacía = **parada**, no «NO DISPONIBLE».
- **Decisión 4**: paradas con código 2, todas ANTES del LLM y sin escribir nada, en este orden: clave del
  proveedor → algún albarán → variables de sigrid-api → `git show dev:` → consulta de obras. Código 1 si ninguna extracción sale.
- **Decisión 5**: variantes intercaladas dentro de cada repetición. Estable = mismo `obra_codigo` en todas (se quitan
  los espacios y el vacío cuenta como null; el nombre no cuenta). Categorías: `difiere` (estables y distintas: señal del
  prompt), `inestable` (ruido), `identico`, `con_errores`. Con una sola variante: `estable`, `inestable` y `con_errores`.
- Salida CON valores: `<dir>/<variante>_r<n>.json` (`caso_id → obra_codigo, obra_nombre` o `error`) y `<dir>/resumen.md`,
  ignorados (`git check-ignore`: `.gitignore:53`). SIN valores y versionable: `progress/comparar_obra_F-048.md`.

**Comando** (se factura: 10 casos × 2 variantes × 3 repeticiones = 60 llamadas a IA1; la rama `dev` tiene que estar en local):
```
python -m evals.comparar_obra --casos GEN-001,GEN-009,GEN-010,HOR-003,HOR-006,FER-003,RES-005,RES-011,RES-012,RES-015 --repeticiones 3 --variante ambas
```
Desde el merge de F-048 en `dev` (`2b05ba7`), repetir esta medición pide añadir `--base 1807e83` (el `dev` de antes de
F-048): sin `--base`, la variante `dev` sale de la rama `dev` y ya lleva el prompt nuevo
(`progress/impl_fix_F-048_comparar_obra_base.md`).
Entorno (solo nombres): `GEMINI_API_KEY` (o `OPENAI_API_KEY`/`ANTHROPIC_API_KEY` si `IA_PRIMERA_FASE` lo cambia),
`SIGRID_API_BASE_URL`, `SIGRID_API_FUNCTION_KEY`, `SIGRID_API_DATABASE`. Opcionales, con los defectos de sv2:
`IA_PRIMERA_FASE`, `GEMINI_MODEL`, `SIGRID_API_TIMEOUT_S`, `OBRAS_ACTIVAS_COD_MIN`, `OBRAS_ACTIVAS_MAX`.

**RED** (test antes del código; el de `dev`, rompiendo una copia del montaje y restaurándola):
```
python -m pytest tests/test_f048_comparar_obra.py -q --tb=line -p no:cacheprovider
E   ImportError: cannot import name 'comparar_obra' from 'evals' (...\evals\__init__.py)      -> 1 error in 0.94s
python -m pytest tests/test_f048_comparar_obra_prompt_dev.py -q --tb=line -p no:cacheprovider
  sin recortar el schema:    E AssertionError: assert 'lectura_correo' not in {'cabecera': ...}   2 failed, 2 passed in 7.42s
  YAML de HEAD como de dev:  E AssertionError: assert 'Eres un admi..._imputacion`.' == 'Eres un admi..._imputacion`.'  1 failed, 3 passed in 6.63s
-> 32 passed in 3.35s (comparador) · 4 passed in 14.84s (prompt de dev)
```
**MANUAL (líder)**: lanzar el comando y leer `progress/comparar_obra_F-048.md`. **Fuera**: fase 2, correo, ground truth.

| Evidencia (comparador) | Valor real |
|---|---|
| Tests | 36 nuevos; raíz `932 passed in 404.61s` en `bash harness/init.sh` (ENTORNO LISTO) |
| Cobertura de las líneas cambiadas | 98.7 % (1158/1173). Sin cubrir: 12 de `sv2_obra.py`, que solo corren en el subproceso del test de `dev` |
| Mutación | no relanzada; las dos roturas de la fase RED hacen de mutantes a mano. Campaña nueva: la decide el líder |
| Tiempo de la suite | raíz 404.61 s; los dos ficheros nuevos, 3.35 s y 14.84 s |
