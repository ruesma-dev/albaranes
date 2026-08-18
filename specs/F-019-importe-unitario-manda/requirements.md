<!-- specs/F-019-importe-unitario-manda/requirements.md -->
# F-019 · Importe de línea: manda el unitario leído; el importe solo se despeja si faltan campos · Requisitos

Notación EARS. Cada requisito se traduce a >= 1 test con nombre trazable
(`test_f019_rN_...`). Los unit tests NO tocan red ni BBDD real: los servicios
de sv6 son clases puras y se prueban con DTOs construidos a mano; el SELECT de
sv5 se prueba ejecutándolo contra **SQLite en memoria** con la tabla creada al
vuelo (comprobado viable, ver `design.md` §«Cómo se prueba el SQL sin BBDD»).

Rigor declarado: **critico** (`harness/features.json`). Es dinero: un fallo
aquí multiplica importes por la cantidad de la línea.

Normativa de referencia: `docs/ARCHITECTURE.md` §«Semántica de dominio»
(reglas 3, 8 y 11) y `docs/referencia/dominio_negocio_albaranes.md` §10.4
(albaranes que VIENEN valorados: «transcribir, no recomponer») y §10.5
(precedencia de importe).

## Vocabulario (fijado por esta feature)

| Término | Significado |
|---|---|
| **unitario bruto** | precio por unidad ANTES de descuento. Es lo que sv2 extrae en `precio` y lo que sv6 persiste en `precio_unitario_final`. |
| **importe de línea** | total de la línea DESPUÉS de descuento. Es lo que sv2 extrae en el campo llamado `precio_neto` (nombre histórico y engañoso, ver R1) y lo que sv6 persiste en `importe_calculado`. |
| **importe efectivo** | el valor que sv5 entrega a sv6 como `importe_albaran`. |
| **derivar** | despejar el unitario bruto del importe: `importe / (cantidad × (1 − dto/100))`. |

Fórmula canónica del dominio, única y sin excepciones:

```
importe_de_linea = cantidad × unitario_bruto × (1 − descuento/100)
```

## G1 — La semántica de `precio_neto` queda fijada y vigilada

- **R1.** El sistema debe tratar `precio_neto` de una línea de albarán
  (`albaran_lines`/`albaran_lines_merge`, campo homónimo del envelope de
  extracción) como el **IMPORTE de la línea tras descuento**, NUNCA como un
  precio unitario. Esta semántica es la que ya aplican el prompt de IA1
  (`services/albaranes-api/config/prompts.yaml`: «calcula
  cantidad*precio*(1 - descuento/100)»), el guard de consistencia de sv3
  (`albaran_confidence_service._is_line_net_consistent`, que compara
  `precio_neto` contra `cantidad × precio × (1 − dto/100)`), el front sv4
  (`review_repository`: `eff_importe = line.precio_neto`) y los clientes de
  Document AI / Document Intelligence (`precio_neto ← Amount / LineAmount /
  TotalPrice`). El único consumidor que la contradecía era sv5 (R2).

- **R2.** SI alguien cambia el prompt de IA1 de modo que `precio_neto` deje de
  definirse como el importe total de la línea, ENTONCES un test de contrato
  cruzado del monorepo debe FALLAR, señalando que sv5 y sv6 deben
  reconciliarse en el mismo trabajo. *(Guardia deliberada contra F-003 R1,
  que planea sustituir ese campo por uno con nombre propio: el test no
  prohíbe el cambio, obliga a hacerlo entero.)*

- **R3.** El sistema debe dejar la semántica escrita **donde se consume**, no
  solo en el prompt: en `docs/ARCHITECTURE.md` (§Semántica de dominio, regla
  nueva), en el SELECT de sv5, en el DTO del envelope de sv6
  (`AlbaranLineContextDto.precio_neto_albaran`) y en `sv5.md` / `sv6.md`.

## G2 — sv5 deja de inflar el importe

- **R4.** CUANDO sv5 construye el contexto de valoración de una línea que trae
  `precio_neto`, el sistema debe entregar `importe_albaran = precio_neto`
  (el importe leído, tal cual), sin multiplicarlo por la cantidad.
  *(Caso de referencia Feymaco 2.137.569 línea 1: cantidad 108,
  precio 0,543, descuento 40 %, precio_neto 35,19 → `importe_albaran` = 35,19,
  nunca 3.800,52.)*

- **R5.** CUANDO la línea NO trae `precio_neto` pero sí `precio`, el sistema
  debe entregar `importe_albaran = cantidad × precio × (1 − COALESCE(dto,0)/100)`.
  *(Es la cascada que introdujo el «FIX 2 (jul 2026)» y que se conserva
  íntegra: sin ella, un albarán con precios pero sin descuento llegaba a sv6
  con el importe mudo.)*

- **R6.** SI la línea no trae ni `precio_neto` ni `precio`, ENTONCES
  `importe_albaran` debe ser NULL y sv6 debe seguir cayendo al precio del
  contrato. *(Caso hormigón: el albarán no imprime precios; el importe lo pone
  el contrato. Comportamiento actual, que NO se toca.)*

- **R7.** CUANDO la línea trae `precio_neto` pero NO trae cantidad,
  el sistema debe entregar igualmente `importe_albaran = precio_neto`.
  *(Hoy sale NULL porque el producto con cantidad NULL es NULL: el importe
  leído se perdía. Cambio de comportamiento deliberado.)*

## G3 — sv6: manda el unitario leído

- **R8.** CUANDO una línea del albarán trae **unitario declarado** distinto de
  cero, el `PriceReconciler` debe devolver ese unitario como
  `final_price` con `source = "albaran_declared"`, con independencia de que
  exista o no importe leído del que derivar. *(Inversión de la prioridad
  actual: hoy el importe manda y el declarado solo se respeta si coincide.)*

- **R9.** CUANDO la línea NO trae unitario declarado (ausente o cero) pero sí
  importe leído y cantidad válida, el `PriceReconciler` debe despejar el
  unitario bruto `importe / (cantidad × (1 − dto/100))` y devolverlo con
  `source = "albaran_calculated"`. *(Segunda mitad de la regla del humano: el
  importe solo se despeja cuando faltan los campos.)*

- **R10.** CUANDO existen unitario declarado e importe leído derivable y ambos
  discrepan más allá de `PRICE_TOLERANCE_PCT`, el sistema debe usar el
  **declarado** (R8), devolver `agreement = "mismatch"` y dejar el motivo
  `unitario_declarado_vs_derivado_mismatch:<declarado>!=<derivado>`; la línea
  debe quedar `review_required = true`. *(Hoy el mismatch se registra pero
  NADIE lo lleva a revisión: el dato malo se persistía en silencio.)*

- **R11.** MIENTRAS la línea del albarán no traiga ni unitario declarado ni
  importe leído derivable, el sistema debe conservar EXACTAMENTE la cadena de
  fallback al contrato vigente (1a y 1b coinciden → media; discrepan → 1a;
  solo 1a → 1a; solo 1b → 1b; nada → `None` + `no_price_available`).
  *(Es el caso para el que nació la valoración: el albarán sin valorar.)*

- **R12.** SI una línea del albarán trae valores leídos, ENTONCES el precio del
  contrato NO debe pisarlos en ningún caso. *(Protección contra partidas
  alzadas que motivó el diseño de jul 2026: la cinta de señalización de
  18,84 € leídos que se valoró a 960.000 € por casar con una PA de 8.000 €.
  Test de regresión obligatorio: esa protección no se pierde al invertir la
  prioridad interna entre importe y unitario, porque ambos son del albarán.)*

- **R13.** El sistema debe seguir tratando un valor leído **igual a 0** como
  AUSENTE (celda vacía), tanto en el importe como en el unitario, dejando su
  motivo de auditoría (`importe_albaran_cero_ignorado`,
  `precio_declarado_cero_ignorado`). *(Regresión: comportamiento actual.)*

- **R14.** SI el descuento de la línea es 100 %, o la cantidad es nula o cero,
  ENTONCES la derivación del unitario no debe ejecutarse (división imposible)
  y el sistema debe dejar el motivo correspondiente
  (`descuento_100_no_derivable`, `importe_leido_sin_cantidad_no_derivable`) y
  continuar por la siguiente prioridad, sin excepción ni valor inventado.
  *(Regresión: comportamiento actual, revalidado tras la inversión.)*

- **R15.** SI el descuento viene fuera del rango [0,100], ENTONCES ni la
  derivación de sv6 ni el cálculo del importe deben aplicarlo, y debe quedar
  el motivo `descuento_fuera_de_rango_ignorado:<valor>`. *(Regresión del
  `ImporteCalculator`; se revalida porque la fórmula canónica de R4/R5 usa el
  mismo descuento.)*

## G4 — Los dos albaranes de Feymaco, con sus números

- **R16.** CUANDO se valora el albarán Feymaco **2.137.569** (ferretería,
  contrato CTSU24/0454, descuento 40 % en las cinco líneas), el sistema debe
  producir por línea el unitario y el importe de la columna «correcto»:

  | # | Concepto | Cantidad | Precio leído | Dto | Importe | Hoy (mal) |
  |---|---|---|---|---|---|---|
  | 1 | PAPEL HIGIENICO (SACO 108) | 108 | 0,543 | 40 % | 35,19 | 58,6500 / 3.800,52 |
  | 2 | LTS. JABON LIQUIDO PH NEUTRO | 10 | 3,422 | 40 % | 20,53 | 34,2167 / 205,30 |
  | 3 | ROLLO PAPEL IND. | 12 | 7,726 | 40 % | 55,63 | 92,7167 / 667,56 |
  | 4 | KGS AÑIL ESPECIAL FEYMACO | 4 | 5,497 | 40 % | 13,19 | 21,9833 / 52,76 |
  | 5 | BOLSA BASURA 52X58 | 100 | 0,252 | 40 % | 15,12 | 25,2000 / 1.512,00 |

  y la suma de los importes de línea debe ser **139,66 €** (hoy: 6.238,14 €).

- **R17.** CUANDO se corrige el importe efectivo de R4, el unitario **derivado**
  de la línea 1 (`35,19 / (108 × 0,6) = 0,543055…`) debe coincidir con el
  **declarado** (`0,543`) dentro de `PRICE_TOLERANCE_PCT`, de modo que la línea
  salga `agreement != "mismatch"` y NO se marque revisión por este motivo.
  *(Comprobación explícita pedida por el humano: corrigiendo el punto 1 de la
  cadena causal, el punto 2 ya cuadra solo. La inversión de prioridad de R8 es
  la garantía de que vuelva a cuadrar aunque el documento traiga ruido.)*

- **R18.** CUANDO se valora el albarán Feymaco **2.139.643**, el total valorado
  debe ser **19,41 €** y no 970,50 €. *(Solo se conoce el total: verificación
  MANUAL (humano) contra el pipeline local, ver `tasks.md` T9.)*

## G5 — Regresión y documentos ya persistidos

- **R19.** SI una línea ya persistida se re-valora tras esta feature, ENTONCES
  el resultado debe recalcularse con las reglas nuevas sin migración de datos
  ni script: la valoración es un **replace transaccional** por `document_id`
  (`docs/ARCHITECTURE.md` regla 2) y el contexto se relee del merge, que NO
  cambia. El sistema NO debe reescribir histórico por su cuenta.

- **R20.** MIENTRAS no se re-valore, las valoraciones antiguas conservan sus
  importes inflados. El sistema debe permitir corregirlas con el mecanismo YA
  existente (re-valorar desde sv4 publicando en `q-valoracion`); la lista de
  documentos afectados y su reproceso son decisión del humano, no de esta
  feature. *(Se documenta en `progress/`; no hay código nuevo.)*

- **R21.** SI un envelope en vuelo o una fila de BBDD es anterior a esta
  feature, ENTONCES la valoración debe completarse sin error (semántica
  at-least-once de las colas: no se puede exigir redrive). Los campos del
  contrato sv5→sv6 no cambian de nombre ni de tipo en esta feature.

- **R22.** Los ficheros tocados bajo
  `services/albaran-valoracion-persist/application/services/**` son **rutas
  sensibles** declaradas en `harness/rutas_sensibles.json`. CUANDO la puerta de
  `bash harness/init.sh` las señale, el sistema debe producir
  `progress/evals_F-019.md` con la pasada declarada
  (`python -m evals.runner --con-llm --feature F-019`); SI el ground truth
  sigue vacío y la pasada da `NO_EVALUABLE`, ENTONCES el motivo debe constar
  por escrito en el informe de review (exigencia `aviso`, decisión D5 de
  F-011). *(No es un checkbox que se marque N/A a secas: CHECKPOINTS.md C4
  ter.)*
