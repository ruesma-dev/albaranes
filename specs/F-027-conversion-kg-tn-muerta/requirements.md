<!-- specs/F-027-conversion-kg-tn-muerta/requirements.md -->
# F-027 · Error de ×1000 en el importe: la red KG→TN de `UnitConverter` es código muerto · Requisitos

Notación EARS. Cada requisito se traduce a >= 1 test con nombre trazable
(`test_f027_rN_...`). Los unit tests NO tocan red ni BBDD: los cinco servicios
de sv6 son clases puras y el `ValuationBuilder` recibe sus cinco colaboradores
por constructor, así que se prueban con DTOs Pydantic construidos a mano.

Rigor declarado: **critico** (`harness/features.json`). Es dinero, y no un
error de céntimos: **tres órdenes de magnitud** que llegan persistidos a
`albaran_valuations.total_valorado` y de ahí a la bandeja del revisor.

Servicio tocado: **sv6** (`services/albaran-valoracion-persist`) y solo sv6.

Fuentes: `progress/revision_resto_lote_20260818.md` §4.1 y H-1 (revisión de los
7 albaranes restantes del lote `alvaro_17082026`, 2026-08-18);
`docs/ARCHITECTURE.md` §«Semántica de dominio» regla 8 («no comparar cantidades
ni precios de unidades distintas sin pasar por el conversor»);
`services/albaran-valoracion-persist/sv6.md` §5.2, §6.2 y §6.3.

## Los números del defecto (medidos, no deducidos)

Prueba local del 2026-08-18, albaranes de MATERIALES Y HORMIGONES (MAHORSA)
contra el contrato CTSU25/0085:

| Albarán | Cantidad leída | Unidad leída | Unidad contrato | Esperado (GT) | Obtenido | Δ |
|---|---|---|---|---|---|---|
| 58826 | 30.380 | *(NULL)* | TN | **390,99 €** | **468.763,40 €** | +468.372,41 € |
| 58878 | 29.960 | *(NULL)* | TN | **385,59 €** | **462.282,80 €** | +461.897,21 € |

## Reproducción de la cadena causal (ejecutada al redactar esta spec)

Ejecutando el código real de `dev` (`YamlUnitRegistry` + `UnitConverter` +
`ImporteCalculator`, sin BBDD ni red):

```
HOY — el builder pasa cantidad=None porque category_match es False:
  convert(cantidad=None, unidad_albaran=None, unidad_contrato='TN')
    → ConvertedQuantity(cantidad_convertida=None, factor=None,
                        ambiguous=False, reasons=['no_quantity_in_albaran'])
  compute(cantidad_convertida=None, cantidad_albaran=30380.0, precio=15.43)
    → importe_calculado=468763.4  source='calculated'
      reasons=['importe_using_albaran_quantity_fallback']

CON LA CANTIDAD REAL — la red de plausibilidad SÍ se alcanza:
  convert(cantidad=30380.0, unidad_albaran=None, unidad_contrato='TN')
    → ConvertedQuantity(cantidad_convertida=30.38, factor=0.001,
                        ambiguous=True,
                        reasons=['cantidad_sin_unidad_reinterpretada_kg_a_tn'])
  compute(cantidad_convertida=30.38, precio=15.43) → 468.76
  compute(cantidad_convertida=30.38, precio=12.87) → 390.99   ← el del GT
```

**Conclusión medida**: el conversor está bien escrito y su red funciona; lo que
falla es que el `ValuationBuilder` lo llama a ciegas. El defecto es de UNA
rama `else` de cinco líneas.

**Conclusión igual de importante para no prometer de más**: F-027 elimina el
factor 1000, no el error entero. Con el precio que hoy elige IA3 (15,43 €/TN
en vez de 12,87) el 58826 queda en **468,76 €**, no en 390,99 €. Los 77,77 €
que faltan son **F-031** (elección de línea de contrato por partida) y esta
feature no los toca — ver R23.

## Vocabulario (fijado por esta feature)

| Término | Significado |
|---|---|
| **red de plausibilidad TN** | bloque `unit_converter.py:83-113`: albarán sin unidad + contrato en toneladas ⇒ `>= 1000` se reinterpreta como KG (`/1000`), `>= 100` solo se avisa. |
| **desacuerdo de categoría** | `UnitCategoryGuard.resolve` devuelve `category_match=False`: la IA lo dijo, o una de las dos unidades es `unknown`, o son de categorías conocidas y distintas. |
| **unidad de destino** | la unidad a la que se convierte la cantidad; debe ser siempre la de la línea **que pone el precio** (contrato o derivada). |
| **cantidad efectiva** | la que usa `ImporteCalculator`: `cantidad_convertida` si existe, si no `cantidad_albaran` (fallback crudo, `importe_using_albaran_quantity_fallback`). |

---

## G1 — La red determinista deja de ser inalcanzable

- **R1.** CUANDO el `ValuationBuilder` construye una línea `from_albaran`, el
  sistema debe llamar a `UnitConverter.convert` con la **cantidad realmente
  leída del albarán** (`AlbaranLineContextDto.cantidad`), con independencia del
  valor de `unidad_category_match`. *(Hoy la rama `else` de
  `valuation_builder.py:1020-1025` pasa `cantidad=None` a propósito: ese es el
  defecto. El orden pasa a ser **convertir primero, decidir revisión después**.)*

- **R2.** MIENTRAS haya desacuerdo de categoría de unidad, el sistema debe
  seguir marcando la línea `review_required = true` y conservando el motivo del
  guard (`ia_unit_category_mismatch`, `unit_category_partially_unknown` o
  `unit_category_hard_mismatch:<a>!=<b>`). *(`category_match=False` pasa a
  significar solo «esto lo mira un humano», nunca «tira la cantidad».)*

- **R3.** CUANDO la línea del albarán no trae unidad, el contrato tarifa en
  toneladas y la cantidad es `>= 1000`, el sistema debe valorar con la cantidad
  reinterpretada `cantidad / 1000`, dejar `factor_conversion = 0,001`, el motivo
  `cantidad_sin_unidad_reinterpretada_kg_a_tn` y `review_required = true`.
  *(La red existe desde jul 2026 y sus tests unitarios pasan; lo que faltaba
  era un test que la ejercitara **a través del builder**, que es donde muere.)*

- **R4.** CUANDO la línea no trae unidad, el contrato tarifa en toneladas y la
  cantidad está en `[100, 1000)`, el sistema NO debe alterar la cantidad y debe
  dejar el motivo `cantidad_tn_implausible_revisar` con
  `review_required = true`. *(Implausible pero no seguro: se avisa, no se toca.
  Regresión del comportamiento ya escrito en el conversor.)*

- **R5.** SI las dos unidades son conocidas y de categorías distintas de verdad
  (p. ej. `UD` contra `M3`), ENTONCES el sistema NO debe convertir: el conversor
  debe devolver `cantidad_convertida = None` con
  `unit_category_mismatch_in_conversion`, el importe debe caer al fallback con
  la cantidad cruda (`importe_using_albaran_quantity_fallback`) y la línea debe
  ir a revisión. *(Verificado al redactar: `convert(108, 'UD', 'M3')` ya
  devuelve `None`. **Es el argumento central del diseño**: el conversor YA se
  niega a cruzar categorías, así que anular la cantidad en el builder no
  protege de nada — solo mata las redes del caso `unknown`.)*

## G2 — La unidad de destino es la de la línea que pone el precio

- **R6.** CUANDO la valoración de una línea genera una **línea de contrato
  derivada**, el sistema debe convertir la cantidad a la unidad de **esa línea
  derivada** (`DerivedContratoLineRecord.unidad_medida`), que es la que lleva el
  precio con el que se multiplica. *(Hoy `valuation_builder.py:1009-1012` usa
  `unidad_albaran` cuando hay derivada. Eso solo es correcto cuando la derivada
  heredó la unidad del albarán; `PartidaMatcher._build_derived:263-266` le da la
  unidad de la línea de contrato casada por la IA siempre que exista, que es el
  caso normal.)*

- **R7.** CUANDO el albarán trae `KG`, el contrato tarifa en `TN` y el matching
  de partida genera una derivada, el sistema debe valorar con la cantidad
  convertida (`30.380 KG → 30,38 TN`, factor 0,001) y NO con la cantidad cruda.
  *(Es la **otra mitad del mismo ×1000**, viva hoy sin necesidad de que la IA
  falle: con ambas unidades presentes el guard da `category_match=True`, entra
  por la rama de la derivada y convierte `KG → KG` con factor 1 contra un precio
  por tonelada. Y es exactamente el escenario que activa **F-024** cuando IA1
  empiece a extraer la unidad.)*

## G3 — La guarda de cantidad ausente sigue protegiendo

- **R8.** SI la línea del albarán no trae cantidad (`cantidad is None`),
  ENTONCES `UnitConverter.convert` debe seguir devolviendo
  `cantidad_convertida = None`, `factor = None` y el motivo
  `no_quantity_in_albaran`, sin entrar en ninguna red de plausibilidad.
  *(Esa guarda existe por algo y no se toca: sin cantidad no hay nada que
  reinterpretar. Regresión estricta del comportamiento actual.)*

- **R9.** CUANDO la cantidad leída es `0`, el sistema debe seguir tratándola
  como cantidad presente y de valor cero (factor 1, sin reinterpretación), para
  no interferir con la regla de residuos «una línea de movimiento sin cantidad
  vale 1» (`valuation_builder.py:1047-1063`). *(Regresión: hoy `0` ya pasa la
  guarda de `None`.)*

- **R10.** SI una línea tiene cantidad leída, ENTONCES el sistema NO debe emitir
  `no_quantity_in_albaran` para esa línea. *(Consecuencia directa de R1, no
  código nuevo: al desaparecer la rama que pasaba `cantidad=None` a propósito,
  el motivo vuelve a significar lo que dice. Es el hallazgo H-2 de la revisión
  de hormigones y el objeto de **F-025**; ver R22 para la coordinación. Esta
  feature **no** renombra ni añade ningún motivo.)*

## G4 — Los dos albaranes de MAHORSA, con sus números

- **R11.** CUANDO se valora el albarán **58826** (línea única
  `ARIDO M-20/40-S EN 12620:2002H`, cantidad `30380`, sin unidad, contrato
  CTSU25/0085 con la línea tarifada en `TN`), el sistema debe producir
  `cantidad_convertida = 30,38`, `factor_conversion = 0,001` y un
  `importe_calculado` **del orden de las centenas de euros**, nunca 468.763,40 €:
  **390,99 €** con el precio de contrato correcto (12,87 €/TN) y **468,76 €**
  con el que hoy elige IA3 (15,43 €/TN, defecto de F-031).

- **R12.** CUANDO se valora el albarán **58878** (cantidad `29960`, mismas
  condiciones), el sistema debe producir `cantidad_convertida = 29,96` e
  `importe_calculado` **385,59 €** con 12,87 €/TN y **462,28 €** con 15,43 €/TN,
  nunca 462.282,80 €.

- **R13.** El sistema debe fijar por test el **total del documento**
  (`ValuationHeaderRecord.total_valorado`, la columna
  `albaran_valuations.total_valorado`), no solo el importe de la línea suelta:
  para el 58826 debe salir del `ValuationBuilder.build` completo y no superar
  los 500 €. *(Lección de F-019 R25: los tests que solo miran la línea dejan
  pasar el agregado, que es lo que ve el revisor en la bandeja.)*

## G5 — Lo que hoy funciona debe seguir dando exactamente lo mismo

- **R14.** CUANDO se valora una línea de **hormigón o mortero** sin unidad leída
  contra un contrato en `M3` (los 4 albaranes del lote `alvaro_17082026`:
  224964 con 4 m³, 225137 con 9 m³, 1167 con 8 m³, 1229 con 3 m³), el sistema
  debe producir **exactamente el mismo importe que hoy**. *(Medido: hoy la
  cantidad cae al fallback crudo con factor 1; tras el cambio el conversor
  devuelve la misma cantidad con `no_albaran_unit_assumed_same` y factor 1. El
  número no se mueve; lo que cambia es el motivo, que pasa a ser cierto.)*

- **R15.** CUANDO se valora una línea de **ferretería en unidades** (albaranes
  Feymaco 2.137.569 y 2.139.643, unidades leídas y contrato en `UD`), el sistema
  debe producir exactamente los mismos unitarios e importes que fija F-019 R16
  y R18. *(La conversión ya se ejecutaba porque `category_match` era `True`:
  esta feature no la roza.)*

- **R16.** CUANDO se valora el albarán **A261584 de VODALAND** (único del lote
  con total correcto hoy: **3.393,00 €**), el sistema debe seguir dando
  3.393,00 €. *(Testigo de no-regresión elegido a propósito: si el cambio
  moviera algo que hoy está bien, este es el que lo delata.)*

- **R17.** MIENTRAS una unidad sea de las declaradas **ambiguas** en
  `config/unit_registry.yaml` (`saco`, `caja`, `palet`, `rollo`…), el sistema
  debe seguir convirtiéndola con factor 1 marcando
  `ambiguous_unit_conversion` y `review_required = true`. *(Regresión.)*

- **R18.** El sistema NO debe modificar `config/unit_registry.yaml`, ni los
  umbrales `_TN_UMBRAL_CONVERTIR = 1000` / `_TN_UMBRAL_AVISAR = 100`, ni la
  firma pública de `UnitConverter.convert`. *(El conversor no está mal: está
  desconectado. Un cambio ahí sería tratar el síntoma.)*

## G6 — El revisor tiene que poder ver qué pasó

- **R19.** El sistema debe distinguir con motivos DISTINTOS estos tres estados,
  para que el revisor sepa cuál está mirando:

  | Estado | Motivo en `review_reasons` | `cantidad_convertida` | `factor_conversion` |
  |---|---|---|---|
  | Se convirtió aplicando la red de plausibilidad | `cantidad_sin_unidad_reinterpretada_kg_a_tn` | cantidad / 1000 | 0,001 |
  | Magnitud sospechosa pero no se tocó | `cantidad_tn_implausible_revisar` | cantidad | 1,0 |
  | No se pudo convertir (categorías incompatibles) | `unit_category_mismatch_in_conversion` + `importe_using_albaran_quantity_fallback` | `None` | `None` |
  | La cantidad falta de verdad | `no_quantity_in_albaran` | `None` | `None` |

  *(Los cuatro motivos ya existen; el requisito es que lleguen a la línea, que
  es lo que hoy no ocurre. Comprobado por `grep` en todo el monorepo: fuera de
  sv6 y de `sv6.md` nadie consume estos strings, así que no hay lector que
  romper.)*

- **R20.** CUANDO se aplique la reinterpretación de R3, el sistema debe dejar
  rastro **numérico** además del textual: `cantidad_albaran = 30380` junto a
  `cantidad_convertida = 30,38` y `factor_conversion = 0,001` en
  `albaran_line_valuations`. *(La ficha de línea de sv4 ya lee las tres
  columnas —`review_repository.py:970-974` y `1071-1074`—, así que la
  reinterpretación es visible en el front sin tocar sv4.)*

- **R21.** El sistema debe conservar el `logger.warning` del conversor
  («cantidad %s sin unidad con contrato en TN: reinterpretada como KG») como
  traza de operación. *(Hoy ese warning no se ha emitido nunca en producción:
  su ausencia en los logs del 2026-08-18 es, en sí misma, la prueba de que la
  red estaba muerta.)*

## G7 — Alcance, coordinación y puertas

- **R22.** El sistema NO debe renombrar, añadir ni retirar ningún string de
  motivo de revisión en esta feature. *(**Coordinación con F-025**: F-025
  propone emitir `conversion_skipped_unit_category_mismatch` en la rama `else`
  que F-027 elimina. Al no haber ya conversión omitida a propósito, F-025 se
  queda sin su caso principal y su alcance debe **reevaluarlo el humano** antes
  de arrancarla. Queda anotado en `progress/current.md` como decisión abierta.)*

- **R23.** El sistema NO debe tocar la elección de línea de contrato ni el
  `PartidaMatcher`. *(**Coordinación con F-031**: el precio 15,43 €/TN en vez de
  12,87 sobrevive a esta feature a propósito. F-027 arregla el factor 1000;
  F-031 arregla el precio. Mezclarlas haría imposible saber cuál de las dos
  produjo cada euro de diferencia en la prueba local.)*

- **R24.** El sistema NO debe tocar ningún prompt ni ninguna fase de IA.
  **La corrección determinista de sv6 NO sustituye a la revisión razonada de
  plausibilidad de IA2**, que es una capa distinta y debe existir igualmente.
  Regla del humano, 2026-08-18, literal:

  > «En este caso la IA2 al revisar debería darse cuenta de que un camión no
  > puede llevar 30.000 toneladas. Si la cantidad es esa, tiene que ser kg.
  > Debe haber una revisión razonada de unidades, para casos tan claros.»

  Esa capa se especifica en **F-024** (misma familia de prompts y mismo
  problema de raíz), no aquí. Defensa en profundidad: **IA2 detecta arriba,
  sv6 protege abajo**; que la red de sv6 funcione no legitima que el dato siga
  llegando mal desde la extracción.

- **R25.** SI el diff toca
  `services/albaran-valoracion-persist/application/services/**` —lo hace:
  `valuation_builder.py` es ruta sensible declarada en
  `harness/rutas_sensibles.json` (motivo «redes deterministas de sv6»)—,
  ENTONCES el cierre debe producir `progress/evals_F-027.md` con la pasada
  declarada `python -m evals.runner --con-llm --feature F-027`; SI el ground
  truth sigue vacío y la pasada da `NO_EVALUABLE`, ENTONCES el motivo debe
  constar por escrito en el informe de review (exigencia `aviso`, decisión D5
  de F-011; CHECKPOINTS.md C4 ter). *(No se marca N/A a secas.)*

- **R26.** SI una valoración ya persistida se re-valora tras esta feature,
  ENTONCES el importe debe recalcularse solo con el mecanismo existente
  —replace transaccional por `document_id` (`docs/ARCHITECTURE.md` regla 2)
  disparado desde sv4 → `q-valoracion`—, **sin script de migración ni
  reescritura de histórico**. Los 468.763,40 € persistidos del 58826 siguen ahí
  hasta que el humano decida re-valorar. *(Mismo criterio que F-019 R19/R20.)*

- **R27.** CUANDO sv4 recalcula el importe de una línea ya valorada, debe
  seguir usando `cantidad_convertida` con fallback a `cantidad_albaran`
  (`review_repository.py:1434-1438` y `1689-1690`), de modo que el 30,38 que
  escribe sv6 sea también el que use el front. *(No hay cambio de código en
  sv4: es una verificación de que la corrección no se deshace al guardar desde
  el front. **Ojo al solape con F-019**, que está reescribiendo esas mismas
  fórmulas — ver `design.md` §«Solape con F-019».)*

---

## Trazabilidad rápida requisito → nivel de prueba

| Requisito | Nivel |
|---|---|
| R3, R4, R5, R8, R9, R17 | unit de `UnitConverter` (ya existe la lógica; falta el test) |
| R1, R2, R6, R7, R10, R19, R20 | unit de `ValuationBuilder._build_line` con DTOs a mano |
| R11, R12, R13 | `ValuationBuilder.build` completo (línea + cabecera) |
| R14, R15, R16 | regresión con los envelopes del lote `alvaro_17082026` |
| R18, R22, R23, R24 | test de contrato/estructura (fichero sin cambios, motivos sin altas ni bajas) |
| R21 | `caplog` sobre el conversor |
| R25 | puerta de `init.sh` + `progress/evals_F-027.md` |
| R26, R27 | MANUAL (humano), prueba local de extremo a extremo |
