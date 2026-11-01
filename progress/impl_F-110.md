# F-110 · informe del implementer

Rama `feature/F-110-descuento-linea-sigrid` (worktree `../albaranes-F-110`). Rigor `critico`.

## T0 · precondición

- `git merge dev` (169 commits por detrás) sin conflictos: merge `ee32a55`. Entran F-106, F-108, F-113, F-114, F-115
  y el alta de F-116; comun **0.11.0**.
- Nombres reales que dejó F-106 (design §2 y §8 los suponían):
  - comun `alta_sigrid.linea_a_sigrid(*, vinculada, cantidad_albaran, cantidad_convertida, importe)` devuelve una
    **tupla** `(cantidad, precio)`; los tests de F-106 la comparan con `== (48.0, 2.17)` y sv9 la desempaqueta.
  - Llamantes: sv9 `validador_alta._linea_peticion`; sv4 `review_models.a_sigrid_de_fila` (vista «A Sigrid», la llama
    `review_repository._marcar_cuadre`, estático); JS `precioASigrid(cant, imp, factor)` + `textoASigrid`
    (`static/app.js`); el script R18 (`scripts/listar_altas_descuadradas_f106.py`) NO llama a `linea_a_sigrid`.
  - P y d en `LineaAlta`: `precio_unitario_final`, `descuento_albaran_aplicado`. R17 de F-106: `_detalle_no_cuadra`
    (Q = convertida o, sin ella, la del albarán).
  - Ninguna R de F-106 cambia ⇒ se sigue (design §11 R-4).
- Línea base: `bash harness/init.sh` (con `PYTHONPATH` y `ARNES_SIN_CACHE=1`) verde en todas las suites salvo los dos
  ficheros RED nuevos de F-110 (ya escritos al terminar la base); comun sin ellos: 1342 passed.
- *Junction* `services/albaranes-front/.venv` → la del árbol principal (quitar con `cmd /c rmdir`).
- `features.json`: F-110 `in_progress`.

## Desviaciones respecto a la spec (justificadas)

1. **`LineaASigrid` no es una dataclass** (design §6/§8 la pedía «dataclass congelada»): es una tupla inmutable de
   dos elementos `(cantidad, precio)` con el atributo `dto`. Motivo: T3 y R23 exigen que los tests de F-106 sigan
   sin tocar aserciones, y esos tests comparan con `(48.0, 2.17)` y desempaquetan dos valores. La igualdad con una
   tupla simple solo vale con `dto` nulo; con `dto`, solo es igual a otra `LineaASigrid` con el mismo `dto`.
   Design §11 R-4 prevé este ajuste («se ajusta el diseño sin cambiar R»).
2. **`dto` que redondea a 0** (p. ej. d = 0,004): va como hoy, sin `dto` (caso `l_redondea_a_cero`). El contrato v8.4
   trata `dto` 0 como «sin descuento» y design §4 dice que albaranes nunca manda 0.
3. **`test_f115_t2_version_0110`** pasa de «== 0.11.0» a «≥ 0.11.0 y pyproject igual» (lo mismo que hicieron F-098,
   F-106 y F-113 con el suyo); la exacta 0.12.0 la fija `test_f110_t3_version_0120`.

## Fase RED (trazas reales)

**T2 · comun** — `python -m pytest tests/test_f110_linea_a_sigrid.py -q --tb=short` (desde `services/albaranes-comun`):

```
tests\test_f110_linea_a_sigrid.py:26: in <module>
    from ruesma_comun.alta_sigrid import (
E   ImportError: cannot import name 'LITERAL_ENVIAR_DTO' from 'ruesma_comun.alta_sigrid'
ERROR tests/test_f110_linea_a_sigrid.py
1 error in 1.16s
```
Tras T3: `58 passed in 0.95s`; suite de comun `1401 passed` (F-106 sin tocar aserciones).

**T4 · sv9 config e infra** — `python -m pytest tests/test_f110_config.py tests/test_f110_infra.py -q --tb=line`
(desde `services/albaranes-alta-sigrid`), extracto:

```
test_f110_infra.py:49: assert '"ALTA_SIGRID_ENVIAR_DTO=$($Global:ALTA_SIGRID_ENVIAR_DTO)"' in 'function Global:AltaSigridEnvComun() {...'
test_f110_infra.py:55: assert '"ALTA_SIGRID_ENVIAR_DTO"' in '"ALTA_SIGRID_DESDE_UTC", "ALTA_SIGRID_ESPERA_INCIERTO_MIN", "ALTA_SIGRID_PRODUCTO_POR_DEFECTO"'
FAILED tests/test_f110_config.py::test_f110_r5_apagada_por_defecto - Attribut...
FAILED tests/test_f110_config.py::test_f110_r5_config_alta_nace_apagada - Att...
FAILED tests/test_f110_config.py::test_f110_r5_log_dice_encendida - ValueErro...
FAILED tests/test_f110_infra.py::test_f110_r20_vars_versiona_la_guarda_apagada
20 failed, 20 passed in 3.07s
```

**T6 · sv9 petición** — `python -m pytest tests/test_f110_peticion.py -q --tb=line`, extracto:

```
test_f110_peticion.py:212: AssertionError: assert <EstadoAlta.ERROR: 'error'> is <EstadoAlta.NO_ADMITIDO: 'no_admitido'>
test_f110_peticion.py:229: AttributeError: 'LineaPeticion' object has no attribute 'dto'
test_f110_peticion.py:278: KeyError: 'dto'
FAILED tests/test_f110_peticion.py::test_f110_r7_cecois_bruto_y_dto_tras_el_precio
FAILED tests/test_f110_peticion.py::test_f110_r8_r22f_no_cuadra_a_sigrid - As...
FAILED tests/test_f110_peticion.py::test_f110_r9_r22d_vinculada_feymaco_con_dto
FAILED tests/test_f110_peticion.py::test_f110_aviso1_el_dto_solo_va_por_el_modo_extendido
15 failed, 12 passed in 1.15s
```
(Los 12 que pasan en RED son los de R6, la guarda apagada y las claves del modo extendido: fijan lo de hoy.)
Tras T7: `27 passed`. Un caso del RED se corrigió (no el código): la vinculada con conversión llevaba P en la unidad
del albarán y F-106 R17 (que compara con la convertida) la paraba; P va en la unidad del contrato (25,0).

**T8 · sv9 previa** — `python -m pytest tests/test_f110_previa.py -q --tb=line`, extracto:

```
test_f110_previa.py:129: AssertionError: assert <EstadoAlta.INCIERTO: 'incierto'> is <EstadoAlta.REVISAR: 'revisar'>
FAILED tests/test_f110_previa.py::test_f110_r11_difiere_mas_de_0005[7.006-7,006]
FAILED tests/test_f110_previa.py::test_f110_r11_sin_dto_en_la_previa - Assert...
FAILED tests/test_f110_previa.py::test_f110_r11_dto_ilegible[None] - Assertio...
FAILED tests/test_f110_previa.py::test_f110_r11_en_el_servicio_va_a_revisar_sin_grabar
14 failed, 8 passed in 1.09s
```
(Sin `dto_distinto`, la previa sin `dto` pasaba y el servicio seguía a grabar.) Tras T8, con `test_f053_comparador.py`:
`52 passed`.

**T9 · regresión sv9** — `python -m pytest -q` en sv9: `1162 passed` sin tocar aserciones de F-053…F-106. Un test de
F-069 lanza un script en un subproceso sin `PYTHONPATH` (usa la comun 0.11 del árbol principal): `LineaASigrid` se
importa solo bajo `TYPE_CHECKING` en `validador_alta.py`, así el módulo no exige el nombre al importarse.

**T10 · sv4 ficha** — `.venv/Scripts/python.exe -m pytest tests/test_f110_ficha.py -q --tb=line` (desde sv4), extracto:

```
test_f110_ficha.py:170: TypeError: AlbaranReviewRepository.__init__() takes 2 positional arguments but 3 were given
test_f110_ficha.py:223: assert ('data-alta-dto="1"' in '<input type="text" ... data-factor-alta="1.0" value="120.00" placeholder="—">') is True
FAILED tests/test_f110_ficha.py::test_f110_r14_apagada_por_defecto - Attribut...
FAILED tests/test_f110_ficha.py::test_f110_r15_cecois_con_la_guarda - TypeErr...
FAILED tests/test_f110_ficha.py::test_f110_r15_repositorio_con_la_guarda - Ty...
24 failed, 2 passed in 3.83s
```
Tras T10: `86 passed` (`test_f110_ficha.py` con los de ficha de F-106).

**T11 · sv4 JS** — `.venv/Scripts/python.exe -m pytest tests/test_f110_js.py -q --tb=short`, extracto:

```
E   AssertionError: a_cecois
E   assert (12, 0.6, None) == (12, 0.645, 7)
E     At index 0 diff: 'A Sigrid: 12 × 0,645 €' != 'A Sigrid: 12 × 0,645 € −7 %'
test_f051_almacen_front.py:1239: ValueError: substring not found      (dtoDifiere aún no existe en app.js)
17 failed in 4.11s
```
Tras T11: `34 passed` (`test_f110_js.py` y `test_f106_js.py`, este sin tocar).

**T12 · sv4 panel** — `.venv/Scripts/python.exe -m pytest tests/test_f110_panel.py -q --tb=line`, extracto:

```
test_f110_panel.py:98: ValueError: 'Dto %' is not in list
test_f110_panel.py:103: KeyError: 'dto_distinto'
FAILED tests/test_f110_panel.py::test_f110_r17_lineas_con_dto_pedido_y_de_sigrid
12 failed in 1.56s
```
Además `test_f077_r27_todo_codigo_de_sv9_tiene_texto` (F-077, lee las fuentes de sv9) ya fallaba tras T8:
`assert ['dto_distinto'] == []`.
Tras T12: `122 passed` (`test_f110_panel.py`, `test_f077_motivos_alta.py`, `test_f104_textos_avisos.py`, `test_f053_t21_panel.py`).

**T13 · regresión sv4** — `.venv/Scripts/python.exe -m pytest -q` en sv4: `2441 passed in 226.63s`, sin tocar
aserciones de tests anteriores.

**T14 · script R18/R19** — `python -m pytest tests/test_f110_script.py -q --tb=line` (sv9), extracto:

```
FAILED tests/test_f110_script.py::test_f110_r19_con_dto_bruto_y_dto_correctos_no_sale
FAILED tests/test_f110_script.py::test_f110_r19_sin_dto_como_f106 - Attribute...
FAILED tests/test_f110_script.py::test_f110_r19_csv_con_las_columnas_nuevas_al_final
15 failed, 2 passed in 0.91s
```
Tras T14: `46 passed` (`test_f110_script.py` y `test_f106_script.py`, este sin tocar; solo `SELECT`).

**T19 · avisos v8.4** (hecha contra el contrato publicado, por indicación del líder del 2026-11-01: F-018 desplegada) —
`.venv/Scripts/python.exe -m pytest tests/test_f110_avisos_v84.py -q --tb=line`:

```
test_f110_avisos_v84.py:39: AssertionError: assert [{'codigo': '..._linea': '9'}] == [{'codigo': '..._linea': '9'}]
FAILED tests/test_f110_avisos_v84.py::test_f110_r13_texto_de_los_avisos_v84[dto_distinto_del_contrato-...]
FAILED tests/test_f110_avisos_v84.py::test_f110_r13_texto_de_los_avisos_v84[precio_distinto_del_contrato-...]
3 failed, 1 passed in 0.78s
```
Tras T19: `54 passed` (con F-104 y F-077). Sin códigos nuevos de error: un `dto` mal formado es 400 sin código ⇒
`error` (H25), así que `CODIGOS_LINEA` no cambia.

**T15 · documentación** — `docs/ARCHITECTURE.md` regla 19 (viñeta «Precio y descuento a Sigrid (F-110)»), `sv9.md`
(sección «Descuento por línea», «Llaves» y «Reglas») y `azure-apps/albaranes.md` §10 (commit local `3b09da9` en
`azure-apps`, sin push). `azure-apps/sigrid_api.md` no se toca.

**T16 · mutación** — `python -m harness.mutacion --feature F-110 --base dev --max-mutantes 0` (4 workers, sin otra
suite en marcha): **108 mutantes, 90 muertos, 18 supervivientes**, 0 timeouts, 4145,6 s. 15 eran huecos reales: 13
tests nuevos `test_f110_t16_*` (comun, sv9 petición y script, sv4 ficha). Cada mutante se reaplicó a mano y su test
falla (`1 failed`). 3 son equivalentes justificados. Análisis uno a uno en `progress/mutacion_F-110.md`; fila nueva
en `progress/inventario_mutacion_F-039.md` (la pedía `test_f039_r2…`).

## Ficheros tocados (40, `git diff --stat ee32a55..HEAD`)

- **comun** (0.12.0): `ruesma_comun/alta_sigrid.py` (`LITERAL_ENVIAR_DTO`, `enviar_dto_activo`, `LineaASigrid`,
  `linea_a_sigrid` con §5), `pyproject.toml`, `__init__.py`; tests `f110_casos.json` (tabla compartida con el JS),
  `test_f110_linea_a_sigrid.py`, `test_f115_pertenencia.py` (desviación 3).
- **sv9**: `config/settings.py`, `interface_adapters/composition.py`, `main_worker.py` (log de la guarda),
  `.env.example`, `domain/models/alta_models.py` (`LineaPeticion.dto`), `domain/services/validador_alta.py` (R7–R9),
  `domain/services/comparador_previa.py` (`dto_distinto`), `scripts/listar_altas_descuadradas_f106.py` (R19),
  `sv9.md`; tests `test_f110_{config,infra,peticion,previa,script}.py`.
- **sv4**: `config/settings.py`, `domain/models/alta_sigrid_models.py` (columna «Dto %», textos `dto_distinto` y avisos
  v8.4), `domain/models/review_models.py` (`a_sigrid_de_fila`), `infrastructure/database/review_repository.py`,
  `interface_adapters/web/app.py`, `templates/document_detail.html`, `templates/_alta_sigrid.html`, `static/app.js`;
  tests `test_f110_{ficha,js,panel,avisos_v84}.py`.
- **infra**: `00_capps_vars.ps1` (`ALTA_SIGRID_ENVIAR_DTO = "false"` en `AltaSigridEnvComun`), `set_alta_sigrid.ps1`.
- **docs y arnés**: `docs/ARCHITECTURE.md` (regla 19), `azure-apps/albaranes.md` §10 (otro repo, commit `3b09da9`),
  `harness/features.json` (F-110 `in_progress`), `progress/current.md`, `progress/inventario_mutacion_F-039.md`,
  `specs/F-110-descuento-linea-sigrid/tasks.md`.

## Fuera de alcance y pendiente (sin marcar en `tasks.md`)

- **La guarda nace apagada** (`ALTA_SIGRID_ENVIAR_DTO = "false"` en `00_capps_vars.ps1`, `.env.example` vacío): hasta
  que el humano la encienda tras desplegar, producción manda lo de F-106.
- **T1** (líder, lectura de PostgreSQL de Azure): repetir las lecturas de design §3.
- **T17** (líder, Chrome con el pipeline local y la guarda encendida): ficha CECOIS y panel «Dto %».
- **T18** (líder): contrastar v8.4 con design §4. Para T19 ya se usó el contrato publicado. **Aviso 2**, por revisar
  aquí: una vinculada enviada **sin** `dto` (guarda apagada o d no aplicable) puede volver de la previa con el `dto`
  copiado del `ctrpro` (opción C). R11 no lo compara (solo las pedidas con `dto`), pero el `total` de la previa
  puede apartarse del importe y dar `importe_distinto` (tolerancia 0,05) ⇒ `revisar`. No se añadió lógica: lo decide
  el líder.
- **T20** (líder): listar las altas ya grabadas en neto (design §9); el humano decide (D5).
- **T21** (humano): despliegue en dos pasos y encender la llave. **T22** (líder): primera alta real con descuento.
- El *junction* `services/albaranes-front/.venv` del worktree apunta a la del árbol principal: quitarlo con
  `cmd /c rmdir` antes de borrar el worktree (no borrar con `rm -rf`, que entraría en la venv real).

## Evidencias

| Evidencia | Valor real |
|---|---|
| Tests (init.sh, `ARNES_SIN_CACHE=1`) | raíz 1919 · sv1 236 · sv2 496 · sv3 1608 · sv4 2447 · sv5 125 · sv6 506 (+1 skip) · sv9 1186 · comun 1406: 9925, verdes |
| Tests nuevos de F-110 | comun 64 · sv9 113 (config, infra, petición, previa, script) · sv4 61 (ficha, JS, panel, avisos) |
| Cobertura de líneas cambiadas | `PUERTA COBERTURA: 98.3% de 174 líneas cambiadas cubiertas (171/174, umbral 80%, nivel critico)` |
| Mutación (completa, sin tope) | 108 generados · 90 muertos · 18 supervivientes ⇒ 15 matados después con tests nuevos, 3 equivalentes |
| Tiempo de la suite | raíz 286,7 s · sv4 238,3 s · comun 53,3 s · sv9 43,6 s (el resto < 29 s) |
| Tiempo de la campaña | 4145,6 s (38,4 s por mutante) |
| `PUERTA TAMAÑO` | requirements 116/150 · design 189/250 · impl 208/220 |

**T23 · `bash harness/init.sh`** (`PYTHONPATH` a la comun del worktree y `ARNES_SIN_CACHE=1`, sobre `d789d5e`):
`ENTORNO LISTO. Puedes trabajar.` La primera pasada dio KO en la raíz por `test_f039_r2…` (faltaba la fila de F-110 en
el inventario de mutación); con la fila añadida, verde.
