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
