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
