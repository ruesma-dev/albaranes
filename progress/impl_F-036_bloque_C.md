<!-- progress/impl_F-036_bloque_C.md -->
# F-036 · Implementación — BLOQUE C (T14-T20, sv6 + prompt de sv5)

Rama `feature/F-036-residuos-contenedores-e-incrementos`, rigor `critico`.
**Solo el bloque C**: D3 (los incrementos por LER no se emitían nunca) y la
guarda que impide valorar la línea base con la tarifa del incremento. Bloque
A: `impl_F-036.md`. Bloque B: `impl_F-036_bloque_B.md`. Un commit por tarea,
ninguno subido.

| Commit | Tarea |
|---|---|
| `66b32da` | T14 · `residuos_incrementos.py`: reglas del incremento por LER |
| `d1e0f9d` | T15 · guarda anti-incremento de la línea base |
| `54f853c` | T16 · `_sinteticas_residuos_faltantes` + dedupe |
| `863ca43` | T17 · sin tarifa se emite igual, sin precio, a revisión |
| `0d6922b` | T18 · la sintética hereda el nº de contenedores |
| `59b9765` | T19 · predicado por código LER del matcher |
| `2cca7a7` | T20 · prompt `valuation_residuos` de sv5 |

## Ficheros tocados

**Creados**
- `services/albaran-valoracion-persist/application/services/residuos_incrementos.py`
- `services/albaran-valoracion-persist/tests/f036_escenarios_residuos.py` (apoyo)
- `services/albaran-valoracion-persist/tests/test_f036_r16_r19_sinteticas_ler.py`
- `services/albaran-valoracion-persist/tests/test_f036_r15_r20_matcher_ler.py`
- `services/albaran-valoracion-api/tests/test_f036_r16_prompt_residuos_sinteticas.py`

**Modificados**
- `.../application/services/valuation_builder.py` (guarda R15, recorrido R16/R18,
  razón R17, herencia de cantidad R19)
- `.../application/services/modifier_contract_matcher.py` (predicado R20)
- `services/albaran-valoracion-api/config/prompts.yaml` (bloque `valuation_residuos`)

**No se tocó** nada de sv3, sv4 ni `ruesma_comun` (el catálogo LER se consume
desde `ruesma_comun.ler`, no se redefine), ni `residuos_container_calc.py`,
ni `unit_converter`, ni `importe_calculator`, ni `partida_matcher`.

## Fase RED · trazas reales

Comando en los tres casos, desde `services/albaran-valoracion-persist`:
`python -m pytest tests/<fichero> -q` (intérprete `.venv/Scripts/python.exe`,
el que resuelve `python -m harness.servicios --shell`).

**T14 — el módulo no existe** (7 tests en rojo):

```
E       ModuleNotFoundError: No module named 'application.services.residuos_incrementos'
tests\test_f036_r16_r19_sinteticas_ler.py:180: ModuleNotFoundError
...
7 failed in 0.52s
```

**T15 — la base se queda casada con el incremento y con su precio**:

```
>       assert base.matched_contrato_line_id is None
E       assert 9002 is None

>       assert "residuos_base_casada_con_incremento" in base.review_reasons
E       AssertionError: assert 'residuos_base_casada_con_incremento' in
        ['ia_unit_category_mismatch', 'only_1a_available', 'ia_match_trusted',
         'category_mismatch:volume!=count', 'unit_category_mismatch_in_conversion',
         'residuos_contenedores=1 (m3=6 / contenedor=6 m3)']

>       assert base.precio_unitario_contrato_db is None
E       assert 51.0 is None
```

**T16 — no se inyecta ninguna sintética**:

```
>       assert len(sinteticas) == 1
E       assert 0 == 1
E        +  where 0 = len([])
tests\test_f036_r16_r19_sinteticas_ler.py:212: AssertionError
```

**T17 — la línea sin tarifa no dice por qué**:

```
>       assert "residuos_ler_sin_tarifa_en_contrato" in syn.review_reasons
E       AssertionError: assert 'residuos_ler_sin_tarifa_en_contrato' in
        ['inherited_from_base_line', 'modifier_identified_no_tariff']
```

**T18 — la sintética hereda los m³, no los contenedores** (el hallazgo, ver
más abajo):

```
>       assert syn.cantidad_albaran == pytest.approx(1.0)
E         Obtained: 6.0
E         Expected: 1.0 ± 1.0e-06

>       assert cabecera.total_valorado == pytest.approx(171.0)
E       assert 426.0 == 171.0 ± 1.7e-04

>       assert syn.cantidad_convertida == pytest.approx(2.0)
E         Obtained: 12.0
E         Expected: 2.0 ± 2.0e-06
```

**T19 — `"RESIDUOS" in d` casa lo primero que pasa** (incluso la línea de
contenedor, que también lleva la palabra RESIDUOS):

```
>       assert resultado.matched_line.contrato_line_id == INCREMENTO_170904.contrato_line_id
E       AssertionError: assert 9001 == 9003
E        +  where 9001 = ContratoLineContextDto(..., descripcion='MOVIMIENTO DE
           CONTENEDOR DE 6 M CUBICOS MEZCLA OTROS RESIDUOS', ...)

>       assert resultado.matched_line is None
E       AssertionError: assert ContratoLineContextDto(contrato_line_id=9001, ...) is None
```

**T20 — el prompt no nombra al responsable real** (desde
`services/albaran-valoracion-api`):

```
>           assert "incremento por codigo ler" in texto, parte[:120]
E           AssertionError: Eres un experto valorador de obra en Espana, ...
>       assert posicion > 0
E       assert -1 > 0
2 failed, 1 passed in 0.17s
```

## Decisiones de diseño (y por qué)

1. **La guarda de R15 corre ANTES de la reconciliación de precio**, no en
   `:944-1000` como decía el design. Anular solo el id dejaba vivo el
   `precio_unitario_contrato_db` del incremento (51 €/contenedor en el
   escenario, 90 €/m³ en SS-0003967), así que la guarda no habría servido de
   nada. Se anula el match ENTERO —id, precio y `match_method`— que es el
   criterio ya establecido en la casa por `_sanear_matches_incremento_year`.
   Hay un test que lo fija (`..._no_se_queda_con_el_precio_del_incremento`) y
   otro que comprueba que la línea bien casada no se toca.
2. **La fábrica del DTO vive en `residuos_incrementos.py`, no en el builder**
   (el design pedía `_dto_red_residuos` en `valuation_builder.py`). El builder
   importa el módulo de reglas; el import en sentido contrario cierra un ciclo
   de importación. Además es lo que hace cierto R21: una regla nueva (F-006) se
   escribe ENTERA en ese fichero. Igual `claves_dedupe`: la clave de dedupe la
   decide la regla, no el recorrido.
3. **El recorrido del builder no conoce ninguna regla**: itera
   `REGLAS_SINTETICAS_RESIDUOS` y deduplica con `_mod_ya_emitido` usando el
   `rol_linea` del DTO producido y las claves que da el módulo. Test que lo
   demuestra: se añade una regla ficticia a la lista y su sintética sale en la
   valoración sin tocar el builder.
4. **`modifier_source='gestion_residuos'`** ya estaba en el `Literal` de sv5 y
   en el record de sv6: esta red NO estrena valor nuevo, así que los cinco
   sitios de la regla 10 de `docs/ARCHITECTURE.md` quedan intactos.
5. **La razón de R17 se nombra aparte de `modifier_identified_no_tariff`**
   porque dice algo más concreto (el contrato no cubre ESE código LER) y
   porque sv4 la pinta en la ficha (R23, ya hecho en el bloque A).

## Hallazgo: R19 NO era «solo un test»

El design afirmaba que `_build_synthetic_line` ya heredaba el nº de
contenedores y que R19 «solo exige test». El test lo desmintió: heredaba
`parent_record.cantidad_albaran`, que en residuos son los **m³ crudos** del
albarán (`cantidad_albaran` conserva el dato del documento;
`cantidad_convertida` es la cantidad VALORADA, el nº de contenedores). Con 6 m³
= 1 contenedor, el incremento salía a 6 × 51 = 306 € y SS-0000589 en **426 €**
en vez de 171. La herencia se cambia SOLO cuando el padre es
`tipo_familia='residuos'`; fuera de ahí ambas cantidades coinciden y no se
mueve nada (hay test de no regresión con una sintética de hormigón).

## Hallazgos que NO se han tocado (son de otro)

1. **`ModifierContractMatcher` no está cableado en producción.** No lo
   instancia nadie: ni `composition.py` ni el builder (`grep` en todo el
   repositorio: solo su propia definición y las specs de F-004). El predicado
   de T19 queda escrito y probado, pero **hoy no afecta a ninguna valoración
   real**; el precio de la sintética lo pone la tarifa que localiza
   `tarifa_incremento_ler`. Cablearlo es F-004, no F-036.
2. **`texto_contiene_ler` busca `"ler"` como SUBCADENA** (`ruesma_comun/ler.py`,
   `_PALABRAS_CONTEXTO_LER`), así que `TORNILLERIA`, `ALQUILER` o `TALLER` dan
   «contexto de residuos» a cualquier 6-dígitos con forma de capítulo LER. Es
   herencia de sv2 y está pendiente de decisión del humano: **no se ha tocado
   ni rodeado**. Este bloque no lo usa: `es_linea_incremento_ler` y la regla
   usan `normalizar_ler`, que valida capítulo/subcapítulo contra el catálogo y
   no mira palabras de contexto.
3. **`config/prompts.yaml` es ruta sensible** (`harness/rutas_sensibles.json`,
   exigencia `aviso`): su verificación es `python -m evals.runner --con-llm`.
   **No se ha lanzado**: gasta LLM real y esa decisión es del humano, en T25.

## Verificación (resultados literales)

- `python -m pytest tests -q` en `services/albaran-valoracion-persist`:
  **156 passed in 1.14s**. Antes del bloque, 125 (los 31 nuevos son de aquí).
- `python -m pytest tests -q` en `services/albaran-valoracion-api`:
  **34 passed in 0.89s** (incluye el test de T13, que fija el orden de
  prioridades en el mismo prompt que toca T20: sigue en verde sin tocarlo).
- `python -m harness.cobertura --base dev --config harness/rigor.json`:
  `PUERTA COBERTURA: 97.9% de 287 líneas cambiadas cubiertas (281/287,
  umbral 80%, nivel critico)`.
- `python -m harness.tamano --feature F-036`: `PUERTA TAMAÑO: F-036 dentro de
  los topes (requirements 149/150, design 228/250, impl 220/220)`.
- `python -m ruff check` sobre los ficheros nuevos: sin avisos. En
  `valuation_builder.py` y `modifier_contract_matcher.py` el recuento de avisos
  es el mismo que antes del bloque (deuda previa de `Dict`/`Optional`).
- **NO** se ejecutó `bash harness/init.sh` completo: es T25, del bloque D.

## Evidencias

| Evidencia | Valor |
|---|---|
| Tests ejecutados (sv6) | 156, todos en verde |
| Tests ejecutados (sv5) | 34, todos en verde |
| Tests nuevos de este bloque | 34 (23 en `sinteticas_ler`, 8 en `matcher_ler`, 3 en el prompt de sv5) |
| Cobertura de líneas cambiadas | **97.9 %** (281/287), umbral 80 % |
| Mutantes generados / supervivientes | **pendiente: es T23**, tarea propia del bloque de aceptación (`python -m harness.mutacion --feature F-036` → `progress/mutacion_F-036.md`). No se lanza aquí por encargo del líder, que acotó este bloque a T14-T20 |
| Tiempo de ejecución de la suite | sv6 1,14 s · sv5 0,89 s |

Las 6 líneas cambiadas sin cubrir son todas de bloques anteriores
(`ruesma_comun/ler.py` medido desde el `coverage.json` de un servicio que no
ejerce esa función, y `review_repository.py:3244`, ya justificadas en
`impl_F-036.md` y `impl_F-036_bloque_B.md`). De este bloque **no queda ninguna
línea cambiada sin cubrir**.

## Lo que queda fuera y lo que falta

- **T21-T25 no se han tocado**: el escenario de aceptación de SALMEDINA (T21,
  T22), la campaña de mutación (T23), la comprobación MANUAL contra la BBDD
  real (T24, del humano) y `init.sh` en verde (T25).
- **Nada se ha ejecutado contra Azure ni contra la BBDD real.** Todos los tests
  son puros: sin red, sin BBDD, sin LLM.
- **Ningún `git push`.** Siete commits locales en la rama de la feature.
- Los `coverage.json` de sv5 y sv6 quedaron regenerados por la medida de
  cobertura; están en `.gitignore` y no entran en ningún commit.
